# Packaging: titles and thumbnails

The title and thumbnail decide whether anyone sees the video. Design them
before (or alongside) the script. Reference: `references/packaging.md`.

## 1. Learn the niche's packaging

- `yt_competitors.py scan @competitor` -> `title_patterns`, `frequent_title_phrases`,
  and the outliers' titles and thumbnail URLs.
- `yt_trends.py search "<topic>" --days 365` -> titles and thumbnails of the top
  results for the topic. Look at the thumbnails (open the URLs if you can view
  images); note what the feed will look like next to the user's thumbnail.

## 2. Titles

Write 8-10 options across different formulas (curiosity gap, specific result,
story, question, list, contrast, warning, "why/how"), then shortlist 3. For each:
- Front-load the words that matter (mobile truncates around 60-70 characters,
  though up to 100 are allowed).
- Plain words the audience uses (from comments and autocomplete).
- Honest: the video must pay it off in the first minute or two.
- In the channel's language; for search-led topics include the search phrase naturally.
- Run `yt_seo.py lint --title "..." --keyword "..."` on the shortlist.

## 3. Thumbnails

For the top title, write 3 thumbnail concepts that **add** to the title instead
of repeating it. Each concept:
- One focal subject (face with clear emotion, character, object, scene), large
  and readable at phone size.
- 0-4 words of text, only if it adds something the title doesn't say.
- High contrast; a background that stands out from competitors' thumbnails in
  the same feed.
- A visible question or tension (before/after, unexpected detail, scale, danger).
- Fit with the channel's visual identity.

Describe each as a production brief (layout, subject, expression, colours,
text, font weight) detailed enough for a designer or an image generator. If an
image-generation tool is installed (`references/optional-integrations.md`),
offer to generate drafts at 16:9 (1280x720).

## 4. Test plan

YouTube Studio's "Test & compare" can A/B test up to 3 thumbnails (and titles,
where available) on long-form videos. Suggest testing two concepts that differ
in one big idea, not small tweaks. For older videos, see `workflows/publish.md`
(change one thing, wait 7-14 days, compare with the video's own baseline).

## Output

`templates/upload-package.md` packaging section: 3 titles ranked with reasoning,
3 thumbnail briefs, what to test.
