"""Parse YouTube IDs out of whatever the user pastes."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
CHANNEL_ID = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
PLAYLIST_ID = re.compile(r"^(PL|UU|LL|FL|OL|RD)[A-Za-z0-9_-]{10,}$")


def video_id(raw: str) -> str:
    """Accept an ID, watch URL, youtu.be, /shorts/, /live/ or /embed/ link."""
    raw = raw.strip()
    if VIDEO_ID.match(raw):
        return raw
    try:
        url = urlparse(raw if "://" in raw else "https://" + raw)
    except ValueError:
        url = None
    if url and url.netloc:
        host = url.netloc.lower()
        if host.endswith("youtu.be"):
            cand = url.path.strip("/").split("/")[0]
            if VIDEO_ID.match(cand):
                return cand
        qs = parse_qs(url.query)
        if "v" in qs and VIDEO_ID.match(qs["v"][0]):
            return qs["v"][0]
        m = re.search(r"/(?:shorts|live|embed|v)/([A-Za-z0-9_-]{11})", url.path)
        if m:
            return m.group(1)
    raise ValueError(f"Could not find a YouTube video ID in: {raw!r}")


def video_ids(raws) -> list[str]:
    out: list[str] = []
    for raw in raws:
        for part in str(raw).split(","):
            if part.strip():
                out.append(video_id(part))
    return list(dict.fromkeys(out))


def channel_ref(raw: str) -> dict:
    """Classify a channel reference.

    Returns one of:
        {"id": "UC..."}            channel ID or /channel/UC... URL
        {"handle": "@name"}        @handle or /@handle URL
        {"username": "name"}       legacy /user/name URL
        {"query": "text"}          /c/custom URL or free text (needs search)
    """
    raw = raw.strip()
    if CHANNEL_ID.match(raw):
        return {"id": raw}
    if raw.startswith("@"):
        return {"handle": raw}
    try:
        url = urlparse(raw if "://" in raw else "https://" + raw)
    except ValueError:
        url = None
    if url and url.netloc and "youtube" in url.netloc.lower():
        parts = [p for p in url.path.split("/") if p]
        if parts:
            if parts[0] == "channel" and len(parts) > 1 and CHANNEL_ID.match(parts[1]):
                return {"id": parts[1]}
            if parts[0].startswith("@"):
                return {"handle": parts[0]}
            if parts[0] == "user" and len(parts) > 1:
                return {"username": parts[1]}
            if parts[0] == "c" and len(parts) > 1:
                return {"query": parts[1]}
    return {"query": raw}


def playlist_id(raw: str) -> str:
    raw = raw.strip()
    if PLAYLIST_ID.match(raw):
        return raw
    try:
        qs = parse_qs(urlparse(raw).query)
        if "list" in qs:
            return qs["list"][0]
    except ValueError:
        pass
    return raw


def uploads_playlist(channel_id: str) -> str:
    """The uploads playlist of channel UCxxxx is UUxxxx."""
    return "UU" + channel_id[2:] if channel_id.startswith("UC") else channel_id


def watch_url(vid: str, t: int | None = None) -> str:
    return f"https://youtu.be/{vid}" + (f"?t={int(t)}" if t else "")


def channel_url(cid: str) -> str:
    return f"https://www.youtube.com/channel/{cid}"


def thumbnail_url(vid: str, size: str = "mqdefault") -> str:
    return f"https://i.ytimg.com/vi/{vid}/{size}.jpg"
