---
name: SakThai-hf-reasoning-corpus-4k-5m
description: "Qyrou/reasoning-corpus-4K-5M-v1 \u2014 curated 5M-row / ~9B-token reasoning corpus\
  \ for SLM SFT & distillation. Source map, schema, streaming recipes, and pitfalls."
---

# Reasoning Corpus 4K-5M (Qyrou)

Curated mega-corpus of model reasoning chains for **SFT / reasoning distillation into
small language models**. Apache-2.0, un-gated, streaming-friendly, zero-cost.

**Repo:** `Qyrou/reasoning-corpus-4K-5M-v1`
**Scale:** ~4,975,727 rows · ~8.95B tokens · 93 source sub-entries (2026-07-31)

## What's inside

Reasoning traces from DeepSeek-v4 (Pro+Flash), DeepSeek-R1 family, Qwen3/3.5/3.6
(open+API), Gemma4-31B, Kimi-K2.5, GPT-OSS-120B, GLM-5.1, Nemotron-Cascade,
Dolci-Think, OpenThoughts2-1M, Magpie, and ~80 more. Top sources by share:

- glaiveai/reasoning-v1-20m — 19.52% (1.05M rows)
- PrimeIntellect/INTELLECT-3-SFT (openreasoning_science + am_chat) — ~18%
- BAAI/OpenSeek-Synthetic-Reasoning-Data-Examples — 6.34%
- nvidia/Nemotron-Cascade-SFT (general/math/science/code/swe splits) — ~11%
- open-thoughts/OpenThoughts2-1M — 4.78% · PrimeIntellect/SYNTHETIC-1-SFT — 4.67%

## Schema

| Column | Use |
|---|---|
| `repo_id` | Source repo — mixture balancing, provenance, source caps |
| `tok_len` | Estimated length — cheap pre-filter (example: keep 128–4096) |
| `user` | Prompt |
| `thought_trace` | CoT reasoning — explicit reasoning supervision |
| `assistant` | Final answer |
| `ChatML` | Preformatted complete sample for direct text training |

## Usage recipes

**Load (streaming recommended):**
```python
from datasets import load_dataset
ds = load_dataset("Qyrou/reasoning-corpus-4K-5M-v1", split="train", streaming=True)
```

**Filter before tokenizing** (keep cheap ops early):
```python
ds = ds.filter(lambda r: bool(r["user"].strip()) and bool(r["assistant"].strip())
               and 128 <= r["tok_len"] <= 4096)
ds = ds.filter(lambda r: r["repo_id"] in allowed_sources)  # controlled mixture
ds = ds.remove_columns(["ChatML", "repo_id", "tok_len", "user", "thought_trace", "assistant"])
```

**Shuffle buffer:** 4096 single-GPU / 512 debug / 8192–32768 distributed.

**Strict length filtering:** tokenize with `truncation=False`, then discard rows whose
true tokenized length exceeds the target context window (don't silently truncate away
final answers).

**Validation split (deterministic, leakage-safe):** blake2b hash of `repo_id \0 user`
mod 1000 → <10 = validation (~1%, capped at 5,000 rows), ≥10 = train.

**Distributed:** same fixed seed on all ranks + `split_dataset_by_node(rank, world_size)`.

## Pitfalls

| Pitfall | Note |
|---|---|
| README ID says `SupraLabs/...` | Canonical live repo is `Qyrou/reasoning-corpus-4K-5M-v1` (verified via `/api/datasets` 2026-07-31). Possibly a mirror exists under SupraLabs; if `Qyrou/...` load fails, try `SupraLabs/...` but verify. |
| `tok_len` is an estimate | Differs across tokenizers; always re-validate with the target model's tokenizer before final filtering. |
| Traces are NOT verified proofs | Model-generated; may contain unnecessary steps, wrong assumptions, or answer leakage. Source-balance, dedup, and spot-check for formal evals. |
| `datasetsServerInfo` sparse | API returns `numRows: 0` / empty formats — don't trust server info for row counts; use README's source table (93 rows) or a streamed `.take()` sample. |

## Related

- Findings: `~/profiles/sakthai/cron/findings/hf-findings-2026-07-31-reasoning-corpus-4k-5m.md`
- Similar curated SFT corpora covered by the household: `sakthai-hf-agent-traces-datasets`
  (Fable-5 traces), `sakthai-hf-stack-v3` (code pretraining).
