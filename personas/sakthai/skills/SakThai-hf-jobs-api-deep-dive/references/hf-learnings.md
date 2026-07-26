# HF Learnings — Hugging Face Jobs API Python SDK Deep Dive

## 2026-07-25: hf-jobs-api-deep-dive — Python SDK Internals (Topic #354)

### Summary

Deep dive into the Hugging Face **Jobs** compute platform's Python SDK (`huggingface_hub` v1.24.0). This goes beyond the CLI surface to examine the **source-level architecture**: dataclass models, API method signatures, implementation patterns, SSE streaming, volume derivation, and job lifecycle management. Based on source code analysis of `_jobs_api.py` (573 lines) and the Jobs methods in `hf_api.py`.

Key insight: The Jobs SDK is one of the newest and most sophisticated subsystems in `huggingface_hub` (copyright 2025). It uses a REST API at `/api/jobs/` and `/api/scheduled-jobs/`, with Server-Sent Events (SSE) for real-time log and metric streaming, and a `WeakFileLock`-based local directory sync mechanism for volume mounting.

---

### 1. Dataclass Architecture (`_jobs_api.py`)

The entire Jobs API is built on a hierarchy of immutable-style dataclasses that deserialize from Hub's camelCase JSON responses.

#### Core Hierarchy

```
JobHardware (Enum)         — hardware flavor identifiers
JobStage (Enum)            — lifecycle stages
JobStatus                  — stage + message + expose_urls + ssh_url
JobDurations               — scheduling_secs, running_secs, total_secs
JobOwner                   — id + name + type
JobInitiator               — type (user/org/scheduled-job/duplicated-job) + id + name
  ├── JobInfo              — single Job run (id, created_at, status, ...)
  └── ScheduledJobInfo     — cron schedule definition
        └── JobSpec        — reusable job spec (image, command, env, secrets, flavor, ...)
              └── ScheduledJobStatus — last_job + next_job_run_at
                    └── LastJobInfo  — id + at
JobAccelerator             — GPU type/model/vram/manufacturer
JobHardwareInfo            — full hardware spec (name, cpu, ram, accelerator, cost)
```

#### `JobHardware` Enum (21 flavors)

```python
class JobHardware(str, Enum):
    # CPU
    CPU_BASIC = "cpu-basic"           # 2 vCPU, 16 GB, $0.01/hr
    CPU_UPGRADE = "cpu-upgrade"       # 8 vCPU, 32 GB, $0.03/hr
    CPU_PERFORMANCE = "cpu-performance"
    CPU_XL = "cpu-xl"                 # 16 vCPU, 124 GB, $1.00/hr

    # GPU — NVIDIA
    T4_SMALL = "t4-small"             # 1×T4 (16 GB), $0.40/hr
    T4_MEDIUM = "t4-medium"
    L4X1 = "l4x1"                    # 1×L4 (24 GB)
    L4X4 = "l4x4"                    # 4×L4
    L40SX1 = "l40sx1"                # 1×L40S (48 GB), $1.80/hr
    L40SX4 = "l40sx4"
    L40SX8 = "l40sx8"
    A10G_SMALL = "a10g-small"        # 1×A10G (24 GB), $1.00/hr
    A10G_LARGE = "a10g-large"
    A10G_LARGEX2 = "a10g-largex2"
    A10G_LARGEX4 = "a10g-largex4"
    A100_LARGE = "a100-large"        # 1×A100 (80 GB), $2.50/hr
    A100X4 = "a100x4"
    A100X8 = "a100x8"
    H200 = "h200"                    # 1×H200 (141 GB), $5.00/hr
    H200X2 = "h200x2"
    H200X4 = "h200x4"
    H200X8 = "h200x8"
    RTX_PRO_6000 = "rtx-pro-6000"    # 1×RTX PRO 6000 (96 GB), $2.75/hr
    RTX_PRO_6000X2 = "rtx-pro-6000x2"
    RTX_PRO_6000X4 = "rtx-pro-6000x4"
    RTX_PRO_6000X8 = "rtx-pro-6000x8"
```

Enums support string comparison: `assert JobHardware.CPU_BASIC == "cpu-basic"`.

#### `JobStage` Enum — Lifecycle States

```python
class JobStage(str, Enum):
    SCHEDULING = "SCHEDULING"   # queued, waiting for hardware
    RUNNING = "RUNNING"         # executing
    COMPLETED = "COMPLETED"     # successful completion
    CANCELED = "CANCELED"       # cancelled by user
    ERROR = "ERROR"             # failed
    DELETED = "DELETED"         # deleted

TERMINAL_JOB_STAGES = (JobStage.COMPLETED, JobStage.CANCELED, JobStage.ERROR, JobStage.DELETED)
```

#### `JobInfo` — Complete Job Run Data (14 fields)

| Field | Type | Source |
|-------|------|--------|
| `id` | `str` | JSON `id` |
| `created_at` | `datetime\|None` | `createdAt` |
| `started_at` | `datetime\|None` | `startedAt` |
| `finished_at` | `datetime\|None` | `finishedAt` |
| `docker_image` | `str\|None` | `dockerImage` |
| `space_id` | `str\|None` | `spaceId` (Space as image source) |
| `command` | `list[str]\|None` | `command` |
| `arguments` | `list[str]\|None` | `arguments` |
| `environment` | `dict\|None` | `environment` |
| `secrets` | `dict\|None` | `secrets` |
| `flavor` | `JobHardware\|None` | `flavor` |
| `labels` | `dict[str,str]\|None` | `labels` |
| `volumes` | `list[Volume]\|None` | Deserialized from JSON |
| `status` | `JobStatus` | `{stage, message, exposeUrls, sshUrl}` |
| `durations` | `JobDurations\|None` | `{schedulingSecs, runningSecs, totalSecs}` |
| `owner` | `JobOwner` | `{id, name, type}` |
| `initiator` | `JobInitiator\|None` | `{type, id, name}` |

**Inferred fields** (computed, not from API):
- `endpoint: str` — defaults to `constants.ENDPOINT`
- `url: str` — `f"{endpoint}/jobs/{owner.name}/{id}"`

**JSON deserialization is tolerant** — the `__init__` checks both camelCase (API response) and snake_case (manual construction) keys.

#### `ScheduledJobInfo` — Cron Schedule Data (9 fields)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Scheduled Job ID |
| `created_at` | `datetime\|None` | When the schedule was created |
| `job_spec` | `JobSpec` | Reusable job spec (image, command, env, etc.) |
| `schedule` | `str\|None` | `"@hourly"`, `"@daily"`, or CRON `"*/5 * * * *"` |
| `suspend` | `bool\|None` | Whether paused |
| `concurrency` | `bool\|None` | Whether concurrent runs allowed |
| `status` | `ScheduledJobStatus` | `{lastJob: {id, at}, nextJobRunAt: datetime}` |
| `owner` | `JobOwner` | `{id, name, type}` |

#### `JobSpec` — Portable Job Definition

```python
@dataclass
class JobSpec:
    docker_image: str | None
    space_id: str | None          # Space as alternative to Docker image
    command: list[str] | None
    arguments: list[str] | None
    environment: dict[str, Any] | None
    secrets: dict[str, Any] | None
    flavor: JobHardware | None
    timeout: int | None           # in seconds
    tags: list[str] | None
    arch: str | None              # CPU architecture
    labels: dict[str, str] | None
    volumes: list[Volume] | None
```

#### `JobHardwareInfo` — Hardware Catalog Entry

```python
@dataclass
class JobHardwareInfo:
    name: str                     # "cpu-basic", "a10g-small"
    pretty_name: str              # "CPU Basic", "Nvidia A10G - small"
    cpu: str                      # "2 vCPU"
    ram: str                      # "16 GB"
    ephemeral_storage: str        # "20 GB"
    accelerator: JobAccelerator | None  # GPU details if applicable
    unit_cost_micro_usd: int      # cost in micro-dollars (e.g. 167 = $0.000167)
    unit_cost_usd: float          # cost in USD
    unit_label: str               # "minute"
```

#### `JobAccelerator` — GPU Specification

```python
@dataclass
class JobAccelerator:
    type: str                     # "gpu"
    model: str                    # "T4", "A10G", "A100", "L4", "L40S"
    quantity: str                 # "1", "2", "4", "8"
    vram: str                     # "16 GB", "24 GB", "80 GB"
    manufacturer: str             # "Nvidia"
```

---

### 2. Full Python API Surface

All methods below are on `HfApi` and also exposed as standalone functions at the `huggingface_hub` module level.

#### 2.1 Running Jobs

**`run_job(image, command, env, secrets, flavor, timeout, name, labels, volumes, expose, ssh, namespace, token) -> JobInfo`**

- Posts to `POST /api/jobs/{namespace}`
- Uses `_create_job_spec()` to build the payload
- `image` can be a Docker Hub image (`"python:3.12"`) or a Space (`"hf.co/spaces/user/space-name"`)
- When image starts with `https://huggingface.co/spaces/`, `https://hf.co/spaces/`, etc., it's converted to `spaceId` instead of `dockerImage`
- Default flavor: `cpu-basic`
- Returns immediately with a `JobInfo`; job runs asynchronously

**`run_uv_job(script, script_args, dependencies, python, image, env, secrets, flavor, timeout, name, labels, volumes, expose, ssh, namespace, token) -> JobInfo`** (marked `@experimental`)

- Runs a UV Python script instead of a raw Docker command
- Default image: `ghcr.io/astral-sh/uv:python3.12-bookworm`
- Auto-installs dependencies specified in `dependencies: list[str]`
- Supports both URL scripts and local paths
- Simplified API: just pass a script path/URL + deps, no Docker knowledge needed

#### 2.2 Scheduled Jobs (CRON)

**`create_scheduled_job(image, command, schedule, suspend, concurrency, env, secrets, flavor, timeout, name, labels, volumes, expose, namespace, token) -> ScheduledJobInfo`**

- Posts to `POST /api/scheduled-jobs/{namespace}`
- `schedule`: supports `@annually`, `@yearly`, `@monthly`, `@weekly`, `@daily`, `@hourly` shortcuts, or full CRON expressions like `"0 9 * * 1"` or `"*/5 * * * *"`
- `suspend`: `True` = created in paused state
- `concurrency`: `True` = allow overlapping runs

**`create_scheduled_uv_job(script, script_args, schedule, suspend, concurrency, dependencies, python, image, env, secrets, flavor, timeout, name, labels, volumes, expose, namespace, token) -> ScheduledJobInfo`** (marked `@experimental`)

- Same as `create_scheduled_job` but for UV Python scripts
- Simplest way to run a Python script on a schedule

**`list_scheduled_jobs(timeout, namespace, token) -> list[ScheduledJobInfo]`**

- `GET /api/scheduled-jobs/{namespace}`

**`inspect_scheduled_job(scheduled_job_id, namespace, token) -> ScheduledJobInfo`**

- `GET /api/scheduled-jobs/{namespace}/{id}`

**`delete_scheduled_job(scheduled_job_id, namespace, token) -> None`**

- `DELETE /api/scheduled-jobs/{namespace}/{id}`

**`suspend_scheduled_job(scheduled_job_id, namespace, token) -> None`**

- `POST /api/scheduled-jobs/{namespace}/{id}/suspend`

**`resume_scheduled_job(scheduled_job_id, namespace, token) -> None`**

- `POST /api/scheduled-jobs/{namespace}/{id}/resume`

**`trigger_scheduled_job(scheduled_job_id, namespace, token) -> JobInfo`**

- `POST /api/scheduled-jobs/{namespace}/{id}/run`
- Triggers **one immediate run** without affecting the schedule
- Returns HTTP 409 if another run is active and `concurrency` is disabled

**`update_scheduled_job_labels(scheduled_job_id, labels, namespace, token) -> ScheduledJobInfo`**

- `PUT /api/scheduled-jobs/{namespace}/{id}/labels`
- Replaces **all** existing labels (not additive)

#### 2.3 Job Lifecycle

**`list_jobs(status, labels, timeout, namespace, token) -> Iterable[JobInfo]`**

- `GET /api/jobs/{namespace}` with query params
- Supports filtering: `status` (single or list of `JobStage` values), `labels` (dict of `key=value` pairs)
- Returns a generator (uses `paginate` for multi-page results)

**`inspect_job(job_id, namespace, token) -> JobInfo`**

- `GET /api/jobs/{namespace}/{id}`

**`cancel_job(job_id, namespace, token) -> JobInfo`**

- `POST /api/jobs/{namespace}/{id}/cancel`

**`wait_for_job(job_id, poll_interval, timeout, namespace, token) -> JobInfo`**

- Polls `inspect_job` every `poll_interval` seconds until terminal state
- Returns final `JobInfo`

#### 2.4 Logs & Metrics (SSE Streaming)

**`fetch_job_logs(job_id, namespace, follow, tail, token) -> Iterable[str]`**

- Uses **Server-Sent Events** (SSE) to stream logs
- `follow=True`: real-time streaming, blocks until job completes
- `follow=False`: fetch currently available logs, returns immediately
- `tail=N`: only return last N lines
- Filters out the `"===== Job started"` header line from output
- Timeout logic: 4×30s (120s) when following, 5s when not following
- Retries on timeout, ChunkedEncodingError, etc.
- The SSE stream has `: keep-alive` pings every 30 seconds

**`fetch_job_metrics(job_id, namespace, token) -> Iterable[dict]`**

- Real-time hardware metrics via SSE
- One metric event per second
- Returns dicts with: `cpu_usage_pct`, `cpu_millicores`, `memory_used_bytes`, `memory_total_bytes`, `rx_bps`, `tx_bps`, `gpus` (per-GPU dict with `utilization`, `memory_used_bytes`, `memory_total_bytes`), `replica`
- Tolerates HTTP 500 (job already finished)
- Stream ends when timeout hits (no clean end event)

#### 2.5 Hardware Catalog

**`list_jobs_hardware(token) -> list[JobHardwareInfo]`**

- `GET /api/jobs/hardware`
- Returns the full catalog of available hardware with pricing

---

### 3. Internal Implementation Patterns

#### 3.1 `_create_job_spec()` — Payload Builder

The helper function `_create_job_spec()` (lines 513–573) centralizes payload construction for both `run_job` and `create_scheduled_job`:

```python
def _create_job_spec(*, image, command, env, secrets, flavor, timeout, name, labels, volumes, expose, ssh) -> dict:
```

Key behaviors:
- **Name conflict guard**: raises `ValueError` if both `name` and `labels["name"]` are provided
- **Timeout parsing**: supports string time units (`"5m"`, `"2h"`, `"3d"`, `"30s"`) via factor lookup
- **Image prefix detection**: detects Space images by checking 4 prefix variants and sets `spaceId` instead of `dockerImage`
- **SSH flag**: sets `job_spec["ssh"] = {"enabled": True}`
- **Port expose**: sets `job_spec["expose"] = {"ports": expose}`

#### 3.2 `_derive_job_volume_name()` — Local Directory Sync

```python
def _derive_job_volume_name(source: str | Path) -> str:
    resolved = Path(source).expanduser().resolve()
    digest = hashlib.sha256(f"{platform.node()}:{resolved}".encode()).hexdigest()[:8]
    dirname = resolved.name.replace(" ", "_") or "root"
    return f"{dirname}-{digest}"
```

This produces a stable remote folder name for local directory syncing:
- Hash fingerprints `hostname:absolute_path` — same dir from same machine = same name (delta-sync)
- Same-named dirs from different machines = different hash (no collision)
- Same dir from different path on same machine = different hash (safe)

#### 3.3 SSE Streaming Architecture

`_fetch_running_job_sse()` (lines 11929–11968) is the base SSE streaming method used by both `fetch_job_logs` and `fetch_job_metrics`:

```python
def _fetch_running_job_sse(self, *, job_id, route, timeout, skip_previous_events_on_retry,
                          tolerated_status_codes, follow, namespace, token, params) -> Iterable[dict]:
```

- **Follow vs. no-follow**: When `follow=False`, uses a short timeout (5s) to fetch buffered historical data
- **Termination check**: After each SSE callback, calls `has_job_finished()` which hits `GET /api/jobs/{namespace}/{id}` and checks if stage is past `RUNNING`/`UPDATING`
- **Retry logic**: Tolerates timeouts, `ChunkedEncodingError`, and configurable HTTP status codes
- **Keep-alive**: `: keep-alive` pings every 30 seconds; the system waits through 4 of these (120s) before treating a silent stream as finished

#### 3.4 `JobInfo.__init__()` — CamelCase ↔ snake_case Bridge

All dataclasses in `_jobs_api.py` accept **both** camelCase (from Hub JSON API) and snake_case (for manual construction). Pattern:

```python
def __init__(self, **kwargs) -> None:
    self.id = kwargs["id"]
    created_at = kwargs.get("createdAt") or kwargs.get("created_at")
    self.created_at = parse_datetime(created_at) if created_at else None
```

This dual-key pattern is used consistently across every dataclass, making the objects easy to construct both from API responses and from test fixtures.

#### 3.5 Error Handling

- **HTTP 409** on `trigger_scheduled_job()`: another instance already running, concurrency disabled
- **HTTP 500** tolerated in `fetch_job_metrics()`: job already finished, no metrics available
- **Timeouts** in log streaming: treat as end-of-stream signal
- **`ChunkedEncodingError`** in log/metric SSE: treat as connection reset (retry or stop)

---

### 4. Practical Usage Patterns

#### 4.1 Run a One-Shot GPU Training Job

```python
from huggingface_hub import run_job, wait_for_job

job = run_job(
    image="pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel",
    command=[
        "python", "-c",
        "import torch; print(f'GPU: {torch.cuda.get_device_name()}')"
    ],
    flavor="a10g-small",
    timeout="30m",
    name="gpu-test",
)
print(f"Job submitted: {job.url}")

# Wait for completion
final = wait_for_job(job_id=job.id, poll_interval=10)
print(f"Stage: {final.status.stage}")
```

#### 4.2 Schedule a UV Python Script to Run Weekly

```python
from huggingface_hub import create_scheduled_uv_job

scheduled = create_scheduled_uv_job(
    script="https://raw.githubusercontent.com/user/repo/main/train.py",
    script_args=["--epochs", "3", "--lr", "1e-4"],
    dependencies=["torch", "transformers", "datasets"],
    schedule="@weekly",
    flavor="t4-small",
    timeout="6h",
    name="weekly-finetune",
)
print(f"Scheduled: {scheduled.id}, next run at: {scheduled.status.next_job_run_at}")
```

#### 4.3 Stream Real-Time Job Logs

```python
from huggingface_hub import run_job, fetch_job_logs

job = run_job(image="python:3.12", command=["python", "-c", "print('Hello!')"])

# Stream logs in real-time (blocking)
for line in fetch_job_logs(job_id=job.id, follow=True):
    print(line)
```

#### 4.4 Mount Datasets and Buckets as Volumes

```python
from huggingface_hub import Volume, run_job

volumes = [
    Volume(type="dataset", source="HuggingFaceFW/fineweb", mount_path="/data"),
    Volume(type="bucket", source="username/my-bucket", mount_path="/output"),
]

job = run_job(
    image="duckdb/duckdb",
    command=["duckdb", "-c", "COPY (SELECT * FROM '/data/**/*.parquet' LIMIT 5) TO '/output/sample.parquet'"],
    volumes=volumes,
)
```

#### 4.5 Run an Ephemeral Inference Server

```python
job = run_job(
    image="vllm/vllm-openai",
    command=["vllm", "serve", "Qwen/Qwen2-0.5B", "--host", "0.0.0.0", "--port", "8000"],
    flavor="l4x1",
    expose=[8000],
    ssh=True,
    name="ephemeral-vllm",
)

# The server is now reachable at https://{job.id}--8000.hf.jobs
# Requires Bearer token with read access to namespace
print(f"Model server: {job.status.expose_urls[0]}")
```

#### 4.6 Create a Cron-Job with Labels and Monitoring

```python
scheduled = create_scheduled_job(
    image="python:3.12",
    command=["python", "-c", "print('Daily health check')"],
    schedule="@daily",
    labels={"env": "production", "team": "ml"},
    concurrency=False,
    timeout="5m",
)

# Monitor with labels
from huggingface_hub import list_jobs
for job in list_jobs(labels={"env": "production"}):
    print(f"{job.id}: {job.status.stage}")

# Trigger immediate run
from huggingface_hub import trigger_scheduled_job
triggered = trigger_scheduled_job(scheduled_job_id=scheduled.id)
```

#### 4.7 Full Lifecycle: Schedule → Suspend → Resume → Delete

```python
s = create_scheduled_job(image="python:3.12", command=["echo", "hello"], schedule="@hourly")

# Pause (suspend)
suspend_scheduled_job(scheduled_job_id=s.id)

# Resume
resume_scheduled_job(scheduled_job_id=s.id)

# List all schedules
schedules = list_scheduled_jobs()

# Inspect a specific one
info = inspect_scheduled_job(scheduled_job_id=s.id)

# Delete when no longer needed
delete_scheduled_job(scheduled_job_id=s.id)
```

---

### 5. Key Differences from the CLI

| Feature | CLI (`hf jobs`) | Python SDK |
|---------|----------------|------------|
| Run Docker | `hf jobs run <image> <cmd>` | `run_job(image, command)` |
| Run UV script | `hf jobs uv run script.py` | `run_uv_job(script, deps)` |
| Schedule | `hf jobs scheduled uv run @daily script.py` | `create_scheduled_uv_job(script, schedule="@daily")` |
| List jobs | `hf jobs ps` | `list_jobs()` (returns generator) |
| Stream logs | `hf jobs logs <id>` | `fetch_job_logs(id, follow=True)` |
| Metrics | `hf jobs stats <id>` | `fetch_job_metrics(id)` |
| Wait | `hf jobs wait <id>` | `wait_for_job(id)` |
| SSH into job | `hf jobs ssh <id>` | No Python equivalent (use CLI or direct SSH) |
| Hardware list | `hf jobs hardware` | `list_jobs_hardware()` |
| Named jobs | Added via CLI automatically | Must pass `name="..."` explicitly |
| `--detach` | Default in CLI | Always non-blocking (returns immediately) |

---

### 6. Edge Cases & Limitations

- **No `run_uv_job` for one-shot** (only scheduled): `run_uv_job` exists but is `@experimental`; the stable one-shot is `run_job` with a regular Docker image
- **No Python API for `hf jobs ssh`**: SSH connections require CLI or direct SSH client
- **Scheduled jobs don't support SSH**: `ssh=True` parameter exists on `run_job` but is not present on `create_scheduled_job` (no SSH for cron jobs)
- **Labels are replaced, not merged**: `update_scheduled_job_labels()` does a full replace
- **No `run_job` with `schedule`**: scheduling and running are separate APIs — create a schedule, then trigger it if you want immediate + recurring
- **Job names are NOT unique**: The `name` field is just a label, not an identifier — use `job.id` for uniqueness
- **Billing**: Requires positive credit balance at `/settings/billing`
- **Volume sync**: Local dir volumes sync to `jobs-artifacts` bucket; hash-based naming from `_derive_job_volume_name` ensures consistent paths per machine+dir

---

### 7. Source

- `huggingface_hub` v1.24.0 installed at `/opt/data/.venv-sakthai/lib/python3.14/site-packages/huggingface_hub/`
- Core API dataclasses: `_jobs_api.py` (573 lines)
- API methods: `hf_api.py` lines 11802–13200+
- Hub API reference: `https://huggingface.co/docs/hub/en/jobs`
- Pricing: `https://huggingface.co/pricing`

### Skill Created

`hf-jobs-api-deep-dive/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with source-level API reference.
