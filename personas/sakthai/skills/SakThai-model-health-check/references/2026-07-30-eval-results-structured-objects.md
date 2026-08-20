# EvalResult Structured Objects via `card_data.eval_results`

## Discovery

During the 2026-07-30 evening cron health check on `Nanthasit/sakthai-coder-1.5b`, accessing `model_info.card_data.model_index` raised:

```
AttributeError: 'ModelCardData' object has no attribute 'model_index'. Did you mean: 'model_name'?
```

The `model_index` from the raw JSON API is NOT exposed as a direct attribute on `ModelCardData`. However, `model_info.card_data.eval_results` IS — returning a list of typed `EvalResult` dataclass objects.

## Usage

```python
from huggingface_hub import HfApi

api = HfApi()
model_info = api.model_info("Nanthasit/sakthai-coder-1.5b")

# Structured access — NOT model_info.card_data.model_index
eval_results = model_info.card_data.eval_results  # list[EvalResult] or None

for er in (eval_results or []):
    print(f"{er.dataset_name} / {er.metric_name} = {er.metric_value} (verified={er.verified})")
```

## EvalResult Fields

| Field | Type | Example |
|---|---|---|
| `task_type` | `str\|None` | `"text-generation"` |
| `dataset_type` | `str\|None` | `"openai_humaneval"` |
| `dataset_name` | `str\|None` | `"HumanEval"` |
| `metric_type` | `str\|None` | `"pass@1"` |
| `metric_name` | `str\|None` | `"pass@1 (base model reference)"` |
| `metric_value` | `float\|None` | `74.4` |
| `verified` | `bool` | `False` |
| `task_name` | `str\|None` | `None` |
| `dataset_config` | `str\|None` | `None` |
| `dataset_split` | `str\|None` | `None` |
| `dataset_revision` | `str\|None` | `None` |
| `dataset_args` | `str\|None` | `None` |
| `metric_config` | `str\|None` | `None` |
| `metric_args` | `str\|None` | `None` |
| `source_name` | `str\|None` | `None` |
| `source_url` | `str\|None` | `None` |

## When to Use Each Approach

| Approach | Pros | Cons |
|---|---|---|
| `card_data.eval_results` | Typed access, no JSON parsing, full field set | Only available via huggingface_hub library; `eval_results` may be `None` if no model-index in card; doesn't expose raw `model-index` task/dataset metadata (e.g. `task.type`, `dataset.type` at the result level are mapped into `er.task_type`/`er.dataset_type` but less transparent than raw JSON) |
| Raw `data["model-index"]` from JSON API | Complete raw structure, works with curl, no library dependency | Manual navigation, string-key access, no type safety |

## Verification Pattern

```python
er = model_info.card_data.eval_results
if er:
    # Prefer structured access for value comparison
    for entry in er:
        assert entry.metric_value > 0
        assert isinstance(entry.verified, bool)
else:
    # Fall back to raw model-index from JSON
    pass
```
