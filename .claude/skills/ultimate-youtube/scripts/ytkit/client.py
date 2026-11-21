"""Service builders and the single place every API request goes through.

``call(request, "videos.list")`` checks the local quota tracker, executes with
retries on transient errors, records quota use and turns Google's HttpError
into a short, actionable YtError.
"""

from __future__ import annotations

import json
import time

from . import auth, config, quota


class YtError(RuntimeError):
    def __init__(self, message: str, fix: str = "", reason: str = "", status: int | None = None):
        super().__init__(message)
        self.fix = fix
        self.reason = reason
        self.status = status


def _build(*args, **kwargs):
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover
        raise YtError(str(exc), auth.INSTALL_HINT) from exc
    return build(*args, cache_discovery=False, **kwargs)


def public(prefer_oauth: bool = False):
    """Data API client for public reads: API key first, read token as fallback."""
    key = config.api_key()
    if key and not prefer_oauth:
        return _build("youtube", "v3", developerKey=key)
    try:
        return _build("youtube", "v3", credentials=auth.load_credentials("read"))
    except auth.AuthError as exc:
        if key:
            return _build("youtube", "v3", developerKey=key)
        raise YtError(
            "No API key or read token available for public YouTube data.",
            "Set YOUTUBE_API_KEY (python scripts/yt_auth.py set-key YOUR_KEY) or run "
            "python scripts/yt_auth.py login. See workflows/setup.md",
        ) from exc


def owner(write: bool = False):
    """Data API client acting as the signed-in channel owner."""
    kind = "write" if write else "read"
    try:
        return _build("youtube", "v3", credentials=auth.load_credentials(kind))
    except auth.AuthError as exc:
        if not write:
            # A write token can also read; use it if that's all we have.
            try:
                return _build("youtube", "v3", credentials=auth.load_credentials("write"))
            except auth.AuthError:
                pass
        raise YtError(str(exc), exc.fix) from exc


def analytics(revenue: bool = False):
    scopes = auth.READ_SCOPES_REVENUE if revenue else auth.READ_SCOPES
    try:
        creds = auth.load_credentials("read", scopes)
    except auth.AuthError as exc:
        raise YtError(str(exc), exc.fix) from exc
    return _build("youtubeAnalytics", "v2", credentials=creds)


def reporting():
    try:
        creds = auth.load_credentials("read")
    except auth.AuthError as exc:
        raise YtError(str(exc), exc.fix) from exc
    return _build("youtubereporting", "v1", credentials=creds), creds


_RETRY_STATUS = {500, 502, 503, 504}
_FIXES = {
    "quotaExceeded": "Daily quota used up. It resets at midnight Pacific Time; request a "
    "quota increase in Google Cloud Console if this happens often.",
    "dailyLimitExceeded": "Daily quota used up. It resets at midnight Pacific Time.",
    "rateLimitExceeded": "Too many requests too quickly. Wait a minute and retry.",
    "keyInvalid": "The API key is invalid. Re-create it and run yt_auth.py set-key.",
    "accessNotConfigured": "Enable the API for your Cloud project (YouTube Data API v3, "
    "YouTube Analytics API, YouTube Reporting API) in Google Cloud Console.",
    "forbidden": "The signed-in account does not own or manage this resource.",
    "insufficientPermissions": "The token lacks the required scope. Re-run yt_auth.py login "
    "(add --write for changes, --revenue for money metrics).",
    "videoNotFound": "Video not found, private, or not owned by this channel.",
    "uploadLimitExceeded": "This channel hit YouTube's own daily upload limit. Try tomorrow.",
    "commentsDisabled": "Comments are disabled on this video.",
    "uploadRateLimitExceeded": "Too many uploads in a short time. Wait and retry.",
}


def _reason(exc) -> tuple[str, str]:
    try:
        body = json.loads(exc.content.decode("utf-8"))
        err = body.get("error", {})
        errors = err.get("errors") or [{}]
        return errors[0].get("reason", ""), err.get("message", "")
    except Exception:
        return "", str(exc)


def call(request, method: str | None = None, count: int = 1, retries: int = 4):
    """Execute a googleapiclient request with quota tracking and retries."""
    from googleapiclient.errors import HttpError

    if method:
        ok, why = quota.can_afford(method, count)
        if not ok:
            raise YtError(why, _FIXES["quotaExceeded"], "localQuota")
    delay = 2.0
    for attempt in range(retries + 1):
        try:
            result = request.execute()
            if method:
                quota.record(method, count)
            return result
        except HttpError as exc:
            status = getattr(exc.resp, "status", None)
            reason, message = _reason(exc)
            if method:
                quota.record(method, count)  # failed calls still cost quota
            transient = status in _RETRY_STATUS or reason in ("rateLimitExceeded", "backendError")
            if transient and attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise YtError(
                f"{method or 'API call'} failed ({status} {reason}): {message}",
                _FIXES.get(reason, ""),
                reason,
                status,
            ) from exc
        except (ConnectionError, TimeoutError, OSError) as exc:
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise YtError(f"Network error: {exc}", "Check your internet connection.") from exc
    raise YtError("unreachable")
