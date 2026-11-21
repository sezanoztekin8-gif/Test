#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-api-python-client>=2.100", "google-auth-oauthlib>=1.2", "google-auth>=2.23", "tzdata"]
# ///
"""Private analytics for YOUR channel (YouTube Analytics API v2, read token).

Commands (all accept --days N, default 28; or --start/--end YYYY-MM-DD)
  overview          headline totals + change vs the previous period
  daily             day-by-day views, watch time, subscribers
  top-videos        best videos in the window (--sort views|estimatedMinutesWatched|subscribersGained|averageViewPercentage)
  video VIDEO       one video: totals, traffic sources, retention summary
  retention VIDEO   audience retention curve with drop-off points (needs ~100+ views)
  traffic           traffic sources (search, browse, suggested, external, Shorts feed...)
  search-terms      YouTube search terms that brought viewers (optionally --video)
  external          external websites/apps sending traffic
  suggested         videos (yours and others') that recommended yours
  audience          age/gender, subscribed vs not, new vs returning not available via API
  geography         countries (and --country XX for regions/states)
  devices           device types and operating systems
  playback          where it was watched (watch page, embedded, Shorts, channel page)
  sharing           where viewers shared your videos
  revenue           estimated revenue, RPM/CPM (needs `yt_auth.py login --revenue`)
  report            everything above in one JSON + markdown brief saved to the reports dir

Impressions and click-through rate are NOT in this API - use yt_reporting.py (reach report).
Analytics data lags 1-3 days, so windows end yesterday by default.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ytkit import cli, client, data, ids, util  # noqa: E402
from ytkit.client import YtError, call  # noqa: E402

CORE = "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost,likes,comments,shares"
REVENUE = "estimatedRevenue,estimatedAdRevenue,estimatedRedPartnerRevenue,grossRevenue,cpm,playbackBasedCpm,adImpressions,monetizedPlaybacks"


def window(args):
    if args.start and args.end:
        return args.start, args.end
    return util.date_window(args.days)


def q(an, start, end, metrics, **kw):
    params = {"ids": "channel==MINE", "startDate": start, "endDate": end, "metrics": metrics}
    params.update({k: v for k, v in kw.items() if v is not None})
    res = call(an.reports().query(**params))
    cols = [h["name"] for h in res.get("columnHeaders", [])]
    return [dict(zip(cols, row)) for row in res.get("rows", []) or []]


def soft(an, *a, **kw):
    try:
        return q(an, *a, **kw)
    except YtError as exc:
        return [{"unavailable": str(exc)}]


def titles_for(video_ids):
    if not video_ids:
        return {}
    try:
        yt = client.public()
        return {v["video_id"]: v for v in data.videos(yt, video_ids, parts="snippet,contentDetails,statistics")}
    except YtError:
        return {}


def attach(rows, key="video"):
    meta = titles_for([r[key] for r in rows if r.get(key)])
    for r in rows:
        m = meta.get(r.get(key))
        if m:
            r["title"] = m["title"]
            r["published_at"] = m["published_at"]
            r["duration"] = m["duration"]
            r["format"] = "short" if 0 < m["duration_s"] <= 180 else "long"
    return rows


def video_filter(args):
    return f"video=={ids.video_id(args.video)}" if getattr(args, "video", None) else None


# ---------------------------------------------------------------- commands

def cmd_overview(args, an=None):
    an = an or client.analytics()
    start, end = window(args)
    cur = q(an, start, end, CORE)
    days = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    p_end = date.fromisoformat(start) - timedelta(days=1)
    p_start = p_end - timedelta(days=days - 1)
    prev = q(an, p_start.isoformat(), p_end.isoformat(), CORE)
    cur, prev = (cur or [{}])[0], (prev or [{}])[0]
    change = {}
    for k, v in cur.items():
        pv = prev.get(k)
        if isinstance(v, (int, float)) and isinstance(pv, (int, float)) and pv:
            change[k] = f"{(v - pv) / pv * 100:+.1f}%"
    cur["netSubscribers"] = (cur.get("subscribersGained") or 0) - (cur.get("subscribersLost") or 0)
    cur["watchHours"] = round((cur.get("estimatedMinutesWatched") or 0) / 60, 1)
    return {"window": {"start": start, "end": end, "days": days}, "totals": cur,
            "previous_window": {"start": p_start.isoformat(), "end": p_end.isoformat()},
            "previous": prev, "change_vs_previous": change}


def cmd_daily(args, an=None):
    an = an or client.analytics()
    start, end = window(args)
    return q(an, start, end, "views,estimatedMinutesWatched,subscribersGained,subscribersLost,likes,shares", dimensions="day", sort="day")


def cmd_top_videos(args, an=None):
    an = an or client.analytics()
    start, end = window(args)
    rows = q(an, start, end, CORE, dimensions="video", sort="-" + args.sort, maxResults=args.max)
    return attach(rows)


def cmd_retention(args, an=None):
    an = an or client.analytics()
    vid = ids.video_id(args.video)
    start, end = window(args) if (args.start or args.days != 28) else ("2005-04-23", util.date_window(1)[1])
    filt = f"video=={vid}" + (f";audienceType=={args.audience_type}" if args.audience_type else "")
    try:
        curve = q(an, start, end, "audienceWatchRatio,relativeRetentionPerformance", dimensions="elapsedVideoTimeRatio", filters=filt, sort="elapsedVideoTimeRatio")
    except YtError:
        curve = soft(an, start, end, "audienceWatchRatio", dimensions="elapsedVideoTimeRatio", filters=filt, sort="elapsedVideoTimeRatio")
    meta = titles_for([vid]).get(vid, {})
    dur = meta.get("duration_s") or 0
    drops = []
    for i, r in enumerate(curve):
        if "elapsedVideoTimeRatio" not in r:
            continue
        r["at"] = util.hms(r["elapsedVideoTimeRatio"] * dur) if dur else None
        if i:
            delta = curve[i - 1].get("audienceWatchRatio", 0) - r.get("audienceWatchRatio", 0)
            if delta >= 0.03:
                drops.append({"at": r["at"], "ratio": r["elapsedVideoTimeRatio"], "drop": round(delta, 3)})
    def at(p):
        pts = [r for r in curve if r.get("elapsedVideoTimeRatio") is not None]
        return min(pts, key=lambda r: abs(r["elapsedVideoTimeRatio"] - p)).get("audienceWatchRatio") if pts else None
    return {
        "video_id": vid, "title": meta.get("title"), "duration": meta.get("duration"),
        "checkpoints": {"0%": at(0.0), "10%": at(0.1), "25%": at(0.25), "50%": at(0.5), "75%": at(0.75), "end": at(0.99)},
        "biggest_drops": sorted(drops, key=lambda d: -d["drop"])[:8],
        "curve": curve,
        "how_to_read": "audienceWatchRatio = share of viewers still watching (can exceed 1 when people rewatch). "
                       "relativeRetentionPerformance compares with similar-length YouTube videos: >0.5 better than typical.",
    }


def cmd_video(args, an=None):
    an = an or client.analytics()
    vid = ids.video_id(args.video)
    start, end = window(args) if (args.start or args.days != 28) else ("2005-04-23", util.date_window(1)[1])
    f = f"video=={vid}"
    return {
        "video_id": vid,
        "meta": titles_for([vid]).get(vid),
        "window": {"start": start, "end": end},
        "totals": soft(an, start, end, CORE, filters=f),
        "traffic": soft(an, start, end, "views,estimatedMinutesWatched", dimensions="insightTrafficSourceType", filters=f, sort="-views"),
        "search_terms": soft(an, start, end, "views", dimensions="insightTrafficSourceDetail",
                             filters=f + ";insightTrafficSourceType==YT_SEARCH", sort="-views", maxResults=15),
        "first_days": soft(an, start, end, "views,estimatedMinutesWatched,subscribersGained", dimensions="day", filters=f, sort="day")[:14],
    }


def cmd_traffic(args, an=None):
    an = an or client.analytics()
    start, end = window(args)
    rows = q(an, start, end, "views,estimatedMinutesWatched,averageViewDuration", dimensions="insightTrafficSourceType", filters=video_filter(args), sort="-views")
    total = sum(r.get("views", 0) for r in rows) or 1
    for r in rows:
        r["share_pct"] = round(r["views"] / total * 100, 1)
    return rows


def _detail(an, args, source, n):
    start, end = window(args)
    f = f"insightTrafficSourceType=={source}" + (";" + video_filter(args) if video_filter(args) else "")
    return q(an, start, end, "views,estimatedMinutesWatched", dimensions="insightTrafficSourceDetail", filters=f, sort="-views", maxResults=n)


def cmd_search_terms(args, an=None):
    return _detail(an or client.analytics(), args, "YT_SEARCH", args.max)


def cmd_external(args, an=None):
    return _detail(an or client.analytics(), args, "EXT_URL", args.max)


def cmd_suggested(args, an=None):
    rows = _detail(an or client.analytics(), args, "RELATED_VIDEO", args.max)
    meta = titles_for([r["insightTrafficSourceDetail"] for r in rows if r.get("insightTrafficSourceDetail")])
    for r in rows:
        m = meta.get(r.get("insightTrafficSourceDetail"))
        if m:
            r.update(title=m["title"], channel=m["channel_title"])
    return rows


def cmd_audience(args, an=None):
    an = an or client.analytics()
    start, end = window(args)
    f = video_filter(args)
    return {
        "age_gender": soft(an, start, end, "viewerPercentage", dimensions="ageGroup,gender", filters=f, sort="gender,ageGroup"),
        "subscribed_status": soft(an, start, end, "views,estimatedMinutesWatched,averageViewDuration", dimensions="subscribedStatus", filters=f),
        "creator_content_type": soft(an, start, end, "views,estimatedMinutesWatched", dimensions="creatorContentType", filters=f),
    }


def cmd_geography(args, an=None):
    an = an or client.analytics()
    start, end = window(args)
    if args.country:
        return q(an, start, end, "views,estimatedMinutesWatched", dimensions="province", filters=f"country=={args.country}", sort="-views")
    return q(an, start, end, "views,estimatedMinutesWatched,averageViewDuration,subscribersGained", dimensions="country", filters=video_filter(args), sort="-views", maxResults=args.max)


def cmd_devices(args, an=None):
    an = an or client.analytics()
    start, end = window(args)
    return {"device": soft(an, start, end, "views,estimatedMinutesWatched", dimensions="deviceType", sort="-views"),
            "os": soft(an, start, end, "views,estimatedMinutesWatched", dimensions="operatingSystem", sort="-views")}


def cmd_playback(args, an=None):
    an = an or client.analytics()
    start, end = window(args)
    return q(an, start, end, "views,estimatedMinutesWatched", dimensions="insightPlaybackLocationType", filters=video_filter(args), sort="-views")


def cmd_sharing(args, an=None):
    an = an or client.analytics()
    start, end = window(args)
    return q(an, start, end, "shares", dimensions="sharingService", filters=video_filter(args), sort="-shares")


def cmd_revenue(args, an=None):
    an = an or client.analytics(revenue=True)
    start, end = window(args)
    return {"totals": q(an, start, end, REVENUE),
            "by_video": attach(soft(an, start, end, "estimatedRevenue,playbackBasedCpm,views", dimensions="video", sort="-estimatedRevenue", maxResults=args.max)),
            "by_country": soft(an, start, end, "estimatedRevenue,playbackBasedCpm,views", dimensions="country", sort="-estimatedRevenue", maxResults=15)}


def cmd_report(args):
    an = client.analytics()
    yt = client.owner()
    ch = data.my_channel(yt)
    args.video = None
    args.country = None
    rep = {
        "channel": {k: ch[k] for k in ("title", "channel_id", "subscribers", "total_views", "video_count")},
        "overview": cmd_overview(args, an),
        "top_videos": cmd_top_videos(args, an),
        "traffic": cmd_traffic(args, an),
        "search_terms": soft_call(cmd_search_terms, args, an),
        "suggested_by": soft_call(cmd_suggested, args, an),
        "external": soft_call(cmd_external, args, an),
        "audience": cmd_audience(args, an),
        "geography": soft_call(cmd_geography, args, an),
        "devices": cmd_devices(args, an),
        "daily": cmd_daily(args, an),
    }
    if args.revenue:
        rep["revenue"] = soft_call(cmd_revenue, args, None)
    name = f"analytics-{util.slug(ch['title'])}-{args.days}d-{date.today().isoformat()}.json"
    path = util.save_json(rep, name, args.reports_dir)
    o = rep["overview"]
    t = o["totals"]
    return {
        "saved": str(path),
        "headline": {
            "window": o["window"], "views": t.get("views"), "watch_hours": t.get("watchHours"),
            "net_subscribers": t.get("netSubscribers"), "avg_view_pct": t.get("averageViewPercentage"),
            "change_vs_previous": o["change_vs_previous"],
        },
        "top_5": [{k: r.get(k) for k in ("title", "video", "views", "averageViewPercentage", "subscribersGained")} for r in rep["top_videos"][:5]],
        "traffic_mix": [{r["insightTrafficSourceType"]: r["share_pct"]} for r in rep["traffic"][:6]],
        "next_step": "Read the saved JSON and write the brief using templates/analytics-report.md",
    }


def soft_call(fn, args, an):
    try:
        return fn(args, an)
    except YtError as exc:
        return {"unavailable": str(exc)}


def main():
    p = cli.parser(__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)

    def common(name, video=False, video_opt=False, mx=None):
        s = sp.add_parser(name)
        if video:
            s.add_argument("video")
        if video_opt:
            s.add_argument("--video", help="limit to one video")
        s.add_argument("--days", type=int, default=28)
        s.add_argument("--start")
        s.add_argument("--end")
        if mx:
            s.add_argument("--max", type=int, default=mx)
        return s

    common("overview")
    common("daily")
    tv = common("top-videos", mx=20)
    tv.add_argument("--sort", default="views", choices=["views", "estimatedMinutesWatched", "subscribersGained", "averageViewPercentage", "likes", "shares"])
    common("video", video=True)
    rt = common("retention", video=True)
    rt.add_argument("--audience-type", choices=["ORGANIC", "AD_INSTREAM", "AD_INDISPLAY"])
    common("traffic", video_opt=True)
    common("search-terms", video_opt=True, mx=25)
    common("external", video_opt=True, mx=25)
    common("suggested", video_opt=True, mx=25)
    common("audience", video_opt=True)
    g = common("geography", video_opt=True, mx=25)
    g.add_argument("--country", help="ISO code for a regional breakdown, e.g. US, IN")
    common("devices")
    common("playback", video_opt=True)
    common("sharing", video_opt=True)
    common("revenue", mx=20)
    r = common("report", mx=20)
    r.add_argument("--sort", default="views")
    r.add_argument("--revenue", action="store_true")
    cli.add_reports_dir(r)
    args = p.parse_args()
    return globals()["cmd_" + args.cmd.replace("-", "_")](args)


if __name__ == "__main__":
    cli.run(main)
