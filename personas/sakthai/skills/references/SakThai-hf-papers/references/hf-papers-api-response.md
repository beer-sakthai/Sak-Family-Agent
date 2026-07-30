# HF Papers API Response Structure

Observed response shapes from `https://huggingface.co/api/papers?limit=N`.

## Shape A — Flat list (most common as of Jul 2026)

```json
[
  {"id": "2607.19343", "title": "Masked Visual Actions for Unified World Modeling", "upvotes": 4},
  {"id": "2607.19191", "title": "ABot-World-0: Infinite Interactive World Rollout on a Single Desktop GPU", "upvotes": 199},
  ...
]
```

Top-level is a JSON array. No wrapping object.

## Shape B — Dict with `papers` key (less common, earlier API version)

```json
{
  "papers": [
    {"id": "2607.19191", "title": "...", "upvotes": 199},
    ...
  ]
}
```

## Shape C — Dict with `dailyPapers` key (rare, seen on error-recovery paths)

```json
{
  "dailyPapers": [
    {"id": "2607.19191", "title": "...", "upvotes": 199},
    ...
  ]
}
```

## Defensive extraction (handles all shapes)

```python
data = json.load(f)
papers = (
    data if isinstance(data, list)
    else data.get('papers', data.get('dailyPapers', []))
)
```

## Field mapping

| Field       | Type    | Notes                                        |
|-------------|---------|----------------------------------------------|
| `id`        | string  | arXiv ID (e.g. "2607.19343")                 |
| `title`     | string  | May be truncated — see Title Truncation note |
| `upvotes`   | int     | Community upvotes ("likes")                   |
| `published` | string  | ISO date, may be absent                      |

## Title truncation

The API sometimes omits leading tokens from paper titles. Example observed:

- **API title:** `"Generative World Renderer at the Speed of Play"`
- **Actual title:** `"AlayaRenderer-Flash: Generative World Renderer at the Speed of Play"`

**Mitigation:** Always cross-reference candidate papers by arXiv ID (the `id` field), not by title string. When comparing against the tracker, do a case-insensitive substring check: `tracker_title.lower() in api_title.lower() or api_title.lower() in tracker_title.lower()`.

## Pagination

The `limit` parameter is reliable up to 100. For trackers with 15+ entries, use `?limit=50` or `?limit=100` to ensure enough uncovered candidates appear. There is no cursor/page token — the API returns a single batch.
