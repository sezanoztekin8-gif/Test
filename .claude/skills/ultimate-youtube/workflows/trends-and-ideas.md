# Trends, keywords and video ideas

Goal: a ranked list of ideas the user can make next, each backed by demand
evidence. Read `channel-profile.md` first (niche, audience, languages, formats,
topics to avoid).

## 1. Gather signals (use what applies)

| Signal | Command | What it tells you |
|---|---|---|
| What people type | `yt_trends.py suggest "<seed>" --expand --lang xx --region XX` | real search phrasing, modifiers, questions (free) |
| What wins in search results | `yt_trends.py search "<phrase>" --days 180 --lang xx --region XX` | views/day, views per subscriber, small channels breaking out |
| Competitor outliers | `yt_competitors.py outliers --watchlist --days 90` (or list channels) | proven demand from this audience |
| Audience requests | `yt_comments.py channel @competitor --videos 10` and `yt_comments.py mine` | explicit asks, unanswered questions |
| Your own winners | `yt_analytics.py top-videos --days 365`, `search-terms` | topics your audience already trusts you on |
| Platform trending | `yt_trends.py trending --region XX --category ID` | broad, fast-moving interest (rarely niche) |
| Seasonality / news | web search, Google Trends, DataForSEO if installed | timing windows |

Use 3-5 seed phrases. For multi-language channels, run suggest/search per language.

## 2. Generate candidates

Aim for 15-25 raw ideas. Good sources:
- An outlier's topic with a new angle, format or audience (never the same video).
- Recurring comment requests and questions.
- Autocomplete questions ("why", "how", "what happens if").
- Your own winners: sequels, deeper dives, opposite angles, series.
- A format that wins in another language or niche, bent into this one.

## 3. Score each idea (1-5 each, show the table)

| Criterion | 5 means |
|---|---|
| Demand | strong evidence: outliers on it, search results with high views/day, autocomplete |
| Competition gap | few good videos, or the top ones are old/weak/in another language |
| Audience fit | squarely what the profile's audience wants; your winners are nearby |
| Packaging potential | a clear, curiosity-driving title and thumbnail exist |
| Feasibility | doable with the user's skills, tools, time and budget |
| Originality | the user has a real angle (experience, access, craft, perspective) |

Total /30. Break ties by "evidence from two independent signals".

## 4. Deliver the top 10

Fill `templates/video-ideas.md`: for each idea the working title (2 options),
thumbnail concept, hook angle, format and target length, the evidence (linked
videos/numbers/requests), traffic strategy (search, browse, Shorts), and score.
Mark 2-3 as "make first". Offer to continue into `workflows/script.md` or
`workflows/calendar.md`.

## Rules

- Autocomplete has no volume numbers; treat order as a rough popularity hint.
- A topic that only big channels win is a weaker bet for a small channel.
- Respect the profile's no-go topics and accuracy rules.
