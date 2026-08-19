---
name: SakThai-hf-hub-spaces-python-sdk
description: '# Hugging Face Spaces Python SDK'
---

# Hugging Face Spaces Python SDK

author: SakThai
license: MIT

Comprehensive reference for the `huggingface_hub` Spaces management API — the programmatic interface for managing Spaces on the Hugging Face Hub. Covers all space lifecycle operations, runtime management, secrets/variables, volumes, logging, dev mode, and semantic search.

## Overview

The Spaces Python SDK is a set of methods on `HfApi` (and standalone function aliases in `huggingface_hub`) that let you manage Spaces programmatically — create, list, pause, restart, configure hardware/sleep, set secrets/variables, mount volumes, fetch logs, and wait for terminal states. All operations go through the `https://huggingface.co/api/spaces/` REST endpoints.

## Core Methods

### Lifecycle Management

| Method | API Endpoint | Description |
|--------|-------------|-------------|
| `create_repo(repo_type="space", space_sdk, space_hardware, ...)` | `POST /api/spaces` | Create a new Space |
| `delete_repo()` | `DELETE /api/spaces/{id}` | Delete a Space |
| `restart_space(repo_id, factory_reboot=False)` | `POST /api/spaces/{id}/restart` | Restart a Space (opt. factory reboot) |
| `pause_space(repo_id)` | `POST /api/spaces/{id}/pause` | Pause a Space (stop billing) |
| `duplicate_space(from_id, to_id, ...)` *(deprecated, use `duplicate_repo`)* | `POST /api/spaces/{id}/duplicate` | Server-side copy |

### Runtime & Hardware

| Method | API Endpoint | Description |
|--------|-------------|-------------|
| `space_info(repo_id)` | `GET /api/spaces/{id}` | Full Space metadata + siblings |
| `get_space_runtime(repo_id)` | `GET /api/spaces/{id}/runtime` | Current stage, hardware, sleep_time, volumes |
| `request_space_hardware(repo_id, hardware, sleep_time)` | `POST /api/spaces/{id}/hardware` | Change hardware tier |
| `set_space_sleep_time(repo_id, sleep_time)` | `POST /api/spaces/{id}/sleeptime` | Set custom inactivity timeout |
| `list_spaces_hardware()` | `GET /api/spaces/hardware` | List available hardware options |
| `wait_for_space(repo_id, timeout, poll_interval)` | Polls `get_space_runtime` | Blocks until Space reaches terminal stage |

### Secrets & Variables

| Method | API Endpoint | Description |
|--------|-------------|-------------|
| `add_space_secret(repo_id, key, value, description)` | `POST /api/spaces/{id}/secrets` | Add/update a secret (write-only) |
| `get_space_secrets(repo_id)` | `GET /api/spaces/{id}/secrets` | List secrets (values hidden, only metadata) |
| `delete_space_secret(repo_id, key)` | `DELETE /api/spaces/{id}/secrets` | Remove a secret |
| `add_space_variable(repo_id, key, value, description)` | `POST /api/spaces/{id}/variables` | Add/update an env variable |
| `get_space_variables(repo_id)` | `GET /api/spaces/{id}/variables` | List all variables |
| `delete_space_variable(repo_id, key)` | `DELETE /api/spaces/{id}/variables` | Remove a variable |

### Volumes (Persistent Storage)

| Method | API Endpoint | Description |
|--------|-------------|-------------|
| `set_space_volumes(repo_id, volumes)` | `PUT /api/spaces/{id}/volumes` | Set (replace) all mounted volumes |
| `delete_space_volumes(repo_id)` | `DELETE /api/spaces/{id}/volumes` | Remove all volumes |

### Dev Mode

| Method | API Endpoint | Description |
|--------|-------------|-------------|
| `enable_space_dev_mode(repo_id)` | `POST /api/spaces/{id}/dev-mode` | Enable dev mode (PRO+ plan) |
| `disable_space_dev_mode(repo_id)` | `POST /api/spaces/{id}/dev-mode` | Disable dev mode |

### Logs

| Method | API Endpoint | Description |
|--------|-------------|-------------|
| `fetch_space_logs(repo_id, build, follow)` | `GET /api/spaces/{id}/logs/{run\|build}` | SSE stream of run or build logs |

### Discovery & Search

| Method | API Endpoint | Description |
|--------|-------------|-------------|
| `list_spaces(filter, author, search, sort, limit, ...)` | `GET /api/spaces` | List/filter Spaces (paginated) |
| `search_spaces(query, filter, sdk, include_non_running)` | `GET /api/spaces/semantic-search` | Semantic search (embedding-based) |
| `list_space_templates()` | `GET /api/spaces/templates` | List official Space templates |

## Data Model Classes

### `SpaceRuntime`
The current runtime state of a Space, returned by `get_space_runtime`, `pause_space`, `restart_space`, `request_space_hardware`, etc.

```python
@dataclass
class SpaceRuntime:
    stage: SpaceStage          # e.g. "RUNNING", "BUILDING", "PAUSED", "BUILD_ERROR"
    hardware: SpaceHardware | None        # e.g. "cpu-basic", "t4-medium"
    requested_hardware: SpaceHardware | None
    sleep_time: int | None               # seconds of inactivity before sleep
    storage: SpaceStorage | None         # deprecated, use volumes
    dev_mode: bool
    hot_reloading: SpaceHotReloading | None
    volumes: list[Volume] | None
    raw: dict                             # full server response
```

### `SpaceSecret`
Write-only secret metadata (value never returned).

```python
@dataclass
class SpaceSecret:
    key: str
    description: str | None
    updated_at: datetime | None
```

### `SpaceVariable`
Public environment variable metadata (value IS returned).

```python
@dataclass
class SpaceVariable:
    key: str
    value: str
    description: str | None
    updated_at: datetime | None
```

### `Volume`
Describes a volume mount (bucket, model, dataset, or Space).

```python
@dataclass
class Volume:
    type: Literal["bucket", "model", "dataset", "space"]
    source: str                  # e.g. "username/my-bucket"
    mount_path: str              # e.g. "/data" (must start with /)
    revision: str | None = None  # git revision for repos
    read_only: bool | None = None
    path: str | None = None      # subfolder prefix

    def to_dict(self) -> dict: ...
    def to_uri(self) -> str: ...  # HF mount URI format
```

### `SpaceHardware` (Enum)
```python
CPU_BASIC = "cpu-basic"       # Free tier
CPU_UPGRADE = "cpu-upgrade"   # Paid CPU
ZERO_A10G = "zero-a10g"       # ZeroGPU (free, limited)
T4_SMALL / T4_MEDIUM = "t4-small" / "t4-medium"
L4X1 / L4X4 = "l4x1" / "l4x4"
L40SX1 / L40SX4 / L40SX8 = "l40sx1" / "l40sx4" / "l40sx8"
A10G_SMALL / A10G_LARGE / A10G_LARGEX2 / A10G_LARGEX4
A100_LARGE / A100X4 / A100X8
```

### `SpaceStorage` (Enum) — deprecated, use Volumes
```python
SMALL = "small"   # 50 GB
MEDIUM = "medium" # 150 GB
LARGE = "large"   # 500 GB
```

### `SpaceInfo`
Full metadata for a Space repo, returned by `space_info` and `list_spaces`.

### `SpaceSearchResult`
A single result from `search_spaces` (semantic search), including `ai_category`, `semantic_relevancy_score`, `ai_short_description`.

### `SpaceTemplate`
```python
@dataclass
class SpaceTemplate:
    name: str               # "JupyterLab", "chatbot", "Streamlit"
    repo_id: str            # "SpacesExamples/jupyterlab"
    sdk: str                # "gradio", "docker", "static"
    preferred_private: bool
```

## Key Patterns

### Create a Space from a Template
```python
from huggingface_hub import create_repo, list_space_templates

templates = list_space_templates()
jupyter_template = next(t for t in templates if t.name == "JupyterLab")

url = create_repo(
    "my-jupyter-space",
    repo_type="space",
    space_sdk="docker",
    space_template=jupyter_template.repo_id,
)
```

### Lifecycle: Restart → Wait → Verify
```python
from huggingface_hub import restart_space, wait_for_space

restart_space("username/my-space", factory_reboot=True)
runtime = wait_for_space("username/my-space", timeout=120)
assert runtime.stage == "RUNNING", f"Build failed: {runtime.stage}"
```

### Manage Secrets
```python
from huggingface_hub import HfApi

api = HfApi()
api.add_space_secret("username/my-space", "OPENAI_KEY", "sk-...", 
                     description="OpenAI API key")

# List secrets (values never returned)
secrets = api.get_space_secrets("username/my-space")
for key, secret in secrets.items():
    print(f"{key}: updated {secret.updated_at}")
```

### Mount Volumes
```python
from huggingface_hub import HfApi, Volume

api = HfApi()
api.set_space_volumes(
    "username/my-space",
    volumes=[
        Volume(type="model", source="username/my-model", 
               mount_path="/models", read_only=True),
        Volume(type="bucket", source="username/my-bucket", 
               mount_path="/data"),
    ],
)
```

### Fetch Build Logs for Debugging
```python
from huggingface_hub import fetch_space_logs

# Non-blocking: get current build logs
for line in fetch_space_logs("username/my-space", build=True):
    print(line, end="")

# Real-time streaming of run logs
for line in fetch_space_logs("username/my-space", follow=True):
    print(line, end="")
```

### Semantic Search
```python
from huggingface_hub import HfApi

api = HfApi()
results = list(api.search_spaces("generate image", sdk="gradio"))
for r in results[:5]:
    print(f"{r.id} — {r.ai_category} (score: {r.semantic_relevancy_score:.2f})")
```

## Edge Cases & Constraints

- **Static Spaces** cannot be paused, restarted, or mounted with volumes. Attempting these raises `BadRequestError`.
- **CPU-basic** (free) hardware has a fixed 48h sleep timeout — `set_space_sleep_time` warns but won't apply.
- **Factory reboot** (`restart_space(factory_reboot=True)`) rebuilds from scratch, clearing all cached dependencies.
- **Secrets are write-only**: values are never returned by `get_space_secrets`. Store them externally if you need to reference them.
- **Volume paths** must start with `/`. Volume `type` determines read_only defaults: repos are forced `True`, buckets default `False`.
- **Dev Mode** requires a PRO or Team & Enterprise plan.
- **Intermediate stages** during startup: `BUILDING`, `RUNNING_BUILDING`, `APP_STARTING`, `RUNNING_APP_STARTING`. Use `wait_for_space` to wait for terminal stage.

## Sources

- Source code: `huggingface_hub._space_api` (SpaceRuntime, SpaceSecret, SpaceVariable, Volume, SpaceHardware, SpaceStorage, SpaceSearchResult, SpaceTemplate, SpaceHotReloading)
- Source code: `huggingface_hub.hf_api` (all space-related HfApi methods)
- Docstrings verified against huggingface_hub v1.24.0
