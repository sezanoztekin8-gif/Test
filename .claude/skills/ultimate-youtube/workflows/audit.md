# Channel audit

A scored health check across five dimensions, each backed by data. Use the
channel profile for context. Works for the user's channel (full) or any public
channel (public data only; say which).

## Collect

Run what credentials allow. If the Agent tool is available, the three data
groups can run in parallel subagents; otherwise run them in sequence.

1. **Public picture** - `yt_competitors.py scan @handle --max 100` (outliers,
   formats, cadence, title patterns, length buckets) and
   `yt_seo.py channel @handle --max 50` (or `--mine`).
2. **Private picture** (read token) - `yt_analytics.py report --days 90`,
   `retention` for the 3 latest long videos and the 2 best,
   `yt_reporting.py ctr --days 90` if a reach job exists.
3. **Market picture** - `yt_competitors.py compare @own @comp1 @comp2 @comp3 --max 50`
   using competitors from the profile.

## Score (0-10 each, with the reason)

| Dimension | Look at | Strong signs |
|---|---|---|
| Packaging | CTR vs own history, title patterns, thumbnail consistency, SEO lint scores | outliers share a clear title/thumbnail formula; few lint errors |
| Retention | avg view %, first-30s drop, relative retention | opening holds; relative retention > 0.5 |
| Content-market fit | outlier rate, topic lift, views/sub vs competitors, search terms | repeatable winning topics; more than one outlier per 20 videos |
| Consistency | uploads/week, longest gaps, format mix | steady cadence the creator can sustain |
| Growth & audience | net subs, returning interest, traffic mix balance, geography/language fit | not dependent on one source or one video |

Add **Monetization** as a sixth score when relevant (`references/monetization.md`).

## Write

Fill `templates/audit-report.md`: overall score, the scorecard, the three
biggest problems with evidence, the three biggest opportunities (usually from
outliers and competitor gaps), and a 30-day action list ordered by impact and
effort. Save to `youtube-reports/audit-<handle>-<date>.md`.

Point the lowest-scoring dimension to its workflow (packaging -> `packaging.md`,
retention -> `script.md`, fit -> `competitor-intel.md` + `trends-and-ideas.md`,
consistency -> `calendar.md`, growth -> `strategy.md`).
