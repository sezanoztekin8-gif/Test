"""Shared CLI plumbing: consistent errors and JSON output for every script."""

from __future__ import annotations

import argparse
import sys

from . import util
from .auth import AuthError
from .client import YtError


def parser(description: str) -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)


def run(main) -> None:
    """Call main(); turn known errors into a JSON error payload and exit code 1."""
    util.utf8_stdout()
    try:
        result = main()
    except (YtError, AuthError) as exc:
        util.fail(str(exc), getattr(exc, "fix", ""))
    except ValueError as exc:
        util.fail(str(exc))
    except KeyboardInterrupt:
        util.fail("Interrupted", code=130)
    if result is not None:
        util.emit(result)


def confirm_note(action: str) -> dict:
    return {
        "dry_run": True,
        "next_step": f"Show this preview to the user. Only after they approve, re-run the same command with --confirm to {action}.",
    }


def add_reports_dir(p: argparse.ArgumentParser) -> None:
    p.add_argument("--reports-dir", help="Where to save output files (default ./youtube-reports or $YT_REPORTS_DIR)")


def need(args, *names):
    missing = [n for n in names if getattr(args, n, None) in (None, "")]
    if missing:
        util.fail("Missing required option(s): " + ", ".join("--" + m.replace("_", "-") for m in missing))


def stdin_is_tty() -> bool:
    return sys.stdin.isatty()
