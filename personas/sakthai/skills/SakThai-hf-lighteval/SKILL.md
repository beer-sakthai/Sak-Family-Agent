---
name: SakThai-hf-lighteval
description: "Complete reference for Hugging Face LightEval \u2014 the all-in-one LLM evaluation\
  \ toolkit supporting 1000+ tasks across 8 backends (inspect-ai, accelerate, vllm,\
  \ sglang, nanotron, TGI, Inference Endpoints, LiteLLM, Inference Providers). Covers\
  \ CLI usage, Python API, custom tasks/metrics, result management, backend configuration,\
  \ and zero-cost evaluation patterns."
---

# LightEval — Complete Reference

LightEval is Hugging Face's all-in-one toolkit for evaluating LLMs across multiple backends. Built and maintained by the Hugging Face Leaderboard and Evals Team, it provides a unified interface for evaluating models whether they are being served remotely or loaded in memory.

- **GitHub**: https://github.com/huggingface/lighteval
- **Documentation**: https://huggingface.co/docs/lighteval/main/en/index
- **Stars**: ~2,500
- **License**: MIT
- **Latest Version**: 0.11.x

## 1. Architecture Overview

### Core Pipeline

```
CLI/API → Registry (task discovery) → Pipeline (evaluation orchestrator)
  ├── Tasks: Loaded from suite directories
  ├── Model: Abstracted via LightevalModel interface
  └── Metrics: Sample-level + corpus-level
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| `Pipeline` | `pipeline.py` | Main orchestrator (load tasks, run model, compute metrics) |
| `Registry` | `tasks/registry.py` | Task discovery and loading from suite directories |
| `LightevalTask` | `tasks/lighteval_task.py` | Single evaluation task with dataset, metrics, prompt templates |
| `ModelConfig` | `models/abstract_model.py` | Base configuration for all model types |
| `LightevalModel` | `models/abstract_model.py` | Abstract interface for model inference |
| `EvaluationTracker` | `logging/evaluation_tracker.py` | Results logging and Hub push |

## 2. Installation

```bash
pip install lighteval
```

### Extras

| Extra | Purpose |
|-------|---------|
| `[dev]` | Development (code quality, tests) |
| `[dev-gpu]` | GPU development with vLLM |
| `[vllm]` | vLLM backend support |
| `[nanotron]` | Nanotron distributed training |
| `[sglang]` | SGLang backend support |

## 3. CLI Commands — 8 Evaluation Backends

LightEval offers multiple entry points via `lighteval <command>`:

| Command | Backend | Best For |
|---------|---------|----------|
| `lighteval eval` | **inspect-ai** (preferred) | All API-served models, zero local GPU |
| `lighteval accelerate` | 🤗 Accelerate | CPU/single-GPU/multi-GPU with Transformers |
| `lighteval vllm` | vLLM | GPU-accelerated with vLLM serving |
| `lighteval sglang` | SGLang | GPU-accelerated with SGLang |
| `lighteval nanotron` | Nanotron | Distributed multi-node evaluation |
| `lighteval endpoint inference-endpoint` | HF Inference Endpoints | HF-hosted dedicated endpoints |
| `lighteval endpoint tgi` | TGI (local) | Self-hosted Text Generation Inference |
| `lighteval endpoint litellm` | LiteLLM | Any OpenAI-compatible API |
| `lighteval endpoint inference-providers` | HF Inference Providers | Serverless HF inference |
| `lighteval custom` | Custom | Any custom model implementation |

### 3.1 Preferred Backend: `lighteval eval` (inspect-ai)

The `eval` command uses **inspect-ai** from the UK AI Safety Institute as the evaluation engine. This is the preferred backend for all API-served models.

**Minimal usage:**
```bash
# Evaluate on a single task
lighteval eval "hf-inference-providers/openai/gpt-oss-20b" gpqa:diamond
```

**Full syntax:**
```bash
lighteval eval <models> <tasks> [options]
```

**Key options:**
```
Modeling Parameters:
  --model-base-url TEXT        Base URL for model API
  --model-roles TEXT           Model creation args (dict or path to JSON/YAML)
  --max-tokens INT             Max tokens for generation
  --temperature FLOAT          Sampling temperature
  --top-p FLOAT                Nucleus sampling parameter
  --seed INT                   Random seed for reproducibility
  --system-message TEXT        Override system message
  --stop-seqs TEXT             Stop sequences
  --num-choices INT            Number of choices per step
  --reasoning-effort TEXT      Reasoning effort: minimal/low/medium/high

Task Parameters:
  --custom-tasks PATH          Python file with custom LightevalTaskConfig
  --max-samples INT            Max samples per task/subtask
  --epochs INT                 Number of evaluation epochs (default: 1)
  --epochs-reducer TEXT        Aggregation: mean/median/mode/max/at_least_{n}/pass_at_{k}

Connection Parameters:
  --max-connections INT        Max concurrent connections (default: 50)
  --timeout INT                Per-connection timeout (default: 30s)
  --max-retries INT            Max retries (default: 5)

Logging:
  --log-dir PATH               Log directory
  --display TEXT               Display mode: rich/full/conversations/plain/log/none
  --repo-id TEXT                Push results to HF Hub Space
  --public                     Make results public
```

### 3.2 Accelerate Backend

For evaluating models loaded via `transformers`:

```bash
lighteval accelerate "meta-llama/Llama-3.1-8B-Instruct" "gsm8k" \
  --max-samples 10 \
  --output-dir ./results
```

### 3.3 Endpoint Subcommands

```bash
# Hugging Face Inference Endpoints
lighteval endpoint inference-endpoint "https://your-endpoint.us-east-1.aws.endpoints.huggingface.cloud" "gsm8k"

# Local TGI
lighteval endpoint tgi "http://localhost:8080" "mmlu"

# LiteLLM (any provider)
lighteval endpoint litellm "gpt-3.5-turbo" "mmlu_pro"

# Inference Providers
lighteval endpoint inference-providers "meta-llama/Llama-3.1-8B-Instruct" "mmlu_pro"
```

### 3.4 Special Model Syntax

For evaluating across all inference providers:
```bash
lighteval eval "hf-inference-providers/meta-llama/Llama-3.1-8B-Instruct:all" "gsm8k"
```
The `:all` suffix auto-discovers all live providers via the HF Models API `inferenceProviderMapping`.

## 4. Supported Tasks (1000+)

LightEval organizes tasks into **suites** and **sub-suites**:

### Core Suites (always available)

| Suite | Examples |
|-------|----------|
| `lighteval` | LightEval curated tasks |
| `leaderboard` | Open LLM Leaderboard tasks |
| `harness` | LM Evaluation Harness compatibility |
| `helm` | HELM benchmark tasks |
| `bigbench` | BIG-Bench tasks |
| `original` | Original implementation tasks |
| `extended` | Extended community tasks |
| `custom` | User-defined tasks |
| `test` | Testing/debugging tasks |

### Optional Suites

| Suite | Description |
|-------|-------------|
| `community` | Community-contributed tasks |
| `multilingual` | Multilingual evaluation tasks |

### Popular Task Names

| Task | Suite | Description |
|------|-------|-------------|
| `mmlu` | lighteval | Massive Multitask Language Understanding |
| `mmlu_pro` | leaderboard | MMLU-Pro (10 choices) |
| `gsm8k` | lighteval | Grade School Math 8K |
| `math` | lighteval | MATH (Mathematics Aptitude Test) |
| `math_500` | lighteval | MATH subset (500 problems) |
| `gpqa` | lighteval | Graduate-Level Google-Proof Q&A |
| `bbh` | lighteval | Big Bench Hard (23 subtasks) |
| `ifeval` | leaderboard | Instruction Following Evaluation |
| `musr` | leaderboard | Multistep Soft Reasoning |
| `hellaswag` | lighteval | Commonsense NLI |
| `winogrande` | lighteval | Winograd Schema Challenge |
| `truthfulqa` | lighteval | TruthfulQA |
| `arc` | lighteval | AI2 Reasoning Challenge |
| `hle` | lighteval | Humanity's Last Exam |
| `simpleqa` | lighteval | Simple Question Answering |
| `aime24`, `aime25` | lighteval | American Invitational Mathematics Exam |
| `ruler` | lighteval | Long Context Evaluation |
| `drop` | harness | Discrete Reasoning Over Paragraphs |
| `anli` | lighteval | Adversarial NLI |
| `bbq` | lighteval | Bias Benchmark for QA |
| `blimp` | lighteval | Benchmark of Linguistic Minimal Pairs |
| `boolq` | lighteval | Boolean Questions |
| `commonsenseqa` | lighteval | Commonsense QA |
| `agieval` | lighteval | AGI Evaluation |
| `olympiad_bench` | lighteval | Olympiad Bench |
| `gsm_plus` | lighteval | GSM-Plus (variations of GSM8K) |
| `flores200` | multilingual | 200-language translation evaluation |
| `xcopa` | multilingual | Cross-lingual Choice of Plausible Alternatives |
| `xquad` | multilingual | Cross-lingual SQuAD |

### Task Specification Syntax

```bash
# Single task
lighteval eval "model" "gsm8k"

# Subtask filtering
lighteval eval "model" "bbh:boolean_expressions"

# Multiple tasks
lighteval eval "model" "gsm8k,mmlu_pro,ifeval"

# All subtasks of a suite
lighteval eval "model" "leaderboard"
```

## 5. Python API

### 5.1 Using inspect-ai Backend

```python
from lighteval.tasks.registry import Registry

# Load tasks
registry = Registry(tasks="gsm8k")
task_configs = registry.task_to_configs
```

### 5.2 Using Accelerate/Transformers Backend

```python
from transformers import AutoModelForCausalLM
from lighteval.logging.evaluation_tracker import EvaluationTracker
from lighteval.models.transformers.transformers_model import (
    TransformersModel, TransformersModelConfig
)
from lighteval.pipeline import ParallelismManager, Pipeline, PipelineParameters

MODEL_NAME = "meta-llama/Meta-Llama-3-8B-Instruct"
BENCHMARKS = "gsm8k"

# Setup tracking
evaluation_tracker = EvaluationTracker(output_dir="./results")

# Configure pipeline
pipeline_params = PipelineParameters(
    launcher_type=ParallelismManager.NONE,
    max_samples=10  # limit for testing
)

# Load model
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, device_map="auto")
config = TransformersModelConfig(model_name=MODEL_NAME, batch_size=1)
lighteval_model = TransformersModel.from_model(model, config)

# Create and run pipeline
pipeline = Pipeline(
    model=lighteval_model,
    pipeline_parameters=pipeline_params,
    evaluation_tracker=evaluation_tracker,
    tasks=BENCHMARKS,
)

results = pipeline.evaluate()
pipeline.show_results()
results = pipeline.get_results()
```

### 5.3 Model Configuration

```python
from lighteval.models.abstract_model import ModelConfig

config = ModelConfig(
    model_name="meta-llama/Llama-3.1-8B-Instruct",
    generation_parameters=GenerationParameters(
        temperature=0.7,
        top_p=0.9,
        max_new_tokens=512,
    ),
    system_prompt="You are a helpful assistant.",
    cache_dir="~/.cache/huggingface/lighteval",
)
```

Configuration can also be loaded from YAML:
```yaml
# model_config.yaml
model_parameters:
  model_name: "meta-llama/Llama-3.1-8B-Instruct"
  generation_parameters:
    temperature: 0.7
    top_p: 0.9
  system_prompt: "You are a helpful assistant."
```

```python
config = ModelConfig.from_path("model_config.yaml")
```

### 5.4 PipelineParameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `launcher_type` | `ParallelismManager` | required | NONE, ACCELERATE, VLLM, SGLANG, NANOTRON, TGI, OPENAI, CUSTOM |
| `dataset_loading_processes` | `int` | 1 | Parallel processes for dataset loading |
| `num_fewshot_seeds` | `int` | 1 | Different random seeds for few-shot |
| `max_samples` | `int` | None | Limit samples per task |
| `remove_reasoning_tags` | `bool` | True | Strip reasoning tags (e.g. `<think>`) |
| `reasoning_tags` | `str` | `[('<think>', '</think>')]` | Tag pairs to remove |
| `bootstrap_iters` | `int` | 1000 | Bootstrap iterations for confidence intervals |
| `load_responses_from_details_date_id` | `str` | None | Re-evaluate from cached model responses |

## 6. Custom Tasks

### 6.1 Define a Custom Task

Create a Python file with a `TASKS_TABLE` list of `LightevalTaskConfig`:

```python
# my_custom_task.py
from lighteval.tasks.lighteval_task import LightevalTaskConfig

TASKS_TABLE = [
    LightevalTaskConfig(
        name="my_custom_qa",
        suite="custom",
        prompt_function="prompt_fn",  # function name in this module
        hf_repo="my-org/my-dataset",
        hf_subset="default",
        hf_avail_splits=["train", "test"],
        evaluation_splits=["test"],
        few_shots=[],
        metric=["my_metric"],
    )
]

def prompt_fn(line, example):
    """Return the prompt for a dataset example."""
    return f"Question: {line['question']}\nAnswer:"
```

### 6.2 Use Custom Tasks

```bash
lighteval eval "model" "my_custom_qa" --custom-tasks ./my_custom_task.py
```

Or with the Python API:
```python
registry = Registry(
    tasks="my_custom_qa",
    custom_tasks="./my_custom_task.py",
)
```

## 7. Custom Metrics

LightEval supports three metric types:

| Metric Type | Class | Description |
|-------------|-------|-------------|
| Sample-level | `SampleLevelMetric` | Per-example score (exact match, F1, etc.) |
| Sample-level Grouping | `SampleLevelMetricGrouping` | Per-example with grouped aggregation |
| Corpus-level | `CorpusLevelMetric` | Corpus-wide score (perplexity, BLEU, etc.) |
| Corpus-level Grouping | `CorpusLevelMetricGrouping` | Corpus-wide with grouped aggregation |

### Built-in Metrics

| Metric | Class | Sample Method | Description |
|--------|-------|---------------|-------------|
| Exact Match | `ExactMatches` | Generative | String equality |
| F1 Score | `F1_score` | Generative | Token-wise F1 |
| BLEU | `BLEU` | Generative | BLEU score |
| ROUGE | `ROUGE` | Generative | ROUGE-L |
| BERTScore | `BertScore` | Generative | BERT-based similarity |
| Perplexity | `CorpusLevelPerplexityMetric` | Perplexity | Token perplexity |
| Accuracy | `LoglikelihoodAcc` | Logprobs | Log-likelihood accuracy |
| Gold Likelihood | `AccGoldLikelihood` | Logprobs | Gold token likelihood |
| MRR | `MRR` | Logprobs | Mean Reciprocal Rank |
| Pass@K | `PassAtK` | Generative | Code pass rate |
| Maj@N | `MajAtN` | Generative | Majority voting |
| JudgeLLM (SimpleQA) | `JudgeLLMSimpleQA` | Generative | LLM-as-Judge |
| Faithfulness | `Faithfulness` | Generative | Factual consistency |
| Extractiveness | `Extractiveness` | Generative | Source overlap |

### Sampling Methods

Metrics are associated with sampling methods:

| Sampling Method | Enum Value | Description |
|-----------------|------------|-------------|
| Generative | `GENERATIVE` | Free text generation (greedy_until) |
| Logprobs | `LOGPROBS` | Log likelihood of target (loglikelihood) |
| Perplexity | `PERPLEXITY` | Rolling perplexity (loglikelihood_rolling) |

### Define a Custom Metric

```python
from lighteval.metrics.metrics_sample import SampleLevelMetric
from lighteval.metrics.utils.metric_utils import SampleLevelMetric, SamplingMethod

def my_custom_score(predictions, references):
    """Compute custom score."""
    correct = sum(1 for p, r in zip(predictions, references) if p.strip() == r.strip())
    return correct / len(predictions) if predictions else 0.0

my_metric = SampleLevelMetric(
    metric_name="my_custom_acc",
    sample_level_fn=...,  # Your metric function
    category=SamplingMethod.GENERATIVE,
)
```

### Inspect-ai Metrics Integration

When using `lighteval eval`, metrics are built as inspect-ai scorers:

```python
from inspect_ai.scorer import Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import TaskState

@scorer(metrics=[accuracy(), stderr()])
def my_custom_scorer():
    async def score(state: TaskState, target: Target):
        return Score(
            value="C" if state.output.completion == target.text else "I",
            explanation=state.output.completion,
            answer=state.output.completion,
        )
    return score
```

## 8. Results Management

### 8.1 Output Structure

Results are saved to `--output-dir` (default: `./results`):

```
results/
├── <date_id>_<model_name>/
│   ├── results.json           # Aggregated results
│   ├── details/               # Per-sample details (if --save-details)
│   │   ├── <task_name>_0.json
│   │   └── ...
│   ├── logs/                  # TensorBoard logs (if --push-to-tensorboard)
│   └── config.json            # Evaluation configuration
```

### 8.2 Push to Hub

```bash
lighteval eval "model" "gsm8k" \
  --repo-id "my-org/my-eval-results" \
  --public
```

This creates a Hugging Face Space with results browsable in the browser.

### 8.3 Re-evaluate from Cached Responses

```bash
lighteval accelerate "model" "gsm8k" \
  --load-responses-from-details-date-id "<date_id>"
```

### 8.4 Results Table Format

LightEval uses the `results_to_markdown_table` utility to produce formatted tables:

```
| Model | gsm8k | gpqa | mmlu_pro | average |
|-------|-------|------|----------|---------|
| model_A | 82.5 | 35.2 | 68.1 | 61.93 |
| model_B | 85.0 | 38.7 | 72.3 | 65.33 |
```

## 9. Backend Details

### 9.1 Parallelism Management

| Backend | Parallelism Manager | Multi-GPU | Distributed |
|---------|-------------------|-----------|-------------|
| NONE (in-memory) | `NONE` | No | No |
| Accelerate | `ACCELERATE` | Yes | Single node |
| vLLM | `VLLM` | Yes | Single node |
| SGLang | `SGLANG` | Yes | Single node |
| Nanotron | `NANOTRON` | Yes | Multi-node (TP, PP, DP) |
| TGI | `TGI` | No (API) | No (API) |
| OpenAI | `OPENAI` | No (API) | No (API) |

### 9.2 Model Backend Discovery

The inspect-ai backend auto-discovers providers:
```python
def _get_huggingface_providers(model_id: str):
    """Discover live HF Inference Providers for a model."""
    url = f"https://huggingface.co/api/models/{model_id}"
    params = {"expand[]": "inferenceProviderMapping"}
    response = requests.get(url, params=params)
    data = response.json()
    providers = data.get("inferenceProviderMapping", {})
    return [p for p, info in providers.items() if info.get("status") == "live"]
```

### 9.3 Task Loading Flow

1. `Registry` takes task string (e.g., "gsm8k")
2. Matches against suite directories to find `LightevalTaskConfig`
3. Loads dataset from Hugging Face Hub
4. Creates `LightevalTask` instances with prompt functions + metrics
5. Pipeline batches requests by `SamplingMethod` (GENERATIVE, LOGPROBS, PERPLEXITY)
6. Model executes requests asynchronously or synchronously
7. Metrics computed per task; results aggregated with optional bootstrapping

## 10. Zero-Cost Evaluation

### 10.1 Free Inference Providers

```bash
# Using HF Inference Providers (free tier available)
lighteval eval "hf-inference-providers/meta-llama/Llama-3.1-8B-Instruct:nebius" "gsm8k"
```

### 10.2 Small Models on CPU

```bash
# Evaluate a small model on CPU with limited samples
lighteval accelerate "Qwen/Qwen2.5-0.5B-Instruct" "gsm8k" \
  --max-samples 10 \
  --output-dir ./results
```

### 10.3 LiteLLM with Free APIs

```bash
# Use any free API provider via LiteLLM
lighteval endpoint litellm "gemini/gemini-2.0-flash-exp" "gsm8k" \
  --max-samples 5
```

### 10.4 Hub Hosting for Results

Pushing results to the Hugging Face Hub as a Space is free:

```bash
lighteval eval "hf-inference-providers/gpt-oss-20b" "gsm8k" \
  --repo-id "beer-sakthai/lighteval-results" \
  --public \
  --max-samples 10
```

## 11. Task Suite Architecture

LightEval stores task definitions as Python files in suite directories:

```
src/lighteval/tasks/
├── registry.py              # Registry + task discovery
├── lighteval_task.py        # LightevalTask + LightevalTaskConfig
├── requests.py              # Doc/SamplingMethod definitions
├── suites/                  # Task definition directories
│   ├── lighteval/           # LightEval curated tasks
│   │   ├── gsm8k.py
│   │   ├── mmlu.py
│   │   └── ...
│   ├── leaderboard/         # Open LLM Leaderboard tasks
│   ├── harness/             # LM Eval Harness compatibility
│   ├── helm/                # HELM tasks
│   ├── bigbench/            # BIG-Bench tasks
│   ├── custom/              # User custom tasks
│   ├── extended/            # Extended tasks
│   ├── multilingual/        # Multilingual tasks
│   └── test/               # Test/debug tasks
community_tasks/             # Community-contributed tasks
```

A task definition file exports a `TASKS_TABLE`:
```python
from lighteval.tasks.lighteval_task import LightevalTaskConfig
from lighteval.metrics import Metrics

TASKS_TABLE = [
    LightevalTaskConfig(
        name="gsm8k",
        suite="lighteval",
        prompt_function="gsm8k_prompt_fn",
        hf_repo="gsm8k",
        hf_subset="main",
        hf_avail_splits=["train", "test"],
        evaluation_splits=["test"],
        few_shots=[],
        metric=["gsm8k"],
    )
]
```

## References

- LightEval GitHub: https://github.com/huggingface/lighteval
- LightEval Documentation: https://huggingface.co/docs/lighteval/main/en/index
- Inspect-ai: https://inspect.aisi.org.uk/
- HF Inference Providers: https://huggingface.co/docs/inference-providers/en/index
- Open LLM Leaderboard: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard
