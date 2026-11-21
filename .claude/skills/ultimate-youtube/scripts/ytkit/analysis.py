"""Pure, network-free analysis. Everything here is unit-tested.

Key ideas (combined from the source projects, see NOTICE.md):

* Outlier ratio  - views / median views of the same channel and the same
  format (Shorts are compared with Shorts, long-form with long-form).
* Neighbour ratio - views / median of the N uploads published closest in
  time (same format). This corrects for channel growth and video age, so an
  old video is not called a hit just because it had years to collect views.
* A video is an outlier when its neighbour ratio >= threshold (default 2x)
  and it is old enough for the number to mean something.
* Views-per-subscriber - a cross-channel signal used for search results,
  where there is no per-channel baseline.

Tokenisation splits on whitespace and punctuation only, so title and tag
analysis works for any language and script, not just English.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from . import util

SHORTS_MAX_SECONDS = 180  # YouTube allows Shorts up to 3 minutes (since Oct 2024)

_SPLIT = re.compile(r"[\s|/\\\-–—:;,.!?¿¡()\[\]{}\"'“”‘’«»#@&+*=<>~^`…।॥、。，！？]+", re.UNICODE)
_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U0001F900-\U0001F9FF]",
    re.UNICODE,
)
_NUMBER = re.compile(r"\d")
_TIMESTAMP = re.compile(r"\b(\d{1,2}:)?\d{1,2}:\d{2}\b")

STOPWORDS = set(
    """a an the and or but if of in on at to for from by with without about into over under
    is are was were be been being am do does did doing have has had having it its this that
    these those i me my we our you your he she they them their his her him what which who whom
    how why when where not no nor so than too very can will just should now vs via up out all
    any more most some such only own same s t don ll ve re d m o y amp""".split()
)


# ---------------------------------------------------------------- basics

def is_short(video: dict, threshold: int = SHORTS_MAX_SECONDS) -> bool:
    if video.get("is_short") is not None:
        return bool(video["is_short"])
    dur = video.get("duration_s") or 0
    return 0 < dur <= threshold


def video_format(video: dict) -> str:
    if video.get("was_live"):
        return "live"
    return "short" if is_short(video) else "long"


def enrich(video: dict, subscribers: int | None = None, now: datetime | None = None) -> dict:
    """Add rate metrics to a normalized video dict (returns a new dict)."""
    v = dict(video)
    views = v.get("views") or 0
    age = util.age_days(v.get("published_at"), now)
    v["age_days"] = round(age, 1)
    v["views_per_day"] = round(views / max(age, 1.0), 1)
    v["engagement_rate"] = round(((v.get("likes") or 0) + (v.get("comments") or 0)) / views * 100, 2) if views else 0.0
    v["like_rate"] = round((v.get("likes") or 0) / views * 100, 2) if views else 0.0
    v["comment_rate"] = round((v.get("comments") or 0) / views * 1000, 2) if views else 0.0  # per 1k views
    v["format"] = video_format(v)
    if subscribers:
        v["views_per_sub"] = round(views / subscribers, 2)
    return v


def score_outliers(
    videos: list[dict],
    threshold: float = 2.0,
    neighbours: int = 10,
    min_age_days: float = 3.0,
) -> list[dict]:
    """Add outlier_ratio, neighbour_ratio and is_outlier, per format. Returns new list."""
    out = [dict(v) for v in videos]
    by_format: dict[str, list[dict]] = {}
    for v in out:
        by_format.setdefault(v.get("format") or video_format(v), []).append(v)

    for group in by_format.values():
        mature = [v for v in group if (v.get("age_days") or 0) >= min_age_days]
        base = util.median(v["views"] for v in mature) or util.median(v["views"] for v in group)
        ordered = sorted(group, key=lambda v: v.get("published_at") or "")
        for idx, v in enumerate(ordered):
            v["outlier_ratio"] = round(v["views"] / base, 2) if base else 0.0
            lo = max(0, idx - neighbours // 2)
            hi = min(len(ordered), lo + neighbours + 1)
            lo = max(0, hi - neighbours - 1)
            peers = [p["views"] for j, p in enumerate(ordered[lo:hi], start=lo) if j != idx]
            peer_median = util.median(peers)
            v["neighbour_median"] = int(peer_median)
            v["neighbour_ratio"] = round(v["views"] / peer_median, 2) if peer_median else 0.0
            old_enough = (v.get("age_days") or 0) >= min_age_days
            v["is_outlier"] = bool(old_enough and v["neighbour_ratio"] >= threshold and len(group) >= 3)
            v["is_underperformer"] = bool(old_enough and peer_median and v["neighbour_ratio"] <= 0.5)
    return out


def format_split(videos: list[dict]) -> dict:
    out = {}
    for fmt in ("long", "short", "live"):
        group = [v for v in videos if v.get("format") == fmt]
        if not group:
            continue
        out[fmt] = {
            "count": len(group),
            "median_views": int(util.median(v["views"] for v in group)),
            "median_views_per_day": round(util.median(v.get("views_per_day", 0) for v in group), 1),
            "median_duration": util.hms(util.median(v.get("duration_s", 0) for v in group)),
            "median_engagement_rate": round(util.median(v.get("engagement_rate", 0) for v in group), 2),
            "outliers": sum(1 for v in group if v.get("is_outlier")),
        }
    return out


# ---------------------------------------------------------------- cadence

def cadence(videos: list[dict], tz_offset_hours: float = 0.0) -> dict:
    times = sorted(t for t in (util.parse_time(v.get("published_at")) for v in videos) if t)
    if len(times) < 2:
        return {"uploads": len(times)}
    shift = timedelta(hours=tz_offset_hours)
    gaps = [(b - a).total_seconds() / 86400 for a, b in zip(times, times[1:])]
    span_days = max((times[-1] - times[0]).total_seconds() / 86400, 1)
    weekdays = Counter((t + shift).strftime("%a") for t in times)
    hours = Counter((t + shift).hour for t in times)
    recent_cut = times[-1] - timedelta(days=30)
    return {
        "uploads": len(times),
        "first": times[0].isoformat(),
        "last": times[-1].isoformat(),
        "uploads_per_week": round(len(times) / span_days * 7, 2),
        "uploads_last_30d": sum(1 for t in times if t >= recent_cut),
        "median_gap_days": round(util.median(gaps), 1),
        "longest_gap_days": round(max(gaps), 1),
        "days_since_last_upload": round(util.age_days(times[-1].isoformat()), 1),
        "timezone_offset_hours": tz_offset_hours,
        "by_weekday": dict(weekdays.most_common()),
        "by_hour": {f"{h:02d}:00": c for h, c in sorted(hours.items())},
        "top_slot": f"{weekdays.most_common(1)[0][0]} ~{hours.most_common(1)[0][0]:02d}:00",
    }


# ---------------------------------------------------------------- titles & tags

def tokens(text: str) -> list[str]:
    return [t for t in _SPLIT.split(text.lower()) if t and not t.isdigit()]


def title_features(title: str) -> dict:
    words = [w for w in title.split() if w]
    latin = [w for w in words if re.search(r"[A-Za-z]", w)]
    caps = [w for w in latin if len(w) > 1 and w.isupper()]
    return {
        "chars": len(title),
        "words": len(words),
        "has_number": bool(_NUMBER.search(title)),
        "starts_with_number": bool(re.match(r"^\s*\d", title)),
        "has_question": "?" in title,
        "has_exclamation": "!" in title,
        "has_brackets": bool(re.search(r"[\(\[\{]", title)),
        "has_separator": bool(re.search(r"[|:\-–—]", title)),
        "has_emoji": bool(_EMOJI.search(title)),
        "has_hashtag": "#" in title,
        "all_caps_words": len(caps),
        "addresses_viewer": bool(re.search(r"\b(you|your|you're)\b", title, re.I)),
        "first_person": bool(re.search(r"\b(i|i'm|my|we|our)\b", title, re.I)),
        "truncation_risk": len(title) > 60,
    }


def title_patterns(videos: list[dict]) -> dict:
    """Which title features show up more often in outliers than in the rest."""
    if not videos:
        return {}
    feats = [(title_features(v["title"]), v.get("is_outlier", False)) for v in videos]
    keys = [k for k in feats[0][0] if isinstance(feats[0][0][k], bool)]
    outliers = [f for f, o in feats if o]
    rest = [f for f, o in feats if not o]

    def share(group, key):
        return round(sum(1 for f in group if f[key]) / len(group) * 100) if group else None

    rows = {k: {"all_pct": share([f for f, _ in feats], k), "outliers_pct": share(outliers, k), "others_pct": share(rest, k)} for k in keys}
    return {
        "median_title_chars": int(util.median(f["chars"] for f, _ in feats)),
        "median_title_chars_outliers": int(util.median(f["chars"] for f in outliers)) if outliers else None,
        "features": rows,
    }


def ngrams(texts: list[str], n: int = 1, top: int = 25, stop: set[str] = STOPWORDS) -> list[tuple[str, int]]:
    counts: Counter = Counter()
    for text in texts:
        toks = [t for t in tokens(text) if t not in stop and len(t) > 1]
        grams = toks if n == 1 else [" ".join(toks[i : i + n]) for i in range(len(toks) - n + 1)]
        counts.update(set(grams))  # document frequency: once per title
    return [(g, c) for g, c in counts.most_common(top) if c > 1]


def top_tags(videos: list[dict], top: int = 30) -> list[tuple[str, int]]:
    counts: Counter = Counter()
    for v in videos:
        counts.update({t.strip().lower() for t in v.get("tags", []) if t.strip()})
    return counts.most_common(top)


def topic_lift(videos: list[dict], top: int = 15, min_count: int = 2) -> list[dict]:
    """Words whose videos beat the channel's median - a rough 'what topics win' signal."""
    groups: dict[str, list[float]] = {}
    for v in videos:
        ratio = v.get("neighbour_ratio") or v.get("outlier_ratio")
        if not ratio:
            continue
        for tok in set(t for t in tokens(v["title"]) if t not in STOPWORDS and len(t) > 2):
            groups.setdefault(tok, []).append(ratio)
    rows = [
        {"term": t, "videos": len(r), "median_ratio": round(util.median(r), 2)}
        for t, r in groups.items()
        if len(r) >= min_count
    ]
    rows.sort(key=lambda r: (r["median_ratio"], r["videos"]), reverse=True)
    return rows[:top]


def length_buckets(videos: list[dict]) -> list[dict]:
    edges = [(0, 60, "<1m"), (60, 180, "1-3m"), (180, 480, "3-8m"), (480, 900, "8-15m"),
             (900, 1500, "15-25m"), (1500, 2700, "25-45m"), (2700, 10**9, "45m+")]
    rows = []
    for lo, hi, label in edges:
        group = [v for v in videos if lo < (v.get("duration_s") or 0) <= hi]
        if group:
            rows.append({
                "length": label,
                "videos": len(group),
                "median_views": int(util.median(v["views"] for v in group)),
                "median_ratio": round(util.median(v.get("neighbour_ratio", 0) for v in group), 2),
            })
    return rows


# ---------------------------------------------------------------- comments

_COMMENT_RULES = {
    "question": r"\?|^(how|what|when|where|why|which|who|can|could|does|do|is|are|will|should)\b",
    "request": r"\b(make a video|do a video|video on|video about|part ?2|part two|next video|next part|"
    r"please (make|do|cover|upload|explain)|can you (make|do|cover|explain)|would love to see|"
    r"waiting for|more (of|videos)|cover|series on|upload more)\b",
    "pain_point": r"\b(struggl|confus|frustrat|stuck|can't figure|don't understand|hard to|problem|issue|help me)\w*",
    "criticism": r"\b(wrong|incorrect|mistake|misleading|clickbait|boring|too long|too loud|bad audio|"
    r"music (is )?(too )?loud|disappointed|waste|inaccurate|dislike)\w*",
    "praise": r"\b(love|loved|amazing|awesome|great|best|thank|helpful|beautiful|incredible|brilliant|goosebumps)\w*",
    "monetization_signal": r"\b(course|buy|price|merch|membership|patreon|sponsor|link|where can i get|book)\w*",
}
_COMMENT_RE = {k: re.compile(p, re.I) for k, p in _COMMENT_RULES.items()}


def categorize_comment(text: str) -> list[str]:
    """English keyword heuristics. For other languages the agent should read raw text."""
    cats = [k for k, rx in _COMMENT_RE.items() if rx.search(text)]
    if _TIMESTAMP.search(text):
        cats.append("timestamp")
    return cats or ["general"]


def summarize_comments(comments: list[dict], per_bucket: int = 8) -> dict:
    buckets: dict[str, list[dict]] = {}
    for c in comments:
        for cat in categorize_comment(c.get("text", "")):
            buckets.setdefault(cat, []).append(c)
    words = ngrams([c.get("text", "") for c in comments], 1, 30)
    phrases = ngrams([c.get("text", "") for c in comments], 2, 20)
    return {
        "total": len(comments),
        "counts": {k: len(v) for k, v in sorted(buckets.items(), key=lambda kv: -len(kv[1]))},
        "top_by_category": {
            k: sorted(v, key=lambda c: c.get("likes", 0), reverse=True)[:per_bucket]
            for k, v in buckets.items()
            if k != "general"
        },
        "top_liked": sorted(comments, key=lambda c: c.get("likes", 0), reverse=True)[:per_bucket],
        "frequent_words": words,
        "frequent_phrases": phrases,
    }


# ---------------------------------------------------------------- velocity (watchlist)

def velocity(history: list[tuple[str, int]]) -> float | None:
    """Views per hour between the last two snapshots [(iso_time, views), ...]."""
    if len(history) < 2:
        return None
    (t1, v1), (t2, v2) = history[-2], history[-1]
    a, b = util.parse_time(t1), util.parse_time(t2)
    if not a or not b or b <= a:
        return None
    return round((v2 - v1) / ((b - a).total_seconds() / 3600), 1)


def early_performance(video: dict, peers: list[dict], max_age_days: float = 7, min_peer_age: float = 14) -> dict | None:
    """How a fresh upload compares with what a typical video of the channel ends up with.

    ``pct_of_typical`` = views so far / median lifetime views of mature same-format
    uploads. A video at 100%+ within its first days is an early breakout.
    """
    age = util.age_days(video.get("published_at"))
    if age <= 0 or age > max_age_days:
        return None
    fmt = video.get("format") or video_format(video)
    mature = [
        p["views"] for p in peers
        if p["video_id"] != video["video_id"]
        and (p.get("format") or video_format(p)) == fmt
        and util.age_days(p.get("published_at")) >= min_peer_age
    ]
    base = util.median(mature)
    return {
        "age_hours": round(age * 24, 1),
        "views_per_hour": round(video["views"] / max(age * 24, 1), 1),
        "typical_lifetime_views": int(base),
        "pct_of_typical": round(video["views"] / base * 100) if base else None,
    }


def now() -> datetime:
    return datetime.now(timezone.utc)
