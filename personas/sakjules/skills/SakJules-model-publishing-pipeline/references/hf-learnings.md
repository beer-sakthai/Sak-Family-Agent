# HF Learnings — Model Publishing Pipeline

> Learned: 2026-07-24 | Authoritative source: huggingface_hub (v1.24+), HF Hub source
> Covers: HF Hub repo creation, configuration, metadata setup, and publishing automation

## Summary

Complete reference for programmatically creating and configuring Hugging Face Hub repositories for model publishing — from `HfApi.create_repo()` through metadata setup, card management, and CI-ready automation patterns.

---

## 1. Repo Creation — `HfApi.create_repo()`

### Signature

```python
def create_repo(
    repo_id: str,
    *,
    repo_type: str = "model",          # "model" | "dataset" | "space"
    private: bool = False,
    exist_ok: bool = False,
    license: str | None = None,        # "mit", "apache-2.0", "openrail", etc.
    repo_visibility: str | None = None, # "public" | "private" (overrides private=)
    token: str | None = None,
    ...
) -> RepoUrl
```

### Key parameters

| Parameter | Type | Default | Behavior |
|-----------|------|---------|----------|
| `repo_id` | str | required | `namespace/repo-name` or just `repo-name` (creates under user namespace) |
| `repo_type` | str | `"model"` | `"model"`, `"dataset"`, `"space"` |
| `private` | bool | `False` | `True` = private repo (uses free tier quota) |
| `exist_ok` | bool | `False` | `True` = silently succeed if repo exists (returns existing URL) |
| `license` | str | `None` | HF license identifier (sets in YAML card metadata) |
| `token` | str | `None` | Falls back to `HF_TOKEN` env var, then stored token |

### Return value

```python
url: RepoUrl = api.create_repo("beer-sakthai/my-model")
print(url)               # RepoUrl object
str(url)                 # "https://huggingface.co/beer-sakthai/my-model"
url.endpoint             # "https://huggingface.co"
url.repo_id              # "beer-sakthai/my-model"
url.repo_type            # "model"
url.url                  # full HTTPS URL
```

### Error handling

```python
# Repo already exists (exist_ok=False by default)
try:
    api.create_repo("beer-sakthai/my-model")
except OSError as e:  # or HTTPError
    print(f"Repo exists: {e}")

# Safe creation
api.create_repo("beer-sakthai/my-model", exist_ok=True)
url = api.create_repo("beer-sakthai/my-model", exist_ok=True)
# always succeeds; check url.url if needed
```

### Create with initial card

```python
api.create_repo(
    "nanthasit/my-model",
    repo_type="model",
    license="apache-2.0",
    exist_ok=True,
)
# Repo is created with default README.md (auto-generated)
```

---

## 2. Repo Configuration — Post-Creation

### Update metadata — `update_repo_settings()`

```python
api.update_repo_settings(
    repo_id="nanthasit/my-model",
    repo_type="model",
    gated=False,                      # disable gated access
    # deprecated: use create_repo(license=...) instead
)
```

### Update repo visibility

```python
# Public → Private
api.update_repo_visibility(
    repo_id="nanthasit/my-model",
    private=True,
    repo_type="model",
)

# Private → Public
api.update_repo_visibility(
    repo_id="nanthasit/my-model",
    private=False,
    repo_type="model",
)
```

### Set pipeline tag (appears in HF Model Cards search)

```python
api.update_repo_settings(
    repo_id="nanthasit/my-model",
    pipeline_tag="text-generation",  # sets the pipeline badge
    # Common values: "text-generation", "text-classification",
    # "image-classification", "image-to-text", "automatic-speech-recognition", etc.
)
```

### Set library_name

The `library_name` tag is set at repo creation or via card YAML. It's not directly settable through `update_repo_settings()` — use the model card's YAML `library_name` field instead.

---

## 3. Model Card (README.md) Management

### Set card content right after creation

```python
from huggingface_hub import ModelCard, ModelCardData

card_data = ModelCardData(
    language="en",
    license="apache-2.0",
    library_name="transformers",
    pipeline_tag="text-generation",
    tags=["sakthai", "tool-calling", "qwen"],
)
card = ModelCard.from_template(card_data)
card.push_to_hub("nanthasit/my-model", repo_type="model")
```

### Card YAML front matter fields for models

```yaml
---
language: en
license: apache-2.0
library_name: transformers
pipeline_tag: text-generation
tags:
- sakthai
- tool-calling
- qwen2.5
- instruct
- gguf
model-index:
- name: my-model
  results: []
---
```

### programmatic card from template

```python
from huggingface_hub import ModelCard, ModelCardData

card_data = ModelCardData(
    language="en",
    license="apache-2.0",
    library_name="transformers",
    pipeline_tag="text-generation",
    tags=["my-tag"],
)
card = ModelCard.from_template(
    card_data,
    pretty_name="My Model",
    summary="A short description",
)

# Replace card content
card.text = "\n## Model Description\n\nLonger description here.\n"

# Push
card.push_to_hub("nanthasit/my-model", commit_message="Add model card")
```

---

## 4. File Upload — Publishing Artifacts

### Single file

```python
api.upload_file(
    path_or_fileobj="model.safetensors",   # local file path or BytesIO
    path_in_repo="model.safetensors",       # path in the repo
    repo_id="nanthasit/my-model",
    repo_type="model",
    commit_message="Upload model weights",
)
```

### Entire folder

```python
api.upload_folder(
    folder_path="./output/merged/",
    path_in_repo=".",                      # root of repo, or a subfolder
    repo_id="nanthasit/my-model",
    repo_type="model",
    commit_message="Upload merged model",
    allow_patterns=["*.safetensors", "*.json", "*.txt"],
    ignore_patterns=["*.bin", "cache/", "**/.gitkeep"],
)
```

### Multi-file atomic commit

```python
from huggingface_hub import CommitOperationAdd, CommitOperationDelete

operations = [
    CommitOperationAdd(
        path_in_repo="model-0001-of-0002.safetensors",
        path_or_fileobj="./output/model-0001-of-0002.safetensors",
    ),
    CommitOperationAdd(
        path_in_repo="model-0002-of-0002.safetensors",
        path_or_fileobj="./output/model-0002-of-0002.safetensors",
    ),
    CommitOperationAdd(
        path_in_repo="config.json",
        path_or_fileobj="./output/config.json",
    ),
]

api.create_commit(
    repo_id="nanthasit/my-model",
    operations=operations,
    commit_message="Upload sharded model v1.0",
    repo_type="model",
)
```

### Large file best practices

| File type | Method | Notes |
|-----------|--------|-------|
| Small (<5MB) | `upload_file()` | Single-shot, simplest |
| Medium (5MB-50MB) | `upload_file()` | Acceptable with progress bar |
| Large (>50MB) | `upload_folder()` | LFS auto-detected, chunked uploads |
| Sharded model | `upload_folder()` | With `allow_patterns` for control |
| GGUF (>2GB) | `upload_folder()` or `hf upload` | Use `hf upload-large-folder` for >5GB |
| Checkpoints | `create_commit()` | Atomic multi-file, avoid partial states |

---

## 5. Repo Deletion and Cleanup

### Delete repo permanently

```python
# ⚠️ IRREVERSIBLE
api.delete_repo(
    repo_id="nanthasit/experiment-failed",
    repo_type="model",
)
```

### Delete specific files

```python
api.delete_file(
    path_in_repo="checkpoint-1000/optimizer.pt",
    repo_id="nanthasit/my-model",
    repo_type="model",
    commit_message="Remove unused checkpoint",
)

api.delete_folder(
    path_in_repo="checkpoints/",
    repo_id="nanthasit/my-model",
    repo_type="model",
    commit_message="Clean up training checkpoints",
)
```

---

## 6. Move and Transfer

### Transfer ownership

```python
api.move_repo(
    from_id="nanthasit/old-name",
    to_id="nanthasit/new-name",
    repo_type="model",
)
```

### Move across namespaces (requires write access to both)

```python
api.move_repo(
    from_id="old-org/old-name",
    to_id="nanthasit/my-model",
    repo_type="model",
)
```

---

## 7. Branch and Tag Management

```python
# List refs
refs = api.list_repo_refs("nanthasit/my-model", repo_type="model")
# refs.convert: list of GitRefInfo for branches
# refs.convert: list of GitRefInfo for tags

# Create branch
api.create_branch(
    repo_id="nanthasit/my-model",
    branch="experiment-bnb-4bit",
    repo_type="model",
)

# Create tag
api.create_tag(
    repo_id="nanthasit/my-model",
    tag="v1.0.0",
    repo_type="model",
)

# Delete branch
api.delete_branch(
    repo_id="nanthasit/my-model",
    branch="experiment-bnb-4bit",
    repo_type="model",
)

# Delete tag
api.delete_tag(
    repo_id="nanthasit/my-model",
    tag="v1.0.0",
    repo_type="model",
)
```

### Semantic versioning for model tags

Recommended convention for model publishing:

| Tag | Meaning |
|-----|---------|
| `v1.0.0` | First official release |
| `v1.1.0` | New features (e.g., new quantization format) |
| `v1.1.1` | Bug fixes, card updates (no weight changes) |
| `rc1` | Release candidate before final tag |
| `experiment-<name>` | Temporary branches for experiments |

---

## 8. CI/CD and Automation Patterns

### Safe upsert pattern

```python
def ensure_repo(repo_id: str, repo_type: str = "model",
                private: bool = False, license: str | None = None) -> str:
    """Create repo if it doesn't exist, return its URL."""
    api = HfApi()
    url = api.create_repo(
        repo_id,
        repo_type=repo_type,
        private=private,
        license=license,
        exist_ok=True,
    )
    return str(url)
```

### Automated publishing pipeline

```python
from huggingface_hub import HfApi, CommitOperationAdd
from pathlib import Path

def publish_model(
    local_dir: Path,
    repo_id: str,
    commit_message: str = "Update model",
) -> str:
    """Upload all safetensors + config + card from local_dir to Hub."""
    api = HfApi()
    api.create_repo(repo_id, exist_ok=True)

    ops = []
    for f in local_dir.rglob("*"):
        if f.is_file() and f.suffix in (".safetensors", ".json", ".py", ".md"):
            rel_path = f.relative_to(local_dir)
            ops.append(CommitOperationAdd(
                path_or_fileobj=str(f),
                path_in_repo=str(rel_path),
            ))

    if ops:
        api.create_commit(
            repo_id=repo_id,
            operations=ops,
            commit_message=commit_message,
        )
    return f"https://huggingface.co/{repo_id}"
```

### Verification after publishing

```python
def verify_published(repo_id: str) -> dict:
    """Check that repo exists and list key files."""
    api = HfApi()
    info = api.repo_info(repo_id)
    files = api.list_repo_files(repo_id)
    return {
        "repo_id": repo_id,
        "private": info.private,
        "pipeline_tag": getattr(info, "pipeline_tag", None),
        "file_count": len(files),
        "has_safetensors": any(f.endswith(".safetensors") for f in files),
        "has_config": "config.json" in files,
        "has_card": "README.md" in files,
    }
```

### Cron-ready publishing check

```python
# Check if a build artifact needs publishing
import os
from huggingface_hub import HfApi, HfFolder, repo_exists

api = HfApi(token=os.environ.get("HF_TOKEN"))

if not repo_exists(repo_id="nanthasit/my-model"):
    api.create_repo("nanthasit/my-model", private=False)
    print("Created repo")
elif not any(f.endswith(".safetensors")
             for f in api.list_repo_files("nanthasit/my-model")):
    # Repo exists but empty — needs initial upload
    print("Repo exists but empty — upload needed")
else:
    print("Model already published")
```

---

## 9. Common Pitfalls

### Pitfall 1: `create_repo` without `exist_ok=True` in scripts
Always use `exist_ok=True` in automation scripts. Without it, a second run crashes with `HTTPError: 409 Client Error`.

### Pitfall 2: Uploading to wrong `path_in_repo`
`path_in_repo="."` uploads to root. `path_in_repo="./subdir"` creates a subfolder. For sharded models, keep them at root with `path_in_repo="."`.

### Pitfall 3: LFS file limits
Free HF accounts have limited LFS storage (5GB for models). Uploading large GGUF files (>5GB) may hit storage limits. Use `hf upload-large-folder` or the bucket API for >5GB files.

### Pitfall 4: No card = poor discoverability
Models without cards (README.md with YAML front matter) don't appear in HF Hub search properly. Always push a card with pipeline_tag, license, and tags.

### Pitfall 5: Model card YAML format strictness
The `license` and `tags` fields in YAML must use the exact identifiers HF recognizes. Invalid values cause the card to render without metadata in the web UI.

### Pitfall 6: `create_commit` with no operations fails
`api.create_commit()` with an empty `operations` list raises an error. Always check `if ops:` before calling.

### Pitfall 7: Moving repos breaks existing URLs
`move_repo()` changes the repo_id. All existing URLs, git remotes, and cached references break. Use sparingly and update all references.

---

## 10. CLI Equivalent (`hf repos`)

```bash
# Create repo
hf repos create nanthasit/my-model --type model --license apache-2.0

# Create private dataset
hf repos create nanthasit/private-data --type dataset --private

# Delete repo (interactive confirmation)
hf repos delete nanthasit/old-experiment

# Move repo
hf repos move nanthasit/old-name nanthasit/new-name

# List branches
hf repos branch nanthasit/my-model --list

# Create tag
hf repos tag nanthasit/my-model --create v1.0.0

# Upload folder (recommended for bulk uploads)
hf upload nanthasit/my-model ./output
```

---

## 11. Quick Reference — Common Publishing Scenarios

### Scenario A: Publish LoRA adapter

```python
api = HfApi()
api.create_repo("nanthasit/my-lora", exist_ok=True)
api.upload_folder(
    folder_path="./lora-output/",
    repo_id="nanthasit/my-lora",
    commit_message="Publish LoRA adapter v1",
    allow_patterns=["*.safetensors", "*.json", "README.md"],
)
```

### Scenario B: Publish merged + quantized model

```python
api = HfApi()
api.create_repo("nanthasit/my-model-gguf", exist_ok=True)
card = ModelCard.from_template(
    ModelCardData(language="en", license="apache-2.0",
                  library_name="transformers", pipeline_tag="text-generation"),
)
card.push_to_hub("nanthasit/my-model-gguf")
api.upload_file(
    path_or_fileobj="./output/model-Q4_K_M.gguf",
    path_in_repo="model-Q4_K_M.gguf",
    repo_id="nanthasit/my-model-gguf",
    commit_message="Add Q4_K_M GGUF",
)
```

### Scenario C: Publish benchmark results

```python
import json
results = {
    "model": "nanthasit/my-model",
    "date": "2026-07-24",
    "benchmark": {
        "simple": 0.95,
        "multiple": 0.88,
        "irrelevance": 0.92,
    },
}
api.upload_file(
    path_or_fileobj=json.dumps(results, indent=2).encode(),
    path_in_repo="results/benchmark.json",
    repo_id="nanthasit/my-model",
    commit_message="Add benchmark results",
)
```

---

## References

- `huggingface_hub` source: `src/huggingface_hub/hf_api.py` (HfApi class)
- HF Hub docs: https://huggingface.co/docs/hub/en/repositories-getting-started
- Model Cards: https://huggingface.co/docs/hub/en/model-cards
- CLI reference: built-in skill `huggingface-hub/SKILL.md`
