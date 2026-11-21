# How YouTube surfaces videos (working model)

YouTube's public statements describe a recommendation system that tries to
match each viewer with the videos they are most likely to watch and be
satisfied with. It does not "push" or "punish" channels directly; it follows
viewer behaviour. Use this model to reason, not as hard numbers.

## Surfaces (traffic sources)

| Surface | Analytics name | What drives it |
|---|---|---|
| Home / Browse | `SUBSCRIBER`, Browse features | viewer's history; past satisfaction with similar videos; packaging (CTR) |
| Suggested (next to/after videos) | `RELATED_VIDEO` | what viewers of a video went on to watch and enjoy; topic and audience overlap |
| YouTube search | `YT_SEARCH` | relevance to the query (title, description, captions), engagement with the result, freshness for timely queries |
| Shorts feed | `SHORTS` | swipe-away vs watch/replay, engagement, viewer interests |
| External | `EXT_URL` | links from websites, apps, social posts, AI assistants |
| Notifications, playlists, channel page | various | existing audience and session flow |

## Signals that matter

- **Click-through on impressions** - does the packaging earn the click from the
  people it's shown to? Compare with the channel's own typical CTR for the same
  traffic source; CTR naturally falls as a video is shown to colder audiences.
- **Watch time and average view percentage** - do people keep watching?
- **Satisfaction** - surveys, likes, shares, "not interested", comments, returning
  to the channel. Clickbait that disappoints hurts later distribution.
- **Session continuation** - do viewers keep watching YouTube afterwards
  (series, playlists, end screens help).

## Practical consequences

- A new upload is first shown to likely-interested viewers (often subscribers and
  people who watched similar videos). Strong response -> wider tests -> more
  impressions. That's why the first days' CTR and retention matter, and why
  a video can also grow slowly for months via search or suggested.
- Videos compete for each viewer's attention in a specific feed. Packaging is
  judged relative to the alternatives next to it.
- Topic interest sets the ceiling: a perfectly made video on a topic few people
  care about stays small. Outliers usually combine a high-interest topic with
  strong packaging.
- Subscriber count is not a guarantee of views; recent performance is.
- Consistency builds an audience that expects and returns, but there is no
  documented penalty for pausing.
- Changing titles/thumbnails is allowed and sometimes helps; changing a winner
  can disrupt what's working.

## Myths to avoid repeating as fact

Shadow bans for normal channels, "the algorithm hates long videos", exact
"magic" CTR or retention thresholds, tags as a major ranking factor, posting at a
specific minute being decisive, deleting underperforming videos to "fix" a channel.
