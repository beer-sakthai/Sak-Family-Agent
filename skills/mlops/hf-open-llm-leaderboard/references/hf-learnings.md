# HF Open LLM Leaderboard v2 — Deep Dive

> Research date: 2026-07-25
> Author: SakThai · Main Lead of the House & Master of Hugging Face
> License: MIT

## Summary

Deep-dive into the Hugging Face Open LLM Leaderboard v2 — the standardized evaluation platform for open-source LLMs. This is a deepening of Topic #40, covering the 6-benchmark methodology, submission pipeline, results dataset architecture, reproducibility commands, and infrastructure.

## Key Sources

- Leaderboard: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard
- Results dataset: https://huggingface.co/datasets/open-llm-leaderboard/results
- Requests dataset: https://huggingface.co/datasets/open-llm-leaderboard/requests
- HF lm-eval fork: https://github.com/huggingface/lm-evaluation-harness
- Full deep-dive in main references: `skill_view(name='huggingface-hub', file_path='references/hf-learnings.md')` — search for "hf-open-llm-leaderboard-deep-dive"

---

## The 6 Benchmarks

| Benchmark | Paper | Shots | Metric | What It Tests |
|-----------|-------|-------|--------|---------------|
| IFEval | 2311.07911 | 0 | `inst_level_strict_acc` + `prompt_level_strict_acc` | Instruction following & formatting adherence |
| BBH | 2210.09261 | 3 | `acc_norm` (23 subtasks) | Multistep reasoning, arithmetic, logic |
| MATH Lvl 5 | 2103.03874 | 4 | `exact_match` | Hardest high-school competition math |
| GPQA | 2311.12022 | 0 | `acc_norm` (4-choice) | PhD-level domain expertise (gated access) |
| MuSR | 2310.16049 | 0 | `acc_norm` (3 subtasks) | Long-range narrative reasoning (algorithmic) |
| MMLU-PRO | 2406.01574 | 5 | `acc` (10-choice) | Expert-refined knowledge across 57 subjects |

## Reproducibility Command

```bash
git clone git@github.com:huggingface/lm-evaluation-harness.git
cd lm-evaluation-harness && pip install -e .

# Base models:
lm-eval --model_args="pretrained=org/model,dtype=float16" \
        --tasks=leaderboard --batch_size=auto --output_path=./results

# Chat models (add flags):
lm-eval --model_args="pretrained=org/model,dtype=float16" \
        --tasks=leaderboard --batch_size=auto \
        --apply_chat_template --fewshot_as_multiturn \
        --output_path=./results
```

## Infrastructure

- **Deployment**: Docker Space on CPU Upgrade hardware ($0.03/hr)
- **Results storage**: HF Dataset (`open-llm-leaderboard/results`) as Parquet
- **Evaluation**: Sequential queue, 1-6 hours per model
- **Model categories**: 🟢 Pretrained, 🟩 Continuously Pretrained, 🔶 Fine-Tuned, 💬 Chat, 🤝 Merges

## Known Limitations

1. Batch-size padding variance can shift scores ±1%
2. Self-reported categories not always accurate
3. Precision not standardized — float16 vs 4bit compared together
4. All benchmarks are English-only; no multilingual evaluation
5. No multi-turn conversation evaluation
