# HF Learnings — HF Sandboxes v3: Background Processes, Port Proxy, Pool Management, and Source Architecture

## 2026-07-25: hf-sandboxes-v3-deep-dive — Hugging Face Sandbox API: Complete Source Architecture & Advanced Patterns (Topic #327)

### Summary
Source-code-level deep dive into the complete Hugging Face Sandboxes system as of `huggingface_hub v1.24.0` (released 2026-07-17). The sandbox API has evolved significantly since the initial deep-dive (Topic #148), gaining background process support (v1.22.0), port proxy for in-sandbox servers (v1.22.0), SandboxPool with cache persistence and cross-process host discovery (v1.22.0), and parallel file transfers for large files. The system is built entirely on HF Jobs — a sandbox is just a Job running a ~640KB static Rust binary (`sbx-server`), with no dedicated infrastructure beyond the Job API. This document covers the full 1764-line `_sandbox.py` module, the 159-line `_sandbox_cache.py` module, and the 480-line CLI surface.

### Source Files Analyzed

| File | Lines | Purpose |
|------|-------|---------|
| `huggingface_hub/_sandbox.py` | 1764 | Core Sandbox + SandboxPool implementation |
| `huggingface_hub/_sandbox_cache.py` | 159 | Best-effort pool cache for cross-process host reuse |
| `huggingface_hub/cli/sandbox.py` | 480 | CLI commands (`hf sandbox *`) |
| `huggingface_hub/errors.py` | 609 | SandboxError, SandboxCommandError exception types |

### Public API

```python
from huggingface_hub import Sandbox, SandboxPool, SandboxCommandResult, SandboxProcess
from huggingface_hub.errors import SandboxError, SandboxCommandError
```

---

### 1. Architecture Overview

Sandboxes have **zero dedicated infrastructure** — they are HF Jobs running a static Rust binary. This design choice means they inherit Jobs' billing, hardware flavors (cpu-basic → H200), namespace permissions, and volume system for free.

```
User Code
  ↓
Sandbox.create() / SandboxPool.create()
  ↓
HfApi.run_job()       ← Jobs API creates a VM
  │  [image: python:3.12, flavor: cpu-basic, expose: 49983]
  ↓
Job starts on infra
  │  Bootstrap script (wget/curl sbx-server binary)
  │  Token auth via HMAC-SHA256
  ↓
sbx-server (Rust binary) running on port 49983
  │  Hand-rolled HTTP/1.1 server
  │  NDJSON event streams for exec
  │  /health, /exec, /files/*, /processes, /proxy/*, /v1/sandboxes/*
  ↓
Sandbox._server (httpx.Client) → base_url/job-id--49983.hf.jobs
```

**Two modes:**

| Mode | Class | Isolation | GPU | Cold Start | Cost Profile |
|------|-------|-----------|-----|------------|--------------|
| Dedicated | `Sandbox.create()` | Full VM | ✅ Yes | ~5-7s | One Job per sandbox |
| Shared/Pooled | `SandboxPool.create()` | uid + Landlock LSM | ❌ No | ~1ms server-side | Many sandboxes per host VM |

**Bootstrap sequence (in `/bin/sh`):**
1. Download `sbx-server` from HF bucket with `wget`/`curl` (fast ~6s cold start)
2. Fallback: read from always-mounted server bucket via FUSE (+2-3s)
3. Execute binary on port 49983 with derived auth token
4. Server starts, begins health-check polling
5. `Sandbox` client polls `/health` until 200 → ready

**Key constants:**
```python
SANDBOX_SERVER_PORT = 49983      # In-job server port (deliberately uncommon)
SANDBOX_LABEL = "hf-sandbox"     # Label on every sandbox job
MODE_LABEL = "hf-sandbox-mode"   # "dedicated" or "pool"
MODE_DEDICATED = "dedicated"
MODE_POOL = "pool"
POOL_LABEL = "hf-sandbox-pool"   # Pool name label
NONCE_LABEL = "hf-sandbox-nonce" # Public nonce for token derivation
DEFAULT_IMAGE = "python:3.12"
DEFAULT_IDLE_TIMEOUT = 600       # 10 minutes
SANDBOX_MAX_LIFETIME = "24h"     # Absolute max job lifetime
DEFAULT_SANDBOXES_PER_HOST = 50  # Pool sandboxes per host VM
SHARED_ID_SEP = "."              # Separator in shared sandbox ids: <host_job_id>.<local_id>
```

---

### 2. Stateless Authentication System

Sandbox auth is **entirely stateless** — no database, no stored tokens, no session state.

**Two-layer security:**
1. **Transport layer (proxy gate):** The Jobs proxy (`.hf.jobs`) validates the user's HF token — only authenticated users can reach the sandbox server
2. **Application layer (sandbox gate):** A per-sandbox HMAC-SHA256 token, derived from the user's HF token + a public nonce, authenticates every API request inside the sandbox

**Token derivation (never sends HF token to sandbox):**
```python
def _derive_sandbox_token(hf_token: str, nonce: str) -> str:
    return hmac.new(
        hf_token.encode(),
        f"hf-sandbox:{nonce}".encode(),
        hashlib.sha256
    ).hexdigest()
```

**Flow during creation:**
1. Client generates random `nonce = token_hex(16)`
2. Client computes `sandbox_token = _derive_sandbox_token(hf_token, nonce)`
3. Nonce is stored as the `hf-sandbox-nonce` job label (public)
4. Sandbox token is sent as `SBX_TOKEN` in job secrets (encrypted server-side)
5. When reconnecting: read nonce from job labels, recompute token locally
6. HTTP requests carry: `Authorization: Bearer {hf_token}` + `X-Sandbox-Token: {sandbox_token}`

**Reconnection from any machine:**
```python
# No local state needed — token is recomputed from job metadata
sandbox = Sandbox.connect("job_id_here")
```
The server validates both headers: the HF token (proxy gate) and the sandbox token (application gate). If the HF token changes (e.g., regenerated), reconnection fails — the sandbox token is bound to the original HF token via HMAC.

---

### 3. Data Structures

#### SandboxCommandResult
```python
@dataclass
class SandboxCommandResult:
    exit_code: int | None
    stdout: str
    stderr: str
    signal: int | None = None
    timed_out: bool = False
    duration_ms: int = 0

    @property
    def ok(self) -> bool:
        return self.exit_code == 0
```

#### SandboxProcess (background processes, v1.22.0+)
```python
@dataclass
class SandboxProcess:
    pid: int
    cmd: str | List[str]
    _sandbox: "Sandbox"  # back-reference for kill(), excluded from repr/eq
    tag: str | None = None
    started_at_ms: int | None = None
    running: bool = True
    exit_code: int | None = None

    def kill(self) -> None:
        """Terminate the background process (idempotent server-side)."""
        self._sandbox._request("DELETE", f"/processes/{self.pid}")
```

#### FileEntry
```python
@dataclass
class FileEntry:
    name: str
    path: str
    type: Literal["file", "dir", "symlink"]
    size: int
    mtime_ms: int | None = None
    mode: str = ""
```

#### _SandboxServer (internal transport)
```python
class _SandboxServer:
    """HTTP transport to one sbx-server instance — a dedicated job or a shared host."""
    def __init__(self, *, job_id, owner, image, base_url, nonce,
                 sandbox_token, api, max_connections=10, capacity=0):
        self.job_id = job_id
        self.owner = owner
        self._image = image
        self.base_url = base_url
        self.nonce = nonce
        self._api = api
        self._auth_token = _effective_token(api)
        self._sandbox_token = sandbox_token
        self.capacity = capacity     # Max sandboxes this host can pack (pool mode)
        self.live = 0                # Current sandbox count
        self.verified = True         # False for hosts from cache (unverified)

        # Single httpx.Client for all operations (thread-safe!)
        self._client = httpx.Client(
            headers={"Authorization": f"Bearer {self._auth_token}",
                     "X-Sandbox-Token": sandbox_token},
            limits=httpx.Limits(max_connections=max_connections,
                                max_keepalive_connections=max_connections),
            follow_redirects=True,
        )
```

#### CachedHost & PoolCache (cache layer)
```python
@dataclass
class CachedHost:
    job_id: str
    owner: str
    base_url: str           # Does not change while the job lives
    nonce: str              # For re-deriving sandbox token
    capacity: int           # Max sandboxes
    live: int               # Last observed count (may be stale)
    updated_at: float = 0.0

@dataclass
class PoolCache:
    pool_id: str
    image: str
    flavor: str
    sandboxes_per_host: int
    max_hosts: int | None
    idle_timeout: int | None
    namespace: str | None
    hosts: List[CachedHost] = field(default_factory=list)
    version: int = 1
    updated_at: float = 0.0
```

---

### 4. Sandbox (Dedicated Mode)

#### Creating a Dedicated Sandbox

```python
Sandbox.create(
    image: str = "python:3.12",
    flavor: str = "cpu-basic",
    idle_timeout: int | float | str | None = 600,
    env: dict[str, Any] | None = None,
    secrets: dict[str, Any] | None = None,
    volumes: List[Volume] | None = None,
    namespace: str | None = None,
    forward_hf_token: bool = False,
    start_timeout: float = 120.0,
    token: str | None = None,
) -> Sandbox
```

**Creation flow (source `_sandbox.py` lines 512-611):**
1. Generate random nonce + derive sandbox token
2. Build job spec via `_bootstrap_job_spec()` — generates bootstrap command, env vars, secrets, volumes
3. Call `api.run_job()` with `image`, `flavor`, command, env, secrets, labels (SANDBOX_LABEL, MODE_DEDICATED, NONCE_LABEL), volumes, and `expose=[SANDBOX_SERVER_PORT]`
4. Build `_SandboxServer` from returned job info (`from_job()`)
5. Wait for server readiness via `wait_ready(start_timeout)` — polls `/health` every 150ms, checks job stage every 2s
6. If startup fails: cancel the job (cleanup billable resource) before re-raising
7. Returns `Sandbox(id=job.id, server=server, local_id=None, owns_sandbox=True, owns_server=True)`

**Recovery from failed startup:**
```python
# In Sandbox.create(), lines 601-610:
except Exception:
    try:
        api.cancel_job(job_id=job.id, namespace=job.owner.name)
    except Exception as e:
        logger.warning(f"Failed to cancel sandbox job {job.id} after startup failure: {e}")
    if server is not None:
        server.close()
    raise
```

#### Reconnecting

```python
Sandbox.connect(sandbox_id: str, *, namespace: str | None = None,
                token: str | None = None) -> Sandbox
```

**Two paths (source lines 613-650):**
- **Shared sandbox** (`.` in id): Split `host_job_id.local_id`, connect to host, verify local_id exists on host
- **Dedicated sandbox**: Inspect job by id, verify it's a sandbox (has SANDBOX_LABEL), verify it's still RUNNING, recompute token from nonce, build server transport

Returns a Sandbox with `owns_sandbox=False` (exiting `with` block won't kill it).

#### Running Commands

```python
# Foreground (waits for completion, streams output live)
result: SandboxCommandResult = sbx.run(
    cmd="python train.py --epochs 10",
    shell=True,                          # infer from cmd type: True for str
    env={"LR": "0.001"},                 # extra env vars for this command
    cwd="/workspace",                    # working directory
    timeout=300.0,                       # kill after this many seconds
    stdin="y\n",                         # stdin data
    on_stdout=lambda chunk: print(chunk, end=""),  # live stdout callback
    on_stderr=lambda chunk: print(chunk, end=""),  # live stderr callback
    check=True,                          # raise SandboxCommandError on non-zero exit
)

# Background (returns immediately, process runs detached)
process: SandboxProcess = sbx.run(
    cmd="uvicorn app:app --host 0.0.0.0 --port 8000",
    background=True,
)
```

**Execution architecture (source lines 725-816):**
- Foreground: POST `/v1/exec` (or `/v1/sandboxes/<local_id>/exec` in pool mode) with NDJSON streaming
  - Server sends events: `stdout`, `stderr`, `exit`
  - Client accumulates stdout/stderr in lists
  - On `exit` event: construct SandboxCommandResult with exit_code, stdout, stderr, signal, timed_out, duration_ms
  - If check=True and non-zero exit: raise SandboxCommandError
- Background: POST `/v1/processes` (returns just `{"pid": N, "tag": "..."}`)

**NDJSON event stream format:**
```json
{"event": "stdout", "data": "Hello "}
{"event": "stdout", "data": "World\n"}
{"event": "exit", "exit_code": 0, "signal": null, "timed_out": false, "duration_ms": 45}
```

Keepalive pings (every 15s from server) are filtered out:
```python
def _iter_events(response):
    for line in response.iter_lines():
        if not line:
            continue
        event = json.loads(line)
        if event.get("event") != "ping":
            yield event
```

#### Background Process Management (v1.22.0+)

```python
# List all background processes
processes: List[SandboxProcess] = sbx.processes()

# Stop a specific process
proc = sbx.run("python long_task.py", background=True)
proc.kill()   # DELETE /processes/{pid}

# Process properties
proc.pid           # int
proc.cmd           # original command
proc.running       # bool
proc.exit_code     # None if still running, int if completed
proc.tag           # optional user tag
proc.started_at_ms # timestamp
```

Completed processes stay in the listing (with `running=False` and `exit_code`) until the sandbox is deleted.

#### File Operations

```python
sbx.files.read(path) -> bytes              # GET /files/read?path=...
sbx.files.read_text(path) -> str           # wrapper around read()
sbx.files.write(path, data, mode=None)     # PUT /files/write
sbx.files.upload(local_path, path)         # upload local file
sbx.files.download(path, local_path)       # download to local file
sbx.files.list(path) -> List[FileEntry]    # GET /files/list
sbx.files.stat(path) -> FileEntry          # GET /files/stat
sbx.files.exists(path) -> bool             # check existence
sbx.files.delete(path, recursive=False)    # DELETE /files/delete
sbx.files.mkdir(path)                      # POST /files/mkdir
```

**Path semantics:**
- **Dedicated mode**: paths are absolute on the container filesystem
- **Pool (shared) mode**: paths are rooted at the sandbox's private home directory — a leading `/` is taken relative to that home

#### Parallel File Transfers (v1.22.0+)

Files >2MB are automatically transferred using parallel ranged requests for bandwidth aggregation:

```python
class SandboxFiles:
    PARALLEL_THRESHOLD = 2 * 1024 * 1024   # 2MB — above this, use parallel
    PARALLEL_CHUNK_SIZE = 1 * 1024 * 1024  # 1MB per chunk
    PARALLEL_MAX_WORKERS = 16              # up to 16 concurrent connections
```

The parallel transfer uses `ThreadPoolExecutor` with ranged GET/PUT requests:
```python
def _read_ranges(self, path, size):
    def fetch(rng):
        offset, length = rng
        response = self._sandbox._request(
            "GET", "/files/read",
            params={"path": path, "offset": offset, "length": length}
        )
        return response.content
    return self._parallel(self._ranges(size), fetch)
```

This compensates for the per-TCP-stream bandwidth-delay product limitation (~2 MiB/s at ~100ms RTT through the Jobs proxy).

#### Port Proxy (v1.22.0+)

Allows accessing a server running *inside* the sandbox from outside:

```python
url = sandbox.proxy_url_for(
    port=8000,
    path="/api/health",
    scheme="https://"        # or "wss://" for WebSocket
)
# Returns: https://<job_id>--49983.hf.jobs/v1/proxy/8000/api/health

headers = sandbox.proxy_headers
# Returns: {"Authorization": "Bearer <hf_token>",
#           "X-Sandbox-Token": "<sandbox_token>"}
```

**Pool vs dedicated differences:**
- **Pool/shared sandbox**: Cannot bind TCP (Landlock restriction). Must bind a **unix socket** at `$SBX_PROXY_DIR/<port>.sock`:
  ```python
  # Inside sandbox:
  import uvicorn
  uvicorn.run(app, uds=f"{os.environ['SBX_PROXY_DIR']}/8000.sock")
  ```
- **Dedicated sandbox**: Bind normal TCP port on `127.0.0.1:<port>` (can also expose directly via job proxy without port proxy)

**WebSocket support:**
```python
url = sandbox.proxy_url_for(8000, "/ws", scheme="wss://")
import websockets
async with websockets.connect(url, additional_headers=sandbox.proxy_headers) as ws:
    await ws.send("hello")
```

The proxy is protocol-agnostic — only the client-side scheme changes.

---

### 5. SandboxPool (Shared/Pooled Mode)

SandboxPool packs many lightweight sandboxes onto shared host VMs, each isolated by uid + Landlock LSM. One host = one HF Job (a VM). Up to 50 sandboxes per host by default.

#### Creating a Pool

```python
pool = SandboxPool(
    image="python:3.12",
    flavor="cpu-basic",
    sandboxes_per_host=50,
    warm_up=1,                # Pre-provision 1 host in constructor
    max_hosts=None,           # Optional cost ceiling
    name=None,                # Random if omitted (e.g. "pool-ab12cd34ef56")
    idle_timeout=600,         # Host idle timeout (no sandboxes → shutdown)
    namespace=None,
    start_timeout=120.0,
    token=None,
)
```

The constructor blocks until `warm_up` hosts are ready. Uses threading locks to serialize concurrent operations.

#### Creating Sandboxes in a Pool

```python
with SandboxPool(image="python:3.12", warm_up=2) as pool:
    boxes = [pool.create(env={"WORKER_ID": str(i)})
             for i in range(100)]   # Packed across warm hosts
    print(boxes[0].run("echo hi").stdout)
```

`pool.create()` (source lines 1134-1235) implements a **pack-retry loop**:

1. **Reserve** a slot on a known host with free capacity (`host.live < host.capacity`)
2. **Discover** warm hosts via job labels if no capacity (one-shot per create)
3. **Boot** a new host if still no capacity (under `_boot_lock` to serialize)
4. **Create** sandbox on reserved host via `POST /v1/sandboxes`
5. **Retry** (up to `_MAX_PACK_ROUNDS=8`) if host filled between reservation and create
6. **Rollback** all newly booted hosts if any step fails

**Key design decisions:**
- `_boot_lock` serializes host creation — a burst of `create()` calls queue here, and each new host frees `sandboxes_per_host` slots for waiting threads
- `_adopt_pending_host()` detects hosts already `SCHEDULING` for this pool (started by another process or earlier create) and waits for them instead of booting duplicates
- All-or-nothing teardown: if `create()` fails after booting new hosts, cancel them to prevent billing leaks

#### Pool Reconnection

```python
# Reattach to a pool from any machine
pool = SandboxPool.connect("pool-ab12cd34ef56")
sandbox = pool.create()  # uses existing warm hosts
```

**Two paths (source lines 1052-1105):**
1. **Fast path**: Local cache hit → rebuild pool from `PoolCache` with no HTTP. Hosts are verified lazily on first `create()`
2. **Cold path**: Find running host via job labels (`MODE_LABEL=pool` + `POOL_LABEL`), rebuild config from host's env vars (`SBX_CAPACITY`, `SBX_IDLE_TIMEOUT`, `SBX_MAX_HOSTS`)

#### Warming Hosts

```python
pool.warm(num_hosts=2)
# Pre-provisions 2 empty hosts (or adopts existing ones). Returns list of host job ids.
```

Creates hosts that carry the pool label and config in env vars. Cross-process discoverable: another machine can `SandboxPool.connect(pool_id)` and find them. Hosts persist until killed or idle-timed-out.

#### Pool Properties

```python
pool.num_hosts      # int — host jobs provisioned
pool.num_sandboxes  # int — sandboxes currently handed out
pool.host_ids       # List[str] — host job ids
```

#### Pool Cleanup

```python
pool.close()  # For owned pools: cancels all host jobs + sandboxes, deletes cache
              # For connect()'d handles: releases HTTP clients only, leaves hosts running

# Context manager:
with SandboxPool(...) as pool:
    ...
# Automatically calls close()
```

---

### 6. Pool Cache System (v1.22.0+)

The cache lives at `~/.cache/huggingface/sandbox/pools/<pool_id>.json` with a companion `.lock` file.

**Cache operations (source `_sandbox_cache.py`):**
```python
# Read: returns None if missing/corrupt/incompatible version
cache = read_pool_cache(pool_id)  # → PoolCache | None

# Write: upserts hosts by job_id, removes dead_host_ids, atomic write
save_pool_cache(pool_id, image=..., flavor=..., sandboxes_per_host=...,
                max_hosts=..., idle_timeout=..., namespace=...,
                hosts=[CachedHost(...)], dead_host_ids={"job_id_1"})

# Delete: removes cache file
delete_pool_cache(pool_id)
```

**Cache design principles:**
- **Best-effort**: Save failures are logged but never raised. Read failures silently return None.
- **Concurrency-safe**: Uses `WeakFileLock` with 5s timeout. Read-merge-write: reads existing, upserts by job_id, removes dead hosts.
- **Atomic writes**: Writes to temp file then `os.replace()` — readers never see partial content.
- **Versioned**: Cache version `_CACHE_VERSION=1` — incompatible versions are silently dropped.

**Dead host pruning:** Hosts found dead during this session are tracked in `self._dead_host_ids` and removed from the cache on save. This prevents stale entries from lingering.

**Cross-process sharing flow:**
```
Process A           → Creates SandboxPool → warms hosts → saves cache
Process B           → SandboxPool.connect() → reads cache (zero HTTP)
Process B.create()  → First request to cached host → succeeds → host verified
                     └─ Host gone → drops it, discovers via labels, boots replacement
```

---

### 7. Host Discovery & Cross-Process Sharing

Pools use **label-based discovery** via the Jobs API to find hosts across processes:

```python
def _discover_hosts(self):
    known = {host.job_id for host in self._hosts}
    matches = [
        job for job in self._api.list_jobs(
            status="RUNNING",
            labels={MODE_LABEL: MODE_POOL, POOL_LABEL: self.name},
            namespace=self._namespace,
        )
        if job.id not in known
    ]
    for job in matches:
        server = _connect_host(self._api, job.id, namespace=self._namespace)
        # Read host's actual capacity from env, live count from server
        server.capacity = int(env.get("SBX_CAPACITY", self.sandboxes_per_host))
        server.live = len(server.request("GET", "/v1/sandboxes").json())
        self._hosts.append(server)
```

**Cross-process adoption prevents over-provisioning:**
```python
def _adopt_pending_host(self):
    """Find a host already SCHEDULING for this pool → wait for it instead of booting."""
    pending = next((
        job for job in self._api.list_jobs(
            status="SCHEDULING",
            labels={MODE_LABEL: MODE_POOL, POOL_LABEL: self.name},
            namespace=self._namespace,
        )
        if job.id not in known
    ), None)
    # Wait for it to reach RUNNING + server ready
```

---

### 8. Parallel Host Provisioning

When multiple hosts need to be booted (e.g., `warm_up=4`), they are booted in parallel:

```python
def _provision_hosts(self, num_new: int) -> List[_SandboxServer]:
    with ThreadPoolExecutor(max_workers=min(num_new, 32)) as executor:
        futures = [executor.submit(self._boot_host) for _ in range(num_new)]
    # Collect all results; if any fail, cancel all booted hosts
    booted: List[_SandboxServer] = []
    error: Exception | None = None
    for future in futures:
        try:
            booted.append(future.result())
        except Exception as e:
            error = e
    if error is not None:
        for server in booted:
            server.cancel_job()  # Cancel already-booted hosts
        raise error
    return booted
```

---

### 9. CLI Surface (hf sandbox)

Full CLI parity with the Python API, auto-detecting agent mode for token-efficient output.

| Command | Purpose |
|---------|---------|
| `hf sandbox create [image]` | Create a dedicated sandbox (or shared with `--pool`) |
| `hf sandbox exec <id> -- <cmd>` | Run a command in an existing sandbox |
| `hf sandbox cp <src> <dst>` | Copy files to/from a sandbox |
| `hf sandbox spawn <id> -- <cmd>` | Start a background process |
| `hf sandbox process ls <id>` | List background processes |
| `hf sandbox process kill <id> <pid>` | Stop a background process |
| `hf sandbox kill <id>` | Terminate a sandbox |
| `hf sandbox pool create [name]` | Create a shared pool |
| `hf sandbox pool connect <id>` | Reattach to a pool |
| `hf sandbox pool delete <id>` | Delete a pool (terminates all hosts) |
| `hf sandbox pool ls` | List pools with running hosts |

**Key CLI features:**
- `--pool` flag on `hf sandbox create` for pooled mode
- `--flavor`, `--idle-timeout`, `--env`, `--secret`, `--volume` flags
- Auto-detects namespace from sandbox id format (`namespace/id`)
- Process commands work on both dedicated and pooled sandboxes

---

### 10. Resource Limits & Safety

| Constraint | Value | Where Enforced |
|------------|-------|----------------|
| Max sandbox lifetime | 24h | `SANDBOX_MAX_LIFETIME` constant |
| Default idle timeout | 10 min | `DEFAULT_IDLE_TIMEOUT = 600` |
| Default sandboxes per host | 50 | `DEFAULT_SANDBOXES_PER_HOST` |
| Max pack retries | 8 | `_MAX_PACK_ROUNDS` |
| Parallel transfer threshold | 2MB | `SandboxFiles.PARALLEL_THRESHOLD` |
| Max parallel workers | 16 | `SandboxFiles.PARALLEL_MAX_WORKERS` |
| Server port | 49983 | `SANDBOX_SERVER_PORT` |
| Wait timeout | 120s default | `start_timeout` parameter |
| Cache lock timeout | 5s | `_LOCK_TIMEOUT` in cache module |

**SandboxPool limits:**
- `max_hosts` provides a cost ceiling — when reached and all hosts are full, `create()` raises `SandboxError`
- Hosts auto-terminate on idle (no sandboxes) after `idle_timeout`
- `Sandbox.create()` dedicated sandboxes have no built-in limit beyond the 24h max lifetime

---

### 11. Error Handling

```python
# SandboxError — base for all sandbox-specific errors
from huggingface_hub.errors import SandboxError, SandboxCommandError

# Raised when run(check=True) exits non-zero
try:
    result = sbx.run("python failing_script.py")
except SandboxCommandError as e:
    print(f"Command failed: {e.cmd}")
    print(f"Exit code: {e.result.exit_code}")
    print(f"stderr: {e.result.stderr}")

# Generic sandbox errors (connection, auth, resource limits)
except SandboxError as e:
    print(f"Sandbox error: {e}")
    # Has .status_code attribute for HTTP-level errors
```

**Error recovery patterns from source:**
- Startup failure → cancel the job (prevents billing leak)
- Host unreachable from cache → drop host, fall back to discovery
- Host full between reservation and create → retry up to 8 rounds
- Partial host boot failure → cancel all booted hosts (all-or-nothing)
- Parallel transfer failure → standard httpx error propagation

---

### 12. Complete Request Lifecycle

```
User code
  ↓
Sandbox.create(image="python:3.12", flavor="cpu-basic")
  │
  ├─ HfApi.run_job()      ─── POST /api/jobs
  │   │                       Returns: JobInfo with expose_urls
  │   └─ Job labels: hf-sandbox=1, hf-sandbox-mode=dedicated, hf-sandbox-nonce=<nonce>
  │
  ├─ _SandboxServer.from_job() — reads base_url from expose_urls
  │
  ├─ Sandbox.wait_ready()
  │   │  Loop until /health returns 200 or job terminal:
  │   │  ├─ GET /health every 150ms
  │   │  └─ inspect_job every 2s (check for terminal stage)
  │   └─ On terminal: read last 20 log lines, raise SandboxError
  │
  ├─ Return Sandbox(id=job.id, server=..., owns_sandbox=True)
  │
  ├─ sbx.run("python train.py")
  │   │
  │   └─ POST /v1/exec
  │       │  Streaming NDJSON:
  │       │  {"event": "stdout", "data": "Epoch 1/10..."}
  │       │  {"event": "stdout", "data": "Loss: 0.23"}
  │       │  {"event": "exit", "exit_code": 0, "duration_ms": 45000}
  │       └─ Return SandboxCommandResult(exit_code=0, stdout=..., stderr=...)
  │
  ├─ sbx.files.download("/output/model.pt", "./model.pt")
  │   │
  │   └─ Parallel GET /files/read with ranged requests (>2MB)
  │
  └─ sbx.kill()  (or exiting `with` block)
      │
      └─ _server.cancel_job()  ─── POST /api/jobs/{id}/cancel
          └─ _server.close() — close httpx.Client
```

---

### 13. Best Practices

**Context managers prevent billing leaks:** Always use `with` blocks — the `__exit__` cancels the job on any exception, so a crash mid-computation doesn't leave a billable orphan:
```python
with Sandbox.create(flavor="a10g-small") as sbx:
    sbx.run("python train.py")  # any exception → job cancelled
```

**Pre-provision pool hosts for latency-sensitive workloads:** `warm_up=3` pre-boots hosts in the constructor. Without it, the first `create()` pays a cold start.

**Use `--pool` for CPU fan-out:** A pooled sandbox costs ~$0.0009 each (amortized across 50 per host) vs ~$0.06 for a dedicated one.

**Large files auto-parallelize:** Files >2MB use 16 concurrent ranged connections. No manual tuning needed.

**Set `idle_timeout` aggressively:** The default 10 minutes is generous for most workloads. Shorten to `"30s"` or `60` for bursty batch jobs to reclaim resources faster.

**Forward HF token sparingly:** `forward_hf_token=True` injects your token into the sandbox as `HF_TOKEN`. Only enable when the code inside needs Hub access (e.g., pushing models).

**Verify sandbox is running before connecting:** `Sandbox.connect()` inspects the job — if it's in a terminal stage, it raises immediately with the status message.

**Use `sbx.run(background=True)` for servers:** Start a web server or API in the background, then use `sbx.proxy_url_for()` to reach it from outside.

---

### Sources

- Source code: `huggingface_hub/_sandbox.py` (1764 lines, v1.24.0) — complete Sandbox and SandboxPool implementation
- Source code: `huggingface_hub/_sandbox_cache.py` (159 lines, v1.24.0) — pool cache persistence
- Source code: `huggingface_hub/cli/sandbox.py` (480 lines, v1.24.0) — CLI implementation
- Source code: `huggingface_hub/errors.py` (609 lines, v1.24.0) — SandboxError + SandboxCommandError
- Official docs: https://huggingface.co/docs/huggingface_hub/guides/sandbox
- Official docs: https://huggingface.co/docs/huggingface_hub/package_reference/sandbox
- GitHub: https://github.com/huggingface/sandbox-server (sbx-server Rust binary)
- Release notes: huggingface_hub v1.22.0 (SandboxPool, background processes, port proxy)
