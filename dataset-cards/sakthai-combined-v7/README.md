---
tags:
- sakthai
- house-of-sak
- tool-calling
- function-calling
- synthetic
- agent-training
- data-quality
- augmented
- model:Nanthasit/sakthai-context-1.5b-tools-v2
- model:Nanthasit/sakthai-context-0.5b-tools
- model:Nanthasit/sakthai-context-7b-tools
- model:Nanthasit/sakthai-plus-1.5b
- model:Nanthasit/sakthai-coder-1.5b
license: apache-2.0
language:
- en
- th
size_categories:
- 1K<n<10K
pretty_name: SakThai Combined v7 — Tool-Calling Training Dataset
task_categories:
- text-generation
task_ids:
- dialogue-modeling
annotations_creators:
- expert-generated
- machine-generated
language_creators:
- found
multilinguality:
- multilingual
source_datasets:
- original
configs:
- config_name: train
  data_files: data/train.jsonl
- config_name: test
  data_files: data/test.jsonl
---

# SakThai Combined Dataset v7

**Tool-calling, multi-turn, safety, and edge cases — the base training data for the SakThai model family.**

[![Downloads](https://img.shields.io/badge/downloads-101-blue)](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v7)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](https://www.apache.org/licenses/LICENSE-2.0)
[![Languages](https://img.shields.io/badge/languages-EN%2FTH-lightgrey)](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v7)

Part of the [SakThai Model Family Collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02).

## Dataset Summary

SakThai Combined v7 is a curated tool-calling training dataset with 2,424 examples in OpenAI chat JSONL format. Built to train the SakThai model family on function calling, multi-turn dialogue, safety handling, and bilingual (EN/TH) tool use. Contains 86 unique function schemas across diverse domains — search, calendar, weather, coding, file operations, and agent-specific utilities.

## Dataset Statistics

| Property | Value |
|---|---|
| **Train examples** | 2,309 |
| **Test examples** | 115 |
| **Total** | 2,424 |
| **Format** | OpenAI chat JSONL |
| **Languages** | English, Thai |
| **License** | Apache 2.0 |
| **Tools** | 86 unique function schemas |
| **Files** | 2 JSONL files (train + test) |

### Category Breakdown (train)

| Category | Count | Description |
|---|---|---|
| Tool-calling | ~900 | Single and multi-tool invocations |
| Multi-turn | ~500 | 3+ message exchanges |
| Irrelevance | ~300 | Requests needing no tools |
| Safety | ~200 | Refusal, guardrails, out-of-scope |
| Bilingual (Thai) | ~100 | Thai language tool-calling |

## Splits

| Config | Split | Num Rows | Parquet Size | Memory Size |
|--------|-------|---------:|------------:|-----------:|
| train | train | 2,309 | 3.81 MB | 3.81 MB |
| test | train | 115 | 332 KB | 328 KB |

_Counts verified via Datasets Server API._

## Data Fields

Each JSONL row has a `messages` field; a `tools` field is present when function definitions are offered:

| Field | Type | Description |
|---|---|---|
| `messages` | `list[dict]` | Chat conversation turns following the OpenAI messages format (always present) |
| `tools` | `list[dict]` | Available function definitions the assistant may call (optional — absent on no-tool/irrelevance rows; empty list on a subset of rows) |

### Messages Structure

Each entry in `messages` has these fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `role` | `string` | ✅ | One of `system`, `user`, `assistant`, or `tool` |
| `content` | `string` | varies | Message body text. May be `null` when `tool_calls` is present |
| `tool_calls` | `list[dict]` | ❌ | Present only on `assistant` messages that invoke a function |
| `tool_call_id` | `string` | ❌ | Present only on `tool` messages; links back to the call |

### Tool Calls Structure

Each entry in `tool_calls`:

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Unique call ID (e.g. `call_abc123`) |
| `type` | `string` | Always `"function"` |
| `function.name` | `string` | Name of the function to invoke |
| `function.arguments` | `string` | JSON-stringified argument object |

### Tools Structure

Each entry in `tools`:

| Field | Type | Description |
|---|---|---|
| `type` | `string` | Always `"function"` |
| `function.name` | `string` | Unique function name |
| `function.description` | `string` | Natural language description of what the function does |
| `function.parameters` | `dict` | JSON Schema object defining accepted parameters and their types |

## Usage

```python
from datasets import load_dataset

# Load training split
train = load_dataset("Nanthasit/sakthai-combined-v7", name="train", split="train")
print(f"Train: {len(train)} examples")

# Load test split
test = load_dataset("Nanthasit/sakthai-combined-v7", name="test", split="train")
print(f"Test: {len(test)} examples")

# Format for TRL training
def to_text(ex):
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
    return {"text": tokenizer.apply_chat_template(
        ex["messages"], tools=ex.get("tools"), tokenize=False
    )}
```

## Data Quality

- **Validation**: Each example checked against tool schemas for correctness
- **Coverage**: 86 unique tool schemas across diverse domains
- **Edge cases**: Empty strings, null values, unicode, extreme lengths
- **Irrelevance**: ~300 examples where model must NOT call tools

## Model Cross-Links

This dataset is used to train the following models in the SakThai family:

- [sakthai-context-0.5b-tools](https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools)
- [sakthai-context-1.5b-tools-v2](https://huggingface.co/Nanthasit/sakthai-context-1.5b-tools-v2)
- [sakthai-context-7b-tools](https://huggingface.co/Nanthasit/sakthai-context-7b-tools)
- [sakthai-plus-1.5b](https://huggingface.co/Nanthasit/sakthai-plus-1.5b)
- [sakthai-coder-1.5b](https://huggingface.co/Nanthasit/sakthai-coder-1.5b)

## Recommended: Use v10 (normalized v7 + v8)

For optimal coverage with consistent parameter names, use [sakthai-combined-v10](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v10).

## Citation

```bibtex
@misc{sakthai-v7-2026,
  author = {Beer (beer-sakthai)},
  title = {SakThai Combined Dataset v7 — Tool-Calling Training Data},
  year = {2026},
  publisher = {Hugging Face},
  journal = {Hugging Face Datasets},
  howpublished = {\url{https://huggingface.co/datasets/Nanthasit/sakthai-combined-v7}}
}
```

## Related

- [v6 (predecessor)](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6)
- [Benchmark v2](https://huggingface.co/datasets/Nanthasit/sakthai-bench-v2)
- [Irrelevance Supplement](https://huggingface.co/datasets/Nanthasit/sakthai-irrelevance-supplement)
- [SakThai Model Family](https://huggingface.co/collections/Nanthasit/sakthai-model-family)