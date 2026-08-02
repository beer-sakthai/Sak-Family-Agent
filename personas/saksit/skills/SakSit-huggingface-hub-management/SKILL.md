---
name: SakSit-huggingface-hub-management
category: mlops
description: Manage HF repos, model cards, Spaces, audits.
version: 1.3.0
author: SakSit (House of Sak)
tags:
- huggingface
- model-card
- audit
- image-generation
- HF-Spaces
---

# Hugging Face Hub Management

Complete workflow for managing Beer's Hugging Face presence under `Nanthasit` account.

## 🔴 CRITICAL RULES (Never Break)

### Lane: I Am Media, Not Engineer
**SakSit is the storyteller.** My lane: model card content (badges, descriptions, sections, branding), whitepapers, blog posts, social media content, infographics, and documentation. I do NOT touch: training scripts, dataset engineering, GPU configs, benchmark execution, or cloud infrastructure. Those are SakThai's job. If the task involves Python training code, hyperparameter tuning, or model architecture changes — stop and redirect.

### Content Writing Rules
1. **ADD, NEVER REMOVE** — When updating model cards, merge new content (branding, tags) with existing content. Never strip technical details, eval results, usage code, or architecture tables. If user says "bring back" or "more detail" — you stripped content. Fix it immediately.
2. **Cards evolve in stages but aim for v3 on first try** — v1 (branding only ❌), v2 (restored tech ✅), v3 (professional: 11 sections, badges, eval samples, citation ✅). Skip straight to v3. Don't make the user ask three times.
3. **Dual repos need both cards** — When a repo exists in BOTH model and dataset API lists, update both sides: `repo_type='model'` AND `repo_type='dataset'`.
4. **CARE MEANS UNIVERSAL QUALITY** — Every single repo gets the same professional standard: deprecated datasets, old adapters, the profile page, the Space. There is no "this one doesn't matter." If the user says "keep standards for all because we are care" — they mean even the repos you think are too small to bother with. Do not stop fixing when the main models are done.

### Process Rules
5. **FULL AUDIT FIRST** — Always list ALL repos (models + datasets + Spaces) before making changes. Check `api.list_models(author='Nanthasit')`, `api.list_datasets(author='Nanthasit')`, `api.list_spaces(author='Nanthasit')`. Some repos appear in BOTH lists — deduplicate by unique ID.
6. **EACH REPO GETS A CARD** — Every model, dataset, and space should have a proper README.md.
7. **VERIFY TO 100%** — After any batch of updates, run a verification script that checks EVERY repo. Do NOT stop until the script shows zero failures. "Check again 10 time" means run the verification to completion.
8. **GATED ACCESS CHECKING** — `api.model_info(repo_id)` returns data for ANY public model, even without approved access. To confirm real download access, call `api.list_repo_files(repo_id)`. But the definitive source is `huggingface.co/settings/gated-repos`. NEVER claim gated access from model_info() alone.

## Account Info

- **Username:** Nanthasit
- **Token sources (in order of reliability):**
  1. `huggingface_hub` auto-detection (cached login, env vars)
  2. Extract from `/opt/data/.git-credentials`: grep for `Nanthasit` + `huggingface.co`, extract token between last `:` and `@`
  3. `HfApi(token="...")` explicit argument
- **Profile:** https://huggingface.co/Nanthasit
- **Organization Member:** `litert-community` (LiteRT Community, FKA TFLite) — role: contributor

## Prerequisites

```bash
uv venv /tmp/hf-venv
uv pip install --python /tmp/hf-venv/bin/python huggingface-hub
```

## Workflow

### Step 1: Full Audit

```python
from huggingface_hub import HfApi
api = HfApi()

models = list(api.list_models(author='Nanthasit'))
datasets = list(api.list_datasets(author='Nanthasit'))
spaces = list(api.list_spaces(author='Nanthasit'))

print(f"Models: {len(models)}, Datasets: {len(datasets)}, Spaces: {len(spaces)}")

# For each model, list non-README files
for m in models:
    files = api.list_repo_files(m.modelId)
    extras = [f for f in files if f not in ['README.md', '.gitattributes']]
    print(f"{m.modelId}: {len(extras)} extra files, {m.downloads or 0} downloads")
```

### Step 2: Fetch Current README Before Changes

```python
# ALWAYS read the current card before modifying
content = api.hf_hub_download(repo_id='Nanthasit/repo-name', filename='README.md')
with open(content, 'r') as f:
    current = f.read()
# Now MERGE — keep all existing content, add new content
```

### Step 3: Build Merged Card (NEVER strip)

Template structure for every card:
1. Original YAML frontmatter + new tags (house-of-sak, agent)
2. Original description + House of Sak branding header
3. ALL original technical tables (architecture, training, eval)
4. ALL original usage code examples
5. ALL original evaluation results
6. Links to related repos + House of Sak profile

### Step 4: Upload

```python
api.upload_file(
    path_or_fileobj=content.encode(),
    path_in_repo='README.md',
    repo_id='Nanthasit/repo-name',
    repo_type='model',  # or 'dataset'
    commit_message='SakSit: update model card'
)
```

### Step 5: Verify Everything Passes

After ALL cards are uploaded, run a final audit to confirm every repo meets standard:

```python
# Count PASS/FAIL
for repo_id in all_repos:
    score = sum([has_badges, has_hos, has_architecture, has_training,
                 has_eval, has_code, has_links, has_limits, has_citation])
    if score < 6: print(f'FAIL: {repo_id}')
```

Target: 100% pass rate (every repo ≥ 6/9). Do not stop until verified.

## Professional Card Evolution

When upgrading cards, expect three phases:
1. **v1 — Branding only** (WRONG): Adds House of Sak, strips technical detail. ~2-3K chars.
2. **v2 — Restored** (OK): Adds back what was removed. ~3-5K chars.
3. **v3 — Professional** (TARGET): 11 sections, badges, architecture, training, eval with samples, limitations, citation. ~6-10K chars.

ALWAYS aim for v3 on the first try. If user has to ask for "more detail" or "level up" twice, you went to v1 instead of v3.

## Paper & Whitepaper Publishing

**This is core SakSit lane.** Writing papers, blog posts, and documentation is media/storytelling work.

### Workflow
1. **Write the paper** — `PAPER.md` with 11 standard sections (abstract through appendices)
2. **Create a model repo** — `api.create_repo('Nanthasit/{paper-name}', repo_type='model')`
3. **Upload paper** — `api.upload_file(..., path_in_repo='PAPER.md')`
4. **Upload README** — Paper card with badges, abstract, BibTeX citation, links
5. **Verify** — Open the repo URL and confirm renders correctly

### What to include
- House of Sak origin story (this is what makes it unique)
- Sample eval responses with real model outputs
- Proper citations (LoRA, YaRN, Qwen2.5, etc.)
- Broader impact section (the human story)

Full details: `references/paper-publishing-workflow.md`

## Collection Management (HF Collections)

Collections are the best way to group related models, datasets, and Spaces for discoverability. They appear on the profile and in search results.

### Available API Methods (`HfApi`)

| Method | Purpose |
|--------|---------|
| `get_collection(slug, token)` | Get collection details + items |
| `add_collection_item(slug, item_id, item_type, note, exists_ok, token)` | Add item to collection |
| `delete_collection_item(slug, item_id, item_type, token)` | Remove item |
| `update_collection_metadata(slug, title=None, description=None, token)` | Update title/description |
| `create_collection(title, namespace, description, token)` | Create new collection |
| `list_collections(owner, token)` | List all collections for an owner |

**Slug format:** `owner/title-slug-uuid` — always retrieve via `get_collection()` to get the exact slug.

### Collection Slug Discovery

To find existing collections for an account:

```python
collections = api.list_collections(owner='Nanthasit', token=token)
for c in collections:
    print(f"{c.slug}: {c.title} ({c.item_count} items)")
```

The `slug` from `list_collections` is what you pass to `get_collection`.

### Adding Items

```python
api.add_collection_item(
    collection_slug="Nanthasit/sakthai-model-family-...",
    item_id="Nanthasit/sakthai-context-1.5b-merged",
    item_type="model",          # "model", "dataset", "space", "paper", "collection"
    note="Flagship — most downloaded",  # optional, max 500 chars
    exists_ok=True,             # don't error if already added
    token=token
)
```

`item_type` must be one of: `"model"`, `"dataset"`, `"space"`, `"paper"`, `"collection"`, `"bucket"`.

### Verifying Collection Contents

```python
collection = api.get_collection(slug, token=token)
print(f"{collection.title}: {len(collection.items)} items")
for item in collection.items:
    print(f"  {item.item_id} ({item.item_type})")
```

### Known Limits

- **Collection description: max 150 characters.** Longer descriptions get rejected with a `400 Bad Request`. Keep descriptions concise.
- **Item notes: max 500 characters.** Used for brief context on why an item belongs.
- **Creating collections** requires write token.

## Pre-Update Checklist

Before uploading ANY model card:
- [ ] Read the current README.md first
- [ ] Preserve ALL technical details (architecture, training, eval, usage)
- [ ] Add House of Sak branding as a header, NOT as a replacement
- [ ] Add new tags (house-of-sak, agent, function-calling) to frontmatter
- [ ] Verify content is longer/more detailed, not shorter
- [ ] Check ALL repos (models + datasets + spaces), not just a subset

## Level Up Workflow (when user says "level up" or "more detail")

When told to improve a card, follow this sequence:

1. **Open the reference card** — The best example is `Nanthasit/sakthai-context-0.5b-merged` (9/9, 8.2K chars). Compare the target card against it section by section.
2. **Check each missing section** — Architecture table, training hyperparams, eval with sample responses, limitations, citation, badges, links.
3. **Build the merged card** — Read the current README.md first, preserve EVERYTHING, add missing sections. Do NOT strip any existing content.
4. **Push and verify** — Upload, then re-read to confirm it's longer, not shorter.

Failure pattern: treating level-up as "replace" rather than "add to existing." The 0.5B card is the quality benchmark.

## Professional Card Template

### 1. YAML Frontmatter
license, language, library_name, pipeline_tag, tags (+house-of-sak, agent), datasets, base_model, model-index with eval metrics.

### 2. Badges
Shields.io: HF profile, GitHub, House of Sak, license, download count.

### 3. Model Description
Paragraph: base model, purpose, key capability. Include House of Sak origin.

### 4. Quick Start
Copy-paste Python code snippet for inference.

### 5. Architecture Table
Params, hidden size, layers, attention heads, intermediate size, vocab, context, activation, precision.

### 6. Training Hyperparameters
LoRA r/alpha/dropout, target modules, dataset size, epochs, steps, duration, optimizer, LR, compute.

### 7. Evaluation Results
Full tables from eval/ + comparison vs base model.

### 8. Sample Responses
Table of actual model outputs for test cases.

### 9. Limitations & Biases
Size constraints, data scope, language support, safety.

### 10. Citation (BibTeX)

### 11. Links Table
| Resource | Link |

## Pitfalls

1. **Never use `upload_file` with stripped content** — always merge with existing.
2. **Models and datasets use different repo_type** — 'model' vs 'dataset'.
3. **Space URLs** cannot be modified via the API — only model/dataset READMEs.
4. **Git push is deprecated** by Hugging Face (Python library recommended), **but still works** if you have `.git-credentials` configured. Prefer `api.upload_file()` for new work; use git clone + commit + push as fallback when the Python library isn't available or auth scope is narrower.
5. **Token scope** — The token may have write access for models but not datasets (check first). If `api.upload_file()` fails with 401/403 for datasets, extract the Nanthasit token from `/opt/data/.git-credentials`: `token = line.split(':', 2)[-1].split('@')[0]` where line contains both `Nanthasit` and `huggingface.co`. Multiple HF tokens may be in that file — use the correct one.
6. **eval/ files** contain detailed benchmark results — reference them in the card but don't duplicate them entirely (link to the files).
7. **Some repos are dual-listed** (appear in BOTH model and dataset APIs). Always check both lists and deduplicate.
8. **Gated access from `list_repo_files()` can still be a false positive** — the HF settings page at `huggingface.co/settings/gated-repos` is the definitive source of truth.
9. **Partial-fix trap** — Fixing the main models and leaving "small" repos undone will get called out. Do NOT stop at 80% complete. Every single repo gets the same standard. If the verification script shows any FAIL repos, keep fixing until 100% pass.
10. **Profile repo uses different standard** — `Nanthasit/Nanthasit` is a personal profile, not a model. It needs badges, HoS branding, and links but NOT architecture/eval/citation. Don't apply the 11-section template to it. Adapters (tools repos) need 5-7/9, not the full 11-section treatment.
11. **Collection description: max 150 characters** — `update_collection_metadata()` rejects longer descriptions with HTTP 400. Keep it tight.
12. **Collection contents may pre-exist** — A collection that appears empty in the listing API (`item_count=0`) may already have items visible in `get_collection()`. Always verify with the detail endpoint before assuming emptiness.
13. **HF token in env may not be exported to agent shell** — The credential store references `source: env:HF_TOKEN` but the env var isn't always in the agent's subprocess environment. When `hf` CLI or `huggingface_hub` can't auth, extract from `.git-credentials` as a fallback, or use `HfApi(token="...")` explicitly.
14. **Story inaccuracies can persist** — When doing a story pass across many repos, search for "Thailand" specifically — earlier dataset cards misstated the shelter location (Thailand → Cork, Ireland). Always verify location facts when editing story sections.

## Reference Files
- `references/professional-card-template.md` — 11-section card template with validation
- `references/paper-publishing-workflow.md` — Publish whitepapers on HF (create repo, upload PAPER.md, add badge README with citation)
- `references/jul23-2026-session-log.md` — Session learnings, what went wrong, gated model list
