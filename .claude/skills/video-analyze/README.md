# video-analyze

**A Claude Code skill that lets Claude actually watch a video.**

Give Claude a link — Instagram reel, TikTok, YouTube, X post, or a raw `.mp4` — and it downloads the
video, samples frames on a smart interval, transcribes the audio, aligns every frame to what's being
said at that moment, and reads the whole thing back as images it can see.

Out of the box it does one thing most video tools don't: **when a frame contains a UI, layout, or
style worth stealing, Claude writes a replication prompt for it.** Paste that into an image model or
hand it to Claude to build — you've turned a 12-second reel into a spec.

```
you  ▸ analyze this reel and rebuild the landing page: instagram.com/reel/ABC/
     ▸ [downloads, extracts 15 frames, transcribes]
     ▸ [reads each frame]

     [DESIGN REFERENCE — t=6s]
     Replication prompt:
     "Full-bleed hero, off-white #FAF9F6 ground. Display serif headline at ~11vw,
      tight -0.03em tracking, sentence case, near-black #111. Single product shot
      offset 60% right, no drop shadow, hard-edged. Nav is 11px mono ALL CAPS,
      letter-spaced 0.18em, pinned top-left with 48px margins. Editorial, high
      contrast, generous negative space..."
     image_path: /tmp/video-analyze/a3f1-.../frames/0004.jpg
```

---

## Why this exists

Claude can see images but can't open a video. The usual workaround — screenshotting by hand, or
pasting a transcript with no visuals — loses either the pictures or the words.

This skill closes that gap with a four-stage pipeline that hands Claude a *multimodal package*:
frames it can look at, with the narration for each frame attached.

| Without | With |
|---|---|
| "I can't watch videos." | 15 frames + aligned transcript in context |
| A wall of transcript text | "At 0:06 the headline animates in as the nav fades" |
| "It looks minimal and clean" | A 120-word replication prompt with hex values and tracking |

---

## Install

**Requirements:** `ffmpeg`, `yt-dlp`, `curl`, and Python 3 with Pillow.

```bash
# macOS
brew install ffmpeg yt-dlp && python3 -m pip install --user pillow

# Debian / Ubuntu
sudo apt install ffmpeg python3-pil && python3 -m pip install --user yt-dlp
```

Then:

```bash
git clone https://github.com/mfrashad/video-analyze.git
cd video-analyze
./install.sh
```

That copies the skill to `~/.claude/skills/video-analyze/` and verifies your dependencies.

<details>
<summary>Other install modes</summary>

```bash
./install.sh --project     # install into ./.claude/skills (per-project, committable)
./install.sh --link        # symlink instead of copy, for hacking on the skill
./install.sh --dir <path>  # custom skills directory
./install.sh --uninstall   # remove it
```
</details>

**Optional keys.** Copy `.env.example` to `.env`, or just export them in your shell:

```bash
export OPENAI_API_KEY=sk-...      # enables transcription (frames work fine without it)
export APIFY_API_TOKEN=apify_...  # fallback downloader for Instagram / TikTok
```

---

## Use it

Start a new Claude Code session and talk normally:

> "analyze this video: https://youtu.be/dQw4w9WgXcQ"

> "break down this TikTok — I want to copy the transitions"

> "watch this reel and tell me what the UI does when you tap the card"

Claude invokes the skill, runs the pipeline, and reads the frames back to you. That's it.

**You can also run it directly**, without Claude, and get JSON:

```bash
~/.claude/skills/video-analyze/scripts/run.sh <url> [flags]
# prints the path to manifest.json on stdout
```

### Flags

| Flag | Default | What it does |
|---|---|---|
| `--interval <sec>` | auto | Force N seconds between frames |
| `--max-frames <n>` | 20 | Hard cap on frames extracted |
| `--fidelity high\|low` | `high` | `low` tiles frames into compressed grids to save context |
| `--grid-size 2\|3\|4` | 4 | Frames per grid tile (low fidelity only) |
| `--skip-transcript` | off | Skip Whisper entirely |
| `--out-dir <path>` | `/tmp/video-analyze/<hash>-<ts>/` | Where output lands |
| `--ig-tt-auth auto\|cookies\|apify` | `auto` | Auth strategy for Instagram / TikTok |

### Frame sampling

The interval adapts to length, so you get roughly 12–15 frames regardless of duration:

| Duration | Interval | ~Frames |
|---|---|---|
| < 30s | every 2s | ~15 |
| 30–60s | every 5s | ~12 |
| > 60s | `ceil(duration / 15)` | ~15 |

If that would exceed `--max-frames`, the interval widens until it fits.

---

## Platform support

| Platform | How | Notes |
|---|---|---|
| **YouTube** | yt-dlp | Works out of the box |
| **Instagram** | yt-dlp + browser cookies → Apify fallback | Needs you logged in, or `APIFY_API_TOKEN` |
| **TikTok** | yt-dlp + browser cookies → Apify fallback | Same |
| **X / Twitter** | yt-dlp | Public posts; no special-casing |
| **Direct `.mp4`** | yt-dlp → curl | Referer headers set automatically for CDN links |

Instagram and TikTok gate downloads behind auth. The skill reads cookies from your logged-in browser
via `yt-dlp --cookies-from-browser`. If you don't use Chrome:

```bash
export VIDEO_ANALYZE_BROWSER=firefox   # or safari, edge, brave, chromium
```

If cookies fail and `APIFY_API_TOKEN` is set, it falls back to the Apify scrapers automatically.

---

## Output

The pipeline writes a directory and prints the manifest path:

```
/tmp/video-analyze/a3f1b2c4-1754650000/
├── video.mp4
├── audio.mp3
├── duration.txt
├── frames/0001.jpg ... 0015.jpg
├── grids/grid_0001.jpg          # low fidelity only
├── transcript.json
└── manifest.json                # ← the thing Claude reads
```

`manifest.json` is the contract — stable, and easy to consume from your own scripts:

```json
{
  "source":     { "url": "...", "platform": "tiktok", "duration_sec": 42.5,
                  "downloaded_via": "yt-dlp+cookies" },
  "extraction": { "interval_sec": 3, "frame_count": 15, "fidelity": "high",
                  "grid_size": null },
  "frames": [
    { "index": 1, "t_sec": 0.0,
      "image": "frames/0001.jpg",
      "image_path": "/tmp/video-analyze/.../frames/0001.jpg",
      "transcript": "ok so today we are going to",
      "transcript_t": [0.0, 3.2] }
  ],
  "grids": [],
  "transcript": { "language": "en", "text": "...", "segments": [...] }
}
```

`transcript` is `null` when transcription was skipped or failed — the frames are still there.
Nothing in the pipeline hard-fails because audio didn't work.

---

## High vs low fidelity

**`--fidelity high` (default)** — one image per frame. Use it for anything with fine detail: UI
screenshots, small type, subtle motion. This is the right mode for design replication.

**`--fidelity low`** — tiles 2–4 frames into a single compressed grid with burned-in timestamps.
Roughly 4× less context for the same coverage. Use it for long videos, bold visuals, talking heads,
or when you just want the gist.

Don't use low fidelity to study an interface. Downscaling to 512px cells destroys exactly the small
text and edge detail you're trying to read.

---

## Configuration

Every one of these is optional.

| Variable | Default | Effect |
|---|---|---|
| `OPENAI_API_KEY` | — | Enables Whisper transcription |
| `APIFY_API_TOKEN` | — | Enables the Apify fallback for IG / TikTok |
| `VIDEO_ANALYZE_BROWSER` | `chrome` | Which browser yt-dlp reads cookies from |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Point at any OpenAI-compatible endpoint |
| `WHISPER_MODEL` | `whisper-1` | Transcription model |
| `VIDEO_ANALYZE_TMPDIR` | `/tmp/video-analyze` | Base output directory |

Running transcription locally instead of paying OpenAI:

```bash
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=whatever-your-server-wants
```

---

## Testing

```bash
./test.sh smoke     # local ffmpeg pipeline, no network — should always pass
./test.sh youtube   # real download + transcription
./test.sh direct    # public .mp4 via curl
./test.sh tiktok    # Apify path (needs APIFY_API_TOKEN)
./test.sh           # everything
```

`smoke` builds a synthetic 25-second video with ffmpeg and runs the whole pipeline on it, so it
works offline and in CI.

---

## How it works

```
url ──▶ download.sh ──▶ extract.sh ──▶ transcribe.sh ──▶ assemble.py ──▶ manifest.json
        yt-dlp/cookies   ffmpeg         Whisper API       align + grid       │
        Apify/curl       frames+audio   (optional)        Pillow             ▼
                                                                        Claude reads
                                                                        the frames
```

Each stage is a standalone script under `scripts/` that reads and writes a shared output directory.
You can run any of them by hand, swap one out, or call `run.sh` from something other than Claude.
`SKILL.md` is the instruction file Claude itself reads — including the rules for emitting design
reference blocks.

See **[GUIDE.md](GUIDE.md)** for the full walkthrough: design replication workflow, per-stage
internals, extending the pipeline, and troubleshooting.

---

## Fair use

This tool downloads videos you point it at, using your own browser session. That means it can reach
anything *you* can already see while logged in.

Use it on content you have the right to analyze. Respect the terms of service of the platforms you
pull from, and don't republish other people's work as your own. "Study this design and build
something in that spirit" is a good use. "Pixel-copy this person's site and ship it" is not, and the
license here doesn't grant you rights to their content.

## Contributing

Issues and PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Run `./test.sh smoke` before
opening a PR.

## License

MIT — see [LICENSE](LICENSE).
