# candidates.json schema

Input of `scripts/rank.py`. Written by the collection stage, read by the ranking script.

```
py -3.12 scripts/rank.py <candidates.json> --config config/ranking.json --out-json <ranked.json> --out-md <top5.md>
```

Exit codes: `0` success (also when fewer than `top_n` videos survive), `2` input or config file unreadable or malformed.

## File

| Field | Type | Notes |
|-------|------|-------|
| `topic` | string | Search topic. |
| `generated_at` | string, ISO-8601 | Reference "now" for the `period_days` filter (not the wall clock). |
| `candidates` | array | Candidate records, see below. |

## Candidate record

Any metric may be `null` (unknown). `null` is not the same as `0`: a `null` metric is left out of the engagement formula and listed in `missing_metrics`; `0` is a real value.

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Platform video id. `(platform, id)` is the de-duplication key. |
| `platform` | `instagram` / `tiktok` / `youtube` | Percentile ranks are computed per platform. |
| `url` | string | Link to the video. |
| `author` | string | Author handle; capped by `max_per_author`. |
| `caption` | string | Video caption (any Unicode). |
| `posted_at` | string, ISO-8601 | Publication time. Videos older than `period_days` are dropped. |
| `duration_sec` | number | Videos longer than `max_duration_sec` are dropped. |
| `views` | number | `null` or `0` drops the video (`no_views`); below `min_views` drops it (`min_views`). |
| `likes` | number | Engagement metric, weight 1. |
| `comments` | number | Engagement metric, weight 2. |
| `shares` | number | Engagement metric, weight 3. |
| `saves` | number | Engagement metric, weight 3. |
| `author_median_views` | number | Typical views of the author; used for virality when there is no `outlier_score`. |
| `outlier_score` | number | Source-provided outlier multiplier; highest-priority virality signal. |
| `source` | `vidiq` / `scrapecreators` | Where the record came from. |

When the same `(platform, id)` appears twice, the record with more non-null fields wins (first one on a tie).

## Example

```json
{
  "topic": "video editing tips",
  "generated_at": "2026-11-15T12:00:00+00:00",
  "candidates": [
    {
      "id": "tt1",
      "platform": "tiktok",
      "url": "https://tiktok.example/tt1",
      "author": "dan",
      "caption": "Test clip",
      "posted_at": "2026-11-13T12:00:00+00:00",
      "duration_sec": 18,
      "views": 1200000,
      "likes": 150000,
      "comments": 4000,
      "shares": 9000,
      "saves": 12000,
      "author_median_views": null,
      "outlier_score": 12.5,
      "source": "scrapecreators"
    }
  ]
}
```

## Output (`ranked.json`)

`{"topic", "generated_at", "top": [...], "reserve": [...], "dropped": [...]}`.

Each `top` / `reserve` record keeps all input fields and adds:

| Field | Meaning |
|-------|---------|
| `virality_raw` | `outlier_score`, else `views / author_median_views`, else `views / platform median views`. |
| `virality_basis` | `outlier`, `author` or `platform`: which of the three was used. |
| `engagement_raw` | `sum(weight * metric) / (views * sum(weights of present metrics))`. |
| `missing_metrics` | Engagement metrics that were `null`. |
| `virality_pct`, `engagement_pct` | Per-platform percentile rank in `(0, 1]`. |
| `score` | `weights.virality * virality_pct + weights.engagement * engagement_pct`. |

Each `dropped` record keeps all input fields plus `reason`: `no_views`, `duration`, `period` or `min_views`.
