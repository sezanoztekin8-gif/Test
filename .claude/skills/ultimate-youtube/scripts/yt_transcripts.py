#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-api-python-client>=2.100", "google-auth-oauthlib>=1.2", "google-auth>=2.23", "youtube-transcript-api>=1.0", "tzdata"]
# ///
"""Transcripts for any public video, plus a local library you can search.

Commands
  get VIDEO [--lang en,hi] [--timed] [--start S --end S] [--translate en] [--own] [--refresh]
        print a transcript (cached after the first fetch). --own uses the official
        captions API for videos on your channel (200 units) as a last resort.
  hook VIDEO [--seconds 45]       just the opening - the part that decides retention
  sync CHANNEL [--max 50] [--lang en]
        fetch transcripts of a channel's recent uploads into the library
        (yours or a competitor's; ~2 API units + no quota for the transcripts)
  search "phrase" [--channel UC..] [--max 30] [--context 1]
        search every cached transcript; returns timestamps and deep links
  list [--channel UC..]           what is in the library
  stats VIDEO                     words, words-per-minute, segment pacing

Transcripts are cached in ~/.ultimate-youtube/cache/transcripts/.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ytkit import cli, client, data, ids, transcript, util  # noqa: E402


def langs(args):
    return [l.strip() for l in (args.lang or "en").split(",") if l.strip()]


def fetch(vid, args, meta=None):
    try:
        return transcript.get(vid, langs(args), own=getattr(args, "own", False), refresh=getattr(args, "refresh", False),
                              translate_to=getattr(args, "translate", None), meta=meta)
    except RuntimeError as exc:
        try:
            detail = json.loads(str(exc))
        except json.JSONDecodeError:
            detail = str(exc)
        util.fail("No transcript available", "Check the video has captions; try --lang with its language; "
                  "if requests are blocked, run from a home connection (references/transcripts.md).", detail=detail)


def cmd_get(args):
    vid = ids.video_id(args.video)
    tr = fetch(vid, args)
    segs = transcript.window(tr["segments"], args.start or 0, args.end)
    out = {k: tr.get(k) for k in ("video_id", "language", "is_generated", "method", "word_count", "duration_s", "cached")}
    out["available"] = tr.get("available")
    if args.timed:
        out["text"] = transcript.timed_text(segs)
    else:
        out["text"] = transcript.plain_text(segs)
    if args.save:
        path = Path(args.save)
        path.write_text(out["text"], encoding="utf-8")
        out["text"] = f"(saved to {path})"
    return out


def cmd_hook(args):
    vid = ids.video_id(args.video)
    tr = fetch(vid, args)
    segs = transcript.window(tr["segments"], 0, args.seconds)
    words = sum(len(s["text"].split()) for s in segs)
    return {"video_id": vid, "language": tr["language"], "seconds": args.seconds, "words": words,
            "hook": transcript.timed_text(segs)}


def cmd_stats(args):
    vid = ids.video_id(args.video)
    tr = fetch(vid, args)
    segs = tr["segments"]
    minutes = max(tr["duration_s"] / 60, 0.1)
    per_min = []
    for m in range(int(minutes) + 1):
        w = sum(len(s["text"].split()) for s in segs if m * 60 <= s["start"] < (m + 1) * 60)
        per_min.append(w)
    return {"video_id": vid, "language": tr["language"], "words": tr["word_count"],
            "duration": util.hms(tr["duration_s"]), "words_per_minute": round(tr["word_count"] / minutes),
            "words_by_minute": per_min, "questions_asked": sum(s["text"].count("?") for s in segs)}


def cmd_sync(args):
    yt = client.public()
    cid = data.resolve_channel(yt, args.channel)
    vids = data.channel_videos(yt, cid, args.max)
    done, failed, cached = 0, [], 0
    for v in vids:
        if v["duration_s"] and v["duration_s"] < args.min_seconds:
            continue
        try:
            tr = transcript.get(v["video_id"], langs(args), meta=v)
            if tr.get("cached"):
                cached += 1
            else:
                done += 1
        except RuntimeError:
            failed.append(v["video_id"])
    return {"channel_id": cid, "videos_checked": len(vids), "fetched": done, "already_cached": cached,
            "failed": failed, "library": str(transcript.library_dir())}


def cmd_search(args):
    hits = transcript.search_library(args.query, args.max, args.context, args.channel)
    return {"query": args.query, "hits": len(hits), "results": hits}


def cmd_list(args):
    rows = []
    for p in sorted(transcript.library_dir().glob("*.json")):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        meta = rec.get("meta") or {}
        if args.channel and args.channel not in (meta.get("channel_id"), meta.get("channel_title")):
            continue
        rows.append({"video_id": rec["video_id"], "title": meta.get("title"), "channel": meta.get("channel_title"),
                     "language": rec.get("language"), "words": rec.get("word_count")})
    return {"count": len(rows), "transcripts": rows}


def main():
    p = cli.parser(__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    g = sp.add_parser("get")
    g.add_argument("video")
    g.add_argument("--lang", default="en")
    g.add_argument("--timed", action="store_true")
    g.add_argument("--start", type=float)
    g.add_argument("--end", type=float)
    g.add_argument("--translate", help="machine-translate to this language code")
    g.add_argument("--own", action="store_true", help="allow the official captions API for your own videos")
    g.add_argument("--refresh", action="store_true")
    g.add_argument("--save", help="write the text to this file instead of printing it")
    h = sp.add_parser("hook")
    h.add_argument("video")
    h.add_argument("--seconds", type=int, default=45)
    h.add_argument("--lang", default="en")
    st = sp.add_parser("stats")
    st.add_argument("video")
    st.add_argument("--lang", default="en")
    s = sp.add_parser("sync")
    s.add_argument("channel")
    s.add_argument("--max", type=int, default=50)
    s.add_argument("--lang", default="en")
    s.add_argument("--min-seconds", type=int, default=0, help="skip videos shorter than this (e.g. 61 to skip Shorts)")
    se = sp.add_parser("search")
    se.add_argument("query")
    se.add_argument("--channel")
    se.add_argument("--max", type=int, default=30)
    se.add_argument("--context", type=int, default=1)
    ls = sp.add_parser("list")
    ls.add_argument("--channel")
    args = p.parse_args()
    return globals()["cmd_" + args.cmd](args)


if __name__ == "__main__":
    cli.run(main)
