# HF Learnings Log — Hugging Face Hub Sandboxes Python SDK

## 2026-07-25: hf-hub-sandboxes-python-sdk — Sandboxes in huggingface_hub v1.24.0+ (Topic #386 Deepening: hf-hub-sandboxes-deep-dive)

### Summary
Deep-dive into the **Hugging Face Hub Sandboxes Python SDK** — the `Sandbox`
and `SandboxPool` classes and `hf sandbox` CLI commands available in
`huggingface_hub` v1.24.0+. Sandboxes provide isolated cloud VMs (built on HF
Jobs) that spin up in ~6s, run commands with live-streamed output, transfer
files, and proxy to inner servers — all from Python or the CLI. Covers the
full API surface, stateless HMAC auth, uid+Landlock pool isolation,
performance benchmarks, and zero-cost strategies.

### Key Findings

| Area | Finding |
|------|---------|
| **What it is** | Sandbox = HF Job running `sbx-server` (static Rust binary). Two kinds: dedicated (one Job = one VM) and pooled (many Landlock-isolated sandboxes per VM). |
| **Python API** | `Sandbox.create()` / `.connect()` / `.run()` / `.files()` / `.proxy_url_for()` / `.kill()`. `SandboxPool` for shared multi-sandbox hosts. |
| **CLI** | `hf sandbox create|exec|cp|kill|spawn|process|pool` — mirrors Python API. |
| **Auth** | Stateless HMAC: token derived from HF token + job nonce. No server-side storage. HF token never enters sandbox (opt-in). |
| **Dedicated isolation** | Full VM — GPU capable, strong isolation for untrusted code. |
| **Pool isolation** | uid (≥20000) + Landlock ABI 6 + NO_NEW_PRIVS + per-sandbox home (0700). No inter-sandbox file/process/signal access. No TCP binding. |
| **Pool limitations** | No VM-level isolation (same kernel, shared CPU/RAM). Process-list metadata visible in `/proc`. No GPU. |
| **File API** | `write()`, `read_text()`, `upload()`, `download()`, `list()`, `stat()`, `exists()`, `mkdir()`, `delete()`. Pool files rooted at sandbox home. |
| **Proxy** | `proxy_url_for(port, path)` returns proxied URL; `proxy_headers` for auth. Dedicated: TCP. Pooled: Unix socket (`$SBX_PROXY_DIR/<port>.sock`). |
| **Lifecycle** | `idle_timeout` (default 10min) + 24h max lifetime. Sandbox outlives creating process — reconnect from anywhere. |
| **Performance** | Dedicated cold start ~5.8s. `run()` p50 ~110ms. File transfer ~340 MiB/s down, ~441 MiB/s up. 1000 pooled sandboxes in ~16s total. |
| **Cost** | HF Jobs billing (no free tier). `idle_timeout` auto-shuts down abandoned sandboxes. Pools amortize cost across many sandboxes. |

### Comparison: Dedicated vs Pool Sandboxes

| Aspect | Dedicated (`Sandbox.create`) | Pool (`SandboxPool`) |
|--------|------------------------------|----------------------|
| **Mapping** | 1 Job = 1 sandbox (full VM) | 1 Job = many sandboxes |
| **Isolation** | Full VM isolation | uid + Landlock (same-user trust) |
| **Cold start** | ~6s per sandbox | ~6s first host, ~1 RTT thereafter |
| **GPU** | ✅ All flavors | ❌ CPU only |
| **Per-sandbox volumes** | ✅ Supported | ❌ Fixed at host boot |
| **Secrets** | ✅ Encrypted Job secrets | ❌ Plain env only (not stored in job metadata) |
| **Port binding** | TCP on 127.0.0.1:<port> | Unix socket at $SBX_PROXY_DIR/<port>.sock |
| **Best for** | GPU workloads, untrusted code | Many cheap CPU sandboxes (RL, eval, fan-out) |

### Architecture: "No New Service"

- No dedicated sandbox backend — sandbox = Job + `sbx-server` binary
- Server: ~640KB static musl Rust binary, hand-rolled HTTP/1.1 (for streaming)
- Two-layer auth: Jobs proxy (HF token gate) + sbx-server (HMAC token)
- Token derivation: `HMAC-SHA256(key=HF_TOKEN, msg="hf-sandbox:" + nonce)`
- Server downloaded via `wget`/`curl` at startup, with volume mount fallback

### Pool Isolation: What's Protected

✅ Process memory (cannot read another sandbox's `environ`)
✅ Signals (cannot SIGKILL/ptrace another sandbox)
✅ Files (0700 home, Landlock-confined to own home)
✅ `/tmp` and `/dev/shm` (blocked via Landlock)
✅ TCP port binding (blocked via Landlock)
✅ Abstract Unix sockets (blocked via `LANDLOCK_SCOPED_ABSTRACT_UNIX_SOCKET`)

❌ CPU/RAM/disk (shared kernel, no cgroup delegation — risk of DoS)
❌ Process-list metadata (`/proc` visible, cannot read/signal but can see names)

### Pool State Model

- No authoritative local state — pool = its running host Jobs
- Hosts carry config in env vars (image, flavor, `sandboxes_per_host`, timeout)
- Labels only used for filtering (`hf-sandbox-pool=<id>`)
- Best-effort cache at `$HF_HOME/sandbox/pools/<pool-id>.json` speeds up `create`
- Cache is never authoritative: stale entries = wasted request, not correctness

### Key Differences from Previous Coverage

My earlier `hf-hub-sandboxes-deep-dive` and `hf-hub-sandboxes-deep-dive-v2`
covered the underlying Sandboxes API (the Hub REST API for managing sandboxes).
This deep-dive covers the **huggingface_hub Python SDK integration** (v1.24.0+)
that provides `Sandbox` and `SandboxPool` Python classes, the `hf sandbox` CLI,
and the full programmatic interface — which is a distinct and much richer API
surface.

### Skill Created
`hf-hub-sandboxes-python-sdk/` — SKILL.md (author: SakThai, license: MIT) +
references/hf-learnings.md with full Sandbox API, SandboxPool API, CLI
reference, architecture, auth model, comparison tables, performance benchmarks,
and zero-cost analysis.

### Sources
- https://huggingface.co/docs/huggingface_hub/en/guides/sandbox — Sandboxes guide
- https://huggingface.co/docs/huggingface_hub/en/package_reference/sandbox — Sandbox API reference
- https://huggingface.co/docs/huggingface_hub/en/concepts/sandbox — Sandboxes under the hood
- https://github.com/huggingface/sandbox-server — Open source sbx-server repo

### Tags
`sandbox` `jobs` `python-sdk` `huggingface-hub` `cloud-compute` `isolation` `cli` `proxy` `landlock` `hmac`
