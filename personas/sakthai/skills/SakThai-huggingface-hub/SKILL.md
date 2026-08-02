---
name: SakThai-huggingface-hub
description: "HuggingFace hf CLI: search/download/upload models, datasets."
---
# Hugging Face CLI (`hf`) Reference Guide

The `hf` command is the modern command-line interface for interacting with the Hugging Face Hub, providing tools to manage repositories, models, datasets, and Spaces.

> **IMPORTANT:** The `hf` command replaces the now deprecated `huggingface-cli` command.

## Quick Start
*   **Installation:** `curl -LsSf https://hf.co/cli/install.sh | bash -s`
*   **Help:** Use `hf --help` to view all available functions and real-world examples.
*   **Authentication:** Recommended via `HF_TOKEN` environment variable or the `--token` flag.

---

## Core Commands

### General Operations
*   `hf download REPO_ID`: Download files from the Hub.
*   `hf upload REPO_ID`: Upload files/folders (recommended for single-commit).
*   `hf upload-large-folder REPO_ID LOCAL_PATH`: Recommended for resumable uploads of large directories.
*   `hf sync`: Sync files between a local directory and a bucket.
*   `hf env` / `hf version`: View environment and version details.

### Authentication (`hf auth`)
*   `login` / `logout`: Manage sessions using tokens from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
*   `list` / `switch`: Manage and toggle between multiple stored access tokens.
*   `whoami`: Identify the currently logged-in account.

### Repository Management (`hf repos`)
*   `create` / `delete`: Create or permanently remove repositories.
*   `duplicate`: Clone a model, dataset, or Space to a new ID.
*   `move`: Transfer a repository between namespaces.
*   `branch` / `tag`: Manage Git-like references.
*   `delete-files`: Remove specific files using patterns.

---

## Specialized Hub Interactions

### Datasets & Models
*   **Datasets:** `hf datasets list`, `info`, and `parquet` (list parquet URLs).
*   **SQL Queries:** `hf datasets sql SQL` — Execute raw SQL via DuckDB against dataset parquet URLs.
*   **Models:** `hf models list` and `info`.
*   **Papers:** `hf papers list` — View daily papers.

### Discussions & Pull Requests (`hf discussions`)
*   Manage the lifecycle of Hub contributions: `list`, `create`, `info`, `comment`, `close`, `reopen`, and `rename`.
*   `diff`: View changes in a PR.
*   `merge`: Finalize pull requests.

### Infrastructure & Compute
*   **Endpoints:** Deploy and manage Inference Endpoints (`deploy`, `pause`, `resume`, `scale-to-zero`, `catalog`).
*   **Jobs:** Run compute tasks on HF infrastructure. Includes `hf jobs uv` for running Python scripts with inline dependencies and `stats` for resource monitoring.
*   **Spaces:** Manage interactive apps. Includes `dev-mode` and `hot-reload` for Python files without full restarts.

## InferenceClient — Serverless Inference API

`InferenceClient` (`huggingface_hub`) routes requests through multiple providers (Together, Replicate, fal.ai, Novita). Use it for chat, text-to-image, embeddings, speech, and more — all serverless, all via the Hub.

### Quick Patterns
```python
from huggingface_hub import InferenceClient

client = InferenceClient()                           # auto provider
client = InferenceClient(provider="fal-ai")           # pinned provider
client = InferenceClient(timeout=30)                  # with timeout

# Chat
result = client.chat_completion(
    model="deepseek-ai/DeepSeek-R1",
    messages=[{"role": "user", "content": "Hello!"}],
)

# Streaming
stream = client.chat_completion(model="...", messages=[...], stream=True)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")

# Image generation
client.text_to_image("A cat", model="black-forest-labs/FLUX.1-schnell")

# Async
from huggingface_hub import AsyncInferenceClient
async def main():
    async with AsyncInferenceClient() as c:
        r = await c.chat_completion(model="...", messages=[...])
```

### OpenAI-Compatible Endpoint
```python
from openai import OpenAI
client = OpenAI(base_url="https://router.huggingface.co/v1", api_key="hf_...")
# Model suffix: :fastest, :cheapest, :preferred
client.chat.completions.create(model="deepseek-ai/DeepSeek-R1:fastest", ...)
```

### Full Reference
See [`references/hf-inference-client.md`](references/hf-inference-client.md) — covers all methods, function calling, structured outputs, billing, and task-specific patterns.

## Python API Reference
See [`references/hf-hub-python-api.md`](references/hf-hub-python-api.md) — covers the `huggingface_hub` Python library (`HfApi` class, `create_repo`, `upload_folder`, `snapshot_download`, `hf_hub_download`, `create_commit`, metadata updates, Space management, collections, and common automation patterns). All `HfApi` methods also work as top-level functions.

### Cache Internals & Environment Variables
See [`references/hf-hub-cache-and-env.md`](references/hf-hub-cache-and-env.md) — deep-dive into:
- **Environment variables:** `HF_HOME`, `HF_HUB_CACHE`, `HF_TOKEN`, `HF_XET_CACHE`, `HF_ASSETS_CACHE`, `HF_HUB_VERBOSITY`, and more — with exact defaults and best practices.
- **Cache system internals:** Blob/snapshot/refs/trees directory structure, `scan_cache_dir()` for programmatic inspection, `DeleteCacheStrategy` for non-destructive cleanup, `try_to_load_from_cache()`, and `cached_assets_path()`.
- **HfApi utilities:** Programmatic workflows (`create_repo` + `upload_folder`, `snapshot_download`, `CommitOperationAdd/Delete` for atomic commits), token management, Space secrets, webhooks, collections, and common automation patterns.
- **Troubleshooting:** cache bloat, download timeouts, symlink warnings on Windows, hf_transfer for faster downloads.

### Storage — Buckets API (`hf://buckets/...`)
*   **Buckets (v1.x):** Full S3-like object storage on the Hub — no Git/LFS overhead.
    - **CLI:** `hf buckets create|list|info|delete|rm|move|cp|sync`
    - **Python API:** `create_bucket()`, `list_buckets()`, `batch_bucket_files()`, `sync_bucket()`, `download_bucket_files()`
    - **Sync:** Bidirectional local↔bucket with filter patterns, plan/apply workflow, dry-run
    - **URL format:** `hf://buckets/{namespace}/{name}(/path)`
    - **Zero-cost:** Free on Hub's free tier (public unlimited, private with limits)
    - **Full reference:** [`references/hf-learnings.md`](references/hf-learnings.md) — Buckets deep-dive (Topic #105)
*   **Cache:** Manage local storage with `hf cache list`, `hf cache prune` (remove detached revisions), and `hf cache verify` (checksum checks). Or use the Python API for fine-grained: `scan_cache_dir().delete_revisions()`.
*   **Webhooks:** Automate workflows by managing Hub webhooks (`create`, `watch`, `enable`/`disable`).
*   **Collections:** Organize Hub items into collections (`add-item`, `update`, `list`).

---

## Advanced Usage & Tips

### Global Flags
*   `--format json`: Produces machine-readable output for automation.
*   `-q` / `--quiet`: Limits output to IDs only.

### Extensions & Skills
*   **Extensions:** Extend CLI functionality via GitHub repositories using `hf extensions install REPO_ID`.
*   **Skills:** Manage AI assistant skills with `hf skills add`.
