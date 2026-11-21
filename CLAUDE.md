# Project: Reels / YouTube video studio

## Memory (read first)
- At the start of a session run `python3 .claude/memory/memory.py top 15` and follow what it says.
- When the user corrects you, states a preference, or a decision or fix is made, append it:
  `python3 .claude/memory/memory.py add <preference|decision|pattern|fact> <key> "<value>" "<context>" <0-1 importance>`
  (same key = newer entry wins). Pipeline map: `.claude/memory/graph.json`. Last session summary: `.claude/sessions/`.

## Who and how
- The user writes in Turkish. Answer in Turkish: short, plain words, no jargon.
- The user wants finished videos, not long option lists. Make a sensible choice, build it, show it.
- Never post, schedule or publish anything to Instagram or YouTube without the user's explicit "evet" on that exact video and caption.
- Never put API keys, tokens or client secrets in the repo or ask for them in chat; use the environment's network secrets (secure form).

## What this repo is
- Skills live in `.claude/skills/` (video creation, editing, analysis, publishing, plus general coding/agent skills).
- Episodes live in `video-agent/edits/<slug>/`: `script.json`, `build.py` (writes `index.html` + `assets/master.m4a`), `scenes/` (images), `fonts/`, `lib/gsap.min.js`.
- `assets/`, `output/`, `snapshots/`, `.env`, `node_modules/` are git-ignored (big or secret). Commit sources only.
- Default branch: `claude/new-session-0db055` (the only branch; push there).

## Video pipeline (what works)
- Visuals: 3D animated-film style stills generated in Figma (`generate_image`, gemini-3.1-flash-lite-image, 9:16), upscaled to 1080 wide, animated with Ken Burns + transitions in HyperFrames.
- Render: `npx --no-install hyperframes render <dir> -o <dir>/output/x.mp4 -f 30 -q high`, then a CRF 21 share copy with ffmpeg. Check with `hyperframes lint` and `hyperframes snapshot --at ...` before rendering.
- Keep GSAP and fonts local (Chrome cannot reach CDNs); name font families "BH Fredoka" / "BH Nunito" so HyperFrames does not override them.
- Music/SFX: CC0 library in `.claude/skills/editing-videos/library/` and the generated beds in `.claude/skills/short-editing/assets/music/`.

## Voices
- Preferred: ElevenLabs real Turkish voices via the ElevenLabs connector (e.g. Seyfullah Kartal for old men). Free plan credits run out fast; check before a full episode.
- Fallback: ElevenLabs v3 premade voices with emotion tags; or free Edge voices (`edge-tts --proxy "$HTTPS_PROXY"`, tr-TR-AhmetNeural / tr-TR-EmelNeural). The user did not like the Edge voices; use them only when nothing else is available, and say so.

## Accounts
- Instagram: connected through WoopSocial (MCP at api.woopsocial.com, key saved as a network secret). Use the instagram-skill flow.
- YouTube: ultimate-youtube skill; OAuth client file goes in `~/.ultimate-youtube/` (not in the repo).

## Content direction
- Format the user chose: "Gizli Reklam" (secret free ads for struggling local businesses, ~70 s, "Yarın kimin reklamını yapalım?"). Real businesses need the owner's consent and real footage; never present a made-up business or result as real.
- Turkish AI-animation reels that break out: absurd non-human characters + very Turkish daily life + episodic "Bölüm X" with a cliffhanger.

## Environment
- Cloud environment "Test" has a setup script that installs whisper, HyperFrames packages, the short-editing engine, edge-tts, uv and skill deps on each new session.
