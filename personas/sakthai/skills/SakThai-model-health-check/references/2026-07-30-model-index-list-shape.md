# model-index Can Be a List, Not Just a Dict with `results`

Observed 2026-07-30 on `Nanthasit/sakthai-plus-1.5b`.

## Symptoms

```python
mi_raw = api.get('model-index') or card_data.get('model-index') or []
results = mi_raw.get("results", [])
# AttributeError: 'list' object has no attribute 'get'
```

## Root Cause

The cascade `or []` produces a plain Python list `[]` when both `api.get('model-index')` and `card_data.get('model-index')` are absent/null. Lists don't have `.get()`. Also possible: some repos store `model-index` as a flat JSON array (no `results` wrapper).

## Fix

Always guard with `isinstance()` before accessing `.get("results")`:

```python
mi_raw = api.get('model-index') or card_data.get('model-index') or []
if isinstance(mi_raw, list):
    entries = mi_raw
else:
    entries = mi_raw.get("results", [])
for result in entries:
    task = result.get("task", {})
    ...
```

This handles three shapes in one expression:
- **Dict with `results` key** (standard HF format)
- **Flat list** (some repos, or a fallback `[]`)
- **`None`** (collapsed by `or []` to list, caught by the guard)
