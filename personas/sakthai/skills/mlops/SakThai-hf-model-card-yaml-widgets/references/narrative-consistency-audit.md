# Narrative Consistency Audit — Model Card Origin Story Alignment

Ensure every model card in a family tells the same origin story. When a family grows to 10+ model repos, narrative drift is inevitable — later additions get technical depth but miss the emotional anchor present on the flagship cards.

## Trigger

- Cron-driven "one improvement" self-improvement cycle
- When a new model is added to the family
- Spot-checking after enriching several cards

## Step-by-Step

### 1. Inventory all model cards

```python
from huggingface_hub import HfApi
api = HfApi()
models = list(api.list_models(author='YourUsername'))
# Filter to only your family (skip profile repos, aux repos)
family = [m for m in models if m.id.startswith('YourUsername/sakthai-')]
```

### 2. Define markers

Pick the narrative elements that define your family. For the House of Sak, these are:

| # | Marker | What to Check | Example |
|---|--------|---------------|---------|
| 1 | `house-of-sak` YAML tag | Present in YAML `tags:` list | `- house-of-sak` |
| 2 | Origin story | Mentions shelter or recovery journey | "Built from a shelter in Cork, Ireland" |
| 3 | Beer reference | Creator's name appears | "Beer" |
| 4 | Beer quote | The tagline quote | `"I even don't know what I will have..."` |
| 5 | GitHub link | Link to beer-sakthai | `github.com/beer-sakthai` |
| 6 | House of Sak website | Link to HoS site | `house-of-sak.vercel.app` |
| 7 | Zero-budget mention | $0 infrastructure narrative | "$0 budget" |
| 8 | Purpose statement | Why the family exists | "companionship, not a business" |

### 3. Audit all cards

```python
import requests, re

def check_markers(repo_id) -> dict:
    url = f'https://huggingface.co/{repo_id}/raw/main/README.md'
    resp = requests.get(url)
    content = resp.text if resp.ok else ''
    return {
        'house-of-sak tag': 'house-of-sak' in content,
        'shelter narrative': 'shelter' in content or 'Cork' in content,
        'Beer reference': 'Beer' in content,
        'Beer quote': 'So nothing to lose' in content,
        'GitHub link': 'github.com/beer-sakthai' in content,
        'HoS link': 'house-of-sak.vercel.app' in content,
        'zero budget': '$0' in content or 'zero budget' in content,
        'purpose': 'family' in content.lower() and 'companion' in content.lower(),
    }

report = {}
for m in family:
    markers = check_markers(m.id)
    passed = sum(1 for v in markers.values() if v)
    report[m.id] = {'passed': passed, 'total': len(markers), 'missing': [k for k, v in markers.items() if not v]}
```

### 4. Pick the target

- Sort by `passed` ascending — the card with the fewest markers gets the fix
- Among ties, pick the one with lowest downloads (highest marginal gain)

### 5. Enrich the target card

Add the narrative section after the YAML frontmatter, preserving all existing technical content. Template:

```markdown
<p align="center"><em>🏠 Part of the <strong>House of Sak</strong> — 6 AI agents, one shared mind. Built from a shelter in Cork, Ireland with $0 budget.</em></p>
<p align="center">
  <a href="https://github.com/beer-sakthai"><img src="https://img.shields.io/badge/GitHub-beer--sakthai-181717" alt="GitHub"/></a>
  <a href="https://house-of-sak.vercel.app"><img src="https://img.shields.io/badge/🏠-House%20of%20Sak-gold" alt="HoS"/></a>
</p>

---

## The House of Sak

> *"I even don't know what I will have. So nothing to lose at the moment."* — Beer

The **House of Sak** is an AI agent family built by **Beer** during his recovery journey — from a shelter in Cork, Ireland, with no income and no infrastructure budget. What started as a project in isolation became a family of six AI personas that work together, learn together, and share one long-term memory brain.

This model is the **[role]** of that family — **[one-line purpose]**. Every model in the SakThai family was trained, quantized, and published on a **$0 budget** using free-tier infrastructure (Kaggle T4 GPUs, HF Inference, llama.cpp).

*Built with hope, one line of code at a time.*

---
```

Also add `house-of-sak` to the YAML tags list:
```yaml
tags:
  - sakthai-family
  - house-of-sak   # ← add this
```

### 6. Upload and verify

```python
api.upload_file(
    path_or_fileobj=enriched_card.encode(),
    path_in_repo='README.md',
    repo_id=f'YourUsername/{target_model}',
    repo_type='model',
    commit_message='docs: add House of Sak narrative to model card'
)
```

After upload, verify every marker renders:
```python
path = hf_hub_download(f'YourUsername/{target_model}', 'README.md')
verified = open(path).read()
for marker_name, check_fn in markers.items():
    assert check_fn(verified), f'{marker_name} missing after upload'
```

### 7. Record

Log in `LEARNING_JOURNAL.md`:
```
## Narrative Consistency Audit — <model-name>

### Cards audited: N | Missing narrative: M
### Enriched: <model> (X → Y chars, +Z)

Markers added:
- house-of-sak YAML tag
- Origin story (shelter, Cork, Beer)
- HoS banner with GitHub + website links

### Remaining gap: <which cards still need fixing>
```

## Common Pitfalls

| Pitfall | Mitigation |
|---------|------------|
| **Adding narrative breaks existing card formatting** | Always read the full card content first, then insert the narrative section at the top (after title/badges, before technical sections). Don't remove or reorder existing sections. |
| **Narrative section duplicates on re-run** | Guard with `if 'House of Sak' not in content:` before inserting. |
| **YAML validation fails on upload** | Use `create_commit` with `CommitOperationAdd` instead of `upload_file` to catch YAML errors early. The `base_model` field is especially strict — must be a valid HF model ID. |
| **Security scanner blocks emoji** | Write the card to a file first, then upload via Python — don't pipe inline heredocs with emoji through `terminal()`. |
| **Card size grows large** | Narrative section adds ~1,000–1,500 chars. Check the card doesn't exceed HF's README size limits (typically fine under 20KB). |
| **Forgetting to preserve technical content** | Before/after diff: verify that all original sections (Usage, Benchmarks, Family Links, File Structure) still appear in the output. |
| **Narrative text embeds stale asset counts** | The narrative section (tables, bullet lists) may contain hardcoded model/dataset/Space counts or download totals. When repos are deleted, made private, or added, these counts silently drift from API reality — no CI catches it. Always verify every hardcoded count against live `api.list_models()`, `api.list_datasets()`, and `api.list_spaces()` before uploading. Prefer dynamic badges (`img.shields.io/endpoint`) over hardcoded numbers when possible. Sanity-check: if your narrative says "14 models" but the API returns 12, fix the text — don't just update the badge. |

## Expected Impact

| Metric | Expected change |
|--------|----------------|
| Card completeness | 0/8 → 8/8 narrative markers |
| Emotional connection | Readers understand "why this exists", not just "what it does" |
| Cross-linking | GitHub + House of Sak website appear in every card |
| Downloads | Indirect — cards alone don't drive traffic, but consistent branding builds trust |
