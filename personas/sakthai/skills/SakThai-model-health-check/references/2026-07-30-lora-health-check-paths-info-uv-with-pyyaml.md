# 2026-07-30: LoRA Health Eval — get_paths_info + uv --with pyyaml

Session: cron health eval on `Nanthasit/sakthai-plus-1.5b-lora` (6th run).

## New patterns established

### 1. `api.get_paths_info()` for LoRA adapter file sizes

Previous sessions used `/tree/main` endpoint or HEAD redirects for LoRA adapter
file sizes. This session discovered that `api.get_paths_info()` works directly
for LoRA adapters, returning `RepoFile` objects with `size` populated:

```python
from huggingface_hub import HfApi
api = HfApi()
files = api.list_repo_files(repo_id)
meta = api.get_paths_info(repo_id, paths=files)
for m in meta:
    sz = getattr(m, 'size', 0) or 0
    print(f'{m.path}: {sz:,} bytes')
```

Results for `sakthai-plus-1.5b-lora` (11 files):
- `adapter_model.safetensors`: 73,911,112 bytes
- `tokenizer.json`: 11,421,892 bytes
- `adapter_config.json`: 1,158 bytes
- All 11 files accounted for with real sizes.

This is cleaner than the `/tree/main` raw JSON approach — no JSON parsing,
type-safe `RepoFile` objects, single API call for all file sizes.

**Limitation**: still returns shape (C) (only `rfilename`) for some Xet-backed
repos. Works reliably for LoRA/PEFT repos verified on 2026-07-30.

### 2. `uv run --with pyyaml python3` for YAML verification

When `pyyaml` isn't installed in the base environment, use uv's on-the-fly
package installation:

```bash
uv run --with pyyaml python3 -c "
import yaml
with open('health-check.yaml') as f:
    d = yaml.safe_load(f)
print('model:', d.get('model', {}).get('id', '?'))
"
```

This installs pyyaml to a temporary uv-managed venv without polluting any
project dependencies. Works in cron mode.

### 3. Canonical verification pattern for this session

```bash
# Step 1: Write health-check YAML (via write_file to .eval_results/)
# Step 2: Upload via huggingface_hub
uv run python3 -c "
from huggingface_hub import HfApi
api = HfApi()
api.upload_file(
    path_or_fileobj='.eval_results/health-check-slug-DATE.yaml',
    path_in_repo='.eval_results/health-check-slug-DATE.yaml',
    repo_id='REPO_ID',
    repo_type='model',
)"
# Step 3: Verify by downloading and checking content identity
uv run python3 -c "
from huggingface_hub import HfApi
api = HfApi()
local = api.hf_hub_download(
    repo_id='REPO_ID',
    filename='.eval_results/health-check-slug-DATE.yaml',
    repo_type='model',
)
with open(local) as f:
    assert 'MODEL_ID' in f.read()
    print('Verified: model identity confirmed')
"
# Step 4: Validate YAML structure with uv --with pyyaml
uv run --with pyyaml python3 -c "
import yaml
with open('.eval_results/health-check-slug-DATE.yaml') as f:
    d = yaml.safe_load(f)
checks = [
    d.get('model', {}).get('id') == 'EXPECTED_ID',
    len(d.get('file_sizes', {}).get('files', [])) == 11,
    d.get('health_assessment', {}).get('status') == 'healthy',
]
print('PASS' if all(checks) else 'FAIL')
"
```

## Key metrics recorded

| Metric | Value |
|--------|-------|
| adapter_model.safetensors | 73,911,152 bytes |
| tokenizer.json | 11,421,892 bytes |
| Total active files | 87.3 MB (11 files) |
| usedStorage | 715.7 MB (Xet overhead) |
| Downloads | 0 (brand new) |
| Base model | Qwen/Qwen2.5-1.5B-Instruct |
| cardMetadata | Not present |
