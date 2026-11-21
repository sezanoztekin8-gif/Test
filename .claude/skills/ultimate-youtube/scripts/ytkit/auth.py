"""Authentication: one API key plus two deliberately separate OAuth tokens.

    API key        public Data API reads (any channel, video, comment, search)
    read token     youtube.readonly + yt-analytics.readonly (+ monetary, opt-in)
                   -> your private analytics, Reporting API, your own uploads
    write token    youtube.force-ssl ONLY
                   -> upload, update, delete, thumbnails, playlists, captions

Keeping the write token in its own file means analytics and research can
never accidentally modify a channel, and deleting token_write.json removes
all write capability without touching anything else.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from . import config

SCOPE_YT_READ = "https://www.googleapis.com/auth/youtube.readonly"
SCOPE_ANALYTICS = "https://www.googleapis.com/auth/yt-analytics.readonly"
SCOPE_MONETARY = "https://www.googleapis.com/auth/yt-analytics-monetary.readonly"
SCOPE_WRITE = "https://www.googleapis.com/auth/youtube.force-ssl"

READ_SCOPES = [SCOPE_YT_READ, SCOPE_ANALYTICS]
READ_SCOPES_REVENUE = READ_SCOPES + [SCOPE_MONETARY]
WRITE_SCOPES = [SCOPE_WRITE]

WRITE_LIKE = {
    SCOPE_WRITE,
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtubepartner",
}

INSTALL_HINT = (
    "Google client libraries are missing. Install them with:\n"
    "  pip install -r requirements.txt\n"
    "or run scripts through uv (dependencies are declared inline):\n"
    "  uv run scripts/<script>.py ..."
)


class AuthError(RuntimeError):
    def __init__(self, message: str, fix: str = ""):
        super().__init__(message)
        self.fix = fix


def _libs():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:  # pragma: no cover - environment specific
        raise AuthError(str(exc), INSTALL_HINT) from exc
    return Request, Credentials, InstalledAppFlow


def _setup_fix(kind: str) -> str:
    flag = "--write" if kind == "write" else ""
    return (
        f"Run: python scripts/yt_auth.py login {flag}".rstrip()
        + f"\n(needs {config.client_secret_path()} - see workflows/setup.md)"
    )


def load_credentials(kind: str, required_scopes: list[str] | None = None):
    """Load + refresh a stored token. Raises AuthError with a fix if unusable."""
    Request, Credentials, _ = _libs()
    path = config.token_path(kind)
    if not path.exists():
        raise AuthError(f"No {kind} token found at {path}", _setup_fix(kind))

    data = json.loads(path.read_text(encoding="utf-8"))
    granted = set(data.get("scopes") or [])

    if kind == "read" and granted & WRITE_LIKE:
        raise AuthError(
            "The read token carries write scopes; refusing to use it.",
            f"Delete {path} and run: python scripts/yt_auth.py login",
        )
    if kind == "write" and granted - set(WRITE_SCOPES):
        raise AuthError(
            "The write token carries unexpected extra scopes; refusing to use it.",
            f"Delete {path} and run: python scripts/yt_auth.py login --write",
        )
    missing = set(required_scopes or []) - granted
    if missing:
        raise AuthError(
            f"The {kind} token is missing scopes: {sorted(missing)}",
            "Re-run login with the needed option, e.g. "
            "python scripts/yt_auth.py login --revenue",
        )

    creds = Credentials.from_authorized_user_info(data, sorted(granted) or None)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as exc:
                raise AuthError(
                    f"Could not refresh the {kind} token: {exc}",
                    "Tokens of apps in 'Testing' mode expire after 7 days. "
                    + _setup_fix(kind),
                ) from exc
            _save(kind, creds)
        else:
            raise AuthError(f"The {kind} token is invalid.", _setup_fix(kind))
    return creds


def _save(kind: str, creds) -> Path:
    path = config.token_path(kind)
    path.write_text(creds.to_json(), encoding="utf-8")
    config.restrict(path)
    return path


def login(kind: str, revenue: bool = False, manual: bool = False, port: int = 0):
    """Run the browser consent flow and store the token."""
    _, _, InstalledAppFlow = _libs()
    secret = config.client_secret_path()
    if not secret.exists():
        raise AuthError(
            f"OAuth client file not found at {secret}",
            "Create a 'Desktop app' OAuth client in Google Cloud Console, download "
            f"the JSON and save it as {secret}. Step-by-step: workflows/setup.md",
        )
    scopes = WRITE_SCOPES if kind == "write" else (READ_SCOPES_REVENUE if revenue else READ_SCOPES)
    flow = InstalledAppFlow.from_client_secrets_file(str(secret), scopes)

    if manual:
        # Headless machines: user opens the URL anywhere, pastes the redirect URL back.
        os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
        flow.redirect_uri = "http://localhost:1"
        url, _ = flow.authorization_url(access_type="offline", prompt="consent")
        print("Open this URL in any browser and approve access:\n\n" + url + "\n")
        print("The browser will then fail to load a localhost page - that is expected.")
        reply = input("Paste the full URL from the address bar here: ").strip()
        flow.fetch_token(authorization_response=reply)
        creds = flow.credentials
    else:
        creds = flow.run_local_server(
            port=port,
            access_type="offline",
            prompt="consent",
            authorization_prompt_message="Opening browser for Google sign-in...\n{url}",
            success_message="Authorized. You can close this tab and return to the terminal.",
        )
    return _save(kind, creds), creds


def token_status(kind: str) -> dict:
    path = config.token_path(kind)
    if not path.exists():
        return {"kind": kind, "status": "missing", "fix": _setup_fix(kind)}
    try:
        creds = load_credentials(kind)
    except AuthError as exc:
        return {"kind": kind, "status": "error", "error": str(exc), "fix": exc.fix}
    return {"kind": kind, "status": "ok", "path": str(path), "scopes": sorted(creds.scopes or [])}


def revoke(kind: str) -> dict:
    path = config.token_path(kind)
    if not path.exists():
        return {"kind": kind, "status": "nothing to revoke"}
    revoked_remote = False
    try:
        import urllib.parse
        import urllib.request

        token = json.loads(path.read_text(encoding="utf-8")).get("refresh_token") or ""
        if token:
            body = urllib.parse.urlencode({"token": token}).encode()
            req = urllib.request.Request("https://oauth2.googleapis.com/revoke", data=body)
            urllib.request.urlopen(req, timeout=15)
            revoked_remote = True
    except Exception:
        pass
    path.unlink(missing_ok=True)
    return {"kind": kind, "status": "deleted", "revoked_at_google": revoked_remote}
