# Transcripts

## Methods (tried in order)

1. **youtube-transcript-api** - any public video with captions (manual or
   auto-generated). No API key, no quota.
2. **yt-dlp** - subtitle download, if installed (`pip install yt-dlp`).
3. **captions.download** (Data API, 200 units) - only videos the signed-in
   account owns; enable with `--own`.

Results are cached in `~/.ultimate-youtube/cache/transcripts/<id>.json` and
searchable with `yt_transcripts.py search`.

## Languages

- `--lang hi,en` = try Hindi first, then English. Manual captions are preferred
  over auto-generated ones in the requested languages; otherwise the first
  available track is used and `available` lists the alternatives.
- `--translate en` = YouTube's machine translation of the track (good enough for
  analysis, not for quoting).
- Auto-captions miss names, numbers and specialised terms. Check against the title,
  description and context before quoting.
- Videos without speech (music, pure visuals) or with captions disabled have no
  transcript. Say so; analyse packaging and comments instead.

## "Blocked" errors

YouTube blocks caption requests from many cloud and VPS IP ranges and from IPs
that make too many requests. Symptoms: `RequestBlocked`, `IpBlocked`, HTTP 429.

Fixes, in order:
1. Run from a home or office connection.
2. Slow down: sync fewer videos at a time.
3. Install yt-dlp (different request path).
4. Configure a residential proxy. youtube-transcript-api supports
   `proxy_config` (see its README); route it via environment variables
   `HTTPS_PROXY`/`HTTP_PROXY` if the library version supports them.

## Using transcripts well

- Hooks: `yt_transcripts.py hook URL --seconds 45`.
- Pacing: `yt_transcripts.py stats URL` (words per minute, words by minute).
- Structure: read the timed transcript and tag beats (`references/retention-and-hooks.md`).
- Research library: `sync @channel --max 50` for several competitors, then
  `search "phrase"` to see who covered what, and when.
- Quote only short excerpts; never republish a full transcript.
