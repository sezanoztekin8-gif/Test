# Video breakdown: why did this video get its views?

Input: any public video URL. Output: an evidence-based explanation plus a
reusable formula the creator can apply. References:
`references/outlier-method.md`, `references/retention-and-hooks.md`,
`references/packaging.md`.

## 1. Pull the evidence pack

`yt_competitors.py video <url> --lang <video language> [--hook 45] [--comments 100]`

It returns and saves: stats and rates; performance against the channel's own
baseline (outlier and neighbour ratio, rank, views vs subscribers); packaging
(title features, thumbnail URL, tags, description, chapters); timing (weekday,
hour, gap since the previous upload); the hook and ending transcript; a path to
the full timed transcript; and comment themes (top liked, requests, questions,
criticism, timestamps people mention).

Look at the thumbnail (open the URL with an image-capable tool if available) and
read the full transcript file when you need structure, not just the hook.

## 2. Was it actually a hit?

- `neighbour_ratio` >= 2 -> outlier for that channel. 1-2 -> normal.
  Below 0.5 -> underperformed.
- Views vs subscribers above 100% -> it reached far beyond the existing audience
  (browse/suggested pickup or search demand).
- Young videos (under ~7 days) aren't settled; say so.

## 3. Explain the views (use the evidence; rank the likely causes)

Check each factor and note the evidence for or against:

1. **Topic demand** - Is the subject searched or trending? (`yt_trends.py suggest "<topic>"`,
   `yt_trends.py search "<topic>" --days 365`). Do several channels have hits on it?
2. **Packaging** - What does the title promise? Which formula does it follow
   (`references/packaging.md`)? Is it different from the channel's usual titles?
   Thumbnail: subject, emotion, text, contrast, curiosity. Do title and thumbnail
   add to each other instead of repeating?
3. **Hook** - Quote the first 15-30 seconds. Does it confirm the promise fast,
   raise stakes, open a loop? Tag the beats (`references/retention-and-hooks.md`).
4. **Structure and pacing** - Map beats across the transcript: re-hooks,
   payoffs, where the main promise is paid off, words per minute vs the channel norm.
5. **Format and length** - Is the format new for the channel? Length vs the
   channel's best length bucket.
6. **Timing** - Publish day/hour, news or seasonal moment, gap since last upload.
7. **Audience reaction** - Comment themes: emotion, debate, "part 2" requests,
   timestamps quoted (moments that landed), criticism.
8. **External boost** - Collaborations, a famous guest, news coverage or links in
   the description that could explain a spike rather than the formula.

Write a ranked "why it worked" list. For each cause: the evidence and how
confident you are. Separate "can be reused" from "one-off luck/fame/access".

## 4. Extract the reusable formula

- **Title formula** with slots, e.g. `Why [Familiar Thing] Is Secretly [Surprising Fact]`.
- **Thumbnail formula** as parts: `[subject, emotion, position] + [object] + [2-3 word text]`.
- **Hook formula** as an order of beats, e.g. `bold claim -> proof teaser -> stakes -> promise`.
- **Structure** as a timed beat sheet: Hook 0:00 -> Promise 0:20 -> ... -> Payoff -> CTA.
- **Length and pacing** targets.

## 5. Apply it to the user's channel

Give 3 original video ideas that use the formula for the user's niche and
audience (read `channel-profile.md`), each with a title, thumbnail concept and
hook draft. Offer to continue with `workflows/script.md`.

Fill `templates/video-breakdown.md`. For several videos, keep each breakdown to
the essentials and add a "patterns across these videos" section; a pattern
needs at least two videos.

## Rules

- Quote hooks word for word (they are the finding), but never paste the whole transcript.
- Don't state the cause as fact. The data shows what the video did, not why each
  viewer clicked.
- Auto-generated captions misspell names and numbers; verify against the title
  and description before quoting a figure.
