# HF Hub Dynamic Badge URL Reference

> Correct URL patterns for shields.io dynamic badges on Hugging Face Hub repos.
> Verified against `img.shields.io/badge/dynamic/json` with HF API responses.

## Why `dynamic/json` not `endpoint`

The `endpoint` badge format (`img.shields.io/endpoint?url=...`) requires the target URL to return JSON in shields.io's custom schema:
```json
{"schemaVersion": 1, "label": "Downloads", "message": "89", "color": "blue"}
```

The HF API returns its own JSON format — so `endpoint` badges pointing at HF API URLs will **always be broken**.
Use `dynamic/json` instead, which queries the JSON API with a `query=` JSONPath expression.

## Badge URL Chart

| Asset Type | HF API Endpoint | Query Field | Badge URL (URL-encoded) |
|---|---|---|---|
| **Model** | `https://huggingface.co/api/models/{author}/{repo}` | `downloads` | `https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fmodels%2F{author}%2F{repo}&label=Downloads&query=downloads&color=blue` |
| **Dataset** | `https://huggingface.co/api/datasets/{author}/{repo}` | `downloads` | `https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fdatasets%2F{author}%2F{repo}&label=Downloads&query=downloads&color=blue` |
| **Space** | `https://huggingface.co/api/spaces/{author}/{repo}` | `downloads` | `https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fspaces%2F{author}%2F{repo}&label=Downloads&query=downloads&color=blue` |

## Template (copy-paste)

```markdown
<!-- Models -->
![Downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fmodels%2FAUTHOR%2FREPO&label=Downloads&query=downloads&color=blue)

<!-- Datasets -->
![Downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fdatasets%2FAUTHOR%2FREPO&label=Downloads&query=downloads&color=blue)

<!-- Spaces -->
![Downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fspaces%2FAUTHOR%2FREPO&label=Downloads&query=downloads&color=blue)
```

## Real Example (from food-penguin-v1 dataset card update)

```html
<img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fdatasets%2FNanthasit%2Ffood-penguin-v1&label=Downloads&query=downloads&color=blue" alt="Downloads"/>
```

This displays the live download count from the HF API. When a user downloads the dataset, the badge auto-updates — no manual URL edits needed.

## Other common badges (static)

These don't need dynamic queries since they don't change:

```markdown
![License](https://img.shields.io/badge/License-MIT-yellow)
![Examples](https://img.shields.io/badge/examples-648-blue)
![Tools](https://img.shields.io/badge/tools-7-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Framework](https://img.shields.io/badge/🤗-Transformers-FF6F00)
```

## Verified Behavior

- **API response field name:** `downloads` (integer, top-level key in the HF API JSON response for models/datasets/spaces)
- **URL encoding:** The `://` and `&` characters in the target URL must be URL-encoded (use `https%3A%2F%2F` for `https://`, `%3F` for `?`, `%3D` for `=`, `%26` for `&`)
- **Caching:** shields.io caches badge responses. Changes to the download count may take a few minutes to reflect.
- **Rate limits:** shields.io has rate limits. For repos with very high traffic, consider a custom badge server or static badges.
