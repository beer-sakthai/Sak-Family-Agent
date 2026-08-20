# Embedding Model API Sparsity — Two-Call Data Source Pattern

**Date:** 2026-07-30
**Model:** `Nanthasit/sakthai-embedding-multilingual` (384-dim sentence-transformers BERT)
**Finding:** The HF API returns DIFFERENT fields depending on query parameters, and they are mutually exclusive for sparsely-populated models.

## The Trap

The single-model endpoint `/api/models/{id}` returns:
- With `?blobs=true&expand[]=siblings`: only `_id`, `id`, `siblings` — all scalar fields (`downloads`, `likes`, `createdAt`, `pipeline_tag`, `library_name`) are `None`
- With `?expand[]=cardData`: only `_id`, `id`, `cardData` — `siblings` array is EMPTY (zero length)
- With NO query params: only `_id`, `id` (most sparse)

None of these alone gives you everything you need for a health check.

## The Fix — Three Separate Calls

```bash
# Call 1: cardData (pipeline_tag, library_name, license, tags, datasets) — NO siblings
curl -s "https://huggingface.co/api/models/{REPO_ID}?expand[]=cardData" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -o "/tmp/${MODEL_SLUG}_card.json"

# Call 2: siblings with file sizes — NO cardData, NO scalar fields
curl -s "https://huggingface.co/api/models/{REPO_ID}?blobs=true&expand[]=siblings" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -o "/tmp/${MODEL_SLUG}_sib.json"

# Call 3: scalar fields (downloads, likes, createdAt) from author list
curl -s "https://huggingface.co/api/models?author={AUTHOR}&sort=downloads&limit=50" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -o "/tmp/${MODEL_SLUG}_author.json"
```

Then merge in Python:
```python
import json

with open(f'/tmp/{MODEL_SLUG}_card.json') as f:
    card_data = json.load(f).get('cardData', {}) or {}

with open(f'/tmp/{MODEL_SLUG}_sib.json') as f:
    siblings = json.load(f).get('siblings', [])

with open(f'/tmp/{MODEL_SLUG}_author.json') as f:
    author_models = json.load(f)

# Find scalar fields for this specific model
target = next((m for m in author_models if m['id'] == REPO_ID), {})
downloads = target.get('downloads', 0)
likes = target.get('likes', 0)
created_at = target.get('createdAt')
```

## Sibling `size` Field Without `lfs`

The `?blobs=true` call returned siblings with keys `['rfilename', 'blobId', 'size']` — no `lfs` sub-dict. The `size` field was directly on the sibling dict:

```python
for sib in siblings:
    # This works: sib['size'] is the actual file size
    sz = sib.get('size', 0)

    # This FAILS: sib.get('lfs', {}) returns {} and lfs.get('size') returns 0
    # lfs = sib.get('lfs', {})
    # sz = lfs.get('size', 0)  # Always 0!
```

The universal safe pattern checks for `lfs` existence first:
```python
lfs = sib.get('lfs')
if lfs and isinstance(lfs, dict):
    sz = lfs.get('size', 0)
else:
    sz = sib.get('size', 0)
```

## Detection Signal

If the initial `/api/models/{REPO_ID}` response has fewer than 5 top-level keys (e.g. only `_id`, `id`, `siblings`), immediately plan for multi-call workflow. This is NOT a skeleton repo signal — the model has real weights (449 MB model.safetensors) but the API simply doesn't return scalar fields through the single-model endpoint.

## Root Cause

The `sentence-transformers` library creates repos via a pattern that may not populate all HF API metadata fields uniformly. The author search endpoint (which indexes from a different data source) always has complete scalar fields. This is a known HF API indexing behavior — not a bug, but a design asymmetry between the single-model endpoint and the search/listing endpoint.
