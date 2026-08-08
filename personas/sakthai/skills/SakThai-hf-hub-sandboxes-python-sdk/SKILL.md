---
name: SakThai-hf-hub-sandboxes-python-sdk
description: ">-   Comprehensive deep-dive into the Hugging Face Hub Sandboxes Python SDK   (huggingface_hub v1.24.0+) — Sandbox and SandboxPool classes, CLI commands,   stateless HMAC auth, uid+Landlock pool isolation, file API, proxy for inner   servers, lifecyc"
---
# Hugging Face Sandboxes Python SDK — Deep Dive

## Overview

**HF Sandboxes** (available in `huggingface_hub` v1.24.0+) let you spin up
isolated cloud machines in seconds and interact with them from Python or the
CLI. Each sandbox is an **HF Job** (a VM) running a tiny static server
(`sbx-server`) that exposes command execution, file transfer, and port proxy
over HTTP.

Two kinds of sandbox:
- **Dedicated** (`Sandbox.create()`) — one Job = one sandbox (full VM, GPU-capable)
- **Pooled/shared** (`SandboxPool`) — one VM hosts many Landlock-isolated sandboxes

### Why This Matters

Sandboxes solve a fundamental need: running code somewhere that isn't your
machine. They're ideal for:
- Running untrusted or AI-generated code safely
- Reproducible builds and experiments
- Fanning out parallel work (RL rollouts, evaluation, batch execution)
- Agentic tool use and code execution

Because they're built on Jobs, they inherit billing, hardware flavors, and
namespace permissions for free.

---

## Architecture: "No New Service"

There is no dedicated sandbox backend. A sandbox is **just an HF Job running
`sbx-server`** — a ~640KB static musl Rust binary with zero runtime
dependencies. The client talks to it through the Jobs proxy (`*.hf.jobs`).

### Server Bootstrap

At job startup, a small `/bin/sh -c` script fetches `sbx-server` from the HF
CDN (fast path via `wget`/`curl`), or reads it off a mounted volume as fallback
(slower by ~2-3s). Then it execs the server, which listens on port **49983** (an
uncommon port so dev ports stay free).

### Authentication (Stateless HMAC)

Two layers protect a sandbox:

1. **Jobs proxy gate** — only requests with an HF token that has read access to
   the namespace reach the VM.
2. **sbx-server application gate** — checks a per-sandbox `X-Sandbox-Token` on
   every request.

The token is derived (not stored):

```
nonce  = random 128-bit hex (in job label "hf-sandbox-nonce")
token  = HMAC-SHA256(key=your_hf_token, msg="hf-sandbox:" + nonce)
```

Consequences:
- **Stateless reconnection**: `Sandbox.connect(id)` works from any machine with
  the same HF token — no local files needed.
- **HF token never enters the sandbox** (unless `forward_hf_token=True`).
- **Per-sandbox scope**: leaking one token compromises that sandbox only.

---

## Sandbox Class API

### Creating a Dedicated Sandbox

```python
from huggingface_hub import Sandbox

# Simplest form (python:3.12, cpu-basic, 10min idle timeout)
with Sandbox.create() as sbx:
    result = sbx.run("python -c 'print(40 + 2)'")
    print(result.stdout)  # "42"

# With custom image and GPU
sbx = Sandbox.create(
    image="pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel",
    flavor="a10g-small",           # GPU flavor
    idle_timeout="30m",            # 30 min idle before shutdown
    env={"LOG_LEVEL": "debug"},
    secrets={"API_KEY": "sk-..."}, # encrypted server-side
    volumes=[Volume(...)],          # mount HF repos/buckets
    forward_hf_token=True,          # inject HF_TOKEN inside
    namespace="beer-sakthai",
)
```

#### Sandbox.create() Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `image` | `python:3.12` | Any Docker image with `/bin/sh` |
| `flavor` | `cpu-basic` | Hardware flavor (see `hf jobs hardware`) |
| `idle_timeout` | `600` (10 min) | Idle shutdown timeout; `None` to disable |
| `env` | `None` | Environment variables |
| `secrets` | `None` | Encrypted env vars (server-side) |
| `volumes` | `None` | HF repos/buckets to mount (`Volume(...)`) |
| `namespace` | `None` | User/org namespace (defaults to current user) |
| `forward_hf_token` | `False` | Inject `HF_TOKEN` into sandbox (opt-in) |
| `start_timeout` | `120.0` | Max seconds to wait for sandbox readiness |
| `token` | `None` | HF token override |

### Running Commands

```python
# Shell string → runs through /bin/sh -c (supports pipes, globs, $VARS)
sbx.run("pip install -q numpy && python -c 'import numpy; print(numpy.__version__)'")

# Argv list → exec'd directly (no quoting surprises, safe for user input)
sbx.run(["python", "-c", "import numpy; print(numpy.__version__)"])

# Mode inference: str=shell, list=exec. Override explicitly:
sbx.run("echo $HOME && ls | wc -l", shell=True)   # force shell
sbx.run(["git", "commit", "-m", msg], shell=False) # force exec

# Live output streaming
sbx.run("make -j4", on_stdout=print, on_stderr=print)

# Non-zero exit handling
result = sbx.run("test -f /tmp/missing", check=False)
print(result.exit_code)  # 1

# Background process (for servers, watchers)
proc = sbx.run("python -m http.server 8000", background=True)
print(proc.pid, proc.running)
```

#### SandboxCommandResult

| Field | Type | Description |
|-------|------|-------------|
| `exit_code` | `int \| None` | Exit code (None if still running) |
| `stdout` | `str` | Standard output |
| `stderr` | `str` | Standard error |
| `signal` | `int \| None` | Signal if killed |
| `timed_out` | `bool` | Whether command timed out |
| `duration_ms` | `int` | Wall-clock duration |

### Background Processes

```python
# Start a server in background
proc = sbx.run("python -m http.server 8000", background=True)

# List all processes
for p in sbx.processes():
    print(f"PID {p.pid}: {'running' if p.running else f'exited ({p.exit_code})'}")

# Kill a specific process
proc.kill()
```

### File API

```python
# Write content (str, bytes, or file-like)
sbx.files.write("/app/script.py", "print('hi')")

# Read content
text = sbx.files.read_text("/app/script.py")

# Upload/download
sbx.files.upload("local_data.csv", "/data/data.csv")     # local → sandbox
sbx.files.download("/data/results.bin", "results.bin")    # sandbox → local

# List directory
entries = sbx.files.list("/data")
for e in entries:
    print(f"{e.name} ({e.type}, {e.size} bytes)")

# Other helpers
sbx.files.stat("/data/data.csv")   # FileEntry
sbx.files.exists("/app/script.py") # bool
sbx.files.mkdir("/app/output")     # create directory
sbx.files.delete("/tmp/old.log")   # delete file
```

#### FileEntry Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | File name |
| `path` | `str` | Full path |
| `type` | `'file' \| 'dir' \| 'symlink'` | Entry type |
| `size` | `int` | Size in bytes |
| `mtime_ms` | `int \| None` | Modification timestamp |
| `mode` | `str` | Unix permissions string |

### Proxying to Inner Servers

Start a server inside the sandbox, then reach it from outside via the Jobs proxy.

```python
import httpx

with Sandbox.create() as sbx:
    sbx.files.write("app.py", "...")
    sbx.run("uvicorn app:app --host 127.0.0.1 --port 8000", background=True)

    # Plain HTTP
    r = httpx.get(
        sbx.proxy_url_for(8000, "/hello"),
        headers=sbx.proxy_headers
    )

    # WebSocket (wss://)
    ws_url = sbx.proxy_url_for(8000, "/ws", scheme="wss://")
```

**Port binding depends on sandbox kind:**
- **Dedicated**: bind TCP on `127.0.0.1:<port>`
- **Pooled**: bind Unix socket at `$SBX_PROXY_DIR/<port>.sock` (Landlock blocks TCP)

### Lifecycle Management

```python
# Create and keep alive
sbx = Sandbox.create(idle_timeout="30m")

# Reconnect from anywhere (same HF token)
sbx = Sandbox.connect("687f911eaea852de79c4a50a")

# Context manager: auto-kills on exit
with Sandbox.create() as sbx:
    ...

# Explicit kill
sbx.kill()

# Close (release HTTP client, don't kill)
sbx.close()
```

Lifecycle rules:
- **idle_timeout** (default 10 min): shuts down when no API calls and no
  running processes
- **24h max lifetime**: hard backstop (not configurable)
- **Sandbox outlives the creating process**: reconnect from any machine

---

## SandboxPool — Many Cheap Sandboxes

When you need 100–1000 short-lived CPU sandboxes, `SandboxPool` packs many
sandboxes into a few shared host Jobs. One VM serves up to
`sandboxes_per_host` (default 50) Landlock-isolated sandboxes.

### Usage

```python
from huggingface_hub import SandboxPool

# Create a pool
with SandboxPool(
    image="python:3.12",
    flavor="cpu-basic",
    sandboxes_per_host=50,
    warm_up=2,           # pre-provision 2 host VMs
    idle_timeout=600,    # host idle timeout
    name="my-pool",      # for cross-process sharing
) as pool:
    # Create individual sandboxes (packs onto warm hosts)
    boxes = [pool.create() for _ in range(100)]

    # Run commands on all of them
    results = [box.run("echo hi").stdout for box in boxes]
```

### Pool vs Dedicated Comparison

| Aspect | Dedicated (`Sandbox.create`) | Pool (`SandboxPool`) |
|--------|------------------------------|----------------------|
| Mapping | 1 Job = 1 sandbox | 1 Job = many sandboxes |
| Isolation | Full VM | uid + Landlock |
| Cold start | ~6s per sandbox | ~6s first host, then ~1 RTT |
| GPU | ✅ | ❌ (CPU only) |
| Best for | Single sandbox, GPU, untrusted code | Many cheap CPU sandboxes |
| Per-sandbox env/secrets | ✅ (with encrypted secrets) | ✅ (no encrypted secrets, use plain env) |
| Per-sandbox volumes | ✅ | ❌ (fixed at host boot) |

### Pool Lifecycle

```python
# Pre-warm hosts
pool.warm(num_hosts=3)

# Reuse across processes (same image/flavor/name)
pool = SandboxPool(image="python:3.12", flavor="cpu-basic")

# Connect from another machine (no local state needed)
pool = SandboxPool.connect("pool-ae9f7efe0bc7")

# Close releases HTTP clients; leaves hosts running for others
pool.close()
```

### Pool Isolation Details

Pooled sandboxes are NOT nested VMs or containers. They use:
- **Dedicated uid** (≥ 20000) per sandbox
- **0700 private home** owned by that uid
- **NO_NEW_PRIVS** + per-process rlimits
- **Per-sandbox Landlock ruleset** (Linux Security Module, ABI 6)
- **env_clear** — host secrets never leak in

What's isolated: process memory, signals, files, `/tmp`/`/dev/shm` (denied),
TCP port binding (blocked), abstract Unix sockets (blocked via
`LANDLOCK_SCOPED_ABSTRACT_UNIX_SOCKET`).

What's shared (acceptable under same-user trust): CPU/RAM/disk capacity (no
cgroup delegation), process-list metadata in `/proc`.

### Pool File Model

Pool sandbox files are rooted at the sandbox's private home directory:
- `files.write("data/in.txt", ...)` → writes to `$HOME/data/in.txt`
- Leading `/` is relative to home
- `..` cannot escape the home directory
- Files are chowned to the sandbox uid

---

## CLI Commands

The `hf sandbox` subcommand mirrors the Python API:

```bash
# Create a dedicated sandbox
hf sandbox create
# ✓ Sandbox ready id=687f911eaea852de79c4a50a image=python:3.12 elapsed=6.0s

# Run a command (streams output live, exits with command's exit code)
hf sandbox exec 687f911eaea852de79c4a50a -- python -c "print('hi')"

# Copy files
hf sandbox cp data.csv 687f911eaea852de79c4a50a:/data/data.csv

# Kill a sandbox
hf sandbox kill 687f911eaea852de79c4a50a

# Background process management
hf sandbox spawn $ID -- python -m http.server 8000
hf sandbox process ls $ID
hf sandbox process kill $ID 1234

# Sandbox Pool commands
hf sandbox pool create python:3.12 --flavor cpu-basic
# ✓ Pool created id=pool-ae9f7efe0bc7 host=687f... elapsed=5.7s
hf sandbox create --pool pool-ae9f7efe0bc7 --env LOG_LEVEL=debug
hf sandbox pool ls
hf sandbox pool delete pool-ae9f7efe0bc7

# Composition in scripts
hf sandbox exec $ID -- pytest && echo "tests passed"
```

Pool sandbox IDs look like `<host_job_id>.<local_id>` and work everywhere a
dedicated ID does (`exec`, `cp`, `kill`).

---

## Performance Benchmarks

Measured on `cpu-basic`, client on laptop, traffic through Jobs proxy:

| Operation | Dedicated | Pool (shared) |
|-----------|-----------|---------------|
| Cold start (create ready) | ~5.8s median | ~6s first host, ~1 RTT thereafter |
| `run()` round-trip | p50 ~110ms | p50 ~110ms |
| File transfer (>8 MiB) | ~340 MiB/s down, ~441 MiB/s up | Same |
| 100 sandboxes (1 host, 50/host) | N/A | 6.1s provision + 1.5s exec + 0.6s kill |
| 1000 sandboxes (20 hosts) | N/A | 7.4s + 4.2s + 4.2s = ~15.8s total |

1000 pooled sandboxes cost ~$0.0009 total (20 × cpu-basic) versus ~$0.06 for
1000 dedicated (one VM each). Server-side create/exec/delete are ~1ms each;
the budget is network round-trip.

---

## Zero-Cost Analysis

| Pattern | Cost | Notes |
|---------|------|-------|
| `Sandbox.create()` on `cpu-basic` | Paid (HF Jobs billing) | Cheapest CPU flavor; idle_timeout controls cost |
| `SandboxPool` with `warm_up=1` | Paid per host VM | Amortized over many sandboxes — cheapest per-sandbox |
| CLI with existing tokens | Free (tokens in env) | No additional infra |
| Local SBX development | Free | Open source `sbx-server` |
| **Pro bono / free credits** | ❓ | No known free tier — check HF billing for org/education credits |

**Important**: Sandboxes are built on HF Jobs, which are a paid service. There
is no free tier for Jobs. However, `idle_timeout` (default 10 min) ensures
abandoned sandboxes stop billing automatically. Pooled sandboxes are the most
cost-effective for CPU workloads.

---

## Design Decisions (Recap)

| Decision | Why |
|----------|-----|
| Built on Jobs, no new service | Inherits billing, hardware, permissions; works in any image |
| Static Rust binary, downloaded at startup | No Python/pip dependency; ~6s cold start vs 30-90s pip bootstrap |
| Hand-rolled HTTP/1.1 | Minimal frameworks buffer chunked responses and break live streaming |
| Stateless HMAC auth | Reconnect from anywhere; HF token never enters sandbox |
| `run()` raises on non-zero (opt-out) | Best DX for "run code, see error" loops (E2B-style) |
| idle_timeout watchdog | Persistent sandboxes are a feature; leaked ones still die |
| Pools = uid + Landlock, no local state | Fast same-user fan-out; correct under concurrency; reattachable anywhere |

---

## Sources

- https://huggingface.co/docs/huggingface_hub/en/guides/sandbox — Sandboxes guide
- https://huggingface.co/docs/huggingface_hub/en/package_reference/sandbox — Sandbox API reference
- https://huggingface.co/docs/huggingface_hub/en/concepts/sandbox — Sandboxes under the hood
- https://github.com/huggingface/sandbox-server — Open source `sbx-server` repo
- `hf jobs hardware` — Available hardware flavors

## See Also

- `hf-hub-sandboxes-deep-dive` — Original sandboxes API deep-dive
- `hf-hub-sandboxes-deep-dive-v2-architecture-and-api` — Sandboxes v2 arch
- `hf-jobs-api-deep-dive` — HF Jobs API (sandboxes are built on Jobs)
- `hf-hub-jobs-api-deep-dive` — Jobs ecosystem
- `hf-openenv-agentic-execution` — OpenEnv (alternative way to run agentic code)
