# HF Learnings — Deep Dive: hf-hub-spaces-python-sdk

## 2026-07-25: hf-hub-spaces-python-sdk (v2 deep dive)

### Summary
Deep dive into the Hugging Face Spaces Python SDK — the complete programmatic interface for managing Spaces via `huggingface_hub`. Researched directly from source code (`huggingface_hub._space_api` and `huggingface_hub.hf_api` v1.24.0). Covers all 25+ space-related `HfApi` methods across lifecycle management, hardware/runtime, secrets/variables, volumes (replacing deprecated persistent storage), dev mode, logs (SSE-based), and discovery (semantic search).

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

**Standalone API at `/api/spaces`:**
| Endpoint | Method | Returns |
|----------|--------|---------|
| `/api/spaces` GET | `list_spaces()` | `Iterable[SpaceInfo]` |
| `/api/spaces/semantic-search` GET | `search_spaces()` | `Iterable[SpaceSearchResult]` |
| `/api/spaces/hardware` GET | `list_spaces_hardware()` | `list[JobHardwareInfo]` |
| `/api/spaces/templates` GET | `list_space_templates()` | `list[SpaceTemplate]` |

**Data model classes** (all in `huggingface_hub._space_api`):
- `SpaceRuntime` — stage (enum-like string), hardware, requested_hardware, sleep_time, storage (deprecated), dev_mode, hot_reloading, volumes, raw
- `SpaceSecret` — key, description (write-only, value not returned), updated_at
- `SpaceVariable` — key, value (public, IS returned), description, updated_at
- `Volume` — type (bucket/model/dataset/space), source, mount_path, revision, read_only, path
- `SpaceHardware` — 18-value enum: CPU_BASIC, CPU_UPGRADE, ZERO_A10G, T4_*, L4*, L40S*, A10G_*, A100_*
- `SpaceStorage` — SMALL/MEDIUM/LARGE (deprecated in favor of volumes)
- `SpaceTemplate` — name, repo_id, sdk, preferred_private
- `SpaceSearchResult` — id, author, title, emoji, sdk, likes, private, tags, runtime, ai_category, ai_short_description, semantic_relevancy_score, trending_score

**Important constraints:**
- Static Spaces: no pause/restart/volumes support
- CPU-basic (free): fixed 48h sleep, not configurable
- Secrets: values never exposed after creation; store externally if re-read needed
- Dev Mode: PRO/Team plan only
- Factory reboot (`restart_space(factory_reboot=True)`): full rebuild, no cache

### Skill Created
`hf-hub-spaces-python-sdk/` — complete reference with full method catalog, data model classes, key patterns, edge cases, and source-code-verified endpoint mapping.

### Sources
- `huggingface_hub._space_api` (SpaceRuntime, SpaceSecret, SpaceVariable, Volume, SpaceHardware, SpaceStorage, SpaceSearchResult, SpaceTemplate, SpaceHotReloading) — v1.24.0
- `huggingface_hub.hf_api` (all 26 space-related HfApi methods) — v1.24.0
- Verified via live Python introspection on 2026-07-25
