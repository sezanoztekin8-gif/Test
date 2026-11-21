# Publish and manage videos

Script: `yt_publish.py` (write token). Read the safety model in its `--help`
once per session. The pattern for every change is the same:

```
1. dry run      ->  yt_publish.py <command> ... (no --confirm)
2. show preview ->  tell the user exactly what will change, on which channel
3. approval     ->  the user says yes to THIS preview
4. write        ->  same command + --confirm
5. report       ->  what changed, the backup path, how to undo
```

Before the first write of a session: `yt_auth.py whoami --write` and name the
channel. If the user changes their mind later, `revert` the update.

## Upload

1. Collect metadata. If the user hasn't written it, run `workflows/seo.md` to
   produce an upload package, then lint it: `yt_seo.py lint --title ... --description @desc.txt --tags ...`.
2. Required decisions (ask if unknown):
   - Audience: `--made-for-kids` or `--not-made-for-kids` (legal declaration;
     never guess - ask).
   - Visibility: default `private`. To schedule: `--publish-at 2026-12-01T14:30:00+05:30`
     (stays private until then, YouTube publishes it automatically).
   - Altered or synthetic content: `--synthetic-media yes` when realistic-looking
     people, places or events were generated or meaningfully altered (YouTube
     requires disclosure). Not needed for clearly unrealistic animation,
     beauty filters, or AI used only for scripts/captions. If unsure, ask.
   - Language: `--language` (title/description language) and
     `--audio-language` (spoken language).
   - Category: `yt_publish.py categories --region XX` lists IDs.
3. Save long metadata in a JSON file and pass `--metadata meta.json`:
   ```json
   {"title": "...", "description": "...", "tags": ["..."], "categoryId": "27",
    "privacyStatus": "private", "publishAt": "2026-12-01T14:30:00Z",
    "defaultLanguage": "en", "defaultAudioLanguage": "en",
    "selfDeclaredMadeForKids": false, "containsSyntheticMedia": false}
   ```
4. Dry run: `yt_publish.py upload video.mp4 --metadata meta.json --thumbnail thumb.jpg --playlist PL... --captions subs.srt --captions-lang en`
5. After approval add `--confirm`. Large files upload in resumable chunks with
   retries; progress prints to stderr.
6. Then `yt_publish.py status VIDEO_ID` until `uploadStatus` is `processed`.
   Report `rejectionReason` or `failureReason` if present.
7. Remind the user about unaudited-project uploads being private-only
   (`workflows/setup.md`) if they planned a public upload.

`--no-notify` skips subscriber notifications (useful for re-uploads/backfills).

## Edit metadata

`yt_publish.py update VIDEO --title "..." [--description @d.txt] [--tags ...] [--privacy ...] [--publish-at ...]`

- The preview is a field-by-field diff. If it shows a **warning** that the video
  is one of the channel's top performers, relay it and recommend against
  changing the title unless the user insists.
- Retitle candidates are packaging problems, not content problems: good
  retention (average view percentage at or above the channel's norm) but weak
  views or impressions CTR. Check with `yt_analytics.py video VIDEO` and
  `yt_reporting.py ctr` before proposing a change.
- Change one thing at a time (title OR thumbnail) and wait 7-14 days to judge,
  comparing with the video's own previous 7-14 days.
- Undo: `yt_publish.py revert VIDEO` (dry run) then `--confirm`. List backups
  with `yt_publish.py backups VIDEO`.

## Thumbnail

`yt_publish.py thumbnail VIDEO image.jpg` -> preview -> `--confirm`.
JPG/PNG under 2 MB, 1280x720 recommended. Needs a phone-verified channel.
Thumbnails are not backed up by the API; keep the old file if the user may want it back.

## Translated titles and descriptions

`yt_publish.py localize VIDEO --lang hi --title "..." --description @hi.txt`.
Viewers whose YouTube language is `hi` then see that title. The video needs a
default language (`--default-language en` the first time). Write the
translation yourself only if the user asked; otherwise ask for it or offer a
draft for them to check. Good for multi-language audiences (`references/multilingual.md`).

## Captions

- `yt_publish.py captions list VIDEO`
- `yt_publish.py captions upload VIDEO --file subs.srt --lang en [--name "English"] [--draft]` (400 units)
- `yt_publish.py captions delete CAPTION_ID`

## Playlists

- `yt_publish.py playlist list`
- `yt_publish.py playlist create --title "..." --description "..." --privacy public`
- `yt_publish.py playlist add --playlist PL... --video VIDEO [--position 0]`
- `yt_publish.py playlist remove --playlist PL... --video VIDEO`
- `yt_publish.py playlist delete --playlist PL...` (videos are kept)

Series playlists in viewing order raise session watch time; suggest one per
recurring format or story arc.

## Delete

Prefer `update VIDEO --privacy private` (reversible, keeps views and comments).
If the user still wants deletion: dry run `yt_publish.py delete VIDEO`, show
title and views, state that it is permanent, and only then `--confirm`. Metadata
is backed up first, but the video, its views and comments are gone.

## Your uploads

`yt_publish.py mine --max 50` lists your videos including private and scheduled
ones with their status. `yt_publish.py get VIDEO` shows full current metadata.

## Errors

| Error | Meaning | Fix |
|---|---|---|
| `forbidden` / `insufficientPermissions` | token is for another channel or lacks write scope | `whoami --write`; `login --write` |
| `uploadLimitExceeded` | channel hit YouTube's daily upload limit | try tomorrow |
| local quota message | today's budget is used up | wait for midnight Pacific |
| `invalid_grant` | testing-mode token expired (7 days) | `login --write` again |
