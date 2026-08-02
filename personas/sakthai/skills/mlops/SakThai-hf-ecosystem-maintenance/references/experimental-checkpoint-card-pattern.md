# Experimental Checkpoint Card Pattern

Pattern for replacing auto-generated "Model Card for Model ID" boilerplate on **training sweep checkpoints** (experimental models from LoRA-rank sweeps, epoch comparisons, learning-rate grids). These are NOT production models — the card must clearly communicate "intermediate artifact" while still being discoverable and useful.

## When to Use

- Model name contains `exp-` (e.g., `sakthai-context-0.5b-exp-lora-masked-v2`)
- Card is the auto-generated HF template: "Model Card for Model ID" with `[More Information Needed]` in every section
- YAML frontmatter has only `library_name: transformers` and `tags: [trl, sft]` — no license, no base_model, no datasets, no pipeline_tag
- Model has 0 downloads and is part of a known experiment sweep (multiple variants differing by rank, epochs, LR, etc.)

## Card Structure

### 1. YAML Frontmatter

Replace the bare-minimum auto-generated frontmatter:

```yaml
# BEFORE (auto-generated):
---
library_name: transformers
tags:
- trl
- sft
---

# AFTER:
---
library_name: transformers
tags:
- trl
- sft
- sakthai
- house-of-sak
- qwen2.5
- fine-tune
- experimental
- context-model
- lora              # or full-finetune
license: apache-2.0
language:
- en
pipeline_tag: text-generation
base_model: Qwen/Qwen2.5-0.5B-Instruct   # or whatever the base model is
datasets:
- Nanthasit/sakthai-combined-v6
- Nanthasit/sakthai-combined-v7
- Nanthasit/sakthai-irrelevance-supplement
---
```

**Mandatory additions:**
- `license:` — set explicitly (Apache-2.0 for most SakThai work)
- `pipeline_tag:` — enables HF search filtering (e.g., `text-generation`)
- `base_model:` — critical for attribution; links back to the foundational model
- `datasets:` — enables dataset-filtered search; list ALL training datasets used
- `language:` — ISO code(s)

### 2. Badge Bar

```markdown
<p align="center">
  <a href="https://huggingface.co/collections/author/collection-id"><img src="https://img.shields.io/badge/🏠-SakThai%20Family-6644cc" alt="Collection"/></a>
  <a href="https://huggingface.co/author/production-model"><img src="https://img.shields.io/badge/⬆️-Upstream-47d147" alt="Upstream"/></a>
  <img src="https://img.shields.io/badge/status-experimental-orange" alt="Experimental"/>
  <img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="Apache 2.0"/>
  <a href="https://huggingface.co/author?search_models=exp-prefix"><img src="https://img.shields.io/badge/🔬-Sibling%20Experiments-blue" alt="Sibling Experiments"/></a>
</p>
```

Badges needed:
| Badge | Purpose | Static/Dynamic |
|-------|---------|:-------------:|
| Collection | Links to the family collection hub | Static |
| Upstream | Links to the production merged model | Static |
| Experimental | Orange badge signals "not production" | Static |
| License | Apache-2.0 or whatever applies | Static |
| Sibling Experiments | Search link to all experiment variants | Static |

### 3. Warning Banner

```markdown
> **Experimental training checkpoint** from the [family name] [model scale] context model development pipeline.
> This is an intermediate artifact — for production use see
> [production-model-name](https://huggingface.co/author/production-model).
```

Place this right after the title/badges, before any technical content. The message must:
- Use **bold** for "Experimental training checkpoint"
- State what kind of training this is (LoRA SFT, full SFT, etc.)
- Link to the production merged model
- Use a blockquote to visually distinguish from normal card content

### 4. Description Paragraph

Two purposes: (a) identify what this specific variant is, and (b) state why it's published.

```markdown
A **LoRA SFT fine-tune** (r=16) of `Qwen/Qwen2.5-0.5B-Instruct`, trained on the
SakThai tool-calling dataset with **masked loss** — only assistant turns are trained,
user/system turns are masked out. Part of a sweep comparing full fine-tune vs. LoRA
at multiple ranks and learning rates for the 0.5B scale.

**This is NOT a production model.** It is published for:
- Reproducibility of the SakThai training pipeline
- Comparison across the [scale] experiment family
- Continued training / checkpoint stacking
```

### 5. Experiment Family Table

The most important section. Shows ALL variants in the sweep so a visitor can compare at a glance:

```markdown
## Experiment family

| Variant | Type | Key params |
|---------|------|-----------|
| `full-masked-v2` | Full SFT | All params, masked loss |
| **`lora-masked-v2`** | **LoRA** | **r=16, default LR ← you are here** |
| `lora-masked-v2s2` | LoRA | r=16, LR step schedule |
| `lora-masked-v2e6` | LoRA | r=16, 6 epochs |
| `lora-masked-v2e6lr` | LoRA | r=16, 6 epochs, adjusted LR |
| `lora-masked-v2r32` | LoRA | r=32 |
| `lora-masked-v2r64` | LoRA | r=64 |
| `lora-masked-v2len` | LoRA | Length-weighted sampling |

The best-performing variant was merged into
[production-model](https://huggingface.co/author/production-model)
(GGUF quantized for CPU inference).
```

**Requirements:**
- **Bold + marker** for the current variant ("← you are here")
- Every variant in the sweep must be listed (even if some don't have cards yet)
- Include the "best performed → merged into" line at the bottom linking to the production model
- Key params column should be specific (r=16, not just "LoRA")

### 6. Training Details

Adapted from the production model's documentation:

```markdown
## Training details

- **Base model:** [Qwen/Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
- **Framework:** TRL `SFTTrainer` + Hugging Face Transformers + PEFT LoRA
- **LoRA rank:** r=16
- **Target modules:** q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
- **LoRA alpha:** 32
- **LoRA dropout:** 0.05
- **Dataset:** [sakthai-combined-v7](https://huggingface.co/datasets/author/sakthai-combined-v7) (N examples)
- **Loss masking:** Only assistant responses contribute to loss
- **Optimizer:** AdamW (lr=2e-4, linear schedule)
- **Hardware:** Free Kaggle GPU (T4 x2, 16 GB VRAM each)
```

Include only what's known. If a hyperparameter isn't recorded, omit it rather than guessing.

### 7. Usage Example

Since these are PEFT adapters (not merged models), the usage example must show how to load adapter weights:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")

# Load LoRA adapter
model = PeftModel.from_pretrained(base, "Nanthasit/this-experiment-repo")
```

Then add a note pointing to the production model for real use:

```bash
# For CPU-friendly production inference, use the GGUF-quantized model:
ollama pull hf.co/Nanthasit/sakthai-context-0.5b-merged
```

### 8. Related Links

```markdown
## Related

- **Production model:** [sakthai-context-0.5b-merged](https://huggingface.co/author/production-model) (N ⬇)
- **Sibling experiments:** [All [scale] checkpoints](https://huggingface.co/author?search_models=exp-prefix)
- **Family collection:** [SakThai Model Family](https://huggingface.co/collections/author/collection-id)
```

### 9. Footer

```markdown
---

<p align="center"><sub>🏠 House of Sak · Built from a shelter in Cork, Ireland on a $0 budget</sub></p>
```

## Git Push Workflow

Since `hf upload` CLI and `HfApi.create_commit()` can fail for various reasons (see `cron-mode-workarounds.md`), use the raw git approach:

```bash
# Clone
HF_TOKEN=$(cat ~/.cache/huggingface/token)
cd /tmp && rm -rf repo_name
GIT_TERMINAL_PROMPT=0 git clone "https://user:$HF_TOKEN@huggingface.co/author/repo-name" repo_name

# Update card
cp /path/to/new_README.md repo_name/README.md

# Commit + push
cd repo_name
git add README.md
git commit -m "Replace auto-generated card with comprehensive README

Summary of changes (3-5 bullet points)."
git push

# Clean up
rm -rf repo_name
```

## Verification

After pushing, verify the card is live via the HF API:

```bash
# Raw README
curl -s "https://huggingface.co/author/repo-name/raw/main/README.md" | head -10

# API metadata
curl -s -o /tmp/verify.json "https://huggingface.co/api/models/author/repo-name"
python3 -c "
import json
with open('/tmp/verify.json') as f:
    d = json.load(f)
print(f'Pipeline: {d.get(\"pipeline_tag\")}')
print(f'License: {d.get(\"cardData\",{}).get(\"license\")}')
print(f'Base model: {d.get(\"cardData\",{}).get(\"base_model\")}')
print(f'Datasets: {d.get(\"cardData\",{}).get(\"datasets\")}')
print(f'SHA: {d.get(\"sha\",\"?\")[:12]}')
"
```

## Do's and Don'ts

**Do:**
- Boldly state "NOT a production model" — prevents misuse
- Include the full experiment family table — context is the main value of this card
- Link to the production model prominently
- Set pipeline_tag in YAML — makes the model searchable
- Use `PeftModel.from_pretrained()` for usage examples (not `AutoModel` directly)

**Don't:**
- Claim benchmark results you haven't run (these are training checkpoints, not eval'd)
- Make the card longer than the production model's card
- Include download-count badges that show 0 — it looks abandoned; omit the badge or use a dynamic one
- Reference deleted sibling models (verify they still exist on HF before linking)

## Real Example

Applied 2026-07-29 to `Nanthasit/sakthai-context-0.5b-exp-lora-masked-v2`:
- Before: 5,180-byte auto-generated boilerplate, `library_name: transformers` only in YAML, no sections populated
- After: 4,569-byte dense card with YAML frontmatter (12 tags), experiment family table, training details, PEFT usage example, badges, cross-links
- Commit: `aed3e0f` — [view on HF](https://huggingface.co/Nanthasit/sakthai-context-0.5b-exp-lora-masked-v2/commit/aed3e0f0f444e10033b40c5265888e8159d5fc7b)
