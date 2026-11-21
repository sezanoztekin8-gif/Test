# YouTube API cheat sheet

Official docs: Data API v3 https://developers.google.com/youtube/v3 ·
Analytics API https://developers.google.com/youtube/analytics ·
Reporting API https://developers.google.com/youtube/reporting ·
Quota costs https://developers.google.com/youtube/v3/determine_quota_cost

## Which API answers what

| Need | API | Auth |
|---|---|---|
| Public data of any channel/video/playlist/comment | Data API v3 | API key or OAuth |
| Search | Data API v3 `search.list` | API key or OAuth |
| Upload, edit, delete, thumbnails, playlists, captions | Data API v3 | OAuth `youtube.force-ssl` |
| Your watch time, retention, traffic, demographics, revenue | Analytics API v2 | OAuth `yt-analytics.readonly` (+ `yt-analytics-monetary.readonly`) |
| Impressions + impressions CTR, bulk daily CSVs | Reporting API v1 | OAuth `yt-analytics.readonly` |
| Other channels' CTR, retention, revenue, impressions | none | not available to anyone |

## Quota (Data API v3)

Three daily buckets per Google Cloud project, reset at midnight Pacific:
- 10,000 units shared by most methods
- `search.list`: its own bucket, 100 calls/day by default
- `videos.insert`: its own bucket, 100 calls/day by default

| Method | Units | | Method | Units |
|---|---|---|---|---|
| videos/channels/playlists/playlistItems/commentThreads `.list` | 1 | | videos.update / delete | 50 |
| videoCategories / i18n `.list` | 1 | | thumbnails.set | 50 |
| captions.list | 50 | | playlists / playlistItems insert/update/delete | 50 |
| captions.download | 200 | | comments.insert | 50 |
| captions.insert | 400 | | captions.update | 450 |

Every request costs at least 1 unit, including failed ones. Analytics and
Reporting APIs have their own, much larger quotas. Google can change costs; if
the tracker and Google disagree, Google wins (raise limits in `config.json`).

**Cheap patterns**: a channel's uploads = playlist `UU` + channel ID without
`UC` (1 unit per 50 videos). Batch up to 50 IDs per `videos.list`/`channels.list`.
`channels.list(forHandle="@x")` resolves handles for 1 unit.

## Scopes used by this skill

| Token file | Scopes |
|---|---|
| `token_read.json` | `youtube.readonly`, `yt-analytics.readonly` (+ `yt-analytics-monetary.readonly` with `--revenue`) |
| `token_write.json` | `youtube.force-ssl` only |

## Hard limits

- Title <= 100 characters; description <= 5,000 bytes; no `<` or `>` in either.
- Tags <= 500 characters total (a tag with spaces counts its quotes).
- Thumbnail <= 2 MB, JPG/PNG/GIF/BMP; 1280x720 recommended; needs a verified channel.
- `publishAt` only works with `privacyStatus: private`.
- `videos.update` with `part=snippet` replaces the whole snippet: always send
  title, categoryId and every field you want to keep (the script does this).
  Same for `part=status`.
- Localizations require `snippet.defaultLanguage`.

## Gotchas

- Uploads from API projects that haven't passed Google's compliance audit are
  restricted to private.
- OAuth apps in "Testing" status: refresh tokens expire after 7 days.
- `search.list` results are a sample, not complete; total counts are estimates.
- The API has no Shorts flag. Heuristic: duration <= 180 s; exact check:
  `https://www.youtube.com/shorts/ID` returns 200 for Shorts and redirects otherwise
  (`--verify-shorts`).
- `statistics.dislikeCount` is private. `likeCount` and `commentCount` can be hidden.
- Subscriber counts are rounded to 3 significant figures for public reads.
- Analytics data lags 1-3 days; retention needs roughly 100+ views.
- `impressions` and `impressionClickThroughRate` are not Analytics API metrics;
  use Reporting API `channel_reach_basic_a1` (`video_thumbnail_impressions`,
  `video_thumbnail_impressions_ctr`) or `channel_reach_combined_a1` (adds traffic
  source and device dimensions). The first files arrive ~24-48h after creating the job.
- Brand Accounts: sign in and choose the brand channel in the account picker.
