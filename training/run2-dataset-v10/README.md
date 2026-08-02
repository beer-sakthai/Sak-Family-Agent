---
license: apache-2.0
pretty_name: SakThai Combined Tool-Calling Dataset v10
tags:
- model:Nanthasit/sakthai-context-7b-tools
- instruction-tuning
- model:Nanthasit/sakthai-plus-1.5b
- model:Nanthasit/sakthai-coder-1.5b
- synthetic
- model:Nanthasit/sakthai-context-1.5b-merged-v2
- function-calling
- agent
- tool-calling
- sakthai
language:
- en
size_categories:
- 1K<n<10K
task_categories:
- text-generation
config_names:
- default
---

<div align="center">

[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Nanthasit%2Fsakthai--combined--v10-orange)](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v10)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Downloads](https://img.shields.io/badge/datasets-0-yellow)](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v10)

</div>

# SakThai Combined v10

Part of the SakThai model family: a combined tool-calling instruction dataset for agentic tuning.

- **Owner:** `Nanthasit`
- **Format:** JSONL with `messages` + `tools`
- **Rows:** ~2,965
- **Schema:** `messages`, `tools`
- **Generated:** 2026-08 enrichment cycle
- **License:** Apache 2.0

## Dataset Description

This dataset is an enriched combined corpus of tool-calling conversations. It is intended for instruction tuning and function-calling evaluation of small language models. Each row contains multi-turn messages and structured tool definitions.

## Fields

| Field   | Type   | Description |
|---------|--------|-------------|
| `messages` | list[dict] | Multi-turn conversation with `role` and `content`. Roles include `system`, `user`, and `assistant`. |
| `tools`    | list[dict] | Structured tool definitions with name, description, and parameters. Compatible with the SakThai `<tools>` / `<tool_call>` XML format. |

## Loading

```python
from datasets import load_dataset

# Basic load
ds = load_dataset("Nanthasit/sakthai-combined-v10", split="train")
print(ds[0])

# Streaming for large workloads
ds_stream = load_dataset("Nanthasit/sakthai-combined-v10", split="train", streaming=True)
for row in ds_stream.take(5):
    print(row["messages"][0]["role"])
```

## Dataset Size

- Estimated size: ~1-10M tokens
- Rows: ~2,965
- Splits: `train`
- File format: JSONL

## Use

- Fine-tuning base models for tool-calling behavior.
- Benchmarking tool selection and argument accuracy.
- Training merges for SakThai context/merged variants.

## License

Apache 2.0. Use freely, attribution appreciated.

## Links

- [SakThai Model Family Collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02)
- [GitHub](https://github.com/beer-sakthai/Sak-Family-Agent)

Enriched by SakThai ecosystem health check on 2026-08-01.

<div align="center">

[![Download dataset](https://img.shields.io/badge/downloads-0-blue)](#loading)

</div>

## Dataset Size

- Rows: 2,965
- File: `data/train.jsonl` (5.57 MB)
- Splits: `train`
- Format: JSONL with `messages` + `tools`

## Loading Examples

```python
from datasets import load_dataset

# Train split
ds = load_dataset("Nanthasit/sakthai-combined-v10", split="train")
print(ds[0])

# Streaming
stream = load_dataset("Nanthasit/sakthai-combined-v10", split="train", streaming=True)
for row in stream.take(3):
    print(row["messages"][0].get("role"))
```

```python
# pandas + hf:// direct access
import pandas as pd
df = pd.read_json("hf://datasets/Nanthasit/sakthai-combined-v10/data/train.jsonl", lines=True)
print(df.head(1).to_dict(orient="records")[0])
```

## Verification

- Verified via local file probe on 2026-08-01.
- README head matches: yes.
- Datasets Server viewer: **unverified** for this repo state.


## Row Preview

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of Thailand?"},
    {"role": "assistant", "content": "The capital of Thailand is Bangkok."}
  ],
  "tools": [
    {
      "name": "search",
      "description": "Search the web.",
      "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    }
  ]
}
```

## File Stats

- File: `data/train.jsonl`
- Bytes: 5,836,234
- Rows: 2,965
- Approx tokens: ~600k
- Split: `train`

## Notes

- Load with `datasets>=2.x`. No `trust_remote_code` required.
- Tool format follows `<tools>` XML schema compatible with SakThai-trained models.
- For large-scale fine-tuning, prefer `streaming=True` to avoid materializing the full dataset.
