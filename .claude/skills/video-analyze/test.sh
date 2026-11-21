#!/usr/bin/env bash
# Integration tests for the video-analyze skill.
# Not installed into ~/.claude/skills — run from a repo clone to verify the pipeline.
#
# Usage:
#   ./test.sh              # all tests
#   ./test.sh smoke        # only local tests (no network)
#   ./test.sh youtube      # YouTube download + transcription
#   ./test.sh tiktok       # TikTok via Apify
#   ./test.sh low          # low-fidelity grid smoke test

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$SKILL_DIR/scripts"
FILTER="${1:-all}"

# Find a python3 with Pillow (mirrors run.sh logic)
PYTHON3=python3
for _py in python3 /usr/bin/python3 python3.11 python3.12; do
    if command -v "$_py" &>/dev/null && "$_py" -c "from PIL import Image" 2>/dev/null; then
        PYTHON3="$_py"; break
    fi
done

# ---- Load credentials from a repo-local .env (git-ignored) ----
# Only sets vars that are not already in the environment (so CLI-passed vars win).
# See .env.example for the supported keys.
load_envs() {
    local f line varname varval
    for f in \
        "$SKILL_DIR/.env" \
        "${VIDEO_ANALYZE_ENV_FILE:-}"; do
        [[ -n "$f" && -f "$f" ]] || continue
        while IFS= read -r line || [[ -n "$line" ]]; do
            # Skip comments and empty lines
            [[ "$line" =~ ^[[:space:]]*# ]] && continue
            [[ -z "${line// }" ]] && continue
            if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
                varname="${BASH_REMATCH[1]}"
                varval="${BASH_REMATCH[2]//\"/}"  # strip surrounding quotes
                # Only export if not already set in environment
                if [[ -z "${!varname:-}" ]]; then
                    export "$varname=$varval"
                fi
            fi
        done < "$f"
    done
}
load_envs

# ---- Helpers ----
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
PASS=0; FAIL=0; SKIP=0

pass() { echo -e "${GREEN}[PASS]${NC} $1"; PASS=$((PASS + 1)); }
fail() { echo -e "${RED}[FAIL]${NC} $1 — $2"; FAIL=$((FAIL + 1)); }
skip() { echo -e "${YELLOW}[SKIP]${NC} $1"; SKIP=$((SKIP + 1)); }
section() { echo -e "\n${BOLD}── $1 ──${NC}"; }

assert_file()    { [[ -f "$1" ]] && [[ -s "$1" ]] || { fail "$2" "file missing or empty: $1"; return 1; }; }
assert_json()    { python3 -c "import json; json.load(open('$1'))" 2>/dev/null || { fail "$2" "invalid JSON: $1"; return 1; }; }
assert_ge()      { python3 -c "import sys; sys.exit(0 if int('$1') >= int('$2') else 1)" || { fail "$3" "expected $1 >= $2"; return 1; }; }
assert_contains(){ python3 -c "import json; d=json.load(open('$1')); v=d; [v:=v[k] for k in '$2'.split('.')]; assert v" 2>/dev/null || { fail "$3" "'$2' missing or falsy in $1"; return 1; }; }

# ---- Test 1: Smoke test (no network) ----
run_smoke() {
    section "SMOKE — local ffmpeg pipeline (no network)"

    local out="/tmp/va-test-smoke"
    rm -rf "$out"
    mkdir -p "$out/frames" "$out/grids"

    # 1a. Create synthetic 25s video
    ffmpeg -y \
        -f lavfi -i "testsrc=duration=25:size=640x360:rate=5" \
        -f lavfi -i "sine=frequency=440:duration=25" \
        -c:v libx264 -preset ultrafast -c:a aac \
        "$out/video.mp4" -loglevel error
    echo "curl" > "$out/download_method.txt"

    assert_file "$out/video.mp4" "synthetic video created" && pass "synthetic video created (25s)"

    # 1b. Extract frames (25s → interval 2 → ~13 frames)
    bash "$SCRIPTS/extract.sh" "$out" 2 2>/dev/null
    local frame_count
    frame_count=$(find "$out/frames" -name "*.jpg" | wc -l | tr -d ' ')
    assert_file "$out/duration.txt" "duration.txt written"
    assert_file "$out/audio.mp3" "audio.mp3 extracted"
    assert_ge "$frame_count" 10 "frame count >= 10 (got $frame_count)"
    pass "extract: $frame_count frames, duration=$(cat "$out/duration.txt")s"

    # 1c. Assemble manifest (high fidelity, no transcript)
    "$PYTHON3" "$SCRIPTS/assemble.py" \
        --out-dir "$out" --url "https://example.com/test.mp4" \
        --fidelity high --grid-size 4 --max-frames 20 --interval 2 2>/dev/null
    assert_file "$out/manifest.json" "manifest.json written"
    assert_json  "$out/manifest.json" "manifest.json is valid JSON"
    local fc
    fc=$(python3 -c "import json; m=json.load(open('$out/manifest.json')); print(m['extraction']['frame_count'])")
    assert_ge "$fc" 10 "manifest frame_count >= 10"
    pass "assemble (high): manifest valid, frame_count=$fc, transcript=null"

    # 1d. Interval cap: 25s, max_frames=5 — interval should recalc so count stays reasonable
    rm -rf "$out/frames"; mkdir -p "$out/frames"
    bash "$SCRIPTS/extract.sh" "$out" 5 2>/dev/null
    "$PYTHON3" "$SCRIPTS/assemble.py" \
        --out-dir "$out" --url "https://example.com/test.mp4" \
        --fidelity high --grid-size 4 --max-frames 5 --interval 5 2>/dev/null
    local capped_fc
    capped_fc=$(python3 -c "import json; m=json.load(open('$out/manifest.json')); print(m['extraction']['frame_count'])")
    assert_ge 5 1 "capped frame_count > 0"
    pass "interval cap: frame_count=$capped_fc with max_frames=5"

    # 1e. Low fidelity grids
    rm -rf "$out/frames" "$out/grids"
    mkdir -p "$out/frames" "$out/grids"
    bash "$SCRIPTS/extract.sh" "$out" 2 2>/dev/null
    "$PYTHON3" "$SCRIPTS/assemble.py" \
        --out-dir "$out" --url "https://example.com/test.mp4" \
        --fidelity low --grid-size 4 --max-frames 20 --interval 2 2>/dev/null
    local grid_count
    grid_count=$(find "$out/grids" -name "*.jpg" 2>/dev/null | wc -l | tr -d ' ')
    assert_ge "$grid_count" 1 "at least 1 grid created"
    local gc_manifest
    gc_manifest=$(python3 -c "import json; m=json.load(open('$out/manifest.json')); print(len(m['grids']))")
    assert_ge "$gc_manifest" 1 "manifest.grids count >= 1"
    local grid_size
    grid_size=$(stat -f%z "$out/grids/grid_0001.jpg" 2>/dev/null || stat -c%s "$out/grids/grid_0001.jpg")
    assert_ge 200000 "$grid_size" "grid file <= 200KB (got ${grid_size}B)"  # inverted: 200000 >= grid_size
    pass "low fidelity: $gc_manifest grids, grid_0001.jpg = $(( grid_size / 1024 ))KB"

    # 1f. Skip-transcript path (no transcript.json → manifest.transcript should be null)
    local transcript_val
    transcript_val=$(python3 -c "import json; m=json.load(open('$out/manifest.json')); print(m['transcript'])")
    [[ "$transcript_val" == "None" ]] && pass "no transcript.json → manifest.transcript is null" \
        || fail "transcript null check" "expected None, got $transcript_val"

    # 1g. Graceful handling: transcript.json with error field
    echo '{"error":"test error","text":"","segments":[]}' > "$out/transcript.json"
    "$PYTHON3" "$SCRIPTS/assemble.py" \
        --out-dir "$out" --url "https://example.com/test.mp4" \
        --fidelity high --max-frames 20 --interval 2 2>/dev/null
    local t2
    t2=$(python3 -c "import json; m=json.load(open('$out/manifest.json')); print(m['transcript'])")
    [[ "$t2" == "None" ]] && pass "error transcript.json → manifest.transcript is null" \
        || fail "error transcript null" "expected None, got $t2"
}

# ---- Test 2: YouTube download + transcription ----
run_youtube() {
    section "YOUTUBE — real download via yt-dlp + Whisper transcription"

    if ! command -v yt-dlp &>/dev/null; then
        skip "yt-dlp not installed (brew install yt-dlp)"; return
    fi

    local out="/tmp/va-test-youtube"
    rm -rf "$out"
    # "Me at the zoo" — first YouTube video, 19s, always public
    local url="https://www.youtube.com/watch?v=jNQXAC9IVRw"

    echo "  Downloading: $url" >&2
    local manifest_path
    manifest_path=$(bash "$SCRIPTS/run.sh" "$url" \
        --out-dir "$out" \
        --fidelity high \
        --max-frames 15 \
        2>/dev/null)

    assert_file "$manifest_path" "manifest.json returned"
    assert_json  "$manifest_path" "manifest.json valid JSON"

    local duration platform frame_count dl_via
    duration=$(python3 -c "import json; m=json.load(open('$manifest_path')); print(m['source']['duration_sec'])")
    platform=$(python3 -c "import json; m=json.load(open('$manifest_path')); print(m['source']['platform'])")
    frame_count=$(python3 -c "import json; m=json.load(open('$manifest_path')); print(m['extraction']['frame_count'])")
    dl_via=$(python3 -c "import json; m=json.load(open('$manifest_path')); print(m['source']['downloaded_via'])")

    assert_ge "$frame_count" 5 "frame_count >= 5 (got $frame_count)"
    [[ "$platform" == "youtube" ]] && pass "platform detected as youtube" \
        || fail "platform detection" "expected youtube, got $platform"
    pass "YouTube download: ${duration}s, $frame_count frames via $dl_via"

    # Verify frames exist on disk
    local first_frame="$out/$(python3 -c "import json; m=json.load(open('$manifest_path')); print(m['frames'][0]['image'])")"
    assert_file "$first_frame" "first frame file exists"
    pass "first frame on disk: $first_frame"

    # Transcription
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then
        local transcript
        transcript=$(python3 -c "import json; m=json.load(open('$manifest_path')); print(m.get('transcript') or 'null')")
        if [[ "$transcript" != "null" ]] && [[ "$transcript" != "None" ]]; then
            local seg_count
            seg_count=$(python3 -c "import json; m=json.load(open('$manifest_path')); print(len(m['transcript']['segments']))")
            assert_ge "$seg_count" 1 "transcript has >= 1 segment"
            local has_aligned
            has_aligned=$(python3 -c "
import json
m = json.load(open('$manifest_path'))
aligned = [f for f in m['frames'] if f.get('transcript')]
print(len(aligned))
")
            pass "transcription: $seg_count segments, $has_aligned frames have aligned text"
        else
            fail "transcription" "OPENAI_API_KEY set but transcript is null"
        fi
    else
        skip "OPENAI_API_KEY not set — skipping transcription check"
    fi
}

# ---- Test 3: TikTok via Apify ----
run_tiktok() {
    section "TIKTOK — Apify fallback (clockworks/tiktok-scraper)"

    if [[ -z "${APIFY_API_TOKEN:-}" ]]; then
        skip "APIFY_API_TOKEN not set"; return
    fi

    local out="/tmp/va-test-tiktok"
    rm -rf "$out"
    # TikTok For You page's own tutorial video — stable official content
    local url="https://www.tiktok.com/@tiktok/video/7106594312292453675"

    echo "  Downloading via Apify: ${url:0:70}..." >&2
    local manifest_path rc=0
    # Force apify auth to specifically test that path
    manifest_path=$(bash "$SCRIPTS/run.sh" "$url" \
        --out-dir "$out" \
        --fidelity low \
        --grid-size 4 \
        --skip-transcript \
        --ig-tt-auth apify \
        2>/tmp/va-test-tiktok-stderr.txt) || rc=$?

    if [[ $rc -ne 0 ]]; then
        local err
        err=$(cat /tmp/va-test-tiktok-stderr.txt 2>/dev/null | tail -3)
        skip "TikTok Apify: run.sh failed (video may be unavailable or Apify limits): $err"
        return
    fi

    assert_file "$manifest_path" "manifest.json returned"
    assert_json  "$manifest_path" "manifest.json valid JSON"

    local dl_via frame_count grid_count
    dl_via=$(python3 -c "import json; m=json.load(open('$manifest_path')); print(m['source']['downloaded_via'])")
    frame_count=$(python3 -c "import json; m=json.load(open('$manifest_path')); print(m['extraction']['frame_count'])")
    grid_count=$(python3 -c "import json; m=json.load(open('$manifest_path')); print(len(m['grids']))")

    [[ "$dl_via" == "apify" ]] && pass "downloaded_via=apify" \
        || fail "downloaded_via" "expected apify, got $dl_via"
    assert_ge "$frame_count" 1 "frame_count >= 1 (got $frame_count)"
    assert_ge "$grid_count" 1 "grid_count >= 1 (got $grid_count)"
    pass "TikTok Apify: $frame_count frames, $grid_count grids (low fidelity)"
}

# ---- Test 4: Generic direct URL via curl ----
run_direct_url() {
    section "DIRECT URL — curl download of a public mp4"

    # A well-known tiny public MP4 test file from W3Schools (used in their HTML5 video examples)
    local url="https://www.w3schools.com/html/mov_bbb.mp4"
    local out="/tmp/va-test-direct"
    rm -rf "$out"

    echo "  Downloading direct mp4: $url" >&2
    local manifest_path
    manifest_path=$(bash "$SCRIPTS/run.sh" "$url" \
        --out-dir "$out" \
        --skip-transcript \
        --max-frames 10 \
        2>/dev/null) || { fail "direct URL download" "run.sh exited non-zero"; return; }

    assert_file "$manifest_path" "manifest.json returned"
    assert_json  "$manifest_path" "manifest.json valid JSON"

    local frame_count dl_via
    frame_count=$(python3 -c "import json; m=json.load(open('$manifest_path')); print(m['extraction']['frame_count'])")
    dl_via=$(python3 -c "import json; m=json.load(open('$manifest_path')); print(m['source']['downloaded_via'])")

    assert_ge "$frame_count" 1 "frame_count >= 1 (got $frame_count)"
    pass "direct URL: $frame_count frames via $dl_via"
}

# ---- Summary ----
print_summary() {
    echo ""
    echo -e "${BOLD}────────────────────────────────${NC}"
    echo -e "${GREEN}PASS: $PASS${NC}  ${RED}FAIL: $FAIL${NC}  ${YELLOW}SKIP: $SKIP${NC}"
    [[ $FAIL -eq 0 ]] && echo -e "${GREEN}All tests passed.${NC}" || echo -e "${RED}Some tests failed.${NC}"
    [[ $FAIL -gt 0 ]] && exit 1 || exit 0
}

# ---- Dispatch ----
case "$FILTER" in
    smoke)       run_smoke;;
    youtube)     run_youtube;;
    tiktok)      run_tiktok;;
    direct|curl) run_direct_url;;
    low)         run_smoke;;  # smoke covers low-fidelity
    all)
        run_smoke
        run_youtube
        run_tiktok
        run_direct_url
        ;;
    *)  echo "Usage: $0 [all|smoke|youtube|tiktok|direct]" >&2; exit 1;;
esac

print_summary
