"""Quota-efficient data fetchers shared by every research script.

Rules baked in here:
* A channel's uploads come from its uploads playlist (1 unit / 50 videos),
  never from search.list.
* Video and channel details are always batched 50 IDs per call.
* @handles resolve with channels.list(forHandle=...) for 1 unit; only free
  text falls back to search.list.
"""

from __future__ import annotations

from . import ids, util
from .client import YtError, call

VIDEO_PARTS = "snippet,statistics,contentDetails,status,liveStreamingDetails,topicDetails"
CHANNEL_PARTS = "snippet,statistics,contentDetails,brandingSettings,topicDetails"


def resolve_channel(yt, raw: str) -> str:
    ref = ids.channel_ref(raw)
    if "id" in ref:
        return ref["id"]
    if "handle" in ref:
        res = call(yt.channels().list(part="id", forHandle=ref["handle"]), "channels.list")
    elif "username" in ref:
        res = call(yt.channels().list(part="id", forUsername=ref["username"]), "channels.list")
    else:
        res = call(
            yt.search().list(part="snippet", q=ref["query"], type="channel", maxResults=1),
            "search.list",
        )
        items = res.get("items", [])
        if items:
            return items[0]["snippet"]["channelId"]
        raise YtError(f"No channel found for {raw!r}", "Pass the @handle or channel URL instead.")
    items = res.get("items", [])
    if not items:
        # forHandle sometimes misses handles typed without @, try once more with search
        if "handle" in ref:
            return resolve_channel(yt, ref["handle"].lstrip("@") + " ")
        raise YtError(f"No channel found for {raw!r}")
    return items[0]["id"]


def channels(yt, channel_ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for batch in util.chunks(list(dict.fromkeys(channel_ids)), 50):
        res = call(yt.channels().list(part=CHANNEL_PARTS, id=",".join(batch), maxResults=50), "channels.list")
        for item in res.get("items", []):
            out[item["id"]] = normalize_channel(item)
    return out


def normalize_channel(item: dict) -> dict:
    sn = item.get("snippet", {})
    st = item.get("statistics", {})
    branding = item.get("brandingSettings", {}).get("channel", {})
    return {
        "channel_id": item["id"],
        "title": sn.get("title"),
        "handle": sn.get("customUrl"),
        "url": ids.channel_url(item["id"]),
        "description": sn.get("description", ""),
        "country": sn.get("country"),
        "default_language": sn.get("defaultLanguage") or branding.get("defaultLanguage"),
        "created_at": sn.get("publishedAt"),
        "subscribers": util.to_int(st.get("subscriberCount")),
        "subscribers_hidden": st.get("hiddenSubscriberCount", False),
        "total_views": util.to_int(st.get("viewCount")),
        "video_count": util.to_int(st.get("videoCount")),
        "keywords": branding.get("keywords", ""),
        "topics": [t.rsplit("/", 1)[-1] for t in item.get("topicDetails", {}).get("topicCategories", [])],
        "uploads_playlist": item.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
        or ids.uploads_playlist(item["id"]),
        "thumbnail": (sn.get("thumbnails", {}).get("high") or {}).get("url"),
    }


def playlist_video_ids(yt, playlist_id: str, limit: int = 50) -> list[str]:
    vids: list[str] = []
    token = None
    while len(vids) < limit:
        res = call(
            yt.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=min(50, limit - len(vids)),
                pageToken=token,
            ),
            "playlistItems.list",
        )
        vids += [i["contentDetails"]["videoId"] for i in res.get("items", [])]
        token = res.get("nextPageToken")
        if not token:
            break
    return vids


def videos(yt, video_ids: list[str], parts: str = VIDEO_PARTS) -> list[dict]:
    """Full details, order preserved. Missing/private videos are skipped."""
    found: dict[str, dict] = {}
    for batch in util.chunks(list(dict.fromkeys(video_ids)), 50):
        res = call(yt.videos().list(part=parts, id=",".join(batch), maxResults=50), "videos.list")
        for item in res.get("items", []):
            found[item["id"]] = normalize_video(item)
    return [found[v] for v in video_ids if v in found]


def normalize_video(item: dict) -> dict:
    sn = item.get("snippet", {})
    st = item.get("statistics", {})
    cd = item.get("contentDetails", {})
    status = item.get("status", {})
    live = item.get("liveStreamingDetails")
    thumbs = sn.get("thumbnails", {})
    best_thumb = next(
        (thumbs[k]["url"] for k in ("maxres", "standard", "high", "medium", "default") if k in thumbs), None
    )
    duration = util.iso_duration_seconds(cd.get("duration"))
    return {
        "video_id": item["id"],
        "url": ids.watch_url(item["id"]),
        "title": sn.get("title", ""),
        "description": sn.get("description", ""),
        "tags": sn.get("tags", []),
        "category_id": sn.get("categoryId"),
        "channel_id": sn.get("channelId"),
        "channel_title": sn.get("channelTitle"),
        "published_at": sn.get("publishedAt"),
        "default_language": sn.get("defaultLanguage"),
        "default_audio_language": sn.get("defaultAudioLanguage"),
        "duration_s": duration,
        "duration": util.hms(duration),
        "definition": cd.get("definition"),
        "has_captions": cd.get("caption") == "true",
        "licensed_content": cd.get("licensedContent"),
        "views": util.to_int(st.get("viewCount")),
        "likes": util.to_int(st.get("likeCount")),
        "comments": util.to_int(st.get("commentCount")),
        "privacy": status.get("privacyStatus"),
        "made_for_kids": status.get("madeForKids"),
        "publish_at": status.get("publishAt"),
        "was_live": bool(live),
        "live_scheduled": (live or {}).get("scheduledStartTime"),
        "topics": [t.rsplit("/", 1)[-1] for t in item.get("topicDetails", {}).get("topicCategories", [])],
        "thumbnail": best_thumb,
    }


def channel_videos(yt, channel_id: str, limit: int = 50, uploads: str | None = None) -> list[dict]:
    vids = playlist_video_ids(yt, uploads or ids.uploads_playlist(channel_id), limit)
    return videos(yt, vids)


def comments(yt, video_id: str, limit: int = 100, order: str = "relevance", replies: bool = False) -> list[dict]:
    """Top-level comments (+ first replies if asked). 1 unit per 100 comments."""
    out: list[dict] = []
    token = None
    while len(out) < limit:
        try:
            res = call(
                yt.commentThreads().list(
                    part="snippet,replies" if replies else "snippet",
                    videoId=video_id,
                    maxResults=min(100, limit - len(out)),
                    order=order,
                    textFormat="plainText",
                    pageToken=token,
                ),
                "commentThreads.list",
            )
        except YtError as exc:
            if exc.reason in ("commentsDisabled", "forbidden"):
                return out
            raise
        for item in res.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            row = {
                "text": top.get("textDisplay", ""),
                "likes": top.get("likeCount", 0),
                "replies": item["snippet"].get("totalReplyCount", 0),
                "published_at": top.get("publishedAt"),
            }
            if replies and item.get("replies"):
                row["reply_texts"] = [r["snippet"].get("textDisplay", "") for r in item["replies"]["comments"][:5]]
            out.append(row)
        token = res.get("nextPageToken")
        if not token:
            break
    return out


def my_channel(yt) -> dict:
    res = call(yt.channels().list(part=CHANNEL_PARTS, mine=True), "channels.list")
    items = res.get("items", [])
    if not items:
        raise YtError(
            "The signed-in Google account has no YouTube channel.",
            "Sign in with the account (or Brand Account) that owns the channel: "
            "re-run python scripts/yt_auth.py login",
        )
    return normalize_channel(items[0])


def is_short_url_check(video_id: str, timeout: float = 8.0) -> bool | None:
    """Unofficial but reliable: /shorts/<id> answers 200 for Shorts and redirects otherwise.

    Returns None when the check could not be made (network, consent wall).
    """
    import urllib.error
    import urllib.request

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(
        f"https://www.youtube.com/shorts/{video_id}",
        method="HEAD",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    try:
        resp = opener.open(req, timeout=timeout)
        return resp.status == 200
    except urllib.error.HTTPError as exc:
        if exc.code in (301, 302, 303, 307, 308):
            return False
        return None
    except Exception:
        return None
