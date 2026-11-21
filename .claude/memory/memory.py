"""Project memory: .claude/memory/memory.jsonl (one JSON object per line, schema line anywhere).

  python3 .claude/memory/memory.py top [N] [--types pattern,decision] [--min 0.7]   # best memories first
  python3 .claude/memory/memory.py add <type> <key> "<value>" "<context>" <importance>
Types: preference, decision, pattern, fact. A newer entry with the same key replaces older ones in `top`.
"""
import json, math, os, sys
from datetime import datetime, timezone

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memory.jsonl')


def load_memories(path=PATH, types=None, min_importance=0.0):
    memories = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = json.loads(line)
            if 'schema' in m:          # schema line, wherever it is
                continue
            if types and m['type'] not in types:
                continue
            if m.get('importance', 1.0) < min_importance:
                continue
            memories.append(m)
    latest = {}                        # newest entry per key wins
    for m in sorted(memories, key=lambda m: m['ts']):
        latest[m['key']] = m
    return list(latest.values())


def score_memory(memory, now=None):
    """Score = importance * recency decay (half-life about 69 days)."""
    now = now or datetime.now(timezone.utc)
    ts = datetime.fromisoformat(memory['ts'].replace('Z', '+00:00'))
    age_days = max(0.0, (now - ts).total_seconds() / 86400)
    return memory.get('importance', 0.7) * math.exp(-0.01 * age_days)


def main(argv):
    if not argv or argv[0] == 'top':
        n = int(argv[1]) if len(argv) > 1 and argv[1].isdigit() else 20
        types = argv[argv.index('--types') + 1].split(',') if '--types' in argv else None
        mn = float(argv[argv.index('--min') + 1]) if '--min' in argv else 0.0
        for m in sorted(load_memories(types=types, min_importance=mn), key=score_memory, reverse=True)[:n]:
            print(f"[{m['type']}] {m['key']} ({score_memory(m):.2f}): {m['value']}")
    elif argv[0] == 'add' and len(argv) == 6:
        _, t, key, value, context, imp = argv
        row = {'ts': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'type': t, 'key': key,
               'value': value, 'context': context, 'importance': float(imp)}
        with open(PATH, 'a') as f:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
        print('added', key)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
