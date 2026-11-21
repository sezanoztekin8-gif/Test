# Analytics metrics

## Definitions (Analytics API names)

| Metric | Meaning |
|---|---|
| `views` | views counted in the window |
| `estimatedMinutesWatched` | total watch time in minutes (watch hours = /60) |
| `averageViewDuration` | seconds watched per view |
| `averageViewPercentage` | share of the video watched per view (%) |
| `subscribersGained/Lost` | from the channel or from a video (with video filter) |
| `likes`, `comments`, `shares` | engagement counts |
| `audienceWatchRatio` | retention curve: share of viewers still watching at each point |
| `relativeRetentionPerformance` | 0-1, compares with videos of similar length on YouTube (>0.5 better) |
| `viewerPercentage` | demographic share (age/gender) of logged-in viewers |
| `estimatedRevenue` | net revenue to the creator (all sources) |
| `playbackBasedCpm` | gross revenue per 1,000 monetized playbacks |
| Reporting API `video_thumbnail_impressions` | times a thumbnail was shown on YouTube |
| Reporting API `video_thumbnail_impressions_ctr` | share of impressions that became views |

Dimensions used: `day`, `video`, `insightTrafficSourceType` (+ `insightTrafficSourceDetail`
for search terms, external sites, suggesting videos), `ageGroup`, `gender`,
`country`, `province`, `deviceType`, `operatingSystem`,
`insightPlaybackLocationType`, `subscribedStatus`, `creatorContentType`,
`sharingService`, `elapsedVideoTimeRatio`.

## The funnel

```
impressions -> (CTR) -> views -> (retention) -> watch time -> (satisfaction) -> more impressions
                                         \-> subscribers, comments, shares
```

Find the weakest step compared with the channel's own history, not with other channels.

## Diagnosis tree

1. Views down? -> which traffic source fell (`traffic` both periods).
2. That source's impressions down? -> topic interest, fewer uploads, or weaker
   satisfaction on recent uploads.
3. Impressions steady but CTR down? -> packaging (title/thumbnail) or a less
   interested audience being reached.
4. CTR fine but watch time down? -> retention: first 30 seconds, pacing, length.
5. Subscribers flat while views rise? -> one-off viewers (Shorts, broad topics);
   add series, end screens, clearer channel promise.

## Rough context (use sparingly, always labelled as rough)

YouTube Studio has said most channels' impressions CTR falls between roughly
2% and 10%. CTR varies hugely by traffic source (search and subscriber traffic
click more than browse), by video age and by niche. Average view percentage
depends heavily on length. Prefer "compared with your last 10 videos".
