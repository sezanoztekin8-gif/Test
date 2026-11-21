#!/usr/bin/env bash
# Usage: transcribe.sh <out_dir>
# Calls OpenAI Whisper API to transcribe audio.mp3.
# Writes transcript.json. Exits 0 even on failure (pipeline continues).

set -euo pipefail

OUT_DIR="$1"
AUDIO="${OUT_DIR}/audio.mp3"
TRANSCRIPT="${OUT_DIR}/transcript.json"

if [[ ! -f "$AUDIO" ]]; then
    echo "  No audio file found, skipping transcription." >&2
    echo '{"error":"no audio file","text":"","segments":[]}' > "$TRANSCRIPT"
    exit 0
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "  OPENAI_API_KEY not set, skipping transcription." >&2
    echo '{"error":"OPENAI_API_KEY not set","text":"","segments":[]}' > "$TRANSCRIPT"
    exit 0
fi

# Point at any OpenAI-compatible transcription endpoint (e.g. a local
# faster-whisper server) by setting OPENAI_BASE_URL / WHISPER_MODEL.
BASE_URL="${OPENAI_BASE_URL:-https://api.openai.com/v1}"
MODEL="${WHISPER_MODEL:-whisper-1}"

echo "  Calling Whisper API (${MODEL})..." >&2
HTTP_CODE=$(curl -s -o "$TRANSCRIPT" -w "%{http_code}" \
    "${BASE_URL%/}/audio/transcriptions" \
    -H "Authorization: Bearer ${OPENAI_API_KEY}" \
    -F "file=@${AUDIO};type=audio/mpeg" \
    -F "model=${MODEL}" \
    -F "response_format=verbose_json" \
    -F "timestamp_granularities[]=segment")

if [[ "$HTTP_CODE" != "200" ]]; then
    ERR_BODY=$(head -c 500 "$TRANSCRIPT" 2>/dev/null || echo "unknown error")
    echo "  Whisper API returned HTTP $HTTP_CODE: $ERR_BODY" >&2
    echo "{\"error\":\"Whisper API HTTP $HTTP_CODE\",\"text\":\"\",\"segments\":[]}" > "$TRANSCRIPT"
    exit 0
fi

SEGMENT_COUNT=$(python3 -c "
import json, sys
d = json.load(open('${TRANSCRIPT}'))
print(len(d.get('segments', [])))
" 2>/dev/null || echo "?")
echo "  Transcription done: ${SEGMENT_COUNT} segments." >&2
