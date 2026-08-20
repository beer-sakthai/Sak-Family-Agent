# HF Model Card Update Workflow — Jul 23, 2026

Hard-won from a real session where git push to HF broke entirely.

## Problem

HF deprecated password-based git authentication. This command no longer works:

```
git clone https://user:TOKEN@huggingface.co/Nanthasit/my-model
# → "Password authentication in git is no longer supported"
```

This affects all `git clone` + `git push` operations against HF repos.

## Solution: huggingface_hub Python API

The `huggingface_hub` library's `HfApi.upload_file()` works reliably.

### One-time setup

```bash
uv venv /tmp/hf-venv
uv pip install --python /tmp/hf-venv/bin/python huggingface-hub
```

### Updating a single model card

```python
import os
from huggingface_hub import HfApi

HF_TOKEN = os.environ.get('HF_TOKEN', '')
# Or read from .env file

api = HfApi()
api.upload_file(
    path_or_fileobj=content.encode(),  # str → bytes
    path_in_repo='README.md',
    repo_id='Nanthasit/sakthai-context-0.5b-merged',
    commit_message='SakSit: update model card'
)
```

For datasets, add `repo_type='dataset'`.

### Updating multiple cards

```python
models = ['sakthai-context-0.5b-merged', 'sakthai-context-1.5b-merged',
          'sakthai-context-7b-merged', 'sakthai-context-7b-128k']
datasets = ['sakthai-combined-v4', 'sakthai-combined-v5']

# Models
for m in models:
    content = build_model_card(m)  # generate card content
    api.upload_file(
        path_or_fileobj=content.encode(),
        path_in_repo='README.md',
        repo_id=f'Nanthasit/{m}',
        commit_message='SakSit: update model card'
    )

# Datasets
for d in datasets:
    content = build_dataset_card(d)
    api.upload_file(
        path_or_fileobj=content.encode(),
        path_in_repo='README.md',
        repo_id=f'Nanthasit/{d}',
        repo_type='dataset',
        commit_message='SakSit: update dataset card'
    )
```

### Checking HF access

```python
api = HfApi()
user = api.whoami()
print(user['auth']['accessToken']['role'])  # should be 'write'
```

## YAML Frontmatter Template (Models)

```yaml
---
license: apache-2.0
language:
- en
library_name: transformers
pipeline_tag: text-generation
tags:
- qwen2.5
- sakthai
- house-of-sak
- tool-calling
- instruct
- agent
datasets:
- Nanthasit/sakthai-combined-v5
base_model: Qwen/Qwen2.5-7B-Instruct
---
```

Key tags for discoverability: `house-of-sak`, `agent`, `function-calling`.

## What NOT to Do

- Don't try `git clone https://TOKEN@huggingface.co/...` (fails with credential prompt)
- Don't embed the HF_TOKEN in the script file (it gets written to disk)
- Don't use `model_info()` to check gated access — it returns public data for all models, even ones you're not approved for. Use the settings page at `huggingface.co/settings/gated-repos` for the real list.
