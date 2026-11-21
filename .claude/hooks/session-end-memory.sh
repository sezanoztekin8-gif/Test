#!/bin/bash
# SessionEnd: ask a small model to pull learnings out of this session's transcript and append them
# to .claude/memory/memory.jsonl. MEMORY_HOOK stops the child `claude -p` from running hooks again.
[ -n "$MEMORY_HOOK" ] && exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
LOG=.claude/memory/hook.log
INPUT=$(cat)
TRANSCRIPT=$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
[ -f "$TRANSCRIPT" ] || { echo "$(date -u +%FT%TZ) no transcript" >> "$LOG"; exit 0; }
EXCERPT=$(python3 - "$TRANSCRIPT" <<'PY'
import json, sys
out = []
for line in open(sys.argv[1], errors='ignore'):
    try: e = json.loads(line)
    except Exception: continue
    m = e.get('message') or {}
    role = m.get('role') or e.get('type')
    if role not in ('user', 'assistant'): continue
    c = m.get('content')
    if isinstance(c, list):
        c = ' '.join(p.get('text', '') for p in c if isinstance(p, dict) and p.get('type') == 'text')
    if isinstance(c, str) and c.strip():
        out.append(f"{role.upper()}: {c.strip()[:1500]}")
print('\n'.join(out)[-30000:])
PY
)
[ -n "$EXCERPT" ] || exit 0
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
PROMPT="Below is the end of a Claude Code session in this video-studio project. Extract only durable learnings: debugging patterns, project facts, user preferences, decisions. Skip anything already obvious or one-off. Output ONLY JSON lines, nothing else, each exactly:
{\"ts\": \"$NOW\", \"type\": \"pattern|fact|preference|decision\", \"key\": \"short_snake_key\", \"value\": \"what to remember\", \"context\": \"brief context\", \"importance\": 0.0-1.0}
Never include API keys, tokens, passwords or personal contact details. Output nothing if there is nothing worth keeping."
RESULT=$(printf '%s' "$EXCERPT" | MEMORY_HOOK=1 timeout 150 claude -p --model haiku --no-session-persistence "$PROMPT" 2>>"$LOG")
printf '%s\n' "$RESULT" | python3 -c '
import json, sys
ok = 0
with open(".claude/memory/memory.jsonl", "a") as f:
    for line in sys.stdin:
        line = line.strip()
        if not line.startswith("{"): continue
        try: m = json.loads(line)
        except Exception: continue
        if not all(k in m for k in ("ts", "type", "key", "value", "importance")): continue
        if m["type"] not in ("pattern", "fact", "preference", "decision"): continue
        f.write(json.dumps(m, ensure_ascii=False) + "\n"); ok += 1
print(ok)' > /tmp/memory-hook-count 2>>"$LOG"
echo "$(date -u +%FT%TZ) added $(cat /tmp/memory-hook-count 2>/dev/null) memories" >> "$LOG"
exit 0
