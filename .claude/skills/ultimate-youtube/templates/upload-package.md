# Upload package: [working title]

## Packaging
**Titles (ranked)**
1. [title] - [why]
2. [title]
3. [title]

**Thumbnail briefs**
- A: [layout, subject + emotion, text, colours, background]
- B: [...]
- Test: [A vs B in Test & compare]

## Metadata (copy-paste)

**Title**
```
[title]
```

**Description**
```
[1-2 sentence summary with the main phrase]

[2-4 short paragraphs]

Chapters
0:00 [..]
[..]

[Related videos / playlist / sources / links]

#[hashtag] #[hashtag]
```

**Tags**
```
[tag, tag, tag]
```

## Settings
| Field | Value |
|---|---|
| Category | [id - name] |
| Visibility | private / unlisted / public / scheduled [ISO time + tz] |
| Made for kids | yes / no (creator's declaration) |
| Altered/synthetic content | yes / no |
| Title/description language | [code] |
| Audio language | [code] |
| Playlist | [name/id] |
| Captions | [file, language] |
| Translations | [languages] |
| End screen / cards | [video links] |
| Pinned comment | [text] |

## Lint
`yt_seo.py lint` score: [..] · errors: [..] · notes: [..]

## Publish command (dry run first)
```
python SKILL_DIR/scripts/yt_publish.py upload [file] --metadata [meta.json] --thumbnail [img] --playlist [id]
```
