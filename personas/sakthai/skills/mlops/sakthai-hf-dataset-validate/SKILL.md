---
name: sakthai-hf-dataset-validate
category: mlops
description: "Validates a JSONL dataset file for LoRA fine-tuning on Hugging Face. Checks schema: input (string), output (valid JSON with tool_name + arguments), max 500 lines."
author: SakThai
version: 1.0
created: 2026-06-21
---

# HF Dataset Validator for LoRA Training

Use this skill to validate a `.jsonl` dataset before uploading to Hugging Face.

## Input
- `path`: Absolute path to `.jsonl` file (e.g., `/home/sakthai/data/dataset.jsonl`)

## Output
- Returns `valid: true/false` + error message if invalid

## Steps

1. Read the file line by line
2. For each line:
   - Parse as JSON
   - Check if `input` exists and is a string
   - Check if `output` exists and is a string
   - Parse `output` as JSON → must have `tool_name` and `arguments`
   - Reject if `tool_name` is empty or `arguments` is not an object
3. Count total lines — must be ≤ 500
4. Return summary: total lines, invalid lines, validity status

## Example Usage

```bash
skill_run hf-dataset-validate --path /home/sakthai/data/hf_training_data_composio_tools_50.jsonl
```

## Pitfalls

- ❌ File has `tools` array instead of `output` JSON → invalid
- ❌ `output` is missing → invalid
- ❌ `input` is not a string → invalid
- ❌ More than 500 lines → reject to prevent overfitting

## Verification

After validation, manually inspect:

https://hf.co/datasets/Nanthasit/hf-training-composio-tools-50

If valid, proceed to upload via `hf-dataset-upload`.

## Dependencies

- Python 3.11+
- No external packages — uses only `json` and `sys`

## Related Skills

- `hf-dataset-upload`
- `hf-jobs-submit`
