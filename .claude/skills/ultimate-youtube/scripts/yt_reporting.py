#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-api-python-client>=2.100", "google-auth-oauthlib>=1.2", "google-auth>=2.23", "requests", "tzdata"]
# ///
"""Bulk reports from the YouTube Reporting API - the only API source of
thumbnail IMPRESSIONS and impressions CLICK-THROUGH RATE (CTR).

How it works: you create a reporting job once; YouTube then generates a daily
CSV for that job. The first files appear roughly 24-48 hours after the job is
created (with some historical backfill), so set this up early.

Commands
  types                       list report types available to your channel
  jobs                        list your reporting jobs
  setup [--type T]            create a job (default: channel_reach_basic_a1 = impressions + CTR)
  fetch [--type T] [--days N] download recent report files, merge, save CSV + JSON
  ctr [--days N] [--top N]    per-video impressions, CTR and views from the reach report

Examples
  python scripts/yt_reporting.py setup
  python scripts/yt_reporting.py ctr --days 28
"""

import csv
import io
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ytkit import cli, client, data, util  # noqa: E402
from ytkit.client import YtError, call  # noqa: E402

REACH = "channel_reach_basic_a1"


def svc():
    return client.reporting()


def find_job(rep, type_id):
    res = call(rep.jobs().list())
    for job in res.get("jobs", []):
        if job.get("reportTypeId") == type_id:
            return job
    return None


def cmd_types(_args):
    rep, _ = svc()
    res = call(rep.reportTypes().list())
    return [t["id"] for t in res.get("reportTypes", [])]


def cmd_jobs(_args):
    rep, _ = svc()
    return call(rep.jobs().list()).get("jobs", [])


def cmd_setup(args):
    rep, _ = svc()
    existing = find_job(rep, args.type)
    if existing:
        return {"exists": True, "job": existing}
    job = call(rep.jobs().create(body={"reportTypeId": args.type, "name": f"ultimate-youtube {args.type}"}))
    return {"created": True, "job": job, "note": "First report files usually appear within 24-48 hours."}


def download(rep, creds, type_id, days):
    job = find_job(rep, type_id)
    if not job:
        raise YtError(f"No reporting job for {type_id}.", f"Run: python scripts/yt_reporting.py setup --type {type_id} (then wait 24-48h)")
    since = (date.today() - timedelta(days=days + 2)).isoformat() + "T00:00:00Z"
    reports, token = [], None
    while True:
        res = call(rep.jobs().reports().list(jobId=job["id"], createdAfter=since, pageToken=token))
        reports += res.get("reports", [])
        token = res.get("nextPageToken")
        if not token:
            break
    if not reports:
        raise YtError("The job exists but no report files are available yet.", "Reports appear 24-48 hours after setup. Try again later.")
    from google.auth.transport.requests import AuthorizedSession

    session = AuthorizedSession(creds)
    rows, seen = [], set()
    # Newest file per covered day wins (YouTube may regenerate days).
    for r in sorted(reports, key=lambda r: r.get("createTime", ""), reverse=True):
        day = r.get("startTime", "")[:10]
        if day in seen:
            continue
        seen.add(day)
        resp = session.get(r["downloadUrl"], timeout=60)
        resp.raise_for_status()
        rows += list(csv.DictReader(io.StringIO(resp.content.decode("utf-8"))))
    return job, rows


def cmd_fetch(args):
    rep, creds = svc()
    job, rows = download(rep, creds, args.type, args.days)
    cutoff = (date.today() - timedelta(days=args.days)).strftime("%Y%m%d")
    rows = [r for r in rows if r.get("date", "99999999") >= cutoff]
    path = util.save_json(rows, f"reporting-{args.type}-{date.today().isoformat()}.json", args.reports_dir)
    return {"job": job["id"], "type": args.type, "rows": len(rows), "columns": list(rows[0].keys()) if rows else [], "saved": str(path)}


def cmd_ctr(args):
    rep, creds = svc()
    _, rows = download(rep, creds, REACH, args.days)
    cutoff = (date.today() - timedelta(days=args.days)).strftime("%Y%m%d")
    agg = defaultdict(lambda: {"impressions": 0, "clicks_est": 0.0})
    for r in rows:
        if r.get("date", "") < cutoff:
            continue
        imp = util.to_int(r.get("video_thumbnail_impressions"))
        ctr = float(r.get("video_thumbnail_impressions_ctr") or 0)
        if ctr > 1:  # tolerate percent-formatted values; the API documents a ratio
            ctr /= 100
        a = agg[r.get("video_id")]
        a["impressions"] += imp
        a["clicks_est"] += imp * ctr
    out = []
    for vid, a in agg.items():
        if not vid or not a["impressions"]:
            continue
        out.append({"video_id": vid, "impressions": a["impressions"], "ctr_pct": round(a["clicks_est"] / a["impressions"] * 100, 2)})
    out.sort(key=lambda r: -r["impressions"])
    out = out[: args.top]
    try:
        meta = {v["video_id"]: v for v in data.videos(client.public(), [r["video_id"] for r in out], parts="snippet,contentDetails")}
        for r in out:
            m = meta.get(r["video_id"])
            if m:
                r["title"] = m["title"]
                r["format"] = "short" if 0 < m["duration_s"] <= 180 else "long"
    except YtError:
        pass
    total_imp = sum(r["impressions"] for r in out)
    channel_ctr = round(sum(r["impressions"] * r["ctr_pct"] for r in out) / total_imp, 2) if total_imp else None
    return {"days": args.days, "channel_ctr_pct_weighted": channel_ctr, "videos": out,
            "how_to_read": "CTR depends on traffic source and audience size; compare a video with your own channel's typical CTR, not a universal benchmark."}


def main():
    p = cli.parser(__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("types")
    sp.add_parser("jobs")
    s = sp.add_parser("setup")
    s.add_argument("--type", default=REACH)
    f = sp.add_parser("fetch")
    f.add_argument("--type", default=REACH)
    f.add_argument("--days", type=int, default=28)
    cli.add_reports_dir(f)
    c = sp.add_parser("ctr")
    c.add_argument("--days", type=int, default=28)
    c.add_argument("--top", type=int, default=30)
    args = p.parse_args()
    return globals()["cmd_" + args.cmd](args)


if __name__ == "__main__":
    cli.run(main)
