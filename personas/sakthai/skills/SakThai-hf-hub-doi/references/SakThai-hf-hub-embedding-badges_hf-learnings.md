# HF Learnings: Hugging Face Hub Embedding, Badges & oEmbed API

## 2026-07-25: hf-hub-embedding-badges-oembed-deep-dive

### Summary
Comprehensive deep dive into embedding Hugging Face Hub content (Spaces, datasets, models) in external websites, using shields.io badges, Open Graph social cards, and the Hub's embed/iframe infrastructure. Covers Spaces embedding (direct URL, iframe, Gradio WebComponents), dataset viewer embedding, shields.io badge patterns, OG social cards, the oEmbed API, SQL console embeds, and protected Space embedding.

### Key Embedding Patterns

**Spaces — Iframe (all types):**
```html
<iframe src="https://{namespace}-{space-name}.hf.space" frameborder="0" width="850" height="450"></iframe>
```

**Spaces — Gradio WebComponents (Gradio only):**
```html
<script src="https://gradio.s3-us-west-2.amazonaws.com/{version}/gradio.js"></script>
<gradio-app src="https://{namespace}-{space-name}.hf.space"></gradio-app>
```

**Dataset Viewer Embed:**
```
https://huggingface.co/datasets/{namespace}/{dataset-name}/embed/viewer
```
Params: `config`, `split`, `filter`, `search`, `row`

**Shields.io Static Badges with HF Logo:**
```md
![HuggingFace](https://img.shields.io/badge/HuggingFace-{name}-FFD21E?logo=huggingface)
![Model](https://img.shields.io/static/v1?label=Model&message={name}&color=blue&logo=huggingface)
```

**Shields.io Dynamic Badges (from HF API):**
```md
![Downloads](https://img.shields.io/badge/dynamic/json?url=https://huggingface.co/api/models/{model}&query=downloads&label=Downloads)
```

**Open Graph Social Cards (auto-generated):**
```
https://cdn-thumbnails.huggingface.co/social-thumbnails/{type}/{namespace}/{repo}.png
```

**oEmbed API (auth required):**
```
GET /api/oembed?url=https://huggingface.co/{type}/{namespace}/{repo}
Authorization: Bearer {token}
```

**SQL Console Embeds (API-managed):**
```
POST/PATCH/DELETE /api/{repoType}/{namespace}/{repo}/sql-console/embed/{id}
```

### Key Limitations
- Model inference widgets are NOT iframe-embeddable — only render on model page
- No dedicated shields.io HuggingFace badge service exists
- oEmbed API requires authentication (not public)
- Protected Spaces keep source private but allow public embedding

### Resources
- [Spaces Embed Docs](https://huggingface.co/docs/hub/en/spaces-embed)
- [Dataset Viewer Embed Docs](https://huggingface.co/docs/hub/en/datasets-viewer)
- [Shields.io Badges](https://shields.io/badges)
- [HF OpenAPI Spec](https://huggingface.co/.well-known/openapi.json)

### Skill Created
`hf-hub-embedding-badges/` — complete reference with all embedding patterns, badge APIs, and use cases.

---
