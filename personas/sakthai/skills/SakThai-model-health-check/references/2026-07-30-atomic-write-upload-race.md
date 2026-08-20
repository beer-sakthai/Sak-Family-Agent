# Atomic Write+Upload Pattern — Sibling Race Solution

**Date:** 2026-07-30
**Context:** Health check for `Nanthasit/sakthai-plus-1.5b-coder`
**Problem:** Sibling subagents (from parallel cron jobs) overwrote `.eval_results/health-check.yaml` 3 times in 20 minutes.

## The Fix

Generate YAML from a Python dict via `yaml.dump()`, then upload immediately in the same Python subprocess. No gap between write and upload means no race window.

```python
import yaml, os
from huggingface_hub import HfApi

content = {
    "target_model": {"id": "Nanthasit/sakthai-plus-1.5b-coder", "scanned_at": "2026-07-30T22:15:00Z"},
    "health": {"status": "critical", "score": 10, "max_score": 100,
        "dimensions": {"availability": 0, "metadata_card": 75, "popularity": 0}},
    # ... full dict ...
}

with open("/opt/data/.eval_results/health-check.yaml", "w") as f:
    yaml.dump(content, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

HfApi().upload_file(
    token=os.environ["HF_TOKEN"],
    path_or_fileobj="/opt/data/.eval_results/health-check.yaml",
    path_in_repo=".eval_results/health-check.yaml",
    repo_id="Nanthasit/sakthai-plus-1.5b-coder",
    repo_type="model",
)
```

Run with: `uv run python3 script.py`

## Detection

If `write_file` returns `_warning: "was modified by sibling subagent '<id>'"`, a sibling agent overwrote your file between your write and your upload. Recovery:

```python
from huggingface_hub import HfApi
api = HfApi(token=os.environ["HF_TOKEN"])
path = api.hf_hub_download(repo_id, ".eval_results/health-check.yaml")
# Read it, or re-write using the atomic pattern above
```

## Side Benefits

- `yaml.dump()` avoids all manual YAML quoting errors (arrows `-> →`, booleans, parentheses)
- Single process, two operations — no intermediate shell state to lose
- Verifiable: local file + remote file content match is guaranteed by same process
