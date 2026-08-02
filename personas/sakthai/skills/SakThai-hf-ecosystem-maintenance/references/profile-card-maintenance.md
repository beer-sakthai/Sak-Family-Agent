# Profile/Gateway Card Maintenance

**Target:** The author profile model card (e.g., `Nanthasit/Nanthasit`), which serves as the ecosystem gateway / landing page.

## Why Profile Cards Matter

Unlike regular model cards, the profile card:
- Has **0 downloads by design** — it's a profile, not a downloadable model. This means it won't appear in "low downloads" promotion targets or sorted-by-downloads lists.
- Is the **first page visitors see** when clicking the author name on any model/dataset/space page.
- Contains an **ecosystem summary** (model count, dataset count, download badges, family table) that drives discovery of **all** sibling assets.
- Stale stats here are **multiplier-negative** — they underrepresent the whole portfolio, not just one asset.

## Signal: When to Target the Profile Card

Run a profile card update when **any** of these are true:

| Signal | Example |
|--------|---------|
| Model count in profile badges/counts doesn't match API reality | Badge says `12 models` but API returns 14 |
| Dataset count is stale | Badge says `5 datasets` but API lists 6 |
| Grouped/abbreviated model rows hide individual assets | One row `context-{7b,1.5b,0.5b}-tools` instead of 4 separate rows |
| Missing entries for new siblings | A new LoRA adapter or dataset was published but never added to the profile table |
| Zero-download siblings have no dedicated row | `sakthai-context-0.5b-tools-v2` (0 dl) shares a generic row with other adapters |
| Total downloads counter is stale | Badge says `4.1K+` but actual sum is different |

## Workflow

### 1. Audit Current State

Fetch live counts from the HF API:

```bash
python3 -c "
from huggingface_hub import HfApi
api = HfApi()
models = list(api.list_models(author='Nanthasit'))
datasets = list(api.list_datasets(author='Nanthasit'))
total_dl = sum(m.downloads or 0 for m in models)
print(f'Models: {len(models)} (real models)')
print(f'Datasets: {len(datasets)}')
print(f'Total downloads: {total_dl}')
for m in sorted(models, key=lambda x: x.downloads or 0):
    print(f'  {m.downloads or 0:>5} | {m.id.split(\"/\")[1]}')
for d in sorted(datasets, key=lambda x: x.downloads or 0):
    print(f'  DS | {d.id.split(\"/\")[1]} | {d.downloads or 0}')
"
```

### 2. Identify Stale Assets in the Profile Card

Download the current profile README and scan for:

**0. URL validation — verify every family-table URL resolves.** Models get renamed or deleted between cron cycles. Check each row's URL:

```bash
for model in "sakthai-context-1.5b-merged" "sakthai-context-0.5b-tools" "sakthai-context-0.5b-exp-lora-masked-v4"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://huggingface.co/api/models/Nanthasit/$model")
  [ "$code" != "200" ] && echo "❌ $model ($code — may not exist)"
done
```

Also check dataset and Space URLs with their respective API endpoints. If any return 401/404 (with auth token), flag them for replacement or removal. See `references/deleted-repo-cleanup-sweep.md` for the full `check_repo` workflow and cascade-cleanup pattern.

Then continue with the standard staleness scan:

1. **Badge counts**: `img.shields.io/badge/models-N-blue` — does N match the API count?
2. **Stats table**: `| Models | N |`, `| Datasets | N |` — do they match?
3. **Section header**: `**N models · M datasets · P Spaces**` — check all 3 numbers.
4. **Grouped rows**: Any row like `context-{7b,1.5b,0.5b}-tools` that combines multiple siblings into one. These hide individual download stats and suppress discovery of zero-download models.
5. **Missing entries**: New adapters, datasets, or spaces that were published after the profile card was last edited.
6. **Total downloads**: `downloads-XXK%2B` badge — is it within range?

### 3. Fix Strategy

Apply changes in order of impact:

#### a) Badges (highest visibility)
Update the `img.shields.io/badge/` URLs in the badge row. Profile cards typically have 4 badges: models, datasets, spaces, downloads.

```markdown
<!-- Before -->
<img src="https://img.shields.io/badge/models-12-blue" alt="12 models"/>
<img src="https://img.shields.io/badge/datasets-5-ff69b4" alt="Datasets"/>

<!-- After -->
<img src="https://img.shields.io/badge/models-14-blue" alt="14 models"/>
<img src="https://img.shields.io/badge/datasets-6-ff69b4" alt="Datasets"/>
```

#### b) Stats table
Update the Metrics table rows:

```markdown
<!-- Before -->
| Models | 12 |
| Datasets | 5 |

<!-- After -->
| Models | 14 |
| Datasets | 6 |
```

#### c) Section header
Update the claim in the Model Family section header:

```markdown
<!-- Before -->
**12 models · 5 datasets · 3 Spaces**

<!-- After -->
**14 models · 6 datasets · 3 Spaces**
```

#### d) Expand grouped rows (highest impact for low-download promotion)

Replace a single combined row with individual rows. Include download-count-context when applicable (the profile card doesn't always show counts, but the separate row itself is the promotion):

```markdown
<!-- Before: single grouped row -->
| [context-{7b,1.5b,0.5b}-tools](...) | LoRA | Tool-calling adapters |

<!-- After: individual rows with rank context -->
| [context-7b-tools](...) | LoRA (r=16) | Full-size tool-calling adapter |
| [context-1.5b-tools](...) | LoRA (r=8) | Mid-size tool-calling adapter 🏆 |
| [context-0.5b-exp-lora-masked-v4](...) | LoRA (r=8) | Experimental masked-LoRA adapter |
| [context-0.5b-tools](...) | LoRA (r=8) | Original edge tool-calling adapter |
```

The **ordering principle**: list larger/better models first (7B → 1.5B → 0.5B), and within the same size, put the newer version before the older one. Mark the most popular sibling with 🏆.

#### e) Add missing entries

Check the profile table against the API listing. Every public model and dataset should appear:

| Missing type | Reason it's often missing |
|:-------------|---------------------------|
| New LoRA adapter (e.g., v2) | Published after profile card was last edited |
| Monolingual embedding model | Overshadowed by the multilingual sibling |
| New dataset (e.g., combined-v7) | Published as part of a dataset iteration |
| New Space | Created outside the profile-update workflow |

Add each with a short description and size (if applicable).

### 4. Upload

Use `api.upload_file()` for the full profile card rewrite:

```python
api.upload_file(
    path_or_fileobj=updated_readme.encode('utf-8'),
    path_in_repo="README.md",
    repo_id="Nanthasit/Nanthasit",
    repo_type="model",
    commit_message="Update profile: N models, M datasets, add v2/v7 cross-links"
)
```

**Note:** The profile repo has type `model` even though it contains no model weights. It's a model card acting as a landing page.

### 5. Verify

After upload, re-fetch and check every changed element:

```python
from huggingface_hub import HfApi
api = HfApi()
readme = api.hf_hub_download('Nanthasit/Nanthasit', 'README.md')
with open(readme) as f:
    content = f.read()

checks = [
    ('models-14', 'models badge'),
    ('datasets-6-ff69b4', 'datasets badge'),
    ('| Models | 14 |', 'models stat'),
    ('| Datasets | 6 |', 'datasets stat'),
    ('14 models · 6 datasets', 'header'),
    ('context-0.5b-exp-lora-masked-v4', 'exp-lora in models table'),
    ('context-0.5b-tools](', 'v1 in table'),
    ('sakthai-combined-v7', 'v7 in datasets'),
    ('embedding](', 'embedding model'),
]
all_ok = True
for needle, label in checks:
    found = needle in content
    if not found:
        all_ok = False
        print(f'❌ {label}')
if all_ok:
    print('✅ All checks pass')
```

### 6. Record

Record the change in LEARNING_JOURNAL.md with:
- The target profile card and its download count (always 0)
- Before/after counts (models, datasets, badges)
- Whether grouped rows were expanded
- Whether new entries were added
- Verification status

## Pitfalls

### Profile card has 0 downloads — don't treat it as a "low-download problem"
The profile card's 0 downloads is by design (it's a profile page, not a downloadable model). Do NOT flag it as a promotion target or a "needs attention" model in ecosystem reports. Its value is as a gateway, not as a downloadable asset.

### Badge updates are easy to miss in the middle of content edits
Profile cards have badges embedded in the badge row alongside GitHub links, collection links, and other badges. When editing, scan the ENTIRE badge row — it's easy to update the stats table and header but miss the badges, leaving the page self-contradictory (body says 14 models, badge says 12).

### Grouped rows compound staleness
A single grouped row like `context-{7b,1.5b,0.5b}-tools` hides not just the individual download counts but also whether each sibling even exists anymore. When you expand grouped rows, you might discover:
- A version that should be deprecated but isn't marked
- A version that was renamed and the old name is orphaned
- A model that accumulated downloads (give it a 🏆 if it outpaced larger siblings)

Check model existence and downloads for EACH sibling before writing the expanded rows.

### Profile cards often list "models" that aren't downloadable
The profile repo itself (`Nanthasit/Nanthasit`) appears in the API as a model with 0 downloads. When computing the "models count" for the profile card, decide whether to include or exclude the profile repo itself. Standard practice: include it in the total count (the badge says `14 models` including the profile page) but don't list it in the family table (it would be circular — linking to itself). Document this decision in the LEARNING_JOURNAL entry so future cron runs don't count it differently.

### If the profile card has a "Story" section, be careful not to disrupt it
Profile cards often have narrative content (origin story, agent descriptions, personal context) that should not be touched during a stats update. When patching, target only the badges, header, stats table, models table, and datasets table. Leave the story, agent descriptions, GitHub links, and footer untouched.

### Sort order matters for the models table
When expanding grouped rows into individual entries, the sort order should be:
1. By parameter size descending: 7B → 1.5B → 0.5B
2. Within same size: merged models before LoRA adapters
3. Within same size and type: newer version before older (v2 before v1)
4. Mark the top performer (by downloads within its peer group) with 🏆

This gives visitors a clear hierarchy from "most capable" to "most portable" and helps them choose.

### Verification must catch ALL stale references
A profile card with 3 stale numbers (badge, body header, stats table) is only 3 `content.replace()` calls to fix, but there are usually 4-5+ locations. Always run a comprehensive check after upload:
1. API value → badge match (e.g., is `models-14` present?)
2. Badge → stats table match (body table says same number as badge)
3. Header → table match (header line says same as table)
4. Family table completeness (every API model listed?)
5. Zero-download presence (were any missing entries added?)

## Related

- `references/card-enrichment-patterns.md` — Thin→rich card enrichment (for regular model cards, not the profile gateway)
- `references/stale-count-detection.md` — Comprehensive stale count scan and fix workflow
- `references/deleted-repo-cleanup-sweep.md` — Mass cleanup when multiple repos are deleted and their links cascade across cards
- `cron-execution-patterns.md` — Cron-safe workflow for ecosystem maintenance runs
