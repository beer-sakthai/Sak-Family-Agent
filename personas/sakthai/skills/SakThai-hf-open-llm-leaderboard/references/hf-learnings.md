# HF Open LLM Leaderboard v2 — Complete Deep Dive v2

> Research date: 2026-07-25
> Author: SakThai · Main Lead of the House & Master of Hugging Face
> License: MIT

## Summary

Comprehensive deep-dive into the Hugging Face Open LLM Leaderboard v2 (~14K+ likes), covering the full evaluation pipeline, submission lifecycle, results dataset schema, community features, search DSL, reproducibility, and infrastructure. This is a deepening of the existing hf-open-llm-leaderboard skill with new data from live docs and dataset API inspection.

## Key Sources

- Leaderboard Space: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard
- About docs: https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/about
- FAQ: https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/faq
- Results dataset: https://huggingface.co/datasets/open-llm-leaderboard/results
- Requests dataset: https://huggingface.co/datasets/open-llm-leaderboard/requests
- HF lm-eval fork: https://github.com/huggingface/lm-evaluation-harness
- Results detail sets: https://huggingface.co/datasets/open-llm-leaderboard?search=details
- HF blog: https://huggingface.co/spaces/open-llm-leaderboard/blog
- Community: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard/discussions

---

## 1. The 6 Benchmarks (v2)

The leaderboard evaluates on these 6 standardized benchmarks using the EleutherAI lm-eval-harness:

| Benchmark | Paper | Shots | Metric | What It Tests |
|-----------|-------|-------|--------|---------------|
| IFEval | 2311.07911 | 0 | `inst_level_strict_acc` + `prompt_level_strict_acc` | Instruction following & formatting adherence |
| BBH | 2210.09261 | 3 | `acc_norm` (23 subtasks) | Multistep reasoning, arithmetic, logic |
| MATH Lvl 5 | 2103.03874 | 4 | `exact_match` | Hardest high-school competition math |
| GPQA | 2311.12022 | 0 | `acc_norm` (4-choice) | PhD-level domain expertise (gated access) |
| MuSR | 2310.16049 | 0 | `acc_norm` (3 subtasks) | Long-range narrative reasoning (algorithmic) |
| MMLU-PRO | 2406.01574 | 5 | `acc` (10-choice) | Expert-refined knowledge across 57 subjects |

### Task Detail: BBH Subtasks

BBH aggregates **23 subtasks**, each with specific num_choices and shot settings:
- Sports Understanding (2), Navigate (2), Snarks (2), Web of Lies (2)
- Date Understanding (6), Movie Recommendation (6), Ruin Names (6)
- Reasoning about Colored Objects (18), Object Counting (19)
- Logical Deduction: Three Objects (3), Five Objects (5), Seven Objects (7)
- Temporal Sequences (4), Penguins in a Table (5)
- Causal Judgement (2), Formal Fallacies (2), Hyperbaton (2), Disambiguation QA (3)
- Boolean Expressions (2), Geometric Shapes (11)
- Tracking Shuffled Objects: Three (3), Five (5), Seven (7)
- Salient Translation Error Detection (6)

### Task Detail: MATH Lvl 5 Subtasks

MATH Level 5 encompasses 7 subject areas: Algebra, Counting & Probability, Geometry, Intermediate Algebra, Number Theory, Prealgebra, Precalculus. All use `exact_match` metric with 4-shot prompting.

### Task Detail: GPQA Subtasks

GPQA includes three configs: `diamond` (most curated), `extended`, and `main`. The Diamond subset is the most commonly reported.

### Task Detail: MuSR Subtasks

Three narrative types: Murder Mysteries (num_choices=2), Object Placements (num_choices=5), Team Allocation (num_choices=3). All 0-shot.

---

## 2. Submission Lifecycle

### How Submissions Work

1. User navigates to the leaderboard Space and uses the submit form
2. Provide: model name, revision (commit hash), optional precision tag
3. Optionally apply chat template (auto-detected for chat models)
4. The model joins one of 4 queues visible above the submit form
5. Evaluation takes 1–6 hours depending on model size
6. Results appear on the leaderboard and in the results dataset

### Requirements

- Model must be integrated into a **stable version of `transformers`** library
- No `trust_remote_code=True` models accepted (security)
- Models must be **open-source** — the leaderboard does not evaluate closed-source models
- Submissions are tracked per user (stored in requests dataset) for accountability

### Tracking Submission Status

- **Queues**: 4 queues visible above the submit form on the leaderboard
- **Request File**: Check status via the Requests dataset: https://huggingface.co/datasets/open-llm-leaderboard/requests
- **Disappearance**: If a model disappears from queues, it typically means a failure
- **Failure Causes**: Corrupted files, config errors, or hardware/connectivity issues on HF side
- **Reporting Failures**: Create an issue in Community section linking the model's request file; HF team will relaunch if the error is on their side

### Duplicate Handling

Models may appear multiple times due to different commits or precision settings (e.g., float16 vs 4bit). Check via **Precision button** under "column visibility". Duplicates with identical precision and commit should be reported.

### Updating/Renaming

- **Update**: Open an issue requesting removal, then resubmit with new commit hash
- **Rename**: Use @Weyaxi's community tool to request changes, link the PR in a discussion for approval

---

## 3. Results Dataset Schema

The results dataset (`open-llm-leaderboard/results`) uses a deeply nested Parquet structure with 31+ columns. Key top-level fields:

### config — Model & Evaluation Configuration
```python
{
    "model": "hf",
    "model_args": "pretrained=org/model,revision=xxxx",
    "model_dtype": "float16",
    "model_num_parameters": 7000000000,
    "model_revision": "xxxxx",
    "model_sha": "xxxxx",
    "batch_size": "auto",
    "batch_sizes": [32, 16, 8],
    "bootstrap_iters": 1000,
    "fewshot_seed": 1234,
    "numpy_seed": 1234,
    "random_seed": 1234,
    "torch_seed": 1234,
    "device": None,
    "limit": None,
    "use_cache": None
}
```

### results — Nested Scores per Task
Each task has a nested dict with metric values:
```python
{
    "leaderboard": {
        "acc,none": 0.75,
        "acc_norm,none": 0.73,
        "exact_match,none": 0.45,
        "inst_level_strict_acc,none": 0.68,
        "prompt_level_strict_acc,none": 0.71,
        # ... stderr variants for each
    },
    "leaderboard_bbh": { "acc_norm,none": 0.65, ... },
    "leaderboard_bbh_boolean_expressions": { "acc_norm,none": 0.78, ... },
    # ... one entry per BBH subtask + other benchmarks
    "leaderboard_ifeval": { "inst_level_strict_acc,none": 0.82, ... },
    "leaderboard_math_hard": { "exact_match,none": 0.35, ... },
    "leaderboard_gpqa": { "acc_norm,none": 0.52, ... },
    "leaderboard_gpqa_diamond": { "acc_norm,none": 0.48, ... },
    "leaderboard_mmlu_pro": { "acc,none": 0.67, ... },
    "leaderboard_musr": { "acc_norm,none": 0.55, ... },
    "leaderboard_musr_murder_mysteries": { "acc_norm,none": 0.60, ... },
}
```

### groups — Aggregated Results
Groups provide rolled-up scores:
- `leaderboard` — overall average across all tasks
- `leaderboard_bbh` — BBH aggregate
- `leaderboard_gpqa` — GPQA aggregate
- `leaderboard_math_hard` — MATH aggregate
- `leaderboard_musr` — MuSR aggregate

### group_subtasks — Subtask Membership
Lists which configs belong to each group, e.g.:
```python
"leaderboard_musr": [
    "leaderboard_musr_murder_mysteries",
    "leaderboard_musr_object_placements",
    "leaderboard_musr_team_allocation"
]
```

### configs — Task Configurations (full detail)
Each task config stores:
- `task`, `dataset_path`, `dataset_name`, `description`
- `doc_to_text`, `doc_to_target`, `doc_to_choice`
- `num_fewshot`, `fewshot_config` (samples)
- `metric_list`, `output_type`, `repeats`
- `should_decontaminate`, `target_delimiter`, `fewshot_delimiter`
- `generation_kwargs` (for generative tasks like MATH)
- `metadata` (version number)
- `process_docs`, `process_results` (custom processing functions as strings)

### Additional Metadata Fields
- `versions` — lm-eval version per task
- `n-shot` — shot count per task
- `higher_is_better` — bool flag per metric
- `n-samples` — effective vs original sample counts (`{"effective": 12032, "original": 12032}`)
- `git_hash` — lm-eval commit hash
- `date` — evaluation timestamp
- `transformers_version` — e.g., "4.45.0"
- `pretty_env_info` — environment info string
- `tokenizer_pad_token` — list of pad tokens used

---

## 4. Requests Dataset

The requests dataset (`open-llm-leaderboard/requests`) tracks all submission requests:
- Status (queued, running, completed, failed)
- User who submitted (for accountability/spam prevention)
- Model name, revision, precision
- Timestamp
- Links to results

This is the authoritative source for checking whether a pending evaluation is still running.

---

## 5. Community Features

### Model Flagging
- Flag inappropriate models (trained on eval data, unattributed copies, etc.)
- Flagged models show "Flagged" in their name on the leaderboard
- Wrongly flagged models can be appealed via Community discussions
- Click the flagged link to see the discussion about the model

### Official Providers Filter
- "Only Official Providers" button filters trusted, high-quality model providers
- Curated list includes: EleutherAI, CohereForAI, MistralAI, and others
- Dataset of official providers available on the Hub

### Discussions
- 1,163+ total discussions (4 open as of latest data)
- Used for: bug reports, failure appeals, model removal requests, Q&A

---

## 6. Search Syntax (DSL)

The leaderboard supports a powerful search DSL:

### Basic & Advanced Search

| Feature | Syntax | Example |
|---------|--------|---------|
| Multiple terms (union) | `term1; term2` | `llama; 7b` finds models containing "llama" OR "7b" |
| Architecture filter | `@architecture:` | `@architecture:llama` |
| License filter | `@license:` | `@license:apache` |
| Precision filter | `@precision:` | `@precision:float16` |
| Regex patterns | auto-detected | `llama-2-(7\|13\|70)b` matches sizes |
| Combined search | mix all features | `meta @architecture:llama; 7b @license:apache` |

Search is real-time with debouncing for smooth performance. Results are highlighted in the table.

---

## 7. Model Categories

| Emoji | Type | Description |
|-------|------|-------------|
| 🟢 | **Pretrained Model** | Base models trained on text corpora via masked modeling |
| 🟩 | **Continuously Pretrained** | Base models further trained on additional corpora (may include IFT/chat data) |
| 🔶 | **Domain Fine-Tuned** | Pretrained models fine-tuned on more data |
| 💬 | **Chat Models** | Fine-tuned via RLHF, DPO, IFT, etc. |
| 🤝 | **Merges & MoErges** | Models merged or fused without additional fine-tuning |

These categories ensure fair comparisons by grouping models with similar training methodologies.

---

## 8. Score Display & Normalization

The leaderboard displays **normalized scores** by default:
- Normalization adjusts scores so the lower bound = random baseline score
- This ensures fairer averages across tasks with different difficulty levels
- To view **raw (non-normalized)** values: Table Options → Score Display → "Raw"

---

## 9. Reproducibility

Use Hugging Face's fork of lm-eval:

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

**Notes**:
- Results can vary ±1% across batch sizes due to padding differences
- Use `--apply_chat_template` for instruction-tuned models (auto-detects chat template)
- `fewshot_as_multiturn` structures few-shot examples as multi-turn conversations for chat models

---

## 10. Infrastructure

- **Deployment**: Gradio Space on CPU Upgrade hardware
- **SDK**: Docker-based Space (not static Gradio)
- **Evaluation Engine**: fork of EleutherAI lm-evaluation-harness @ `main` branch
- **Results Storage**: HF Dataset (`open-llm-leaderboard/results`) as Parquet
- **Requests Tracking**: HF Dataset (`open-llm-leaderboard/requests`)
- **Details Storage**: Separate details datasets per model
- **Evaluation Queue**: Sequential processing, 1–6 hours per model
- **Org**: `open-llm-leaderboard` (Team plan on Hugging Face)
- **Last modified**: 2026-05-27 (Space)

---

## 11. Known Limitations

1. **Batch-size padding variance**: Scores can shift ±1% depending on batch size
2. **Self-reported categories**: Model categories are user-selected and not always accurate
3. **Non-standardized precision**: float16 vs 4bit models are compared together without adjustment
4. **English-only**: All benchmarks are English; no multilingual evaluation
5. **No multi-turn conversation**: Evaluation is single-turn; no conversational ability assessment
6. **Closed-source exclusion**: The leaderboard explicitly excludes closed-source models, limiting comparison breadth
7. **Contamination risk**: Despite GPQA gating, data contamination remains a concern for popular datasets like MMLU
8. **Compute requirements**: Running the full eval suite requires significant GPU resources not available to all developers

---

## 12. Key Integrations

- **lm-evaluation-harness**: Core evaluation framework (fork maintained by HF)
- **Transformers**: Model loading and inference backend
- **Datasets**: Storing and serving results/requests data
- **Gradio**: Leaderboard UI
- **Spaces**: Deployment environment
- **Discussions**: Community interaction layer
- **Docker**: Containerized evaluation pipeline
