"""Transcript fetching with fallbacks, plus a local searchable library.

Order of attempts (no Data API quota is spent unless you ask for it):
  1. youtube-transcript-api  - any public video, manual or auto captions
  2. yt-dlp                  - subtitle download, if yt-dlp is installed
  3. captions.download       - Data API, ONLY for videos you own (200 units),
                               used when --own is passed

Every transcript is cached in ~/.ultimate-youtube/cache/transcripts/ so it is
fetched once and can then be searched across channels with `yt_transcripts.py search`.

Note: YouTube blocks many cloud/VPS IP ranges for caption requests. If you see
"blocked" or "RequestBlocked" errors, run from a home connection or configure a
proxy (see references/transcripts.md).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import config, util


def library_dir() -> Path:
    return config.sub("cache", "transcripts")


def _cache_path(video_id: str) -> Path:
    return library_dir() / f"{video_id}.json"


def load_cached(video_id: str) -> dict | None:
    path = _cache_path(video_id)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
    return None


def save(record: dict) -> Path:
    path = _cache_path(record["video_id"])
    path.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


# ------------------------------------------------------------------ method 1

def via_transcript_api(video_id: str, langs: list[str], translate_to: str | None = None) -> dict:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as exc:
        raise RuntimeError("youtube-transcript-api not installed (pip install youtube-transcript-api)") from exc

    api = YouTubeTranscriptApi()
    listing = api.list(video_id)
    available = [
        {"language": t.language, "code": t.language_code, "generated": t.is_generated}
        for t in listing
    ]
    chosen = None
    try:
        chosen = listing.find_manually_created_transcript(langs)
    except Exception:
        try:
            chosen = listing.find_transcript(langs)
        except Exception:
            chosen = next(iter(listing), None)
    if chosen is None:
        raise RuntimeError("No transcripts available")
    if translate_to and chosen.language_code != translate_to and chosen.is_translatable:
        chosen = chosen.translate(translate_to)
    fetched = chosen.fetch()
    snippets = getattr(fetched, "snippets", fetched)
    segments = []
    for s in snippets:
        text = getattr(s, "text", None) if not isinstance(s, dict) else s.get("text")
        start = getattr(s, "start", None) if not isinstance(s, dict) else s.get("start")
        dur = getattr(s, "duration", None) if not isinstance(s, dict) else s.get("duration")
        text = (text or "").replace("\n", " ").strip()
        if text:
            segments.append({"start": round(float(start or 0), 2), "dur": round(float(dur or 0), 2), "text": text})
    return {
        "language": chosen.language_code,
        "is_generated": chosen.is_generated,
        "available": available,
        "segments": segments,
    }


# ------------------------------------------------------------------ method 2

_VTT_TIME = re.compile(r"(?:(\d+):)?(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(?:(\d+):)?(\d{2}):(\d{2})[.,](\d{3})")


def _secs(h, m, s, ms) -> float:
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_vtt(content: str) -> list[dict]:
    """Parse WebVTT/SRT, stripping tags and the rolling duplicates of auto-captions."""
    segments: list[dict] = []
    start = end = None
    buf: list[str] = []

    def flush():
        if start is None or not buf:
            return
        text = re.sub(r"<[^>]+>", "", " ".join(buf))
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            segments.append({"start": round(start, 2), "dur": round(max((end or start) - start, 0), 2), "text": text})

    for line in content.splitlines():
        line = line.strip()
        m = _VTT_TIME.search(line)
        if m:
            flush()
            g = m.groups()
            start, end = _secs(*g[:4]), _secs(*g[4:])
            buf = []
        elif not line or line.isdigit() or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE", "STYLE")):
            continue
        else:
            buf.append(line)
    flush()

    # Auto-captions repeat the previous line inside the next cue. Keep only new words.
    cleaned: list[dict] = []
    for seg in segments:
        if cleaned:
            prev = cleaned[-1]["text"]
            if seg["text"] == prev:
                continue
            if seg["text"].startswith(prev):
                seg = dict(seg, text=seg["text"][len(prev):].strip())
                if not seg["text"]:
                    continue
        cleaned.append(seg)
    return cleaned


def via_ytdlp(video_id: str, langs: list[str]) -> dict:
    exe = shutil.which("yt-dlp")
    cmd = [exe] if exe else [sys.executable, "-m", "yt_dlp"]
    with tempfile.TemporaryDirectory() as tmp:
        args = cmd + [
            "--skip-download", "--write-subs", "--write-auto-subs",
            "--sub-langs", ",".join(langs + [f"{l}.*" for l in langs]),
            "--sub-format", "vtt/srt/best", "--no-warnings", "--quiet",
            "-o", str(Path(tmp) / "%(id)s.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}",
        ]
        try:
            proc = subprocess.run(args, capture_output=True, text=True, timeout=90)
        except FileNotFoundError as exc:
            raise RuntimeError("yt-dlp not installed (pip install yt-dlp)") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("yt-dlp timed out") from exc
        files = sorted(Path(tmp).glob("*.vtt")) + sorted(Path(tmp).glob("*.srt"))
        if not files:
            raise RuntimeError("yt-dlp found no subtitles. " + (proc.stderr or "").strip()[:300])

        def rank(p: Path):
            code = p.suffixes[-2].lstrip(".") if len(p.suffixes) >= 2 else ""
            base = code.split("-")[0]
            return langs.index(base) if base in langs else len(langs)

        best = sorted(files, key=rank)[0]
        code = best.suffixes[-2].lstrip(".") if len(best.suffixes) >= 2 else "unknown"
        return {
            "language": code,
            "is_generated": None,
            "available": [{"code": f.suffixes[-2].lstrip(".") if len(f.suffixes) >= 2 else "?"} for f in files],
            "segments": parse_vtt(best.read_text(encoding="utf-8", errors="replace")),
        }


# ------------------------------------------------------------------ method 3

def via_captions_api(video_id: str, langs: list[str]) -> dict:
    from . import client

    yt = client.owner(write=False)
    tracks = client.call(yt.captions().list(part="snippet", videoId=video_id), "captions.list").get("items", [])
    if not tracks:
        raise RuntimeError("No caption tracks on this video")
    tracks.sort(key=lambda t: (t["snippet"]["language"].split("-")[0] not in langs, t["snippet"].get("trackKind") == "asr"))
    track = tracks[0]
    raw = client.call(yt.captions().download(id=track["id"], tfmt="vtt"), "captions.download")
    text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
    return {
        "language": track["snippet"]["language"],
        "is_generated": track["snippet"].get("trackKind") == "asr",
        "available": [t["snippet"]["language"] for t in tracks],
        "segments": parse_vtt(text),
    }


# ------------------------------------------------------------------ public API

def get(
    video_id: str,
    langs: list[str] | None = None,
    own: bool = False,
    refresh: bool = False,
    translate_to: str | None = None,
    meta: dict | None = None,
) -> dict:
    langs = langs or ["en"]
    if not refresh and not translate_to:
        cached = load_cached(video_id)
        if cached:
            have = cached.get("language", "").split("-")[0]
            offered = {str(a.get("code", a) if isinstance(a, dict) else a).split("-")[0] for a in cached.get("available", [])}
            # Reuse the cache if it is in a wanted language, or no wanted language exists anyway.
            if have in langs or not (offered & set(langs)):
                cached["cached"] = True
                return cached

    attempts = []
    methods = [("youtube-transcript-api", lambda: via_transcript_api(video_id, langs, translate_to)),
               ("yt-dlp", lambda: via_ytdlp(video_id, langs))]
    if own:
        methods.append(("captions.download", lambda: via_captions_api(video_id, langs)))

    for name, fn in methods:
        try:
            result = fn()
            if not result["segments"]:
                raise RuntimeError("empty transcript")
        except Exception as exc:  # each method fails in its own way; record and move on
            attempts.append({"method": name, "error": f"{type(exc).__name__}: {exc}"[:300]})
            continue
        record = {
            "video_id": video_id,
            "method": name,
            **result,
            "word_count": sum(len(s["text"].split()) for s in result["segments"]),
            "duration_s": int(result["segments"][-1]["start"] + result["segments"][-1]["dur"]),
            "fetched_at": util.now_utc().isoformat(),
        }
        if meta:
            record["meta"] = {k: meta.get(k) for k in ("title", "channel_title", "channel_id", "published_at", "views")}
        if not translate_to:
            save(record)
        return record

    raise RuntimeError(json.dumps({"video_id": video_id, "attempts": attempts}))


def plain_text(segments: list[dict]) -> str:
    return " ".join(s["text"] for s in segments)


def timed_text(segments: list[dict]) -> str:
    return "\n".join(f"[{util.hms(s['start'])}] {s['text']}" for s in segments)


def window(segments: list[dict], start: float = 0, end: float | None = None) -> list[dict]:
    return [s for s in segments if s["start"] >= start and (end is None or s["start"] < end)]


def search_library(query: str, max_hits: int = 30, context: int = 1, channel: str | None = None) -> list[dict]:
    terms = [t for t in query.lower().split() if t]
    hits = []
    for path in sorted(library_dir().glob("*.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        meta = rec.get("meta") or {}
        if channel and channel not in (meta.get("channel_id"), meta.get("channel_title")):
            continue
        segs = rec.get("segments", [])
        for i, seg in enumerate(segs):
            lo, hi = max(0, i - context), min(len(segs), i + context + 1)
            text = " ".join(s["text"] for s in segs[lo:hi])
            if all(t in text.lower() for t in terms) and query.lower().split()[0] in seg["text"].lower():
                hits.append({
                    "video_id": rec["video_id"],
                    "title": meta.get("title"),
                    "channel": meta.get("channel_title"),
                    "at": util.hms(seg["start"]),
                    "link": f"https://youtu.be/{rec['video_id']}?t={int(seg['start'])}",
                    "context": text,
                })
                if len(hits) >= max_hits:
                    return hits
    return hits
