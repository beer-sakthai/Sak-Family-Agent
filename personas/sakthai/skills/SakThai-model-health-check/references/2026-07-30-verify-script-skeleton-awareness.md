# Verify Script Skeleton-Awareness Patch

**Date:** 2026-07-30
**Model:** `Nanthasit/sakthai-plus-1.5b-coder` (skeleton)
**File patched:** `scripts/verify-health-check.py`

## Problem

The `verify-health-check.py` script exits 1 on skeleton repos (repos with no model weights, e.g. only README.md + .gitattributes). The `4/5 values` step flags `MODEL_FILE_SIZE_ZERO` because `total_weight_bytes` is legitimately 0 — there are no weights to upload yet.

## Root Cause

The size-zero check had no skeleton-awareness:
```python
# Before patch — flags every size=0 repo as error:
if size <= 0 and SCHEMA and SCHEMA != 'generic':
    errors.append("MODEL_FILE_SIZE_ZERO")
```

## Fix

Before flagging `MODEL_FILE_SIZE_ZERO`, check whether the repo is a skeleton:

```python
is_skeleton = False
if SCHEMA == 'new':
    cm = d.get('core_metrics', {})
    if cm.get('has_weights') is False or 'skeleton' in str(cm.get('model_type', '')).lower():
        is_skeleton = True
elif SCHEMA == 'old':
    tm = d.get('target_model', {})
    if tm.get('model_type') == 'skeleton' or tm.get('weight_status') == 'MISSING':
        is_skeleton = True
if size <= 0 and SCHEMA and SCHEMA != 'generic' and not is_skeleton:
    errors.append("MODEL_FILE_SIZE_ZERO")
```

## Gotcha: `SCHEMA` vs `schema` (variable casing)

The verify script uses `SCHEMA` (uppercase) as a module-level variable set during schema detection in step 2.

**DO NOT use lowercase `schema` in conditionals.** The first attempt used:
```python
    if schema == 'new':   # NameError! Variable is SCHEMA, not schema
```
This crashes with `NameError: name 'schema' is not defined`.

**Fix:** Always use `SCHEMA` (the actual variable name) when referencing the detected schema in conditionals.

```python
    if SCHEMA == 'new':   # ✓ correct
```

## Regression Test Pattern

When patching the verify script, test BOTH paths to ensure skeleton-awareness doesn't break the non-skeleton check:

**Test A — Skeleton YAML (should pass):**
```bash
uv run python3 scripts/verify-health-check.py \
  .eval_results/health-check-sakthai-plus-1.5b-coder-2026-07-30.yaml \
  Nanthasit/sakthai-plus-1.5b-coder
# Expected: exit 0, no MODEL_FILE_SIZE_ZERO
```

**Test B — Non-skeleton YAML with size=0 (should fail with MODEL_FILE_SIZE_ZERO):**
Create a mock YAML with `has_weights: true` and `total_weight_bytes: 0`, then verify it still flags:
```bash
uv run python3 scripts/verify-health-check.py \
  /tmp/mock-non-skeleton.yaml \
  nanthasit/regression-test
# Expected: exit 1, contains "MODEL_FILE_SIZE_ZERO"
```

Both must pass to confirm the patch is correct.

## Schema Coverage

| Schema | Detection Field | Skeleton Condition |
|--------|----------------|-------------------|
| `new` | `core_metrics.has_weights` | `is False` |
| `new` | `core_metrics.model_type` | contains `"skeleton"` (case-insensitive) |
| `old` | `target_model.model_type` | `== "skeleton"` |
| `old` | `target_model.weight_status` | `== "MISSING"` |

The LLM cron schema (`llm_cron`) and LoRA adapter schema (`slim`) are not skeleton-checked because those YAML generators don't produce skeleton repos as output.
