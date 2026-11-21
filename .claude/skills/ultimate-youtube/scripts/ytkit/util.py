"""Small shared helpers: parsing, formatting, dates and JSON output."""

from __future__ import annotations

import json
import re
import statistics
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import config

_DUR = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?")


def iso_duration_seconds(value: str | None) -> int:
    if not value:
        return 0
    m = _DUR.fullmatch(value)
    if not m:
        return 0
    d, h, mi, s = m.groups()
    return int(d or 0) * 86400 + int(h or 0) * 3600 + int(mi or 0) * 60 + int(float(s or 0))


def hms(seconds: float | int | None) -> str:
    if seconds is None:
        return ""
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def age_days(published: str | None, now: datetime | None = None) -> float:
    dt = parse_time(published)
    if not dt:
        return 0.0
    return max(((now or now_utc()) - dt).total_seconds() / 86400, 0.0)


def date_window(days: int, end_offset: int = 1) -> tuple[str, str]:
    """Analytics data lags ~1-2 days, so the default window ends yesterday."""
    end = date.today() - timedelta(days=end_offset)
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def to_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def human(n: float | int | None) -> str:
    if n is None:
        return "-"
    n = float(n)
    for unit, div in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= div:
            return f"{n / div:.1f}{unit}"
    return f"{n:.0f}" if n == int(n) else f"{n:.1f}"


def median(values) -> float:
    vals = [v for v in values if v is not None]
    return float(statistics.median(vals)) if vals else 0.0


def chunks(seq, size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def slug(text: str, max_len: int = 50) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "-", text)[:max_len].strip("-") or "item"


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def eprint(*args) -> None:
    print(*args, file=sys.stderr)


def _default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, set):
        return sorted(obj)
    raise TypeError(f"Not JSON serializable: {type(obj)}")


def dumps(payload) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, default=_default)


def save_json(payload, name: str, reports_dir: str | None = None, subdir: str = "data") -> Path:
    folder = config.reports_dir(reports_dir) / subdir
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(dumps(payload), encoding="utf-8")
    return path


def emit(payload) -> None:
    """Print JSON for the agent. UTF-8 safe on Windows consoles."""
    text = dumps(payload)
    try:
        sys.stdout.write(text + "\n")
    except UnicodeEncodeError:
        sys.stdout.buffer.write((text + "\n").encode("utf-8"))


def fail(message: str, fix: str = "", code: int = 1, **extra) -> None:
    payload = {"error": message}
    if fix:
        payload["fix"] = fix
    payload.update(extra)
    emit(payload)
    sys.exit(code)


def read_text_arg(value: str | None) -> str | None:
    """Arguments may be literal text or @path/to/file.txt."""
    if value and value.startswith("@"):
        return Path(value[1:]).expanduser().read_text(encoding="utf-8")
    return value


def utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
