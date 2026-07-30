# LM Evaluation Harness — Complete Reference

**Topic:** lm-evaluation-harness-complete-reference
**Date:** 2026-07-24
**Author:** SakThai
**License:** MIT

## Summary

Complete deep-dive into the [EleutherAI LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness) — the de facto standard framework for evaluating large language models on academic benchmarks. This document covers the v0.4.0+ architecture including the refactored CLI (`lm-eval run`/`ls`/`validate` subcommands), YAML config file support, the Python API (`simple_evaluate`, `EvaluatorConfig`, `evaluate`), all supported model backends (HF transformers, vLLM, SGLang, nemo, megatron, API models), task creation (YAML config with Jinja2 templating), filter pipelines, evaluation of thinking/reasoning models (Qwen3, DeepSeek-R1), multi-GPU parallelism strategies, and the HuggingFace Hub logging integration.

---

## Key Discovery #1: CLI Refactored to Subcommands

The v0.4.0 release (2025/12) overhauled the CLI from a single-command flat interface to structured subcommands:

```bash
# New structure
lm-eval run       # Run evaluations
lm-eval ls        # List tasks/groups/subtasks/tags
lm-eval validate  # Validate task configs

# Legacy flat syntax still works (auto-inserts "run")
lm_eval --model hf --tasks hellaswag    # still works, same as:
lm-eval run --model hf --tasks hellaswag
```

**Key details:**
- `lm-eval ls tasks` — list all available tasks including groups, subtasks, and tags
- `lm-eval ls groups` — list only top-level task groups (mmlu, glue, superglue, etc.)
- `lm-eval ls subtasks` — list only individual subtask names
- `lm-eval ls tags` — list task categories (reasoning, knowledge, etc.)
- `lm-eval validate --tasks <names>` — validate config without running; checks existence, YAML syntax, dataset access, metrics, filters, templates
- `--config` / `-C` — YAML config file. CLI args override config file values.

---

## Key Discovery #2: Lighter Install — Model Backends Are Extras

Since v0.4.0, the base `lm_eval` package no longer bundles `transformers`/`torch`. Model backends are installed separately via extras:

```bash
pip install "lm_eval[hf]"      # HuggingFace transformers
pip install "lm_eval[vllm]"    # vLLM inference server
pip install "lm_eval[sglang]"  # SGLang runtime
pip install "lm_eval[api]"     # OpenAI/Anthropic/third-party APIs
pip install "lm_eval[hf,vllm,api]"  # multiple backends
```

This reduces the base install footprint and lets users pull only what they need.

---

## Key Discovery #3: Thinking/Reasoning Model Support

Models like Qwen3, DeepSeek-R1, and Phi-4-mini produce CoT reasoning traces before their final answer. Two model args handle this:

```bash
lm-eval run --model hf \
  --model_args pretrained=Qwen/Qwen3-32B,enable_thinking=True,think_end_token=200008 \
  --tasks gsm8k --apply_chat_template
```

- `enable_thinking=True` — activates thinking mode in the chat template
- `think_end_token` — (required when `enable_thinking=True`) delimiter marking the end of the thinking section. Everything up to and including the last occurrence is stripped before metrics.
- **HF backend**: accepts string or **token ID** (int). Token ID is more reliable — avoids edge cases where the string appears in normal text.
- **vLLM/SGLang backends**: only accept string form (e.g., `think_end_token="</think>"`)
- Only compatible with `generate_until` (generative) tasks — NOT with loglikelihood-based tasks
- Find the correct token in the model's `tokenizer_config.json` (look for the token closing the thinking block in the chat template)

---

## Key Discovery #4: Python API — Three Entry Points

### 1. `simple_evaluate()` (recommended for most use cases)
```python
import lm_eval

results = lm_eval.simple_evaluate(
    model="hf",
    model_args="pretrained=gpt2,dtype=float32",
    tasks=["hellaswag", "arc_easy"],
    num_fewshot=5,
    batch_size=8,
    device="cuda:0",
)

# results["results"]["hellaswag"]["acc"] -> 0.45...
```

Supports passing a pre-initialized LM instance, custom `TaskManager`, external task paths, and all CLI-equivalent kwargs.

### 2. `EvaluatorConfig` (config-driven, from YAML or dataclass)
```python
from lm_eval.config.evaluate_config import EvaluatorConfig

config = EvaluatorConfig.from_config("eval_config.yaml")
task_manager = config.process_tasks()
results = lm_eval.simple_evaluate(
    model=config.model,
    model_args=config.model_args,
    tasks=config.tasks,
    num_fewshot=config.num_fewshot,
    batch_size=config.batch_size,
    device=config.device,
    task_manager=task_manager,
)
```

### 3. `evaluate()` (low-level, full control)
Passes pre-built task dictionaries and raw LM objects. Best for custom orchestration.

### Return value structure:
```python
{
    "results": {"task_name": {"metric": value, "metric,stderr": stderr}},
    "configs": {...}, "versions": {...}, "n-shot": {...},
    "higher_is_better": {...}, "n-samples": {...},
    "samples": {...}  # only if log_samples=True
}
```

---

## Key Discovery #5: YAML Config File Format (Reusable Evaluation Plans)

All CLI arguments can be specified in a YAML file:

```yaml
model: hf
model_args:
  pretrained: meta-llama/Llama-2-7b-hf
  dtype: bfloat16
tasks:
  - hellaswag
  - arc_easy
  - mmlu
num_fewshot: 5
batch_size: auto
device: cuda:0
output_path: ./results/llama2-7b/
log_samples: true
wandb_args:
  project: llm-evals
  name: llama2-7b-baseline
hf_hub_log_args:
  hub_results_org: my-org
  results_repo_name: llm-eval-results
  push_results_to_hub: true
  public_repo: false
```

Then run with: `lm-eval run --config eval_config.yaml`

---

## Key Discovery #6: Task Configuration Format

Tasks are defined in YAML using `TaskConfig` fields. Core structure:

```yaml
task: mmlu_anatomy
dataset_path: mmlu
dataset_name: anatomy
validation_split: validation
test_split: test
fewshot_split: validation
output_type: multiple_choice    # or: generate_until, loglikelihood, loglikelihood_rolling
doc_to_text: "{{question}}\nA. {{choices[0]}}\nB. {{choices[1]}}\nC. {{choices[2]}}\nD. {{choices[3]}}\nAnswer:"
doc_to_target: "{{answer}}"      # returns index into doc_to_choice
doc_to_choice: ["A", "B", "C", "D"]
metric_list:
  - metric: acc
    aggregation: mean
    higher_is_better: true
metadata:
  version: 1.0
```

**Supported output types:**
| Type | Use Case | Method |
|------|----------|--------|
| `generate_until` | Free-form generation (GSM8K, HumanEval) | Generate until stop token |
| `loglikelihood` | Per-token scoring (HellaSwag, WinoGrande) | Compare target likelihoods |
| `loglikelihood_rolling` | Long-document perplexity (Wikitext, PTB) | Sliding window loglikelihood |
| `multiple_choice` | MCQ benchmarks (MMLU, ARC) | Loglikelihood of each choice |

---

## Key Discovery #7: Filter Pipelines for Post-Processing

Filters transform raw model outputs before metrics. Multiple pipelines can run on the same outputs.

**Example: GSM8K self-consistency (Maj@64):**
```yaml
repeats: 64
filter_list:
  - name: "score-first"
    filter:
      - function: "regex"
        regex_pattern: "The answer is (\\-?[0-9\\.\\,]*[0-9]+)"
      - function: "take_first"
  - name: "maj@64"
    filter:
      - function: "regex"
        regex_pattern: "The answer is (\\-?[0-9\\.\\,]*[0-9]+)"
      - function: "majority_vote"
```

Available filter types: `regex`, `take_first`, `majority_vote`, `lambda_filter`, `remove_whitespace`, `stderr` for confidence intervals.

---

## Key Discovery #8: Multi-GPU Parallelism Strategies

Three main approaches:

1. **Data Parallel** (via `accelerate launch`): Each GPU loads a full model copy. K GPUs = K× speed. Works with any model that fits on one GPU.
   ```bash
   accelerate launch -m lm_eval --model hf --tasks hellaswag --batch_size 16
   ```

2. **Model Parallel** (via `parallelize=True`): Model weights split across GPUs using HF `device_map`.
   ```bash
   lm_eval --model hf --model_args pretrained=bigmodel,parallelize=True --batch_size 16
   ```

3. **Tensor Parallel** (native PyTorch, via `tp_plan`): Shards weights across GPUs using DTensor. Requires PyTorch ≥ 2.4, transformers ≥ 4.47.
   ```bash
   torchrun --nproc-per-node=4 -m lm_eval \
     --model hf --model_args pretrained=google/gemma-4-31B-it,tp_plan=auto --batch_size 16
   ```

For **vLLM**: `tensor_parallel_size` and `data_parallel_size` combine both.
For **SGLang**: `dp_size` (data parallel) and `tp_size` (tensor parallel).

---

## Key Discovery #9: HuggingFace Hub Logging

Results can be pushed directly to the Hub:

```bash
lm-eval run --model hf \
  --model_args pretrained=gpt2 \
  --tasks hellaswag \
  --output_path ./results/ \
  --log_samples \
  --hf_hub_log_args "hub_results_org=my-org,results_repo_name=eval-results,push_results_to_hub=True,public_repo=False"
```

Or in config:
```yaml
hf_hub_log_args:
  hub_results_org: my-org
  details_repo_name: eval-details      # detailed samples
  results_repo_name: eval-results      # aggregated results
  push_results_to_hub: true
  push_samples_to_hub: true            # requires --log_samples
  public_repo: false
  gated: true
  point_of_contact: email@example.com
```

---

## Key Discovery #10: Environment Variables

| Variable | Purpose |
|----------|---------|
| `LMEVAL_LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `LM_HARNESS_CACHE_PATH` | Custom cache path for preprocessed prompts |
| `HF_TOKEN` | HF Hub token for private repos |
| `TOKENIZERS_PARALLELISM` | Set `false` to avoid warnings (auto-set by CLI) |

The library also auto-sets `HF_XET_HIGH_PERFORMANCE=1` and `HF_HUB_ENABLE_HF_TRANSFER=1` on import for fast Hub downloads.

---

## Key Discovery #11: 60+ Benchmarks, Hundreds of Subtasks

The harness supports evaluation on 60+ benchmarks with hundreds of subtasks/variants. Popular groups include:

| Group | Tasks | Output Type |
|-------|-------|-------------|
| `mmlu` | 57 subtasks (anatomy, clinical_knowledge, ...) | multiple_choice |
| `arc` | Easy + Challenge | multiple_choice |
| `hellaswag` | Sentence completion | loglikelihood |
| `gsm8k` | Math word problems (+ CoT variant) | generate_until |
| `lambada` | Word prediction | loglikelihood |
| `truthfulqa` | Multiple choice + generation | multiple_choice + mc2 |
| `winogrande` | Pronoun resolution | loglikelihood |
| `bbh` (BIG-Bench Hard) | 27 CoT reasoning tasks | generate_until |
| `human_eval` | Code generation | generate_until |
| `wikitext` | Perplexity | loglikelihood_rolling |

---

## Zero-Cost Relevance

The lm-evaluation-harness is **100% free and open-source** (MIT license). For Beer's use case:
- Evaluate 0.5B and 1.5B GGUF models locally using the `hf` backend with `gguf_file`
- Use `--limit 100` for fast smoke tests during development
- No API costs, no GPU needed for small models on CPU
- Config-driven evaluation for reproducible benchmarking across model versions
- Can push results to Beer's HF Hub org for public leaderboard entries

The only cost is compute — small models (0.5B-1.5B) run on CPU, larger models need local GPU or free tier.

---

## References

- https://github.com/EleutherAI/lm-evaluation-harness
- https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/interface.md
- https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/python-api.md
- https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/config_files.md
- https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/task_guide.md
- https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/API_guide.md
- https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard
