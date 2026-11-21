# SEO and AI-search visibility (GEO)

## What YouTube reads

Title, description, captions/transcript (spoken words), chapters, tags (minor),
category, language settings, the thumbnail (text and objects can be detected),
and how viewers respond to the video for a query.

## Metadata checklist

- **Title**: main phrase early when search-led; natural wording.
- **Description**: the first ~150 characters show in search; lead with what the
  viewer gets. Then a natural summary naming the key entities. Avoid keyword lists
  (spam policy).
- **Chapters**: first `0:00`, >= 3 chapters, each >= 10 seconds, ascending.
  Name them as the viewer would search ("How to...", "Why...").
- **Hashtags**: 2-3 relevant ones. The first three appear above the title.
  More than 15 -> all ignored. Misleading hashtags break policy.
- **Tags**: misspellings and variants; small effect.
- **Captions**: upload accurate ones; edit auto-captions for names and terms.
- **Language fields**: `defaultLanguage` (metadata) and `defaultAudioLanguage`
  (speech) - helps YouTube serve the right audience.
- **Localizations**: translated titles/descriptions for viewers using other
  interface languages (`yt_publish.py localize`).
- **Playlists**: descriptive titles and descriptions; they rank in search too.
- **Pinned comment**: a summary/question to start discussion.

## Search intent

Match the video to the intent: "how to" (step-by-step, chapters), "what is/why"
(clear answer early, then depth), "best/vs" (comparison structure), entertainment/
story queries (curiosity packaging). Look at what currently ranks
(`yt_trends.py search`) to see which intent YouTube serves for a phrase.

## Evergreen vs timely

Evergreen search topics keep bringing views for years; update descriptions and
pinned comments to keep them current. Timely topics need speed; publish while
interest rises.

## GEO: being cited by AI assistants and AI search

AI systems summarise and cite videos using transcripts, titles, descriptions
and chapters. To be quotable:
- Say the direct answer clearly in the video (it ends up in the transcript).
- Description: a plain-language summary that answers the core question in the
  first lines; define terms; name entities consistently.
- Chapters phrased as the questions they answer.
- Accurate captions in each language you serve.
- Cite sources in the description for factual content; consistency across your
  videos builds topical authority.
- Make the channel's topic clear (channel description, playlists, consistent pillars).
