---
name: SakThai-hf-datasets-server-is-valid-endpoint
description: "Complete reference for the Datasets Server /is-valid endpoint — checking dataset availability, viewer/preview/search/filter/statistics capabilities, gated dataset access, and integration patterns."
---

# HuggingFace Datasets Server — /is-valid Endpoint
**created:** 2026-07-25  
**type:** reference / deep-dive  
**depends_on:** hf-datasets-server-core-endpoints

## Purpose

Complete reference for the Datasets Server `/is-valid` endpoint — the pre-download validation gateway that checks whether a dataset is loadable, what capabilities (viewer, preview, search, filter, statistics) are available, and why a dataset might fail to load. Essential for building robust dataset pipelines that gracefully handle missing, gated, or broken datasets.

## Key Concepts

| Concept | Description |
|---------|-------------|
| **`/is-valid` endpoint** | `GET https://datasets-server.huggingface.co/is-valid?dataset=<repo>` |
| **Response fields** | `preview`, `viewer`, `search`, `filter`, `statistics` — each is `true`/`false` |
| **Config support** | Optional `&config=<name>` query param to check a specific subset |
| **Error response** | Returns `{"error": "..."}` for missing/private/gated datasets |
| **Auth required** | Public datasets don't need auth; gated datasets need `Authorization: Bearer <token>` |
| **Streaming detection** | `preview: true` + `viewer: false` means only first 100 rows are available (streaming) |

## Endpoint Behaviour

### Success — Fully supported dataset
```
GET /is-valid?dataset=HuggingFaceFW/fineweb
→ {
    "preview": true,
    "viewer": true,
    "search": true,
    "filter": true,
    "statistics": true
  }
```

### Success — Partial support (no search)
```
GET /is-valid?dataset=HuggingFaceFW/fineweb&config=default
→ {
    "preview": true,
    "viewer": true,
    "search": false,
    "filter": false,
    "statistics": false
  }
```
Config-specific endpoints may have reduced capabilities — always check per-config.

### Valid but streaming-only (preview only)
```
{
  "viewer": false,
  "preview": true,
  "search": true,
  "filter": true,
  "statistics": true
}
```
Means: full viewer is unavailable (too large), but first 100 rows are accessible.

### Invalid / non-existent
```
GET /is-valid?dataset=nonexistent123456789
→ {
    "error": "The dataset does not exist, or is not accessible without authentication (private or gated). Please check the spelling of the dataset name or retry with authentication."
  }
```

## Error Causes

| Condition | Error |
|-----------|-------|
| Dataset doesn't exist | `"dataset does not exist"` |
| Viewer disabled in dataset card | Returns all-`false` under the dataset name |
| Gated dataset, no token | Same "does not exist" error (hides existence) |
| Private dataset (non-PRO) | Same error (hides existence) |
| No data / unsupported format | All-`false` response |
| Renamed dataset | `"The dataset has been renamed. Please use the current dataset name."` |

## Integration Patterns

### Pre-flight check before loading
```python
import requests

def check_dataset(dataset_id: str, token: str | None = None) -> dict:
    """Check if a dataset is valid before attempting to load it."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(
        f"https://datasets-server.huggingface.co/is-valid?dataset={dataset_id}",
        headers=headers,
        timeout=10
    )
    return resp.json()

result = check_dataset("HuggingFaceFW/fineweb")
if "error" in result:
    print(f"Cannot load: {result['error']}")
elif result.get("viewer"):
    print("Full dataset viewer available")
elif result.get("preview"):
    print("Only preview (first 100 rows) available — dataset is streamed")
```

### Capability-aware routing
```python
capabilities = check_dataset("HuggingFaceFW/fineweb")
if capabilities.get("search"):
    # Use /search endpoint
    pass
if capabilities.get("filter"):
    # Use /filter endpoint
    pass
if capabilities.get("statistics"):
    # Use /statistics endpoint
    pass
```

## Sources

- Official docs: https://huggingface.co/docs/dataset-viewer/en/valid
- Raw markdown source: https://github.com/huggingface/dataset-viewer/blob/main/docs/source/valid.md
- Hub dataset viewer docs: https://huggingface.co/docs/dataset-viewer/en/
- Live API: `GET https://datasets-server.huggingface.co/is-valid`
- ReDoc UI: https://redocly.github.io/redoc/?url=https://datasets-server.huggingface.co/openapi.json
