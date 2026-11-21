#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-api-python-client>=2.100", "google-auth-oauthlib>=1.2", "google-auth>=2.23", "tzdata"]
# ///
"""Lint and audit titles, descriptions, tags, hashtags and chapters.

Commands
  lint --title "..." [--description @desc.txt] [--tags "a,b"] [--keyword "..."] [--duration 600] [--short]
        check a draft BEFORE publishing (no API calls)
  video VIDEO [--keyword "..."]
        audit any public video's live metadata
  channel CHANNEL [--max 50] [--mine]
        audit every recent upload, worst first (use --mine to include private videos)
  chapters @desc.txt [--duration 600]
        validate chapter timestamps only

Scores start at 100: -20 per ERROR (breaks a YouTube rule), -6 per WARN.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ytkit import analysis, cli, client, data, ids, seo, util  # noqa: E402


def cmd_lint(args):
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    return seo.lint(util.read_text_arg(args.title) or "", util.read_text_arg(args.description) or "", tags,
                    args.keyword, args.duration, args.short)


def audit(v, keyword=None):
    res = seo.lint(v["title"], v["description"], v["tags"], keyword, v["duration_s"], analysis.is_short(v))
    return {"video_id": v["video_id"], "title": v["title"], "views": v["views"], "url": v["url"], **res}


def cmd_video(args):
    yt = client.public()
    vids = data.videos(yt, [ids.video_id(args.video)])
    if not vids:
        util.fail("Video not found or not public")
    return audit(vids[0], args.keyword)


def cmd_channel(args):
    if args.mine:
        yt = client.owner()
        ch = data.my_channel(yt)
        vids = data.channel_videos(yt, ch["channel_id"], args.max, ch["uploads_playlist"])
    else:
        yt = client.public()
        vids = data.channel_videos(yt, data.resolve_channel(yt, args.channel), args.max)
    rows = sorted((audit(v) for v in vids), key=lambda r: r["score"])
    common = {}
    for r in rows:
        for i in r["issues"]:
            key = i.split(":")[0] + ":" + i.split(":")[1].split(";")[0][:60] if ":" in i else i
            common[key] = common.get(key, 0) + 1
    path = util.save_json(rows, "seo-audit.json", args.reports_dir)
    return {
        "videos": len(rows),
        "median_score": util.median(r["score"] for r in rows),
        "most_common_issues": sorted(common.items(), key=lambda kv: -kv[1])[:12],
        "worst": [{k: r[k] for k in ("title", "score", "issues", "url")} for r in rows[: args.show]],
        "saved": str(path),
    }


def cmd_chapters(args):
    text = util.read_text_arg(args.description) or ""
    ch = seo.parse_chapters(text)
    return {"chapters": ch, "issues": seo.check_chapters(ch, args.duration) or ["OK"]}


def main():
    p = cli.parser(__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    l = sp.add_parser("lint")
    l.add_argument("--title", required=True)
    l.add_argument("--description")
    l.add_argument("--tags")
    l.add_argument("--keyword")
    l.add_argument("--duration", type=int, help="video length in seconds (for chapter checks)")
    l.add_argument("--short", action="store_true", help="the video is a Short")
    v = sp.add_parser("video")
    v.add_argument("video")
    v.add_argument("--keyword")
    c = sp.add_parser("channel")
    c.add_argument("channel", nargs="?")
    c.add_argument("--mine", action="store_true")
    c.add_argument("--max", type=int, default=50)
    c.add_argument("--show", type=int, default=10)
    cli.add_reports_dir(c)
    ch = sp.add_parser("chapters")
    ch.add_argument("description", help="text or @file")
    ch.add_argument("--duration", type=int)
    args = p.parse_args()
    if args.cmd == "channel" and not (args.channel or args.mine):
        p.error("give a CHANNEL or --mine")
    return globals()["cmd_" + args.cmd](args)


if __name__ == "__main__":
    cli.run(main)
