---
name: SakThai-hf-hub-sandboxes
description: "Complete reference on Hugging Face Sandboxes \u2014 on-demand isolated cloud machines\
  \ for running code, AI-generated scripts, batch evaluation, and RL rollouts. Covers\
  \ dedicated (Sandbox.create) and pooled (SandboxPool) modes, CLI commands, file\
  \ transfer, proxying, and internals."
---

# 🤗 Hub Sandboxes — Isolated Cloud Machines

## Overview

Sandboxes are on-demand isolated cloud machines you can spin up in seconds from Python or the CLI. They are built on top of [HF Jobs](../jobs): under the hood a sandbox is just a Job running a tiny static binary server (`sbx-server`) that exposes command execution, file transfer, and process management over HTTP.

### When to use sandboxes

- **Running untrusted or AI-generated code** — let an agent execute arbitrary code without giving it access to your filesystem
- **Reproducible builds and experiments** — run on a clean, well-defined image, CPU or GPU
- **Fanning out work** — launch hundreds of parallel environments (RL rollouts, evaluation, batch tool execution) cheaply

Any Docker image with `/bin/sh` works — no Python/pip/agent needs to be preinstalled.

---

## Two Kinds of Sandbox

| Aspect | `Sandbox.create()` — **Dedicated** | `SandboxPool` — **Shared / Pool** |
|--------|-----------------------------------|-----------------------------------|
| Mapping | One Job = one sandbox (full VM) | One Job = many sandboxes (one VM, packed) |
| Isolation | Full VM | uid + Landlock (same-user trust) |
| Cold start | ~6s per sandbox | ~6s for first host, then ~1 round-trip |
| Cost | One VM per sandbox | One VM per host, amortized |
| GPU | ✅ | ❌ (CPU only) |
| Best for | Single sandbox, GPU, untrusted code | Many cheap CPU sandboxes |

Rule of thumb: need a GPU or mutually-untrusted code → dedicated. Need hundreds of cheap CPU sandboxes → a pool.

---

## Quickstart

```python
from huggingface_hub import Sandbox

with Sandbox.create() as sbx:
    result = sbx.run("python -c 'print(40 + 2)'")
    print(result.stdout)  # 42
```

Pick any image and hardware flavor:

```python
sbx = Sandbox.create(image="pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel", flavor="a10g-small")
```

---

## Running Commands

### `Sandbox.run()`

```python
# Shell string → runs through /bin/sh -c
sbx.run("pip install -q numpy")

# Argv list → exec'd directly
sbx.run(["python", "-c", "import numpy; print(numpy.__version__)"])

# Live output streaming
sbx.run("make -j4", cwd="/app", env={"CC": "gcc"}, timeout=600,
        on_stdout=print, on_stderr=print)
```

**`shell=` parameter:** Explicitly control execution mode. `shell=True` requires a string; `shell=False` requires a list. Default infers from type.

**Error handling:** Non-zero exit raises `SandboxCommandError`. Pass `check=False` to get `SandboxCommandResult` instead:

```python
result = sbx.run("test -f /tmp/missing", check=False)
print(result.exit_code)  # 1
```

### Background Processes

```python
proc = sbx.run("python -m http.server 8000", background=True)
# Returns SandboxProcess immediately
print(sbx.processes())  # list all processes
proc.kill()             # stop one
```

---

## File Operations

```python
sbx.files.write("/app/script.py", "print('hi')")   # str/bytes/file-like
sbx.files.read_text("/app/script.py")
sbx.files.upload("local_data.csv", "/data/data.csv")
sbx.files.download("/data/results.bin", "results.bin")
sbx.files.list("/data")
sbx.files.stat("/data/data.csv")  # FileEntry with size, type, mtime
sbx.files.exists("/data")
sbx.files.mkdir("/data/newdir")
sbx.files.delete("/data/temp")
```

---

## Proxying to a Server Inside a Sandbox

```python
import httpx

with Sandbox.create() as sbx:
    sbx.files.write("app.py", "...")  # server code
    sbx.run("uvicorn app:app --host 127.0.0.1 --port 8000", background=True)
    
    # Plain HTTP
    r = httpx.get(sbx.proxy_url_for(8000, "/hello"), headers=sbx.proxy_headers)
    
    # WebSocket
    ws_url = sbx.proxy_url_for(8000, "/ws", scheme="wss://")
```

**Dedicated:** bind TCP on `127.0.0.1:<port>`. **Pooled:** bind a unix socket at `$SBX_PROXY_DIR/<port>.sock`.

---

## Lifecycle

- Sandbox outlives the creating process — reconnect from anywhere with `Sandbox.connect(id)`
- `idle_timeout` (default 10 min) auto-shuts down abandoned sandboxes
- Hard 24h maximum lifetime per job (not configurable)
- `forward_hf_token=True` to opt-in HF token injection

```python
sbx = Sandbox.create()
sid = sbx.id

# Later, from anywhere:
sbx = Sandbox.connect(sid)
sbx.kill()  # terminate
```

---

## SandboxPool — Many Sandboxes at Once

```python
from huggingface_hub import SandboxPool
from concurrent.futures import ThreadPoolExecutor

with SandboxPool(image="python:3.12", flavor="cpu-basic", warm_up=2) as pool:
    boxes = [pool.create() for _ in range(100)]
    with ThreadPoolExecutor(32) as ex:
        outputs = list(ex.map(lambda b, t: b.run(t.cmd).stdout, boxes, tasks))
```

**Pool inputs vs dedicated:**

| Input | `Sandbox.create()` | `SandboxPool.create()` |
|-------|-------------------|----------------------|
| `image`, `flavor` | per-sandbox | fixed by pool |
| `volumes` | per-sandbox | not available |
| `env` | per-sandbox | per-sandbox |
| `idle_timeout` | per-sandbox | per-sandbox |
| `forward_hf_token` | per-sandbox | per-sandbox |

**Pre-warming:** `pool.warm(N)` provisions N hosts ahead of time. Warm hosts are discovered by job labels, so they survive across processes.

**Reattach:** `SandboxPool.connect(pool_id)` from any machine — no local state needed.

**Cache:** A best-effort cache at `$HF_HOME/sandbox/pools/<pool-id>.json` keeps `create --pool` fast (avoids network rediscovery).

---

## CLI Commands (`hf sandbox`)

```bash
# Dedicated sandbox
hf sandbox create
hf sandbox exec <id> -- python -c "print('hi')"
hf sandbox cp data.csv <id>:/data/data.csv
hf sandbox kill <id>

# Background processes
hf sandbox spawn <id> -- python -m http.server 8000
hf sandbox process ls <id>
hf sandbox process kill <id> <pid>

# Pool management
hf sandbox pool create python:3.12 --flavor cpu-basic
hf sandbox create --pool <pool-id>
hf sandbox pool ls
hf sandbox pool delete <pool-id>
```

---

## Internals

- **No dedicated sandbox service:** A sandbox is just an HF Job running the `sbx-server` static binary (~640KB, musl, zero deps)
- **Auth:** HMAC per-sandbox token derived from HF token + nonce (stateless, reconnect from anywhere)
- **Pool isolation:** uid + Landlock LSM ruleset (no nested namespaces possible without CAP_SYS_ADMIN)
- **The sbx-server** is open source at [github.com/huggingface/sandbox-server](https://github.com/huggingface/sandbox-server)
- See `references/hf-learnings.md` for the full conceptual deep-dive
