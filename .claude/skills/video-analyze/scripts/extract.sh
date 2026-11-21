#!/usr/bin/env bash
# Usage: extract.sh <out_dir> <interval_sec>
# Extracts frames at the given interval and audio from video.mp4.
# Writes frames/NNNN.jpg, audio.mp3, duration.txt.

set -euo pipefail

OUT_DIR="$1"
INTERVAL="$2"

VIDEO="${OUT_DIR}/video.mp4"

if [[ ! -f "$VIDEO" ]]; then
    echo "ERROR: video.mp4 not found in $OUT_DIR" >&2
    exit 3
fi

mkdir -p "${OUT_DIR}/frames"

# --- get duration ---
DURATION=$(ffprobe -v quiet -print_format json -show_format "$VIDEO" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(float(d['format']['duration']))")
echo "$DURATION" > "${OUT_DIR}/duration.txt"
echo "  Duration: ${DURATION}s" >&2

# --- extract frames ---
echo "  Extracting frames every ${INTERVAL}s..." >&2
ffmpeg -y -i "$VIDEO" \
    -vf "fps=1/${INTERVAL}" \
    -q:v 3 \
    "${OUT_DIR}/frames/%04d.jpg" \
    -loglevel error

FRAME_COUNT=$(find "${OUT_DIR}/frames" -name "*.jpg" | wc -l | tr -d ' ')
echo "  Extracted ${FRAME_COUNT} frames." >&2

# --- extract audio ---
echo "  Extracting audio..." >&2
ffmpeg -y -i "$VIDEO" \
    -vn -acodec libmp3lame -q:a 4 \
    "${OUT_DIR}/audio.mp3" \
    -loglevel error
echo "  Audio extracted: $(du -h "${OUT_DIR}/audio.mp3" | cut -f1)" >&2
