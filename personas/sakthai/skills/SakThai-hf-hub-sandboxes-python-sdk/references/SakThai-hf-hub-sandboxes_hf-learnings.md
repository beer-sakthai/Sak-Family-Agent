# HF Learnings — Hub Sandboxes Deep Dive

**Topic:** hf-hub-sandboxes-deep-dive (deepening of #148)
**Date:** 2026-07-24
**author:** SakThai
**license:** MIT
**Source:** Hugging Face Hub docs (`huggingface_hub` v1.24.0)
**Research method:** Official HF docs markdown fetched via raw API

---

## Summary

Deep dive into Hugging Face **Sandboxes** — on-demand isolated cloud machines for running code, AI-generated scripts, batch evaluation, RL rollouts, and any remote compute needs. Sandboxes build on top of HF Jobs, using a static `sbx-server` binary that speaks HTTP/1.1 (hand-rolled for live output streaming). Two modes: dedicated (full VM per sandbox, GPU-capable) and pooled (uid + Landlock isolation, CPU-only, ~1000 sandboxes in ~16s total).

---

## 1. Architecture

### There is no "sandbox service"

A sandbox is just an HF Job running one static binary `sbx-server` (~640KB, musl, zero deps). The client talks to that server through the Jobs proxy (`*.hf.jobs` URL). Everything else — auth, discovery, packing many sandboxes into one Job — is built out of existing Jobs primitives.

```
Your machine → Jobs proxy → sbx-server (in Job VM, port 49983)
```

### Bootstrap

At job startup, the Job's command is a `/bin/sh -c` script that fetches the `sbx-server` binary from CDN (`wget`/`curl` fast path) or copies it off a mounted volume (fallback, ~2-3s slower). Every common base image ships `wget` or `curl`.

### Hand-rolled HTTP/1.1

The server implements HTTP/1.1 by hand because minimal Rust HTTP frameworks buffer chunked responses until the response completes, which breaks live output streaming (verified against `tiny_http`). Uses NDJSON event streams for `exec`, raw bodies for files.

### Port 49983

Deliberately uncommon so common dev ports (3000, 8000, 8080, …) stay free for user code.

---

## 2. Authentication (Stateless)

Two independent layers:

1. **Proxy gate:** Jobs proxy only forwards requests carrying an HF token with read access to the job's namespace
2. **Application gate:** `sbx-server` checks a per-sandbox `X-Sandbox-Token` on every request

Token derivation:
```
nonce = random 128-bit hex  (stored in job label "hf-sandbox-nonce")
token = HMAC-SHA256(key=your_hf_token, msg="hf-sandbox:" + nonce)
```

Consequences:
- Reconnect from anywhere with the same HF token
- HF token never enters the sandbox (unless `forward_hf_token=True`)
- Each sandbox has a unique nonce — leaked token compromises one sandbox only
- Job labels: `hf-sandbox=1` and `hf-sandbox-mode=dedicated|pool` for discovery

---

## 3. Dedicated Sandboxes (`Sandbox.create()`)

One Job = one sandbox = one VM. Strongest isolation, supports any hardware flavor including GPUs.

| Metric | Value |
|--------|-------|
| Cold start | ~5.8s median |
| `run()` round-trip | p50 ~110ms |
| File transfer (>8 MiB) | ~340 MiB/s down, ~441 MiB/s up |

API routes at `/v1/*`. Paths are absolute on the container filesystem. `kill()` cancels the Job.

---

## 4. Pooled Sandboxes (`SandboxPool`)

### Design

One Job runs as a "host" and multiplexes many sandboxes inside it using Unix multi-user primitives:

- **Dedicated uid** (≥ 20000)
- **Private `0700` home** owned by that uid
- Commands exec'd as that uid with **scrubbed environment** (`env_clear`), `NO_NEW_PRIVS`, per-process **rlimits**, and a per-sandbox **Landlock ruleset**

Creating a sandbox is `mkdir + chown + build ruleset` ≈ 1ms server-side.

### Isolation: uid + Landlock

Verified against hostile sandbox A attacking victim B:
- ✅ A cannot read B's `environ` → tokens never leak
- ✅ A cannot `SIGKILL` / `ptrace` / read B's memory or `0700` home
- ✅ `/tmp` and `/dev/shm` denied — confined to own home
- ✅ A cannot `bind` a TCP port (outbound connect stays allowed)
- ✅ Cross-sandbox abstract unix sockets blocked (`LANDLOCK_SCOPED_ABSTRACT_UNIX_SOCKET`)

⚠ **Not a VM substitute:** kernel is shared. Two gaps:
- **Resource DoS:** No cgroup delegation. `RLIMIT_NPROC`/`RLIMIT_AS` bound per-process, but aggressive sandbox can starve neighbours or trip OOM.
- **Process-list metadata:** A sandbox can see other processes via `/proc` (names, cmdlines) — just can't read/signal them.

### Performance

| N sandboxes | Hosts (50/host) | Provision + create all | Exec all | Kill all | Total |
|------------|-----------------|----------------------|----------|---------|-------|
| 100 | 2 | 6.1s | 1.5s | 0.6s | **8.2s** |
| 1000 | 20 | 7.4s | 4.2s | 4.2s | **15.8s** |

Server-side create/exec/delete ≈ 1ms each; the budget is entirely the network round-trip.

### File model in pools

Rooted at the sandbox's Landlock-confined home. Leading `/` is taken relative to home; `..` cannot escape it. Files written through the API are `chown`ed to the sandbox's uid.

### Pool lifecycle

- Pool = its set of running host Jobs sharing `hf-sandbox-pool=<id>` label
- No authoritative local state — everything discoverable from labels
- Host carries config in env vars; client reads it back from a running host for consistency
- Capacity is server-authoritative: host refuses creates beyond `sandboxes_per_host`
- Two-level idle eviction: per-sandbox → per-host (billing backstop)
- Best-effort cache at `$HF_HOME/sandbox/pools/<pool-id>.json` for fast `create --pool`
  - Never trusted as truth; self-healing; concurrency-safe (file lock); disposable

---

## 5. Key API Reference

### `Sandbox` class

| Method | Description |
|--------|-------------|
| `Sandbox.create(...)` | Create dedicated sandbox (one Job). Params: `image`, `flavor`, `idle_timeout`, `env`, `secrets`, `volumes`, `namespace`, `forward_hf_token`, `start_timeout` |
| `Sandbox.connect(id)` | Reattach to running sandbox by id |
| `sbx.run(cmd, ...)` | Execute command. Params: `shell`, `env`, `cwd`, `timeout`, `stdin`, `on_stdout`, `on_stderr`, `check`, `background` |
| `sbx.files` | File operations: `write`, `read_text`, `upload`, `download`, `list`, `stat`, `exists`, `mkdir`, `delete` |
| `sbx.processes()` | List background processes |
| `sbx.proxy_url_for(port, path, scheme)` | Get URL to proxy to server inside sandbox |
| `sbx.kill()` | Terminate sandbox |

### `SandboxPool` class

| Method | Description |
|--------|-------------|
| `SandboxPool(image, flavor, sandboxes_per_host, warm_up, ...)` | Create pool |
| `pool.create(env, idle_timeout, forward_hf_token)` | Create one sandbox in pool |
| `pool.warm(num_hosts)` | Pre-provision hosts |
| `pool.close()` | Release/terminate |
| `SandboxPool.connect(pool_id)` | Reattach from anywhere |

### CLI (`hf sandbox`)

| Command | Description |
|---------|-------------|
| `hf sandbox create` | Create dedicated sandbox |
| `hf sandbox exec <id> -- <cmd>` | Run command, stream output |
| `hf sandbox cp <src> <dest>` | Copy files in/out |
| `hf sandbox spawn <id> -- <cmd>` | Start background process |
| `hf sandbox process ls/kill` | Manage processes |
| `hf sandbox pool create <image> --flavor <f>` | Create a pool |
| `hf sandbox create --pool <id>` | Create sandbox in pool |
| `hf sandbox pool delete <id>` | Terminate pool's hosts |

---

## 6. Key Insights

1. **No dedicated sandbox service** — everything is Jobs + a static binary. This is by design: inherits billing, hardware flavors, namespace permissions for free.

2. **Stateless HMAC auth is elegant** — sandbox token derived from HF token + public nonce. Reconnect from anywhere without local state. Token never enters the sandbox (opt-in only).

3. **Pool isolation is fast but not VM-grade** — uid + Landlock is the right boundary for same-user parallel workloads. For mutually-hostile code, use dedicated.

4. **~16 seconds for 1000 sandboxes** — pools amortize VM cold start across hundreds of sandboxes.

5. **Zero-cost access pattern** — free tier can use sandboxes via HF Jobs (billing requires positive credit balance, but `hf jobs run` is pay-as-you-go). For truly free alternatives, use Spaces ZeroGPU for inference or the free Inference API.

6. **Sandboxes are persistent** — they outlive the creating process. Always set `idle_timeout` or use a context manager to avoid orphan billing.

7. **Proxy for inner servers** — no extra public ports needed. Works for HTTP and WebSocket. Pooled sandboxes use unix sockets instead of TCP for the inner server.
