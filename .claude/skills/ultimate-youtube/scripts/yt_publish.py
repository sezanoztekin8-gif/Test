#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-api-python-client>=2.100", "google-auth-oauthlib>=1.2", "google-auth>=2.23", "tzdata"]
# ///
"""Publish and manage videos on YOUR channel (YouTube Data API v3, write token).

SAFETY MODEL - every command that changes the channel:
  * runs as a DRY RUN by default and prints a preview / diff,
  * only writes when re-run with --confirm (after the user approved the preview),
  * backs up the current metadata before any update or delete,
  * can be undone with `revert` (metadata) - deletes cannot be undone.
Uploads default to PRIVATE. Never pass --confirm without explicit user approval.

Commands
  mine [--max N]                          your uploads incl. private/scheduled
  get VIDEO                               full current metadata of one of your videos
  status VIDEO                            upload/processing status, rejection reasons
  upload FILE [metadata options]          resumable upload (default privacy: private)
  update VIDEO [metadata options]         change title/description/tags/privacy/schedule...
  revert VIDEO [--backup PATH]            restore metadata from the latest backup
  backups [VIDEO]                         list metadata backups
  delete VIDEO                            permanently delete (backs up metadata first)
  thumbnail VIDEO IMAGE                   set a custom thumbnail (JPG/PNG, <= 2 MB)
  localize VIDEO --lang hi --title ...    add/replace a translated title & description
  captions list|upload|delete             manage caption tracks
  playlist list|create|add|remove|delete  manage playlists
  categories [--region IN]                assignable category IDs

Metadata options (upload/update)
  --title, --description (text or @file.txt), --tags "a,b,c", --category ID,
  --privacy private|unlisted|public, --publish-at 2026-12-01T15:30:00Z (schedules; needs private),
  --made-for-kids / --not-made-for-kids, --language hi, --audio-language hi,
  --synthetic-media yes|no (altered/synthetic content disclosure), --license youtube|creativeCommon,
  --embeddable yes|no, --public-stats yes|no, --metadata file.json (any of the above as JSON keys)
Upload-only: --thumbnail IMG, --playlist ID, --captions FILE --captions-lang xx, --no-notify
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ytkit import cli, client, config, data, ids, util  # noqa: E402
from ytkit.client import YtError, call  # noqa: E402

SNIPPET_FIELDS = ("title", "description", "tags", "categoryId", "defaultLanguage", "defaultAudioLanguage")
STATUS_FIELDS = ("privacyStatus", "publishAt", "license", "embeddable", "publicStatsViewable",
                 "selfDeclaredMadeForKids", "containsSyntheticMedia")
VIDEO_EXT = {".mov", ".mpeg4", ".mp4", ".avi", ".wmv", ".mpegps", ".flv", ".3gpp", ".webm", ".mkv", ".m4v"}
THUMB_EXT = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}


# ---------------------------------------------------------------- helpers

def yt_write():
    return client.owner(write=True)


def yesno(value):
    if value is None:
        return None
    return str(value).lower() in ("yes", "true", "1", "y")


def collect_metadata(args) -> dict:
    """Merge --metadata JSON with explicit flags (flags win). Keys use API names."""
    meta: dict = {}
    if getattr(args, "metadata", None):
        raw = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
        alias = {"category": "categoryId", "privacy": "privacyStatus", "publish_at": "publishAt",
                 "language": "defaultLanguage", "audio_language": "defaultAudioLanguage",
                 "made_for_kids": "selfDeclaredMadeForKids", "synthetic_media": "containsSyntheticMedia",
                 "public_stats": "publicStatsViewable"}
        for k, v in raw.items():
            meta[alias.get(k, k)] = v
    flags = {
        "title": util.read_text_arg(args.title),
        "description": util.read_text_arg(args.description),
        "tags": [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags is not None else None,
        "categoryId": args.category,
        "privacyStatus": args.privacy,
        "publishAt": args.publish_at,
        "defaultLanguage": args.language,
        "defaultAudioLanguage": args.audio_language,
        "selfDeclaredMadeForKids": args.made_for_kids,
        "containsSyntheticMedia": yesno(args.synthetic_media),
        "license": args.license,
        "embeddable": yesno(args.embeddable),
        "publicStatsViewable": yesno(args.public_stats),
    }
    meta.update({k: v for k, v in flags.items() if v is not None})
    if isinstance(meta.get("tags"), str):
        meta["tags"] = [t.strip() for t in meta["tags"].split(",") if t.strip()]
    return meta


def validate(meta: dict) -> list[str]:
    problems = []
    title = meta.get("title")
    if title is not None:
        if not title.strip():
            problems.append("Title is empty.")
        if len(title) > 100:
            problems.append(f"Title is {len(title)} chars; the limit is 100.")
    for field in ("title", "description"):
        if meta.get(field) and ("<" in meta[field] or ">" in meta[field]):
            problems.append(f"{field} contains '<' or '>', which YouTube rejects.")
    desc = meta.get("description")
    if desc and len(desc.encode("utf-8")) > 5000:
        problems.append(f"Description is {len(desc.encode('utf-8'))} bytes; the limit is 5000 bytes.")
    tags = meta.get("tags")
    if tags:
        total = sum(len(t) + (2 if " " in t else 0) for t in tags) + max(len(tags) - 1, 0)
        if total > 500:
            problems.append(f"Tags total ~{total} chars; the limit is 500 (tags with spaces count +2).")
    if meta.get("publishAt"):
        when = util.parse_time(meta["publishAt"])
        if not when or when.tzinfo is None:
            problems.append("--publish-at must be ISO 8601 with timezone, e.g. 2026-12-01T15:30:00Z or +05:30.")
        elif when <= datetime.now(timezone.utc):
            problems.append("--publish-at is in the past.")
        if meta.get("privacyStatus") not in (None, "private"):
            problems.append("Scheduling (--publish-at) requires privacy 'private'; YouTube flips it public at that time.")
    if meta.get("privacyStatus") not in (None, "private", "unlisted", "public"):
        problems.append("privacy must be private, unlisted or public.")
    return problems


def backup(video_id: str, snapshot: dict, kind: str = "pre-edit") -> Path:
    folder = config.sub("backups", video_id)
    path = folder / f"{util.stamp()}-{kind}.json"
    path.write_text(util.dumps({"video_id": video_id, "kind": kind, "taken_at": util.now_utc().isoformat(), **snapshot}), encoding="utf-8")
    return path


def fetch_current(yt, video_id: str) -> dict:
    res = call(yt.videos().list(part="snippet,status,localizations,statistics", id=video_id), "videos.list")
    items = res.get("items", [])
    if not items:
        raise YtError(f"Video {video_id} not found on the authorized channel.", "Check the ID and that the token belongs to the owning channel (yt_auth.py whoami --write).")
    return items[0]


def writable(part: dict, fields) -> dict:
    return {k: part[k] for k in fields if k in part}


def diff(old: dict, new: dict) -> list[dict]:
    rows = []
    for k in sorted(set(old) | set(new)):
        if old.get(k) != new.get(k):
            a, b = old.get(k), new.get(k)
            if k == "description":
                a = (a or "")[:300] + ("..." if a and len(a) > 300 else "")
                b = (b or "")[:300] + ("..." if b and len(b) > 300 else "")
            rows.append({"field": k, "old": a, "new": b})
    return rows


def winner_warning(yt, item: dict) -> str | None:
    """Warn before repackaging a video that is currently one of the channel's best."""
    try:
        ch_id = item["snippet"]["channelId"]
        recent = data.channel_videos(yt, ch_id, limit=50)
        views = sorted(v["views"] for v in recent)
        if len(views) >= 10:
            p90 = views[int(len(views) * 0.9) - 1]
            mine = util.to_int(item.get("statistics", {}).get("viewCount"))
            if mine >= p90:
                return ("This video is in the channel's top 10% by views. Changing the title or "
                        "thumbnail of a winner can reset how YouTube tests it. Recommend leaving it alone "
                        "unless the user insists.")
    except YtError:
        return None
    return None


def resumable(request, label: str):
    """Drive a resumable upload with progress and retries."""
    from googleapiclient.errors import HttpError

    response, retry = None, 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                util.eprint(f"{label}: {int(status.progress() * 100)}%")
        except HttpError as exc:
            if exc.resp.status in (500, 502, 503, 504) and retry < 8:
                retry += 1
                time.sleep(min(2 ** retry, 60))
                continue
            raise
        except (ConnectionError, TimeoutError, OSError):
            if retry < 8:
                retry += 1
                time.sleep(min(2 ** retry, 60))
                continue
            raise
    return response


# ---------------------------------------------------------------- read commands

def cmd_mine(args):
    yt = client.owner()
    ch = data.my_channel(yt)
    vids = data.channel_videos(yt, ch["channel_id"], args.max, ch["uploads_playlist"])
    rows = [{k: v[k] for k in ("video_id", "title", "published_at", "privacy", "publish_at", "views", "duration", "url")} for v in vids]
    return {"channel": ch["title"], "count": len(rows), "videos": rows}


def cmd_get(args):
    yt = client.owner()
    vid = ids.video_id(args.video)
    item = fetch_current(yt, vid)
    return {"video_id": vid, "snippet": writable(item["snippet"], SNIPPET_FIELDS),
            "status": item.get("status"), "localizations": item.get("localizations", {}),
            "statistics": item.get("statistics")}


def cmd_status(args):
    yt = client.owner()
    vid = ids.video_id(args.video)
    res = call(yt.videos().list(part="status,processingDetails,suggestions", id=vid), "videos.list")
    if not res.get("items"):
        raise YtError(f"Video {vid} not found on this channel.")
    return res["items"][0]


def cmd_categories(args):
    yt = client.public()
    res = call(yt.videoCategories().list(part="snippet", regionCode=args.region, hl=args.hl), "videoCategories.list")
    return [{"id": c["id"], "title": c["snippet"]["title"]} for c in res.get("items", []) if c["snippet"].get("assignable")]


def cmd_backups(args):
    root = config.sub("backups")
    folders = [root / ids.video_id(args.video)] if args.video else sorted(p for p in root.iterdir() if p.is_dir())
    out = []
    for folder in folders:
        for f in sorted(folder.glob("*.json")):
            out.append({"video_id": folder.name, "file": str(f)})
    return out


# ---------------------------------------------------------------- upload

def cmd_upload(args):
    path = Path(args.file).expanduser()
    if not path.is_file():
        raise ValueError(f"File not found: {path}")
    if path.suffix.lower() not in VIDEO_EXT:
        util.eprint(f"warning: {path.suffix} is not a common YouTube video format")
    meta = collect_metadata(args)
    meta.setdefault("title", path.stem[:100])
    meta.setdefault("privacyStatus", "private")
    meta.setdefault("categoryId", "22")
    if meta.get("selfDeclaredMadeForKids") is None:
        raise ValueError("Pass --made-for-kids or --not-made-for-kids (YouTube requires an audience declaration).")
    problems = validate(meta)
    if problems:
        return {"error": "Fix these before uploading", "problems": problems}

    snippet = {k: meta[k] for k in SNIPPET_FIELDS if k in meta}
    status = {k: meta[k] for k in STATUS_FIELDS if k in meta}
    body = {"snippet": snippet, "status": status}
    plan = {
        "action": "upload",
        "file": str(path),
        "size_mb": round(path.stat().st_size / 1_048_576, 1),
        "body": body,
        "notify_subscribers": not args.no_notify,
        "after_upload": {k: v for k, v in {"thumbnail": args.thumbnail, "playlist": args.playlist,
                                            "captions": args.captions}.items() if v},
        "quota": "1 call from the upload bucket (+50 thumbnail, +50 playlist, +400 captions)",
        "notes": [
            "Projects that have not passed Google's API audit can only upload PRIVATE videos; "
            "make them public later in YouTube Studio or after the audit.",
        ],
    }
    if not args.confirm:
        return {**plan, **cli.confirm_note("upload")}

    from googleapiclient.http import MediaFileUpload

    yt = yt_write()
    who = data.my_channel(yt)
    media = MediaFileUpload(str(path), chunksize=16 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media, notifySubscribers=not args.no_notify)
    from ytkit import quota
    ok, why = quota.can_afford("videos.insert")
    if not ok:
        raise YtError(why)
    response = resumable(req, "upload")
    quota.record("videos.insert")
    vid = response["id"]
    result = {"uploaded": True, "video_id": vid, "url": ids.watch_url(vid), "channel": who["title"],
              "privacy": response.get("status", {}).get("privacyStatus"), "follow_up": []}
    if args.thumbnail:
        try:
            result["follow_up"].append(set_thumbnail(yt, vid, args.thumbnail))
        except Exception as exc:  # noqa: BLE001
            result["follow_up"].append({"thumbnail_error": str(exc)})
    if args.playlist:
        try:
            result["follow_up"].append(playlist_add(yt, ids.playlist_id(args.playlist), vid, None))
        except Exception as exc:  # noqa: BLE001
            result["follow_up"].append({"playlist_error": str(exc)})
    if args.captions:
        try:
            result["follow_up"].append(caption_upload(yt, vid, args.captions, args.captions_lang or meta.get("defaultLanguage") or "en", "", False))
        except Exception as exc:  # noqa: BLE001
            result["follow_up"].append({"captions_error": str(exc)})
    result["next"] = f"Check processing with: python scripts/yt_publish.py status {vid}"
    return result


# ---------------------------------------------------------------- update / revert / delete

def cmd_update(args):
    vid = ids.video_id(args.video)
    meta = collect_metadata(args)
    if not meta:
        raise ValueError("Nothing to change. Pass at least one metadata option.")
    problems = validate(meta)
    if problems:
        return {"error": "Fix these first", "problems": problems}

    yt = yt_write()
    item = fetch_current(yt, vid)
    old_sn = writable(item["snippet"], SNIPPET_FIELDS)
    old_st = writable(item.get("status", {}), STATUS_FIELDS)
    new_sn = {**old_sn, **{k: v for k, v in meta.items() if k in SNIPPET_FIELDS}}
    new_st = {**old_st, **{k: v for k, v in meta.items() if k in STATUS_FIELDS}}
    if "publishAt" in meta and "privacyStatus" not in meta:
        new_st["privacyStatus"] = "private"
    if new_st.get("privacyStatus") in ("public", "unlisted") and "publishAt" not in meta:
        new_st.pop("publishAt", None)

    changes = diff(old_sn, new_sn) + diff(old_st, new_st)
    if not changes:
        return {"video_id": vid, "result": "no changes - the video already has these values"}
    preview = {"action": "update", "video_id": vid, "current_title": old_sn.get("title"),
               "channel": item["snippet"].get("channelTitle"), "changes": changes,
               "quota": "50 units"}
    if any(c["field"] == "title" for c in changes):
        warn = winner_warning(yt, item)
        if warn:
            preview["warning"] = warn
    if not args.confirm:
        return {**preview, **cli.confirm_note("apply the update")}

    snap = backup(vid, {"snippet": old_sn, "status": old_st, "localizations": item.get("localizations", {})})
    parts, body = [], {"id": vid}
    if new_sn != old_sn:
        parts.append("snippet")
        body["snippet"] = new_sn
    if new_st != old_st:
        parts.append("status")
        body["status"] = new_st
    call(yt.videos().update(part=",".join(parts), body=body), "videos.update")
    return {"updated": True, "video_id": vid, "changes": changes, "backup": str(snap),
            "undo": f"python scripts/yt_publish.py revert {vid} --confirm"}


def _latest_backup(vid: str) -> Path | None:
    folder = config.home() / "backups" / vid
    files = sorted(p for p in folder.glob("*.json") if "pre-edit" in p.name or "pre-delete" in p.name) if folder.exists() else []
    return files[-1] if files else None


def cmd_revert(args):
    vid = ids.video_id(args.video)
    path = Path(args.backup) if args.backup else _latest_backup(vid)
    if not path or not path.exists():
        raise ValueError(f"No backup found for {vid}.")
    saved = json.loads(path.read_text(encoding="utf-8"))
    yt = yt_write()
    item = fetch_current(yt, vid)
    cur_sn = writable(item["snippet"], SNIPPET_FIELDS)
    cur_st = writable(item.get("status", {}), STATUS_FIELDS)
    target_sn = saved.get("snippet", cur_sn)
    target_st = saved.get("status", cur_st)
    if target_st.get("publishAt") and util.parse_time(target_st["publishAt"]) and util.parse_time(target_st["publishAt"]) <= datetime.now(timezone.utc):
        target_st = {k: v for k, v in target_st.items() if k != "publishAt"}
    changes = diff(cur_sn, target_sn) + diff(cur_st, target_st)
    if not changes:
        return {"video_id": vid, "result": "already matches the backup", "backup": str(path)}
    if not args.confirm:
        return {"action": "revert", "video_id": vid, "backup": str(path), "changes": changes, **cli.confirm_note("revert")}
    pre = backup(vid, {"snippet": cur_sn, "status": cur_st}, kind="pre-revert")
    parts, body = [], {"id": vid}
    if target_sn != cur_sn:
        parts.append("snippet")
        body["snippet"] = target_sn
    if target_st != cur_st:
        parts.append("status")
        body["status"] = target_st
    call(yt.videos().update(part=",".join(parts), body=body), "videos.update")
    return {"reverted": True, "video_id": vid, "from_backup": str(path), "pre_revert_backup": str(pre), "changes": changes}


def cmd_delete(args):
    vid = ids.video_id(args.video)
    yt = yt_write()
    item = fetch_current(yt, vid)
    info = {"video_id": vid, "title": item["snippet"]["title"], "channel": item["snippet"].get("channelTitle"),
            "privacy": item["status"].get("privacyStatus"),
            "views": util.to_int(item.get("statistics", {}).get("viewCount"))}
    if not args.confirm:
        return {"action": "DELETE (permanent, cannot be undone - views, comments and URL are lost)",
                **info, "safer_alternative": f"Make it private instead: yt_publish.py update {vid} --privacy private",
                **cli.confirm_note("permanently delete the video")}
    snap = backup(vid, {"snippet": item["snippet"], "status": item.get("status"),
                        "localizations": item.get("localizations", {}), "statistics": item.get("statistics")}, kind="pre-delete")
    call(yt.videos().delete(id=vid), "videos.delete")
    return {"deleted": True, **info, "metadata_backup": str(snap)}


# ---------------------------------------------------------------- thumbnails

def _image_size(path: Path):
    try:
        from PIL import Image  # optional

        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def set_thumbnail(yt, vid: str, image: str) -> dict:
    from googleapiclient.http import MediaFileUpload

    path = Path(image).expanduser()
    call(yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(path))), "thumbnails.set")
    return {"thumbnail_set": True, "video_id": vid, "image": str(path)}


def cmd_thumbnail(args):
    vid = ids.video_id(args.video)
    path = Path(args.image).expanduser()
    if not path.is_file():
        raise ValueError(f"Image not found: {path}")
    problems = []
    if path.suffix.lower() not in THUMB_EXT:
        problems.append("Use JPG, PNG, GIF or BMP.")
    if path.stat().st_size > 2 * 1024 * 1024:
        problems.append(f"Image is {path.stat().st_size / 1_048_576:.1f} MB; the limit is 2 MB.")
    size = _image_size(path)
    notes = []
    if size and (size[0] < 640 or abs(size[0] / size[1] - 16 / 9) > 0.05):
        notes.append(f"Image is {size[0]}x{size[1]}; recommended 1280x720 (16:9), min width 640.")
    if problems:
        return {"error": "Thumbnail rejected", "problems": problems}
    if not args.confirm:
        return {"action": "set thumbnail", "video_id": vid, "image": str(path), "size": size, "notes": notes +
                ["Custom thumbnails need a phone-verified channel."], "quota": "50 units", **cli.confirm_note("set the thumbnail")}
    return set_thumbnail(yt_write(), vid, str(path))


# ---------------------------------------------------------------- localizations

def cmd_localize(args):
    vid = ids.video_id(args.video)
    yt = yt_write()
    item = fetch_current(yt, vid)
    sn = writable(item["snippet"], SNIPPET_FIELDS)
    locs = dict(item.get("localizations", {}))
    title = util.read_text_arg(args.title)
    desc = util.read_text_arg(args.description)
    if not title:
        raise ValueError("--title is required for a localization")
    problems = validate({"title": title, "description": desc or ""})
    if problems:
        return {"error": "Fix these first", "problems": problems}
    if not sn.get("defaultLanguage") and not args.default_language:
        raise ValueError("The video has no default language. Pass --default-language (the language of the original title).")
    new_sn = dict(sn)
    if args.default_language:
        new_sn["defaultLanguage"] = args.default_language
    before = locs.get(args.lang)
    locs[args.lang] = {"title": title, "description": desc if desc is not None else (before or {}).get("description", "")}
    preview = {"action": "localize", "video_id": vid, "language": args.lang, "old": before, "new": locs[args.lang],
               "default_language": new_sn.get("defaultLanguage"), "quota": "50 units"}
    if not args.confirm:
        return {**preview, **cli.confirm_note("save the translation")}
    snap = backup(vid, {"snippet": sn, "status": writable(item.get("status", {}), STATUS_FIELDS), "localizations": item.get("localizations", {})})
    call(yt.videos().update(part="snippet,localizations", body={"id": vid, "snippet": new_sn, "localizations": locs}), "videos.update")
    return {"localized": True, **preview, "backup": str(snap)}


# ---------------------------------------------------------------- captions

def caption_upload(yt, vid, file, lang, name, draft) -> dict:
    from googleapiclient.http import MediaFileUpload

    body = {"snippet": {"videoId": vid, "language": lang, "name": name or "", "isDraft": bool(draft)}}
    media = MediaFileUpload(str(Path(file).expanduser()), mimetype="application/octet-stream", resumable=True)
    from ytkit import quota
    ok, why = quota.can_afford("captions.insert")
    if not ok:
        raise YtError(why)
    res = resumable(yt.captions().insert(part="snippet", body=body, media_body=media), "captions")
    quota.record("captions.insert")
    return {"caption_uploaded": True, "caption_id": res.get("id"), "language": lang}


def cmd_captions(args):
    if args.action == "list":
        yt = client.owner()
        vid = ids.video_id(args.target)
        res = call(yt.captions().list(part="snippet", videoId=vid), "captions.list")
        return [{"id": c["id"], **{k: c["snippet"].get(k) for k in ("language", "name", "trackKind", "isDraft", "status", "lastUpdated")}} for c in res.get("items", [])]
    if args.action == "upload":
        vid = ids.video_id(args.target)
        if not args.file or not Path(args.file).is_file():
            raise ValueError("--file must point to an .srt/.vtt/.sbv caption file")
        cli.need(args, "lang")
        if not args.confirm:
            return {"action": "upload captions", "video_id": vid, "file": args.file, "language": args.lang,
                    "quota": "400 units", **cli.confirm_note("upload the captions")}
        return caption_upload(yt_write(), vid, args.file, args.lang, args.name, args.draft)
    if args.action == "delete":
        if not args.confirm:
            return {"action": "delete caption track", "caption_id": args.target, **cli.confirm_note("delete the caption track")}
        call(yt_write().captions().delete(id=args.target), "captions.delete")
        return {"deleted_caption": args.target}
    raise ValueError("captions action must be list, upload or delete")


# ---------------------------------------------------------------- playlists

def playlist_add(yt, pl, vid, position) -> dict:
    snippet = {"playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": vid}}
    if position is not None:
        snippet["position"] = position
    res = call(yt.playlistItems().insert(part="snippet", body={"snippet": snippet}), "playlistItems.insert")
    return {"added_to_playlist": pl, "video_id": vid, "item_id": res.get("id")}


def cmd_playlist(args):
    a = args.action
    if a == "list":
        yt = client.owner()
        out, token = [], None
        while True:
            res = call(yt.playlists().list(part="snippet,contentDetails,status", mine=True, maxResults=50, pageToken=token), "playlists.list")
            out += [{"id": p["id"], "title": p["snippet"]["title"], "videos": p["contentDetails"]["itemCount"],
                     "privacy": p["status"]["privacyStatus"]} for p in res.get("items", [])]
            token = res.get("nextPageToken")
            if not token:
                return out
    if a == "create":
        cli.need(args, "title")
        body = {"snippet": {"title": args.title, "description": util.read_text_arg(args.description) or ""},
                "status": {"privacyStatus": args.privacy or "public"}}
        if args.language:
            body["snippet"]["defaultLanguage"] = args.language
        if not args.confirm:
            return {"action": "create playlist", "body": body, "quota": "50 units", **cli.confirm_note("create it")}
        res = call(yt_write().playlists().insert(part="snippet,status", body=body), "playlists.insert")
        return {"created": True, "playlist_id": res["id"], "title": args.title}
    if a in ("add", "remove"):
        cli.need(args, "playlist", "video")
        pl, vid = ids.playlist_id(args.playlist), ids.video_id(args.video)
        if not args.confirm:
            return {"action": f"{a} video", "playlist": pl, "video_id": vid, "quota": "50 units", **cli.confirm_note(a)}
        yt = yt_write()
        if a == "add":
            return playlist_add(yt, pl, vid, args.position)
        res = call(yt.playlistItems().list(part="id", playlistId=pl, videoId=vid, maxResults=50), "playlistItems.list")
        removed = []
        for it in res.get("items", []):
            call(yt.playlistItems().delete(id=it["id"]), "playlistItems.delete")
            removed.append(it["id"])
        return {"removed_items": removed, "playlist": pl, "video_id": vid}
    if a == "delete":
        cli.need(args, "playlist")
        pl = ids.playlist_id(args.playlist)
        if not args.confirm:
            return {"action": "DELETE playlist (videos are kept)", "playlist": pl, **cli.confirm_note("delete the playlist")}
        call(yt_write().playlists().delete(id=pl), "playlists.delete")
        return {"deleted_playlist": pl}
    raise ValueError("playlist action must be list, create, add, remove or delete")


# ---------------------------------------------------------------- argparse

def add_meta(p):
    p.add_argument("--title")
    p.add_argument("--description", help="text, or @path/to/description.txt")
    p.add_argument("--tags", help="comma separated")
    p.add_argument("--category", help="category ID (see `categories`)")
    p.add_argument("--privacy", choices=["private", "unlisted", "public"])
    p.add_argument("--publish-at", help="ISO 8601 with timezone; schedules a private video")
    kids = p.add_mutually_exclusive_group()
    kids.add_argument("--made-for-kids", dest="made_for_kids", action="store_const", const=True)
    kids.add_argument("--not-made-for-kids", dest="made_for_kids", action="store_const", const=False)
    p.add_argument("--language", help="defaultLanguage of title/description, e.g. en, hi, es")
    p.add_argument("--audio-language", help="defaultAudioLanguage")
    p.add_argument("--synthetic-media", choices=["yes", "no"], help="altered or synthetic content disclosure")
    p.add_argument("--license", choices=["youtube", "creativeCommon"])
    p.add_argument("--embeddable", choices=["yes", "no"])
    p.add_argument("--public-stats", choices=["yes", "no"])
    p.add_argument("--metadata", help="JSON file with any of the fields above")
    p.add_argument("--confirm", action="store_true", help="actually write (only after user approval)")


def main():
    p = cli.parser(__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    m = sp.add_parser("mine")
    m.add_argument("--max", type=int, default=50)
    for name in ("get", "status"):
        sp.add_parser(name).add_argument("video")
    c = sp.add_parser("categories")
    c.add_argument("--region", default="US")
    c.add_argument("--hl", default="en")
    up = sp.add_parser("upload")
    up.add_argument("file")
    add_meta(up)
    up.add_argument("--thumbnail")
    up.add_argument("--playlist")
    up.add_argument("--captions")
    up.add_argument("--captions-lang")
    up.add_argument("--no-notify", action="store_true", help="don't notify subscribers")
    u = sp.add_parser("update")
    u.add_argument("video")
    add_meta(u)
    r = sp.add_parser("revert")
    r.add_argument("video")
    r.add_argument("--backup")
    r.add_argument("--confirm", action="store_true")
    b = sp.add_parser("backups")
    b.add_argument("video", nargs="?")
    d = sp.add_parser("delete")
    d.add_argument("video")
    d.add_argument("--confirm", action="store_true")
    t = sp.add_parser("thumbnail")
    t.add_argument("video")
    t.add_argument("image")
    t.add_argument("--confirm", action="store_true")
    lo = sp.add_parser("localize")
    lo.add_argument("video")
    lo.add_argument("--lang", required=True)
    lo.add_argument("--title")
    lo.add_argument("--description")
    lo.add_argument("--default-language")
    lo.add_argument("--confirm", action="store_true")
    cap = sp.add_parser("captions")
    cap.add_argument("action", choices=["list", "upload", "delete"])
    cap.add_argument("target", help="video (list/upload) or caption ID (delete)")
    cap.add_argument("--file")
    cap.add_argument("--lang")
    cap.add_argument("--name", default="")
    cap.add_argument("--draft", action="store_true")
    cap.add_argument("--confirm", action="store_true")
    pl = sp.add_parser("playlist")
    pl.add_argument("action", choices=["list", "create", "add", "remove", "delete"])
    pl.add_argument("--playlist")
    pl.add_argument("--video")
    pl.add_argument("--position", type=int)
    pl.add_argument("--title")
    pl.add_argument("--description")
    pl.add_argument("--privacy", choices=["private", "unlisted", "public"])
    pl.add_argument("--language")
    pl.add_argument("--confirm", action="store_true")
    args = p.parse_args()
    return globals()["cmd_" + args.cmd](args)


if __name__ == "__main__":
    cli.run(main)
