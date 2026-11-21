#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-api-python-client>=2.100", "google-auth-oauthlib>=1.2", "google-auth>=2.23", "youtube-transcript-api>=1.0", "tzdata"]
# ///
"""Competitor intelligence from public data (works on ANY channel).

Commands
  scan CHANNEL            full breakdown of a channel's recent uploads: outliers,
                          formats, cadence, upload slots, title patterns, winning
                          topics, length sweet spot, tags. Saves full data.
  compare CH1 CH2 ...     side-by-side benchmark of several channels
  outliers CH... | --watchlist
                          the videos that beat their channel's normal, across channels
  video VIDEO             "why did this video work?" evidence pack: stats vs its
                          channel's baseline, packaging, timing, hook transcript,
                          full transcript file, comment themes
  discover "query"        find channels in a niche (search: 1 call from the 100/day bucket)
  watch add|remove|list|run
                          watchlist: run it daily/weekly to see new uploads,
                          early breakouts and view velocity since the last run

CHANNEL accepts @handle, channel URL, UC... ID or a name.
Private metrics of other channels (CTR, retention, revenue) are not available
through any official API; everything here is public-data inference.

Quota: a scan of 100 videos costs ~5 units. `discover` uses the search bucket.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ytkit import analysis, cli, client, config, data, ids, transcript, util  # noqa: E402
from ytkit.client import YtError, call  # noqa: E402


def load_channel(yt, ref, limit, verify_shorts=False):
    cid = data.resolve_channel(yt, ref)
    ch = data.channels(yt, [cid]).get(cid)
    if not ch:
        raise YtError(f"Channel {ref} not found")
    vids = data.channel_videos(yt, cid, limit, ch["uploads_playlist"])
    if verify_shorts:
        for v in vids:
            if v["duration_s"] <= analysis.SHORTS_MAX_SECONDS:
                v["is_short"] = data.is_short_url_check(v["video_id"])
    vids = [analysis.enrich(v, ch["subscribers"]) for v in vids]
    return ch, vids


def compact(v, extra=()):
    keys = ("title", "views", "neighbour_ratio", "outlier_ratio", "views_per_day", "engagement_rate",
            "duration", "format", "published_at", "url") + tuple(extra)
    return {k: v.get(k) for k in keys if k in v}


def profile(ch, vids, threshold=2.0, tz=0.0):
    scored = analysis.score_outliers(vids, threshold=threshold)
    outliers = sorted([v for v in scored if v["is_outlier"]], key=lambda v: -v["neighbour_ratio"])
    under = sorted([v for v in scored if v["is_underperformer"]], key=lambda v: v["neighbour_ratio"])
    long_form = [v for v in scored if v["format"] == "long"]
    patterns = analysis.title_patterns(scored)
    if len(outliers) >= 3:
        lifts = {
            k: v for k, v in (patterns.get("features") or {}).items()
            if v["outliers_pct"] is not None and v["others_pct"] is not None and abs(v["outliers_pct"] - v["others_pct"]) >= 15
        }
    else:
        lifts = {"note": f"only {len(outliers)} outlier(s) - too few to compare title features; read the outlier titles instead"}
    return scored, {
        "channel": {k: ch[k] for k in ("title", "handle", "channel_id", "url", "subscribers", "total_views", "video_count", "country", "default_language", "created_at", "topics")},
        "sample": {
            "videos": len(scored),
            "from": min((v["published_at"] for v in scored), default=None),
            "to": max((v["published_at"] for v in scored), default=None),
        },
        "formats": analysis.format_split(scored),
        "cadence": analysis.cadence(scored, tz),
        "outliers": [compact(v) for v in outliers[:12]],
        "underperformers": [compact(v) for v in under[:6]],
        "title_patterns": {
            "median_chars": patterns.get("median_title_chars"),
            "median_chars_outliers": patterns.get("median_title_chars_outliers"),
            "features_that_differ_in_outliers": lifts,
        },
        "frequent_title_words": analysis.ngrams([v["title"] for v in scored], 1, 20),
        "frequent_title_phrases": analysis.ngrams([v["title"] for v in scored], 2, 15),
        "winning_terms": analysis.topic_lift(scored),
        "length_buckets": analysis.length_buckets(long_form),
        "top_tags": analysis.top_tags(scored, 20),
        "medians": {
            "views": int(util.median(v["views"] for v in scored)),
            "views_per_sub_pct": round(util.median(v["views"] for v in scored) / ch["subscribers"] * 100, 1) if ch["subscribers"] else None,
            "engagement_rate": round(util.median(v["engagement_rate"] for v in scored), 2),
            "comment_rate_per_1k": round(util.median(v["comment_rate"] for v in scored), 2),
        },
    }


def cmd_scan(args):
    yt = client.public()
    ch, vids = load_channel(yt, args.channel, args.max, args.verify_shorts)
    scored, prof = profile(ch, vids, args.threshold, args.tz)
    stem = f"scan-{util.slug(ch['handle'] or ch['title'])}-{datetime.now():%Y-%m-%d}"
    path = util.save_json({"profile": prof, "videos": scored}, stem + ".json", args.reports_dir)
    prof["saved_full_data"] = str(path)
    prof["next_steps"] = [
        "Explain each outlier with: python scripts/yt_competitors.py video <url>",
        "Compare transcripts of 3 outliers vs 2 underperformers for hook/structure differences (workflows/competitor-intel.md)",
    ]
    return prof


def cmd_compare(args):
    yt = client.public()
    rows = []
    for ref in args.channels:
        try:
            ch, vids = load_channel(yt, ref, args.max)
        except YtError as exc:
            rows.append({"channel": ref, "error": str(exc)})
            continue
        _, prof = profile(ch, vids)
        c = prof["cadence"]
        rows.append({
            "channel": ch["title"], "handle": ch["handle"], "subscribers": ch["subscribers"],
            "videos_sampled": len(vids),
            "uploads_per_week": c.get("uploads_per_week"),
            "days_since_last_upload": c.get("days_since_last_upload"),
            "median_views": prof["medians"]["views"],
            "views_per_sub_pct": prof["medians"]["views_per_sub_pct"],
            "engagement_rate": prof["medians"]["engagement_rate"],
            "formats": {k: {"count": v["count"], "median_views": v["median_views"]} for k, v in prof["formats"].items()},
            "outliers": len(prof["outliers"]),
            "best_outlier": prof["outliers"][0] if prof["outliers"] else None,
            "top_slot": c.get("top_slot"),
        })
    path = util.save_json(rows, f"compare-{datetime.now():%Y-%m-%d-%H%M}.json", args.reports_dir)
    return {"channels": rows, "saved": str(path)}


def watchlist_path():
    return config.home() / "watchlist.json"


def load_watchlist():
    p = watchlist_path()
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"channels": {}, "snapshots": {}, "last_run": None}


def save_watchlist(w):
    watchlist_path().write_text(util.dumps(w), encoding="utf-8")


def cmd_outliers(args):
    yt = client.public()
    refs = list(args.channels or [])
    if args.watchlist:
        refs += list(load_watchlist()["channels"].keys())
    if not refs:
        raise ValueError("Pass channels or --watchlist")
    found = []
    for ref in dict.fromkeys(refs):
        try:
            ch, vids = load_channel(yt, ref, args.max)
        except YtError as exc:
            util.eprint(f"skip {ref}: {exc}")
            continue
        for v in analysis.score_outliers(vids, threshold=args.threshold):
            if v["is_outlier"] and v["age_days"] <= args.days:
                found.append({**compact(v), "channel": ch["title"], "subscribers": ch["subscribers"]})
    found.sort(key=lambda v: -v["neighbour_ratio"])
    path = util.save_json(found, f"outliers-{datetime.now():%Y-%m-%d-%H%M}.json", args.reports_dir)
    return {"days": args.days, "threshold": args.threshold, "count": len(found), "outliers": found[: args.top], "saved": str(path)}


def cmd_video(args):
    yt = client.public()
    vid = ids.video_id(args.video)
    found = data.videos(yt, [vid])
    if not found:
        raise YtError(f"Video {vid} not found or not public")
    v = found[0]
    ch = data.channels(yt, [v["channel_id"]])[v["channel_id"]]
    v = analysis.enrich(v, ch["subscribers"])

    peers = [analysis.enrich(p, ch["subscribers"]) for p in data.channel_videos(yt, ch["channel_id"], args.peers, ch["uploads_playlist"])]
    if not any(p["video_id"] == vid for p in peers):
        peers.append(v)
    scored = {p["video_id"]: p for p in analysis.score_outliers(peers)}
    me = scored[vid]
    same_fmt = [p for p in scored.values() if p["format"] == me["format"]]

    pub = util.parse_time(v["published_at"])
    desc = v["description"]
    pack = {
        "video": compact(me, ("likes", "comments", "like_rate", "comment_rate", "views_per_sub", "age_days", "has_captions", "default_audio_language", "category_id")),
        "channel": {k: ch[k] for k in ("title", "handle", "subscribers", "video_count", "url")},
        "performance_vs_channel": {
            "baseline": f"median of {len(same_fmt)} recent {me['format']} uploads",
            "channel_median_views": int(util.median(p["views"] for p in same_fmt)),
            "outlier_ratio": me["outlier_ratio"],
            "neighbour_ratio": me["neighbour_ratio"],
            "is_outlier": me["is_outlier"],
            "rank_in_sample": sorted(same_fmt, key=lambda p: -p["views"]).index(me) + 1,
            "views_vs_subscribers_pct": round(me["views"] / ch["subscribers"] * 100, 1) if ch["subscribers"] else None,
        },
        "packaging": {
            "title": v["title"],
            "title_features": analysis.title_features(v["title"]),
            "thumbnail": v["thumbnail"],
            "tags": v["tags"][:30],
            "description_first_200": desc[:200],
            "description_chars": len(desc),
            "has_chapters": bool(analysis._TIMESTAMP.search(desc)) and "0:00" in desc,
            "links_in_description": desc.count("http"),
            "hashtags": [w for w in desc.split() if w.startswith("#")][:10],
        },
        "timing": {
            "published_utc": v["published_at"],
            "weekday_utc": pub.strftime("%A") if pub else None,
            "hour_utc": pub.hour if pub else None,
            "days_since_previous_upload": None,
        },
    }
    ordered = sorted(scored.values(), key=lambda p: p["published_at"] or "")
    idx = next(i for i, p in enumerate(ordered) if p["video_id"] == vid)
    if idx > 0:
        prev = util.parse_time(ordered[idx - 1]["published_at"])
        if prev and pub:
            pack["timing"]["days_since_previous_upload"] = round((pub - prev).total_seconds() / 86400, 1)

    langs = [l.strip() for l in args.lang.split(",") if l.strip()]
    if v.get("default_audio_language"):
        langs.append(v["default_audio_language"].split("-")[0])
    try:
        tr = transcript.get(vid, langs, meta=v)
        segs = tr["segments"]
        txt_dir = config.reports_dir(args.reports_dir) / "transcripts"
        txt_dir.mkdir(parents=True, exist_ok=True)
        txt_path = txt_dir / f"{vid}.txt"
        txt_path.write_text(f"{v['title']}\n{v['url']}\n\n" + transcript.timed_text(segs), encoding="utf-8")
        minutes = max(tr["duration_s"] / 60, 0.1)
        pack["transcript"] = {
            "language": tr["language"], "auto_generated": tr.get("is_generated"),
            "words": tr["word_count"], "words_per_minute": round(tr["word_count"] / minutes),
            "hook_first_seconds": args.hook,
            "hook_text": transcript.timed_text(transcript.window(segs, 0, args.hook)),
            "ending_text": transcript.timed_text(transcript.window(segs, max(tr["duration_s"] - 45, 0))),
            "full_transcript_file": str(txt_path),
        }
    except Exception as exc:  # noqa: BLE001 - transcripts fail for many benign reasons
        pack["transcript"] = {"unavailable": str(exc)[:400]}

    if args.comments:
        try:
            com = data.comments(yt, vid, args.comments)
            summary = analysis.summarize_comments(com, per_bucket=5)
            pack["comments"] = {
                "fetched": summary["total"], "counts": summary["counts"],
                "top_liked": [{"text": c["text"][:300], "likes": c["likes"]} for c in summary["top_liked"]],
                "requests": [c["text"][:300] for c in summary["top_by_category"].get("request", [])],
                "questions": [c["text"][:300] for c in summary["top_by_category"].get("question", [])],
                "criticism": [c["text"][:300] for c in summary["top_by_category"].get("criticism", [])],
                "timestamped": [c["text"][:200] for c in summary["top_by_category"].get("timestamp", [])],
                "frequent_phrases": summary["frequent_phrases"][:12],
            }
        except YtError as exc:
            pack["comments"] = {"unavailable": str(exc)}

    pack["saved"] = str(util.save_json(pack, f"video-{vid}.json", args.reports_dir))
    pack["analyse_with"] = "workflows/video-breakdown.md - explain the views with evidence, then extract a reusable formula"
    return pack


def cmd_discover(args):
    yt = client.public()
    params = dict(part="snippet", q=args.query, type="channel", maxResults=min(args.max, 50))
    if args.region:
        params["regionCode"] = args.region
    if args.lang:
        params["relevanceLanguage"] = args.lang
    res = call(yt.search().list(**params), "search.list")
    cids = [i["snippet"]["channelId"] for i in res.get("items", [])]
    # Also harvest channels from top videos for the query - finds smaller creators too.
    vparams = dict(part="snippet", q=args.query, type="video", maxResults=50, order=args.order)
    if args.region:
        vparams["regionCode"] = args.region
    if args.lang:
        vparams["relevanceLanguage"] = args.lang
    if args.include_video_search:
        vres = call(yt.search().list(**vparams), "search.list")
        cids += [i["snippet"]["channelId"] for i in vres.get("items", [])]
    chans = data.channels(yt, list(dict.fromkeys(cids)))
    rows = []
    for c in chans.values():
        if args.min_subs and c["subscribers"] < args.min_subs:
            continue
        if args.max_subs and c["subscribers"] > args.max_subs:
            continue
        age_years = util.age_days(c["created_at"]) / 365
        rows.append({
            "title": c["title"], "handle": c["handle"], "url": c["url"], "subscribers": c["subscribers"],
            "videos": c["video_count"], "total_views": c["total_views"],
            "views_per_video": int(c["total_views"] / c["video_count"]) if c["video_count"] else 0,
            "channel_age_years": round(age_years, 1), "country": c["country"],
            "default_language": c["default_language"],
        })
    rows.sort(key=lambda r: -r["views_per_video"])
    return {"query": args.query, "channels": rows,
            "tip": "High views_per_video with few videos or a young channel = a format that is working right now. Scan those first."}


def cmd_watch(args):
    w = load_watchlist()
    if args.action == "list":
        return {"channels": w["channels"], "last_run": w["last_run"]}
    if args.action in ("add", "remove"):
        if not args.channels:
            raise ValueError("Pass one or more channels")
        yt = client.public()
        for ref in args.channels:
            cid = data.resolve_channel(yt, ref)
            if args.action == "add":
                ch = data.channels(yt, [cid])[cid]
                w["channels"][cid] = {"title": ch["title"], "handle": ch["handle"], "added": util.now_utc().isoformat(), "note": args.note or ""}
            else:
                w["channels"].pop(cid, None)
        save_watchlist(w)
        return {"channels": w["channels"]}

    # run
    if not w["channels"]:
        raise ValueError("Watchlist is empty. Add channels with: watch add @handle")
    yt = client.public()
    now = util.now_utc().isoformat()
    since = w.get("last_run")
    digest = {"run_at": now, "previous_run": since, "channels": []}
    for cid, info in w["channels"].items():
        try:
            ch = data.channels(yt, [cid])[cid]
            vids = [analysis.enrich(v, ch["subscribers"]) for v in data.channel_videos(yt, cid, args.max, ch["uploads_playlist"])]
        except (YtError, KeyError) as exc:
            digest["channels"].append({"channel": info.get("title"), "error": str(exc)})
            continue
        entry = {"channel": ch["title"], "subscribers": ch["subscribers"],
                 "subscriber_change": ch["subscribers"] - info.get("last_subscribers", ch["subscribers"]),
                 "new_uploads": [], "early_breakouts": [], "fastest_now": []}
        info["last_subscribers"] = ch["subscribers"]
        for v in vids:
            if since and (v["published_at"] or "") > since:
                entry["new_uploads"].append(compact(v))
            early = analysis.early_performance(v, vids, max_age_days=args.fresh_days)
            if early and (early["pct_of_typical"] or 0) >= 100:
                entry["early_breakouts"].append({**compact(v), **early})
            if v["age_days"] <= 30:
                hist = w["snapshots"].setdefault(v["video_id"], [])
                hist.append([now, v["views"]])
                del hist[:-10]
                vel = analysis.velocity(hist)
                if vel is not None:
                    entry["fastest_now"].append({"title": v["title"], "url": v["url"], "views_per_hour_since_last_run": vel, "views": v["views"]})
        entry["fastest_now"] = sorted(entry["fastest_now"], key=lambda r: -r["views_per_hour_since_last_run"])[:3]
        digest["channels"].append(entry)
    # prune snapshots of videos older than ~45 days
    cutoff = datetime.now(timezone.utc).timestamp() - 45 * 86400
    w["snapshots"] = {k: h for k, h in w["snapshots"].items() if h and util.parse_time(h[0][0]).timestamp() > cutoff}
    w["last_run"] = now
    save_watchlist(w)
    digest["saved"] = str(util.save_json(digest, f"watchlist-{datetime.now():%Y-%m-%d-%H%M}.json", args.reports_dir))
    return digest


def main():
    p = cli.parser(__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("scan")
    s.add_argument("channel")
    s.add_argument("--max", type=int, default=100, help="recent uploads to analyse (default 100)")
    s.add_argument("--threshold", type=float, default=2.0, help="outlier = views >= N x neighbour median")
    s.add_argument("--tz", type=float, default=0.0, help="UTC offset for upload-time analysis, e.g. 5.5 or -5")
    s.add_argument("--verify-shorts", action="store_true", help="check /shorts/ URLs instead of the <=180s heuristic")
    cli.add_reports_dir(s)
    c = sp.add_parser("compare")
    c.add_argument("channels", nargs="+")
    c.add_argument("--max", type=int, default=50)
    cli.add_reports_dir(c)
    o = sp.add_parser("outliers")
    o.add_argument("channels", nargs="*")
    o.add_argument("--watchlist", action="store_true")
    o.add_argument("--max", type=int, default=50)
    o.add_argument("--days", type=int, default=90, help="only videos published in the last N days")
    o.add_argument("--threshold", type=float, default=2.0)
    o.add_argument("--top", type=int, default=25)
    cli.add_reports_dir(o)
    v = sp.add_parser("video")
    v.add_argument("video")
    v.add_argument("--lang", default="en", help="preferred transcript languages, comma separated")
    v.add_argument("--hook", type=int, default=45, help="seconds of opening to quote")
    v.add_argument("--comments", type=int, default=100, help="comments to analyse (0 = skip)")
    v.add_argument("--peers", type=int, default=50, help="recent channel uploads used as the baseline")
    cli.add_reports_dir(v)
    d = sp.add_parser("discover")
    d.add_argument("query")
    d.add_argument("--max", type=int, default=25)
    d.add_argument("--min-subs", type=int)
    d.add_argument("--max-subs", type=int)
    d.add_argument("--region", help="ISO country, e.g. US, IN, BR")
    d.add_argument("--lang", help="relevance language, e.g. en, hi, es")
    d.add_argument("--order", default="viewCount", choices=["relevance", "viewCount", "date", "rating"])
    d.add_argument("--include-video-search", action="store_true", help="also harvest channels from top videos (+1 search call)")
    w = sp.add_parser("watch")
    w.add_argument("action", choices=["add", "remove", "list", "run"])
    w.add_argument("channels", nargs="*")
    w.add_argument("--note")
    w.add_argument("--max", type=int, default=30)
    w.add_argument("--fresh-days", type=float, default=7)
    cli.add_reports_dir(w)
    args = p.parse_args()
    return globals()["cmd_" + args.cmd](args)


if __name__ == "__main__":
    cli.run(main)
