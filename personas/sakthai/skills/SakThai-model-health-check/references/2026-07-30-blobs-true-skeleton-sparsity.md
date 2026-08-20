# `?blobs=true` Sparsity on Skeleton Repos

**Date:** 2026-07-30
**Model:** `Nanthasit/sakthai-plus-1.5b-coder`
**Affects:** Skeleton repos (no weights, no config, usedStorage=0)

## Symptoms

Fetching a skeleton repo with `?blobs=true&expand[]=siblings` returned only:

```json
{
  "_id": "6a6b4b860324b69cf68de862",
  "id": "Nanthasit/sakthai-plus-1.5b-coder",
  "siblings": [
    {"rfilename": ".eval_results/health-check-plus-1.5b-coder-2026-07-30.yaml"},
    ...
  ]
}
```

**All other fields missing:** `downloads`, `likes`, `lastModified`, `createdAt`, `pipeline_tag`, `library_name`, `cardData`, `tags`, `config`, `safetensors`, `gguf`, `usedStorage`, `model-index`, `private`, `sha`, `widgetData`, `spaces`, `transformersInfo`.

Response size: ~800 bytes vs ~5300 bytes without `?blobs=true`.

This is **more severe** than the sibling-size sparsity documented in the main skill (where only LFS `size` fields are absent). Here the entire metadata payload is suppressed.

## Root Cause

The HF API's blob-cache layer, when combined with a repo that has zero LFS blobs (no weight files), returns an empty/minimal projection of the model record. The `?blobs=true` flag tells the API to include LFS metadata, but since there are zero blobs, the API short-circuits and returns only the stable identifier + sibling list.

Verified 2026-07-30 on a skeleton repo with 6 siblings (all under 15 KB, none LFS).

## Recovery

**Optimal fetch order for unknown repos:**

1. **Fetch without `?blobs=true` first** — get the full metadata payload (downloads, likes, config, tags, cardData, etc.)
2. **Fetch with `?blobs=true` only if** you need LFS blob sizes AND the model is confirmed non-skeleton (check `usedStorage > 0` or `'safetensors' in info` from step 1)

```bash
# Step 1: metadata (always works)
curl -s "https://huggingface.co/api/models/${REPO_ID}" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -o "/tmp/${SLUG}_info.json"

# Step 2: blobs only when needed
if python3 -c "import json; d=json.load(open('/tmp/${SLUG}_info.json')); assert d.get('usedStorage',0)>0, 'skeleton'"; then
  curl -s "https://huggingface.co/api/models/${REPO_ID}?blobs=true" \
    -H "Authorization: Bearer $HF_TOKEN" \
    -o "/tmp/${SLUG}_blobs.json"
fi
```

## Detection

Check for this sparsity immediately after a `?blobs=true` fetch:

```python
import json
data = json.load(open("/tmp/model_info.json"))
# Sparse if only these keys exist
if set(data.keys()) <= {"_id", "id", "siblings"}:
    # Re-fetch without ?blobs=true
    print("Skeleton repo detected via ?blobs=true sparsity — re-fetching without blobs")
```

## Prevention

Never use `?blobs=true` in the first fetch. Always use the two-step pattern above. The first fetch is cheap (~5300 bytes) and gives you all metadata. Then conditionally fetch blobs only for non-skeleton repos that actually have LFS files to measure.
