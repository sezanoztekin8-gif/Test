# SEO and the upload package

Goal: copy-paste-ready metadata that helps search, suggested and AI answer
engines understand the video, without hurting clicks. Reference:
`references/seo-geo.md`.

## Research (5 minutes)

1. Primary phrase: `yt_trends.py suggest "<topic>" --expand --lang xx` -> pick the
   phrase viewers actually type.
2. Check what ranks: `yt_trends.py search "<phrase>" --lang xx --region XX`.
   Note title wording and lengths that win, and whether the results are old or weak.
3. Your own data: `yt_analytics.py search-terms` shows phrases that already bring
   viewers to the channel.

## Write the package (fill `templates/upload-package.md`)

- **Title**: from `workflows/packaging.md`. Search-led videos put the phrase early;
  browse-led videos favour curiosity. Max 100 characters.
- **Description**:
  - First 1-2 sentences (shown in search): what the viewer gets, with the main phrase.
  - 2-4 short paragraphs summarising the content in natural language (helps
    search and AI summaries). Name the key entities (people, places, products, concepts).
  - Chapters: `0:00` first, at least 3, each at least 10 seconds, descriptive names.
  - Links: related videos/playlist, resources, sources, socials.
  - 2-3 hashtags at the end (more than 15 makes YouTube ignore all of them).
  - Max 5,000 bytes. No `<` or `>`.
- **Tags**: 5-15, main phrase, variants, common misspellings, other-language
  spellings. Tags are a minor signal. Max 500 characters.
- **Category, language, audio language**, made-for-kids, synthetic-content
  disclosure (`workflows/publish.md`).
- **Playlist** and **end screen/cards** target videos.
- **Translations** of title/description for other audiences (`yt_publish.py localize`).
- **Captions**: upload accurate captions in the spoken language (better than
  auto-captions for accessibility and search).

## Validate

`yt_seo.py lint --title "..." --description @desc.txt --tags "..." --keyword "..." --duration <seconds>`
Fix every ERROR. WARNs are judgment calls; explain the trade-off.

## Existing videos

- Audit: `yt_seo.py channel --mine --max 50` -> worst scores and most common issues.
- Fix chapters and missing descriptions first (low risk). Don't rewrite titles of
  videos that are performing well. Apply changes through `workflows/publish.md`.

## AI search visibility (GEO)

AI assistants and Google's AI answers increasingly cite YouTube videos. Help
them: a description that answers the core question plainly, chapters named as
questions/steps, accurate captions, consistent entity names, and a clear
transcript (state the key answer early and clearly in the video itself).
