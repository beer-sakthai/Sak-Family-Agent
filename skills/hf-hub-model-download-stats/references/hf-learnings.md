# HF Learnings — Model Download Stats Deep Dive

## 2026-07-25: hf-hub-model-download-stats-deep-dive — HF Hub Model Download Counting Methodology (Topic #349)

### Summary
Deep dive into the Hugging Face Hub's model download counting system — including the **query files** mechanism, per-library `countDownloads` configuration in the open-source `huggingface.js` library, ElasticSearch query DSL patterns, the diffusers edge case, GGUF handling, Publisher Analytics for organizations, and granular request-level logs for Enterprise Plus. This expands on the earlier July 23 overview with full source-level detail from `model-libraries.ts` (where 200+ libraries define their counting rules), the `ElasticSearchQuery` type, the CSV export API endpoint, and a practical guide for adding custom query files to any library.

### Architecture

The counting system is entirely **server-side**. When a user sends a GET or HEAD request to a file on the Hub, the request path is checked against the model library's query filter. If it matches, the download counter increments by 1.

```
User Request (GET/HEAD)
        │
        ▼
  Hub CDN / Server
        │
        ├── Match against library's countDownloads filter?
        ├── YES → increment download count (+1)
        └── NO  → serve file, no count
```

No client-side instrumentation. No JavaScript pixels. No extra network calls.

### Source Code

The query files configuration lives in the open-source `huggingface.js` monorepo:

- **Repository:** `github.com/huggingface/huggingface.js`
- **File:** `packages/tasks/src/model-libraries.ts`
- **Type:** `packages/tasks/src/model-libraries-downloads.ts`

The `ElasticSearchQuery` type is simply `string` — an ElasticSearch query-string query over these indexed fields:

| Field | Description | Example Value |
|-------|-------------|---------------|
| `path` | Complete file path relative to repo root | `"config.json"`, `"asset/GPT.pt"` |
| `path_prefix` | Directory prefix (empty if root-level) | `"checkpoints/"` |
| `path_extension` | File extension without dot | `"safetensors"`, `"ckpt"`, `"gguf"` |
| `path_filename` | Filename without extension | `"model"`, `"config"` |

### Per-Library Query Patterns (from Source)

The `MODEL_LIBRARIES_UI_ELEMENTS` object contains 200+ libraries. Here are the real patterns used:

**Pattern 1 — Single config file (most common):**
| Library | Query | Reason |
|---------|-------|--------|
| Adapters | `path:"adapter_config.json"` | `adapter_config.json` is the entry point |
| ACE-Step | `path:"ace_step_transformer/config.json"` | Nested config for library |
| Bagel | `path:"llm_config.json"` | LLM-specific config name |
| BM25S | `path:"params.index.json"` | Index file is the meaningful download |
| Aviation NER | `path:"gliner_config.json"` | GLiNER-based config |

**Pattern 2 — Extension-based wildcard:**
| Library | Query | Matches |
|---------|-------|---------|
| AnemoI | `path_extension:"ckpt"` | All `.ckpt` checkpoint files |
| CCPFN | `path_extension:"pt"` | All `.pt` PyTorch files |
| AudioSeal | `path_extension:"pth"` | All `.pth` files |
| clipscope | `path_extension:"pt"` | All `.pt` files |
| Birder | `path_extension:"pt"` | All `.pt` files |
| CheXmix | `path_extension:"safetensors"` | All `.safetensors` files |
| BBoxMaskPose | `path_extension:"pth"` | All `.pth` files |
| Big Vision | `path_extension:"npz"` | All `.npz` numpy files |
| CollectorVision | `path_extension:"onnx"` | All `.onnx` files |

**Pattern 3 — Specific model file (most precise):**
| Library | Query | Reason |
|---------|-------|--------|
| ChatTTS | `path:"asset/GPT.pt"` | Only the entry model file |
| Champ | `path:"champ/motion_module.pth"` | Specific subdirectory model |
| BoltzGen | `path:"boltzgen1_diverse.ckpt"` | Single checkpoint file |
| Cancer@HomeV2 | `path:"run.py"` | Entry script |
| Cloud Agents | `path:"setup.py"` | Setup script as entry point |
| ChaosSIM | `path:"ChaosSim.nb"` | Notebook as primary artifact |

**Pattern 4 — Combined OR (multiple file types):**
| Library | Query |
|---------|-------|
| BioNeMo | `path_extension:"ckpt" OR path:"config.json"` |
| Clara | `path_extension:"ckpt" OR path:"config.json"` |

**Pattern 5 — Libraries with NO countDownloads (use defaults):**
Most libraries omit `countDownloads`, falling back to the default query files: `config.json`, `config.yaml`, `hyperparams.yaml`, `params.json`, `meta.yaml`.

### ElasticSearch Query Details

The query uses ElasticSearch's [query-string query syntax](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html). The available fields are indexed specifically for download counting. The `bool` query with `should`/`minimum_should_match` is used inside the internal codebase for complex cases like diffusers.

### The Diffusers Edge Case (Deep Analysis)

The diffusers library has the most complex counting logic because:

1. **Library users** call `diffusers.from_pretrained()` which downloads `model_index.json` — this is the main entry point
2. **UI users** (Stable Diffusion WebUI, ComfyUI, Auto1111) download top-level `.safetensors`, `.ckpt`, or `.bin` files directly
3. **Nested files** (inside subdirectories like `unet/diffusion_pytorch_model.safetensors`) would double-count if included — they're excluded by the regex `[^/]*\\.safetensors` which only matches root-level files

The filter uses `minimum_should_match: 1` — a download is counted if it matches ANY of the four rules. This captures both library usage and UI downloads while avoiding double-counting of sharded files.

### GGUF Handling

GGUF files are treated as **self-contained** models not tied to any single library. The Hub counts ALL `.gguf` file downloads by default. This means:

- Cloning a repo with 5 GGUF files counts as 5 downloads (potential overcount)
- Most users download a single GGUF file for a given model
- No per-library override needed — GGUF is handled at the platform level

### Adding Custom Query Files

To add download counting for a new library:

1. **Edit** `huggingface.js/packages/tasks/src/model-libraries.ts`
2. **Add** a `countDownloads` field to your library's entry
3. **Use** ElasticSearch query-string syntax over `path`, `path_prefix`, `path_extension`, or `path_filename`
4. **Submit a PR** — [example for VFIMamba](https://github.com/huggingface/huggingface.js/pull/885/files)
5. **Also follow** the [integration guide](https://huggingface.co/docs/hub/models-adding-libraries#register-your-library) for full library registration

The PR for VFIMamba is a minimal reference: it adds a single entry with `countDownloads: \`path:"config.json"\`` to the library configuration.

### Publisher Analytics — CSV Export

Organizations on Team/Enterprise plans can download daily breakdowns:

**Endpoint:**
```
GET https://huggingface.co/organizations/{org}/settings/publisher-analytics/download-breakdown
Authorization: Bearer {token}
```

**Response (CSV):**
| Column | Type | Example |
|--------|------|---------|
| `repoType` | string | `"model"` or `"dataset"` |
| `repoName` | string | `"huggingface/CodeBERTa-small-v1"` |
| `total` | int | `4362460` |
| `timestamp` | ISO 8601 | `"2021-01-22T00:00:00.000Z"` |
| `downloads` | int | `4` |

Records are chronological per-repo. NOTE: Not deduplicated by user.

### Granular Access Logs (Enterprise Plus)

Request-level logs with anonymized user identification:

| Column | PII? | Description |
|--------|------|-------------|
| `timestamp` | No | Request timestamp |
| `status` | No | HTTP status (200, 206, 302, 307, 304) |
| `method` | No | GET or HEAD |
| `repoName` | No | Full repo name |
| `repoType` | No | model/dataset/space |
| `hashedUserId` | Non-reversible hash | Authenticated user ID |
| `hashedIp` | Non-reversible hash | IP of unauthenticated |
| `country` | No | Country ISO code |
| `region` | No | Region/city |
| `userAgent` | Semi | HTTP User-Agent |

These are exported as raw logs — the organization processes them post-download for custom analytics.

### Key Insights

1. **Counting is ElasticSearch-based** — not a simple increment. Each download check is an ES query against indexed file paths.
2. **Config files are the counting proxy** — for most libraries, the config file download is the signal that triggers the count, not the weight file itself.
3. **Extension-based counting is for UI-centric models** — libraries with heavy UI ecosystem (diffusers, checkpoint-based) use extension regex to capture direct downloads.
4. **GGUF is the exception** — counted unconditionally because the format is self-contained and library-agnostic.
5. **Publisher Analytics is the only path to granular data** — the main dashboard shows only total counts; CSV export and granular logs require Team/Enterprise plans.

### Sources
- https://huggingface.co/docs/hub/en/models-download-stats — official docs (source markdown from hub-docs repo)
- https://huggingface.co/docs/hub/en/publisher-analytics — Publisher Analytics
- https://huggingface.co/docs/hub/en/models-adding-libraries — integration guide
- https://github.com/huggingface/huggingface.js/blob/main/packages/tasks/src/model-libraries.ts — countDownloads per library (200+ entries)
- https://github.com/huggingface/huggingface.js/blob/main/packages/tasks/src/model-libraries-downloads.ts — ElasticSearchQuery type
- https://github.com/huggingface/huggingface.js/pull/885/files — example PR for adding query files

### Skill Created/Updated
`hf-hub-model-download-stats/` — comprehensive reference with SKILL.md for quick lookup and this deep-dive learnings file.
