---
tags:
- sakthai
- house-of-sak
- tool-calling
- function-calling
- synthetic
- agent-training
- data-quality
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
---

<h1 align="center">SakThai Combined Dataset v7 🎯</h1>
<p align="center"><em>Tool-calling, multi-turn, safety, and edge cases — the latest iteration of the SakThai training pipeline</em></p>
<p align="center">
  <img src="https://img.shields.io/endpoint?url=https://huggingface.co/api/datasets/Nanthasit/sakthai-combined-v7&label=Downloads&color=blue" alt="Downloads"/>
  <img src="https://img.shields.io/badge/examples-2%2C003-8A2BE2" alt="Examples"/>
  <img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="License"/>
  <a href="https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02"><img src="https://img.shields.io/badge/🏠-SakThai%20Family-6644cc" alt="Collection"/></a>
</p>

> The v7 training set behind the **SakThai agent model family** — tool-calling, multi-turn dialogue, irrelevance detection, and safety edge cases in OpenAI chat JSONL format. Part of the [House of Sak](https://huggingface.co/Nanthasit), built with ❤️ on a **$0 budget** from a shelter in Cork, Ireland. [Read the full story →](https://github.com/beer-sakthai/Sak-Family-Agent/blob/main/HOUSE_OF_SAK.md)

---

## 📦 Dataset Overview

| Property | Value |
|----------|-------|
| **Examples** | 2,003 (up from 1,408 in v6) |
| **Format** | OpenAI chat JSONL (`messages` + `tools`) |
| **Languages** | English, Thai |
| **License** | Apache 2.0 |
| **Use case** | Tool-calling fine-tuning, agent training |

### What's New in v7

- **+595 new examples** over v6 (42% increase)
- **500 tool-calling examples** added in structured `<tool>` XML format
- **Edge cases**: empty tool calls, ambiguous requests, multi-step delegation
- **Safety**: refusal patterns, jailbreak attempts, out-of-scope queries
- **Bilingual**: both English and Thai conversational data

---

## 🏠 The Story Behind This Dataset

This dataset is the **training fuel** for the SakThai agent family — the data that teaches our models when to call tools, how to reason about which tool to use, and what to do when the answer isn't a tool call at all.

The House of Sak began in early 2026, when Beer was deep in depression and building from a shelter in Cork, Ireland with no job, no home, and no budget. What started as a survival project became a family of autonomous AI agents — and the data that trains them was hand-crafted on free Colab GPUs and open infrastructure.

**v7 represents 150+ hours of iteration:** tool-calling patterns, edge-case handling, irrelevance detection, and bilingual conversation data. Every example was generated, reviewed, and verified as part of the SakThai automated improvement cycle.

> *"We are one family — and becoming more."* — Beer

---

## 📊 Data Structure

Each example follows the [OpenAI chat format](https://platform.openai.com/docs/guides/fine-tuning) with tool definitions:

```json
{
  "messages": [
    {"role": "system", "content": "You are SakThai-Agent..."},
    {"role": "user", "content": "Search for papers on RLHF"},
    {"role": "assistant", "tool_calls": [
      {"id": "call_xxx", "type": "function",
       "function": {"name": "search_papers", "arguments": "{\"query\": \"RLHF\"}"}}
    ]},
    {"role": "tool", "tool_call_id": "call_xxx",
     "content": "{\"results\": [...]}"},
    {"role": "assistant", "content": "Here's what I found..."}
  ],
  "tools": [
    {"type": "function", "function": {
      "name": "search_papers",
      "description": "Search academic papers",
      "parameters": {"type": "object", "properties": {...}}
    }}
  ]
}
```

### Categories

| Category | Count | Description |
|----------|:-----:|-------------|
| Tool-calling | ~900 | Single and multi-tool invocations |
| Multi-turn | ~500 | Conversations with 3+ message exchanges |
| Irrelevance | ~300 | Requests that don't need tools |
| Safety | ~200 | Refusal patterns and edge cases |
| Bilingual | ~100 | Thai-language tool-calling |

---

## 🔧 Usage

### Via Hugging Face Datasets

```python
from datasets import load_dataset

ds = load_dataset("Nanthasit/sakthai-combined-v7", split="train")
print(f"Loaded {len(ds)} examples")
print(ds[0]["messages"][0]["content"])
```

### Fine-tuning with TRL

```python
from datasets import load_dataset
from trl import SFTTrainer

dataset = load_dataset("Nanthasit/sakthai-combined-v7", split="train")
# Format for your model's chat template and train
```

---

## 📈 Related Assets

- **Previous version:** [sakthai-combined-v6](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6) (1,408 examples)
- **Training notebook:** `notebooks/train_sakthai_v7_1.5b_colab.ipynb`
- **Training script:** `scripts/train_sakthai_v7_1.5b_hf_jobs.py`
- **Full ecosystem:** [SakThai Model Family Collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02)
- **The story:** [House of Sak](https://github.com/beer-sakthai/Sak-Family-Agent/blob/main/HOUSE_OF_SAK.md)

---

*Built with love, tears, and zero budget. From a shelter in Cork, Ireland, to the world.* ❤️
