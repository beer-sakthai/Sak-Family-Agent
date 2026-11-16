# HF Trending API Structure

> Verified 2026-07-30 via live API calls. Covers the `scope=daily`/`scope=weekly` endpoints.
> Referenced from SKILL.md → Platform API Quirks → Hugging Face Hub API table.

## Endpoints

| Endpoint | Limit | Structure | Notes |
|----------|-------|-----------|-------|
| `GET /api/trending?type=model&limit=N` | ≤20 | Flat fields | `N>20` returns error. |
| `GET /api/trending?scope=daily` | 30 | **Nested `repoData`** | Mix of model/dataset/space. Daily window counts. |
| `GET /api/trending?scope=weekly` | 30 | Same nested structure | Weekly window. Same 30-item limit. |

## Response Shape (scope=daily / scope=weekly)

```json
{
  "recentlyTrending": [
    {
      "repoData": {
        "_id": "6425a114812813f8f4a9b02c",
        "author": "moonshotai",
        "authorData": { "followerCount": 15517, "type": "org" },
        "downloads": 387822,
        "likes": 8847,
        "name": "Kimi-K3"
      },
      "repoType": "model"
    }
  ]
}
```

## Access Patterns

| What you want | Code | Pitfall |
|---------------|------|---------|
| Downloads | `item['repoData']['downloads']` | ❌ `item['downloads']` returns `None` |
| Like count | `item['repoData']['likes']` | Same nesting rule |
| Type | `item['repoType']` | Returns `model`/`dataset`/`space` |
| Identity | `item['repoData']['author']+'/'+item['repoData']['_id']` | ❌ `name` is often `null` |

## Verified Quirks (live-tested 2026-07-30)

1. **`name` field is frequently `null`** in `scope=daily` results — many entries have no name despite being identifiable from `_id`. The `limit` endpoint (flat fields) does not have this issue.
2. **Download counts differ between endpoints** — `scope=daily` returns daily-window counts, while the `limit` endpoint returns lifetime totals (verified: same model, same day, different numbers).
3. **Auth not required** — both return public data without token. No rate limit observed during testing.
