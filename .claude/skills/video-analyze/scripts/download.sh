#!/usr/bin/env bash
# Usage: download.sh <url> <auth_mode> <out_dir>
# Downloads a video to <out_dir>/video.mp4
# Writes <out_dir>/download_method.txt with the method used.

set -euo pipefail

URL="$1"
AUTH_MODE="${2:-auto}"   # auto | cookies | apify
OUT_DIR="$3"

UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

is_social_url() {
    [[ "$1" =~ instagram\.com|instagr\.am|tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com ]]
}

is_instagram() {
    [[ "$1" =~ instagram\.com|instagr\.am ]]
}

is_tiktok() {
    [[ "$1" =~ tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com ]]
}

referer_for_url() {
    local url="$1"
    if [[ "$url" =~ tiktok|tiktokcdn|tiktokv ]]; then
        echo "https://www.tiktok.com/"
    elif [[ "$url" =~ instagram|cdninstagram|fbcdn ]]; then
        echo "https://www.instagram.com/"
    elif [[ "$url" =~ twitter|twimg ]]; then
        echo "https://twitter.com/"
    else
        echo ""
    fi
}

download_with_curl() {
    local video_url="$1"
    local referer
    referer=$(referer_for_url "$video_url")
    local extra_headers=()
    if [[ -n "$referer" ]]; then
        extra_headers+=(-H "Referer: $referer" -H "Origin: ${referer%/}")
    fi
    echo "  curl: ${video_url:0:100}..." >&2
    curl -L --fail --max-time 300 \
        -A "$UA" \
        -H "Accept: video/*,*/*" \
        -H "Accept-Language: en-US,en;q=0.9" \
        "${extra_headers[@]}" \
        -o "${OUT_DIR}/video.mp4" \
        "$video_url"
}

# Which browser yt-dlp pulls cookies from. Override with VIDEO_ANALYZE_BROWSER,
# e.g. firefox, safari, edge, brave, chromium, opera, vivaldi.
COOKIE_BROWSER="${VIDEO_ANALYZE_BROWSER:-chrome}"

try_ytdlp_cookies() {
    echo "  Trying yt-dlp with ${COOKIE_BROWSER} cookies..." >&2
    yt-dlp \
        --cookies-from-browser "$COOKIE_BROWSER" \
        -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' \
        --merge-output-format mp4 \
        --no-playlist \
        -o "${OUT_DIR}/video.mp4" \
        --quiet \
        "$URL" 2>&1 | tail -5 >&2
}

try_ytdlp_no_auth() {
    echo "  Trying yt-dlp (no auth)..." >&2
    yt-dlp \
        -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' \
        --merge-output-format mp4 \
        --no-playlist \
        -o "${OUT_DIR}/video.mp4" \
        --quiet \
        "$URL" 2>&1 | tail -5 >&2
}

try_apify_instagram() {
    if [[ -z "${APIFY_API_TOKEN:-}" ]]; then
        echo "  APIFY_API_TOKEN not set, skipping Apify for Instagram." >&2
        return 1
    fi
    echo "  Trying Apify (instagram-scraper)..." >&2

    local body
    body=$(URL="$URL" python3 -c "
import json, os
print(json.dumps({
    'directUrls': [os.environ['URL']],
    'resultsType': 'posts',
    'resultsLimit': 1,
    'addParentData': False
}))
")

    local response
    response=$(curl -s --max-time 180 -X POST \
        "https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items?token=${APIFY_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$body")

    local video_url
    video_url=$(echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if not isinstance(data, list) or not data:
    sys.exit(1)
item = data[0]
# Try videoUrl first, then childPosts for carousels
url = item.get('videoUrl') or ''
if not url and item.get('childPosts'):
    for cp in item['childPosts']:
        if cp.get('videoUrl'):
            url = cp['videoUrl']
            break
if not url:
    sys.exit(1)
print(url)
" 2>/dev/null) || { echo "  Apify: could not extract video URL from response." >&2; return 1; }

    download_with_curl "$video_url"
}

try_apify_tiktok() {
    if [[ -z "${APIFY_API_TOKEN:-}" ]]; then
        echo "  APIFY_API_TOKEN not set, skipping Apify for TikTok." >&2
        return 1
    fi
    echo "  Trying Apify (tiktok-scraper)..." >&2

    local body
    body=$(URL="$URL" python3 -c "
import json, os
print(json.dumps({
    'postURLs': [os.environ['URL']],
    'shouldDownloadVideos': True,
    'shouldDownloadCovers': True,
    'shouldDownloadSubtitles': False,
    'shouldDownloadSlideshowImages': False
}))
")

    local response
    response=$(curl -s --max-time 180 -X POST \
        "https://api.apify.com/v2/acts/clockworks~tiktok-scraper/run-sync-get-dataset-items?token=${APIFY_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$body")

    local video_url
    video_url=$(echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if not isinstance(data, list) or not data:
    sys.exit(1)
item = data[0]
video_meta = item.get('videoMeta') or {}
media_urls = item.get('mediaUrls') or []
music_meta = item.get('musicMeta') or {}
url = (video_meta.get('downloadAddr') or
       (media_urls[0] if media_urls else '') or
       music_meta.get('playUrl') or '')
if not url:
    sys.exit(1)
print(url)
" 2>/dev/null) || { echo "  Apify: could not extract video URL from TikTok response." >&2; return 1; }

    download_with_curl "$video_url"
}

validate_video() {
    local path="${OUT_DIR}/video.mp4"
    if [[ ! -f "$path" ]] || [[ ! -s "$path" ]]; then
        echo "  Video file missing or empty: $path" >&2
        return 1
    fi
    local mime
    mime=$(file --mime-type -b "$path" 2>/dev/null || true)
    if [[ "$mime" == text/html ]]; then
        echo "  Downloaded file is HTML (auth wall / redirect). Download failed." >&2
        rm -f "$path"
        return 1
    fi
}

# ---- main download logic ----

echo "Downloading: ${URL:0:100}" >&2

if is_social_url "$URL"; then
    downloaded=0

    # --- try yt-dlp first (unless auth=apify) ---
    if [[ "$AUTH_MODE" != "apify" ]]; then
        if try_ytdlp_cookies; then
            if validate_video 2>/dev/null; then
                echo "yt-dlp+cookies" > "${OUT_DIR}/download_method.txt"
                echo "  Downloaded via yt-dlp + Chrome cookies." >&2
                downloaded=1
            fi
        fi
        if [[ $downloaded -eq 0 ]]; then
            echo "  yt-dlp+cookies failed, trying yt-dlp without auth..." >&2
            if try_ytdlp_no_auth 2>/dev/null && validate_video 2>/dev/null; then
                echo "yt-dlp" > "${OUT_DIR}/download_method.txt"
                downloaded=1
            fi
        fi
    fi

    # --- try Apify fallback (unless auth=cookies) ---
    if [[ $downloaded -eq 0 ]] && [[ "$AUTH_MODE" != "cookies" ]]; then
        if is_instagram "$URL"; then
            if try_apify_instagram && validate_video; then
                echo "apify" > "${OUT_DIR}/download_method.txt"
                downloaded=1
            fi
        elif is_tiktok "$URL"; then
            if try_apify_tiktok && validate_video; then
                echo "apify" > "${OUT_DIR}/download_method.txt"
                downloaded=1
            fi
        fi
    fi

    if [[ $downloaded -eq 0 ]]; then
        echo "ERROR: Could not download video." >&2
        echo "  - yt-dlp failed (are you logged in to ${COOKIE_BROWSER}?)" >&2
        echo "    Set VIDEO_ANALYZE_BROWSER=firefox|safari|edge|brave to use another browser." >&2
        if [[ -z "${APIFY_API_TOKEN:-}" ]]; then
            echo "  - APIFY_API_TOKEN not set (Apify fallback unavailable)" >&2
        fi
        exit 2
    fi
else
    # Generic URL: try yt-dlp first (handles YouTube, Twitter, etc.), then curl
    echo "  Not a social URL; trying yt-dlp then curl..." >&2
    downloaded=0

    if command -v yt-dlp &>/dev/null; then
        if try_ytdlp_no_auth 2>/dev/null && validate_video 2>/dev/null; then
            echo "yt-dlp" > "${OUT_DIR}/download_method.txt"
            downloaded=1
        fi
    fi

    if [[ $downloaded -eq 0 ]]; then
        echo "  Falling back to curl..." >&2
        curl -L --fail --max-time 300 -A "$UA" -o "${OUT_DIR}/video.mp4" "$URL" >&2 || true
        if validate_video; then
            echo "curl" > "${OUT_DIR}/download_method.txt"
            downloaded=1
        fi
    fi

    if [[ $downloaded -eq 0 ]]; then
        echo "ERROR: Could not download video from: $URL" >&2
        exit 2
    fi
fi

echo "  Download complete: $(du -h "${OUT_DIR}/video.mp4" | cut -f1)" >&2
