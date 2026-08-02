# Dataset Enrichment Pipeline (validated 2026-07-25)

Reusable workflow for adding examples to Hugging Face datasets without cache corruption.

## Steps

1. **Download current dataset** using `urllib.request.urlopen()` on the raw HF URL — NOT `hf_hub_download()`, which caches aggressively and may return a stale version.

```python
import json, urllib.request
url = "https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6/raw/main/data/train.jsonl"
current = [json.loads(line) for line in urllib.request.urlopen(url) if line.strip()]
```

2. **Count baseline** before generating — `print(f"Current: {len(current)}")`

3. **Generate new examples** matching the existing format. The format is OpenAI `tool_calls` JSON:

```
messages: [
  {"role": "system", "content": "..."},
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": null, "tool_calls": [{"id": "call_...", "type": "function", "function": {"name": "...", "arguments": "..."}}]}
]
tools: [{"type": "function", "function": {...}}]
```

4. **Concatenate**: `total = current + new`
5. **Write to /tmp/**: avoids permission issues with profile directories
6. **Upload via API** with descriptive commit message:

```python
from huggingface_hub import HfApi
api = HfApi()
api.upload_file(
    repo_id="Nanthasit/sakthai-combined-v6",
    path_in_repo="data/train.jsonl",
    path_or_fileobj="/tmp/file.jsonl",
    repo_type="dataset",
    commit_message="v7: add X examples"
)
```

7. **Verify** by downloading the raw URL again and counting lines.

## Pitfalls

- `hf_hub_download()` caches aggressively. After a subagent corrupts the dataset, the cached version may be the corrupted one. Always use `urllib.request.urlopen()` for the raw URL to bypass cache.
- Subagents can overwrite instead of append. Always verify original count before dispatch and compare remote count after.
- Keep the previous good commit hash (`bbdde20621cc` for v6 1,328 baseline) to revert if needed.
