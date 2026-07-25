# HF Learnings — Deep Dive: hf-hub-spaces-python-sdk

## 2026-07-25: hf-hub-spaces-python-sdk (v2 deep dive)

### Summary
Deep dive into the Hugging Face Spaces Python SDK — the complete programmatic interface for managing Spaces via `huggingface_hub`. Researched directly from source code (`huggingface_hub._space_api` and `huggingface_hub.hf_api` v1.24.0). Covers all 26+ space-related `HfApi` methods across lifecycle management, hardware/runtime, secrets/variables, volumes (replacing deprecated persistent storage), dev mode, logs (SSE-based), server-side duplication, and discovery (semantic search).

### Key Findings

**Total API surface:** 26 methods on `HfApi` + 6 standalone function aliases.

**New in v1.24.0:**
- `set_space_volumes` / `delete_space_volumes` replace deprecated `request_space_storage` / `delete_space_storage`
- `Volume` dataclass supports 4 types: `bucket`, `model`, `dataset`, `space`
- `Volume.to_dict()` and `Volume.to_uri()` for serialization
- `wait_for_space()` — block until terminal stage (`RUNNING`, `BUILD_ERROR`, etc.)
- `fetch_space_logs()` — SSE-based log streaming (build or run, follow or snapshot)
- `enable_space_dev_mode` / `disable_space_dev_mode` (PRO+ plan)
- `search_spaces()` — semantic search (embedding-based for multi-word, full-text for single-word)
- `SpaceHotReloading` dataclass for hot-reload status tracking

**API endpoint mapping (all `https://huggingface.co/api/spaces/{id}`):**

| Endpoint suffix | Method | Returns |
|-----------------|--------|---------|
| (bare) GET | `space_info()` | `SpaceInfo` |
| `/runtime` GET | `get_space_runtime()` | `SpaceRuntime` |
| `/hardware` POST | `request_space_hardware()` | `SpaceRuntime` |
| `/sleeptime` POST | `set_space_sleep_time()` | `SpaceRuntime` |
| `/pause` POST | `pause_space()` | `SpaceRuntime` |
| `/restart` POST | `restart_space()` | `SpaceRuntime` |
| `/dev-mode` POST | `enable/disable_space_dev_mode()` | `SpaceRuntime` |
| `/secrets` POST | `add_space_secret()` | None |
| `/secrets` GET | `get_space_secrets()` | `dict[str, SpaceSecret]` |
| `/secrets` DELETE | `delete_space_secret()` | None |
| `/variables` POST | `add_space_variable()` | `dict[str, SpaceVariable]` |
| `/variables` GET | `get_space_variables()` | `dict[str, SpaceVariable]` |
| `/variables` DELETE | `delete_space_variable()` | `dict[str, SpaceVariable]` |
| `/volumes` PUT | `set_space_volumes()` | None |
| `/volumes` DELETE | `delete_space_volumes()` | None |
| `/logs/{run\|build}` GET | `fetch_space_logs()` | `Iterable[str]` (SSE) |
| `/storage` POST | `request_space_storage()` (deprecated) | `SpaceRuntime` |
| `/storage` DELETE | `delete_space_storage()` (deprecated) | `SpaceRuntime` |

**Standalone API at `/api/spaces`:**

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/api/spaces` GET | `list_spaces()` | `Iterable[SpaceInfo]` |
| `/api/spaces/semantic-search` GET | `search_spaces()` | `Iterable[SpaceSearchResult]` |
| `/api/spaces/hardware` GET | `list_spaces_hardware()` | `list[JobHardwareInfo]` |
| `/api/spaces/templates` GET | `list_space_templates()` | `list[SpaceTemplate]` |

**Data model classes** (all in `huggingface_hub._space_api`, 395 lines v1.24.0):
- `SpaceRuntime` — stage (enum-like string), hardware, requested_hardware, sleep_time, storage (deprecated), dev_mode, hot_reloading, volumes, raw
- `SpaceSecret` — key, description (write-only, value not returned), updated_at
- `SpaceVariable` — key, value (public, IS returned), description, updated_at
- `Volume` — type (bucket/model/dataset/space), source, mount_path, revision, read_only, path
- `SpaceHardware` (18-value enum): CPU_BASIC, CPU_UPGRADE, ZERO_A10G, T4_SMALL, T4_MEDIUM, L4X1, L4X4, L40SX1, L40SX4, L40SX8, A10G_SMALL, A10G_LARGE, A10G_LARGEX2, A10G_LARGEX4, A100_LARGE, A100X4, A100X8
- `SpaceStorage` — SMALL/MEDIUM/LARGE (deprecated in favor of volumes)
- `SpaceTemplate` — name, repo_id, sdk, preferred_private
- `SpaceSearchResult` — id, author, title, emoji, sdk, likes, private, tags, runtime, ai_category, ai_short_description, semantic_relevancy_score, trending_score
- `SpaceHotReloading` — status ("created"/"canceled"), replica_statuses, raw

**Important constraints:**
- Static Spaces: no pause/restart/volumes support
- CPU-basic (free): fixed 48h sleep, not configurable
- Secrets: values never exposed after creation; store externally if re-read needed
- Dev Mode: PRO/Team plan only
- Factory reboot (`restart_space(factory_reboot=True)`): full rebuild, no cache

---

## 2026-07-25: v2 Deepening — Source-Level Details (from huggingface_hub v1.24.0)

### 1. Space Stage Machine

Source: `_space_api.py` lines 22–65

The Space lifecycle is a state machine with **11 stages** and 2 groupings:

```python
INTERMEDIATE_SPACE_STAGES = (
    SpaceStage.BUILDING,         # Container building
    SpaceStage.RUNNING_BUILDING, # Rebuilding while running
    SpaceStage.APP_STARTING,     # Application starting up
    SpaceStage.RUNNING_APP_STARTING, # App starting while serving
)

TERMINAL_SPACE_STAGES = (
    SpaceStage.RUNNING,          # Healthy & serving
    SpaceStage.BUILD_ERROR,      # Docker build failed
    SpaceStage.RUNTIME_ERROR,    # App crashed at runtime
    SpaceStage.CONFIG_ERROR,     # Bad configuration
    SpaceStage.NO_APP_FILE,      # Missing app file
    SpaceStage.STOPPED,          # Manually stopped
    SpaceStage.PAUSED,           # Manually paused (no billing)
    SpaceStage.DELETING,         # Being deleted
)
```

All other stages not in `TERMINAL_SPACE_STAGES` are considered intermediate. `wait_for_space()` polls every `poll_interval` (default 1s) and returns only when the stage is no longer intermediate. The check is `stage not in INTERMEDIATE_SPACE_STAGES` — meaning PAUSED, STOPPED, and DELETING are all "terminal" from the wait perspective, though only RUNNING is the success state.

### 2. Volume Dataclass Internals

Source: `_space_api.py` lines 121–178

```python
@dataclass
class Volume:
    type: Literal["bucket", "model", "dataset", "space"]
    source: str                     # e.g. "username/my-model"
    mount_path: str                # e.g. "/data" (MUST start with /)
    revision: str | None = None    # Git revision for repos; defaults to "main"
    read_only: bool | None = None  # Forced True for repos; bucket defaults False
    path: str | None = None        # Subfolder prefix

    def to_dict(self) -> dict:
        """Serialize to API-compatible dict."""
        d = {"type": self.type, "source": self.source, "mountPath": self.mount_path}
        if self.revision is not None:      d["revision"] = self.revision
        if self.read_only is not None:     d["readOnly"] = self.read_only
        if self.path is not None:          d["path"] = self.path
        return d

    def to_uri(self) -> str:
        """Returns HF mount URI e.g. hf://bucket/username/my-bucket?mount_path=/data"""
        return HfUri(
            owner=self.source.split("/")[0],
            repo=self.source.split("/")[1],
            repo_type=self.type,
            mount_path=self.mount_path,
            revision=self.revision,
            subfolder=self.path,
        ).resolve().remotestr
```

The `to_uri()` method produces URIs like:
- `hf://bucket/username/my-bucket?mount_path=/data`
- `hf://models/username/my-model?revision=main&mount_path=/models`

Internally, `set_space_volumes()` serializes each volume via `Volume.to_dict()` and sends as JSON array. The API accepts `camelCase` keys (`mountPath`, `readOnly`), not snake_case — `.to_dict()` handles the translation.

### 3. Space Log Streaming (SSE Internals)

Source: `hf_api.py` lines 8537–8619

The `fetch_space_logs()` function uses Server-Sent Events (SSE):

```
GET /api/spaces/{repo_id}/logs/{run|build}
```

**SSE event format:**
```
data: {"data": "INFO:     Started server process [1]\n", "timestamp": "2026-07-25T12:00:00Z"}

data:  (keep-alive — empty data field, skipped by parser)
```

Key implementation details:
- `_fetch_space_logs_sse()` delegates to `_stream_sse_events()` with the log label `spaces /logs/{type} for repo_id={repo_id!r}`
- **Non-follow mode** (`follow=False`): uses a short read timeout of **5 seconds** — drains the currently buffered log buffer and returns
- **Follow mode** (`follow=True`): uses a **120-second read timeout** — blocks streaming live logs until the server closes the stream or KeyboardInterrupt
- Keep-alive messages (empty `data:` lines) are automatically skipped by the parser (only `data: {` JSON events are yielded)
- The outer `fetch_space_logs()` unwraps the SSE event dict, yielding `event["data"]` (plain string, one per line)
- Build logs vs run logs are selected by the `build` boolean param
- No pagination or seek — you get only the current buffer (or live stream)

### 4. Server-Side Space Duplication (`duplicate_repo`)

Source: `hf_api.py` lines 8687–8776+

The `duplicate_repo()` method performs **server-side copy** of any repo type including Spaces. This preserves full git history, LFS objects, files, and config without a local download/upload round-trip.

For Spaces, the method accepts Space-specific kwargs:

```python
duplicate_repo(
    from_id="username/source-space",
    to_id="username/copy-space",         # Optional — defaults to same name in your account
    repo_type="space",
    private=True,                         # Privacy override (default: same as source)
    exist_ok=False,
    space_hardware="cpu-basic",          # Hardware tier for the copy
    space_storage="small",               # Deprecated — use space_volumes instead
    space_sleep_time=3600,               # Seconds of inactivity before sleep
    space_secrets=[{"key": "API_KEY", "value": "sk-..."}],
    space_variables=[{"key": "MODEL_ID", "value": "my-model"}],
    space_volumes=[Volume(type="model", source="user/model", mount_path="/models", read_only=True)],
)
```

Returns `RepoUrl` (subclass of `str`) with `.endpoint`, `.repo_type`, `.repo_id`.

**Important:** `duplicate_space()` is deprecated in favor of `duplicate_repo()`.

### 5. Deprecated Storage Methods

**`request_space_storage(repo_id, storage)`** (deprecated → `set_space_volumes`)
- POST `/api/spaces/{id}/storage` with payload `{"tier": "small|medium|large"}`
- Returns `SpaceRuntime`

**`delete_space_storage(repo_id)`** (deprecated → `delete_space_volumes`)
- DELETE `/api/spaces/{id}/storage`
- Returns `SpaceRuntime`
- Raises `BadRequestError` if Space has no persistent storage

Both marked with `@_deprecate_method(version="2.0", message="Use ... instead.")`

### 6. SpaceHardware Enum (18 Values)

Source: `_space_api.py` lines 68–101

| Enum Member | String Value | Category |
|-------------|-------------|----------|
| `CPU_BASIC` | `"cpu-basic"` | CPU (free) |
| `CPU_UPGRADE` | `"cpu-upgrade"` | CPU (paid) |
| `ZERO_A10G` | `"zero-a10g"` | ZeroGPU (free) |
| `T4_SMALL` | `"t4-small"` | GPU |
| `T4_MEDIUM` | `"t4-medium"` | GPU |
| `L4X1` | `"l4x1"` | GPU |
| `L4X4` | `"l4x4"` | GPU |
| `L40SX1` | `"l40sx1"` | GPU |
| `L40SX4` | `"l40sx4"` | GPU |
| `L40SX8` | `"l40sx8"` | GPU |
| `A10G_SMALL` | `"a10g-small"` | GPU |
| `A10G_LARGE` | `"a10g-large"` | GPU |
| `A10G_LARGEX2` | `"a10g-largex2"` | GPU |
| `A10G_LARGEX4` | `"a10g-largex4"` | GPU |
| `A100_LARGE` | `"a100-large"` | GPU |
| `A100X4` | `"a100x4"` | GPU |
| `A100X8` | `"a100x8"` | GPU |

Values are comparable to strings: `SpaceHardware.CPU_BASIC == "cpu-basic"` → True.

The strings come from the internal TypeScript enum `SpaceHardwareFlavor` in Hugging Face's moon-landing server code.

### 7. SpaceSearchResult — Semantic Search Response

Source: `_space_api.py` lines 301–364

```python
@dataclass
class SpaceSearchResult:
    id: str                          # "username/repo-name"
    author: str
    title: str
    emoji: str | None
    sdk: str | None                  # "gradio", "docker", "static"
    likes: int
    private: bool
    tags: list[str] | None
    runtime: SpaceRuntime | None
    ai_short_description: str | None  # AI-generated description
    ai_category: str | None           # e.g. "Image Generation"
    semantic_relevancy_score: float | None  # 0–1 relative to query
    trending_score: int | None
```

Key observations:
- `semantic_relevancy_score` uses camelCase from API (`semanticRelevancyScore`), translated to snake_case in Python dataclass
- `runtime` is fully populated `SpaceRuntime` when Space is running, `None` when not
- Works by embedding-based search for multi-word queries, falls back to full-text for single-word

### 8. List Spaces Hardware

Source: `hf_api.py` line 8156

```python
def list_spaces_hardware(self, token=None) -> list[JobHardwareInfo]:
```

Returns `list[JobHardwareInfo]`, the **same type used by Jobs** — meaning the Spaces hardware listing shares the same data model as Jobs hardware flavors. Each `JobHardwareInfo` includes `.flavor`, `.name`, `.type`, `.gpu`, `.cpu`, `.memory`, `.monthly_price`, `.hourly_price`.

### 9. SpaceTemplate — Template-Based Creation

Source: `_space_api.py` lines 367–390

```python
@dataclass
class SpaceTemplate:
    name: str                # "JupyterLab", "chatbot", "Streamlit", etc.
    repo_id: str             # "SpacesExamples/jupyterlab"
    sdk: str                 # "gradio", "docker", "static"
    preferred_private: bool  # Whether to default to private
```

Templates are fetched from `GET /api/spaces/templates`. The `repo_id` can be passed to `create_repo(space_template=...)` to seed a new Space from the template's contents. Available templates include JupyterLab, Gradio chatbot, Streamlit dashboard, Docker blank, Static HTML, and more.

### Skill Created
`hf-hub-spaces-python-sdk/` — complete reference with full method catalog, data model classes, key patterns, edge cases, source-level stage machine, SSE log streaming internals, volume URI format, server-side duplication, deprecated storage migration, and verified endpoint mapping.

### Sources
- `huggingface_hub._space_api` (v1.24.0) — all Space data model classes (395 lines)
- `huggingface_hub.hf_api` (v1.24.0) — all space-related HfApi methods (14985 lines total)
- Official docs: https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api#space-management
- Verified via live Python introspection on 2026-07-25
