---
name: SakThai-hf-hub-evaluation-results
description: "Hugging Face Hub Evaluation Results \u2014 decentralized benchmark tracking via .eval_results/\
  \ YAML files, benchmark dataset registration with eval.yaml, community-contributed\
  \ PR-based scores, and verified evaluation tokens."
---

# Hub Evaluation Results

The Hugging Face Hub provides a **decentralized system** for tracking model evaluation results. Benchmark datasets host leaderboards, and model repos store evaluation scores that automatically appear on both the model page and the benchmark's leaderboard.

## Architecture

Two sides of the same system:

| Side | What | Where |
|------|------|-------|
| **Benchmark** | Defines tasks, evaluation framework, and leaderboard | Dataset repo with `eval.yaml` at root |
| **Model Result** | Records a score on a benchmark task | Model repo with `.eval_results/*.yaml` |

## Benchmark Datasets

To register a dataset as a benchmark:

1. Create a dataset repo containing your evaluation data
2. Add an `eval.yaml` file to the repo root with benchmark configuration
3. The file is validated at push time
4. (Beta) Contact HF to add it to the allow-list

### eval.yaml Specification

```yaml
name: "Humanity's Last Exam"
version: 1.0.0
description: "A multi-modal benchmark at the frontier of human knowledge..."
evaluation_framework: "inspect-ai"   # enumerable, maintained by HF
tasks:
  - id: hle                          # unique task ID for sub-leaderboard
    config: "default"                # optional, dataset config name
    split: "test"                    # optional, default: "test"
```

**Supported evaluation frameworks** (from `huggingface.js/packages/tasks/src/eval.ts`):

| Framework | Description | URL |
|-----------|-------------|-----|
| `inspect-ai` | Open-source LLM eval framework (AISI/UK AI Safety Institute) | https://inspect.aisi.org.uk/ |
| `exgentic` | Open eval for general-purpose AI agents | https://github.com/Exgentic/exgentic |
| `math-arena` | LLM evaluation on math competitions and olympiads | https://github.com/eth-sri/matharena |
| `mteb` | Multimodal embedding/retrieval evaluation | https://github.com/embeddings-benchmark/mteb |
| `olmocr-bench` | Document-level OCR evaluation framework | https://github.com/allenai/olmocr |
| `harbor` | Agent and language model evaluation | https://github.com/laude-institute/harbor |
| `ifstruct` | Structured-output compliance benchmark | https://github.com/Liquid4All/ifstruct |
| `pier` | CLI agent evaluation (DeepSWE fork) | https://github.com/datacurve-ai/pier |
| `redline-bench` | Multi-turn contract redlining with tracked-change .docx edits | https://github.com/crosbylegal/redline-bench |
| `archipelago` | Running/evaluating AI agents against MCP applications | https://github.com/Mercor-Intelligence/archipelago |
| `benchflow` | Agent evaluation on professional, skill-aware workflows | https://github.com/benchflow-ai/benchflow |
| `apex-evals` | Benchmark suite for LLM evaluation | https://github.com/Mercor-Intelligence/apex-evals |
| `screenspot-pro` | GUI grounding benchmark (1,585 images, 26 tools) | https://github.com/likaixin2000/ScreenSpot-Pro |
| `swe-bench` | LLM performance on software engineering tasks | https://github.com/swe-bench/swe-bench |
| `swe-bench-pro` | Long-horizon software engineering (Scale AI) | https://github.com/scaleapi/SWE-bench_Pro-os |
| `nemo-evaluator` | Reproducible LLM eval across 100+ benchmarks (NVIDIA) | https://github.com/NVIDIA-NeMo/Evaluator |
| `yc-bench` | Long-horizon benchmark: agent plays CEO of AI startup | https://github.com/collinear-ai/yc-bench |
| `open-asr-leaderboard` | Speech recognition model ranking | https://github.com/huggingface/open_asr_leaderboard |
| `mdpbench` | Multilingual document parsing (digital + photographed) | https://github.com/Yuliang-Liu/MultimodalOCR |
| `parsebench` | Enterprise document parsing (tables, charts, faithfulness) | https://github.com/run-llama/ParseBench |
| `video-mme-v2` | Video understanding for multimodal LLMs | https://github.com/MME-Benchmarks/Video-MME-v2 |
| `claw-eval` | Autonomous agent eval across 300 human-verified tasks | https://github.com/claw-eval/claw-eval |
| `researchclawbench` | End-to-end scientific research agent evaluation | https://github.com/InternScience/ResearchClawBench |
| `wildclawbench` | In-the-wild agent eval (60 tasks, 6 domains) | https://github.com/InternLM/WildClawBench |
| `wbench` | Interactive video world model eval (5 dims, 22 metrics) | https://github.com/meituan-longcat/WBench |
| `nanofold` | Data-efficiency benchmark for protein structure prediction | https://github.com/ChrisHayduk/nanoFold-Competition |
| `mmmu` | Massive multi-discipline multimodal understanding | https://mmmu-benchmark.github.io/ |

**Inspect-ai specific fields** (required when `evaluation_framework: inspect-ai`):

- `field_spec` — input/output field mapping (`input`, `target`, `choices`, `input_image`)
- `solvers` — solver pipeline (prompting, self-critique, etc.)
- `scores` — scoring functions

### Real-world Benchmarks

| Benchmark | Dataset ID | Tasks |
|-----------|-----------|-------|
| Humanity's Last Exam | `cais/hle` | hle |
| MMLU-Pro | `TIGER-Lab/MMLU-Pro` | mmlu_pro |
| GPQA | `Idavidrein/gpqa` | gpqa_diamond, gpqa_main, gpqa_extended |
| GSM8K | `openai/gsm8k` | gsm8k |

## Model Evaluation Results

Evaluation scores live in `.eval_results/*.yaml` files in model repos. Each YAML file can contain one or more results.

### Result YAML Format

```yaml
- dataset:
    id: cais/hle                  # Required. Benchmark dataset ID
    task_id: hle                   # Required. Task ID from the eval.yaml
    revision: 5503434ddd753f...    # Optional. Dataset revision hash
  value: 20.90                     # Required. Metric score
  verifyToken: <token>             # Optional. Cryptographic proof from HF Jobs
  date: "2026-07-25"              # Optional. ISO-8601 date or datetime
  source:                          # Optional. Attribution
    url: https://hf.co/spaces/...  # Required if source provided
    name: "Eval Logs"
    user: username
    org: orgname
  notes: "no-tools"               # Optional. Setup details

# Minimal required:
- dataset:
    id: Idavidrein/gpqa
    task_id: gpqa_diamond
  value: 0.412
```

### Badges

| Badge | Condition |
|-------|-----------|
| **verified** | Valid `verifyToken` (ran in HF Jobs with inspect-ai) |
| **community** | Submitted via open PR (not merged to main) |
| **leaderboard** | Links to the benchmark dataset |
| **source** | Links to evaluation logs or external source |

### Community Contributions

Anyone can submit eval results to any model via Pull Request:

1. Go to the model page → "Community" tab → open a Pull Request
2. Add a `.eval_results/*.yaml` file with your results
3. The PR shows as "community-provided" while open

Community scores are visible during PR review. If disputed, the model author closes the PR to remove them.

### Verified Scores (verifyToken)

A `verifyToken` proves the evaluation was run in a reproducible, auditable environment (HF Jobs using inspect-ai or lighteval). Evaluation logs from Inspect can be written directly to HF Storage Buckets.

## API Access

Results appear automatically on:
- The model page (with links to benchmark leaderboard)
- The benchmark dataset's leaderboard (aggregated from all models)

## Growth Cycle Integration

Evaluation results serve as the **permanent ledger of every Trust stage** in the Growth Cycle.

### How to Wire Eval → Cycle

Every `.eval_results/*.yaml` file should carry cycle metadata:

```yaml
- dataset:
    id: llamastack/bfcl_v3
    task_id: simple
  value: 0.80
  date: "2026-07-25"
  source:
    url: https://github.com/beer-sakthai/Sak-Family-Agent
    name: SakThai Growth Cycle — Trust Stage
    user: Nanthasit
    org: Nanthasit
  notes: "Cycle: 2026-07-25 Trust Stage — 4/5 simple tool calls"
```

### Key Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `source.name` | Identifies workflow stage | `"SakThai Growth Cycle — Trust Stage"` |
| `source.user` | Author attribution | `Nanthasit` |
| `source.org` | Org attribution | `Nanthasit` |
| `notes` | Cycle context | `"Cycle: 2026-07-29 Trust Stage"` |

### Workflow

Dream → Hope → Care → Joy → **Trust** → Growth → `.eval_results/*.yaml`

Each improvement cycle: build → verify → record eval → capture lessons. The eval YAML files are the permanent record that a cycle completed its Trust stage.

Tracking ID: `hf-hub-evaluation-results`
