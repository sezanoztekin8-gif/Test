"""Metadata linting against YouTube's hard limits and widely documented practice.

Hard limits (from YouTube's own docs/API): title <= 100 chars, description
<= 5000 bytes, tags <= 500 chars total, no '<' or '>', more than 15 hashtags
makes YouTube ignore all of them, chapters need a first timestamp of 0:00,
at least 3 chapters, each at least 10 seconds long.
Everything else is a warning, not a rule.
"""

from __future__ import annotations

import re

from . import analysis

_CHAPTER = re.compile(r"^\s*[\[(]?((?:\d{1,2}:)?\d{1,2}:\d{2})[\])]?\s*[-–—:|]?\s*(.+)$")
_HASHTAG = re.compile(r"(?<!\w)#[^\s#]+", re.UNICODE)


def to_seconds(ts: str) -> int:
    parts = [int(p) for p in ts.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts
    return h * 3600 + m * 60 + s


def parse_chapters(description: str) -> list[dict]:
    out = []
    for line in description.splitlines():
        m = _CHAPTER.match(line)
        if m:
            out.append({"at": m.group(1), "seconds": to_seconds(m.group(1)), "title": m.group(2).strip()})
    return out


def check_chapters(chapters: list[dict], duration_s: int | None = None) -> list[str]:
    issues = []
    if not chapters:
        return issues
    if chapters[0]["seconds"] != 0:
        issues.append("ERROR chapters: the first timestamp must be 0:00 or YouTube ignores all chapters.")
    if len(chapters) < 3:
        issues.append("ERROR chapters: YouTube needs at least 3 timestamps to show chapters.")
    for a, b in zip(chapters, chapters[1:]):
        if b["seconds"] <= a["seconds"]:
            issues.append(f"ERROR chapters: {b['at']} is not after {a['at']} (must be ascending).")
        elif b["seconds"] - a["seconds"] < 10:
            issues.append(f"ERROR chapters: '{a['title']}' is shorter than 10 seconds.")
    if duration_s and chapters[-1]["seconds"] >= duration_s:
        issues.append("ERROR chapters: last timestamp is beyond the end of the video.")
    return issues


def lint(title: str = "", description: str = "", tags: list[str] | None = None,
         keyword: str | None = None, duration_s: int | None = None, is_short: bool = False) -> dict:
    tags = tags or []
    issues: list[str] = []
    kw = (keyword or "").lower().strip()

    # ---- title
    if title:
        f = analysis.title_features(title)
        if f["chars"] > 100:
            issues.append(f"ERROR title: {f['chars']} chars; limit is 100.")
        elif f["chars"] > 70:
            issues.append(f"WARN title: {f['chars']} chars; most surfaces truncate around 60-70. Put the hook words first.")
        elif f["chars"] < 20:
            issues.append("WARN title: very short; there may be room for a clearer promise or keyword.")
        if "<" in title or ">" in title:
            issues.append("ERROR title: '<' and '>' are not allowed.")
        if f["all_caps_words"] >= 4:
            issues.append("WARN title: many ALL-CAPS words read as spammy; emphasise 1-2 words at most.")
        if re.search(r"([!?])\1{2,}", title):
            issues.append("WARN title: repeated punctuation (!!!/???) looks low-quality.")
        if kw:
            pos = title.lower().find(kw)
            if pos < 0:
                issues.append(f"WARN title: target keyword '{keyword}' not in title (fine for browse-focused videos).")
            elif pos > 40:
                issues.append(f"WARN title: keyword appears at char {pos}; front-load it so it survives truncation.")
        if title.count("#") > 0 and not is_short:
            issues.append("INFO title: hashtags in the title replace the ones shown above it; usually keep them in the description.")
    else:
        issues.append("ERROR title: missing.")

    # ---- description
    d_bytes = len(description.encode("utf-8"))
    if d_bytes > 5000:
        issues.append(f"ERROR description: {d_bytes} bytes; limit is 5000 bytes.")
    if "<" in description or ">" in description:
        issues.append("ERROR description: '<' and '>' are not allowed.")
    if description and len(description) < 200 and not is_short:
        issues.append("WARN description: under 200 characters; add context, keywords and links for search.")
    if not description:
        issues.append("WARN description: empty.")
    if kw and description and kw not in description[:200].lower():
        issues.append(f"WARN description: keyword '{keyword}' not in the first ~200 characters (the part shown in search).")
    hashtags = _HASHTAG.findall(description)
    if len(hashtags) > 15:
        issues.append(f"ERROR description: {len(hashtags)} hashtags; above 15 YouTube ignores ALL of them.")
    elif len(hashtags) > 5:
        issues.append(f"INFO description: {len(hashtags)} hashtags; only the first 3 show above the title.")
    chapters = parse_chapters(description)
    issues += check_chapters(chapters, duration_s)
    if not chapters and duration_s and duration_s >= 480 and not is_short:
        issues.append("INFO description: no chapters on an 8+ minute video; chapters help search and key moments.")

    # ---- tags
    total = sum(len(t) + (2 if " " in t else 0) for t in tags) + max(len(tags) - 1, 0)
    if total > 500:
        issues.append(f"ERROR tags: ~{total} chars; limit is 500.")
    lower = [t.lower().strip() for t in tags]
    dups = sorted({t for t in lower if lower.count(t) > 1})
    if dups:
        issues.append(f"WARN tags: duplicates {dups}.")
    if kw and tags and kw not in lower:
        issues.append(f"INFO tags: exact keyword '{keyword}' not tagged (tags are a minor signal, mostly for misspellings).")

    errors = sum(1 for i in issues if i.startswith("ERROR"))
    warns = sum(1 for i in issues if i.startswith("WARN"))
    return {
        "score": max(0, 100 - errors * 20 - warns * 6),
        "errors": errors,
        "warnings": warns,
        "issues": issues,
        "stats": {
            "title_chars": len(title),
            "description_chars": len(description),
            "description_bytes": d_bytes,
            "tags": len(tags),
            "tag_chars": total,
            "hashtags": hashtags[:20],
            "chapters": chapters,
        },
    }
