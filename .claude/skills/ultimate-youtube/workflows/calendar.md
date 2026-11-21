# Content calendar

Goal: a realistic month (or quarter) of uploads that mixes proven demand with
consistency the creator can sustain.

## Inputs

- `channel-profile.md`: sustainable uploads per week, formats, languages, goals.
- Ranked ideas from `workflows/trends-and-ideas.md` (run it first if there are none).
- Best publishing slot: `yt_competitors.py scan @own --tz <offset>` (when the
  channel usually posts) and `yt_analytics.py daily`/`geography` (when and where
  the audience is). Publishing time matters less than consistency; pick a slot
  a few hours before the audience's peak and keep it.
- Seasonal moments, events and holidays relevant to the audience's countries
  and the niche (web search if needed).

## Build

1. Set the cadence the creator can keep for 3 months (consistency beats bursts).
2. Assign content pillars (3-5 recurring themes/series from the profile) so the
   mix stays balanced.
3. Place the "make first" ideas early, seasonal ideas 2-4 weeks before their
   moment (search demand rises before the date), and series in viewing order.
4. Add Shorts: cut-downs of each long video plus native Shorts.
5. For each slot: date, format, pillar, working title, status (idea / scripted /
   produced / scheduled / published), target language(s), playlist.
6. Leave one flexible slot per month for a trend or fast follow-up to a hit.

## Deliver

Fill `templates/content-calendar.md` (markdown table). Save to
`youtube-reports/calendar-<month>.md`. Offer to schedule finished videos with
`yt_publish.py upload ... --publish-at` (approval rules apply).

## Review monthly

Compare plan vs actual and results (`yt_analytics.py top-videos --days 30`),
move the winning pillars up, and drop what didn't work twice.
