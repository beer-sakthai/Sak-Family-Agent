---
name: SakTan-ops-hf-operations-telemetry
version: 1.1.0
description: Operational reference for Hugging Face Hub telemetry, card updates, evals,
  and collections.
category: operations
tags:
- api
- daily-ops
- datasets
- hf
- huggingface
- models
- operations
- ops
- spaces
- telemetry
---

# Hugging Face Hub Operations & Telemetry

A single operational reference for tracking, inspecting, and managing Nanthasit's Hugging Face
Hub ecosystem. Covers asset inventory, model/dataset card improvements, evaluation results,
and collection curation — operating under $0.00 USD financial spend.

## When to Use

- Listing and auditing models, datasets, and Spaces under `Nanthasit`.
- Checking evaluation YAML files under `.eval_results/`.
- Verifying the `sakthai-model-family` collection status.
- Validating download counts, likes, and pipeline tags.

## Prerequisites

- `HF_TOKEN` in environment or `.env` (required for uploads; optional for public reads).
- Python environment with `huggingface_hub` available via `uv run`.

## 1. Asset Inventory & Telemetry Queries

Query the Hugging Face Hub REST API directly:

```bash
# List all models with downloads and pipeline tag:
curl -s "https://huggingface.co/api/models?author=Nanthasit&sort=lastModified" \
  | python3 -c "import json, sys; [sys.stdout.write(f\"{m['id']:45s} downloads: {m.get('downloads',0):5d} pipeline: {m.get('pipeline_tag','?'):20s}\n\") for m in json.load(sys.stdin)]"

# List all datasets:
curl -s "https://huggingface.co/api/datasets?author=Nanthasit" \
  | python3 -c "import json, sys; [sys.stdout.write(f\"{d['id']:40s} downloads: {d.get('downloads',0):5d}\n\") for d in json.load(sys.stdin)]"

# List all Spaces:
curl -s "https://huggingface.co/api/spaces?author=Nanthasit" \
  | python3 -c "import json, sys; [sys.stdout.write(f\"{s['id']:40s} stage: {s.get('runtime',{}).get('stage','?')}\n\") for s in json.load(sys.stdin)]"
```

## 2. Card Improvement Workflow

When improving a model or dataset card:
1. **Fetch Current Card**:
   ```bash
   curl -sSf "https://huggingface.co/{author}/{repo}/raw/main/README.md" > /tmp/readme-baseline.md
   ```
2. **Author Improved Content**:
   - Add standard metadata badges (downloads, license, base model, collection).
   - Document concrete evaluation scores from `.eval_results/` artifacts.
   - Include copy-paste code snippets for model loading.
3. **Upload via `huggingface_hub` API**:
   ```python
   from huggingface_hub import HfApi

   api = HfApi()
   api.upload_file(
       path_or_fileobj=content.encode("utf-8"),
       path_in_repo="README.md",
       repo_id="{author}/{repo}",
       repo_type="model",
       commit_message="docs: improve model card documentation and badges",
   )
   ```
4. **Byte-Level Verification**:
   Fetch the remote README and compare byte count with local file to confirm complete upload.

## 3. Evaluation Artifacts (`.eval_results/*.yaml`)

Hugging Face Hub renders formal benchmark tables from `.eval_results/` files in the repository:
- Check existing eval results:
  ```bash
  curl -s "https://huggingface.co/api/models/{author}/{repo}" \
    | python3 -c "import json, sys; d=json.load(sys.stdin); sys.stdout.write(str([s['rfilename'] for s in d.get('siblings', []) if '.eval_results' in s['rfilename']]) + '\n')"
  ```
- All scores must cite concrete evaluation runs (e.g. `lm-eval`, `open-llm-leaderboard`). Never invent scores.

## 4. Collection Management

The primary family collection is `Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02`.
- Verify collection contents:
  ```bash
  curl -s "https://huggingface.co/api/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02" \
    | python3 -c "import json, sys; c=json.load(sys.stdin); sys.stdout.write(f'Items in collection: {len(c.get(\"items\", []))}\n')"
  ```

## 5. Security & Governance Invariants

- **Triple-Gate Hub Writes**: In accordance with House of Sak governance, production writes to the Hub require explicit authorization (`hub-approved`) and SakThai sign-off. SakTan acts as the monitoring and telemetry sentinel.
- **Secrets Redaction**: Never print `HF_TOKEN` in console logs or session outputs.
