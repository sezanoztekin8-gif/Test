# Routines: daily and weekly operating rhythm

Repeatable checks the user can run by saying "run my daily check" or schedule
with their agent's scheduler (e.g. a scheduled task or `/loop` in Claude Code).
Routines only read data and write reports; they never publish or edit.

## Daily brief (5-10 minutes, ~100 quota units)

1. `yt_competitors.py watch run` - new competitor uploads, early breakouts,
   fastest-moving videos since yesterday.
2. `yt_analytics.py overview --days 7` and `yt_analytics.py top-videos --days 2 --max 5`
   (if a read token exists) - how recent uploads are doing.
3. For any early breakout: `yt_competitors.py video <url>` - quick "why" note.
4. Fill `templates/daily-brief.md`: what happened, 3 things worth attention,
   1 recommended action today (e.g. "fast-follow this topic", "reply to these
   comments", "Short from yesterday's upload").

## Weekly review (20-30 minutes)

1. `yt_analytics.py report --days 7` and `yt_reporting.py ctr --days 7`.
2. `yt_competitors.py outliers --watchlist --days 14`.
3. `yt_comments.py mine --videos 5` - requests and questions this week.
4. Retention check on the week's uploads (`retention VIDEO`).
5. Update the calendar: keep, swap or add ideas based on the above.
6. Fill `templates/analytics-report.md` (weekly) and save it.

## Monthly

Run `workflows/audit.md` light (scores only), refresh the competitor list with
`discover`, and update `channel-profile.md` if the strategy shifted.

## Quota budget

A daily brief with a 10-channel watchlist costs about 30-40 units; a weekly
review about 100-300. Search is not used in routines unless discovering.
