# Model Card Cross-Promotion Patterns

Techniques for turning low-download model cards into ecosystem navigation hubs.
Covers the reverse direction of `dataset-card-cross-promotion.md` — adding
dataset, space, and sibling-model cross-references to model cards.

## When to Use

- The target model has <50 downloads (lowest discoverability = highest marginal gain)
- The card has basic content but no cross-links to sibling assets
- All other models in the family are enriched, making this the "last mile" card
- You want HF search to surface the model via `model-index` YAML (even when inference isn't set up)

## 1. model-index for Low-Download Models

Adding a `model-index` YAML block with **verified benchmark data** helps the model
appear in HF search results filtered by task/benchmark, even when serverless inference
isn't configured. This is one of the highest-leverage improvements for a low-download
model because it unblocks discoverability.

**Pattern:**
```yaml
model-index:
- name: your-model-name
  results:
  - task:
      type: text-generation      # pipeline tag
      name: Tool-Calling         # human-readable task name
    dataset:
      name: your-dataset-name
      type: Nanthasit/your-dataset  # must be a valid HF dataset ID or "internal"
    metrics:
    - type: accuracy
      value: 0.8                  # numeric score
      name: Score (4/5)           # human-readable + original format
      verified: true              # false if upstream estimate
```

**Key rules:**
- Every `results[]` entry **must** have `dataset: {name, type}` — missing it silently
  discards the entire model-index (no error, no rendering)
- Set `verified: false` when scores are upstream estimates, not actual measurements
- Use `verified: true` only when multi-trial evaluation was run on the exact model files
- The `name` field in metrics is human-readable — include the original score format
  (e.g. `"Score (4/5)"` alongside the numeric `value: 0.8`)

**Strategy for low-download models:** Even a single verified result entry (e.g. 4/5 on
tool-calling) gives the model a non-zero entry in HF's search task filters — it becomes
findable alongside the flagship models, not buried at the bottom of the author's list.

**See also:** `hf-model-card-yaml-widgets` skill §1 (YAML schema) and
`model-index-verification.md` (verifying model-index was accepted).

## 2. Download-Count-Anchored Family Table

A family table with download counts sorted by popularity turns a dead-end card into a
navigation hub. Visitors can immediately see which model is most popular (1,269 ⬇) and
find the right sibling for their use case.

**Pattern (markdown table):**
```markdown
| Model | Size | Role | Downloads |
|:------|:----:|:-----|:---------:|
| [context-1.5b-merged](...) | 934 MB | Flagship tool-calling GGUF | 1,269 ⬇ |
| [context-0.5b-merged](...) | 380 MB | Lightweight / edge GGUF | 1,030 ⬇ |
| ...sorted by downloads descending... | | | |
| **★ [this-model](...) (you are here)** | LoRA | Edge tool-calling | 7 🌱 |
```

**Key details:**
- Sort descending by download count — puts popular models first
- Add ★ marker + "(you are here)" for the current model — lets visitors orient
- Use `🌱` seedling emoji for the lowest-download model (shows growth potential)
- Always fetch live download counts from the API before writing the table
- Update ALL sibling card family tables when refresh is needed (cross-table drift is common)
- Include **all** public sibling models — even the ones with very low counts

**Fetching live counts (cron-safe):**
```bash
curl -s "https://huggingface.co/api/models?author=Nanthasit" -o /tmp/models.json
python3 -c "
import json
for m in sorted(json.load(open('/tmp/models.json')), key=lambda x: x.get('downloads',0), reverse=True):
    mid = m['id'].split('/')[1]
    print(f'{mid}: {m.get(\"downloads\",0)} dl')
"
```

## 3. Low-Download Gems Section

A dedicated section on the lowest-download model's card that cross-promotes OTHER
underperforming models, datasets, and spaces. This turns a single dead-end card into
a discovery hub for the entire long tail.

**Pattern (on the 7-dl model's card):**
```markdown
### Low-download gems

These models are new or specialised — downloads are low but they're production-ready:

| Model | Downloads | Best for |
|:------|:---------:|:---------|
| [tts-model](...) | 69 ⬇ | Multi-language TTS, 15 languages |
| [coder-1.5b](...) | 70 ⬇ | Code completion, bug finding |
| [vision-7b](...) | 104 ⬇ | Image-to-text, screenshots, diagrams |

| Dataset | Downloads | Role |
|:--------|:---------:|:-----|
| [irrelevance-supplement](...) | 0 🌱 | Irrelevance-rejection training data |
| [kaggle-notebooks](...) | 103 ⬇ | ML learning notebooks |
| [combined-v6](...) | 175 ⬇ | Tool-calling training data |

| Space | Role |
|:------|:-----|
| [sakthai-tts](...) | TTS web demo (static) |
| [sakthai-vision-demo](...) | Vision demo (static) |
| [sakthai-leaderboard](...) | Family benchmark leaderboard (static) |
```

**Why this works:** A visitor arriving at a 7-dl model already has low expectations.
Showing them 3+ tables of well-organized sibling assets demonstrates ecosystem depth
and invites further exploration. Without this, they'd leave after reading a single card.

**Selection criteria for the "gems" list:**
- Include the next 2-4 lowest-download models (30-200 dl range)
- Include ALL datasets with ≤200 dl
- Include ALL spaces (they all have 0 dl in the SakThai ecosystem)
- Do NOT include the flagship/headliner models (>500 dl) — they already have their own traffic

## 4. Dataset + Space Tables on Model Cards

Model cards that only link to other models miss the opportunity to cross-promote
datasets and Spaces. Adding dedicated tables for them exposes visitors to the full
ecosystem — datasets for training, Spaces for demos.

**When to add:**
- The card has a "Model Family" table but no dataset/spaces section
- A sibling dataset has <100 dl and needs visibility
- All Spaces are 0 dl and need any traffic they can get

**Placement:** After the model family table, before the Links/Footer section:
```markdown
## SakThai Model Family
[family table here]

### Datasets
[dataset table here]

### Spaces
[space table here]

## Links
...
```

**Do NOT duplicate** the data from the main family table — the dataset and space tables
are supplementary and serve a different purpose (showing the full pipeline, not just
model alternatives).

## 5. Verification Checklist

After uploading a cross-promotion-heavy card update, verify with content markers:

```bash
# Fetch live card
curl -s -o /tmp/verified.md "https://huggingface.co/author/repo/raw/main/README.md"

# Check all markers present
python3 -c "
content = open('/tmp/verified.md').read()
checks = {
    'model-index YAML': 'model-index:' in content,
    'download counts in family table': '⬇' in content,
    'low-download gems section': 'Low-download gems' in content or 'Low-download' in content,
    'dataset cross-promotion': 'irrelevance-supplement' in content or 'combined-v6' in content,
    'space cross-promotion': 'vision-demo' in content or 'leaderboard' in content,
    'you are here marker': 'you are here' in content,
    'model count current': '12 models' in content or '11 models' in content,  # adjust to actual
}
for name, result in checks.items():
    print(f'  {\"✅\" if result else \"❌\"} {name}')
"
```

All checks should pass before declaring the run complete. If one fails, re-download,
fix the content, and re-upload.

## Relationship to Other References

| Reference | Relationship |
|-----------|-------------|
| `dataset-card-cross-promotion.md` | Reverse direction: dataset cards → model links |
| `hf-ecosystem-cron-maintenance.md` | General cron workflow this pattern plugs into |
| `pipeline-integration-section.md` | Pipeline flow diagrams — complementary to cross-promotion tables |
| `model-card-audit-workflow.md` (hf-model-card-yaml-widgets) | How to pick which card to improve |
