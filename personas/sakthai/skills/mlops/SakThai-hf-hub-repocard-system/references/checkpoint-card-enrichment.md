# Checkpoint / Experimental Model Card Enrichment

Improving model cards for **training checkpoints and experimental artifacts** that have auto-generated blank READMEs ("Model Card for Model ID — More Information Needed").

## When to use

Training runs pushed to Hugging Face via TRL `SFTTrainer`, `push_to_hub`, or similar generate repos with:

- Auto-generated YAML frontmatter (minimal: `library_name: transformers`, `tags: [trl, sft]`)
- Blank README body with placeholder text everywhere
- 0 downloads (undiscoverable)
- No cross-links to sibling repos, production models, or ecosystem

These repos exist on the Hub but are effectively invisible. A proper card (even 300 words) improves discoverability and prevents confusion.

## Checkpoint Card Anatomy

Every checkpoint card should have these sections:

### 1. YAML Frontmatter

Replace the minimal auto-generated frontmatter:

```yaml
# Before (auto-generated — minimal)
---
library_name: transformers
tags:
- trl
- sft
---

# After (properly enriched)
---
library_name: transformers
tags:
- trl
- sft
- sakthai
- house-of-sak
- experimental
- fine-tune
license: apache-2.0
language:
- en
pipeline_tag: text-generation
base_model: Qwen/Qwen2.5-0.5B-Instruct
datasets:
- Nanthasit/sakthai-combined-v6
- Nanthasit/sakthai-combined-v7
---
```

**Key additions over the template:**
- `license` — always add one (SPDX identifier)
- `base_model` — must be a valid HF model ID, not a description string
- `pipeline_tag` — match the original base model's tag
- `datasets` — link training data repos (bidirectional discoverability)
- Tags: `experimental`, `fine-tune`, ecosystem tags (`sakthai`, `house-of-sak`)

### 2. Badge Row

Standard badges for checkpoint cards:

```markdown
<p align="center">
  <a href="https://huggingface.co/collections/org/slug"><img src="https://img.shields.io/badge/🏠-Family%20Collection-6644cc" alt="Collection"/></a>
  <a href="https://huggingface.co/org/production-model"><img src="https://img.shields.io/badge/⬆️-Upstream-47d147" alt="Production"/></a>
  <img src="https://img.shields.io/badge/status-experimental-orange" alt="Experimental"/>
  <img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="License"/>
</p>
```

### 3. Status Banner

A prominent blockquote at the top clarifying the repo's purpose:

```markdown
> **Experimental training checkpoint** from the [Production Model Name] development pipeline.
> Full-parameter SFT (not LoRA) of [Base Model] with masked loss on tool-calling data.
> This is an **intermediate artifact** — for production use see
> [Production Model](https://huggingface.co/org/production-model).
```

**Why:** Without this, visitors reaching the page from search results may think it's the main model. The banner prevents wasted downloads and confusion.

### 4. Experiment Family Table

If the checkpoint is one of a sweep, list all variants:

```markdown
## Experiment family

| Variant | Type | Key params |
|---------|------|-----------|
| `full-masked-v2` | Full SFT | All params, masked loss |
| `lora-masked-v2` | LoRA | r=16, default LR |
| `lora-masked-v2e6` | LoRA | r=16, 6 epochs |
| `lora-masked-v2r32` | LoRA | r=32 |
| `lora-masked-v2r64` | LoRA | r=64 |

The best-performing variant was merged into
[Production Model](https://huggingface.co/org/production-model)
(GGUF quantized for CPU inference).
```

**Benefits:**
- Shows the work was systematic, not random
- Helps other researchers reproduce or extend the sweep
- Directs visitors to the best variant (production model)

### 5. Training Details

```markdown
## Training details

- **Base model:** [Base Model](https://huggingface.co/org/base-model)
- **Framework:** TRL `SFTTrainer` + Hugging Face Transformers
- **Dataset:** [Training Dataset](https://huggingface.co/datasets/org/dataset)
- **Loss masking:** Only assistant responses contribute to loss
- **Hardware:** Free Kaggle GPU (T4 x2, 16 GB VRAM each)
```

Keep this concise — it's a checkpoint card, not a paper. Training code and config should be in the experiment repo, not the card.

### 6. Usage

A minimal loading example:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("org/checkpoint-name")
tokenizer = AutoTokenizer.from_pretrained("org/checkpoint-name")
```

Then redirect to the production model:

```bash
# For CPU-friendly inference, use the production model:
ollama pull hf.co/org/production-model
```

### 7. Related Links

```markdown
## Related

- **Production model:** [Model Name](https://huggingface.co/org/production-model) (N ↓)
- **Sibling experiments:** [All checkpoints](https://huggingface.co/org?search_models=exp-)
- **Family collection:** [Model Family](https://huggingface.co/collections/org/slug)
```

## Example: Full Card

See the `sakthai-context-0.5b-exp-full-masked-v2` card (commit `e51fb60`) for the canonical example of a checkpoint card enrichment featuring:
- All 7 sections above present
- 8-variant experiment family table
- Clear "not production" disclaimer in blockquote
- Dataset cross-links (3 repos)
- Badges: collection, upstream, experimental status, license

## Cron-Mode Workflow

When running as a cron job (no user present):

```bash
# 1. Check current card
curl -s -o /tmp/card.md "https://huggingface.co/org/checkpoint/raw/main/README.md"

# 2. Write enriched card to /opt/data (NOT /tmp — write_file blocks /tmp)
write_file("/opt/data/new_card.md", enriched_content)

# 3. Upload via huggingface_hub
python3 -c "
from huggingface_hub import HfApi
api = HfApi()
with open('/opt/data/new_card.md') as f:
    content = f.read()
resp = api.upload_file(
    path_or_fileobj=content.encode(),
    path_in_repo='README.md',
    repo_id='org/checkpoint',
    repo_type='model',
    commit_message='Add proper model card: experiment context, family table, cross-links'
)
print(f'Uploaded: {resp}')
"

# 4. Verify
curl -s "https://huggingface.co/org/checkpoint/raw/main/README.md" | head -5
```

## Pitfalls

- **`base_model` must be a valid HF model ID.** The validation rejects names like "Kokoro 82M" or "Qwen2.5" — use `Qwen/Qwen2.5-0.5B-Instruct` format. If no parent model exists on the Hub, omit the field entirely.
- **Do NOT set `verified: true` in model-index** for checkpoint cards. These are training artifacts, not evaluated models. If adding model-index, use `verified: false` with upstream scores only.
- **Family table variant names should be consistent.** Use the exact repo suffix (e.g. `v2`, `r32`, `e6`) so researchers can find the matching weights on the Hub.
- **Don't over-promise.** The usage example should note this is NOT for CPU inference (it's raw PyTorch weights) and redirect to the production GGUF model.
- **Set `tags: [experimental]`** so the model can be filtered out by users looking for production models only.
