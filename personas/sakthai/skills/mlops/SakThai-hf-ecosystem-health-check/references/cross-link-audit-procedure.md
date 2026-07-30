# Cross-Link Audit Procedure

## Purpose

Detect systemic cross-linking gaps across all model cards in a Hugging Face portfolio. A model that isn't linked from its siblings is invisible to users browsing the family. This audit catches: missing download badges, missing sibling references, missing Pipeline Integration sections, and stale model counts in narrative sections.

## Methodology

### Before You Start

Know the full roster. Beer's HF account (`Nanthasit`) has **14 models** on the API (12 meaningful + profile repo + combined-v6 model repo). The meaningful 12 to audit:

- sakthai-context-1.5b-merged, sakthai-context-0.5b-merged, sakthai-context-7b-merged — base LLMs
- sakthai-context-7b-128k — long-context variant
- sakthai-context-7b-tools, sakthai-context-1.5b-tools, sakthai-context-0.5b-tools — LoRA tool-calling adapters
- sakthai-embedding (28 dl), sakthai-embedding-multilingual (0 dl) — embeddings (note: two distinct models)
- sakthai-vision-7b (0 dl), sakthai-tts-model (0 dl) — multimodal
- sakthai-coder-1.5b (15 dl) — code generation

### Data Flow

1. **Authenticated fetch** — unauthenticated requests silently omit some public repos. Always use Bearer token:
   ```python
   req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
   ```
2. **For each model, fetch README** from `https://huggingface.co/Nanthasit/<model>/raw/main/README.md`
3. **Check markers** — use string-in or regex checks per the matrix below

### Marker Matrix

| Marker | How to Check | Why It Matters |
|--------|-------------|----------------|
| Dynamic download badge | `img.shields.io/endpoint?` or `img.shields.io/badge/dynamic/json?url=` + model's own API URL | Shows live download count; signals active model — two equivalent formats exist |
| Collection badge | `model-family` in badge URL AND slug resolves to a real collection (see "Collection slug validation" below) | Links back to family collection — a badge with a non-existent slug is invisible |
| Pipeline Integration section | `## Pipeline Integration` heading | Shows how this model fits in the pipeline |
| Family Links section | `## Family Links` or `### LLM / Reasoning` | Explicit sibling table |
| All siblings present | Count unique `sakthai-*` repo IDs referenced | If < N-1, some siblings invisible from this card |
| Origin story | "shelter in Cork" present | Human narrative — differentiator |
| House of Sak mention | "House of Sak" or "house-of-sak" present | Brand identity |
| Beer reference | "Beer" (capitalised, as person reference) | Personal connection |
| No stale model counts | Check for `\d+ models?` patterns in narrative | Should match current roster count |
| YAML tags | `house-of-sak`, `sakthai-family` in tags | Discoverability via tag search |

### Collection Slug Validation

Collection badge URLs take the form `https://huggingface.co/collections/{owner}/{slug}`. The slug includes a UUID suffix (e.g., `sakthai-model-family-6a64745450b12d421c1f9f02`). **A badge that passes the `model-family` string check may still point to a non-existent collection** — the UUID portion can be wrong while the human-readable prefix still matches.

**Validation pattern** — after extracting the slug from the badge URL, verify it resolves:

```python
from huggingface_hub import HfApi
api = HfApi(token=token)
for model_id in model_list:
    readme = get_readme(model_id)
    # Extract collection slug from badge URL (regex)
    import re
    match = re.search(r'collections/Nanthasit/(sakthai-model-family-\w+)', readme)
    if match:
        slug = match.group(1)
        try:
            col = api.get_collection(f'Nanthasit/{slug}')
            print(f'  [PASS] {model_id}: collection {slug} ({len(col.items)} items)')
        except Exception as e:
            print(f'  [FAIL] {model_id}: collection slug {slug} returned 404 — BROKEN LINK')
```

**What to do when a slug is broken:**
1. **Find the correct slug** by querying `api.list_collections(owner='Nanthasit')` and matching the collection by title (not slug).
2. **Fix every model/dataset card** that references the broken slug by uploading a corrected README.
3. **Root cause** — broken slugs arise from: (a) copy-paste from an outdated README; (b) collection was re-created with a new UUID; (c) auto-sync cron modified the collection while another agent held the old slug.

**Flag as HIGH severity** — a broken collection link means the model's primary cross-reference to the family is dead. No user clicking that badge gets anywhere useful.

### Prioritisation

Priority order for fixing gaps:
1. Zero-download models first (< 50 dl)
2. Models with missing sibling cross-links (direct impact on discoverability)
3. Models missing badges (visual signal of neglect)
4. Models missing Pipeline Integration (missed cross-sell opportunity)

### Reporting Format

Each audit produces:
- Per-model: pass/fail per marker, count of siblings linked vs expected
- Cumulative: total issues by category (badge missing, sibling missing, section missing)
- Priority queue: 2-3 models to fix next, in order

### Historical Findings

**2026-07-27 (first systematic audit):**
- Only `sakthai-embedding` (28 dl) had a dynamic download badge — all 11 others missing
- `sakthai-tts-model` (0 dl): worst offender — 4/11 siblings linked, no download badge, no Family Links section → fixed this run
- `sakthai-vision-7b` (0 dl): missing 3 sibling links (7b-128k, 1.5b-tools, 0.5b-tools), no download badge, says "16 models" in narrative
- `sakthai-context-7b-128k` (324 dl): was missing 3 sibling links (7b-tools, 1.5b-tools, 0.5b-tools) → **enriched 2026-07-27** with dynamic badge, Pipeline Integration, and full sibling table
- Most context models (1.5B, 0.5B, 7B merged + tools) missing Pipeline Integration sections
- `sakthai-embedding-multilingual` (0 dl): solid card, only missing download badge
- "Beer" mention absent from: embedding, coder-1.5b, context-0.5b-tools, context-1.5b-tools
