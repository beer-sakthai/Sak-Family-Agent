---
name: SakThai-hf-frontis-ma1-openmle
description: "Complete reference on Frontis-MA1 + OpenMLE \u2014 the AI4AI / recursive-self-improvement\
  \ (RSI) release for machine learning engineering (MLE). Meta-evolution agent trained\
  \ on four atomic program-evolution operators (Draft/Improve/Debug/Crossover), execution-grounded\
  \ SFT+RL, OpenMLE-Evo search harness."
---

# Frontis-MA1 + OpenMLE — AI4AI / Recursive Self-Improvement for MLE

Reference for the Frontis-MA1 model family and the OpenMLE full-stack RSI system
(arXiv:2607.28568, released 2026-07-31, CC BY-NC 4.0). **First AI4AI/RSI entry in the
HF trending scanner's tracker history** (scan 2026-07-31, daily-papers fallback).
Findings: `cron/findings/hf-findings-2026-07-31-frontis-ma1.md`.

## Repos

| Repo | Base | Format | Notes |
|---|---|---|---|
| `FrontisAI/Frontis-MA1-30B` | Qwen3-30B-A3B-Thinking-2507 | BF16 Transformers (`Qwen3MoeForCausalLM`) | canonical release |
| `FrontisAI/Frontis-MA1-35B` | Qwen3.6-35B-A3B | BF16 Transformers (`Qwen3_5MoeForConditionalGeneration`) | companion, image-text-to-text |
| `FrontisAI/Frontis-MA1-30B-GGUF` | Frontis-MA1-30B | Q4_K_M GGUF (18.56 GB) | local deployment |
| `FrontisAI/OpenMLE-Tasks` | — | dataset | agent environments, tabular, license:other |
| `FrontisAI/OpenMLE-SFT-Traces` | — | dataset | 26,259 examples (17,245 full + 9,014 trajectory steps), parquet, CC BY-NC 4.0 |

Code: https://github.com/FrontisAI/OpenRSI · Collection: https://huggingface.co/collections/FrontisAI/frontis-ma1

## Core concept — the four atomic operators

Post-training and inference are aligned around **four program-evolution operators**:

- **Draft** — create a complete initial solution
- **Improve** — refine a parent program using its score + execution evidence
- **Debug** — repair invalid or failing code
- **Crossover** — recombine useful elements from two parent solutions

The same operators are (1) trained via execution-grounded SFT + RL, then (2) composed at
test time by **OpenMLE-Evo** into long-horizon evolutionary search — coupling learning
and evolution in a single loop. The model IS the evolutionary operator.

## OpenMLE stack (3 components)

- **OpenMLE-Gym** — verifiable task environments with execution feedback
- **OpenMLE-RL** — operator learning (SFT + RL from executed programs)
- **OpenMLE-Evo** — long-horizon search composing the operators; **OpenMLE-Evo-Max** adds
  benchmark-independent experience priors + asynchronous multi-GPU search

## Architecture (verified from config.json 2026-07-31)

**30B** (`qwen3_moe`): 30.5B total / 3.3B activated; 48 layers; hidden 2048; intermediate
6144; 128 experts / 8 per token; moe_intermediate 768; 32 attn / 4 KV heads; vocab
151,936; ctx 262,144 (inherited; SFT cutoff 32,768 — longer contexts unvalidated).

**35B** (`qwen3_5_moe`, image-text-to-text): 40 layers; hidden 2048; 16 attn / 2 KV heads;
vocab 248,320; ctx 262,144; 8 experts/token; moe_intermediate 512.

## Training recipe

- **SFT:** BF16 full-param on 8× H200; global batch 128; lr 3e-5 cosine (0.1 warmup);
  3 epochs; Qwen3 thinking-loss masking
- **RL:** GSPO + execution-grounded reward post-processing; operator mixture
  Draft 0.50 / Improve 0.17 / Debug 0.17 / Crossover 0.16; 16 prompts × 16 samples;
  max response 24,576 tokens; Adam lr 1e-6

## Benchmarks — MLE-Bench Lite (22 tasks, 12 h/task on 0.5× RTX 4090)

| Model | Harness | Valid Rate | Medal Avg | Human Rank |
|---|---|---|---|---|
| Qwen3-30B-A3B-Thinking-2507 | OpenMLE-Evo | 17.33/22 | 34.85% | 0.5573 |
| **Frontis-MA1-30B** | OpenMLE-Evo | 21.67/22 | **53.03%** | **0.7055** |
| **Frontis-MA1-30B** | OpenMLE-Evo-Max | 22.00/22 | **66.67%** | **0.8053** |
| Qwen3.6-35B-A3B | OpenMLE-Evo | 19.67/22 | 39.39% | 0.5828 |
| **Frontis-MA1-35B** | OpenMLE-Evo | 21.67/22 | **60.61%** | **0.7647** |
| **Frontis-MA1-35B** | OpenMLE-Evo-Max | — | **71.21%** | — |

- Fixed-harness comparison is the primary evidence: 30B adds +18.18 pp Medal Avg over its
  base; 35B adds +21.22 pp over Qwen3.6-35B-A3B.
- 35B + Evo-Max exceeds GPT-5.5 + Codex, approaches GPT-5.6 Sol and 2.8T Kimi K3.
- Public-weight table (fixed harness): Kimi K2.6 66.67% / GLM-5.2 62.12% / MiniMax M3
  59.09% / DeepSeek-V4-Flash 51.52%.
- Transfer (NatureBench Lite): model swap 50%→70% Match-SOTA; harness swap 20%→50%.

## Pitfalls

- **Scores are model–harness system results**, not standalone one-shot — reproduction
  requires the same OpenMLE-Evo config + sandbox budget. Never quote as pure model gains.
- **License CC BY-NC 4.0** — non-commercial; upstream Qwen Apache-2.0 preserved in
  LICENSE-UPSTREAM-APACHE-2.0. Training/eval datasets have separate terms
  (OpenMLE-Tasks = license:other).
- Generated code may be incorrect/insecure/destructive — run in isolated sandboxes.
- Context beyond 32,768-token SFT cutoff not validated.
- All repos were 0-download/1-like brand-new at scan (2026-07-31) — counts will drift.

## Serving

```bash
vllm serve FrontisAI/Frontis-MA1-30B --served-model-name Frontis-MA1-30B \
  --tensor-parallel-size 8 --max-model-len 32768 --enable-reasoning \
  --reasoning-parser deepseek_r1
```
