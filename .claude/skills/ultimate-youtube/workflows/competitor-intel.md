# Competitor intelligence

Goal: find what is already working for channels like the user's, explain why,
and turn it into original videos for the user. Reference:
`references/outlier-method.md`.

## 1. Find the right competitors (skip if the profile lists them)

- `yt_competitors.py discover "<niche phrase>" --lang xx --region XX --include-video-search`
  -> channels sorted by views per video. Run 2-3 phrasings of the niche.
- Prefer a mix: 2 similar-size channels (what works at the user's level), 2
  larger ones (proven ceilings), and any **small/young channel with high views per
  video** (a format that is working right now).
- Same language and audience as the user beats same topic in another language,
  but a format that works in one language is often an opening in another
  (note it as a "bend" opportunity).

## 2. Scan

`yt_competitors.py scan @handle --max 100 [--tz <user's UTC offset>]` for each
(about 5 units each). Read from the summary:

- `outliers` - videos at 2x+ their neighbours' median. The core finding.
- `underperformers` - what the audience rejected.
- `formats` - long vs Shorts vs live: counts and medians.
- `cadence` - uploads/week, gaps, most common day and hour (in the user's timezone).
- `title_patterns.features_that_differ_in_outliers` - e.g. outliers use questions
  or numbers more often than the rest.
- `winning_terms` - title words whose videos beat the channel median (topic signal).
- `length_buckets` - which long-form lengths perform best for that channel.
- `frequent_title_phrases`, `top_tags`.

For several channels at once: `yt_competitors.py compare @a @b @c` and
`yt_competitors.py outliers @a @b @c --days 90` (cross-channel outlier list).

## 3. Explain the outliers

Pick the top 3-5 outliers across channels (prefer recent ones, last 6-12 months)
plus 1-2 underperformers from the same channel for contrast. For each run
`yt_competitors.py video <url> --lang <their language>` and follow
`workflows/video-breakdown.md`. That gives the packaging, timing, hook, structure
and audience-reaction evidence.

## 4. Turn findings into a gap map

| Gap type | Question | Source |
|---|---|---|
| Topic | Which winning topics has the user not covered? | outliers + winning_terms vs user's scan |
| Format | Which proven formats (list, story, explainer, challenge, comparison...) has the user not tried? | outlier formats vs user's formats |
| Packaging | Which title/thumbnail formulas win in the niche? | title_patterns, outlier thumbnails |
| Audience | What do competitor viewers ask for that nobody made? | `yt_comments.py channel @comp --videos 10` (requests, questions) |
| Language/region | Is a format working in one language but missing in the user's? | discover in both languages |
| Timing/cadence | When do competitors post; is there an empty slot? | cadence |

## 5. Deliver

Fill `templates/competitor-report.md`. Every finding needs: the linked video or
channel, views, outlier ratio, date. End with 5 video opportunities, each with
the evidence (two independent signals is best, e.g. competitor outlier + comment
requests), a working title, the angle that makes it the user's own, and the
format to use. Save to `youtube-reports/competitors-<date>.md`.

## 6. Keep watching

Offer a watchlist so this becomes ongoing: `yt_competitors.py watch add @a @b @c`
then `watch run` daily or weekly (see `workflows/routines.md`). The digest shows
new uploads, early breakouts (fresh videos already above the channel's typical
lifetime views) and view velocity since the last run.

## Rules

- Never recommend copying a title, script or thumbnail. Extract the pattern
  (slots, beats, composition) and make it original.
- Outliers prove the audience wanted that video from that channel. Big-channel
  hits may rely on fame, budget or access; say so when a move won't transfer.
- One outlier is a hint; a pattern across several outliers or channels is a finding.
- Private metrics (CTR, retention, revenue) of other channels are unknown.
  Infer carefully and label inferences.
