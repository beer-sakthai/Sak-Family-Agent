# Model-Index Verification via HF API

Documented 2026-07-29 — why grep-based verification isn't enough for model-index updates.

## The Gap

Grep-based verification (checking raw README.md for a string) confirms the TEXT was uploaded but does **not** confirm the YAML was parsed correctly by Hugging Face's backend. A YAML indentation error, a wrong field name, or an invalid metric type can silently fail to render in the model page's Evaluations section while the raw file still contains the expected text.

## API-Based Verification

Use `api.model_info().card_data.eval_results` to check that the model-index was parsed into structured objects:

```python
from huggingface_hub import HfApi

api = HfApi()
info = api.model_info('your-username/your-model')
cd = info.card_data

# eval_results is a list of EvalResult dataclasses
er = cd.eval_results
print(f"Results count: {len(er)}")

for r in er:
    print(f"  {r.task_name} / {r.dataset_name}: {r.metric_name} = {r.metric_value} (verified: {r.verified})")
```

## EvalResult Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_name` | str | Human-readable task name (from YAML `task.name`) |
| `task_type` | str | Task type identifier (from YAML `task.type`) |
| `dataset_name` | str | Human-readable dataset name (from YAML `dataset.name`) |
| `dataset_type` | str | Dataset type identifier (from YAML `dataset.type`) |
| `metric_name` | str | Metric display name (from YAML `metrics[].name`) |
| `metric_type` | str | Metric type identifier (from YAML `metrics[].type`) |
| `metric_value` | float | The score value (from YAML `metrics[].value`) |
| `verified` | bool | Whether the result is verified (`True`) or expected/upstream (`False`) |
| `source_name` | str or None | Source identifier for community eval results |

## Key Checks

| Check | What It Catches |
|-------|----------------|
| `len(er) == expected_count` | Wrong nesting, duplicate keys, or missing entries |
| `all(r.verified == False)` for upstream values | Honesty enforcement — don't claim verified without multi-trial |
| `all(r.metric_value > 0)` | Parsing errors that produce NaN or 0 |
| `all(r.task_type is not None)` | Invalid/missing task.type values |
| `all(r.dataset_type is not None)` | Invalid/missing dataset.type values |

## When to Use (vs grep)

Use **API verification** when:
- You updated `model-index` YAML (not card body text)
- You want to confirm HF's backend parsed the YAML correctly
- You're checking multiple results programmatically

Use **grep verification** (HTTP raw README) when:
- You updated card body markdown (text, tables, links)
- The change doesn't affect YAML metadata
- You need a quick existence check

## Pitfall: `card.get('model-index', [])` Fails

`ModelCardData` is a **dataclass**, not a dict. The model-index maps to the `eval_results` attribute, not a key called `model-index`:

```python
# ❌ Wrong — card is not a dict
results = card.get('model-index', [])

# ✅ Correct
results = card.eval_results
```

Access the full card data via `card.to_dict()` if you need raw dict representation.
