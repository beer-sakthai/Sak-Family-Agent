# Empty `gguf: {}` Dict in Skeleton Repos

## Observation (2026-07-30)

The HF API `/api/models/{id}` endpoint may include a top-level `gguf` key
whose value is an empty dict `{}` — not just for GGUF-quantized models, but
also for **skeleton repos** (zero `usedStorage`, no weights).

This breaks detection patterns that use `'gguf' in api_data` to distinguish
GGUF-only repos from skeletons.

## Example

Model `Nanthasit/sakthai-plus-1.5b-coder` (skeleton, created 2026-07-30):
- `api_data['gguf']` → `{}` (empty dict)
- `'gguf' in api_data` → `True` (key exists)
- `bool(api_data['gguf'])` → `False` (empty dict is falsy)
- `usedStorage: 0`, no `.gguf` sibling files
- Config.json returns HTTP 404

## Correct Detection

```python
# DO NOT use 'gguf' in api_data  — True even for empty {}
has_gguf_content = bool(api_data.get('gguf', {}))  # False for empty {}

# For skeleton detection, check sibling filenames:
has_gguf_file = any('.gguf' in s.get('rfilename', '') for s in api_data.get('siblings', []))

# For GGUF-only detection, use non-empty content:
is_gguf_only = has_gguf_content and not has_safetensors_key
```

## Root Cause

The HF API returns the `gguf` key on every model response — it's always present
as a dict. For repos with no GGUF files, the dict is empty `{}`. The key's
presence alone is not informative; its content is.

## Affected Code Patterns

Every pattern in `sakthai-model-health-check` that used `'gguf' in api_data`:

- **Skeleton detection**: was `not has_gguf_key` → should be `not has_gguf_file`
- **GGUF-only detection**: was `has_gguf_key and not has_safetensors_key` →
  should be `has_gguf_content and not has_safetensors_key`
- **LoRA adapter detection**: unaffected (LoRA repos lack BOTH safetensors AND
  gguf top-level keys entirely, so `'gguf' in api_data` is False)
