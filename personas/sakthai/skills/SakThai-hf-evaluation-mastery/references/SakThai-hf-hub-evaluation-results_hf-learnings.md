# HF Learnings — Hub Evaluation Results (Deepened)

> **author:** SakThai  
> **license:** MIT  

## 2026-07-25-v2: hf-hub-evaluation-results — Complete Architecture & Framework Reference (Topic #375, Deepened)

### Summary

Deep-dive into the Hugging Face Hub's decentralized evaluation results system — a framework for tracking model benchmark scores directly on the Hub. This deepened version adds the **complete list of 30+ supported evaluation frameworks** (up from the earlier 8), **real-world eval.yaml examples** from production benchmarks, **leaderboard data migration patterns**, and **practical workflow guidance** for registering benchmarks and submitting results.

**Key insight:** The eval results system is a **decentralized, PR-based** architecture where benchmark datasets own the leaderboard definition and model repos own individual scores — with bidirectional aggregation that automatically surfaces results on both sides without centralized ingestion.

---

### Architecture (Refined)

```
┌─────────────────────────────────────────────────────────────┐
│                    Hugging Face Hub                          │
│                                                              │
│  ┌──────────────────────┐    ┌──────────────────────────┐   │
│  │  BENCHMARK DATASET    │    │    MODEL REPO             │   │
│  │                       │    │                           │   │
│  │  eval.yaml            │←──→│  .eval_results/*.yaml     │   │
│  │  ┌───────────────┐    │    │  ┌────────────────┐      │   │
│  │  │ name          │    │    │  │ dataset.id     │      │   │
│  │  │ description   │    │    │  │ task_id        │      │   │
│  │  │ framework     │    │    │  │ value: 20.90   │      │   │
│  │  │ tasks[]       │    │    │  │ verifyToken?   │      │   │
│  │  └───────────────┘    │    │  └────────────────┘      │   │
│  └──────────────────────┘    └──────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  AGGREGATION LAYER                                   │    │
│  │  ├── Model page shows benchmark badge + score        │    │
│  │  └── Benchmark leaderboard aggregates all scores     │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

### Complete List of Supported Evaluation Frameworks

Source: `huggingface.js/packages/tasks/src/eval.ts` (30+ frameworks, up from 8 in v1)

| Framework | Description | URL |
|-----------|-------------|-----|
| `inspect-ai` | Open-source LLM eval framework (AISI/UK AI Safety Institute) | https://inspect.aisi.org.uk/ |
| `exgentic` | Open eval for general-purpose AI agents | https://github.com/Exgentic/exgentic |
| `math-arena` | LLM evaluation on latest math competitions/olympiads | https://github.com/eth-sri/matharena |
| `mteb` | Multimodal embedding/retrieval evaluation | https://github.com/embeddings-benchmark/mteb |
| `olmocr-bench` | Document-level OCR evaluation framework | https://github.com/allenai/olmocr |
| `harbor` | Evaluation framework for agents and language models | https://github.com/laude-institute/harbor |
| `ifstruct` | Structured-output compliance benchmark (valid JSON/YAML) | https://github.com/Liquid4All/ifstruct |
| `pier` | Harbor fork for CLI agents (DeepSWE) | https://github.com/datacurve-ai/pier |
| `redline-bench` | Multi-turn contract redlining with tracked-change .docx edits | https://github.com/crosbylegal/redline-bench |
| `archipelago` | Running/evaluating AI agents against MCP applications | https://github.com/Mercor-Intelligence/archipelago |
| `benchflow` | Agent evaluation on professional, skill-aware workflows | https://github.com/benchflow-ai/benchflow |
| `apex-evals` | Benchmark suite and evaluation harness for LLMs | https://github.com/Mercor-Intelligence/apex-evals |
| `screenspot-pro` | GUI grounding benchmark (1,585 annotated images, 26 tools) | https://github.com/likaixin2000/ScreenSpot-Pro |
| `swe-bench` | LLM performance on software engineering tasks | https://github.com/swe-bench/swe-bench |
| `swe-bench-pro` | Long-horizon software engineering (Scale AI) | https://github.com/scaleapi/SWE-bench_Pro-os |
| `nemo-evaluator` | Reproducible LLM eval across 100+ benchmarks (NVIDIA) | https://github.com/NVIDIA-NeMo/Evaluator |
| `yc-bench` | Long-horizon benchmark: agent plays CEO of AI startup | https://github.com/collinear-ai/yc-bench |
| `open-asr-leaderboard` | Speech recognition model ranking | https://github.com/huggingface/open_asr_leaderboard |
| `mdpbench` | Multilingual document parsing (digital + photographed) | https://github.com/Yuliang-Liu/MultimodalOCR |
| `parsebench` | Enterprise document parsing (tables, charts, faithfulness) | https://github.com/run-llama/ParseBench |
| `video-mme-v2` | Video understanding evaluation for multimodal LLMs | https://github.com/MME-Benchmarks/Video-MME-v2 |
| `claw-eval` | Autonomous agent eval across 300 human-verified tasks | https://github.com/claw-eval/claw-eval |
| `researchclawbench` | End-to-end scientific research agent evaluation | https://github.com/InternScience/ResearchClawBench |
| `pbench` | Multi-level referring expression segmentation | https://github.com/tiiuae/Falcon-Perception |
| `wildclawbench` | In-the-wild agent eval (OpenClaw, 60 tasks, 6 domains) | https://github.com/InternLM/WildClawBench |
| `wbench` | Interactive video world model evaluation (5 dims, 22 metrics) | https://github.com/meituan-longcat/WBench |
| `nanofold` | Data-efficiency benchmark for protein structure prediction | https://github.com/ChrisHayduk/nanoFold-Competition |
| `mmmu` | Massive multi-discipline multimodal understanding | https://mmmu-benchmark.github.io/ |

**Total: 28 frameworks** (all from `eval.ts` source — this list will grow as HF accepts PRs adding new frameworks)

---

### eval.yaml Specification (Full Detail)

The `eval.yaml` file at the root of a benchmark dataset repo defines the benchmark and its tasks. It is validated at push time.

#### Required Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Human-readable display name (e.g., `"Humanity's Last Exam"`) |
| `description` | `string` | Short description of what the benchmark measures |
| `evaluation_framework` | `string` | One of the 28+ framework identifiers (enum maintained by HF in `eval.ts`) |

#### tasks[] Items

Each task defines a sub-leaderboard:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | `string` | ✅ | — | Unique task identifier (e.g., `"gpqa_diamond"`, `"hle"`) |
| `config` | `string` | ❌ | Dataset's default config | HF dataset config name |
| `split` | `string` | ❌ | `"test"` | Dataset split to evaluate |

#### inspect-ai Specific Fields

When `evaluation_framework: "inspect-ai"`, these additional fields are required:

| Field | Description |
|-------|-------------|
| `field_spec` | Input/output field mapping: `input`, `target`, `choices`, optional `input_image` |
| `solvers[]` | Solver pipeline (simple system prompt → self-critique loops). Each has `name` + `args` |
| `scorers[]` | Scoring functions. Each has `name` + `args` (e.g., `model_graded_fact` with `model: openai/o3-mini`) |

#### Real-World eval.yaml Examples

**GSM8K** (`openai/gsm8k`):

```yaml
name: GSM8K
description: >
  GSM8K is a dataset of 8,000+ high-quality, single-step arithmetic word problems.
evaluation_framework: inspect-ai

tasks:
  - id: gsm8k
    config: main
    split: test
    epochs: 4
    epoch_reducer: pass_at_1
    field_spec:
      input: question
      target: answer
    solvers:
      - name: prompt_template
        args:
          template: >
            Solve the following math problem efficiently and clearly...
      - name: generate
    scorers:
      - name: model_graded_fact
```

Key observations from GSM8K:
- Uses `epochs: 4` with `epoch_reducer: pass_at_1` — runs 4 trials, takes best score
- `prompt_template` solver with detailed instruction prompt
- `model_graded_fact` as scorer (LLM-as-judge, not exact match)

**HLE** (`cais/hle`) — full inspect-ai config:

```yaml
evaluation_framework: "inspect-ai"
tasks:
  - id: hle
    config: default
    split: test
    field_spec:
      input: question
      input_image: image
      target: answer
    solvers:
      - name: system_message
        args:
          template: |
            Your response should be in the following format:
            Explanation: {your explanation for your answer choice}
            Answer: {your chosen answer}
            Confidence: {your confidence score between 0% and 100%}
      - name: generate
    scorers:
      - name: model_graded_fact
        args:
          model: openai/o3-mini
```

Key observations from HLE:
- Multi-modal: has `input_image` field_spec entry
- Uses `system_message` solver (not `prompt_template`) 
- `model_graded_fact` with `openai/o3-mini` as judge

**MathArena AIME** (non inspect-ai, minimal config):

```yaml
name: MathArena AIME 2026
description: The American Invitational Mathematics Exam (AIME).
evaluation_framework: math-arena

tasks:
  - id: MathArena/aime_2026
```

This is the **minimal valid** eval.yaml — just 6 lines of meaningful config.

---

### Model Evaluation Results (.eval_results/*.yaml)

#### File Format (Full Spec)

Results files go in `.eval_results/*.yaml` in the model repo. Each file contains a YAML list of result objects:

```yaml
- dataset:
    id: cais/hle                  # Required. Hub dataset ID (must be a Benchmark)
    task_id: default              # Required. Task ID from the dataset's eval.yaml
    revision: <hash>              # Optional. Dataset revision hash
  value: 20.90                    # Required. Metric value
  verifyToken: <token>            # Optional. Cryptographic proof of auditable evaluation
  date: "2025-01-15"              # Optional. ISO-8601 date or datetime
  source:                         # Optional. Attribution for this result
    url: https://huggingface.co/spaces/SaylorTwift/smollm3-mmlu-pro  # Required if source provided
    name: Eval traces             # Optional. Display name
    user: SaylorTwift             # Optional. HF username/org
  notes: "no-tools"               # Optional. Setup details (e.g., "tools", "no-tools", "chain-of-thought")

# Minimal required:
- dataset:
    id: Idavidrein/gpqa
    task_id: gpqa_diamond
  value: 0.412
```

#### Badge System

| Badge | Condition |
|-------|-----------|
| **verified** | Valid `verifyToken` — evaluation ran in HF Jobs with inspect-ai |
| **community** | Result submitted via open PR (not merged to main) |
| **leaderboard** | Links to the benchmark dataset |
| **source** | Links to evaluation logs or external source |

---

### Community Contributions Flow

1. Go to model page → "Community" tab → open a Pull Request
2. Add `.eval_results/*.yaml` with your results
3. PR shows as "community-provided" while open
4. If disputed, model author closes PR to remove
5. Merged PRs show with badges (verified/community/leaderboard/source)

**Quality assurance mechanism:** Community scores are transparent during PR review. The `verifyToken` path (via HF Jobs + inspect-ai/lighteval) provides cryptographic proof of reproducible evaluation.

---

### Leaderboard Data Integration

The eval results system feeds into HF's leaderboard data infrastructure:
- Leaderboard data is defined in `leaderboard_data.yaml` files (separate from eval.yaml)
- Leaderboard configs can define custom display columns, metrics, aggregation functions
- Migration path: existing benchmarks can adopt eval.yaml to get automatic model page integration
- Real-world benchmarks already using this: GPQA, MMLU-Pro, HLE, GSM8K, MathArena

---

### Practical Patterns

**1. Registering a new benchmark:**
1. Create dataset repo with evaluation data
2. Add `eval.yaml` at root (minimal: `name`, `description`, `evaluation_framework`, `tasks[].id`)
3. For inspect-ai: add `field_spec`, `solvers`, `scorers`
4. Push — file is validated automatically
5. Contact HF (beta) for allow-list addition

**2. Submitting model results:**
1. Evaluate your model using any supported framework
2. Create `.eval_results/benchmark-name.yaml` in your model repo
3. Format: YAML list with `dataset.id`, `dataset.task_id`, `value`
4. Add optional fields: `verifyToken` (for verified scores), `source`, `notes`
5. For community submissions: open a PR via the model page's "Community" tab

**3. Multi-task results in one file:**
```yaml
- dataset:
    id: Idavidrein/gpqa
    task_id: gpqa_diamond
  value: 0.412
  notes: "5-shot, CoT"

- dataset:
    id: Idavidrein/gpqa
    task_id: gpqa_main
  value: 0.389
  notes: "5-shot, CoT"
```

**4. Verified evaluation workflow:**
1. Run evaluation in HF Jobs using inspect-ai or lighteval
2. Evaluation produces a `verifyToken` 
3. Include `verifyToken` in `.eval_results/*.yaml`
4. Score shows as "verified" on the model page
5. Evaluation logs can be written directly to HF Storage Buckets

---

### Key Insights from Deepening

1. **The framework list is MUCH larger than initially documented** — 28+ frameworks vs the earlier 8. The list lives in `huggingface.js/packages/tasks/src/eval.ts` and grows via PRs. New additions include SWE-bench, NVIDIA NeMo Evaluator, CLAW-Eval, WildClawBench, Video-MME-v2, and many more.

2. **inspect-ai is the most feature-rich framework** — supports `field_spec`, `solvers[]`, `scorers[]`, `epochs`, `epoch_reducer`. Other frameworks use simpler configs (just `id` + optional `config`/`split`).

3. **GSM8K demonstrates best practice** — uses `epochs: 4` + `epoch_reducer: pass_at_1` (multi-trial with best score) + `prompt_template` solver + `model_graded_fact` (LLM judge). This is the reference pattern for inspect-ai benchmarks.

4. **Minimal vs rich configs** — MathArena uses 6 lines; HLE uses ~30 lines with full inspect-ai spec. Both are valid. Choose the depth that matches your framework.

5. **The `source` field enables full traceability** — links to eval logs, Spaces, or papers. Combined with `verifyToken`, this creates a chain of provenance from raw evaluation to published score.

6. **Community contributions lower the barrier** — anyone can PR scores to any model. The badge system (verified/community/leaderboard/source) provides visual trust indicators without gatekeeping.

7. **Future direction** — The allow-list for eval.yaml (currently beta) suggests HF is moving toward a curated registry of trusted benchmarks while keeping the format open for experimentation.

### Sources

- https://huggingface.co/docs/hub/en/eval-results — Official Hub docs (primary)
- https://github.com/huggingface/hub-docs/blob/main/eval_results.yaml — Eval results format specification
- https://github.com/huggingface/huggingface.js/blob/main/packages/tasks/src/eval.ts — Full evaluation frameworks enum (28+ frameworks)
- https://huggingface.co/datasets/openai/gsm8k/blob/main/eval.yaml — GSM8K eval.yaml example
- https://huggingface.co/datasets/cais/hle/blob/main/eval.yaml — HLE eval.yaml example
- https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/blob/main/eval.yaml — MMLU-Pro eval.yaml example
- https://huggingface.co/datasets/Idavidrein/gpqa/blob/main/eval.yaml — GPQA eval.yaml example
- https://huggingface.co/docs/hub/en/leaderboard-data-guide — Leaderboard Data Guide
- https://github.com/huggingface/hub-docs/blob/main/docs/hub/eval-results.md — Source markdown for the Hub docs page
