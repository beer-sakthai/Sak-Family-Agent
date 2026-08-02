---
name: SakThai-hf-jobs-configuration
author: SakThai
license: MIT
description: "Complete reference for configuring Hugging Face Jobs — authentication, UV/Docker job config, environment variables and secrets, volume mounting (repos, datasets, buckets, local dirs), hardware flavors and pricing, port exposure, SSH debugging, timeouts, namespace management, and job labels."
version: 1.0.0
category: mlops
tags: [huggingface, jobs, configuration, compute, mlops, cron]
platforms: [linux]
---

# HF Jobs Configuration

Hugging Face Jobs provide on-demand compute for AI and data workflows on HF infrastructure. This skill covers everything about **configuring** Jobs — from authentication and environment variables to volume mounting, hardware selection, SSH access, and labels.

> **Complementary skills:** `hf-hub-jobs-api-deep-dive` for the full Jobs API lifecycle, `hf-jobs-uv-run` for UV-specific patterns, `hf-jobs-serving-vllm` for vLLM serving via Jobs.

## Overview

A Job is defined by:
- A **command** to run (UV script, Python, or arbitrary Docker command)
- A **hardware flavor** (CPU, GPU, or TPU)
- Optionally, a **Docker image** from HF Spaces, Docker Hub, or custom
- **Configuration** via CLI flags, Python arguments, or YAML

Jobs run on HF-managed infrastructure. Pricing starts at **$0.01/hour for CPU-basic** (free-tier eligible).

## Authentication

All Job operations require authentication to HF Hub:

```bash
# Login first
hf auth login

# Or pass token inline
hf jobs uv run --token hf_xxx train.py

# For org jobs, ensure token has Write permission for the org
hf jobs uv run --namespace my-org --token hf_xxx train.py
```

**Python:**
```python
from huggingface_hub import run_job
job = run_job(image="python:3.12", command=["python", "script.py"], token="hf_xxx")
```

**Token scopes needed:**
- `read` — view jobs
- `write` — create, manage, cancel jobs
- For org-run jobs: org-level Write permission

## UV Jobs

The simplest way to run Python workloads. UV handles dependency resolution automatically:

```bash
# Basic
hf jobs uv run train.py

# Inline Python
hf jobs uv run python -c 'print("Hello from the cloud!")'

# With dependencies
hf jobs uv run --with trl train.py

# With specific Python version
hf jobs uv run --python 3.12 train.py

# Custom Docker image (must have UV installed)
hf jobs uv run --image ghcr.io/my-org/my-image train.py
```

**Default image:** `ghcr.io/astral-sh/uv:python3.12-bookworm`

**Separating args:** Use `--` to separate Jobs/UV options from the command:
```bash
hf jobs uv run --with trl-jobs -- trl-jobs sft --model_name Qwen/Qwen3-0.6B
```

## Docker Jobs

For full flexibility — any Docker image, any command:

```bash
hf jobs run ubuntu echo "Hello from the cloud!"

# With options before the command
hf jobs run --token hf_xxx ubuntu -- echo "Hello"
```

**⚠ Pitfall:** All Jobs options must be provided **before** the command. Use `--` to separate if needed.

## Environment Variables & Secrets

### Built-in environment variables

Every Job receives these automatically:

| Variable | Description |
|----------|-------------|
| `JOB_ID` | Unique job identifier (e.g., `699d874f1aad19adb8aaeadc`) |
| `ACCELERATOR` | Hardware flavor (e.g., `t4-medium`, `a10g-small`, `none`) |
| `CPU_CORES` | Allocated CPU cores |
| `MEMORY` | Allocated RAM (e.g., `8Gi`) |

### User-defined variables

```bash
# Pass inline
hf jobs uv run -e FOO=foo -e BAR=bar python -c 'import os; print(os.environ["FOO"])'

# From .env file
hf jobs uv run --env-file .env python -c '...'

# Secrets (encrypted server-side)
hf jobs uv run -s MY_SECRET=psswrd python -c 'print(os.environ["MY_SECRET"])'

# From .env.secrets (auto-encrypted)
hf jobs uv run --secrets-file .env.secrets python -c '...'

# Pass HF_TOKEN implicitly (reads from local environment or HF token file)
hf jobs uv run --secrets HF_TOKEN python -c '...'
```

**🔐 Secret handling:** Secrets are encrypted at rest on HF servers. They never appear in logs.

**Python API:**
```python
from huggingface_hub import run_job
job = run_job(
    image="python:3.12",
    command=["python", "train.py"],
    env={"EPOCHS": "10", "LR": "0.001"},
    secrets={"HF_TOKEN": "hf_xxx", "WANDB_API_KEY": "..."},
)
```

## Volumes

Mount HF repos, datasets, storage buckets, or local directories into your Job container.

### Volume syntax

```
-v hf://[TYPE/]SOURCE:/MOUNT_PATH[:ro|:rw]
```

| Type | Example |
|------|---------|
| Model repo | `-v hf://openai/gpt-oss-120b:/model` |
| Dataset repo | `-v hf://datasets/username/my-dataset:/data` |
| Storage bucket | `-v hf://buckets/username/my-bucket:/mnt` |
| Subfolder | `-v hf://datasets/org/my-dataset/train:/data` |
| Local directory | `-v ./training-data:/data` |

### Access modes

- **Models & datasets** — always mounted **read-only**
- **Buckets** — **read-write** by default (good for checkpoints/outputs)
- **Local directories** — **read-only** by default (`:rw` to allow writes)

```bash
# Mount bucket as read-write (default)
hf jobs run -v hf://buckets/username/my-bucket:/output python:3.12 python script.py

# Mount bucket as read-only
hf jobs run -v hf://buckets/username/my-bucket:/mnt:ro python:3.12 ls /mnt

# Mount a dataset and query it
hf jobs run -v hf://datasets/stanfordnlp/imdb:/dataset duckdb/duckdb duckdb -c "SELECT * FROM '/dataset/**/*.parquet' LIMIT 5"

# Mount local directory with write access
hf jobs uv run -v ./pdfs:/input -v ./md-out:/output:rw ocr.py
```

### Multiple volumes

```bash
hf jobs run \
  -v hf://datasets/username/my-dataset:/data \
  -v hf://buckets/username/my-bucket:/output \
  python:3.12 python script.py
```

### Python API

```python
from huggingface_hub import Volume, run_job

job = run_job(
    image="python:3.12",
    command=["python", "train.py"],
    volumes=[
        Volume(type="dataset", source="username/my-dataset", mount_path="/data"),
        Volume(type="bucket", source="username/my-bucket", mount_path="/output"),
    ],
)
```

### Sync job volume (local directories)

Passing a local directory syncs it to a private `jobs-artifacts` Storage Bucket (created automatically) before the Job starts:

```python
from huggingface_hub import sync_job_volume

volume = sync_job_volume(
    source="./training-data",
    mount_path="/data",
    read_only=False,
)
```

Re-syncing only uploads new/modified files. The CLI prints the exact `hf buckets sync` command for retrieval when the job finishes.

**⚠ Requirements:** Volume mounting requires `huggingface_hub >= 1.8.0`.

## Hardware Flavors

Use `--flavor` to select hardware. Full table from `hf jobs hardware`:

### CPU

| Name | vCPU | RAM | Storage | Cost/min | Cost/hr |
|------|------|-----|---------|----------|---------|
| `cpu-basic` | 2 | 16 GB | 50 GB | $0.0002 | **$0.01** |
| `cpu-upgrade` | 8 | 32 GB | 50 GB | $0.0005 | $0.03 |
| `cpu-performance` | 32 | 256 GB | 1024 GB | $0.0317 | $1.90 |
| `cpu-xl` | 16 | 124 GB | 1000 GB | $0.0167 | $1.00 |

### GPU (selected)

| Name | GPU | vCPU | RAM | Cost/hr |
|------|-----|------|-----|---------|
| `t4-small` | 1× T4 (16 GB) | 4 | 15 GB | $0.40 |
| `t4-medium` | 1× T4 (16 GB) | 8 | 30 GB | $0.60 |
| `a10g-small` | 1× A10G (24 GB) | 4 | 15 GB | $1.00 |
| `a10g-large` | 1× A10G (24 GB) | 12 | 46 GB | $1.50 |
| `a100-large` | 1× A100 (80 GB) | 12 | 142 GB | $2.50 |
| `h200` | 1× H200 (141 GB) | 23 | 256 GB | $5.00 |
| `l4x1` | 1× L4 (24 GB) | 8 | 30 GB | $0.80 |
| `l40sx1` | 1× L40S (48 GB) | 8 | 62 GB | $1.80 |

**Default:** `cpu-basic` ($0.01/hr).

```bash
# Run on A10G
hf jobs uv run --with torch --flavor a10g-small python -c "import torch; print(torch.cuda.get_device_name())"

# List all available hardware
hf jobs hardware
```

## Expose Ports

Jobs can expose container ports via a public proxy:

```bash
# Single port
hf jobs run --expose 8000 python:3.12 python -m http.server 8000

# Multiple ports
hf jobs run --expose 8000 --expose 8001 python:3.12 server.py
```

Each exposed port is reachable at:
```
https://<job_id>--<port>.hf.jobs
```

**Auth required:** HF token with `read` access to the job's namespace:
```bash
curl -H "Authorization: Bearer hf_xxx" https://<job_id>--8000.hf.jobs/
```

**Python:**
```python
job = run_job(
    image="python:3.12",
    command=["python", "-m", "http.server", "8000"],
    expose=[8000],
)
print(job.status.expose_urls)
# ['https://6a2ab384...--8000.hf.jobs']
```

**💰 Pricing:** Exposed ports incur a small flat hourly rate on top of the job's hardware cost, only while running.

## SSH

Open an interactive SSH session into a running Job for debugging or live inspection:

```bash
# Start a job with SSH enabled
hf jobs run --ssh --detach --timeout 10m python:3.12 sleep infinity

# Connect
hf jobs ssh <job_id>

# Dry-run (show ssh command without connecting)
hf jobs ssh <job_id> --dry-run

# Use specific identity file
hf jobs ssh <job_id> -i ~/.ssh/id_ed25519
```

**Python:**
```python
job = run_job(image="python:3.12", command=["sleep", "infinity"], ssh=True)
print(job.status.ssh_url)
# 'ssh://6a2bd1...ad31@ssh.hf.jobs'
```

### Port forwarding

Since SSH is standard, use `-L` and `-R`:

```bash
# Forward TensorBoard from Job to local
ssh -L 6006:localhost:6006 <job_id>@ssh.hf.jobs

# Let Job access a local service
ssh -R 8080:localhost:8080 <job_id>@ssh.hf.jobs
```

**⚠ Requirements:**
- Only users with Write access to the Job's namespace can SSH
- SSH keys must be registered at https://huggingface.co/settings/keys
- Not available for scheduled jobs

## Timeout

Jobs have a **default 30-minute timeout**. Set a custom timeout:

```bash
# As seconds (2 hours)
hf jobs uv run --timeout 7200 --with torch --flavor a10g-large train.py

# As time units
hf jobs uv run --timeout 2h --with torch train.py
```

**Supported units:** `s` (seconds), `m` (minutes), `h` (hours), `d` (days).

**Python:**
```python
job = run_job(
    image="python:3.12",
    command=["python", "train.py"],
    timeout="2h",  # or 7200 (seconds)
)
```

**⚠ Pitfall:** If you don't set a timeout for long-running training, the default 30m will terminate it. Always set `--timeout` explicitly for training jobs.

## Namespace

Run Jobs under an organization account:

```bash
hf jobs uv run --namespace my-org python -c "print('Running in an org')"

# With explicit token
hf jobs uv run --namespace my-org --token hf_xxx python -c "..."
```

**Python:**
```python
job = run_job(
    image="python:3.12",
    command=["python", "train.py"],
    namespace="my-org",
)
```

## Labels & Naming

Add metadata to Jobs for filtering in the UI and CLI:

```bash
# Simple labels
hf jobs uv run --label fine-tuning --label model=Qwen3-0.6B ...

# Name a Job (stored as `name` label)
hf jobs run --name daily-report python:3.12 python report.py
```

**Update labels on existing Jobs:**
```bash
# Replace all labels
hf jobs labels <job_id> --label env=prod --label team=ml

# Set name only (keeps other labels)
hf jobs labels <job_id> --name daily-report

# Clear all labels
hf jobs labels <job_id> --clear
```

**⚠ Pitfall:** Using the same key multiple times causes the last `key=value` to overwrite previous values for that key. Names are not unique — multiple Jobs can share a name.

## Python API Summary

```python
from huggingface_hub import run_job, list_jobs, cancel_job, Volume, sync_job_volume

# Create
job = run_job(
    image="python:3.12",
    command=["python", "train.py"],
    env={"LR": "0.001"},
    secrets={"HF_TOKEN": "hf_xxx"},
    flavor="a10g-small",
    timeout="2h",
    name="sft-training",
    labels={"model": "Qwen3-0.6B"},
    volumes=[Volume(type="dataset", source="...", mount_path="/data")],
    expose=[8000],
    ssh=True,
    namespace="my-org",
)

# List
for j in list_jobs(status="running", labels={"env": "prod"}, namespace="my-org"):
    print(j.job_id, j.status.stage)

# Cancel
cancel_job(job_id=job.job_id)
```

## Pitfalls

| Pitfall | Symptom | Mitigation |
|---------|---------|------------|
| Default 30m timeout kills long training | Job stops mid-training | Always set `--timeout` explicitly (e.g., `--timeout 2h`) |
| Options after command position | `Error: unexpected argument` | Put all Jobs options **before** the command; use `--` to separate |
| Expired secret syntax | Secrets appear in logs | Use `-s` (secret) not `-e` (env var) for sensitive values |
| SSH keys not registered | `Permission denied` | Register keys at https://huggingface.co/settings/keys |
| Volume `huggingface_hub` too old | `Volume` class not found | Upgrade: `uv pip install -U huggingface_hub` (min v1.8.0) |
| Org token lacks permissions | `403 Forbidden` | Verify org-level Write permission on the token |
| Exposed ports not reachable | Curl returns 401 | Pass `Authorization: Bearer hf_xxx` header with read access |
| Bucket mount `:rw` ignored on model repos | Write fails silently | Models/datasets are always read-only; use buckets for write |

## Verification Checklist

- [ ] `hf auth login` succeeds and token has write scope
- [ ] `hf jobs uv run --with torch python -c "..."` runs on default CPU
- [ ] `-e` env vars visible inside container
- [ ] `-s` secrets visible inside container, redacted from logs
- [ ] Volume mount `-v hf://datasets/...:/data` accessible read-only
- [ ] Bucket volume `-v hf://buckets/...:/output` writable
- [ ] `--flavor a10g-small` uses GPU (verify with `torch.cuda.is_available()`)
- [ ] `--expose 8000` creates accessible URL with auth
- [ ] `--ssh` lets you connect with `hf jobs ssh`
- [ ] `--timeout 10m` terminates job after 10 minutes
- [ ] Labels visible in `hf jobs ps` output
- [ ] Python API: `run_job()`, `list_jobs()`, `cancel_job()` all work

## Reference

- [Jobs Overview (docs)](https://huggingface.co/docs/hub/en/jobs-overview)
- [Jobs Configuration (docs)](https://huggingface.co/docs/hub/en/jobs-configuration)
- [Jobs CLI Reference (hf docs)](https://huggingface.co/docs/huggingface_hub/package_reference/cli#hf-jobs)
- [Jobs Python API (hf docs)](https://huggingface.co/docs/huggingface_hub/guides/jobs)
- [Jobs OpenAPI Spec](https://huggingface-openapi.hf.space/#tag/jobs)
- [Jobs Pricing](https://huggingface.co/docs/hub/en/jobs-pricing)
- [Process Large Datasets on Jobs](https://huggingface.co/docs/hub/en/jobs-large-datasets)
