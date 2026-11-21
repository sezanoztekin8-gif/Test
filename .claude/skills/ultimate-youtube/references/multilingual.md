# Serving several languages

Many creators reach audiences in more than one language. Choose a model per
channel; the skill supports all three.

## Models

| Model | How | Best when | Trade-offs |
|---|---|---|---|
| Separate channel per language | one channel per language | languages have large, distinct audiences; different cultural packaging | more work per upload; each channel grows from zero |
| One channel, multi-language audio tracks | upload extra audio tracks to one video (YouTube's multi-language audio, in Studio) | the same visuals work for all languages (animation, narration, faceless) | feature availability varies; titles need localizing too; one video's stats mix languages |
| One channel, one main language + translated metadata/captions | `localize` titles/descriptions, upload captions | one main audience plus secondary readers | spoken language still limits reach |

Multi-language audio tracks are added in YouTube Studio; the Data API doesn't
upload audio tracks. Translated titles/descriptions and captions are supported by
`yt_publish.py localize` and `yt_publish.py captions upload`.

## Research per language

- Run `yt_trends.py suggest/search` with `--lang` and `--region` for each language;
  demand and competition differ a lot between languages.
- `discover` competitors per language. A format that wins in one language and is
  missing in another is an opportunity.
- Transcripts: `--lang xx,en` picks the right caption track; `--translate en`
  machine-translates for analysis (verify important lines).
- Comments in Indic, Arabic, CJK and other scripts aren't covered by the English
  keyword categories. Read and classify them yourself.

## Packaging per language

- Write titles natively; don't translate English formulas word for word.
- Mixed-language titles (e.g. local language + English keyword) can match how
  people search; check autocomplete in that language.
- Thumbnail text in the audience's script; check fonts render correctly.
- Set `defaultLanguage` and `defaultAudioLanguage` correctly on every upload.

## Workflow for one video in several languages

Script in the primary language -> adapt (not literally translate) for each
language -> voice/record -> upload: separate videos per channel, or audio tracks
on one video -> localize titles/descriptions -> captions per language -> track
per-language performance (`yt_analytics.py geography`, per-channel analytics).
