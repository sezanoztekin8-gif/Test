# Contributing

Thanks for taking a look. This is a small project — a handful of shell scripts, one Python file, and
a markdown instruction file that Claude reads.

## Getting set up

```bash
git clone https://github.com/mfrashad/video-analyze.git
cd video-analyze
./install.sh --link          # symlink, so your clone IS the installed skill
cp .env.example .env         # optional, for API keys
```

With `--link`, edits to your clone take effect in the next Claude Code session — no reinstall.

## Before you open a PR

```bash
./test.sh smoke
```

`smoke` generates a synthetic video with ffmpeg and runs the full pipeline offline. It must pass.
If your change touches downloading, also run the network tests that apply:

```bash
./test.sh youtube    # needs yt-dlp
./test.sh direct     # needs network
./test.sh tiktok     # needs APIFY_API_TOKEN
```

If you add a stage or a flag, add a test for it in `test.sh`.

## Conventions

- **Bash**: `set -euo pipefail` at the top of every script. Progress and errors to stderr; stdout is
  reserved for machine-readable output (`run.sh` prints only the manifest path).
- **Portability**: macOS and Linux both matter. Watch for `shasum` vs `sha256sum`, `stat -f%z` vs
  `stat -c%s`, and BSD vs GNU flag differences. Provide a fallback rather than assuming.
- **Never hard-fail on optional features.** Transcription missing, Pillow missing, no font found —
  degrade and continue. Frames are the product.
- **Secrets come from the environment**, never from a path on someone's machine. `.env` is
  git-ignored; document new keys in `.env.example`.
- **Python**: standard library only, plus Pillow (optional at runtime).

## Changing what Claude does

`SKILL.md` is the prompt Claude reads — its frontmatter `description` is what triggers the skill, and
its body is the instructions. Changes there alter behavior more than any code change will.

If you're modifying the design-reference block format, keep it directive and specific: the whole
value is that it forbids vague adjectives and demands hex values, tracking, and proportions.

## Reporting bugs

Include the URL if it's public, the exact command, the platform (macOS/Linux), and stderr output.
`scripts/setup.sh check` output helps too.

Download failures for a specific site are often upstream in yt-dlp — please try `yt-dlp <url>`
directly and `yt-dlp -U` before filing.

## License

Contributions are accepted under the MIT license, same as the project.
