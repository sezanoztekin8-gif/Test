#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-api-python-client>=2.100", "google-auth-oauthlib>=1.2", "google-auth>=2.23", "tzdata"]
# ///
"""Set up and check credentials. Run `doctor` first whenever something fails.

Commands
  doctor                 check everything: libraries, key, tokens, quota, channel
  set-key KEY            save a YouTube Data API key (public research)
  login                  browser sign-in for the READ token (analytics + your channel)
  login --revenue        same, plus revenue metrics (monetized channels)
  login --write          browser sign-in for the separate WRITE token (upload/edit/delete)
  login --manual         headless machines: copy/paste flow instead of a local browser
  status                 show which credentials exist
  whoami [--write]       which channel a token controls (always confirm before writes)
  revoke [--write]       revoke at Google and delete the local token
  quota [--reset]        today's local quota usage (Pacific-time day)

Examples
  python scripts/yt_auth.py doctor
  python scripts/yt_auth.py set-key AIza...
  python scripts/yt_auth.py login
  python scripts/yt_auth.py login --write
"""

import importlib.util
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ytkit import auth, cli, client, config, data, quota  # noqa: E402


def cmd_doctor(_args):
    libs = {
        name: importlib.util.find_spec(mod) is not None
        for name, mod in [
            ("google-api-python-client", "googleapiclient"),
            ("google-auth-oauthlib", "google_auth_oauthlib"),
            ("youtube-transcript-api", "youtube_transcript_api"),
            ("yt-dlp", "yt_dlp"),
            ("tzdata", "tzdata"),
        ]
    }
    libs["yt-dlp (command)"] = shutil.which("yt-dlp") is not None
    report = {
        "python": sys.version.split()[0],
        "skill_home": str(config.home()),
        "reports_dir": str(config.reports_dir()),
        "libraries": libs,
        "api_key": "set" if config.api_key() else "missing",
        "client_secret": "found" if config.client_secret_path().exists() else "missing",
        "read_token": auth.token_status("read"),
        "write_token": auth.token_status("write"),
        "quota": quota.status()["buckets"],
        "capabilities": {},
    }
    caps = report["capabilities"]
    caps["public_research"] = report["api_key"] == "set" or report["read_token"]["status"] == "ok"
    caps["own_analytics"] = report["read_token"]["status"] == "ok"
    caps["publishing"] = report["write_token"]["status"] == "ok"
    caps["transcripts"] = libs["youtube-transcript-api"] or libs["yt-dlp"] or libs["yt-dlp (command)"]

    if caps["own_analytics"]:
        try:
            ch = data.my_channel(client.owner())
            report["read_token"]["channel"] = f"{ch['title']} ({ch['channel_id']})"
        except Exception as exc:  # noqa: BLE001
            report["read_token"]["channel_error"] = str(exc)

    todo = []
    if not libs["google-api-python-client"]:
        todo.append("Install dependencies: pip install -r requirements.txt  (or use `uv run`)")
    if not caps["public_research"]:
        todo.append("Add an API key: python scripts/yt_auth.py set-key YOUR_KEY")
    if report["client_secret"] == "missing":
        todo.append(f"For analytics/publishing save your OAuth client JSON as {config.client_secret_path()}")
    elif not caps["own_analytics"]:
        todo.append("Sign in for analytics: python scripts/yt_auth.py login")
    if report["client_secret"] == "found" and not caps["publishing"]:
        todo.append("Optional, for uploads/edits: python scripts/yt_auth.py login --write")
    if not caps["transcripts"]:
        todo.append("Install youtube-transcript-api for transcripts")
    report["next_steps"] = todo or ["All set."]
    return report


def cmd_set_key(args):
    cfg = config.load_config()
    cfg["api_key"] = args.key.strip()
    path = config.save_config(cfg)
    result = {"saved": str(path)}
    try:
        yt = client.public()
        client.call(yt.videoCategories().list(part="snippet", regionCode="US"), "videoCategories.list")
        result["test"] = "API key works"
    except client.YtError as exc:
        result["test"] = f"API key saved but the test call failed: {exc}"
        result["fix"] = exc.fix
    return result


def cmd_login(args):
    kind = "write" if args.write else "read"
    path, _ = auth.login(kind, revenue=args.revenue, manual=args.manual, port=args.port)
    out = {"saved": str(path), "kind": kind}
    try:
        ch = data.my_channel(client.owner(write=args.write))
        out["channel"] = {"title": ch["title"], "id": ch["channel_id"], "subscribers": ch["subscribers"]}
        out["check"] = "Confirm this is the channel you meant to connect."
    except Exception as exc:  # noqa: BLE001
        out["channel_error"] = str(exc)
    return out


def cmd_status(_args):
    return {
        "api_key": "set" if config.api_key() else "missing",
        "client_secret": str(config.client_secret_path()) if config.client_secret_path().exists() else "missing",
        "read": auth.token_status("read"),
        "write": auth.token_status("write"),
    }


def cmd_whoami(args):
    ch = data.my_channel(client.owner(write=args.write))
    return {"token": "write" if args.write else "read", **{k: ch[k] for k in ("title", "channel_id", "handle", "subscribers", "video_count", "url")}}


def cmd_revoke(args):
    return auth.revoke("write" if args.write else "read")


def cmd_quota(args):
    if args.reset:
        quota.reset()
    return quota.status()


def main():
    p = cli.parser(__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("doctor")
    k = sp.add_parser("set-key")
    k.add_argument("key")
    lg = sp.add_parser("login")
    lg.add_argument("--write", action="store_true", help="separate token with youtube.force-ssl (uploads/edits)")
    lg.add_argument("--revenue", action="store_true", help="add yt-analytics-monetary.readonly to the read token")
    lg.add_argument("--manual", action="store_true", help="copy/paste flow for machines without a browser")
    lg.add_argument("--port", type=int, default=0)
    sp.add_parser("status")
    w = sp.add_parser("whoami")
    w.add_argument("--write", action="store_true")
    r = sp.add_parser("revoke")
    r.add_argument("--write", action="store_true")
    q = sp.add_parser("quota")
    q.add_argument("--reset", action="store_true", help="clear today's local counter (does not affect Google)")
    args = p.parse_args()
    if args.cmd == "login" and args.write and args.revenue:
        p.error("--revenue applies to the read token only")
    return globals()["cmd_" + args.cmd.replace("-", "_")](args)


if __name__ == "__main__":
    cli.run(main)
