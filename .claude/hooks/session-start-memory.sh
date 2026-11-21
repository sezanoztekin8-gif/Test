#!/bin/bash
# SessionStart: put the most important project memories into Claude's context.
[ -n "$MEMORY_HOOK" ] && exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
echo "Project memory (top entries, .claude/memory/memory.jsonl):"
python3 .claude/memory/memory.py top 15 2>/dev/null
ls -1t .claude/sessions/*.md 2>/dev/null | head -1 | sed 's/^/Last session summary: /'
exit 0
