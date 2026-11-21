---
name: ultimate-youtube
description: >
  All-in-one YouTube skill for any creator, niche or language. Publishes and
  manages videos via the YouTube Data API v3 (upload, schedule, edit metadata,
  thumbnails, playlists, captions, translations, delete - with preview,
  approval and undo). Reads private analytics (watch time, retention, traffic,
  search terms, impressions/CTR, audience, revenue). Researches competitors:
  scans any channel, finds outlier videos, pulls transcripts and comments, and
  explains why a video got its views so the format can be reused. Also covers
  trends, keywords, comment mining, SEO, hooks, scripts, thumbnails, Shorts,
  content calendars, audits and growth strategy. Use for anything YouTube:
  "upload my video", "change my title", "how is my channel doing", "why did
  views drop", "analyze this competitor", "why did this go viral", "get the
  transcript", "video ideas", "write a script", "thumbnail", "SEO", "content
  calendar", "audit my channel", "Shorts", "monetize".
---

# Ultimate YouTube

One skill, four jobs. Python scripts fetch real data; workflow files tell you
how to turn that data into decisions. You choose the workflow, run the scripts,
check the quality, and report back.

| Job | What it covers | Workflow files |
|---|---|---|
| **Publish** | upload, schedule, edit, thumbnails, playlists, captions, translations, delete, undo | `workflows/publish.md` |
| **Analyze** | your channel's private analytics, audits, weekly reports | `workflows/analytics.md`, `workflows/audit.md` |
| **Research** | competitors, outlier videos, transcripts, comments, trends, keywords | `workflows/competitor-intel.md`, `workflows/video-breakdown.md`, `workflows/trends-and-ideas.md`, `workflows/audience-research.md` |
| **Create** | ideas, hooks, scripts, titles, thumbnails, SEO, Shorts, calendars, strategy | `workflows/script.md`, `workflows/packaging.md`, `workflows/seo.md`, `workflows/shorts.md`, `workflows/calendar.md`, `workflows/strategy.md` |

`SKILL_DIR` below means the folder this file is in. Scripts live in
`SKILL_DIR/scripts/` and every one prints JSON and supports `--help`.

## Rules that always apply

1. **Never change a channel without approval.** Every write command (upload,
   update, delete, thumbnail, playlist, captions, localize, revert) runs as a
   dry run and prints a preview. Show the preview to the user. Re-run with
   `--confirm` only after the user says yes **to that specific preview**.
   Approval for one change does not cover the next. Before the first write in a
   session, run `yt_auth.py whoami --write` and tell the user which channel will
   be changed.
2. **Prefer reversible actions.** Suggest private/unlisted over delete. Every
   update is backed up and `yt_publish.py revert VIDEO` restores it. Deletes
   cannot be undone, so say that before asking for approval.
3. **Every number comes from a script or the user.** Never invent view counts,
   CTRs, benchmarks or search volumes. Label anything inferred as inference
   ("likely", "suggests"). Other channels' CTR, retention and revenue are not
   available through any API, so never state them as fact.
4. **Compare like with like.** Judge a video against its own channel's recent
   baseline (outlier ratio), Shorts against Shorts and long-form against
   long-form. Generic "good CTR is X%" benchmarks are a last resort and must be
   labelled as rough.
5. **Protect the quota.** Uploads lists cost 1 unit per 50 videos; `search.list`
   has its own small bucket of 100 calls/day. Use the uploads-based scripts
   first and search only to discover. Check `yt_auth.py quota` before big jobs
   and warn the user when a plan needs more than ~20 search calls or 2,000 units.
6. **Keep the context lean.** Scripts save full data to `youtube-reports/` and
   print a summary. Read saved files selectively (specific keys, a few rows), and
   never paste a full transcript to the user; quote the lines that matter.
7. **Speak the creator's language.** Reply in the language the user writes in.
   Pass `--lang` (comma list, e.g. `--lang hi,en`) for transcripts and
   `--lang/--region` for research so results match their audience.
8. **The creator decides.** Recommend one clear next action, with the evidence
   behind it. Don't copy competitors' titles, scripts or thumbnails; extract the
   reusable pattern and make it original.

## Step 0: know the channel

Most workflows need context about the creator. Look for `channel-profile.md`
in the current project (or the path in `$YT_PROFILE`). If it exists, read it
first; it holds the niche, audience, languages, goals, competitors and voice.
If it is missing and the task needs it, run `workflows/onboarding.md` (a few
questions plus a quick data pull) and save the profile from
`templates/channel-profile.md`. Never put a creator's details into this skill
folder: the skill stays generic so anyone can use it.

## Step 1: check what is set up

Run `python SKILL_DIR/scripts/yt_auth.py doctor` the first time in a session
(or when a script errors). It reports which capabilities work:

| Capability | Needs | If missing |
|---|---|---|
| Public research (any channel, video, comment, search) | API key or read token | `workflows/setup.md` part A (5 min) |
| Transcripts | nothing (youtube-transcript-api) | works out of the box |
| Your analytics, your private videos | read token | `workflows/setup.md` part B |
| Publishing and editing | write token | `workflows/setup.md` part C |
| Impressions and CTR | read token + Reporting job | `yt_reporting.py setup`, then wait 24-48h |

If credentials are missing and the user doesn't want to set them up now, keep
working: ask for numbers or screenshots from YouTube Studio, use transcripts
(no key needed), `yt_trends.py suggest` (no key needed) and web search.

## Step 2: route the request

| The user wants to... | Read | Main scripts |
|---|---|---|
| Set up credentials, fix auth errors | `workflows/setup.md` | `yt_auth.py` |
| Describe their channel, start fresh | `workflows/onboarding.md` | `yt_auth.py whoami`, `yt_competitors.py scan` |
| Upload, schedule, edit, delete, thumbnail, playlist, captions, translate titles, undo | `workflows/publish.md` | `yt_publish.py` |
| Know how the channel/a video is doing, why views dropped | `workflows/analytics.md` | `yt_analytics.py`, `yt_reporting.py` |
| Full channel health check | `workflows/audit.md` | analytics + `yt_seo.py channel --mine` + scan |
| Find competitors, analyze a channel, find what works in the niche | `workflows/competitor-intel.md` | `yt_competitors.py discover/scan/compare/outliers/watch` |
| Explain why one video got its views; break down its hook and structure | `workflows/video-breakdown.md` | `yt_competitors.py video`, `yt_transcripts.py` |
| Trending topics, keywords, video ideas, "what should I make next" | `workflows/trends-and-ideas.md` | `yt_trends.py`, `yt_competitors.py outliers` |
| What viewers ask for, complain about, want next | `workflows/audience-research.md` | `yt_comments.py` |
| Hooks and scripts | `workflows/script.md` | `yt_transcripts.py hook` for reference videos |
| Titles and thumbnails | `workflows/packaging.md` | `yt_competitors.py scan` (title patterns) |
| Description, tags, chapters, hashtags, upload package, AI-search visibility | `workflows/seo.md` | `yt_seo.py lint/video/channel` |
| Shorts strategy, turning long videos into Shorts | `workflows/shorts.md` | scan (format split), `yt_transcripts.py` |
| Content calendar, upload schedule | `workflows/calendar.md` | analytics + watchlist |
| Positioning, growth plan, monetization | `workflows/strategy.md` | audit outputs |
| A daily or weekly routine, "run my morning check" | `workflows/routines.md` | watchlist + analytics |

If the request is ambiguous, ask one short question. If it spans several
workflows ("plan, script and package my next video"), run them in order and
pass each output into the next: ideas -> script -> packaging -> seo -> publish.

## Step 3: deliver

- Lead with the answer or recommendation, then the evidence (numbers, linked
  videos, quotes), then the next step.
- Link every video and channel you cite (URLs come from script output; never
  guess one).
- For reports, fill the matching file in `templates/` and save it to
  `youtube-reports/` with a dated name. Tell the user the path.
- Check before you send: specific to this channel (not generic advice), every
  number traceable to data, every template section present. If something
  couldn't be fetched, say so instead of filling the gap.
- End with one or two concrete next steps (often another workflow).

## Script quick reference

Run with `python SKILL_DIR/scripts/<script> ...` after `pip install -r
SKILL_DIR/requirements.txt`, or with `uv run SKILL_DIR/scripts/<script> ...`
(dependencies are declared inside each script).

| Script | Commands | Typical cost |
|---|---|---|
| `yt_auth.py` | doctor, set-key, login [--write] [--revenue] [--manual], status, whoami, revoke, quota | 0-1 unit |
| `yt_publish.py` | mine, get, status, upload, update, revert, backups, delete, thumbnail, localize, captions, playlist, categories | upload: 1 upload-bucket call; update/delete/thumbnail/playlist: 50; captions upload: 400 |
| `yt_analytics.py` | overview, daily, top-videos, video, retention, traffic, search-terms, external, suggested, audience, geography, devices, playback, sharing, revenue, report | Analytics API (separate quota) |
| `yt_reporting.py` | types, jobs, setup, fetch, ctr | Reporting API (separate quota) |
| `yt_competitors.py` | scan, compare, outliers, video, discover, watch add/remove/list/run | scan of 100 videos ~5 units; discover 1-2 search calls |
| `yt_transcripts.py` | get, hook, stats, sync, search, list | 0 (sync: ~2 units for the video list) |
| `yt_comments.py` | video, channel, mine | 1 unit per 100 comments |
| `yt_trends.py` | suggest, search, trending, categories, video | suggest 0; search 1 search call + ~2 units; trending 1 |
| `yt_seo.py` | lint, video, channel, chapters | lint 0; others ~1-3 units |

Data lives outside the skill: credentials, cache, backups and the watchlist in
`~/.ultimate-youtube/` (`$YT_SKILL_HOME`); reports in `./youtube-reports/`
(`$YT_REPORTS_DIR`).

## References (load only when a workflow asks)

| File | Use for |
|---|---|
| `references/api-cheatsheet.md` | endpoints, scopes, quota, limits, known API gotchas |
| `references/algorithm.md` | how browse, suggested, search and Shorts surfaces pick videos |
| `references/outlier-method.md` | outlier math, what it can and can't prove, pitfalls |
| `references/retention-and-hooks.md` | hook patterns, beat types, pacing, retention-curve reading |
| `references/packaging.md` | title formulas, thumbnail principles, title-thumbnail pairing |
| `references/seo-geo.md` | metadata rules, chapters, hashtags, localization, AI-search visibility |
| `references/analytics-metrics.md` | metric definitions and the diagnosis tree |
| `references/shorts.md` | Shorts mechanics and repurposing |
| `references/monetization.md` | YouTube Partner Program and other revenue streams |
| `references/multilingual.md` | serving several languages: channels, audio tracks, translations |
| `references/transcripts.md` | transcript methods, language handling, blocked-IP fixes |
| `references/optional-integrations.md` | DataForSEO, TubeLab, image-generation MCPs if installed |
