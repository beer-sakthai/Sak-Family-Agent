# Embedding Model Health Check — SakThai Embedding Multilingual (384-dim)

**Date:** 2026-07-30
**Model:** Nanthasit/sakthai-embedding-multilingual
**Pipeline:** sentence-similarity
**Library:** sentence-transformers
**Architecture:** BERT (384-dim, 12 layers, 12 heads)

## Summary

Performed zero-cost health eval on the multilingual embedding model. All data fetched via `curl` + HF API (no paid endpoints).

## Key Data Points

| Field | Value | Source |
|-------|-------|--------|
| Downloads | 362 | `/api/models/{id}` |
| Likes | 0 | `/api/models/{id}` |
| Created | 2026-07-25T06:55:26Z | `createdAt` field |
| Last modified | 2026-07-30T21:21:08Z | `lastModified` field |
| Age | 5.6 days | computed |
| Velocity | 64.6 / day | computed (362 / 5.6) |
| Total storage | 487,720,403 bytes (465 MB) | `usedStorage` field |
| Model file | 470,637,416 bytes (448 MB) | `x-linked-size` HEAD header |
| Parameters (F32) | 117,653,760 (117.65M) | `safetensors.parameters.F32` |
| Embedding dim | 384 | `config.json.hidden_size` + tag `"384-dim"` |
| Model type | BertModel, float32 | `config.json` |
| Pipeline tag | `sentence-similarity` | API |
| Library | `sentence-transformers` | API |

## Notable Observations

### 1. `usedStorage` close to model file size

Unlike most Xet repos (which show 8–10x inflation due to Git history), this model's `usedStorage` (465 MB) is only ~3.6% larger than the model file (448 MB). This suggests minimal Git revision history — the model was uploaded once and hasn't been replaced. Good hygiene signal.

### 2. `createdAt` was present

Unlike the `sakthai-plus-1.5b` model (same-day) which lacked `createdAt`, this 5-day-old model had it at `createdAt: 2026-07-25T06:55:26.000Z`. So `createdAt` absence is not just a same-day issue — some repos have it, some don't. Always check both `createdAt` and `_id` (MongoDB ObjectId) fallback.

### 3. Embedding dimension inferred from two sources

- `config.json` → `hidden_size: 384`
- Tag field → `"384-dim"`

Both agreed. The `1_Pooling/config.json` file (which has the authoritative `embedding_dimension`) exists on the repo but wasn't fetched — `hidden_size` + tag cross-reference was sufficient for the report. For production-grade reports, fetch `1_Pooling/config.json` to confirm `pooling_mode` and `include_prompt`.

### 4. No benchmark scores

The model has no `model-index` (no MTEB/BEIR scores). This is common for embedding models but is a major credibility gap. The `.eval_results/` directory on HF had 4 prior health-check files — suggesting automated evals run but no actual MTEB benchmarks.

### 5. Sibling sizes all `None`

The base API response returned sibling entries with only `rfilename` — no `size`, `lfs`, or `type` fields. This is typical for non-Transformers repos (sentence-transformers doesn't register as a transformers library). The model file size had to be obtained via HTTP HEAD `x-linked-size`.

## Workflow

```bash
# Step 1: Fetch model metadata
curl -s "https://huggingface.co/api/models/Nanthasit/sakthai-embedding-multilingual" -o /tmp/embed_model.json

# Step 2: Fetch architecture config
curl -s "https://huggingface.co/Nanthasit/sakthai-embedding-multilingual/raw/main/config.json" -o /tmp/embed_config.json

# Step 3: Get model file size via HEAD
curl -sI "https://huggingface.co/Nanthasit/sakthai-embedding-multilingual/resolve/main/model.safetensors" | grep -i x-linked-size

# Step 4: Parse with python3
python3 << 'PYEOF'
import json
with open('/tmp/embed_model.json') as f:
    d = json.load(f)
print('downloads:', d['downloads'])
print('createdAt:', d.get('createdAt'))
print('params:', d.get('safetensors', {}).get('parameters'))
print('usedStorage:', d.get('usedStorage'))
PYEOF

# Step 5: Write YAML + upload
uv run python3 -c "
from huggingface_hub import HfApi
api = HfApi(token=open('/root/.cache/huggingface/token').read().strip())
api.upload_file(
    path_or_fileobj='.eval_results/health-check.yaml',
    path_in_repo='.eval_results/health-check.yaml',
    repo_id='Nanthasit/sakthai-embedding-multilingual',
    repo_type='model',
    commit_message='health: daily eval 2026-07-30'
)
"
```

## Verification

14/14 checks passed using tempfile-based verification script (`hermes-verify-` prefix in `/tmp`):

1. model.id correct
2. pipeline_tag = sentence-similarity
3. library_name = sentence-transformers
4. downloads = 362
5. likes = 0
6. velocity numeric
7. embedding_dim = 384
8. hidden_size = 384
9. 12 hidden layers
10. 117.65M params
11. healthy = true
12. 7 training datasets
13. TEI compatible
14. Remote upload verified via `urllib.request.urlopen()` to raw content
