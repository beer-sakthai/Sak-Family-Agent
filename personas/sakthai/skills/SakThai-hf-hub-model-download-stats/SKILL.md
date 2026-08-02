---
name: SakThai-hf-hub-model-download-stats
author: SakThai
license: MIT
description: >-
  Complete reference for Hugging Face Hub model download counting methodology —
  query files system per library, countDownloads ElasticSearch query DSL,
  diffusers edge case, GGUF handling, Publisher Analytics CSV export, and
  granular access logs for Enterprise Plus.
version: 1.0.0
metadata:
  hermes:
    tags: [huggingface, hf, hub, models, downloads, stats, analytics, publisher-analytics, elasticsearch]
    category: mlops
category: mlops
---

# HF Hub Model Download Stats: Counting Methodology & Analytics

## What It Is

The HF Hub tracks model downloads server-side by monitoring HTTP GET/HEAD requests to specific **query files**. Every request counted = 1 download. No client-side instrumentation, no extra network calls — counting happens entirely server-side as the Hub serves files.

## Key Concepts

| Concept | Detail |
|---------|--------|
| **Query files** | Per-library set of file paths that trigger download counting |
| **Server-side** | No user info sent; counting is done as files are served |
| **GET & HEAD** | Both HTTP methods count as a download |
| **Default fallback** | `config.json` (single file) when no library is identified |
| **Default set** | `config.json`, `config.yaml`, `hyperparams.yaml`, `params.json`, `meta.yaml` |
| **Per-library override** | Libraries define `countDownloads` field in `model-libraries.ts` |
| **ElasticSearch DSL** | Queries use ElasticSearch query-string syntax |

## Per-Library countDownloads Patterns

The configuration lives at `huggingface.js/packages/tasks/src/model-libraries.ts` and uses ElasticSearch query-string syntax on available fields:

| Field | Description | Example |
|-------|-------------|---------|
| `path` | Complete relative file path | `path:"config.json"` |
| `path_prefix` | Directory prefix | `path_prefix:"checkpoints/"` |
| `path_extension` | File extension only | `path_extension:"safetensors"` |
| `path_filename` | Filename without extension | `path_filename:"model"` |

### Common Patterns

| Pattern | Example Libraries | Query |
|---------|------------------|-------|
| Single config file | Adapters, Bagel, BM25S | `path:"adapter_config.json"` |
| Extension-based | AnemoI, CCPFN, clipscope | `path_extension:"ckpt"` OR `path_extension:"pt"` |
| Specific model file | ChatTTS, Champ, BoltzGen | `path:"asset/GPT.pt"` |
| Combined OR | BioNeMo, Clara | `path_extension:"ckpt" OR path:"config.json"` |
| All GGUF files | Built-in, not per-library | All `.gguf` files counted by default |
| Safetensors | CheXmix | `path_extension:"safetensors"` |
| Onnx at any depth | CollectorVision | `path_extension:"onnx"` |
| Config at root | most libraries | `path:"config.json"` |

### Diffusers Edge Case

Most complex counting because users download via both Python library and UIs:

```json
{
  "bool": {
    "should": [
      { "term": { "path": "model_index.json" } },
      { "regexp": { "path": "[^/]*\\.safetensors" } },
      { "regexp": { "path": "[^/]*\\.ckpt" } },
      { "regexp": { "path": "[^/]*\\.bin" } }
    ],
    "minimum_should_match": 1
  }
}
```

Nested files are excluded via regex to prevent double-counting when a user downloads via `diffusers.from_pretrained()` (counts `model_index.json`) and also grabs a top-level `.safetensors` file.

## How to Add Custom Query Files for Your Library

1. Open a PR at `huggingface.js/packages/tasks/src/model-libraries.ts`
2. Add a `countDownloads` field to your library's entry in `MODEL_LIBRARIES_UI_ELEMENTS`
3. Use ElasticSearch query-string syntax with fields: `path`, `path_prefix`, `path_extension`, `path_filename`
4. Reference: [example PR for VFIMamba](https://github.com/huggingface/huggingface.js/pull/885/files)
5. Follow the [integration guide](https://huggingface.co/docs/hub/models-adding-libraries#register-your-library)

## Publisher Analytics (Team & Enterprise)

For organizations needing more granular data:

| Feature | Free | Team | Enterprise | Enterprise Plus |
|---------|------|------|------------|-----------------|
| Total downloads | ✓ | ✓ | ✓ | ✓ |
| Per-repo breakdown | — | ✓ | ✓ | ✓ |
| CSV export (API) | — | ✓ | ✓ | ✓ |
| Granular access logs | — | — | — | ✓ (add-on) |

### CSV Export API

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://huggingface.co/organizations/YOUR_ORG/settings/publisher-analytics/download-breakdown" \
  --output breakdown.csv
```

**CSV columns:** `repoType`, `repoName`, `total`, `timestamp`, `downloads`

### Granular Access Logs (Enterprise Plus)

Request-level logs with these columns:

| Column | Description |
|--------|-------------|
| `timestamp` | Request timestamp |
| `status` | HTTP status (200, 206, 302, 307, 304) |
| `method` | HTTP method (GET, HEAD) |
| `repoName` | Full repo name |
| `repoType` | model / dataset / space |
| `hashedUserId` | Non-reversible hash of authenticated user |
| `hashedIp` | Non-reversible hash of IP (unauthenticated) |
| `country` | Country ISO code |
| `region` | Region or city name |
| `userAgent` | HTTP User-Agent header |

These are exported as raw logs — your team processes them for custom analytics.

## GGUF Handling

All `.gguf` files in a repo are counted as downloads by default. This may double-count when a user clones the entire repo, but most use-cases download a single GGUF file.

## Related Skills

- hf-hub-egress-metrics
- hf-hub-rate-limits
- hf-hub-api-rate-limiting
- hf-hub-storage-limits-and-plans
