---
name: SakSit-huggingface-hub-management
category: mlops
description: "Manage Hugging Face repos (models, datasets, Spaces) — update model cards, audit all repos, generate images via free HF Spaces. CRITICAL: never strip existing content when updating."
version: 1.1.0
author: SakSit (House of Sak)
tags: [huggingface, model-card, audit, image-generation, HF-Spaces]
---

# Hugging Face Hub Management

Complete workflow for managing Beer's Hugging Face presence under `Nanthasit` account.

## 🔴 CRITICAL RULES (Never Break)

1. **ADD, NEVER REMOVE** — When updating model cards, merge new content (branding, tags) with existing content. Never strip technical details, eval results, usage code, or architecture tables.
2. **FULL AUDIT FIRST** — Always list ALL repos (models + datasets + Spaces) before making any changes. Check `list_models(author='Nanthasit')`, `list_datasets(author='Nanthasit')`, `list_spaces(author='Nanthasit')`. Note: some repos appear in BOTH model AND dataset lists (e.g. simple tool-calling datasets) — deduplicate by counting unique IDs.
3. **EACH REPO GETS A CARD** — Every model, dataset, and space should have a proper README.md with at minimum: description, tags, usage example, and House of Sak branding.
4. **VALIDATE BEFORE PUSH** — Always call `card.validate()` before uploading to catch missing metadata.
5. **VERIFY GATED ACCESS VIA FILE LISTING** — `model_info()` returns data for ANY public model, even without approved access. To confirm download access, call `list_repo_files(repo_id)` — this only succeeds if gated approval is active. NEVER claim gated access from model_info() alone.

## Account Info

- **Username:** Nanthasit
- **Token:** From `/opt/data/.env` as `HF_TOKEN` (role: write)
- **Profile:** https://huggingface.co/Nanthasit

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

## Free Image Generation via HF Spaces

### Primary: FLUX.1-schnell (black-forest-labs)

```python
from gradio_client import Client
client = Client('black-forest-labs/FLUX.1-schnell')
result, seed = client.predict(
    prompt="Your prompt here",
    seed=0, randomize_seed=True,
    width=1344, height=768,
    num_inference_steps=4,
    api_name='/infer'
)
# result is a local file path to the generated image
```

**API Endpoint:** `predict(prompt, seed, randomize_seed, width, height, num_inference_steps, api_name='/infer')`

### ZeroGPU Quota Handling
This Space uses ZeroGPU free tier. The error means exhausted:
> `AppError: You have exceeded your ZeroGPU quota (90s requested vs. 0s left)`

**Fixes:**
1. Wait ~24h for quota reset (no workaround on free tier)
2. Use HF_TOKEN for more quota (set `HF_TOKEN` env var before client init)
3. **Fallback Spaces** (try these when primary is quota'd):
   - `black-forest-labs/FLUX.1-schnell` (primary, 5K likes)
   - `Deddy/Unlimited_FLUX_Schnell_V1-3` (may be offline)
   - `Nymbo/FLUX.1-Schnell-Serverless` (may be offline)
   - Search: `api.list_spaces(search='flux+schnell')`

**Limitations:**
- ZeroGPU quota: ~90s generation time per session
- 4 inference steps recommended for speed
- Results are temporary local files — must be saved/copied before session ends

## Pre-Update Checklist

Before uploading ANY model card:
- [ ] Read the current README.md first
- [ ] Preserve ALL technical details (architecture, training, eval, usage)
- [ ] Add House of Sak branding as a header, NOT as a replacement
- [ ] Add new tags (house-of-sak, agent, function-calling) to frontmatter
- [ ] Verify content is longer/more detailed, not shorter
- [ ] Check ALL repos (models + datasets + spaces), not just a subset

## Professional Card Template

Every model card needs these 11 sections to be professional-grade (matching Qwen/Mistral card quality):

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
4. **Git push is deprecated** by Hugging Face — use `huggingface_hub` Python library.
5. **Token scope** — The token may have write access for models but not datasets (check first).
6. **eval/ files** contain detailed benchmark results — reference them in the card but don't duplicate them entirely (link to the files).
7. **Some repos are dual-listed** (appear in BOTH model and dataset APIs). Always check both lists and deduplicate.
8. **Gated access from `list_repo_files()` can still be a false positive** — the HF settings page at `huggingface.co/settings/gated-repos` is the definitive source of truth.

## Reference Files
- `references/professional-card-template.md` — 11-section card template with validation
- `references/jul23-2026-session-log.md` — Session learnings, what went wrong, gated model list
