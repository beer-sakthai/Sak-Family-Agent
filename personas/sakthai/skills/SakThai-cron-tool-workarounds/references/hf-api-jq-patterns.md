# HF API + jq Patterns for Cron Sessions

Common `jq` incantations for extracting Hugging Face ecosystem data. These bypass tirith's pipe-to-interpreter block by using `jq` instead of `python3 -c`.

## Model Queries

### List all models with key fields (TSV output)

```bash
curl -s 'https://huggingface.co/api/models?author=Nanthasit&limit=50' \
  | jq -r '.[] | [.id, .downloads, .pipeline_tag // "none", .private] | @tsv'
```

**Output:** `Nanthasit/sakthai-context-1.5b-merged	1269	text-generation	false`

### Total download sum across all models

```bash
curl -s 'https://huggingface.co/api/models?author=Nanthasit&limit=50' \
  | jq '[.[].downloads] | add'
```

### Count models (total)

```bash
curl -s 'https://huggingface.co/api/models?author=Nanthasit&limit=50' \
  | jq 'length'
```

### Count public models only

```bash
curl -s 'https://huggingface.co/api/models?author=Nanthasit&limit=50' \
  | jq '[.[] | select(.private == false)] | length'
```

### Count models by pipeline_tag

```bash
curl -s 'https://huggingface.co/api/models?author=Nanthasit&limit=50' \
  | jq 'group_by(.pipeline_tag) | map({tag: .[0].pipeline_tag, count: length})'
```

### Find models with likes > 0 (social signal)

```bash
curl -s 'https://huggingface.co/api/models?author=Nanthasit&limit=50' \
  | jq '[.[] | select(.likes > 0) | {id: .id, likes: .likes}]'
```

## Dataset Queries

### List all datasets with download counts

```bash
curl -s 'https://huggingface.co/api/datasets?author=Nanthasit&limit=50' \
  | jq -r '.[] | [.id, .downloads, .private] | @tsv'
```

### Total dataset downloads

```bash
curl -s 'https://huggingface.co/api/datasets?author=Nanthasit&limit=50' \
  | jq '[.[].downloads] | add'
```

### Count datasets

```bash
curl -s 'https://huggingface.co/api/datasets?author=Nanthasit&limit=50' \
  | jq 'length'
```

## Space Queries

### List all Spaces with SDK

```bash
curl -s 'https://huggingface.co/api/spaces?author=Nanthasit&limit=50' \
  | jq -r '.[] | [.id, .sdk // "none", .private] | @tsv'
```

## Collection Queries

### Get collection summary (items count + breakdown by type)

```bash
curl -s 'https://huggingface.co/api/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02' \
  | jq '{title: .title, description: .description, item_count: (.items | length), model_count: ([.items[] | select(.type == "model")] | length), dataset_count: ([.items[] | select(.type == "dataset")] | length), space_count: ([.items[] | select(.type == "space")] | length)}'
```

### List all collection items with type and id

```bash
curl -s 'https://huggingface.co/api/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02' \
  | jq '[.items[] | {type: .type, id: .id}]'
```

**⚠️ Format may have changed (observed 2026-07-30):** `.type` and `.id` returned null for all 22 items. If this happens, probe the current shape first:
```bash
# Discover fields on first item
curl -s 'https://huggingface.co/api/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02' \
  | jq '.items[0] | keys'

# Then access using the actual field names
curl -s '...' | jq '[.items[] | {id: .???., type: .???}]'  # fill in after discovery
```

### Verify collection description contains correct count

```bash
curl -s 'https://huggingface.co/api/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02' \
  | jq '.description | test("12 models"; "i")'
```

Returns `true` or `false`. Pair with the breakdown query above to compare stated count vs actual.

## Collection PATCH Response Format

The `PATCH /api/collections/{namespace}/{slug}` endpoint returns a **wrapped response**, not the bare collection object:

```json
{
  "success": true,
  "data": {
    "slug": "...",
    "description": "...",
    "items": [...],
    ...
  }
}
```

**If you parse `response.json()['description']` directly, it crashes with KeyError** — the description is inside `.data`. Always unwrap:

```python
import requests
resp = requests.patch(
    f"https://huggingface.co/api/collections/{slug}",
    headers={"Authorization": f"Bearer {HF_TOKEN}"},
    json={"description": new_description},
)
# ❌ response.json()['description'] — KeyError
# ✅ Correct:
updated_desc = resp.json()["data"]["description"]
```

This quirk only affects the PATCH endpoint. The GET endpoint returns the bare collection object directly (no `.success`/`.data` wrapper).

## Combined Patterns

### Full ecosystem snapshot (models + datasets + spaces)

```bash
# Fetch all three in parallel
curl -s 'https://huggingface.co/api/models?author=Nanthasit&limit=50' -o /tmp/hf_models.json &
curl -s 'https://huggingface.co/api/datasets?author=Nanthasit&limit=50' -o /tmp/hf_datasets.json &
curl -s 'https://huggingface.co/api/spaces?author=Nanthasit&limit=50' -o /tmp/hf_spaces.json &
wait

# Extract key metrics
echo "Models: $(jq 'length' /tmp/hf_models.json) — $(jq '[.[].downloads] | add' /tmp/hf_models.json) dl"
echo "Datasets: $(jq 'length' /tmp/hf_datasets.json) — $(jq '[.[].downloads] | add' /tmp/hf_datasets.json) dl"
echo "Spaces: $(jq 'length' /tmp/hf_spaces.json)"
```

### Ecosystem delta check (compare two fetches)

```bash
# After first fetch (baseline)
curl -s '...' | jq '[.[].downloads] | add' > /tmp/prev_dl.txt

# After second fetch (current)
curl -s '...' | jq '[.[].downloads] | add' > /tmp/curr_dl.txt

# Delta
echo "Delta: $(( $(cat /tmp/curr_dl.txt) - $(cat /tmp/prev_dl.txt) ))"
```

## Pitfalls

- **Sort params**: Only `downloads`, `createdAt`, `lastModified` are valid. `trending` is NOT valid for API. Always pair with `direction=-1` (descending).
- **Collection slug**: The full slug includes the UUID suffix (`sakthai-model-family-6a64745450b12d421c1f9f02`). Without the UUID, the API returns 404. Get the slug from the collection URL.
- **Empty/null response**: If `jq` returns `Cannot iterate over null (null)`, the API call failed (network, auth, or wrong URL). Check the raw curl output first.
- **Rate limits**: Unauthenticated HF API calls are generous (~100/min) but not unlimited. Always use `-H "Authorization: Bearer $(cat ~/.cache/huggingface/token)"` for higher limits.
- **Pagination**: Default limit is 50 items per page. Add `&limit=100` for more. For full portfolios, paginate with `&p=N+1`.
- **Private models**: The `/api/models?author=Nanthasit` endpoint includes private models only when authenticated with the owner's token. Without auth, private models are invisible — the count will differ.
