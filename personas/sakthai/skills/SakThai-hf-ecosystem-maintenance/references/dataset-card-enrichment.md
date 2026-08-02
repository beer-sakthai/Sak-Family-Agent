# Dataset Card Enrichment Patterns

Documented 2026-07-29 — patterns for enriching dataset cards with badges, cross-links, and ecosystem navigation. Complements `card-enrichment-patterns.md` (model-focused) and `dataset-card-yaml-fixes.md` (YAML/naming).

## Why Enrich Dataset Cards?

Dataset cards drive discoverability differently than model cards:
- **Models** attract users via pipeline tags and search widgets
- **Datasets** attract users via card metadata search and ecosystem cross-references
- A dataset with no badges or cross-links is invisible even when it's essential (e.g., irrelevance-supplement, bench-v1)

## Core Enrichment: Badges

Every dataset card should start with three badges in a centered `<p>` block immediately after the YAML frontmatter:

```markdown
<p align="center">
  <a href="https://huggingface.co/collections/<author>/<collection-id>"><img src="https://img.shields.io/badge/Collection-<Collection%20Name>-6644cc" alt="Collection"/></a>
  <img src="https://img.shields.io/badge/downloads-<count>-blue" alt="Downloads"/>
  <img src="https://img.shields.io/badge/license-<license>-green" alt="License"/>
</p>
```

### Badge Rules

| Badge | Type | Source | Notes |
|-------|------|--------|-------|
| Collection | Static | Known collection slug | Always add — links the dataset to the ecosystem hub |
| Downloads | Static or dynamic | HF API | Static `downloads-<count>-blue` is simpler and reliable. Dynamic via `img.shields.io/badge/dynamic/json?url=...&query=$.downloads` works but needs URL-encoding. For 0-dl datasets, static is fine. |
| License | Static | Known license | Match the YAML `license:` field. Common: `Apache%202.0`, `MIT`, `CC-BY-4.0`. |

### Placement

Badges go **between the YAML frontmatter and the title**:

```markdown
---
# frontmatter
---

<p align="center">
  ...badges...
</p>

# Dataset Title
```

This is the same placement used for model cards in `card-enrichment-patterns.md`.

## Related Assets Table

Dataset cards need a **different** cross-reference table than model cards. Model cards use a "Model Family" table listing only models. Dataset cards need a "Related Assets" table listing both **models and sibling datasets**, since visitors from a dataset may want to navigate to either.

### Template

```markdown
## Related Assets

| Type | Asset | Description |
|------|-------|-------------|
| 📊 **Benchmark** | [sibling-bench-v2](https://huggingface.co/datasets/<author>/<bench>) | Description of what this benchmark evaluates |
| 📦 **Training** | [sibling-dataset](https://huggingface.co/datasets/<author>/<dataset>) | Description (row count, tools, format) |
| 🧰 **Training** | [supplement-dataset](https://huggingface.co/datasets/<author>/<supplement>) | Specific use-case supplement |
| 🤖 **Model** | [reference-model](https://huggingface.co/<author>/<model>) | What this model does with the data |
| 🏠 **Collection** | [Ecosystem Name](https://huggingface.co/collections/<author>/<collection-id>) | Central hub for all ecosystem assets |

### Emoji Type Indicators

| Emoji | Type | When |
|:-----:|------|------|
| 📊 | Benchmark dataset | Evaluation/benchmark datasets |
| 📦 | Training dataset | Main training data |
| 🧰 | Supplement dataset | Safety, edge-case, or fix supplements |
| 🤖 | Model | Reference or consumer model |
| 🏠 | Collection | Always include the central collection |
| 🚀 | Space | Demo or showcase Space |

### Rules

- **5–7 rows max** — keep it compact
- **Description column** — 5–15 words explaining why this asset matters for *this* dataset
- **Always include the collection** — the last row links back to the hub
- **Sort by relevance** — most-related assets first, collection last
- **Every link** must resolve (verify with `curl -sI`)

## Full Dataset Card Checklist

Use this when enriching a dataset card from scratch:

| # | Element | Priority | How to Check |
|---|---------|:--------:|-------------|
| 1 | YAML `license:` field | High | `grep '^license:' README.md` |
| 2 | YAML `tags:` include `sakthai`, `house-of-sak` | High | `grep '^tags:' README.md` |
| 3 | YAML `pretty_name:` matches repo name | High | `grep '^pretty_name:' README.md` |
| 4 | Collection badge | High | `grep 'Collection-' README.md` |
| 5 | Download badge | High | `grep 'downloads-' README.md` |
| 6 | License badge | Medium | `grep 'license-' README.md` |
| 7 | Related Assets table with cross-links | High | `grep '## Related Assets' README.md` |
| 8 | Dataset description (what, why, when) | High | `grep '^# ' README.md` — title present |
| 9 | Data format / schema documentation | Medium | Check for fields table or schema section |
| 10 | Usage example code | Medium | Check for code block with `load_dataset` |
| 11 | Link to sibling models from Related Assets | High | `grep 'hf.co/' README.md \| grep -c model` ≥ 1 |
| 12 | Link to collection from Related Assets | High | `grep 'collections/' README.md` |

## Dataset vs Model Card Differences

| Aspect | Model Card | Dataset Card |
|--------|-----------|-------------|
| Primary badge | Pipeline + downloads | Collection + downloads + license |
| Cross-reference table | "Model Family" (models only) | "Related Assets" (models + datasets + Spaces) |
| YAML frontmatter | `pipeline_tag`, `base_model`, `model-index` | `configs`, `task_categories`, `pretty_name`, `annotations_creators` |
| Code example | `pipeline("task", model="...")` | `load_dataset("...")` |
| Search discoverability | Pipeline tag + tags | Task categories + tags + pretty_name |

## Real Example: bench-v1 (2026-07-29)

**Target:** `Nanthasit/sakthai-bench-v1` (0 dl, 235 rows, BFCL-style evaluation)

**Before:** 4,426 chars, no badges, no cross-links, no collection reference.

**After:** 5,690 chars, 3 badges + "Related Assets" table with 5 cross-links.

**Verification:** Grep-verified 12 conditions against live HF README:

```python
from huggingface_hub import HfApi
api = HfApi()
path = api.hf_hub_download(repo_id='Nanthasit/sakthai-bench-v1', filename='README.md', repo_type='dataset')
with open(path) as f:
    c = f.read()
assert 'Collection-SakThai' in c       # collection badge
assert 'downloads-0-blue' in c         # download badge
assert 'license-Apache' in c           # license badge
assert '## Related Assets' in c        # cross-links section
assert '/sakthai-bench-v2' in c        # benchmark sibling
assert '/sakthai-combined-v7' in c     # training data sibling
assert '/sakthai-irrelevance-supplement' in c  # fix data sibling
assert '/sakthai-context-0.5b-tools' in c      # model sibling
assert '/sakthai-model-family' in c    # collection hub
assert '## Composition' in c           # original content preserved
assert 'Argument scoring is exact-match' in c  # original caveats preserved
assert 'license: apache-2.0' in c      # YAML frontmatter intact
```

This is the minimum viable enrichment for a 0-download dataset card. Add more sections (schema docs, usage examples, Rising Stars) in subsequent cycles as needed.

## Known Limitations

- **Static download badges** show the count at enrichment time, not live. For datasets with 0 dl the badge is accurate; for growing datasets consider dynamic badges via `img.shields.io/badge/dynamic/json?url=...`.
- **Related Assets tables** require manual updates when new siblings are created. Update in the same cycle as adding a new dataset to the collection.
- **Collection badges** need the collection UUID to be correct. Verify with `curl -s "https://huggingface.co/api/collections/<author>/<collection-id>"` — if it returns `{"title": "..."}`, the UUID is valid.
