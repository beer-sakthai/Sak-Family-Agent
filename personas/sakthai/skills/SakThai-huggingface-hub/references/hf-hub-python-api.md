# huggingface_hub Python API Reference

> **Companion to the `hf` CLI** — this covers the **Python library** (`huggingface_hub` v1.24+).
> All `HfApi` methods are also available as top-level functions.

## Quick Install

```bash
pip install huggingface_hub
# Or with inference extras
pip install huggingface_hub[inference]
```

## Authentication

```python
from huggingface_hub import HfApi, get_token, login

# Option 1: Environment variable (recommended for automation)
# export HF_TOKEN=hf_...

# Option 2: Login once
login(token="hf_...")  # saves token to ~/.cache/huggingface/token

# Option 3: Pass token per call
api = HfApi(token="hf_...")

# Option 4: Check current token
token = get_token()  # returns str | None
```

## HfApi Class — Primary Client

```python
from huggingface_hub import HfApi

api = HfApi()                    # auto-reads token from env / cache
api = HfApi(token="hf_...")     # explicit token
api = HfApi(endpoint="https://huggingface.co")  # custom endpoint
```

All methods below work both as `api.method()` and top-level `huggingface_hub.method()`.

---

## Repository Management

### Create a Repository

```python
from huggingface_hub import create_repo

# Basic
url = create_repo("my-model")
url = create_repo("my-org/my-dataset", repo_type="dataset")

# Private repo
url = create_repo("my-private-model", private=True)

# Space with hardware config
url = create_repo("my-space", repo_type="space",
                  space_sdk="gradio",
                  space_hardware="cpu-basic",
                  space_storage="small")

# With exist_ok (no error if already exists)
url = create_repo("my-model", exist_ok=True)

print(url)  # RepoUrl object — str(RepoUrl) returns "https://huggingface.co/my-org/my-model"
```

**Parameters:** `repo_id`, `private`/`visibility`, `repo_type` (`"model"`, `"dataset"`, `"space"`), `exist_ok`, `space_sdk`, `space_hardware`, `space_storage`, `space_sleep_time`, `space_secrets`, `space_variables`, `space_volumes`.

### Delete a Repository

```python
from huggingface_hub import delete_repo

delete_repo("my-model")                        # model (default)
delete_repo("my-org/my-dataset", repo_type="dataset")
delete_repo("my-space", repo_type="space", missing_ok=True)  # no error if missing
```

### Check Repository Existence

```python
from huggingface_hub import repo_exists

repo_exists("bert-base-uncased")                    # True
repo_exists("nonexistent/model")                     # False
repo_exists("my-dataset", repo_type="dataset")
```

### Update Repository Settings

```python
from huggingface_hub import update_repo_settings

# Toggle private/public
update_repo_settings("my-model", private=True)

# Gated access ("auto" = request-based, "manual" = manual approval)
update_repo_settings("my-model", gated="auto")
```

### Move / Rename Repository

```python
from huggingface_hub import move_repo

move_repo("old-name/model", "new-name/model")
move_repo("old/dataset", "new/dataset", repo_type="dataset")
```

### Duplicate a Space

```python
from huggingface_hub import duplicate_space

url = duplicate_space("huggingface/spaces-demo", to_id="my-team/my-copy")
url = duplicate_space("org/original", to_id="my-org/copy",
                      private=True, hardware="cpu-upgrade")
```

---

## File Uploads

### Upload a Single File

```python
from huggingface_hub import upload_file

# From a local path
result = upload_file(
    path_or_fileobj="/local/path/model.safetensors",
    path_in_repo="model.safetensors",
    repo_id="my-org/my-model",
)

# From bytes
result = upload_file(
    path_or_fileobj=b"file content as bytes",
    path_in_repo="config.json",
    repo_id="my-org/my-model",
)

# To a specific revision/branch
result = upload_file(
    path_or_fileobj="model.safetensors",
    path_in_repo="model.safetensors",
    repo_id="my-org/my-model",
    revision="experimental",
)

# As a Pull Request (instead of direct commit)
result = upload_file(
    ...,
    create_pr=True,
    commit_message="Add new checkpoint",
    commit_description="PR description here",
)
```

### Upload a Folder

```python
from huggingface_hub import upload_folder

# Upload entire folder
result = upload_folder(
    folder_path="./output/checkpoint-1000",
    repo_id="my-org/my-model",
    path_in_repo="checkpoints/run-1",
    commit_message="Upload checkpoint from run 1",
)

# With file filtering (globs)
result = upload_folder(
    folder_path="./output/",
    repo_id="my-org/my-model",
    allow_patterns=["*.safetensors", "*.json"],
    ignore_patterns=["*.bin", "tmp/*"],
)

# Delete remote files matching patterns then upload
result = upload_folder(
    folder_path="./new-output/",
    repo_id="my-org/my-model",
    delete_patterns=["old-checkpoints/*"],
)

# Return info
# result.commit_url      → str
# result.commit_oid      → str  (commit SHA)
# result.commit_message  → str
```

### Upload Large Folders (Resumable)

```python
from huggingface_hub import upload_large_folder

# Best for 5GB+ folders with poor connections
upload_large_folder(
    repo_id="my-org/my-large-model",
    folder_path="./large-checkpoint/",
    repo_type="model",
    num_workers=4,
    print_report_every=120,
)
```

### Advanced: Multi-File Commits

```python
from huggingface_hub import create_commit, CommitOperationAdd, CommitOperationDelete

operations = [
    # Add a file
    CommitOperationAdd(
        path_in_repo="tokenizer.json",
        path_or_fileobj="./tokenizer.json",
    ),
    # Add a file from bytes
    CommitOperationAdd(
        path_in_repo="config.json",
        path_or_fileobj=b'{"model_type": "bert"}',
    ),
    # Delete a file
    CommitOperationDelete(
        path_in_repo="old_checkpoint.pt",
    ),
]

result = create_commit(
    repo_id="my-org/my-model",
    operations=operations,
    commit_message="Replace tokenizer and remove old checkpoint",
    commit_description="Multi-file atomic commit",
    repo_type="model",
    num_threads=5,  # parallel uploads
)
# result.commit_oid → the SHA
```

### Delete Folder

```python
from huggingface_hub import delete_folder

delete_folder(
    path_in_repo="checkpoints/v1",
    repo_id="my-org/my-model",
    commit_message="Remove old v1 checkpoints",
)
```

### Delete File

```python
from huggingface_hub import delete_file

delete_file(
    path_in_repo="old_file.pt",
    repo_id="my-org/my-model",
)
```

---

## File Downloads

### Download a Single File

```python
from huggingface_hub import hf_hub_download

# Download to cache (returns local path)
local_path = hf_hub_download(
    repo_id="bert-base-uncased",
    filename="config.json",
)

# Download to specific directory
local_path = hf_hub_download(
    repo_id="bert-base-uncased",
    filename="pytorch_model.bin",
    local_dir="./models/bert/",
)

# Specific revision
local_path = hf_hub_download(
    repo_id="my-org/my-model",
    filename="checkpoint-1000/model.safetensors",
    revision="v2.0",
)

# Force re-download
local_path = hf_hub_download(
    repo_id="bert-base-uncased",
    filename="config.json",
    force_download=True,
)
```

### Download Full Repository

```python
from huggingface_hub import snapshot_download

# Download to cache, return cache directory path
local_dir = snapshot_download("bert-base-uncased")

# Download to specific folder
local_dir = snapshot_download(
    repo_id="my-org/my-model",
    local_dir="./my-model/",
)

# With file filtering
local_dir = snapshot_download(
    repo_id="meta-llama/Llama-2-7b",
    allow_patterns=["*.json", "*.safetensors"],
    ignore_patterns=["*.bin", "*.pt"],
)

# Dataset
local_dir = snapshot_download(
    repo_id="datasets/my-dataset",
    repo_type="dataset",
    local_dir="./data/",
)

# Max parallel workers
local_dir = snapshot_download(
    repo_id="big-model",
    max_workers=16,  # default: 8
)
```

### List Repository Files

```python
from huggingface_hub import list_repo_files, list_repo_tree

# Simple flat list
files = list_repo_files("bert-base-uncased")
# ['config.json', 'pytorch_model.bin', 'vocab.txt', ...]

# Tree with metadata
for item in list_repo_tree("my-org/my-model", recursive=True):
    print(f"{item.path} ({item.type}, size={item.size})")
    # item can be RepoFile or RepoFolder
```

---

## Search & Discovery

### List Models

```python
from huggingface_hub import list_models

# All models (paginated generator)
for model in list_models():
    print(model.modelId)  # generator yields ~1000 items per page

# Filter by author
models = list(list_models(author="meta-llama"))

# Filter by task (pipeline tag)
models = list(list_models(pipeline_tag="text-classification"))

# Filter by search query
models = list(list_models(search="code generation"))

# Filter by inference provider availability
models = list(list_models(inference="warm"))  # models with warm endpoints

# Sort & limit
models = list(list_models(sort="downloads", limit=20))

# With expanded info
model = next(list_models(filter="bert", expand=["config", "cardData"]))
```

### List Datasets

```python
from huggingface_hub import list_datasets

datasets = list(list_datasets(author="bigcode"))
datasets = list(list_datasets(task_categories="text-generation"))
datasets = list(list_datasets(search="code", limit=10))
```

### List Spaces

```python
from huggingface_hub import list_spaces

spaces = list(list_spaces(author="huggingface"))
spaces = list(list_spaces(search="chatbot", limit=5))
```

### Get Repository Info

```python
from huggingface_hub import model_info, dataset_info, space_info, repo_info

# Model info
info = model_info("bert-base-uncased")
print(info.pipeline_tag)     # "fill-mask"
print(info.siblings)         # list of RepoFile entries
print(info.card_data)        # model card metadata dict

# Dataset info
info = dataset_info("bigcode/the-stack")
print(info.configs)          # dataset configs

# Generic repo info (auto-detect type)
info = repo_info("my-repo", repo_type="model")

# With file metadata
info = model_info("my-model", files_metadata=True)
```

### User Info

```python
from huggingface_hub import HfApi

api = HfApi()
me = api.whoami()
print(me["name"])           # username
print(me["auth"])           # access level (read/write)
print(me["orgs"])           # list of orgs
```

---

## Branches, Tags & Refs

```python
from huggingface_hub import create_branch, delete_branch, create_tag, delete_tag, list_repo_refs

# Branch management
create_branch("my-model", branch="experimental")
delete_branch("my-model", branch="old-branch")

# Tag management
create_tag("my-model", tag="v1.0", revision="main")
delete_tag("my-model", tag="v1.0")

# List branches and tags
refs = list_repo_refs("my-model")
print(refs.branches)  # list of GitRefInfo
print(refs.tags)      # list of GitRefInfo

# List commits
from huggingface_hub import list_repo_commits
commits = list_repo_commits("my-model", revision="main")
```

---

## Model Card & Metadata

### Update Metadata (README.md YAML)

```python
from huggingface_hub import metadata_update

# Update model card metadata
metadata_update(
    repo_id="my-org/my-model",
    metadata={
        "language": ["en", "fr"],
        "license": "apache-2.0",
        "tags": ["text-generation", "transformers"],
        "datasets": ["my-org/my-dataset"],
    },
    overwrite=False,  # merge with existing metadata
    commit_message="Update model card metadata",
)

# Overwrite all metadata
metadata_update(
    repo_id="my-org/my-model",
    metadata={"license": "mit"},
    overwrite=True,
)

# Create a Pull Request with metadata changes
metadata_update(
    repo_id="my-org/my-model",
    metadata={"language": "en"},
    create_pr=True,
)
```

### Upload a Full Model Card

```python
from huggingface_hub import ModelCard, ModelCardData

card = ModelCard.from_template(
    card_data=ModelCardData(
        language="en",
        license="apache-2.0",
        tags=["my-model"],
        metrics=["accuracy", "f1"],
    ),
    template_path="path/to/template.md",
)
card.save("README.md")

# Alternative: From template string
card = ModelCard("---\nlanguage: en\n---\n# My Model\n\nDescription...")
card.push_to_hub("my-org/my-model", commit_message="Add model card")
```

---

## Space Management

```python
from huggingface_hub import (
    add_space_secret, add_space_variable,
    get_space_runtime, restart_space,
    pause_space, delete_space_secret,
    get_space_secrets,
)

# Secrets (encrypted, not visible in logs)
add_space_secret("my-space", key="API_KEY", value="sk-...")
delete_space_secret("my-space", key="API_KEY")

# Variables (visible in Space settings)
add_space_variable("my-space", key="MODEL_NAME", value="gpt2")

# Check runtime status
runtime = get_space_runtime("my-space")
print(runtime.stage)       # SpaceStage.RUNNING / SLEEPING / PAUSED / BUILDING
print(runtime.hardware)    # "cpu-basic", "t4-small", etc.

# Control
restart_space("my-space")
pause_space("my-space")

# Get secrets/variables
secrets = get_space_secrets("my-space")
variables = get_space_variables("my-space")
```

---

## Collections

```python
from huggingface_hub import create_collection, delete_collection, update_collection_metadata, delete_collection_item

# Create a collection
col = create_collection(
    title="My Awesome Models",
    description="A curated list",
    namespace="my-org",  # optional, defaults to user
)

# Add items
col.add_item("models/bert-base-uncased")
col.add_item("spaces/my-org/my-space", note="Interactive demo")
col.add_item("datasets/my-org/dataset1")

# Update
update_collection_metadata(col.slug, title="Better Title")

# Remove items
delete_collection_item(col.slug, item="...")

# Delete whole collection
delete_collection(col.slug)
```

---

## Common Patterns & Pitfalls

### Pattern: Upload after training
```python
# After training completes
create_repo("my-org/my-model", exist_ok=True)
upload_folder(
    folder_path="./output/final",
    repo_id="my-org/my-model",
    commit_message=f"Upload trained checkpoint",
)
metadata_update("my-org/my-model", {
    "metrics": {"accuracy": 0.95},
})
```

### Pattern: Download + load model
```python
from transformers import AutoModel, AutoTokenizer

model_path = snapshot_download("my-org/my-model", local_dir="./cache/")
model = AutoModel.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)
```

### Pattern: Atomic multi-file update
```python
from huggingface_hub import create_commit, CommitOperationAdd, CommitOperationDelete

# Replace a file atomically
ops = [
    CommitOperationDelete(path_in_repo="old/tokenizer.json"),
    CommitOperationAdd(path_in_repo="new/tokenizer.json",
                       path_or_fileobj="./new/tokenizer.json"),
]
create_commit("my-org/my-model", ops, commit_message="Replace tokenizer")
```

### Pattern: Dry-run downloads
```python
# See what would be downloaded without actually downloading
info = snapshot_download("big-model", dry_run=True)
print(info)  # list of DryRunFileInfo with sizes
```

### Pitfalls

- **Token required for write operations** — reads work without auth, writes need a token with write scope.
- **Rate limits** — free tier has ~120 req/min. Use `exist_ok=True` where possible.
- **File size limit** — `upload_file` handles up to 50 GB. For larger, use `upload_large_folder`.
- **Concurrent uploads** — `create_commit` with `num_threads=5` parallelizes file uploads.
- **Repository class is deprecated** — use the `HfApi` methods instead of the old `Repository` class.
- **Metadata merge** — `metadata_update` with `overwrite=False` (default) merges; `overwrite=True` replaces all metadata.
- **`repo_type` parameter** — always specify when using non-model repos (`"dataset"`, `"space"`). Read methods default to `"model"`.
