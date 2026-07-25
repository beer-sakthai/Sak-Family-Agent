# HF Learning: HF Hub Spaces Build, Runtime & Management API — Deep Dive

**Topic:** hf-hub-spaces-build-runtime-api-deep-dive  
**Learned:** 2026-07-25  
**Author:** SakThai  
**License:** MIT  
**Source:** huggingface_hub source code (`_space_api.py`, `hf_api.py`) + live API probing + HF Spaces docs (spaces-gpus, spaces-overview, spaces-settings)

## New Discoveries Beyond v1

This deep dive builds on the initial `hf-hub-spaces-build-runtime-api` entry, covering critical undocumented or recently added features discovered through source code analysis and official docs inspection.

---

### 1. SpaceStage Enum — Full Stage Surface

The `SpaceStage` enum (from `_space_api.py`) exposes **11 stages**, several not covered in v1:

| Stage | Terminal? | Notes |
|-------|-----------|-------|
| `NO_APP_FILE` | Yes | Repo exists but no app file detected |
| `CONFIG_ERROR` | Yes | YAML/configuration broken |
| `BUILDING` | No | Container image is building |
| `BUILD_ERROR` | Yes | Build failed |
| `RUNNING` | Yes | Live and accepting traffic |
| `RUNNING_BUILDING` | No | Deploying after build |
| `RUNTIME_ERROR` | Yes | App crashed at runtime |
| `DELETING` | Yes | Space is being deleted |
| `STOPPED` | Yes | Stopped (sleep/idle) |
| `PAUSED` | Yes | Owner-paused, not billed |
| `APP_STARTING` | No | App process starting |
| `RUNNING_APP_STARTING` | No | App starting after build |

The module also exports these tuples for easy stage classification:

```python
from huggingface_hub._space_api import INTERMEDIATE_SPACE_STAGES, TERMINAL_SPACE_STAGES

# INTERMEDIATE_SPACE_STAGES = (BUILDING, RUNNING_BUILDING, APP_STARTING, RUNNING_APP_STARTING)
# TERMINAL_SPACE_STAGES = (RUNNING, BUILD_ERROR, RUNTIME_ERROR, CONFIG_ERROR, NO_APP_FILE, STOPPED, PAUSED, DELETING)
```

`wait_for_space` uses `INTERMEDIATE_SPACE_STAGES` to decide when to keep polling.

---

### 2. Replicas API (Horizontal Scaling)

**Not covered in v1.** Spaces on upgraded (paid) hardware can scale horizontally via the replicas endpoint:

```
POST https://huggingface.co/api/spaces/{namespace}/{repo}/replicas
Content-Type: application/json

{ "replicas": 2 }
```

- Only available on upgraded (paid) hardware
- Each replica is billed independently
- No dedicated `huggingface_hub` method yet — call via raw `HfApi.post()` or `requests`
- `SpaceRuntime.raw` exposes `replicas: {"current": int, "requested": int}`

---

### 3. Logs Endpoint: `tail` Parameter + Path Structure

The logs endpoint uses a **path-based** structure (not query param for build/run):

```
# Build logs (container build phase):
GET /api/spaces/{namespace}/{repo}/logs/build?tail=100

# Run logs (runtime stdout/stderr):
GET /api/spaces/{namespace}/{repo}/logs/run?tail=100
```

The `tail` parameter limits response to last N lines — critical for debugging without pulling the entire log buffer. In `huggingface_hub`, `fetch_space_logs(repo_id, build=True/False)` handles this internally.

---

### 4. search_spaces — Semantic Search API

New method not covered in v1. Uses embedding-based semantic search for multi-word queries and full-text search for single-word queries:

```python
results = api.search_spaces(
    query="generate image",
    filter="computer-vision",     # tag filter
    sdk="gradio",                  # filter by SDK
    include_non_running=False,     # exclude non-running Spaces
)
```

Returns `Iterable[SpaceSearchResult]` with fields:
- `id` (str) — `"username/repo-name"`
- `author`, `title`, `emoji`, `sdk`
- `likes` (int), `private` (bool), `tags` (list[str])
- `runtime` (SpaceRuntime | None)
- `ai_short_description` (str | None) — AI-generated summary
- `ai_category` (str | None) — e.g. `"Image Generation"`
- `semantic_relevancy_score` (float | None) — 0–1 relevance to query
- `trending_score` (int | None)

---

### 5. list_spaces — Rich Filtering & Sorting

Not in v1's learnings. `list_spaces` supports extensive filtering:

```python
spaces = api.list_spaces(
    author="username",
    search="chatbot",
    filter="text-generation",      # tag
    datasets="bigcode/the-stack",  # Spaces using this dataset
    models="gpt2",                  # Spaces using this model
    linked=True,                    # only linked Spaces
    sort="likes",                   # SpaceSort_T: created_at | last_modified | likes | trending_score
    limit=50,
    expand=["runtime", "sdk", "cardData"],  # ExpandSpaceProperty_T values
    full=True,                      # return all properties
)
```

**ExpandSpaceProperty_T** options:
`author`, `cardData`, `createdAt`, `datasets`, `disabled`, `lastModified`, `likes`, `models`, `private`, `resourceGroup`, `runtime`, `sdk`, `sha`, `siblings`, `subdomain`, `tags`, `trendingScore`, `usedStorage`

**SpaceSort_T** options: `created_at`, `last_modified`, `likes`, `trending_score`

---

### 6. SpaceInfo — Full Metadata Object

`space_info()` returns a `SpaceInfo` dataclass with rich metadata (when `expand` is used):

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Repo ID |
| `author` | str\|None | Owner |
| `card_data` | SpaceCardData\|None | YAML card metadata |
| `created_at` | datetime\|None | Creation date |
| `datasets` | list[str]\|None | Linked datasets |
| `disabled` | bool\|None | Is disabled |
| `gated` | Literal["auto","manual",False]\|None | Gating status |
| `host` | str\|None | Host URL |
| `last_modified` | datetime\|None | Last commit |
| `likes` | int | Number of likes |
| `models` | list[str]\|None | Linked models |
| `private` | bool | Privacy status |
| `resource_group` | dict\|None | RG info |
| `runtime` | SpaceRuntime\|None | Current runtime |
| `sdk` | str\|None | SDK (gradio/docker/static) |
| `sha` | str\|None | Git commit SHA |
| `siblings` | list[RepoFile]\|None | File listing |
| `subdomain` | str\|None | hf.space subdomain |
| `tags` | list[str]\|None | Tags |
| `trending_score` | int\|None | Trending score |

---

### 7. Volume-Based Storage (Replaces Deprecated Storage API)

**`request_space_storage` and `delete_space_storage` are deprecated** (will be removed in v2.0). Use `set_space_volumes` / `delete_space_volumes` instead.

```python
from huggingface_hub import Volume

# Mount a storage bucket
api.set_space_volumes("user/my-space", volumes=[
    Volume(type="bucket", source="user/my-bucket", mount_path="/data", read_only=False)
])

# Mount a model read-only
api.set_space_volumes("user/my-space", volumes=[
    Volume(type="model", source="user/my-model", mount_path="/model", revision="main")
])

# Remove all volumes
api.delete_space_volumes("user/my-space")
```

**Volume fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | Literal["bucket","model","dataset","space"] | Yes | Resource type |
| `source` | str | Yes | Repo/bucket ID |
| `mount_path` | str | Yes | Path inside container (starts with /) |
| `revision` | str\|None | No | Git revision (repos only, default "main") |
| `read_only` | bool\|None | No | Read-only mount |
| `path` | str\|None | No | Subfolder prefix to mount |

**Volume serialization:**
- `to_dict()` — converts to JSON payload for Hub API
- `to_uri()` — returns HF mount URI string for CLI use

---

### 8. duplicate_repo — Replaces duplicate_space

**`duplicate_space` is also deprecated** in favor of `duplicate_repo` (more generic, supports all repo types):

```python
api.duplicate_repo(
    from_id="username/my-space",
    to_id="my-copy",
    repo_type="space",
    private=True,
    space_hardware=SpaceHardware.CPU_UPGRADE,
    space_sleep_time=1800,
    space_secrets=[{"key": "API_KEY", "value": "abc123"}],
    space_variables=[{"key": "DEBUG", "value": "true"}],
    space_volumes=[Volume(type="bucket", source="my-bucket", mount_path="/data")],
)
# Note: space_storage is also deprecated — use space_volumes instead
```

---

### 9. SpaceHotReloading — Dev Mode Deep Dive

`SpaceRuntime.hot_reloading` is populated when hot reloading is active:

```python
@dataclass
class SpaceHotReloading:
    status: Literal["created", "canceled"]
    replica_statuses: list[tuple[str, str | None]]
    raw: dict
```

Only available with PRO/Team plan.

---

### 10. Secrets & Variables Deep Dive

**SpaceSecret** (returned by `get_space_secrets`):
- `key` (str) — secret name
- `description` (str | None)
- `updated_at` (datetime | None)
- **Value is write-only** — cannot be read back after creation

**SpaceVariable** (returned by `get_space_variables`):
- `key` (str)
- `value` (str) — **visible** in UI and API
- `description` (str | None)
- `updated_at` (datetime | None) — `None` if never updated

**Key difference**: `add_space_secret(key, value, description=...)` stores encrypted value; `add_space_variable(key, value, description=...)` stores plaintext.

---

### 11. ZeroGPU Free Tier

`SpaceHardware.ZERO_A10G = "zero-a10g"` is available as a hardware SKU for Spaces. The ZeroGPU tier provides free GPU acceleration (A10G) for eligible Spaces, limited to 2 Gradio Spaces per free personal account. This is a critical zero-cost option.

---

### 12. sync_job_volume — Bucket Sync for Jobs

```python
volume = api.sync_job_volume(
    source="/path/to/local/dir",
    mount_path="/workspace/data",
    remote_name="my-fixed-name",  # optional, else auto-derived
    read_only=True,
)
```

Syncs a local directory to a bucket under `{namespace}/jobs-artifacts` and returns a `Volume` ready to mount. Re-syncing only uploads changed files.

---

### 13. Billing Model

- **Billed by the minute** — every minute the Space runs on upgraded hardware
- **No cost during BUILDING** — only Running or Starting stages incur charges
- **Paused time is not billed** — pause via API or settings
- **Free CPU Basic** sleeps after 48h inactivity, wakes on traffic
- **Upgraded hardware** runs indefinitely by default (set custom sleep time to save)
- **Community GPU Grants** — apply in Space settings for free upgrades
- **Billing stops when a Space fails** (RUNTIME_ERROR triggers auto-suspend)

**Pricing tiers (USD/hour)**:

| Hardware | Price/hr |
|----------|----------|
| CPU Basic | FREE |
| CPU Upgrade | $0.03 |
| T4 Small | $0.40 |
| T4 Medium | $0.60 |
| L4x1 | $0.80 |
| L40Sx1 | $1.80 |
| A10G Small | $1.00 |
| A100 Large | $2.50 |

Each replica billed independently ($/hr × replicas).

---

### 14. Built-in Environment Variables

Spaces expose built-in env vars at runtime:

| Variable | Example |
|----------|---------|
| `ACCELERATOR` | `t4-medium` or `none` |
| `CPU_CORES` | `4` |
| `MEMORY` | `15Gi` |
| `SPACE_AUTHOR_NAME` | `osanseviero` |
| `SPACE_REPO_NAME` | `i-like-flan` |
| `SPACE_TITLE` | `I Like Flan` |
| `SPACE_ID` | `osanseviero/i-like-flan` |
| `SPACE_HOST` | `osanseviero-i-like-flan.hf.space` |
| `SPACE_CREATOR_USER_ID` | `6032802e1f993496bc14d9e3` |

OAuth-enabled Spaces also get: `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_SCOPES`, `OPENID_PROVIDER_URL`.

---

### 15. Complete REST Endpoint Map

Updated with all endpoints discovered:

| Method | HTTP | Endpoint | Notes |
|--------|------|----------|-------|
| `space_info` | GET | `/api/spaces/{repo_id}` | |
| `get_space_runtime` | GET | `/api/spaces/{repo_id}/runtime` | |
| `fetch_space_logs` | GET/SSE | `/api/spaces/{repo_id}/logs/{build\|run}` | Supports `?tail=N` |
| `restart_space` | POST | `/api/spaces/{repo_id}/restart` | `factory_reboot` param |
| `pause_space` | POST | `/api/spaces/{repo_id}/pause` | |
| `enable_space_dev_mode` | POST | `/api/spaces/{repo_id}/dev-mode` | PRO/Team only |
| `disable_space_dev_mode` | DELETE | `/api/spaces/{repo_id}/dev-mode` | |
| `request_space_hardware` | POST | `/api/spaces/{repo_id}/hardware` | |
| `set_space_sleep_time` | POST | `/api/spaces/{repo_id}/sleep-time` | |
| `add_space_secret` | POST | `/api/spaces/{repo_id}/secrets` | Description optional |
| `delete_space_secret` | DELETE | `/api/spaces/{repo_id}/secrets` | JSON body `{"key":"..."}` |
| `get_space_secrets` | GET | `/api/spaces/{repo_id}/secrets` | Values redacted |
| `add_space_variable` | POST | `/api/spaces/{repo_id}/variables` | |
| `delete_space_variable` | DELETE | `/api/spaces/{repo_id}/variables` | |
| `get_space_variables` | GET | `/api/spaces/{repo_id}/variables` | Values visible |
| `set_space_volumes` | POST | `/api/spaces/{repo_id}/volumes` | Replaces storage API |
| `delete_space_volumes` | DELETE | `/api/spaces/{repo_id}/volumes` | |
| `list_spaces_hardware` | GET | `/api/spaces/hardware` | |
| `list_space_templates` | GET | `/api/spaces/templates` | |
| `search_spaces` | GET | `/api/spaces/search` | Semantic search |
| `list_spaces` | GET | `/api/spaces` | Filter, sort, paginate |
| `duplicate_repo` | POST | `/api/spaces/{repo_id}/duplicate` | Replaces duplicate_space |
| **Replicas** | POST | `/api/spaces/{repo_id}/replicas` | No dedicated hub method yet |
| `sync_job_volume` | POST | Bucket sync | Returns Volume for mounting |

---

### Summary of Deprecations to Track

| Old Method | Replacement | Removed in |
|------------|-------------|------------|
| `request_space_storage` | `set_space_volumes` | v2.0 |
| `delete_space_storage` | `delete_space_volumes` | v2.0 |
| `duplicate_space` | `duplicate_repo` | v2.0 |

## Zero-Cost Relevance

- **Always check `unit_cost_usd`** from `list_spaces_hardware()` before requesting hardware
- **ZeroGPU (`zero-a10g`)** provides free GPU — up to 2 per free personal account
- **CPU_BASIC** is always free; sleeps after 48h, wakes on traffic
- **`pause_space()`** stops billing completely
- **Set custom sleep time** on upgraded HW to save during idle periods
- **Use `space_info(expand=["runtime", "usedStorage"])`** to monitor resource usage

---

## 2026-07-25: Space Templates — Complete Deep-Dive (v1.23.0 Feature)

**Topic Deepening:** hf-hub-spaces-build-runtime-api-deep-dive-v3-space-templates

**Verified via:** Live API call to `GET /api/spaces/templates`, source code inspection of `HfApi.list_space_templates()`, `HfApi.create_repo()`, `SpaceTemplate` dataclass, `hf spaces templates` CLI

**Author:** SakThai
**License:** MIT

### Key Discovery: Space Templates (New in v1.23.0)

Released in `huggingface_hub` v1.23.0 on July 9, 2026 — this is a **completely new feature** not present when the original skill and v2 deep-dive were written.

### 1. New API Surface

Three additions to the Spaces management API:

1. **`HfApi.list_space_templates()`** → `list[SpaceTemplate]`
2. **`create_repo(space_template=...)`** — seeds a new Space from a template
3. **`hf spaces templates`** CLI command

### 2. SpaceTemplate Dataclass

```python
@dataclass
class SpaceTemplate:
    name: str               # Human-friendly name (e.g. "JupyterLab")
    repo_id: str            # Full Hub repo (e.g. "SpacesExamples/jupyterlab")
    sdk: str                # "docker" | "static" | "gradio"
    preferred_private: bool # If True, Space auto-created as private
```

Constructed from the API response keys `name`, `repoId`, `sdk`, `preferredPrivate`.

### 3. Template Resolution (from create_repo source)

- **Input format**: Accepts `repo_id` (full) or `name` (short, case-insensitive)
- **Resolution order**: Iterates templates list, tries exact `repo_id` match first, then case-insensitive `name` match
- **SDK auto-set**: `space_sdk` is set to `template.sdk` if not provided; raises `ValueError` if user-provided SDK doesn't match
- **Auto-visibility**: If `template.preferred_private` is True and user didn't set `private` or `visibility`, the Space defaults to private
- **Template value sent in API**: `template.repo_id` (always the full repo ID)

### 4. API Endpoint

```
GET https://huggingface.co/api/spaces/templates
→ {"templates": [{"name", "sdk", "repoId", "preferredPrivate"}, ...]}
```

### 5. Complete Template List (28 verified live)

| SDK | Count | Templates |
|-----|:-----:|-----------|
| **Docker** | 17 | Streamlit, JupyterLab, Argilla, Livebook, LabelStudio, AimStack, Shiny (R), Shiny (Python), ZenML, ChatUI, Panel, Giskard, Quarto, marimo, Evidence, Langfuse, Plotly |
| **Static** | 6 | Paper Project, Gradio-Lite, Transformers.js, React, Svelte, Vue |
| **Gradio** | 5 | chatbot, text-to-image, leaderboard, Trackio, Workflow |

### 6. CLI Commands

```bash
# List all templates
hf spaces templates

# Create Space from template (full repo_id)
hf repos create my-space --type space --template SpacesExamples/jupyterlab

# Create Space from template (short name)
hf repos create my-space --type space --template Streamlit
```

### 7. Zero-Cost Note

**All 5 Static templates** (Paper Project, Gradio-Lite, Transformers.js, React, Svelte, Vue) run on Static Spaces — entirely serverless and 100% free. Docker and Gradio templates can run on free CPU Basic tier. No paid services required to use Space Templates.

### 8. Edge Cases

- `list_space_templates()` requires authentication (HF token)
- Templates cannot be used with `duplicate_repo()` — only `create_repo()`
- No user-created templates; only official HF-curated templates
- `space_sdk` is overwritten by template's SDK — user cannot mix SDK with template
- `JupyterLab` is the only template with `preferred_private=True`

### 9. Integration with Existing Spaces APIs

Space Templates naturally compose with all other Spaces management APIs:
- `space_hardware`, `space_sleep_time`, `space_secrets` — work alongside `space_template`
- `wait_for_space()` — use after creation to wait for template-based Space to be ready
- `add_space_secret()`, `set_space_volumes()` — all post-creation operations work normally
