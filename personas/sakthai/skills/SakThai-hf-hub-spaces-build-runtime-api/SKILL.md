---
name: SakThai-hf-hub-spaces-build-runtime-api
description: "Complete reference for the Hugging Face Spaces Build, Runtime, and Management API\
  \ \u2014 covering SpaceRuntime stages, hardware management, secrets/variables, dev\
  \ mode, logs streaming, wait_for_space, pause/restart, and duplicate workflows via\
  \ huggingface_hub."
---

# Spaces Build, Runtime & Management API — Complete Reference

The Hugging Face Hub provides a comprehensive REST API (exposed via `huggingface_hub.HfApi`) for managing Spaces programmatically: checking build/runtime status, fetching logs, changing hardware, managing secrets and variables, pausing/restarting, and more.

## API Entry Points

All operations are available on the `HfApi` class under `huggingface_hub`:

```python
from huggingface_hub import HfApi
api = HfApi(token="your_token")
```

## SpaceRuntime — The Core Status Object

The `SpaceRuntime` dataclass represents the current operational state of a Space. Constructed from the `/api/spaces/{repo_id}/runtime` endpoint.

### Fields

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `stage` | `str` | `data["stage"]` | Current lifecycle stage (see table below) |
| `hardware` | `str\|None` | `data["hardware"]["current"]` | Currently allocated hardware SKU |
| `requested_hardware` | `str\|None` | `data["hardware"]["requested"]` | Requested hardware SKU (may differ during transition) |
| `sleep_time` | `int\|None` | `data["gcTimeout"]` | Seconds of inactivity before sleep (upgraded HW only) |
| `storage` | `str\|None` | `data["storage"]` | Persistent storage size (e.g. `"small"`, `"medium"`, `"large"`) |
| `dev_mode` | `bool` | `data.get("devMode", False)` | Whether dev mode is enabled |
| `hot_reloading` | `SpaceHotReloading\|None` | `data.get("hotReloading")` | Hot reloading config (PRO/Team plan) |
| `volumes` | `list[Volume]\|None` | `data.get("volumes")` | Attached volume mounts |
| `raw` | `dict` | Full response | Raw API response for debugging |

Additional fields accessible via `runtime.raw`:
- `replicas` — `{"current": int, "requested": int}`
- `domains` — `[{"domain": str, "stage": str}]`
- `sha` — Git commit SHA the Space is running on

### Space Lifecycle Stages

| Stage | Terminal? | Meaning |
|-------|-----------|---------|
| `BUILDING` | No | Container image is building |
| `RUNNING_BUILDING` | No | Container is being deployed after build |
| `APP_STARTING` | No | Application process is starting |
| `RUNNING_APP_STARTING` | No | Application process is starting (post-build) |
| `RUNNING` | Yes | Space is live and accepting traffic |
| `PAUSED` | Yes | Space is paused by owner, not billed |
| `SLEEPING` | Yes | Space went to sleep due to inactivity |
| `BUILD_ERROR` | Yes | Build failed — check build logs |
| `STOPPED` | Yes | Space has been stopped |

### wait_for_space — Wait for a Terminal Stage

```python
runtime = api.wait_for_space(
    repo_id="username/my-space",
    timeout=300,       # seconds, None = indefinite
    poll_interval=1.0, # check every 1s
)
# runtime.stage will be 'RUNNING', 'BUILD_ERROR', 'PAUSED', etc.
```

Returns the final `SpaceRuntime` in all cases. Check `.stage` to determine outcome.

**Intermediate stages** (not terminal, triggers polling): `BUILDING`, `RUNNING_BUILDING`, `APP_STARTING`, `RUNNING_APP_STARTING`

**Terminal stages** (polling stops): `RUNNING`, `BUILD_ERROR`, `PAUSED`, `SLEEPING`, `STOPPED` (plus any stage not in the intermediate list)

---

## Building & Deployment Workflow

### Fetch Build Logs

```python
# Run logs (stdout/stderr of running app)
for line in api.fetch_space_logs("user/my-space", build=False, follow=False):
    print(line)

# Build logs (container build phase — use for BUILD_ERROR)
for line in api.fetch_space_logs("user/my-space", build=True, follow=False):
    print(line)
```

Parameters:
- **`build`** (`bool`, default `False`): `True` = container build logs; `False` = runtime logs
- **`follow`** (`bool`, default `False`): `True` = SSE streaming (blocking, real-time); `False` = buffered snapshot (non-blocking, like `docker logs`)

When `follow=True`, connects to an SSE (Server-Sent Events) endpoint and blocks until the server closes the stream or `KeyboardInterrupt` is raised.

### Restart a Space

```python
# Normal restart (preserves cache)
runtime = api.restart_space("user/my-space")

# Factory reboot (rebuilds from scratch, no caching)
runtime = api.restart_space("user/my-space", factory_reboot=True)
```

Restart is the only way to bring a PAUSED Space back online. The owner must authenticate. Returns the new `SpaceRuntime`.

### Pause a Space

```python
runtime = api.pause_space("user/my-space")
# runtime.stage == 'PAUSED'
```

Paused Spaces stop executing completely and are not billed. Only the Space owner can pause. Use `restart_space` to resume.

### Enable/Disable Dev Mode

```python
# Enable (PRO/Team plan required)
runtime = api.enable_space_dev_mode("user/my-space")
# runtime.stage == 'RUNNING', runtime.dev_mode == True

# Disable
runtime = api.disable_space_dev_mode("user/my-space")
```

Dev Mode keeps the container alive while you restart the app, speeding up iteration. Available on PRO and Team/Enterprise plans.

### Set Custom Sleep Time

```python
# Set 30 minutes of inactivity before sleep
runtime = api.set_space_sleep_time("user/my-space", sleep_time=1800)

# Disable sleep (-1 means never sleep, upgraded hardware only)
runtime = api.set_space_sleep_time("user/my-space", sleep_time=-1)
```

Only works on upgraded (paid) hardware. Free Spaces have a fixed 48h sleep timeout.

---

## Hardware Management

### List Available Hardware

```python
from huggingface_hub import list_spaces_hardware

hardware_list = list_spaces_hardware()
for hw in hardware_list:
    print(f"{hw.name}: {hw.pretty_name} — {hw.cpu}, {hw.ram}, {hw.accelerator}")
```

`JobHardwareInfo` fields:

| Field | Type | Example |
|-------|------|---------|
| `name` | `str` | `"t4-medium"` |
| `pretty_name` | `str` | `"T4 Medium"` |
| `cpu` | `str` | `"8 vCPU"` |
| `ram` | `str` | `"32 GB"` |
| `ephemeral_storage` | `str` | `"210 GB"` |
| `accelerator` | `JobAccelerator\|None` | `{"name": "NVIDIA T4", "memory": "16 GB"}` |
| `unit_cost_micro_usd` | `int` | `299` (micro-dollars per unit) |
| `unit_cost_usd` | `float` | `0.299` (USD per hour per replica) |
| `unit_label` | `str` | `"per hour per replica"` |

### Request Hardware Upgrade

```python
from huggingface_hub import SpaceHardware

# Request T4 Medium with 30 min sleep
runtime = api.request_space_hardware(
    "user/my-space",
    hardware=SpaceHardware.T4_MEDIUM,  # or "t4-medium"
    sleep_time=1800,
)
```

Common `SpaceHardware` values: `CPU_BASIC`, `CPU_UPGRADE`, `T4_SMALL`, `T4_MEDIUM`, `A10G_SMALL`, `A10G_LARGE`, `A100`, `H100`.

**Zero-cost constraint:** Free Spaces (`CPU_BASIC`) sleep after 48h of inactivity but cost $0. Upgraded hardware is billed hourly. Always check `unit_cost_usd` from `list_spaces_hardware()` before requesting.

---

## Secrets & Variables

### Manage Secrets

```python
# Add or update a secret
api.add_space_secret("user/my-space", key="MY_API_KEY", value="abc123")
api.add_space_secret("user/my-space", key="MY_API_KEY", value="abc123", description="API key for service X")

# Delete a secret
api.delete_space_secret("user/my-space", key="MY_API_KEY")

# List all secrets (values are redacted in response)
secrets = api.get_space_secrets("user/my-space")
```

Secrets are encrypted and not visible in Space settings UI after creation (only the key name is shown). They're injected as environment variables at runtime.

### Manage Variables (Environment Variables)

```python
# Add or update a variable
api.add_space_variable("user/my-space", key="DEBUG", value="true")

# Delete a variable
api.delete_space_variable("user/my-space", key="DEBUG")

# List all variables
variables = api.get_space_variables("user/my-space")
# Returns dict[str, SpaceVariable]: {"MY_VAR": SpaceVariable(key="MY_VAR", value="some_value")}
```

Unlike secrets, variable values are visible in the UI and API responses.

---

## Storage Management

### Request Persistent Storage

```python
from huggingface_hub import SpaceStorage

# Request small persistent storage (10 GB)
# Exposed as /data in the Space container
api.request_space_storage("user/my-space", storage=SpaceStorage.SMALL)
```

`SpaceStorage` values: `SMALL` (10 GB), `MEDIUM` (50 GB), `LARGE` (500 GB).

### Delete Persistent Storage

```python
api.delete_space_storage("user/my-space")
```

Deletes the persistent storage volume and all its contents. Irreversible.

### Manage Volumes

```python
# Set volumes
api.set_space_volumes("user/my-space", volumes=["volume-name"])

# Delete all volumes
api.delete_space_volumes("user/my-space")
```

Volumes are shared persistent storage across Spaces in an organization.

---

## Duplicating Spaces

```python
# Simple duplicate
url = api.duplicate_space("pharma/CLIP-Interrogator")
# Returns RepoUrl(url="https://huggingface.co/spaces/yourname/clip-interrogator")

# Duplicate with hardware and secrets
url = api.duplicate_space(
    "pharma/CLIP-Interrogator",
    to_id="my-copy",
    private=True,
    hardware=SpaceHardware.CPU_UPGRADE,
    storage=SpaceStorage.SMALL,
    sleep_time=1800,
    secrets=[{"key": "API_KEY", "value": "abc123", "description": "My key"}],
)
```

> Note: `duplicate_space` is deprecated in favor of `duplicate_repo` (available in newer `huggingface_hub` versions).

---

## Space Templates (New in v1.23.0 — July 2026)

Space Templates let you seed a new Space from one of **28 official templates** instead of starting empty. The SDK, visibility, and boilerplate are handled automatically.

### Listing Templates

```python
from huggingface_hub import list_space_templates

templates = list_space_templates()  # -> list[SpaceTemplate]
for t in templates:
    print(f"{t.name}: {t.repo_id} (SDK: {t.sdk})")
```

### Creating a Space from a Template

```python
# Using short name (case-insensitive, human-friendly)
api.create_repo(
    repo_id="my-jupyter",
    repo_type="space",
    space_template="JupyterLab",   # auto-private, Docker SDK
)

# Using full repo_id
api.create_repo(
    repo_id="my-dashboard",
    repo_type="space",
    space_template="streamlit/streamlit-template-space",
)
```

### Template Resolution Rules

| Rule | Detail |
|------|--------|
| **Input format** | Accepts `repo_id` (full) or `name` (short, case-insensitive) |
| **SDK auto-set** | `space_sdk` is set from template if omitted; raises `ValueError` on mismatch |
| **Auto-visibility** | If `preferred_private=True` and no visibility set → private |
| **API payload** | Sends `template` field with the resolved `repo_id` |

### All 28 Templates by SDK

| SDK | Count | Templates |
|-----|:-----:|-----------|
| **Docker** | 17 | Streamlit, JupyterLab (private), Argilla, Livebook, LabelStudio, AimStack, Shiny (R), Shiny (Python), ZenML, ChatUI, Panel, Giskard, Quarto, marimo, Evidence, Langfuse, Plotly |
| **Static** | 6 | Paper Project, Gradio-Lite, Transformers.js, React, Svelte, Vue |
| **Gradio** | 5 | chatbot, text-to-image, leaderboard, Trackio, Workflow |

### CLI Usage

```bash
# List templates
hf spaces templates

# Create from template (use repo_id or short name)
hf repos create my-lab --type space --template SpacesExamples/jupyterlab
hf repos create my-lab --type space --template JupyterLab
```

---

## Underlying REST Endpoints

All `huggingface_hub` methods call these REST endpoints on the Hub:

| Method | HTTP | Endpoint |
|--------|------|----------|
| `space_info` | GET | `/api/spaces/{repo_id}` |
| `get_space_runtime` | GET | `/api/spaces/{repo_id}/runtime` |
| `fetch_space_logs` | SSE/GET | `/api/spaces/{repo_id}/logs?build={bool}` |
| `restart_space` | POST | `/api/spaces/{repo_id}/restart` |
| `pause_space` | POST | `/api/spaces/{repo_id}/pause` |
| `enable_space_dev_mode` | POST | `/api/spaces/{repo_id}/dev-mode` |
| `disable_space_dev_mode` | DELETE | `/api/spaces/{repo_id}/dev-mode` |
| `request_space_hardware` | POST | `/api/spaces/{repo_id}/hardware` |
| `set_space_sleep_time` | POST | `/api/spaces/{repo_id}/sleep-time` |
| `request_space_storage` | POST | `/api/spaces/{repo_id}/storage` |
| `delete_space_storage` | DELETE | `/api/spaces/{repo_id}/storage` |
| `set_space_volumes` | POST | `/api/spaces/{repo_id}/volumes` |
| `delete_space_volumes` | DELETE | `/api/spaces/{repo_id}/volumes` |
| `add_space_secret` | POST | `/api/spaces/{repo_id}/secrets` |
| `delete_space_secret` | DELETE | `/api/spaces/{repo_id}/secrets` |
| `get_space_secrets` | GET | `/api/spaces/{repo_id}/secrets` |
| `add_space_variable` | POST | `/api/spaces/{repo_id}/variables` |
| `delete_space_variable` | DELETE | `/api/spaces/{repo_id}/variables` |
| `get_space_variables` | GET | `/api/spaces/{repo_id}/variables` |
| `list_spaces_hardware` | GET | `/api/spaces/hardware` |
| `list_space_templates` | GET | `/api/spaces/templates` |
| `duplicate_space`/`duplicate_repo` | POST | `/api/spaces/{repo_id}/duplicate` |

---

## Key Facts

- **Authentication required**: All management operations require a valid HF token (write scope for mutations)
- **Ownership enforced**: Only the Space owner can pause, restart, change hardware, or manage secrets
- **Zero-cost memory**: Free Spaces (`cpu-basic`) are $0 but sleep after 48h inactivity; they wake on new traffic
- **Sleep time configurable**: Only on upgraded hardware; `-1` means never sleep (but continues billing)
- **Logs endpoint**: SSE-based for real-time streaming; buffered snapshot mode for non-blocking reads
- **Secrets vs Variables**: Secrets are encrypted and hidden; variables are visible in plaintext
- **wait_for_space** is idempotent: safe to call on already-terminal stages (returns immediately)
