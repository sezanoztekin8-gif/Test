# Outlier method

Used by `yt_competitors.py`. The aim is to find videos that did much better
than their channel normally does, because that isolates what the audience
wanted (topic, format, packaging) from how big the channel is.

## Metrics

| Metric | Formula | Use |
|---|---|---|
| `outlier_ratio` | views / median views of the channel's sampled uploads of the same format (mature videos, >= 3 days) | simple "how unusual" |
| `neighbour_ratio` | views / median views of the ~10 same-format uploads published closest in time | corrects for channel growth and video age; **primary signal** |
| `is_outlier` | `neighbour_ratio >= threshold` (default 2.0), age >= 3 days, at least 3 same-format videos | flag |
| `is_underperformer` | `neighbour_ratio <= 0.5` | what the audience rejected |
| `views_per_day` | views / max(age in days, 1) | momentum; compare only similar ages |
| `views_per_sub` | views / channel subscribers | cross-channel reach (search results, discovery) |
| `engagement_rate` | (likes + comments) / views x 100 | reaction intensity; compare within a niche |
| `pct_of_typical` (watchlist) | views so far / median lifetime views of mature uploads | early breakout detection |

Shorts, long-form and live are scored separately. Shorts views are counted
differently and are usually far higher, so mixing them hides everything.

## Reading results

- 2-3x = clear win; 5x+ = breakout; 10x+ = usually something extra (trend,
  external push, collaboration, a very broad topic).
- A pattern needs several outliers (ideally across channels). One outlier is a hint.
- Compare outliers with underperformers from the same period: features that
  both share are not why the winners won.
- Turning points: if a channel's median jumps and stays higher after a change
  (new format, title style, length, thumbnail style), that change is a strong lead.
- Old videos keep accumulating views (search, suggested); neighbour comparison
  handles most of that, but very new videos (under ~7 days) are not settled.

## Limits

- Public views only. A high-view video might still have had poor retention, and
  low views might be a deliberate niche video. Say "suggests", not "proves".
- Views can be inflated by ads (promoted videos) or external embeds.
- Subscriber counts are rounded; hidden counts break views_per_sub.
- Sample = the latest N uploads (default 100). Old hits outside the sample are missed;
  increase `--max` for a historical view.
- Deleted/private videos disappear from the baseline.
