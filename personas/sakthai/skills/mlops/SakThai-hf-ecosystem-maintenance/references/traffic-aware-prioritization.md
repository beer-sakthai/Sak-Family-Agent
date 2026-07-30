# Traffic-Aware Prioritization for Card Enrichment

> Added 2026-07-29 — pattern: when enriching or cross-linking, target highest-traffic cards first.

## Core Principle

**A cross-link on the flagship model card reaches 100× more visitors than the same link on a low-traffic model.** Every edit should be ranked by the traffic of the card being edited, not by the discoverability need of the target asset.

## Prioritization Order

When running ANY enrichment pass (add cross-links, promote low-download models, insert Space links, add Rising Stars section):

1. **Sort all public models by downloads descending** (HF API: `/api/models?author=Nanthasit&sort=downloads&direction=-1`)
2. **Start with the highest-traffic card** — the flagship (typically 1.5b-merged at 1200+ dl)
3. **Cascade down** — after each card, move to the next most-downloaded sibling
4. **Stop when cards have <50 downloads** — editing these has negligible discoverability ROI

## What to Add to the Flagship Card

The flagship card should carry these promotion elements:

| Element | Location in Card | Example |
|---------|-----------------|---------|
| Space links (vision-demo, TTS, leaderboard) | `## Links` footer section | `[Vision Demo](...) · [TTS Demo](...)` |
| Low-download gems table | After Model Family table | `## 🌱 Low-download gems` with 4-5 rows |
| `extra.sibling` YAML | Frontmatter | `sibling: author/sakthai-vision-demo` |

## Why This Works

HF's discoverability is search-driven. The flagship card ranks highest in HF search results for the author's name. Every visitor who lands on it and then clicks a cross-link represents **incremental traffic that would never organically reach** the low-download model. This is the cheapest traffic acquisition strategy available (zero cost, no external promotion).

## Real Example (2026-07-29)

**Before:** `sakthai-context-1.5b-merged` (1,269 dl) — Links section had only Leaderboard Space; no Space links to TTS or vision-demo; no low-download promotion section.

**After:** Added vision-demo + TTS demo Space links; inserted a `## 🌱 Low-download gems` section promoting context-0.5b-tools (7 dl), tts-model (69 dl), coder-1.5b (70 dl), vision-7b (104 dl), and irrelevance-supplement dataset (0 dl).

**Impact estimation:** Every 100 visitors to the flagship now see a clear path to 5 previously invisible assets. At 1,269 lifetime downloads, even a 5% click-through = ~63 incremental visits to low-download pages.

## Verification

After editing the flagship, check:

```python
from huggingface_hub import HfApi
api = HfApi()
path = api.hf_hub_download(repo_id='author/flagship-model', filename='README.md', repo_type='model')
with open(path) as f:
    content = f.read()
assert 'vision-demo' in content       # Space link
assert 'Low-download gems' in content  # promotion section
assert 'irrelevance-supplement' in content  # zero-dl dataset promoted
```
