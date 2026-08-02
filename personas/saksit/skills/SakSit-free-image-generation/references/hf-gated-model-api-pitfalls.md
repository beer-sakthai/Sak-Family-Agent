# Hugging Face Gated Model Access — API Pitfalls

## The Problem

`model_info()` returns public metadata for ALL models, even gated ones you haven't been approved for. This gives a false sense of access.

## The Fix

Use `list_repo_files()` to confirm actual download access:

```python
from huggingface_hub import HfApi
api = HfApi()

# WRONG: model_info succeeds for gated repos you don't have access to
info = api.model_info("meta-llama/Llama-3.2-1B")  # Returns data even without approval

# RIGHT: list_repo_files only succeeds if token is approved for download
try:
    files = api.list_repo_files("meta-llama/Llama-3.2-1B")
    print("Access approved")
except Exception as e:
    print("No access or repo not found")
```

## What's Trustworthy

| API Call | Trustworthy? |
|----------|-------------|
| `model_info()` | Not trustworthy for gated access — returns public data |
| `list_repo_files()` | Trustworthy — requires approved access |
| `whoami()` | Trustworthy — confirms token identity |
| HF settings page (gated-repos) | Source of truth |
