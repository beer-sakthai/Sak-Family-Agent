# HF Learnings Log — hf-spaces-dependencies-and-sdks

## 2026-07-25: Hugging Face Spaces — Dependencies, SDKs, & Configuration Complete Reference

### Summary
Comprehensive deep-dive into Hugging Face Spaces dependency management, SDK selection, hardware configuration, build optimization, and environment management. Researched official HF docs (spaces-overview, spaces-dependencies, spaces-sdks-docker, spaces-sdks-gradio, spaces-sdks-static, spaces-sdks-streamlit, spaces-config-reference, spaces-gpus, spaces-zerogpu, spaces-storage, spaces-settings). Covers all SDK types, dependency files, hardware tiers, ZeroGPU free tier, storage options, and optimization strategies for zero-cost deployments.

### Key Findings

#### 1. Spaces SDK Options — Four Flavours

| SDK | Use Case | Compute Required | Cost |
|-----|----------|-----------------|------|
| **Gradio** | ML demos with UI components (images, audio, video, text, plots) | CPU basic or GPU | Free tier: 2 ZeroGPU Spaces for personal accounts; otherwise PRO+ |
| **Docker** | Custom containers (FastAPI, Go, Node, Phoenix, etc.) | CPU basic or GPU | Same as Gradio — requires paid plan to create |
| **Streamlit** | Data app dashboards, simpler ML demos | CPU basic or GPU | Same as Gradio |
| **Static** | HTML/CSS/JS sites, SPAs, static content | None (CDN-served) | **Completely free** — no compute needed |

**Key constraint**: Free personal accounts can host up to **2 Gradio/Docker Spaces running on ZeroGPU**. Static Spaces are always free.

**Python version** defaults to **3.10**. Override with `python_version: 3.x` or `python_version: 3.x.x` in README YAML.

---

#### 2. Dependency Management by SDK

##### Gradio & Streamlit Spaces

**Default pre-installed packages** (no requirement needed):
- `huggingface_hub` — Hub API, Inference Providers access
- `requests` — third-party API calls
- `datasets` — fetch/display datasets from Hub
- `gradio` (for Gradio SDK) — specific version via `sdk_version` in YAML
- Common Debian packages: `ffmpeg`, `cmake`, `libsm6`, and others

**Adding Python packages** — create `requirements.txt` at repo root:
```
transformers
torch
accelerate
sentencepiece
```

**Pre-install dependencies** — create `pre-requirements.txt` (runs before `requirements.txt`, useful for upgrading pip itself):
```
pip>=24.0
setuptools>=68.0
```

**Adding system packages** — create `packages.txt` at repo root (one package per line, installed via `apt-get install`):
```
libsndfile1
espeak-ng
ffmpeg
git-lfs
```

##### Docker Spaces

Dependencies are managed entirely through the `Dockerfile`. Best practices:

**User setup** (container runs as user ID 1000):
```dockerfile
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app
```

**Installing Python packages**:
```dockerfile
RUN pip install --no-cache-dir --upgrade pip
COPY --chown=user . $HOME/app
RUN pip install --no-cache-dir -r requirements.txt
```

**Buildtime vs Runtime variables**:
- **Buildtime**: Passed as `ARG` / `--build-arg` to Dockerfile. Access with `ARG VAR_NAME`.
- **Runtime**: Injected as environment variables. Access with `os.environ.get("VAR_NAME")`.

**Buildtime secrets** (Docker BuildKit):
```dockerfile
RUN --mount=type=secret,id=SECRET_NAME,mode=0444,required=true \
    git init && git remote add origin $(cat /run/secrets/SECRET_NAME)
```

**Runtime secrets**: Available as environment variables (same as Gradio).

**Port configuration**: Default is `7860`, override with `app_port: PORT` in README YAML. Internal multi-port works (e.g., Elasticsearch on 9200 internally), expose via reverse proxy.

##### Static Spaces

Dependencies managed via `app_build_command` (e.g., `npm run build`) and `app_file: dist/index.html`. Build runs in a Job, output stored in `refs/convert/build`.

---

#### 3. Hardware Tiers — Complete Reference

| Hardware | vCPU | RAM | GPU Memory | Hourly Price |
|----------|------|-----|------------|-------------|
| **CPU Basic** (default) | 2 | 16 GB | — | **FREE** |
| CPU Upgrade | 8 | 32 GB | — | $0.03 |
| Nvidia T4-small | 4 | 15 GB | 16 GB | $0.40 |
| Nvidia T4-medium | 8 | 30 GB | 16 GB | $0.60 |
| 1x Nvidia L4 | 8 | 30 GB | 24 GB | $0.80 |
| 4x Nvidia L4 | 48 | 186 GB | 96 GB | $3.80 |
| 1x Nvidia L40S | 8 | 62 GB | 48 GB | $1.80 |
| 4x Nvidia L40S | 48 | 382 GB | 192 GB | $8.30 |
| 8x Nvidia L40S | 192 | 1534 GB | 384 GB | $23.50 |
| Nvidia A10G-small | 4 | 15 GB | 24 GB | $1.00 |
| Nvidia A10G-large | 12 | 46 GB | 24 GB | $1.50 |
| 2x A10G-large | 24 | 92 GB | 48 GB | $3.00 |
| 4x A10G-large | 48 | 184 GB | 96 GB | $5.00 |
| Nvidia A100-large | 12 | 142 GB | 80 GB | $2.50 |
| 4x Nvidia A100 | 48 | 568 GB | 320 GB | $10.00 |
| 8x Nvidia A100 | 96 | 1136 GB | 640 GB | $20.00 |

**Default disk**: 50 GB ephemeral (lost on restart). Persist via Storage Buckets.

---

#### 4. ZeroGPU — Free GPU for Personal Accounts

**What it is**: Shared infrastructure dynamically allocating NVIDIA RTX Pro 6000 Blackwell GPUs. Free GPU time for eligible accounts.

**GPU sizes**:
| Size | Hardware | VRAM | Quota Cost |
|------|----------|------|-----------|
| `large` (default) | Half RTX Pro 6000 Blackwell | 48 GB | 1× |
| `xlarge` | Full RTX Pro 6000 Blackwell | 96 GB | 2× |

**Daily quotas**:
| Account Type | Daily GPU Quota | Queue Priority |
|-------------|----------------|---------------|
| Unauthenticated | 2 minutes | Low |
| Free account (good standing) | 5 minutes | Medium |
| PRO | 40 minutes (extensible) | Highest |
| Team member | 40 minutes (extensible) | Highest |
| Enterprise member | 60 minutes (extensible) | Highest |

**Free personal account requirements for hosting**:
- Verified email
- Account older than 30 days
- Maximum **2 ZeroGPU Spaces**
- **Gradio SDK only** (no Docker/Streamlit ZeroGPU support yet)

**Usage in code**:
```python
import spaces

@spaces.GPU(duration=120)  # default 60s
def predict(image):
    return model(image)
```

**Limitations**:
- `torch.compile` not supported (use AOT compilation instead, torch 2.8+)
- Gradio 4+ only
- PyTorch 2.8.0+
- Python 3.10.13 or 3.12.12
- `xlarge` has higher queue probability and longer wait times

**Extending quota** (PRO/Team/Enterprise): $1 per 10 GPU minutes via pre-paid credits.

---

#### 5. README YAML Configuration — Complete Reference

```yaml
---
title: My Space                 # Display title
emoji: 🤗                       # Emoji for thumbnail
colorFrom: blue                 # Gradient start: red/yellow/green/blue/indigo/purple/pink/gray
colorTo: purple                 # Gradient end
sdk: gradio                     # gradio | docker | streamlit | static
python_version: 3.10            # Any 3.x or 3.x.x; default 3.10
sdk_version: 5.0                # Gradio version (all versions supported)
app_file: app.py                # Main application file
app_port: 7860                  # Port (Docker only, default 7860)
app_build_command: npm run build  # Build command (Static only)
base_path: /app                 # Initial URL path (non-static)
fullWidth: true                 # Full-width iframe (default: true)
header: mini                    # mini | default
short_description: "My demo"    # Short description for thumbnail
models:                         # Linked HF model IDs
  - openai-community/gpt2
datasets:                       # Linked HF dataset IDs
  - mozilla-foundation/common_voice_13_0
tags: [demo, nlp]               # Descriptive tags
pinned: true                    # Pin to profile top
thumbnail: https://example.com/thumb.png  # Custom social thumbnail

# OAuth settings
hf_oauth: true
hf_oauth_scopes: [openid, profile]
hf_oauth_expiration_minutes: 480  # Default 8h, max 43200 (30d)
hf_oauth_authorized_org: my-org   # Restrict OAuth to org members

# Embedding & security
disable_embedding: false         # Prevent iframe embedding
custom_headers:                  # COEP/COOP/CORP headers (lowercase only)
  cross-origin-embedder-policy: require-corp
  cross-origin-opener-policy: same-origin

# Performance
startup_duration_timeout: 30m    # Max startup time before unhealthy (default 30m)
suggested_hardware: t4-small     # Suggested hardware for duplicators
preload_from_hub:                # Preload models/datasets at build time
  - warp-ai/wuerstchen-prior text_encoder/model.safetensors
  - openai-community/gpt2
---
```

---

#### 6. Environment Variables

**Built-in variables** (automatically available):
| Variable | Example | Description |
|----------|---------|-------------|
| `ACCELERATOR` | `t4-medium` | GPU type, or `none` for CPU |
| `CPU_CORES` | `4` | CPU core count |
| `MEMORY` | `15Gi` | RAM allocation |
| `SPACE_AUTHOR_NAME` | `osanseviero` | Space owner username |
| `SPACE_REPO_NAME` | `i-like-flan` | Space repo name |
| `SPACE_TITLE` | `I Like Flan` | Title from README YAML |
| `SPACE_ID` | `osanseviero/i-like-flan` | Full Space ID |
| `SPACE_HOST` | `osanseviero-i-like-flan.hf.space` | Space subdomain |
| `SPACE_CREATOR_USER_ID` | `6032802e...` | User ID of original creator |

**OAuth variables** (when enabled):
| Variable | Description |
|----------|-------------|
| `OAUTH_CLIENT_ID` | OAuth app client ID (public) |
| `OAUTH_CLIENT_SECRET` | OAuth app client secret |
| `OAUTH_SCOPES` | Always `"openid profile"` |
| `OPENID_PROVIDER_URL` | OpenID provider URL |

**Custom variables & secrets**: Configured in Space Settings → Variables (public, viewable) / Secrets (private, hidden after set).

**Access in Static Spaces**: Via `window.huggingface.variables` (client-side JS).

**Access in other SDKs**: Via `os.environ.get("VAR_NAME")`.

---

#### 7. Storage & Persistence

| Type | Capacity | Persistence | Cost |
|------|----------|-------------|------|
| **Ephemeral disk** | 50 GB | Lost on restart | Free |
| **Storage Bucket** | Small/Medium/Large | Survives restarts | Free tier available (storage buckets docs) |

**Mounting models/datasets as volumes**: Use `huggingface_hub` Python API to attach repos as read-only volumes. Can mount private repos (masked in UI for unauthorized users).

**Persistent storage for Docker Spaces**: `/data` volume available at runtime only (not during build). Use Storage Buckets for persistence across restarts.

---

#### 8. Networking

- Ports open: **80 (HTTP)**, **443 (HTTPS)**, **8080** (additional)
- All other ports blocked
- For multi-service Docker Spaces, use reverse proxy (Nginx) on port 7860

---

#### 9. Lifecycle Management

- **Free hardware**: Space sleeps after inactivity (auto-pause)
- **Paid hardware**: Space runs indefinitely
- **Manual pause**: From Settings tab (billing stops for paused time)
- **Dev Mode**: For debugging — see Spaces Dev Mode docs
- **Build triggers**: Every push to the repo triggers rebuild + restart

---

#### 10. Optimization Strategies for Zero-Cost

1. **Choose Static Spaces** when possible — zero compute cost, CDN-served
2. **ZeroGPU for ML demos** — 5 min/day free GPU for personal accounts in good standing (verified email, >30 days old)
3. **Use `preload_from_hub`** to download models at build time (reduces cold start latency, avoids runtime download delays)
4. **Pin Gradio version** with `sdk_version` to avoid unexpected breaking changes on rebuild
5. **Split dependencies** — `pre-requirements.txt` for pip upgrades, `requirements.txt` for app packages
6. **Use `huggingface_hub` inference** instead of loading models locally when possible — saves RAM and compute
7. **Keep Docker images lean** — multi-stage builds, `--no-cache-dir`, avoid `chown` when possible (prefer `COPY --chown=user`)
8. **Mount models as volumes** instead of downloading at every cold start
9. **Set `suggested_hardware`** for Spaces meant to be duplicated — guides users to correct hardware
10. **Set `startup_duration_timeout`** to appropriate value (default 30m is generous) to fail fast on misconfiguration

### Impact & Use Cases
- **Zero-cost deployment**: Choose the right SDK + hardware combination to minimize costs (Static = free, ZeroGPU = free GPU with daily quota)
- **Build optimization**: Proper dependency management reduces rebuild time and failures
- **Docker Space creation**: Complete reference for Dockerfile setup, user permissions, secrets, and buildtime/runtime variable management
- **Space duplication**: YAML config with `suggested_hardware` and `preload_from_hub` ensures duplicated Spaces work correctly
- **Hardware selection**: Choose appropriate GPU tier based on model size and budget

### Skill Created
`hf-spaces-dependencies-and-sdks/` — new skill with SKILL.md (author: SakThai, license: MIT) and this learnings reference. Covers the complete Spaces dependency, SDK, hardware, and configuration ecosystem.

### Sources
- HF Docs: https://huggingface.co/docs/hub/en/spaces-overview
- HF Docs: https://huggingface.co/docs/hub/en/spaces-dependencies
- HF Docs: https://huggingface.co/docs/hub/en/spaces-sdks-gradio
- HF Docs: https://huggingface.co/docs/hub/en/spaces-sdks-docker
- HF Docs: https://huggingface.co/docs/hub/en/spaces-sdks-static
- HF Docs: https://huggingface.co/docs/hub/en/spaces-sdks-streamlit
- HF Docs: https://huggingface.co/docs/hub/en/spaces-config-reference
- HF Docs: https://huggingface.co/docs/hub/en/spaces-gpus
- HF Docs: https://huggingface.co/docs/hub/en/spaces-zerogpu
- HF Docs: https://huggingface.co/docs/hub/en/spaces-storage
- HF Docs: https://huggingface.co/docs/hub/en/spaces-settings

---

## 2026-07-25: hf-hub-spaces-python-sdk — Complete Python SDK Reference (Deep Dive #344)

### Summary
Comprehensive deep-dive into the Hugging Face Spaces Python SDK — 25+ methods on `HfApi` for managing Spaces programmatically. Covers every method with its signature, return type, data model, and practical usage. Source-verified against huggingface_hub v1.24.0 source code.

### 1. Space Runtime & Status Methods

#### get_space_runtime() — Get Current Runtime State
```python
def get_space_runtime(
    repo_id: str,
    *,
    token: bool | str | None = None,
) -> SpaceRuntime
```
Returns `SpaceRuntime` with:
- `stage: SpaceStage` — current lifecycle stage (see enum below)
- `hardware: SpaceHardware | None` — current hardware flavor
- `requested_hardware: SpaceHardware | None` — pending hardware request
- `sleep_time: int | None` — idle timeout in seconds (paid hardware)
- `storage: SpaceStorage | None` — persistent storage tier
- `dev_mode: bool` — whether dev mode is active
- `hot_reloading: SpaceHotReloading | None` — hot reloading config
- `volumes: list[Volume] | None` — mounted volumes
- `raw: dict` — raw API response

**SpaceStage enum** (all possible values):
| Stage | Meaning |
|-------|---------|
| `NO_APP_FILE` | Missing app file — space not configured |
| `CONFIG_ERROR` | YAML/sdk misconfiguration |
| `BUILDING` | Building container (includes `preload_from_hub`) |
| `BUILD_ERROR` | Build failed (check logs) |
| `RUNNING` | Fully operational |
| `RUNNING_BUILDING` | Running while rebuilding (new push) |
| `RUNTIME_ERROR` | Runtime crash |
| `DELETING` | Being deleted |
| `STOPPED` | Manually stopped |
| `PAUSED` | Auto-paused (free tier inactivity) |
| `APP_STARTING` | Application starting after build |
| `RUNNING_APP_STARTING` | Transitional — old version runs while new starts |

#### wait_for_space() — Block Until Terminal State
```python
def wait_for_space(
    repo_id: str,
    *,
    timeout: float | None = None,
    poll_interval: float = 1.0,
    token: bool | str | None = None,
) -> SpaceRuntime
```
Polls every `poll_interval` seconds until the space reaches a terminal stage (RUNNING, BUILD_ERROR, RUNTIME_ERROR, STOPPED, PAUSED, NO_APP_FILE, CONFIG_ERROR, or DELETING). Raises `TimeoutError` if `timeout` seconds pass.

**Zero-cost tip**: Use `wait_for_space(repo_id, timeout=600)` after a deploy to validate the Space started properly.

---

### 2. Hardware & Storage Management

#### request_space_hardware() — Change Hardware Flavor
```python
def request_space_hardware(
    repo_id: str,
    hardware: SpaceHardware,
    *,
    token: bool | str | None = None,
    sleep_time: int | None = None,
) -> SpaceRuntime
```
Sets hardware flavor and optional sleep timeout (seconds, for paid hardware). This triggers a restart. Returns updated `SpaceRuntime`.

**SpaceHardware enum** (complete list):
| Hardware | Identifier | Best For |
|----------|-----------|----------|
| `CPU_BASIC` | `cpu-basic` | Static sites, light demos, APIs |
| `CPU_UPGRADE` | `cpu-upgrade` | Heavier CPU workloads |
| `ZERO_A10G` | `zero-a10g` | Free GPU tier (ZeroGPU, Gradio only) |
| `T4_SMALL` | `t4-small` | Small models (<3B params) |
| `T4_MEDIUM` | `t4-medium` | Medium models (<7B params) |
| `L4X1` | `l4x1` | Mid-range 24 GB VRAM |
| `L4X4` | `l4x4` | Large batch training/serving |
| `L40SX1` | `l40sx1` | 48 GB VRAM — large models |
| `L40SX4` | `l40sx4` | Multi-GPU large models |
| `L40SX8` | `l40sx8` | Massive multi-GPU |
| `A10G_SMALL` | `a10g-small` | Small GPU (24 GB, deprecated path) |
| `A10G_LARGE` | `a10g-large` | Medium GPU (24 GB) |
| `A10G_LARGEX2` | `a10g-largex2` | 2× A10G (48 GB) |
| `A10G_LARGEX4` | `a10g-largex4` | 4× A10G |
| `A100_LARGE` | `a100-large` | 80 GB A100 |
| `A100X4` | `a100x4` | 4× A100 (320 GB) |
| `A100X8` | `a100x8` | 8× A100 (640 GB) |

**Zero-cost note**: `ZERO_A10G` is the only free GPU option. All other GPUs require PRO subscription.

#### request_space_storage() — Add Persistent Storage
```python
def request_space_storage(
    repo_id: str,
    storage: SpaceStorage,
    *,
    token: bool | str | None = None,
) -> SpaceRuntime
```
**SpaceStorage enum**:
| Tier | Capacity | Free Tier? |
|------|----------|-----------|
| `SMALL` | small | See storage buckets docs |
| `MEDIUM` | medium | Paid |
| `LARGE` | large | Paid |

#### delete_space_storage() — Remove Persistent Storage
```python
def delete_space_storage(
    repo_id: str,
    *,
    token: bool | str | None = None,
) -> SpaceRuntime
```

#### set_space_sleep_time() — Configure Idle Timeout
```python
def set_space_sleep_time(
    repo_id: str,
    sleep_time: int,
    *,
    token: bool | str | None = None,
) -> SpaceRuntime
```
Sets idle timeout in seconds for paid hardware Spaces. The Space pauses after `sleep_time` seconds of inactivity. Only applies to upgraded hardware.

#### list_spaces_hardware() — Get Available Hardware
```python
def list_spaces_hardware(
    token: bool | str | None = None,
) -> list[JobHardwareInfo]
```

---

### 3. Lifecycle Management

#### pause_space() — Pause a Space
```python
def pause_space(
    repo_id: str,
    *,
    token: bool | str | None = None,
) -> SpaceRuntime
```
Pauses the Space. For paid hardware, this stops billing while paused. For free Spaces, this is equivalent to stopping.

#### restart_space() — Restart a Space
```python
def restart_space(
    repo_id: str,
    *,
    token: bool | str | None = None,
    factory_reboot: bool = False,
) -> SpaceRuntime
```
`factory_reboot=True` forces a cold restart (re-downloads all dependencies, clears cached state). Use when Space is in a broken state that a normal restart doesn't fix.

#### enable_space_dev_mode() / disable_space_dev_mode()
```python
def enable_space_dev_mode(
    repo_id: str,
    *,
    token: bool | str | None = None,
) -> SpaceRuntime

def disable_space_dev_mode(
    repo_id: str,
    *,
    token: bool | str | None = None,
) -> SpaceRuntime
```
Dev Mode provides interactive terminal access inside the running Space container for debugging. Auto-disables after a timeout.

#### set_space_volumes() / delete_space_volumes()
```python
def set_space_volumes(
    repo_id: str,
    volumes: list[Volume],
    *,
    token: bool | str | None = None,
) -> None

def delete_space_volumes(
    repo_id: str,
    *,
    token: bool | str | None = None,
) -> None
```
Mount/unmount hub model/dataset repos as read-only volumes inside the Space. `Volume` dataclass:
- `component: str` — named component
- `repo_id: str` — hf repo to mount
- `repo_type: Literal["dataset", "space"] | None`
- `revision: str | None` — specific revision

---

### 4. Secrets & Variables

#### add_space_secret() — Set a Secret
```python
def add_space_secret(
    repo_id: str,
    key: str,
    value: str,
    *,
    description: str | None = None,
    token: bool | str | None = None,
) -> None
```
**Warning**: Secret `value` is sent to the API. Once set, the value is never returned in responses. Returns `None` (no value returned — security by design).

#### add_space_variable() — Set a Variable
```python
def add_space_variable(
    repo_id: str,
    key: str,
    value: str,
    *,
    description: str | None = None,
    token: bool | str | None = None,
) -> dict[str, SpaceVariable]
```
Unlike secrets, variables are readable. Returns dict of ALL variables (not just the added one).

#### get_space_secrets() / get_space_variables()
```python
def get_space_secrets(
    repo_id: str,
    *,
    token: bool | str | None = None,
) -> dict[str, SpaceSecret]

def get_space_variables(
    repo_id: str,
    *,
    token: bool | str | None = None,
) -> dict[str, SpaceVariable]
```
**SpaceSecret**: `key: str`, `description: str | None`, `updated_at: datetime | None`
**SpaceVariable**: Same + `value: str` (readable)

**Key difference**: `get_space_secrets()` never returns actual secret values — API returns `{"key": "...", "updatedAt": "..."}` without the value. `get_space_variables()` DOES return values.

#### delete_space_secret() / delete_space_variable()
```python
def delete_space_secret(
    repo_id: str,
    key: str,
    *,
    token: bool | str | None = None,
) -> None

def delete_space_variable(
    repo_id: str,
    key: str,
    *,
    token: bool | str | None = None,
) -> dict[str, SpaceVariable]
```
`delete_space_variable()` returns the remaining variables dict. `delete_space_secret()` returns `None`.

---

### 5. Duplication & Creation

#### duplicate_space() — Full Space Duplication
```python
def duplicate_space(
    from_id: str,
    to_id: str | None = None,
    *,
    private: bool | None = None,
    visibility: RepoVisibility_T | None = None,
    token: bool | str | None = None,
    exist_ok: bool = False,
    hardware: SpaceHardware | None = None,
    storage: SpaceStorage | None = None,
    sleep_time: int | None = None,
    secrets: list[dict[str, str]] | None = None,
    variables: list[dict[str, str]] | None = None,
) -> RepoUrl
```
Most feature-rich duplication method. Can override hardware, storage, sleep time, secrets, and variables at dup time. `secrets=[{"key": "...", "value": "..."}]` injection works at dup time only (secrets once set cannot be read back).

**Zero-cost pattern**: Duplicate a Space with `hardware=SpaceHardware.ZERO_A10G` to get zero-cost GPU from a template.

#### list_space_templates() — Official Templates
```python
def list_space_templates(
    *,
    token: str | bool | None = None,
) -> list[SpaceTemplate]
```
Returns official HF Space templates with their hardware requirements, SDK type, and metadata.

#### create_repo() with space_type — Create New Space
While Spaces are created via `create_repo()` with `repo_type="space"` and a `space_sdk` parameter:
```python
from huggingface_hub import HfApi, SpaceSDK

api = HfApi()
url = api.create_repo(
    repo_id="user/my-demo",
    repo_type="space",
    space_sdk="gradio",      # SpaceSDK.GRADIO (or "docker", "streamlit", "static")
    private=False,
    exist_ok=True,
)
```

---

### 6. Information & Discovery

#### space_info() — Full Space Metadata
```python
def space_info(
    repo_id: str,
    *,
    revision: str | None = None,
    timeout: float | None = None,
    files_metadata: bool = False,
    expand: list[ExpandSpaceProperty_T] | None = None,
    token: bool | str | None = None,
) -> SpaceInfo
```
Returns `SpaceInfo` with comprehensive metadata (24+ fields). The `expand` parameter controls which extended fields to include:

**ExpandSpaceProperty_T** (Literal values):
`'author'`, `'cardData'`, `'createdAt'`, `'datasets'`, `'disabled'`, `'lastModified'`, `'likes'`, `'models'`, `'private'`, `'resourceGroup'`, `'runtime'`, `'sdk'`, `'sha'`, `'siblings'`, `'subdomain'`, `'tags'`, `'trendingScore'`, `'usedStorage'`

**SpaceInfo fields**:
| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Full repo ID (namespace/name) |
| `author` | `str \| None` | Owner username |
| `cardData` | `SpaceCardData \| None` | YAML card metadata |
| `createdAt` | `datetime \| None` | Creation timestamp |
| `datasets` | `list[str] \| None` | Linked dataset IDs |
| `disabled` | `bool \| None` | Is space disabled |
| `gated` | `Literal['auto','manual',False] \| None` | Gated access |
| `host` | `str \| None` | Host domain |
| `lastModified` | `datetime \| None` | Last modified |
| `likes` | `int \| None` | Like count |
| `models` | `list[str] \| None` | Linked model IDs |
| `private` | `bool \| None` | Visibility |
| `resourceGroup` | `dict \| None` | RG info |
| `runtime` | `SpaceRuntime \| None` | Runtime state (includes stage, hardware, sleep) |
| `sdk` | `str \| None` | SDK type (gradio/docker/streamlit/static) |
| `sha` | `str \| None` | Git commit SHA |
| `siblings` | `list[RepoSibling] \| None` | File listing |
| `subdomain` | `str \| None` | Custom subdomain |
| `tags` | `list[str] \| None` | Descriptive tags |
| `trendingScore` | `int \| None` | Trending rank score |
| `usedStorage` | `int \| None` | Storage used in bytes |

#### list_spaces() — Search & Filter Spaces
```python
def list_spaces(
    *,
    filter: str | Iterable[str] | None = None,
    author: str | None = None,
    search: str | None = None,
    datasets: str | Iterable[str] | None = None,
    models: str | Iterable[str] | None = None,
    linked: bool = False,
    sort: SpaceSort | None = None,
    limit: int | None = None,
    expand: list[ExpandSpaceProperty_T] | None = None,
    full: bool | None = None,
    token: bool | str | None = None,
) -> Iterable[SpaceInfo]
```
Filters by author, linked datasets/models, full-text search, and tags. Returns iterator of `SpaceInfo`.

**SpaceSort options** (from `huggingface_hub.constants.SpaceSort`):
- `LIKES` — by like count (most popular)
- `TRENDING` — by trending score (what's hot)
- `DOWNLOADS` — by download count
- `LAST_MODIFIED` — most recently updated

#### search_spaces() — Semantic Search
```python
def search_spaces(
    query: str,
    *,
    filter: str | Iterable[str] | None = None,
    sdk: str | list[str] | None = None,
    include_non_running: bool = False,
    token: bool | str | None = None,
) -> Iterable[SpaceSearchResult]
```
Semantic search across Spaces. Supports filtering by SDK type and running status.

### 7. Logs & Monitoring

#### fetch_space_logs() — Stream Build/Run Logs
```python
def fetch_space_logs(
    repo_id: str,
    *,
    build: bool = False,
    follow: bool = False,
    token: bool | str | None = None,
) -> Iterable[str]
```
Returns an iterable of log lines. `build=True` for build logs (default: run logs). `follow=True` streams live (like `tail -f`). Use in development/debugging to inspect Space behavior.

**Zero-cost pattern**: When a Space fails to start, check `fetch_space_logs(build=True)` first (build errors are faster than runtime errors) — then `fetch_space_logs(build=False)` for runtime issues. Common failure modes:
- Missing packages in `requirements.txt`
- YAML indentation errors
- `CUDA out of memory` (need higher hardware tier)

---

### 8. Practical Automation Patterns

| Task | Method | Notes |
|------|--------|-------|
| **Deploy Space from CI** | `create_repo()` → push files → `wait_for_space()` | Push files via `upload_folder()`, wait for RUNNING |
| **Graceful restart** | `restart_space()` | Existing requests drain; factory_reboot for broken states |
| **Zero-cost GPU dup** | `duplicate_space(hardware=ZERO_A10G)` | Duplicate any Gradio Space to free GPU |
| **Secret injection** | `add_space_secret(key, value)` | Use in CI/CD to set API keys |
| **Bulk variable sync** | `get_space_variables()` → diff → `add_space_variable()` | Sync config across Spaces |
| **Monitor build** | `fetch_space_logs(build=True, follow=True)` | Watch live build output |
| **Scale down** | `pause_space()` | Stop billing on idle |
| **Dev debug** | `enable_space_dev_mode()` → SSH-like debug → `disable_space_dev_mode()` | Temporary terminal access |
| **Template discovery** | `list_space_templates()` | Find official starting points |
| **Usage audit** | `space_info(expand=['runtime', 'usedStorage'])` | Check what hardware/storage used |

---

### 9. Zero-Cost Considerations

- **Creating Spaces is free** — API calls don't cost anything
- **ZeroGPU** (`ZERO_A10G`) is the only free GPU; free accounts get max 2 ZeroGPU Spaces and 5 min/day GPU quota
- **Hardware changes trigger restarts** — each restart incurs build time (build time is not billed for free tier, but takes time)
- **Secrets API is free** — manage secrets programmatically without manual UI steps
- **Storage**: Delete unused persistent storage with `delete_space_storage()` to avoid charges
- **Volumes**: Mount as read-only to avoid accidental writes

### Sources
- Python SDK source: `huggingface_hub.hf_api.HfApi` (v1.24.0), verified via inspect
- Data classes: `huggingface_hub._space_api` module
- SpaceSort: `huggingface_hub.constants.SpaceSort` (v1.24.0)
- Hardware enum: `huggingface_hub.SpaceHardware` — enumerates 17 options
