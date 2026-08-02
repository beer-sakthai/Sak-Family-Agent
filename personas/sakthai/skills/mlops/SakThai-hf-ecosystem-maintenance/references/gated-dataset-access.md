# Gated Dataset Access on Hugging Face Hub

Some datasets in the ecosystem have `gated: auto` — requiring authentication to read their contents. This affects ecosystem maintenance workflows.

## Detection

A dataset is gated when the HF API shows `"gated":"auto"`:

```bash
curl -s 'https://huggingface.co/api/datasets/Nanthasit/SimpleToolCalling' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('gated'))"
# Returns: auto
```

## Impact on README Access

Unauthenticated requests to a gated dataset's raw README return a short error (137 chars):

```
Access to dataset Nanthasit/SimpleToolCalling is restricted. ...
```

**Authenticated requests** (with `Authorization: Bearer $HF_TOKEN`) return the full README normally.

## Workaround: Authenticated Fetch

Always pass the HF token when reading gated dataset READMEs:

```bash
curl -s -H "Authorization: Bearer $HF_TOKEN" \
  'https://huggingface.co/datasets/Nanthasit/SimpleToolCalling/raw/main/README.md'
```

In Python:
```python
import requests
r = requests.get(
    'https://huggingface.co/datasets/Nanthasit/SimpleToolCalling/raw/main/README.md',
    headers={'Authorization': f'Bearer {os.environ["HF_TOKEN"]}'}
)
```

## Tips

- **Gated ≠ Private.** Gated datasets are still listed publicly (`private: false`) and count toward ecosystem totals. Only their content requires authentication.
- **Deprecated + gated.** A gated dataset like `SimpleToolCalling` (52 dl, deprecated) should still have its card updated when enriching the ecosystem — it's a sibling that cross-promotes low-download assets.
- **Token fallback chain.** Check `HF_TOKEN`, then `HUGGING_FACE_HUB_TOKEN`, then `~/.cache/huggingface/token`, then `~/.huggingface/token`.
- **No silent 137-char fallback.** If you get exactly 137 chars of "access restricted" text, you hit a gated repo without auth — try with token before concluding the card is empty.

## Real-world example (2026-07-29)

**Target:** `Nanthasit/SimpleToolCalling` (dataset, 52 dl, gated, deprecated)

**Problem:** The card had stale ecosystem counts ("11 models, 4 datasets"), missing irrelevance-supplement from the datasets table, and no cross-promotion section. As a gated + deprecated dataset, it was the last sibling asset not enriched.

**Fix without local auth:** Used `HfApi` with `HF_TOKEN` from environment to:
1. Read current README (auth required — unauthenticated returned 137-char error)
2. Upload updated README via `api.upload_file()` to `Nanthasit/SimpleToolCalling`, repo_type='dataset'
3. Verify with authenticated GET request

**Changes:** Fixed counts (11/4→12/5 models/datasets), added irrelevance-supplement (0 dl 🚨) to table, added Rising Stars section promoting 0.5B-tools (7 dl 🌱). Card grew 4,427→5,265 chars.

**Key lesson:** Gated repos still need card enrichment — they appear in ecosystems and cross-promote sibling assets. Don't skip them just because they require auth.
