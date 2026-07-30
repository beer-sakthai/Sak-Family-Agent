# Training Data Visibility for Kaggle

## The Problem

Kaggle notebooks run in an isolated environment with limited internet access. When training on a Hugging Face dataset:

1. **Public datasets** → work without any auth, `hf_hub_download()` succeeds with `token=None`
2. **Private datasets** → require `HF_TOKEN` to download

Kaggle Secrets (`UserSecretsClient().get_secret()`) is the intended auth mechanism but:
- Doesn't work if the user hasn't set up the secret in Kaggle web UI
- Cannot be configured programmatically via CLI
- Returns `ConnectionError: HTTP Error 400: Bad Request` when the secret doesn't exist

## The Fix

**Make the dataset public** unless it contains sensitive data:

```python
from huggingface_hub import HfApi
api = HfApi(token="hf_...")
api.update_repo_settings(repo_id="owner/dataset-name", private=False, repo_type="dataset")
```

Then the notebook downloads data without any token.

## 3-tier Auth Fallback

Include this in the notebook's auth cell so it works regardless of how the token is provided:

```python
import os
HF_TOKEN = None
try:
    from kaggle_secrets import UserSecretsClient
    HF_TOKEN = UserSecretsClient().get_secret("HF_TOKEN")
    print("Got token from Kaggle Secrets")
except Exception:
    HF_TOKEN = os.environ.get("HF_TOKEN")
    if not HF_TOKEN:
        tp = os.path.expanduser("~/.cache/huggingface/token")
        if os.path.exists(tp):
            with open(tp) as f:
                HF_TOKEN = f.read().strip()
            print("Got token from HF cache")
if not HF_TOKEN:
    print("No HF_TOKEN — training will run but push will be skipped")
```

## Verification

Check dataset visibility before pushing a notebook:

```bash
curl -s https://huggingface.co/api/datasets/OWNER/NAME | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(f'private: {d.get(\"private\")}')"
```

If `private: True` and the Kaggle kernel needs to read it, either make it public or ensure HF_TOKEN is available.

## Session History

- 2026-07-29: `Nanthasit/sakthai-combined-v7` was private, causing Kaggle training kernel v2 to fail with `RuntimeError: HF_TOKEN required`. Fixed by making dataset public via `api.update_repo_settings()`.
- 2026-07-29: After making dataset public, v3 failed with `KeyError: 'messages'` — 200 legacy v5 rows used `conversations` key instead of `messages`. Fixed by normalizing dataset (rename `conversations`→`messages`) and adding `safe_render()` in notebook that handles both keys.
