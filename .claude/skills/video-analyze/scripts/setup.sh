#!/usr/bin/env bash
# Usage: setup.sh check
# Prints READY if all tools present, or NEEDS_SETUP: <missing> if not.

set -euo pipefail

hint() {
    echo "" >&2
    echo "Install the missing tools:" >&2
    if [[ "$(uname -s)" == "Darwin" ]]; then
        echo "  brew install ffmpeg yt-dlp" >&2
        echo "  python3 -m pip install --user pillow" >&2
    else
        echo "  sudo apt install ffmpeg python3-pil   # Debian/Ubuntu" >&2
        echo "  python3 -m pip install --user yt-dlp pillow" >&2
    fi
}

check() {
    local missing=()
    for tool in ffmpeg ffprobe yt-dlp curl; do
        if ! command -v "$tool" &>/dev/null; then
            missing+=("$tool")
        fi
    done

    # Check for Pillow (needed for low-fidelity grids)
    local pil_ok=0
    for py in python3 /usr/bin/python3; do
        if command -v "$py" &>/dev/null && "$py" -c "from PIL import Image" 2>/dev/null; then
            pil_ok=1; break
        fi
    done
    [[ $pil_ok -eq 0 ]] && missing+=("python-pillow")

    if [[ ${#missing[@]} -eq 0 ]]; then
        echo "READY: ffmpeg=$(ffmpeg -version 2>&1 | head -1 | awk '{print $3}') yt-dlp=$(yt-dlp --version 2>/dev/null || echo 'ok') curl=ok pillow=ok"
        exit 0
    fi

    echo "NEEDS_SETUP: ${missing[*]}"
    hint
    exit 1
}

case "${1:-check}" in
    check) check;;
    *) echo "Usage: setup.sh check" >&2; exit 1;;
esac
