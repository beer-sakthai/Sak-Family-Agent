---
name: SakThai-hf-spaces-dev-mode
description: >-
  Complete reference for Hugging Face Spaces Dev Mode — enabling live development,
  SSH/VS Code debugging, and fast iteration on Spaces by skipping Docker image rebuilds.
  Covers the architecture, REST API, Python SDK (huggingface_hub), CLI, Docker requirements,
  and best practices for PRO and Team & Enterprise users.
category: hf-hub
tags:
  - spaces
  - dev-mode
  - debugging
  - ssh
  - vscode
  - hf-cli
  - huggingface-hub
  - development-workflow
---

# Hugging Face Spaces Dev Mode

## Overview

Spaces Dev Mode is a **PRO / Team & Enterprise** feature that makes iterating on Spaces faster by **skipping the Docker image rebuild** step. Instead of rebuilding a new Docker image and provisioning a new VM for every code change, Dev Mode overrides the running container so you can update code, debug, and restart the application live.

### Key Benefits

- **Skip rebuilds** — code changes take effect in seconds, not minutes
- **SSH access** — connect to the running container for live debugging
- **VS Code integration** — edit code inside the Space via Remote-SSH
- **Resource monitoring** — inspect CPU, memory, and runtime behaviour in real time
- **Live restart** — restart the app process without stopping the container

### Prerequisites

- A **PRO** or **Team & Enterprise** Hugging Face plan
- Your **SSH public key** registered in [your account settings](https://huggingface.co/settings/keys) (for SSH connections)
- An existing Space to enable Dev Mode on

---

## Architecture

Under the hood, Dev Mode works by replacing the standard Docker image with a **special Dev Mode image** that:

1. **Starts your application as a sub-process** — so the app can be restarted independently of the container
2. **Runs an SSH server** in the background (port 22)
3. **Runs a VS Code Web server** (code-server) for browser-based editing
4. **Injects a Refresh API** — a button in the UI that restarts the app process without a full container rebuild

When you make code changes:

```
Edit code → hit Refresh → app restarts (2–5 seconds)
```

Without Dev Mode, the same cycle is:

```
Edit code → git commit → Docker rebuild (2–10 minutes) → new VM provisioned → app starts
```

---

## Enabling Dev Mode

### Via the Web UI

1. Navigate to your Space page (`https://huggingface.co/spaces/{namespace}/{repo}`)
2. Click the **"Dev Mode"** toggle in the Space settings
3. A modal appears showing connection instructions (subdomain, SSH command)

### Via the REST API

```http
POST https://huggingface.co/api/spaces/{namespace}/{repo}/dev-mode
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "enabled": true
}
```

Disable by setting `"enabled": false`.

### Via the Python SDK

**Enable:**
```python
from huggingface_hub import HfApi

api = HfApi()
runtime = api.enable_space_dev_mode("namespace/repo")
print(runtime.stage)  # e.g. "RUNNING"
```

**Disable:**
```python
runtime = api.disable_space_dev_mode("namespace/repo")
```

**Returns:** [`SpaceRuntime`](https://huggingface.co/docs/huggingface_hub/main/en/package_reference/space_runtime) — contains `stage`, `hardware`, `requested_hardware`, `sleep_time`, `volumes`, and `raw` metadata.

### Via the HF CLI

```bash
# Enable Dev Mode and open SSH session
hf spaces ssh namespace/repo

# Enable Dev Mode automatically (skip confirmation prompt)
hf spaces ssh namespace/repo --auto

# Enable Dev Mode without SSH (prints connection instructions)
hf spaces dev-mode namespace/repo

# Print SSH command without executing
hf spaces ssh namespace/repo --dry-run

# Use a specific SSH identity file
hf spaces ssh namespace/repo -i ~/.ssh/id_ed25519
```

The `hf spaces ssh --auto` flag is useful for CI/CD pipelines and automation because it enables Dev Mode without interactive prompting.

---

## Connecting to a Dev Mode Space

### Get the Subdomain

You need the Space's subdomain to connect. Retrieve it from the Dev Mode modal in the UI or programmatically:

```python
from huggingface_hub import HfApi

api = HfApi()
subdomain = api.space_info("namespace/repo").subdomain
print(f"Subdomain: {subdomain}")
```

### Via SSH

```bash
ssh <subdomain>@ssh.hf.space
```

Once connected, you have full shell access to the container — you can inspect processes, edit files, install packages, and restart the application.

### Via VS Code Remote-SSH

1. Install the **Remote - SSH** extension in VS Code
2. Add a new SSH host: `ssh <subdomain>@ssh.hf.space`
3. Connect and browse the `/app` folder
4. Edit files and use the integrated terminal

### Via Cursor / Windsurf

The `hf spaces dev-mode namespace/repo` command prints connection instructions suitable for Cursor and Windsurf as well.

---

## Persisting Changes

**By default, changes made in Dev Mode are ephemeral.** They are discarded when Dev Mode is disabled or the Space goes to sleep.

To persist changes permanently, commit them from inside the container:

```bash
# Inside the Dev Mode SSH session
cd /app
git add .
git commit -m "Update app logic via Dev Mode"
git push
```

The Dev Mode UI warns you when there are uncommitted or unpushed changes.

---

## Application Restart

Unlike normal Spaces, **the app does not restart automatically** when you change code in Dev Mode. You must explicitly restart it:

- **Click the Refresh button** in the Dev Mode modal (UI)
- The app process restarts while the container stays running

If you're using Gradio SDK or a Python-based app, dependencies (`requirements.txt`, `packages.txt`) are **not installed automatically**. Run manually:

```bash
pip install -r requirements.txt
```

---

## Docker Space Requirements

Dev Mode works with Docker Spaces, but the Dockerfile must meet these requirements:

### Required Packages

```dockerfile
RUN apt-get update && \
    apt-get install -y \
      bash \
      curl \
      wget \
      procps \
      git \
      git-lfs \
      && \
    rm -rf /var/lib/apt/lists/*
```

| Package   | Purpose                               |
|-----------|---------------------------------------|
| `bash`    | SSH connections                       |
| `curl`    | VS Code server health checks          |
| `wget`    | VS Code server downloads              |
| `procps`  | VS Code server process management     |
| `git`     | Commit/push changes from Dev Mode     |
| `git-lfs` | Large file support for git            |

### App Location

- Application code must be in **`/app`**
- The `/app` folder must be **owned by uid 1000**

### Startup Instruction

- The Dockerfile **must** contain a `CMD` instruction

```dockerfile
CMD ["python", "app.py"]
# or
CMD ["node", "index.js"]
```

### Base Image

- **Debian-based** images (e.g., `ubuntu`, `debian`, `node:19-slim`) are recommended
- Alpine and other exotic distros are **not tested** and Dev Mode is not guaranteed

### Complete Example (Docker Space)

```dockerfile
FROM node:19-slim

RUN apt-get update && \
    apt-get install -y \
      bash \
      git git-lfs \
      wget curl procps \
      htop vim nano && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --link ./ /app
RUN npm i

RUN chown 1000 /app
USER 1000
CMD ["node", "index.js"]
```

### Reference Docker Spaces

- [Python FastAPI example](https://huggingface.co/spaces/dev-mode-explorers/dev-mode-python)
- [JavaScript Express.js example](https://huggingface.co/spaces/dev-mode-explorers/dev-mode-javascript)
- [Dev Mode discussions & feedback](https://huggingface.co/spaces/dev-mode-explorers/README/discussions)

---

## Limitations

| Limitation | Details |
|------------|---------|
| **Static Spaces** | Dev Mode is not available for static Spaces |
| **Docker Spaces** | Require specific packages and config (see above) |
| **No auto-restart** | Changes require manual Refresh |
| **Dependencies** | Packages not auto-installed in Dev Mode |
| **Ephemeral by default** | Changes lost unless committed and pushed |
| **Base image** | Debian-based only; Alpine not guaranteed |
| **Plan requirement** | Requires PRO, Team, or Enterprise plan |

---

## Python SDK Reference

### Methods on `HfApi`

| Method | Description |
|--------|-------------|
| `enable_space_dev_mode(repo_id)` | Enable Dev Mode on a Space |
| `disable_space_dev_mode(repo_id)` | Disable Dev Mode on a Space |
| `space_info(repo_id).subdomain` | Get the subdomain for SSH connections |
| `get_space_runtime(repo_id)` | Get current runtime stage, hardware, volumes |
| `restart_space(repo_id)` | Restart a Space |
| `pause_space(repo_id)` | Pause a running Space |
| `wait_for_space(repo_id, timeout)` | Block until Space is RUNNING |

### SpaceRuntime Data Class

```python
class SpaceRuntime:
    stage: str             # RUNNING, BUILDING, PAUSED, etc.
    hardware: str | None   # "cpu-basic", "t4-medium", etc.
    requested_hardware: str | None
    sleep_time: int | None # seconds of inactivity before sleep
    volumes: list[Volume] | None
    raw: dict              # server response with additional metadata
```

### Example: Full Workflow

```python
from huggingface_hub import HfApi

api = HfApi()
repo_id = "username/my-space"

# 1. Enable Dev Mode
api.enable_space_dev_mode(repo_id)

# 2. Wait for Space to be ready
runtime = api.wait_for_space(repo_id, timeout=120)
assert runtime.stage == "RUNNING"

# 3. Get the subdomain for SSH
subdomain = api.space_info(repo_id).subdomain
print(f"Connect via: ssh {subdomain}@ssh.hf.space")

# 4. (Later) Disable Dev Mode
api.disable_space_dev_mode(repo_id)
```

---

## CLI Reference

```bash
# SSH into Space (auto-enable Dev Mode)
hf spaces ssh namespace/repo
hf spaces ssh namespace/repo --auto
hf spaces ssh namespace/repo --dry-run
hf spaces ssh namespace/repo -i ~/.ssh/id_ed25519

# Enable Dev Mode without SSH
hf spaces dev-mode namespace/repo

# View Space logs (useful alongside Dev Mode)
hf spaces logs namespace/repo
hf spaces logs namespace/repo -n 50

# Restart Space
hf spaces restart namespace/repo

# Show Space status
hf spaces info namespace/repo
```

---

## Development Workflow (Recommended)

1. **Create or navigate to** your Space on HF Hub
2. **Enable Dev Mode** via CLI: `hf spaces ssh namespace/repo --auto`
3. **SSH in** and make changes to `/app` (edit files, install packages, test)
4. **Restart the app** using the Refresh button in the UI
5. **Iterate** — edit, refresh, verify
6. **Persist changes** when satisfied: `git add . && git commit -m "..." && git push`
7. **Disable Dev Mode** when done: `hf spaces dev-mode namespace/repo` (toggle off)

### Debugging Tips

- Use `htop`, `nvidia-smi` (GPU Spaces), and `df -h` inside SSH to monitor resources
- Check application logs: `hf spaces logs namespace/repo -n 100`
- If the app won't start, verify dependencies are installed (`pip list`, `npm list`)
- For Docker Spaces, confirm `CMD` and `/app` ownership before enabling Dev Mode

---

## Related Skills

- [hf-spaces-configuration-reference](../hf-spaces-configuration-reference/SKILL.md)
- [hf-spaces-lifecycle-sleep-pause-billing-duration](../hf-spaces-lifecycle-sleep-pause-billing-duration/SKILL.md)
- [hf-spaces-logs-monitoring-and-debugging-deep-dive](../hf-spaces-logs-monitoring-and-debugging-deep-dive/SKILL.md)
- [hf-spaces-docker-custom](../hf-spaces-docker-custom/SKILL.md)
- [hf-hub-spaces-build-runtime-api](../hf-hub-spaces-build-runtime-api/SKILL.md)
