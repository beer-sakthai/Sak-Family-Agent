---
name: SakThai-hf-hub-embedding-badges
description: "name: SakThai-hf-hub-embedding-badges"
---

# Hugging Face Hub Embedding, Badges & oEmbed API

## Overview
Complete reference for embedding Hugging Face Hub content in external websites — Spaces (iframe/WebComponents), dataset viewers (iframe), shields.io badges (static + dynamic), Open Graph social cards, the oEmbed API, and SQL console embeds via REST API.

## Embedding Spaces

### Direct URL
Each Space has a unique `https://{namespace}-{space-name}.hf.space` subdomain. Stable unless renamed.

### Iframe Embedding (all Space types)
```html
<iframe src="https://{namespace}-{space-name}.hf.space" frameborder="0" width="850" height="450"></iframe>
```

### Gradio WebComponents (Gradio Spaces only)
Faster than iframes, auto-resizing:
```html
<script type="module" src="https://gradio.s3-us-west-2.amazonaws.com/{version}/gradio.js"></script>
<gradio-app src="https://{namespace}-{space-name}.hf.space"></gradio-app>
```

### Requirements
- Space must be **public** or **protected** (protected keeps source private but allows embedding)
- Embed URL available from Space → Options menu → "Embed this Space"

## Embedding Dataset Viewer

### iframe URL Pattern
```
https://huggingface.co/datasets/{namespace}/{dataset-name}/embed/viewer
```

### Parameters
| Param | Description |
|--------|-------------|
| `config` | Dataset config/subset name |
| `split` | Dataset split (train, test, validation) |
| `filter` | Column filter expression |
| `search` | Full-text search term |
| `row` | Specific row index |

### Example
```html
<iframe src="https://huggingface.co/datasets/nyu-mll/glue/embed/viewer?config=mrpc&split=test" width="100%" height="500"></iframe>
```

## Shields.io Badges

### Static Badges with HF Logo (Recommended)
```md
![Model](https://img.shields.io/static/v1?label=Model&message=gpt2&color=blue&logo=huggingface)
![HF](https://img.shields.io/badge/HuggingFace-{name}-FFD21E?logo=huggingface)
```

### Dynamic Badges from HF API
```md
![Downloads](https://img.shields.io/badge/dynamic/json?url=https://huggingface.co/api/models/{model}&query=downloads&label=Downloads)
![Likes](https://img.shields.io/badge/dynamic/json?url=https://huggingface.co/api/models/{model}&query=likes&label=Likes)
```

### HF Brand Colors
| Color | Hex | Use |
|-------|-----|-----|
| HF Yellow | `#FFD21E` | Brand |
| HF Blue | `#007ec6` | Info |
| HF Green | `#21DE75` | Success |
| Dark | `#555` | Labels |

## Open Graph / Social Cards

Auto-generated at predictable URL pattern:
```
https://cdn-thumbnails.huggingface.co/social-thumbnails/{type}/{namespace}/{repo}.png
```
Where `type` = `models`, `datasets`, or `spaces`.

## oEmbed API

Requires authentication:
```
GET /api/oembed?url=https://huggingface.co/{type}/{namespace}/{repo}
Authorization: Bearer {token}
```
Returns structured embed metadata.

## SQL Console Embeds

REST API for embed management:
- `POST /api/{repoType}/{namespace}/{repo}/sql-console/embed` — Create
- `PATCH /api/{repoType}/{namespace}/{repo}/sql-console/embed/{id}` — Update
- `DELETE /api/{repoType}/{namespace}/{repo}/sql-console/embed/{id}` — Delete

## Protected Spaces

Special visibility mode:
- Source code stays private on Hub
- Space accessible publicly via `.hf.space` URL
- Embed URLs and custom domains continue working

## Limitations

- Model inference widgets are NOT embeddable via iframe — Svelte component only
- No dedicated shields.io HuggingFace badge service
- oEmbed API requires Bearer token auth
- OG card thumbnails are auto-generated, not customizable

## See Also
- [Spaces Embed Docs](https://huggingface.co/docs/hub/en/spaces-embed)
- [Dataset Viewer Docs](https://huggingface.co/docs/hub/en/datasets-viewer)
- [HF OpenAPI Spec](https://huggingface.co/.well-known/openapi.json)
- [Shields.io Badges](https://shields.io/badges)

---
**author**: SakThai
**license**: MIT
**updated**: 2026-07-25
**feature**: Embedding Hub content in external sites
