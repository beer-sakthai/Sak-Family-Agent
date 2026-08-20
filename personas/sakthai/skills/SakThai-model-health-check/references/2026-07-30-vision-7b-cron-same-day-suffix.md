# Vision 7B Health Check: Same-Day Re-run + GGUF-Only Pattern (2026-07-30)

**Model:** `Nanthasit/sakthai-vision-7b` (LLaVA-1.5-7b, Q4_K_M)
**Context:** Third health check on this model on the same calendar date (after v4, v5, v6 earlier runs).

## Key Patterns

### Same-Day Re-run Suffix Discovery

Two existing health checks already on HF from earlier today (base + `-v6`). The skill's "append -2" guidance is insufficient when parallel cron runs have already consumed `-2` through `-N`. Solution:

1. Query remote repo siblings for files matching the date-stamped prefix
2. Parse suffixes from existing filenames (base = suffix 1, `-2.yaml` = 2, etc.)
3. Use `max(found_suffixes) + 1` for the new file

My session used `-2` without checking, which would have collided if another job had written a `-2` between the check and the upload. Fixed in skill patch: added a discovery script to Section 3.

### Vision GGUF Architecture

Confirmed the GGUF-only pattern from the companion reference file:

- **`gguf` top-level API field** provided: `architecture: llama`, `context_length: 4096`, `totalFileSize: 4081370080`
- **No config.json** needed — architecture comes from GGUF header
- **Both GGUF files** required for inference: `llava-1.5-7b-hf-q4_k_m.gguf` + `mmproj-model-f16.gguf`
- **`?blobs=true` endpoint** returned real file sizes (4.08 GB + 624 MB) — no HEAD redirects needed

### Scoring: base_model_deduction as metadata

Health score computed: **47/100**

| Component | Score |
|-----------|:-----:|
| Popularity | 11 |
| Momentum | 60 |
| Benchmarks | 0 |
| Card quality | 90 |
| Repo hygiene | 100 |

Applying `base_model_deduction: -20` would drop to 27 — unreasonably harsh for a LLaVA fine-tune (the model is *designed* to be a fine-tune). Skill patched to clarify this field is informational metadata, not applied to the weighted-average score.

### Session Data Sources

| Source | Endpoint | Usage |
|--------|----------|-------|
| Card data | `?expand[]=cardData` | Metadata, tags, datasets, license |
| Siblings | `?blobs=true&expand[]=siblings` | Real file sizes (GGUF + mmproj) |
| Author list | `.../api/models?author=Nanthasit&limit=50` | Downloads, likes, velocity |
| Raw API | bare `/api/models/{id}` | `gguf` dict, `model-index`, `usedStorage` |
