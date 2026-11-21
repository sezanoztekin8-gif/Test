# Optional integrations

The skill works without any of these. Detect them by checking whether their
tools are available in the session; never block a workflow because one is missing.

## DataForSEO MCP (paid, per call)

Adds search volume, keyword difficulty, YouTube SERP snapshots, Google Trends.
Useful tools (names may vary by server version):
`serp_youtube_organic_live_advanced` (YouTube results for a keyword),
`serp_youtube_video_info_live_advanced`, `serp_youtube_video_comments_live_advanced`,
`serp_youtube_video_subtitles_live_advanced`, `kw_data_google_ads_search_volume`,
`dataforseo_labs_google_keyword_ideas`, `dataforseo_labs_bulk_keyword_difficulty`,
`kw_data_google_trends_explore`.
Use in `trends-and-ideas.md` and `seo.md` to add volume/difficulty to ideas.
Batch keywords into one call; tell the user before expensive runs.

## TubeLab MCP (paid credits)

Large YouTube research database: outlier search across many channels, niche
discovery, trending formats. Complements `yt_competitors.py` when the user wants
niche-wide discovery beyond the channels they know. Searches cost credits; reads
of channels/videos/transcripts are free on their side.
Setup: `claude mcp add --transport http tubelab https://public-api.tubelab.net/mcp`.

## Image generation MCPs

Any image tool that can render 16:9 images can turn thumbnail briefs from
`workflows/packaging.md` into drafts. Generate 2-3 concepts, 1280x720 or larger,
then check readability at small size. Uploading still goes through
`yt_publish.py thumbnail` with approval.

## Web search

Use for news, seasonal events, fact-checking, and anything outside YouTube's
APIs. Cite sources.

## Schedulers

`workflows/routines.md` can run on a schedule through the agent's scheduler.
Routines are read-only by design.
