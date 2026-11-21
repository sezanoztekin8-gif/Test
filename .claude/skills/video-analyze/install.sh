#!/usr/bin/env bash
# Install the video-analyze skill into a Claude Code skills directory.
#
# Usage:
#   ./install.sh                 # install to ~/.claude/skills/video-analyze
#   ./install.sh --project       # install to ./.claude/skills/video-analyze
#   ./install.sh --link          # symlink instead of copy (for development)
#   ./install.sh --dir <path>    # install to a custom skills directory
#   ./install.sh --uninstall     # remove an existing install

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
MODE="copy"
UNINSTALL=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)   SKILLS_DIR="$PWD/.claude/skills"; shift;;
        --dir)       SKILLS_DIR="$2"; shift 2;;
        --link)      MODE="link"; shift;;
        --uninstall) UNINSTALL=1; shift;;
        -h|--help)
            sed -n '2,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0;;
        *) echo "Unknown flag: $1" >&2; exit 1;;
    esac
done

DEST="$SKILLS_DIR/video-analyze"

if [[ $UNINSTALL -eq 1 ]]; then
    if [[ -e "$DEST" || -L "$DEST" ]]; then
        rm -rf "$DEST"
        echo "Removed $DEST"
    else
        echo "Nothing installed at $DEST"
    fi
    exit 0
fi

mkdir -p "$SKILLS_DIR"

if [[ -e "$DEST" || -L "$DEST" ]]; then
    echo "Replacing existing install at $DEST" >&2
    rm -rf "$DEST"
fi

if [[ "$MODE" == "link" ]]; then
    ln -s "$SRC" "$DEST"
    echo "Linked $DEST -> $SRC"
else
    mkdir -p "$DEST/scripts"
    cp "$SRC/SKILL.md" "$DEST/SKILL.md"
    cp "$SRC"/scripts/*.sh "$SRC"/scripts/*.py "$DEST/scripts/"
    chmod +x "$DEST"/scripts/*.sh "$DEST"/scripts/*.py
    echo "Installed to $DEST"
fi

echo ""
echo "Checking dependencies..."
if ! bash "$SRC/scripts/setup.sh" check; then
    echo ""
    echo "Install the tools above, then re-run: $SRC/scripts/setup.sh check" >&2
    exit 1
fi

echo ""
echo "Done. Start a new Claude Code session and ask:"
echo "  \"analyze this video: <url>\""
