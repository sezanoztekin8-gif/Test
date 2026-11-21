"""Local tracker for the YouTube Data API v3 daily quota.

Google's quota page (developers.google.com/youtube/v3/determine_quota_cost)
describes three separate daily buckets per Cloud project:

    units   10,000 units/day shared by every endpoint except the two below
    search  search.list   - its own bucket, default 100 calls/day
    upload  videos.insert - its own bucket, default 100 calls/day

Quota resets at midnight Pacific Time. Google is the source of truth - this
tracker only exists so the agent can plan expensive workflows and warn the
user before they burn through the day's budget. Limits can be overridden in
config.json: {"daily_quota": 10000, "daily_search_calls": 100,
"daily_upload_calls": 100}.

The YouTube Analytics and Reporting APIs have separate, generous quotas and
are not tracked here.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from . import config

# (bucket, cost) per method. Values from the official quota table.
COSTS: dict[str, tuple[str, int]] = {
    "search.list": ("search", 1),
    "videos.insert": ("upload", 1),
    "videos.list": ("units", 1),
    "videos.update": ("units", 50),
    "videos.delete": ("units", 50),
    "videos.rate": ("units", 50),
    "thumbnails.set": ("units", 50),
    "channels.list": ("units", 1),
    "channels.update": ("units", 50),
    "playlists.list": ("units", 1),
    "playlists.insert": ("units", 50),
    "playlists.update": ("units", 50),
    "playlists.delete": ("units", 50),
    "playlistItems.list": ("units", 1),
    "playlistItems.insert": ("units", 50),
    "playlistItems.update": ("units", 50),
    "playlistItems.delete": ("units", 50),
    "commentThreads.list": ("units", 1),
    "comments.list": ("units", 1),
    "comments.insert": ("units", 50),
    "captions.list": ("units", 50),
    "captions.insert": ("units", 400),
    "captions.update": ("units", 450),
    "captions.delete": ("units", 50),
    "captions.download": ("units", 200),
    "videoCategories.list": ("units", 1),
    "i18nLanguages.list": ("units", 1),
    "i18nRegions.list": ("units", 1),
}

WARN_AT = 0.8


def _limits() -> dict[str, int]:
    cfg = config.load_config()
    return {
        "units": int(cfg.get("daily_quota", 10_000)),
        "search": int(cfg.get("daily_search_calls", 100)),
        "upload": int(cfg.get("daily_upload_calls", 100)),
    }


def pacific_today() -> str:
    now = datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo

        return now.astimezone(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
    except Exception:  # tzdata missing (some Windows installs) - approximate with DST rule
        year = now.year
        # US DST: 2nd Sunday of March 10:00 UTC -> 1st Sunday of November 09:00 UTC
        march = datetime(year, 3, 8, 10, tzinfo=timezone.utc)
        dst_start = march + timedelta(days=(6 - march.weekday()) % 7)
        nov = datetime(year, 11, 1, 9, tzinfo=timezone.utc)
        dst_end = nov + timedelta(days=(6 - nov.weekday()) % 7)
        offset = -7 if dst_start <= now < dst_end else -8
        return (now + timedelta(hours=offset)).strftime("%Y-%m-%d")


def _path():
    return config.sub("quota") / f"{pacific_today()}.json"


def _load() -> dict:
    path = _path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {"date": pacific_today(), "used": {"units": 0, "search": 0, "upload": 0}, "methods": {}}


def _save(state: dict) -> None:
    _path().write_text(json.dumps(state, indent=2), encoding="utf-8")


def cost_of(method: str, count: int = 1) -> tuple[str, int]:
    bucket, cost = COSTS.get(method, ("units", 1))
    return bucket, cost * count


def status() -> dict:
    state = _load()
    limits = _limits()
    out = {"date_pacific": state["date"], "buckets": {}, "methods": state["methods"]}
    for bucket, limit in limits.items():
        used = state["used"].get(bucket, 0)
        out["buckets"][bucket] = {
            "used": used,
            "limit": limit,
            "remaining": max(limit - used, 0),
            "used_pct": round(used / limit * 100, 1) if limit else 0,
        }
    warnings = [
        f"{b}: {v['used_pct']}% used ({v['remaining']} left)"
        for b, v in out["buckets"].items()
        if v["limit"] and v["used"] / v["limit"] >= WARN_AT
    ]
    if warnings:
        out["warnings"] = warnings
    return out


def can_afford(method: str, count: int = 1) -> tuple[bool, str]:
    bucket, cost = cost_of(method, count)
    state = _load()
    limit = _limits()[bucket]
    remaining = limit - state["used"].get(bucket, 0)
    if cost > remaining:
        return False, (
            f"{method} x{count} needs {cost} from the '{bucket}' bucket but only "
            f"{remaining} remain today (resets midnight Pacific)."
        )
    return True, ""


def record(method: str, count: int = 1) -> None:
    bucket, cost = cost_of(method, count)
    state = _load()
    state["used"][bucket] = state["used"].get(bucket, 0) + cost
    state["methods"][method] = state["methods"].get(method, 0) + count
    _save(state)


def reset() -> None:
    _path().unlink(missing_ok=True)


def estimate(plan: dict[str, int]) -> dict:
    """Estimate a workflow, e.g. {"search.list": 2, "videos.list": 10}."""
    totals: dict[str, int] = {}
    for method, count in plan.items():
        bucket, cost = cost_of(method, count)
        totals[bucket] = totals.get(bucket, 0) + cost
    return totals
