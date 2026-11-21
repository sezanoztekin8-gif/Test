#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-api-python-client>=2.100", "google-auth-oauthlib>=1.2", "google-auth>=2.23", "tzdata"]
# ///
"""Mine comments for questions, content requests, pain points and criticism.

Commands
  video VIDEO [--max 200] [--order relevance|time]
  channel CHANNEL [--videos 10] [--per-video 100] [--skip-shorts]
        aggregate across a channel's recent uploads (any channel)
  mine [--videos 10] [--per-video 100]
        same, for your own channel (read token)

Output: counts per category, the most-liked examples per category, frequent
words and phrases. Categories use English keyword rules; for other languages
read the `sample` texts directly - the agent should classify them itself.
Quota: 1 unit per 100 comments.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ytkit import analysis, cli, client, data, ids, util  # noqa: E402


def pack(comments, extra=None, sample=40):
    s = analysis.summarize_comments(comments, per_bucket=8)
    trim = lambda c: {"text": c["text"][:400], "likes": c.get("likes", 0), **({"video": c["video"]} if "video" in c else {})}  # noqa: E731
    out = {
        "total": s["total"],
        "counts": s["counts"],
        "by_category": {k: [trim(c) for c in v] for k, v in s["top_by_category"].items()},
        "top_liked": [trim(c) for c in s["top_liked"]],
        "frequent_words": s["frequent_words"],
        "frequent_phrases": s["frequent_phrases"],
        "sample": [trim(c) for c in comments[:sample]],
    }
    if extra:
        out.update(extra)
    return out


def cmd_video(args):
    yt = client.public()
    vid = ids.video_id(args.video)
    com = data.comments(yt, vid, args.max, args.order, replies=args.replies)
    return pack(com, {"video_id": vid})


def _aggregate(yt, cid, args, uploads=None):
    vids = data.channel_videos(yt, cid, args.videos * 2 if args.skip_shorts else args.videos, uploads)
    if args.skip_shorts:
        vids = [v for v in vids if v["duration_s"] > 180][: args.videos]
    all_comments, per_video = [], []
    for v in vids:
        com = data.comments(yt, v["video_id"], args.per_video)
        for c in com:
            c["video"] = v["title"][:80]
        all_comments += com
        per_video.append({"title": v["title"], "views": v["views"], "comments_fetched": len(com),
                          "requests": sum(1 for c in com if "request" in analysis.categorize_comment(c["text"]))})
    result = pack(all_comments, {"videos": per_video})
    result["saved"] = str(util.save_json(all_comments, f"comments-{cid}-{datetime.now():%Y-%m-%d}.json", args.reports_dir))
    return result


def cmd_channel(args):
    yt = client.public()
    return _aggregate(yt, data.resolve_channel(yt, args.channel), args)


def cmd_mine(args):
    yt = client.owner()
    ch = data.my_channel(yt)
    return _aggregate(yt, ch["channel_id"], args, ch["uploads_playlist"])


def main():
    p = cli.parser(__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    v = sp.add_parser("video")
    v.add_argument("video")
    v.add_argument("--max", type=int, default=200)
    v.add_argument("--order", default="relevance", choices=["relevance", "time"])
    v.add_argument("--replies", action="store_true")
    for name in ("channel", "mine"):
        s = sp.add_parser(name)
        if name == "channel":
            s.add_argument("channel")
        s.add_argument("--videos", type=int, default=10)
        s.add_argument("--per-video", type=int, default=100)
        s.add_argument("--skip-shorts", action="store_true")
        cli.add_reports_dir(s)
    args = p.parse_args()
    return globals()["cmd_" + args.cmd](args)


if __name__ == "__main__":
    cli.run(main)
