---
name: SakJules-SakThai-hf-open-llm-leaderboard
description: "Complete reference for the Hugging Face Open LLM Leaderboard v2 \u2014 the 6 benchmark\
  \ tasks (IFEval, BBH, MATH Lvl 5, GPQA, MuSR, MMLU-PRO), evaluation parameters,\
  \ model categories, reproducibility commands, and submission workflow."
---

# Open LLM Leaderboard v2 — Evaluation Methodology

The [Open LLM Leaderboard](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard) (🏆 14K+ likes) tracks, ranks, and evaluates open-source LLMs and chatbots against a standardized suite of 6 benchmarks. Built on the [EleutherAI Language Model Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness).

## The 6 Benchmarks

### 1. IFEval (Instruction Following Evaluation)
- **Paper**: [arxiv.org/abs/2311.07911](https://arxiv.org/abs/2311.07911)
- **Task**: `IFEval`
- **Measure**: Strict Accuracy at Instance and Prompt Levels (`inst_level_strict_acc,none` + `prompt_level_strict_acc,none`)
- **Shots**: 0-shot
- **num_choices**: 0
- **What it tests**: Model's ability to follow explicit formatting instructions (e.g., "include keyword x", "use format y"). Focuses on adherence to formatting, not content quality.

### 2. BBH (Big Bench Hard)
- **Paper**: [arxiv.org/abs/2210.09261](https://arxiv.org/abs/2210.09261)
- **Task**: `BBH` (aggregates 23 subtasks)
- **Measure**: Normalized Accuracy (`acc_norm,none`)
- **Shots**: 3-shot per subtask
- **What it tests**: Multistep arithmetic, algorithmic reasoning, language understanding, world knowledge. 23 subtasks including:
  - Sports Understanding (num_choices=2), Navigate (2), Snarks (2), Date Understanding (6)
  - Reasoning about Colored Objects (18), Object Counting (19), Geometric Shapes (11)
  - Logical Deduction (3/5/7 objects), Temporal Sequences (4), Boolean Expressions (2)
  - Causal Judgement (2), Formal Fallacies (2), Hyperbaton (2), Disambiguation QA (3)
  - Tracking Shuffled Objects (3/5/7), Movie Recommendation (6), Ruin Names (6)
  - Penguins in a Table (5), Salient Translation Error Detection (6), Web of Lies (2)
- BBH performance correlates well with human preferences.

### 3. MATH Lvl 5
- **Paper**: [arxiv.org/abs/2103.03874](https://arxiv.org/abs/2103.03874)
- **Task**: `Math Level 5`
- **Measure**: Exact Match (`exact_match,none`)
- **Shots**: 4-shot
- **num_choices**: 0
- **What it tests**: High-school level competition problems using LaTeX for equations and Asymptote for figures. Only Level 5 (hardest) questions are used.

### 4. GPQA (Graduate-Level Google-Proof Q&A)
- **Paper**: [arxiv.org/abs/2311.12022](https://arxiv.org/abs/2311.12022)
- **Task**: `GPQA`
- **Measure**: Normalized Accuracy (`acc_norm,none`)
- **Shots**: 0-shot
- **num_choices**: 4
- **What it tests**: PhD-level domain expert questions in biology, physics, chemistry. Gated access to minimize data contamination. Plain text examples not provided.

### 5. MuSR (Multistep Soft Reasoning)
- **Paper**: [arxiv.org/abs/2310.16049](https://arxiv.org/abs/2310.16049)
- **Task**: `MuSR` (aggregates 3 subtasks)
- **Measure**: Normalized Accuracy (`acc_norm,none`)
  - Murder Mysteries: 0-shot, num_choices=2
  - Object Placement: 0-shot, num_choices=5
  - Team Allocation: 0-shot, num_choices=3
- **What it tests**: Algorithmically generated 1,000-word complex problems requiring integration of reasoning with long-range context parsing. Few models beat random.

### 6. MMLU-PRO (Massive Multitask Language Understanding - Professional)
- **Paper**: [arxiv.org/abs/2406.01574](https://arxiv.org/abs/2406.01574)
- **Task**: `MMLU-PRO`
- **Measure**: Accuracy (`acc,none`)
- **Shots**: 5-shot
- **num_choices**: 10
- **What it tests**: Refined version of MMLU with 10 choices instead of 4, expert-reviewed for noise reduction, more challenging. Higher quality than the original MMLU.

## Model Categories

| Emoji | Type | Description |
|-------|------|-------------|
| 🟢 | **Pretrained Model** | Base models trained on text corpora via masked modeling |
| 🟩 | **Continuously Pretrained** | Base models further trained on additional corpora (may include IFT/chat data) |
| 🔶 | **Domain Fine-Tuned** | Pretrained models fine-tuned on more data |
| 💬 | **Chat Models** | Fine-tuned via RLHF, DPO, IFT, etc. |
| 🤝 | **Merges & MoErges** | Models merged or fused without additional fine-tuning |

## Results & Datasets

- **Detailed numerical results**: [`open-llm-leaderboard/results`](https://huggingface.co/datasets/open-llm-leaderboard/results/) HF dataset
- **Per-model details**: Click the 📄 emoji next to model names on the leaderboard
- **Community requests & status**: [`open-llm-leaderboard/requests`](https://huggingface.co/datasets/open-llm-leaderboard/requests) HF dataset
- **Flagged models**: Names containing "Flagged" should be ignored — click the link to see the discussion

## Reproducibility

To reproduce leaderboard results locally, use the Hugging Face fork of `lm_eval`:

```bash
git clone git@github.com:huggingface/lm-evaluation-harness.git
cd lm-evaluation-harness
git checkout main
pip install -e .
lm-eval --model_args="pretrained=<your_model>,revision=<your_model_revision>,dtype=<model_dtype>" \
        --tasks=leaderboard \
        --batch_size=auto \
        --output_path=<output_path>
```

**For instruction-tuned models**, add `--apply_chat_template` and `fewshot_as_multiturn` options.

**Note**: Results can vary slightly across batch sizes due to padding differences.

## Precision Tagging

Models on the leaderboard use precision tags in their names:
- `trust_remote_code=True` for models needing custom code
- Common precisions: `float16`, `4bit`, `8bit`
- Format: `@precision:float16` in search

## Search Features

The leaderboard supports advanced search:
- **Combine terms**: `llama; 7b` (union of results)
- **Tag filters**: `@architecture:llama @license:apache`
- **Regex patterns**: `llama-2-(7|13|70)b` (auto-detected)
- **Combined**: `meta @architecture:llama; 7b @license:apache`

## Key Facts

- **Likely score format**: All task metrics report higher-is-better
- **Run on**: `CPU Upgrade` hardware in HF Spaces
- **SDK**: Docker-based Space
- **Org**: `open-llm-leaderboard` (Team plan)
- **Last modified**: 2026-05-27
- **Community discussions**: 1,163 total (4 open as of latest data)
