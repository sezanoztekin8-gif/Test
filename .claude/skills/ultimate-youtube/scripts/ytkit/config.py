"""Paths and settings.

All user state lives OUTSIDE the skill folder so the skill can be shared,
updated or re-installed without touching anyone's credentials or data.

    YT_SKILL_HOME   (default ~/.ultimate-youtube)
        client_secret.json   OAuth client downloaded from Google Cloud Console
        config.json          optional: {"api_key": "...", "daily_quota": 10000}
        token_read.json      read-only token (analytics + channel reads)
        token_write.json     write token (upload / edit / delete) - separate on purpose
        quota/               one JSON file per Pacific-time day
        cache/transcripts/   transcript library (searchable)
        backups/             metadata snapshots taken before every write
        watchlist.json       competitor watchlist + snapshots

    YT_REPORTS_DIR  (default ./youtube-reports in the current working directory)
        Every data file and report the scripts generate.

    YOUTUBE_API_KEY  API key for public Data API reads (optional if OAuth is set up)
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def home() -> Path:
    override = os.environ.get("YT_SKILL_HOME")
    path = Path(override).expanduser() if override else Path.home() / ".ultimate-youtube"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sub(*parts: str) -> Path:
    path = home().joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def reports_dir(override: str | None = None) -> Path:
    raw = override or os.environ.get("YT_REPORTS_DIR") or "youtube-reports"
    path = Path(raw).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def client_secret_path() -> Path:
    return home() / "client_secret.json"


def token_path(kind: str) -> Path:
    if kind not in ("read", "write"):
        raise ValueError("token kind must be 'read' or 'write'")
    return home() / f"token_{kind}.json"


def load_config() -> dict:
    path = home() / "config.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def save_config(data: dict) -> Path:
    path = home() / "config.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    _restrict(path)
    return path


def api_key() -> str | None:
    return os.environ.get("YOUTUBE_API_KEY") or load_config().get("api_key")


def _restrict(path: Path) -> None:
    """Best-effort chmod 600 for files holding secrets (no-op on Windows)."""
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


restrict = _restrict
