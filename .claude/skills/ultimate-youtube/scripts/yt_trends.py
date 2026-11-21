#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-api-python-client>=2.100", "google-auth-oauthlib>=1.2", "google-auth>=2.23", "tzdata"]
# ///
"""Topic and trend research.

Commands
  suggest "seed" [--expand] [--lang en] [--region US]
        YouTube search autocomplete - what people actually type. --expand adds
        "seed a", "seed b", ... and question prefixes (free, no API quota;
        uses Google's public suggest endpoint, unofficial)
  search "query" [--days 30] [--order viewCount] [--duration any|short|medium|long]
                 [--region US] [--lang en] [--max 50]
        top videos for a query with views/day and views-per-subscriber
        (1 call from the 100/day search bucket + ~2 units)
  trending [--region US] [--category ID] [--max 50]
        YouTube's "most popular" chart for a region/category (1 unit)
  categories [--region US]
        category IDs for --category
  video VIDEO [VIDEO ...]
        quick public stats for one or more videos (1 unit per 50)

Search-result signal: views_per_sub > 1 means the video reached far beyond the
channel's subscribers - the topic/packaging is pulling new viewers.
"""

import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ytkit import analysis, cli, client, data, ids, util  # noqa: E402
from ytkit.client import call  # noqa: E402


def _suggest(q, lang, region):
    url = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(
        {"client": "firefox", "ds": "yt", "q": q, "hl": lang, "gl": region}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
    try:
        return json.loads(raw.decode(charset))[1]
    except (UnicodeDecodeError, json.JSONDecodeError, IndexError):
        return json.loads(raw.decode("utf-8", errors="replace"))[1]


def cmd_suggest(args):
    seeds = [args.seed]
    if args.expand:
        seeds += [f"{args.seed} {c}" for c in "abcdefghijklmnopqrstuvwxyz"]
        seeds += [f"{w} {args.seed}" for w in ("how", "why", "what", "best", "is", "can")]
        seeds += [f"{args.seed} vs", f"{args.seed} for"]
    seen, rows = set(), []
    for s in seeds:
        try:
            for sug in _suggest(s, args.lang, args.region):
                if sug not in seen:
                    seen.add(sug)
                    rows.append({"suggestion": sug, "from": s})
        except Exception as exc:  # noqa: BLE001
            util.eprint(f"suggest failed for {s!r}: {exc}")
    words = analysis.ngrams([r["suggestion"].replace(args.seed.lower(), "") for r in rows], 1, 25)
    return {"seed": args.seed, "count": len(rows), "suggestions": [r["suggestion"] for r in rows],
            "modifiers": words,
            "note": "Autocomplete order roughly reflects popularity; it has no volume numbers. "
                    "Validate demand with `search` (are videos on it getting views?)."}


def cmd_search(args):
    yt = client.public()
    params = dict(part="snippet", q=args.query, type="video", maxResults=min(args.max, 50), order=args.order)
    if args.days:
        params["publishedAfter"] = (datetime.now(timezone.utc) - timedelta(days=args.days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if args.duration != "any":
        params["videoDuration"] = args.duration
    if args.region:
        params["regionCode"] = args.region
    if args.lang:
        params["relevanceLanguage"] = args.lang
    res = call(yt.search().list(**params), "search.list")
    vids = data.videos(yt, [i["id"]["videoId"] for i in res.get("items", [])])
    chans = data.channels(yt, list({v["channel_id"] for v in vids}))
    rows = []
    for v in vids:
        subs = chans.get(v["channel_id"], {}).get("subscribers") or 0
        e = analysis.enrich(v, subs)
        rows.append({"title": e["title"], "channel": e["channel_title"], "subscribers": subs, "views": e["views"],
                     "views_per_day": e["views_per_day"], "views_per_sub": e.get("views_per_sub"),
                     "engagement_rate": e["engagement_rate"], "duration": e["duration"], "format": e["format"],
                     "published_at": e["published_at"], "url": e["url"]})
    rows.sort(key=lambda r: -(r["views_per_sub"] or 0))
    summary = {
        "results": len(rows),
        "median_views": int(util.median(r["views"] for r in rows)),
        "median_views_per_day": round(util.median(r["views_per_day"] for r in rows), 1),
        "small_channels_breaking_out": [r for r in rows if r["subscribers"] and r["subscribers"] < 50_000 and (r["views_per_sub"] or 0) >= 1][:10],
        "frequent_title_words": analysis.ngrams([r["title"] for r in rows], 1, 15),
        "frequent_title_phrases": analysis.ngrams([r["title"] for r in rows], 2, 10),
    }
    path = util.save_json(rows, f"search-{util.slug(args.query)}-{datetime.now():%Y-%m-%d}.json", args.reports_dir)
    return {"query": args.query, "filters": {k: params[k] for k in params if k not in ("part", "q")}, "summary": summary,
            "videos": rows[: args.show], "saved": str(path)}


def cmd_trending(args):
    yt = client.public()
    params = dict(part="snippet,statistics,contentDetails", chart="mostPopular", regionCode=args.region, maxResults=min(args.max, 50))
    if args.category:
        params["videoCategoryId"] = args.category
    res = call(yt.videos().list(**params), "videos.list")
    rows = []
    for item in res.get("items", []):
        v = analysis.enrich(data.normalize_video(item))
        rows.append({k: v[k] for k in ("title", "channel_title", "views", "views_per_day", "duration", "format", "published_at", "url")})
    return {"region": args.region, "category": args.category, "videos": rows,
            "frequent_title_words": analysis.ngrams([r["title"] for r in rows], 1, 15)}


def cmd_categories(args):
    yt = client.public()
    res = call(yt.videoCategories().list(part="snippet", regionCode=args.region), "videoCategories.list")
    return [{"id": c["id"], "title": c["snippet"]["title"]} for c in res.get("items", [])]


def cmd_video(args):
    yt = client.public()
    vids = data.videos(yt, ids.video_ids(args.videos))
    return [{k: v[k] for k in ("video_id", "title", "channel_title", "published_at", "views", "likes", "comments",
                                "duration", "tags", "default_audio_language", "has_captions", "url")}
            | {"description": v["description"][:500]} for v in vids]


def main():
    p = cli.parser(__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("suggest")
    s.add_argument("seed")
    s.add_argument("--expand", action="store_true")
    s.add_argument("--lang", default="en")
    s.add_argument("--region", default="US")
    se = sp.add_parser("search")
    se.add_argument("query")
    se.add_argument("--days", type=int, default=0, help="only videos from the last N days (0 = any time)")
    se.add_argument("--order", default="viewCount", choices=["relevance", "viewCount", "date", "rating"])
    se.add_argument("--duration", default="any", choices=["any", "short", "medium", "long"], help="short <4m, medium 4-20m, long >20m")
    se.add_argument("--region")
    se.add_argument("--lang")
    se.add_argument("--max", type=int, default=50)
    se.add_argument("--show", type=int, default=20)
    cli.add_reports_dir(se)
    t = sp.add_parser("trending")
    t.add_argument("--region", default="US")
    t.add_argument("--category")
    t.add_argument("--max", type=int, default=50)
    c = sp.add_parser("categories")
    c.add_argument("--region", default="US")
    v = sp.add_parser("video")
    v.add_argument("videos", nargs="+")
    args = p.parse_args()
    return globals()["cmd_" + args.cmd](args)


if __name__ == "__main__":
    cli.run(main)
