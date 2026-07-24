# HF Hub Configuration & Environment Variables — Complete Reference (2026-07-24)

## Summary
Comprehensive deep-dive into the `huggingface_hub` library's configuration system — every environment variable, cache path, authentication mechanism, boolean toggle, and customization option. Based on the official docs and source code at `constants.py` (v1.24.0).

## Key Sources
- Official docs: https://huggingface.co/docs/huggingface_hub/en/package_reference/environment_variables
- Source: `huggingface_hub/constants.py` (main branch, v1.24.0)
- Source: `huggingface_hub/utils/_token.py`

---

## 1. Path & Directory Variables

### HF_HOME — Base directory for all Hugging Face data
```python
# Resolution order:
# 1. HF_HOME env var
# 2. $XDG_CACHE_HOME/huggingface  (if XDG_CACHE_HOME is set)
# 3. ~/.cache/huggingface          (default)
```
- **Type**: Directory path
- **Default**: `~/.cache/huggingface`
- **Also used by**: `transformers`, `datasets`, `diffusers`, `gradio`
- **Contains**: hub cache, assets cache, token file, stored tokens, update-check marker

### HF_HUB_CACHE — Model/dataset download cache
```python
# Resolution order:
# 1. HF_HUB_CACHE env var (NEW, preferred)
# 2. HUGGINGFACE_HUB_CACHE env var (deprecated)
# 3. $HF_HOME/hub                  (default)
```
- **Type**: Directory path
- **Default**: `~/.cache/huggingface/hub`
- **Structure**: `{HF_HUB_CACHE}/models--{org}--{repo}/snapshots/{revision}/`
- **Legacy**: `HUGGINGFACE_HUB_CACHE` is deprecated but still falls back

### HF_ASSETS_CACHE — Non-essential cached data
```python
# Resolution order:
# 1. HF_ASSETS_CACHE env var (NEW, preferred)
# 2. HUGGINGFACE_ASSETS_CACHE env var (deprecated)
# 3. $HF_HOME/assets               (default)
```
- **Type**: Directory path
- **Default**: `~/.cache/huggingface/assets`
- **Used by**: downloaded configs, auxiliary files, cached metadata

### HF_XET_CACHE — Xet storage cache
- **Type**: Directory path
- **Default**: Inside `HF_HOME` (Xet-managed)
- **Purpose**: Cache for Xet chunk-based storage system
- **Xet-specific**: `HF_XET_CHUNK_CACHE_SIZE_BYTES` (default 100 MB), `HF_XET_SHARD_CACHE_SIZE_LIMIT`, `HF_XET_NUM_CONCURRENT_RANGE_GETS`

### HF_TOKEN_PATH — Auth token file location
```python
# Resolution order:
# 1. HF_TOKEN_PATH env var
# 2. $HF_HOME/token               (default)
```
- **Default**: `~/.cache/huggingface/token`
- **Format**: Plaintext file containing the HF token string
- **Stored tokens dir**: `~/.cache/huggingface/stored_tokens/`

### HF_STORED_TOKENS_PATH — Multiple tokens directory
- **Derived from**: `os.path.join(os.path.dirname(HF_TOKEN_PATH), "stored_tokens")`
- **Purpose**: Directory containing named token files for fine-grained token management

---

## 2. Authentication & Token Variables

### HF_TOKEN — Primary auth token
```python
# Resolution order:
# 1. HF_TOKEN env var
# 2. File at HF_TOKEN_PATH
# 3. HuggingFace CLI `login()` stored token
```
- **Type**: String (the token itself)
- **Replaces**: deprecated `HUGGING_FACE_HUB_TOKEN`
- **Scope**: Read/write access to repos based on token permissions

### HF_HUB_DISABLE_IMPLICIT_TOKEN
- **Type**: Boolean (`1`, `ON`, `YES`, `TRUE`)
- **Default**: Not set (tokens are sent implicitly)
- **Effect**: When set, the cached token is NOT automatically sent in HTTP requests to the Hub. Useful for CI environments or when you want to explicitly control auth.

### Token resolution in code (`utils/_token.py`)
```python
def get_token():
    # 1. Check HF_TOKEN env var
    # 2. Read from HF_TOKEN_PATH file
    # 3. Check HfFolder (legacy)
    # Returns None if not found
```

### Fine-grained tokens
- Newer system supporting multiple named tokens stored under `stored_tokens/` directory
- Each token file has a name (e.g., `stored_tokens/read-token`, `stored_tokens/write-token`)
- The default token is still at `HF_TOKEN_PATH`

---

## 3. Endpoint & Network Variables

### HF_ENDPOINT — Custom Hub endpoint
```python
ENDPOINT = os.getenv("HF_ENDPOINT", "https://huggingface.co").rstrip("/")
```
- **Default**: `https://huggingface.co`
- **Purpose**: Point to a self-hosted Hub instance or staging server
- **Override**: `HUGGINGFACE_CO_STAGING` env var forces staging endpoint
- **Impact**: Changes ALL URL templates (`resolve`, `api`, `blob`, etc.)

### HUGGINGFACE_CO_STAGING — Staging mode
- **Type**: Boolean
- **Effect**: Forces `ENDPOINT` to `https://hub-ci.huggingface.co`
- **Also redirects**: Cache to `~/.cache/huggingface_staging/` to prevent mixing prod/staging data

### HF_INFERENCE_ENDPOINT — Inference API URL
```python
INFERENCE_ENDPOINT = os.environ.get("HF_INFERENCE_ENDPOINT", "https://api-inference.huggingface.co")
```
- **Default**: `https://api-inference.huggingface.co`
- **Purpose**: Custom inference endpoint for `InferenceClient`

### DATASETS_SERVER_ENDPOINT — Datasets server
- **Hardcoded**: `https://datasets-server.huggingface.co`
- **Not configurable** via env var (as of v1.24.0)

### Additional endpoint constants (hardcoded)
| Constant | Value | Purpose |
|----------|-------|---------|
| `INFERENCE_ENDPOINTS_ENDPOINT` | `https://api.endpoints.huggingface.cloud/v2` | Inference Endpoints API |
| `INFERENCE_CATALOG_ENDPOINT` | `https://endpoints.huggingface.co/api/catalog` | Inference catalog |
| `INFERENCE_PROXY_TEMPLATE` | `https://router.huggingface.co/{provider}` | Third-party provider proxy |

---

## 4. Boolean Toggle Variables

All boolean env vars use the same truthy set:
```python
ENV_VARS_TRUE_VALUES = {"1", "ON", "YES", "TRUE"}
```

### Cache & Filesystem

| Variable | Effect when set to `true` |
|----------|---------------------------|
| `HF_HUB_OFFLINE` | No HTTP requests allowed; raises `OfflineModeIsEnabled` exception. Also triggered by `TRANSFORMERS_OFFLINE`. |
| `HF_HUB_DISABLE_SYMLINKS` | Files are **copied** instead of symlinked in cache (important on Windows without developer mode) |
| `HF_HUB_DISABLE_SYMLINKS_WARNING` | Suppresses the warning about unsupported symlinks |
| `HF_HUB_DISABLE_XET` | Disables Xet storage system, falls back to regular Git LFS |

### Telemetry & Output

| Variable | Effect when set to `true` |
|----------|---------------------------|
| `HF_HUB_DISABLE_TELEMETRY` | Disables all telemetry requests. Also triggered by `DISABLE_TELEMETRY` or `DO_NOT_TRACK` |
| `HF_HUB_DISABLE_PROGRESS_BARS` | Suppresses all progress bars globally. `None` = user can toggle programmatically. |
| `HF_HUB_DISABLE_EXPERIMENTAL_WARNING` | Suppresses warnings about experimental features |
| `HF_HUB_DISABLE_UPDATE_CHECK` | Skips the "new version available" PyPI check on startup |
| `HF_DEBUG` | Enables debug logging + prints curl commands for all Hub HTTP requests |
| `NO_COLOR` | Disables ANSI colors in `hf` CLI output (from external `no-color.org` standard) |

### Auth

| Variable | Effect when set to `true` |
|----------|---------------------------|
| `HF_HUB_DISABLE_IMPLICIT_TOKEN` | Stops automatic token injection in HTTP requests |

### Performance

| Variable | Effect when set to `true` |
|----------|---------------------------|
| `HF_XET_HIGH_PERFORMANCE` | Enables high-performance Xet transfer (replaces deprecated `HF_HUB_ENABLE_HF_TRANSFER`) |
| `HF_HUB_ENABLE_HF_TRANSFER` | **DEPRECATED**. Now warns at import time. Use `HF_XET_HIGH_PERFORMANCE` instead. |

### Xet-specific

| Variable | Type | Default | Effect |
|----------|------|---------|--------|
| `HF_XET_HIGH_PERFORMANCE` | bool | not set | High-performance Xet mode |
| `HF_XET_CHUNK_CACHE_SIZE_BYTES` | int | 100 MB | Max size of Xet chunk cache |
| `HF_XET_SHARD_CACHE_SIZE_LIMIT` | int | — | Shard cache size limit |
| `HF_XET_NUM_CONCURRENT_RANGE_GETS` | int | — | Concurrent range GET requests for Xet |
| `HF_XET_RECONSTRUCT_WRITE_SEQUENTIALLY` | bool | not set | Sequential writes instead of parallel (use on HDDs to reduce seeking) |

---

## 5. Verbosity & Timeout Variables

### HF_HUB_VERBOSITY
- **Type**: Log level string (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- **Default**: `WARNING` (or `INFO` if not set)
- **Effect**: Controls `huggingface_hub`'s internal logger level

### HF_HUB_ETAG_TIMEOUT
- **Type**: Integer (seconds)
- **Default**: `10`
- **Purpose**: Timeout for ETag HEAD requests when checking if a cached file is still up-to-date

### HF_HUB_DOWNLOAD_TIMEOUT
- **Type**: Integer (seconds)
- **Default**: `10`
- **Note**: The actual download timeout is 500s — this controls the connection/read timeout for the HEAD request before downloading

### DEFAULT_REQUEST_TIMEOUT
- **Type**: Integer (seconds)
- **Default**: `10`
- **Purpose**: General HTTP request timeout for Hub API calls

---

## 6. File Constants & Naming

### Weight file patterns
| Constant | Value |
|----------|-------|
| `PYTORCH_WEIGHTS_NAME` | `pytorch_model.bin` |
| `SAFETENSORS_SINGLE_FILE` | `model.safetensors` |
| `SAFETENSORS_INDEX_FILE` | `model.safetensors.index.json` |
| `TF2_WEIGHTS_NAME` | `tf_model.h5` |
| `TF_WEIGHTS_NAME` | `model.ckpt` |
| `FLAX_WEIGHTS_NAME` | `flax_model.msgpack` |
| `CONFIG_NAME` | `config.json` |
| `REPOCARD_NAME` | `README.md` |

### Download constants
| Constant | Value | Purpose |
|----------|-------|---------|
| `DOWNLOAD_CHUNK_SIZE` | 10 MB | Chunk size for download streaming |
| `MAX_HTTP_DOWNLOAD_SIZE` | 50 GB | Max single file HTTP download |
| `DEFAULT_ETAG_TIMEOUT` | 10s | Timeout for ETag checks |
| `DEFAULT_DOWNLOAD_TIMEOUT` | 10s | Timeout for download requests |
| `DEFAULT_REQUEST_TIMEOUT` | 10s | Timeout for API requests |
| `FILELOCK_LOG_EVERY_SECONDS` | 10s | Log interval for file lock acquisition |

### Git & revision
| Constant | Value |
|----------|-------|
| `DEFAULT_REVISION` | `main` |
| `REGEX_COMMIT_OID` | `[A-Fa-f0-9]{5,40}` |

---

## 7. Deprecated Variables (fully mapped)

| Deprecated Variable | Replacement | Status |
|--------------------|-------------|--------|
| `HUGGINGFACE_HUB_CACHE` | `HF_HUB_CACHE` | Fallback (lower priority) |
| `HUGGINGFACE_ASSETS_CACHE` | `HF_ASSETS_CACHE` | Fallback (lower priority) |
| `HUGGING_FACE_HUB_TOKEN` | `HF_TOKEN` | Fallback in token resolution |
| `HF_HUB_ENABLE_HF_TRANSFER` | `HF_XET_HIGH_PERFORMANCE` | Emits `FutureWarning` on import |
| `TRANSFORMERS_OFFLINE` | `HF_HUB_OFFLINE` | Still triggers offline mode |

---

## 8. External/Standard Environment Variables

| Variable | Effect |
|----------|--------|
| `XDG_CACHE_HOME` | Used to derive `HF_HOME` when `HF_HOME` is not set → `$XDG_CACHE_HOME/huggingface` |
| `DO_NOT_TRACK` | Disables telemetry globally across HF ecosystem (equivalent to `HF_HUB_DISABLE_TELEMETRY`) |
| `DISABLE_TELEMETRY` | Same effect as `DO_NOT_TRACK` |
| `NO_COLOR` | Disables ANSI color sequences in `hf` CLI output |

---

## 9. Practical Use Cases

### Offline mode (no network — work from cache)
```bash
export HF_HUB_OFFLINE=1
python my_script.py  # raises OfflineModeIsEnabled if it tries network calls
```
Best practice: check `huggingface_hub.is_offline_mode()` before making requests.

### Custom cache location (limited disk space)
```bash
export HF_HOME=/data/huggingface
# or just the hub cache:
export HF_HUB_CACHE=/fast-ssd/models-cache
```

### CI/CD — controlled auth
```bash
export HF_TOKEN=hf_your_token_here
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1
```

### Disable all telemetry & progress bars
```bash
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_DISABLE_PROGRESS_BARS=1
export HF_HUB_DISABLE_UPDATE_CHECK=1
```

### Debug network issues
```bash
export HF_DEBUG=1
# Every Hub HTTP request is printed as a curl command you can copy & paste
```

### Self-hosted Hub
```bash
export HF_ENDPOINT=https://my-hub.example.com
# All API calls now go to your custom endpoint
```

### HDD-friendly Xet
```bash
export HF_XET_RECONSTRUCT_WRITE_SEQUENTIALLY=1
```

### Staging environment testing
```bash
export HUGGINGFACE_CO_STAGING=1
# Uses hub-ci.huggingface.co + separate cache dir
```

---

## 10. Cache Directory Structure

```
~/.cache/huggingface/                    # HF_HOME
├── hub/                                 # HF_HUB_CACHE
│   ├── models--bert-base-uncased/       # repo_id with '--' separator
│   │   ├── refs/
│   │   │   └── main                     # pointer to current snapshot
│   │   ├── snapshots/
│   │   │   └── {commit_hash}/
│   │   │       ├── config.json
│   │   │       └── pytorch_model.bin
│   │   └── blobs/                       # Xet blob storage
│   │       └── {hash}
│   ├── datasets--org--dataset/
│   └── spaces--org--space/
├── assets/                              # HF_ASSETS_CACHE
├── token                                # HF_TOKEN_PATH
├── stored_tokens/                       # fine-grained tokens
│   ├── read-token
│   └── write-token
├── .check_for_update_done               # marker file (24h expiry)
└── .agent_harnesses.json                # AI agent harnesses registry
```

- Repo cache naming uses `--` as separator: `models--org--repo-name`
- Snapshots are named by commit hash (revision)
- Symlinks point from snapshot files to blob store (unless `HF_HUB_DISABLE_SYMLINKS=1`)
- Xet uses its own blob storage under each repo directory with CAS (Content-Addressable Storage)

---

## 11. HF URI System (`hf://`)

The library also supports `hf://` URIs for referencing Hub resources:
- `hf://models/org/repo` — model repo
- `hf://datasets/org/repo` — dataset repo
- `hf://spaces/org/repo` — Space
- `hf://buckets/org/repo` — Bucket

URI prefixes map to canonical types:
```python
HF_URI_TYPE_PREFIXES = {
    "models": "model",
    "datasets": "dataset",
    "spaces": "space",
    "kernels": "kernel",
    "buckets": "bucket",
}
```

The library validates hosts via `HF_URL_HOSTS` (includes public Hub, staging, and custom endpoints).

---

## 12. Source Code Internals: `constants.py` Architecture

Key design patterns in the source:
1. **Last-resolve pattern**: Path vars use `os.getenv("VAR", fallback)` with fallback chains — each fallback checks the deprecated variable before the hardcoded default
2. **`_is_true()` parser**: All boolean vars share the same truthy set `{"1", "ON", "YES", "TRUE"}`; case-insensitive
3. **Staging isolation**: When `HUGGINGFACE_CO_STAGING` is set, ALL cache/token paths redirect to `~/.cache/huggingface_staging/` — preventing any cross-contamination between prod and staging data
4. **Module-level singletons**: Most constants are computed at import time (module level) — changing env vars after import has no effect unless the consuming code re-reads them
5. **Progress bar priority**: Env var > programmatic — if `HF_HUB_DISABLE_PROGRESS_BARS` is set in the environment, code cannot override it

### Key Python API functions for config
```python
from huggingface_hub import (
    is_offline_mode,          # returns bool
    get_token,                # returns token or None
    HfApi,                    # uses configured ENDPOINT
    InferenceClient,          # uses configured INFERENCE_ENDPOINT
    hf_hub_url,               # uses HUGGINGFACE_CO_URL_TEMPLATE
)
```

---

## 13. Changelog from Recent Versions

- **v1.23+**: `HF_HUB_ENABLE_HF_TRANSFER` deprecated in favor of `HF_XET_HIGH_PERFORMANCE`
- **v1.22+**: Fine-grained token management (`stored_tokens/` directory)
- **v1.20+**: Xet storage system with its own env var namespace (`HF_XET_*`)
- **v1.18+**: `HF_ENDPOINT` replaces ad-hoc endpoint configuration
- **v1.16+**: `HF_TOKEN` becomes canonical auth env var, replacing `HUGGING_FACE_HUB_TOKEN`
- **v1.14+**: `HF_HUB_CACHE` and `HF_ASSETS_CACHE` become canonical cache vars, replacing `HUGGINGFACE_HUB_CACHE` and `HUGGINGFACE_ASSETS_CACHE`
