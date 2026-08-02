# Training Plan Workflow — HF CLI Asset Discovery

Quick-reference commands for the Pre-Flight audit phase before planning any training run.

## Authentication

```bash
# Check current user
hf auth whoami

# Token location: ~/.cache/huggingface/token
```

## Model Survey

```bash
# List all models by user, JSON for machine parsing
hf models list --author <username> --format json

# Get detailed info on a specific model
curl -s -H "Authorization: Bearer $(cat ~/.cache/huggingface/token)" \
  "https://huggingface.co/api/models/<username>/<model-name>" | jq .

# Key fields to inspect:
# - tags: contains 'dataset:' to see training lineage
# - cardData.model-index: evaluation results
# - siblings: files in the repo
# - pipeline_tag: 'text-generation', 'feature-extraction', etc.
```

## Dataset Survey

```bash
# List all datasets by user
hf datasets list --author <username> --format json

# Get detailed info — critical for discovering embedded assets
hf datasets info <username>/<dataset>

# The 'siblings' array shows all files. Key paths to look for:
# - notebooks/*.ipynb        — pre-built training notebooks
# - scripts/*.py             — training/validation scripts
# - benchmark/*.ipynb        — benchmark notebooks
# - data/train.jsonl         — actual training data
# - data/test.jsonl          — actual test data

# Download specific files from a dataset repo
hf download --type dataset <username>/<dataset> <file-path>

# Example: download the v7 Colab notebook
hf download --type dataset Nanthasit/sakthai-combined-v6 \
  notebooks/train_sakthai_v7_colab.ipynb
```

## GPU Cost Verification

```bash
# List all hardware flavors with costs
hf jobs hardware

# Free GPU options (verified):
# - Google Colab Free: T4 GPU, ~1hr sessions, may disconnect
# - Kaggle: T4/P100, 30 hrs/week, more reliable
#
# HF Jobs (all cost money — no free GPU tier):
# - t4-small:  $0.40/hr  ← cheapest GPU
# - t4-medium: $0.60/hr
# - a10g, a100, h200: $1–40/hr
```

## Notebook Inspection (Colab Unsloth QLoRA for 7B on T4)

When you find a pre-built notebook in a dataset, inspect these cells:

| Cell | What to check |
|------|---------------|
| Install deps | `unsloth`, `trl>=0.12.0`, `peft`, `bitsandbytes` |
| Auth | Reads `HF_TOKEN` from Colab secrets (key icon) |
| Dataset loading | Uses `hf_hub_download` raw JSONL, not `datasets.load_dataset` (avoids Arrow schema explosion) |
| Render function | Converts OpenAI JSON-string arguments → dicts before `apply_chat_template` |
| Model loading | `FastLanguageModel.from_pretrained(4-bit)` — typically `unsloth/Qwen2.5-7B-Instruct-bnb-4bit` |
| LoRA config | `target_modules` = all linear layers: `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` |
| Training args | `batch=2`, `grad_accum=8`, `epochs=3`, `lr=2e-4`, cosine schedule, `max_seq_length=3072` |
| Push | Pushes adapter to target repo before merge (safe even if Colab disconnects) |
| Smoke test | Quick tool-call + direct-answer verification |

Training time estimates (T4 16GB): 7B = 60–90 min, 1.5B = 15–20 min, 0.5B = 5–8 min.

## Plan Presentation Template

Use this structure when presenting training options:

```markdown
### Option <Name>

- **Cost:** $0 / $<amount>
- **GPU:** <type>
- **Duration:** ~<time>
- **Method:** QLoRA on <base model>
- **Steps:** <2-3 key steps>
- **Output:** <target adapter repo>
- **Success prob:** ~<XX>%
- **Risk:** <main risk>
```

## Beer's Decision Rules (captured from sessions)

- Always provide expected success probability (%) and cost estimate before run
- "Plan first, run after" — present options with tradeoffs, let Beer decide
- Zero-cost only — if a GPU option costs money, skip or flag clearly
- HF-first: when in doubt about approach, prioritize Hugging Face ecosystem
