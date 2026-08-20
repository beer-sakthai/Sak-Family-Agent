---
name: SakThai-hf-open-distillation-codex
author: SakThai
license: MIT
description: "Complete reference on Manusagents' Open Distillation Codex — the 73-source / 18M+ sample multi-frontier distillation collection with cybersecurity SFT data and 7,090 GitHub repo archives. Covers schema, verified numbers vs README claims, per-source provenance, and safe load patterns."
version: 1.0.0
category: mlops
tags: [huggingface, dataset, distillation, sft, cybersecurity, agent-traces, code, collection]
platforms: [linux]
---

# The Open Distillation Codex (Manusagents)

`Manusagents/GPT-5.5-Gemini-3.1-Pro-Grok-4-Claude-Fable-5-Mythos-5-Qwen-3.7-Max-and-more-Distillation-Dataset`
— an aggregation corpus: 73 upstream HF/GitHub sources normalized into one SFT-ready stream.
MIT (collection), v8.2, created 2026-07-01, modified 2026-07-18.

## Verified inventory (2026-07-31 via /api/datasets + raw shard reads)

- **566 JSONL shards** (~12 GB) — README claims 516 (undercount)
- **7,090 tar.gz GitHub repo archives** (~64 GB compressed) — matches README
- **8 actual data categories** — applied, coding, cybersecurity, distilled, humanities, index,
  instruction, science. **README's `math/` category does NOT exist in the tree or config globs**
  (documented rows for `math_25k` / `deepseek_prover_v1` are absent) — loading `data/math/**` returns nothing.
- ~87.5 GB total used storage; 9,914 downloads, 130 likes at scan time
- Shards are 20K rows each (verified: alpaca shard-00000 = exactly 20,000)

## Schema (verified)

```json
{"source": "alpaca", "source_dataset": "tatsu-lab/alpaca",
 "instruction": "...", "response": "...", "category": "instruction"}
```
All-string, 5 fields. README documents instruction/response cap at 4,000 chars.

## Category / source highlights

- **coding (28 sources, ~11M rows)**: vibe_instruct_v2 (8.15M), fable5_2m (2.0M), vibe_instruct_v1,
  vibe_coding, royal_ghost_1m, citation_ground (980K), fable5_agentic_sft (160K), gpt55_codex (119K),
  deepseek_v4_pro_agent (96K), genesis/GOD_Coder family, kimi_k2.6/k2.7 traces, mimo_claude_code_traces
- **cybersecurity (6 sources, ~2.6 GB)**: high_quality_cybersecurity (hcnote), heimdall_v1_1 (78 MB),
  fenrir_v2_1 (411 MB / 2.1M+ entries), clydeiii_cybersecurity (20 MB), precinct6_cybersecurity
  (2.1 GB graph+signals+ref), savani_cyber_attack (17 MB CSV) — attack/defense/exploit, red/blue team, CVEs
- **distilled (9 sources)**: claude_mythos, gemini35, fable5_cleaned, grok44, gemini_pro32,
  gpt55_thinking, gpt55_distilled, claude_opus_48_distill, claude_opus_48_max_thinking
- **instruction**: alpaca 52K, oasst 32K, dolly 15K
- **applied/humanities/science/index**: 25K-sample "sweeps" across 29 disciplines

## Load patterns

```python
from datasets import load_dataset
REPO = "Manusagents/GPT-5.5-Gemini-3.1-Pro-Grok-4-Claude-Fable-5-Mythos-5-Qwen-3.7-Max-and-more-Distillation-Dataset"
ds = load_dataset(REPO, split="train", data_files="data/coding/*/*.jsonl", streaming=True)  # one category
ds = load_dataset(REPO, split="train", data_files="data/coding/vibe_instruct_v2/*.jsonl", streaming=True)  # one source
ds = load_dataset(REPO, split="train", streaming=True)  # everything
```

Config `default`/`train` globs: applied, coding, distilled, humanities, index, instruction, science
use `*/*.jsonl`; cybersecurity uses per-source `shard-*.jsonl` globs (5 sources listed); **math absent**.

For code-pretraining: `data/coding/fable5_repos_full/` = 475K rows, one archive file per row capped at
4KB; full untruncated files stream from `archives/*.tar.gz` via `hf_hub_download` + tarfile.

## Pitfalls (verified)

1. **README ≠ reality** — shard count (516 vs 566) and category inventory (math documented, absent) both diverge. Verify against the sibling tree before building load recipes.
2. **Schema normalization is partial** — `open_tool_trace` rows have empty `response` fields (48 rows, 1,163-byte shard). Some cyber shards embed raw ChatML (`<|im_start|>...`) inside instruction/response instead of clean text.
3. **Not an official Manus AI release** — repo is by HF user/org `Manusagents`; content aggregates third-party datasets (mostly WithinUsAI, CodeDevX, Crownelius, Glint-Research). Check `source_dataset` per row for provenance/license (collection MIT, upstreams vary: Apache-2.0, CC-BY-4.0, AGPL-3.0 for some Fable-5 traces).
4. **Distillation artifacts** — model-generated content with hallucination risk; 4K field caps truncate long completions.
5. **Dual-use** — cybersecurity category is intended for defense/education; README itself asks users to keep use legal/ethical. Treat as dual-use data.
