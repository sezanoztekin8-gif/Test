# Analytics: how is the channel doing, and why

Scripts: `yt_analytics.py` (Analytics API), `yt_reporting.py` (impressions and
CTR). Reference: `references/analytics-metrics.md`.

Data lags 1-3 days. Windows end yesterday by default. Say which window you used.

## Quick answers

| Question | Command |
|---|---|
| How did the last 28 days go? | `overview` (includes change vs the previous 28 days) |
| Which videos carried the period? | `top-videos --days 28` |
| How is one video doing? | `video VIDEO` (lifetime by default) |
| Where do viewers drop off? | `retention VIDEO` |
| Where do views come from? | `traffic` (or `traffic --video VIDEO`) |
| What do people search to find me? | `search-terms` |
| Which videos recommend mine? | `suggested` |
| Who watches? | `audience`, `geography`, `devices` |
| Am I getting clicks? | `yt_reporting.py ctr --days 28` (needs `yt_reporting.py setup` 1-2 days earlier) |
| Money | `revenue` (needs `login --revenue`) |
| Everything, saved | `report --days 28` then fill `templates/analytics-report.md` |

## Diagnosing a change ("views dropped", "this video flopped")

Work down this tree and stop where the evidence points. Quote the numbers.

1. **Is it real?** Compare the same-length windows (`overview` does this). Check
   `daily` for one-off spikes last period (a viral video, an external link) that
   make this period look bad by comparison. Seasonality: compare with the same
   weeks last year if the channel is old enough (`--start/--end`).
2. **Which surface changed?** `traffic` for both periods. A drop concentrated in
   one source points to the cause:
   - Browse features / Suggested down -> packaging (CTR) or audience satisfaction
     (retention) of recent uploads; fewer impressions served.
   - YouTube search down -> a ranking video is aging out or the topic's demand
     fell (check `search-terms`, then `yt_trends.py suggest`/`search`).
   - Shorts feed down -> Shorts output or Shorts performance changed.
   - External down -> a referral (site, social post) dried up.
3. **Impressions or clicks?** `yt_reporting.py ctr`: fewer impressions with
   steady CTR = YouTube is showing it less (satisfaction/topic interest);
   steady impressions with lower CTR = the title/thumbnail is not pulling.
4. **Do viewers stay?** `retention VIDEO` for recent uploads vs older winners.
   Look at the first 30 seconds (hook) and the biggest drops.
5. **Is it the content mix?** `top-videos` this period vs last: are recent topics
   or formats different from what used to work? Cross-check with
   `yt_competitors.py scan @own_handle` (outliers vs underperformers).
6. **Upload consistency**: gaps in uploads usually show as a drop in browse traffic.

Report as: what changed (numbers), the most likely cause (evidence), what to do
next (one to three actions), how to tell if it worked (metric + date).

## Single-video review

`video VIDEO` + `retention VIDEO` + `traffic --video VIDEO` + `search-terms --video VIDEO`
and, if available, its CTR from `yt_reporting.py ctr`. Compare with the channel's
own medians, not with other channels. Retention guide:

- Big drop in the first 30 seconds -> the opening didn't confirm what the title
  and thumbnail promised (`workflows/script.md`).
- Steady slide -> pacing; add re-hooks and cut slow sections.
- Cliff in the middle -> a specific moment lost people; look at the transcript
  there (`yt_transcripts.py get VIDEO --own --timed --start S --end S`).
- Bumps -> moments people rewatch; make more of that.
- `relativeRetentionPerformance` > 0.5 means better than similar-length videos on YouTube.

## Weekly report

`yt_analytics.py report --days 7` (or 28), `yt_reporting.py ctr --days 7` if
available, `yt_competitors.py watch run` if a watchlist exists. Fill
`templates/analytics-report.md`. Keep it to what changed, why, and the next
action.
