# Sibling Config Requires Raw API (blobs=true strips it)

**Observed 2026-07-30, run 5 of `sakthai-context-7b-merged` health check.**

## The problem

When building sibling comparison sections in health-check YAMLs, the natural
approach is to call `?blobs=true&expand[]=siblings` for each sibling to get
their file sizes. However, this endpoint returns `null` for the top-level
`config` and `safetensors` fields — you cannot extract `hidden_size`,
`num_layers`, `num_attention_heads`, or `total_parameters` from it.

## The fix

Fetch sibling data in **two calls** (just like the target model):

```bash
# Call 1: Raw API (no params) — for config + safetensors
curl -s "https://huggingface.co/api/models/${SIBLING_ID}" \
  -H "Authorization: Bearer $HF_TOKEN" -o /tmp/${SLUG}.json

# Call 2: With blobs+siblings — for file sizes
curl -s "https://huggingface.co/api/models/${SIBLING_ID}?blobs=true&expand[]=siblings" \
  -H "Authorization: Bearer $HF_TOKEN" -o /tmp/${SLUG}_sib.json
```

The raw call's `config` dict gives you the architecture data. The blobs call
gives you file sizes and LFS details.

## Data points

- **sakthai-context-0.5b-merged**: `?blobs=true&expand[]=siblings` returned
  `config: null, safetensors: null`. Downloads/likes also null even when
  the model has real data (1370 downloads).
- **sakthai-context-1.5b-merged**: Same pattern — blobs endpoint returned
  null config, null safetensors.

## Economy

Two calls per sibling costs ~200ms each. For a family of 3 siblings, that's
~6 API calls total (vs 3). The overhead is acceptable for a cron health
check that runs every few hours.

## Alternative

If you only need `hidden_size` and `num_layers` for comparison (not full
config), fetch just those from the sibling's `config.json` directly:

```bash
curl -s "https://huggingface.co/${SIBLING_ID}/resolve/main/config.json" \
  -H "Authorization: Bearer $HF_TOKEN" \
  | python3 -c "import sys,json; c=json.load(sys.stdin); print(c.get('hidden_size'), c.get('num_hidden_layers'))"
```

This is cheaper than a full model-info call but brittle if the CDN returns
a 404 for `/resolve/main/` (pattern documented in `config-json-raw-404-despite-existing.md` —
fall back to `hf_hub_download()`).
