#!/usr/bin/env bash
# Usage: run.sh <url> [flags]
# Orchestrates the full video download + frame extraction + transcription pipeline.
# Prints <out_dir>/manifest.json path to stdout on success.

set -euo pipefail

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find a python3 that has Pillow (needed for low-fidelity grids)
PYTHON3=python3
for _py in python3 /usr/bin/python3 python3.11 python3.12; do
    if command -v "$_py" &>/dev/null && "$_py" -c "from PIL import Image" 2>/dev/null; then
        PYTHON3="$_py"
        break
    fi
done

# --- defaults ---
INTERVAL=""
MAX_FRAMES=20
FIDELITY="high"
GRID_SIZE=4
SKIP_TRANSCRIPT=0
OUT_DIR=""
AUTH_MODE="auto"
URL=""

# --- arg parsing ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --interval)        INTERVAL="$2";      shift 2;;
        --max-frames)      MAX_FRAMES="$2";    shift 2;;
        --fidelity)        FIDELITY="$2";      shift 2;;
        --grid-size)       GRID_SIZE="$2";     shift 2;;
        --skip-transcript) SKIP_TRANSCRIPT=1;  shift;;
        --out-dir)         OUT_DIR="$2";       shift 2;;
        --ig-tt-auth)      AUTH_MODE="$2";     shift 2;;
        -h|--help)
            echo "Usage: run.sh <url> [--interval N] [--max-frames N] [--fidelity high|low]"
            echo "             [--grid-size 2|3|4] [--skip-transcript] [--out-dir PATH]"
            echo "             [--ig-tt-auth auto|cookies|apify]"
            exit 0;;
        -*)  echo "Unknown flag: $1" >&2; exit 1;;
        *)   URL="$1"; shift;;
    esac
done

if [[ -z "$URL" ]]; then
    echo "Usage: run.sh <url> [flags]" >&2
    exit 1
fi

# Validate fidelity
if [[ "$FIDELITY" != "high" && "$FIDELITY" != "low" ]]; then
    echo "ERROR: --fidelity must be 'high' or 'low'" >&2; exit 1
fi

# Generate output dir
if [[ -z "$OUT_DIR" ]]; then
    # shasum is macOS/perl, sha256sum is coreutils/Linux — support both
    if command -v shasum &>/dev/null; then
        SLUG=$(printf '%s' "$URL" | shasum -a 256 | cut -c1-8)
    else
        SLUG=$(printf '%s' "$URL" | sha256sum | cut -c1-8)
    fi
    OUT_DIR="${VIDEO_ANALYZE_TMPDIR:-/tmp/video-analyze}/${SLUG}-$(date +%s)"
fi
mkdir -p "${OUT_DIR}/frames" "${OUT_DIR}/grids"

echo "=== video-analyze ===" >&2
echo "URL:     ${URL:0:100}" >&2
echo "Out dir: $OUT_DIR" >&2
echo "Fidelity: $FIDELITY  Max frames: $MAX_FRAMES  Auth: $AUTH_MODE" >&2
echo "" >&2

# --- step 1: download ---
echo "[1/4] Downloading video..." >&2
bash "$SCRIPTS/download.sh" "$URL" "$AUTH_MODE" "$OUT_DIR"

# --- step 2: compute interval + extract ---
echo "[2/4] Extracting frames and audio..." >&2

# Get duration
DURATION=$(ffprobe -v quiet -print_format json -show_format "${OUT_DIR}/video.mp4" \
    | python3 -c "import json,sys; print(float(json.load(sys.stdin)['format']['duration']))")

echo "  Video duration: ${DURATION}s" >&2

# Compute interval if not given
if [[ -z "$INTERVAL" ]]; then
    INTERVAL=$(python3 -c "
import math
d = $DURATION
if d < 30:
    iv = 2
elif d <= 60:
    iv = 5
else:
    iv = math.ceil(d / 15)
# apply max_frames cap
count = int(d / iv) + 1
if count > $MAX_FRAMES:
    iv = math.ceil(d / $MAX_FRAMES)
print(iv)
")
else
    # Still apply the max_frames cap even when interval is explicit
    INTERVAL=$(python3 -c "
import math
d = $DURATION
iv = $INTERVAL
count = int(d / iv) + 1
if count > $MAX_FRAMES:
    iv = math.ceil(d / $MAX_FRAMES)
print(iv)
")
fi

echo "  Frame interval: ${INTERVAL}s" >&2
bash "$SCRIPTS/extract.sh" "$OUT_DIR" "$INTERVAL"

# --- step 3: transcribe ---
if [[ $SKIP_TRANSCRIPT -eq 0 ]]; then
    echo "[3/4] Transcribing audio..." >&2
    bash "$SCRIPTS/transcribe.sh" "$OUT_DIR"
else
    echo "[3/4] Skipping transcription (--skip-transcript)." >&2
fi

# --- step 4: assemble manifest + grids ---
echo "[4/4] Assembling manifest..." >&2
INTERVAL_ARG=""
[[ -n "$INTERVAL" ]] && INTERVAL_ARG="--interval $INTERVAL"

"$PYTHON3" "$SCRIPTS/assemble.py" \
    --out-dir "$OUT_DIR" \
    --url "$URL" \
    --fidelity "$FIDELITY" \
    --grid-size "$GRID_SIZE" \
    --max-frames "$MAX_FRAMES" \
    $INTERVAL_ARG

echo "" >&2
echo "Done! Frame count: $(find "${OUT_DIR}/frames" -name '*.jpg' | wc -l | tr -d ' ') frames" >&2
if [[ "$FIDELITY" == "low" ]]; then
    echo "      Grid count:  $(find "${OUT_DIR}/grids" -name '*.jpg' 2>/dev/null | wc -l | tr -d ' ') grids" >&2
fi

# Print manifest path to stdout (the only stdout output)
echo "${OUT_DIR}/manifest.json"
