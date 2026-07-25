# HF Learning Log — HF Hub Spaces Build, Runtime & Management API

**Topic:** hf-hub-spaces-build-runtime-api  
**Learned:** 2026-07-25  
**Source:** huggingface_hub source code analysis (HfApi space methods) + API endpoint probing

## Key Takeaways

### 1. SpaceRuntime Stage Machine
- 4 intermediate stages (`BUILDING`, `RUNNING_BUILDING`, `APP_STARTING`, `RUNNING_APP_STARTING`) trigger `wait_for_space` polling
- 5 terminal stages (`RUNNING`, `PAUSED`, `SLEEPING`, `BUILD_ERROR`, `STOPPED`) end polling
- `get_space_runtime()` hits `GET /api/spaces/{repo_id}/runtime` — returns raw dict parsed into `SpaceRuntime`

### 2. wait_for_space Implementation
- Polls every `poll_interval` seconds (default 1s)
- Checks `stage` against a hardcoded intermediate set (tuple of strings)
- Returns immediately if stage is already terminal
- Returns the *final* `SpaceRuntime` in all cases (caller must check `.stage`)

### 3. Logs Endpoint Architecture
- Run logs: `?build=false` (default) — stdout/stderr of the running application
- Build logs: `?build=true` — container build phase (use when `BUILD_ERROR`)
- Two modes: buffered (non-blocking, returns available lines) and SSE streaming (`follow=True`, blocking)
- Underlying SSE endpoint: `GET /api/spaces/{repo_id}/logs?build={bool}`

### 4. Hardware Lifecycle
- `list_spaces_hardware()` → `GET /api/spaces/hardware` → `list[JobHardwareInfo]`
- `JobHardwareInfo` includes `unit_cost_usd` for cost-awareness
- `request_space_hardware()` accepts `SpaceHardware` enum or raw string
- Setting `sleep_time` only works on upgraded (paid) hardware
- Free Spaces (`CPU_BASIC`) have fixed 48h sleep — cannot configure

### 5. Secrets vs Variables Design
- **Secrets**: encrypted storage, values redacted after creation, `POST /api/spaces/{repo_id}/secrets`
- **Variables**: plaintext environment variables, visible in API + UI
- Both support `key`, `value`, and optional `description`
- Secrets deletion via `DELETE /api/spaces/{repo_id}/secrets` with JSON body `{"key": "..."}`

### 6. Dev Mode
- Keeps container alive across app restarts — speeds up iteration
- Requires PRO or Team/Enterprise plan
- Enabled via `POST /api/spaces/{repo_id}/dev-mode`, disabled via `DELETE`

### 7. Factory Reboot
- `factory_reboot=True` on `restart_space()` rebuilds without caching
- Forces fresh `pip install` / `apt install` — good for debugging caching issues

### 8. Template System
- `list_space_templates()` → `GET /api/spaces/templates` → `list[SpaceTemplate]`
- Used via `create_repo(space_template="template/repo-id")`
- Each template has: `name`, `repo_id`, `sdk`, `preferred_private`

## API Patterns Observed

- All mutations require `repo_id` + auth token
- `validate_hf_hub_args` decorator normalizes repo_id format
- All methods raise `HfHubHTTPError` on 4xx/5xx
- `wait_for_space` is the recommended polling loop — don't write custom polling
- `SpaceRuntime` exposes `raw` dict for fields not parsed as attributes (e.g., `replicas`, `domains`, `sha`)

## Zero-Cost Relevance

- Only `CPU_BASIC` and `CPU_UPGRADE` hardware tiers are free
- Always check `unit_cost_usd` before requesting hardware
- `pause_space()` stops billing entirely — use for development Spaces
- `duplicate_space()` preserves sleep-time and hardware settings
