# The video-analyze guide

Everything beyond the README: how the pipeline actually works, how to use it for design
replication, how to extend it, and what to do when it breaks.

- [The design replication workflow](#the-design-replication-workflow)
- [Pipeline internals](#pipeline-internals)
- [Choosing your flags](#choosing-your-flags)
- [Getting Instagram and TikTok to work](#getting-instagram-and-tiktok-to-work)
- [Consuming the manifest yourself](#consuming-the-manifest-yourself)
- [Extending the pipeline](#extending-the-pipeline)
- [Troubleshooting](#troubleshooting)

---

## The design replication workflow

This is the use case the skill was built around: you see a reel or a demo video with an interface,
an animation, or a layout you want, and you want a spec you can build from.

### 1. Ask for it explicitly

The skill flags design references on its own, but you get sharper output when you say what you're
after:

> "analyze this reel — I want to rebuild the pricing page they show at the end"

> "watch this and describe the card hover animation frame by frame"

> "extract every distinct screen in this app demo and write me a replication prompt for each"

### 2. Use high fidelity, and raise the frame cap

The defaults are tuned for general video understanding — around 15 frames. UI walkthroughs move
fast, and a 3-second interval will skip whole screens.

```bash
run.sh <url> --fidelity high --interval 1 --max-frames 40
```

One frame per second at 40 frames covers a 40-second demo without missing transitions. High fidelity
is not optional here: the low-fidelity grid downscales cells to 512px, which is exactly enough to
destroy the small text and 1px borders you're trying to read.

### 3. Read what comes back

For each frame Claude flags as a design reference, you get a block like this:

```
[DESIGN REFERENCE — t=6s]
Replication prompt:
"<dense, directive spec>"
image_path: /tmp/video-analyze/.../frames/0004.jpg
```

The replication prompt is written as a brief for an image or UI generator, and the skill instructs
Claude to cover:

| Dimension | What gets described |
|---|---|
| **Layout** | Exact positioning, alignment, white space, proportions |
| **Typography** | Serif/sans/mono/display, weight, size hierarchy, tracking, case, color |
| **Color** | Background, foreground, accent — as hex-ish descriptors, not names |
| **Elements** | Objects, icons, imagery, size relative to frame, opacity, blur, shadow |
| **Composition** | Single focal point vs scattered, centered vs off-axis, density |
| **Texture** | Flat, grainy, glossy, painterly, photographic collage |
| **Motion** | How elements move — drift, snap, spiral, fade |
| **Mood** | Editorial, brutalist, minimal luxury, techy, organic |

The skill explicitly bans vague words like "clean" and "modern." If output still comes back mushy,
push on it: *"redo the t=6s prompt with specific hex values and tracking numbers."*

### 4. Chain into a build

Once you have the prompts, keep going in the same session — Claude still has the frames in context:

> "now build the t=6s screen as a React component with Tailwind"

> "give me the CSS keyframes for the transition between t=4s and t=6s"

The frames stay visible, so you can correct against the source: *"no, the nav is smaller than that —
look at frame 4 again."*

### 5. Compare against what you built

Screenshot your implementation, then ask Claude to diff it against the reference frame. The original
is still in context, which makes this far more useful than describing the difference in words.

---

## Pipeline internals

Four stages, each a standalone script reading and writing one shared output directory.

```
url ──▶ download.sh ──▶ extract.sh ──▶ transcribe.sh ──▶ assemble.py ──▶ manifest.json
```

### Stage 1 — `download.sh`

Produces `video.mp4` and `download_method.txt`.

The strategy branches on whether the URL is a "social" URL (Instagram or TikTok):

**Social URLs** try, in order:
1. `yt-dlp --cookies-from-browser <browser>` — uses your logged-in session
2. `yt-dlp` with no auth — occasionally works for public posts
3. Apify (`apify/instagram-scraper` or `clockworks/tiktok-scraper`), if `APIFY_API_TOKEN` is set —
   returns a CDN URL, which is then fetched with `curl` plus the right `Referer` header

**Everything else** tries `yt-dlp` first (which covers YouTube, X, Vimeo, and hundreds more), then
falls back to plain `curl`.

Every path ends in `validate_video()`, which catches the most common silent failure: a download that
"succeeds" but returns an HTML auth wall instead of a video. If the MIME type is `text/html`, the
file is deleted and the next strategy runs.

`--ig-tt-auth` overrides the ladder: `cookies` refuses to use Apify, `apify` skips yt-dlp entirely.

### Stage 2 — `extract.sh`

Produces `frames/NNNN.jpg`, `audio.mp3`, and `duration.txt`.

Duration comes from `ffprobe`. Frames are sampled with the ffmpeg filter `fps=1/<interval>` at
quality `-q:v 3` (high, close to visually lossless for JPEG). Audio is extracted separately as
128k-ish MP3 via `libmp3lame` — MP3 rather than WAV specifically to stay under Whisper's 25MB
upload limit for long videos.

### Stage 3 — `transcribe.sh`

Produces `transcript.json`.

Posts `audio.mp3` to `POST /audio/transcriptions` with `response_format=verbose_json` and
`timestamp_granularities[]=segment`, which is what gives per-segment start/end times.

**This stage never fails the pipeline.** No key, no audio, API error, rate limit — it writes a
transcript file with an `error` field and exits 0. Frames are the primary output; the transcript is
an enhancement.

Set `OPENAI_BASE_URL` to point at any OpenAI-compatible endpoint, including a local
faster-whisper server, and `WHISPER_MODEL` to change the model.

### Stage 4 — `assemble.py`

Produces `manifest.json` and, in low fidelity, `grids/grid_NNNN.jpg`.

Two jobs:

**Alignment.** For each frame at time `t`, find transcript segments overlapping the window
`[t, t + interval)`. Overlapping segments get joined into one string. If nothing overlaps — silence,
or a gap between segments — it falls back to the nearest segment by start time, so a frame is rarely
left with no context at all.

**Grid tiling** (low fidelity only). Chunks frames by `--grid-size`, thumbnails each to a 512px box
with LANCZOS resampling, pastes them onto a dark canvas with a 4px gutter, and burns an `MM:SS`
label into each cell in yellow with a black drop shadow so it survives JPEG compression. Saved at
quality 70 — a 4-up grid typically lands around 35KB versus ~150KB for four separate frames.

Font lookup walks a list of common paths across macOS, Debian, Fedora, and Windows, falling back to
Pillow's bitmap default. Grids still render if none are found; the labels just get ugly.

---

## Choosing your flags

**How many frames do I actually need?**

| Content | Suggested |
|---|---|
| UI walkthrough / app demo | `--fidelity high --interval 1 --max-frames 40` |
| Design reel, fast cuts | `--fidelity high --interval 1 --max-frames 30` |
| Talking head | `--fidelity low --grid-size 4` — the audio carries it |
| Tutorial with slides | `--fidelity low --grid-size 2` |
| Long lecture (20min+) | `--fidelity low --max-frames 30 --grid-size 4` |
| "Just tell me what's in it" | defaults |

**Context cost, roughly.** A high-fidelity frame runs on the order of a typical image in context; a
4-up grid costs about one image for four moments. If you're pulling 40 frames, expect it to be a
meaningful chunk of the window — worth it for a design spec, wasteful for a summary.

**When to skip transcription.** `--skip-transcript` saves an API call and several seconds. Use it
for silent screen recordings, music-only videos, or when you only care about the visuals. You can
always rerun.

---

## Getting Instagram and TikTok to work

This is where most failures happen. In order of likelihood:

**1. You're not logged in, or you're logged in somewhere else.** yt-dlp reads cookies from Chrome by
default. If you use another browser:

```bash
export VIDEO_ANALYZE_BROWSER=firefox   # safari, edge, brave, chromium, opera, vivaldi
```

**2. Chrome is locking its cookie database.** On macOS, yt-dlp sometimes can't read Chrome's
cookies while Chrome is running, and Chrome may prompt for Keychain access. Quit Chrome fully and
retry, and approve the Keychain prompt if it appears.

**3. Safari needs Full Disk Access.** To read Safari cookies, your terminal app needs Full Disk
Access in System Settings → Privacy & Security.

**4. The post is private.** Cookies only get you what your account can see. A private account you
don't follow will fail regardless.

**5. Fall back to Apify.** Get a token at
[console.apify.com](https://console.apify.com/account/integrations) and set `APIFY_API_TOKEN`. The
free tier covers casual use. Force that path to test it:

```bash
run.sh <url> --ig-tt-auth apify
```

Apify runs the scraper server-side, so it sidesteps cookies entirely — but it costs credits and is
slower (typically 30–90 seconds).

---

## Consuming the manifest yourself

`run.sh` prints exactly one thing to stdout — the manifest path. Everything else goes to stderr.
That makes it clean to script:

```bash
MANIFEST=$(scripts/run.sh "$URL" --skip-transcript --max-frames 12)

# every frame path, in order
python3 -c "
import json, sys
m = json.load(open('$MANIFEST'))
for f in m['frames']:
    print(f\"{f['t_sec']:>6.1f}s  {f['image_path']}\")
"
```

Pull the full transcript as plain text:

```bash
python3 -c "
import json
m = json.load(open('$MANIFEST'))
print((m.get('transcript') or {}).get('text', ''))
"
```

**Stability.** Treat `source`, `extraction`, `frames[]`, `grids[]`, and `transcript` as the public
contract; new keys may be added, existing ones won't be renamed. `transcript` is `null` whenever
transcription was skipped or failed — always guard for it.

---

## Extending the pipeline

The stages are decoupled by the output directory, so you can replace any one of them without
touching the others.

**Add a downloader.** Write a function in `download.sh` that leaves a valid file at
`$OUT_DIR/video.mp4`, echo an identifier into `download_method.txt`, and insert it into the ladder.
The `validate_video` guard will catch it if it returns an auth wall.

**Change frame selection.** `extract.sh` samples on a fixed interval, which is simple and
predictable but will happily give you fifteen near-identical frames of a static screen. A scene-cut
detector is the obvious upgrade:

```bash
ffmpeg -i video.mp4 -vf "select='gt(scene,0.3)',showinfo" -vsync vfr frames/%04d.jpg
```

That yields one frame per visual change, which is much better for UI demos — but frame timestamps no
longer follow `index * interval`, so `assemble.py`'s alignment math needs updating to read real
timestamps from ffmpeg's `showinfo` output.

**Swap the transcriber.** Anything that writes `transcript.json` in Whisper's `verbose_json` shape
(`{language, text, segments: [{start, end, text}]}`) drops straight in.

**Change what Claude does with the output.** Edit `SKILL.md` — that's the file Claude reads. The
design-reference block format lives in the "Analyze" section. Reinstall with `./install.sh` after
editing, or use `./install.sh --link` once so your clone *is* the installed skill.

---

## Troubleshooting

**`NEEDS_SETUP: ffmpeg yt-dlp`**
Dependencies missing. `scripts/setup.sh check` prints the install command for your platform.

**`ERROR: Could not download video`**
See [Getting Instagram and TikTok to work](#getting-instagram-and-tiktok-to-work). For other sites,
try `yt-dlp <url>` directly — if that fails too, it's upstream, and `yt-dlp -U` is often the fix
since sites break extractors regularly.

**`Downloaded file is HTML (auth wall / redirect)`**
Working as intended — the guard caught a login page pretending to be a video. It means cookies
didn't authenticate. Log in, or use Apify.

**Transcript is `null` but I set `OPENAI_API_KEY`**
Check stderr for the HTTP code. `401` is a bad key, `429` is rate limiting, `413` means the audio
exceeded 25MB — trim the video or transcribe it in chunks.

**Frames are all black**
Some videos start on a black frame or fade in. Try `--interval 1`, or a non-zero start via ffmpeg
directly. Also check `video.mp4` actually plays.

**Grid timestamps look like blurry blocks**
No TrueType font was found, so Pillow's bitmap default is being used. Install DejaVu
(`sudo apt install fonts-dejavu-core`) or add your font path to the list in `assemble.py`.

**"Claude isn't picking up the skill"**
Skills load at session start — start a new session after installing. Confirm it landed with
`ls ~/.claude/skills/video-analyze/`, and that `SKILL.md` is present with valid frontmatter.

**Output directory is filling my disk**
Videos and frames accumulate under `/tmp/video-analyze/`. Clear it with
`rm -rf /tmp/video-analyze/`, or point `VIDEO_ANALYZE_TMPDIR` somewhere you manage.
