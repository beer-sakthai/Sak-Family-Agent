---
name: SakThai-hf-hub-jobs-api
author: SakThai
license: MIT
title: Hugging Face Hub Jobs API — Managed Compute on HF Infrastructure
category: mlops
tags: [jobs, compute, managed, huggingface-hub, cli, python-api, batch-processing]
related_skills:
  - hf-hub-sandboxes
  - hf-hub-spaces-build-runtime-api
  - hf-inference-endpoints
  - hf-hub-configuration
description: >-
  Complete reference for the Hugging Face Hub Jobs API — HF's managed compute
  service for running arbitrary code on cloud infrastructure. Covers CLI
  commands (`hf jobs`), Python API (`HfApi.create_job`, `get_job_status`,
  `list_jobs`, `cancel_job`), job lifecycle (queued → running → completed),
  hardware flavors (CPU to H100), log streaming, webhook integration,
  and zero-cost patterns for free-tier compute.
version: 1.0.0
metadata:
  hermes:
    agent: sakthai
    created: 2026-07-25
    updated: 2026-07-25
    type: mlops
    tags: [hf, jobs, compute, batch, automation]
---

# HF Hub Jobs API — Managed Compute Reference

## Overview

Hugging Face **Jobs** is a managed compute service that lets you run arbitrary
code on HF's cloud infrastructure. A Job is a one-shot or recurring workload
that runs in an isolated environment with a specified Docker image, hardware
flavor, and resource configuration.

Use Jobs when you need:
- **Batch processing** — run evaluation, training, or data prep on schedule
- **Ephemeral compute** — spin up, run, tear down (no persistent server)
- **CI/CD integration** — trigger jobs from webhooks or API
- **GPU compute** — access T4, A10G, A100, H100 without managing infrastructure
- **Agent sandbox backend** — power agent sandboxes via the Jobs proxy

## Quick Start

### CLI
```bash
# Run a simple Python script
hf jobs run python:3.12 -- "python -c 'print(40+2)'"

# Run with GPU and custom image
hf jobs run pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel \
  --flavor t4-small \
  -- python train.py --epochs 10
```

### Python
```python
from huggingface_hub import HfApi
api = HfApi()

# Create a job
job = api.create_job(
    image="python:3.12",
    command=["python", "-c", "print('Hello from HF Jobs!')"],
    flavor="cpu-basic",
)

# Monitor status
status = api.get_job_status(job.id)
print(f"Job {job.id}: {status.state}")

# Fetch logs
logs = api.get_job_logs(job.id)
for line in logs:
    print(line)
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `hf jobs run <image> -- <command>` | Create and run a job |
| `hf jobs list` | List all jobs |
| `hf jobs status <id>` | Get job status |
| `hf jobs logs <id>` | Fetch job logs |
| `hf jobs cancel <id>` | Cancel a running job |
| `hf jobs stats` | Resource usage summary |

### Common Flags for `hf jobs run`

| Flag | Description | Default |
|------|-------------|---------|
| `--flavor` | Hardware SKU (cpu-basic, t4-small, a10g-small, etc.) | `cpu-basic` |
| `--sleep-time` | Idle timeout seconds (Spaces integration) | `3600` |
| `--storage` | Persistent storage size (small, medium, large) | None |
| `--env` | Environment variables (`KEY=VALUE`) | None |
| `--secret` | Secrets from Space secrets store | None |
| `--webhook` | Webhook URL for job completion notification | None |

## Python API

All methods on `HfApi`:

```python
from huggingface_hub import HfApi
api = HfApi()
```

| Method | Description |
|--------|-------------|
| `create_job(image, command, flavor, ...)` | Create and start a job |
| `list_jobs(status=None)` | List jobs, optionally filtered by status |
| `get_job_status(job_id)` | Get current job state |
| `get_job_logs(job_id)` | Fetch job stdout/stderr |
| `cancel_job(job_id)` | Cancel a running job |

### `create_job()` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image` | `str` | required | Docker image to run |
| `command` | `list[str]` | required | Entrypoint command (argv) |
| `flavor` | `str` | `"cpu-basic"` | Hardware SKU |
| `sleep_time` | `int` | `3600` | Idle timeout (seconds) |
| `storage` | `str` | None | Persistent storage size |
| `env` | `dict[str,str]` | None | Environment variables |
| `secrets` | `list[dict]` | None | Secrets to inject |
| `webhook` | `str` | None | Completion webhook URL |

## Job Lifecycle

```
CREATED → QUEUED → RUNNING → COMPLETED
                   → RUNNING → FAILED
                   → RUNNING → CANCELLED
                   → QUEUED → CANCELLED
```

| State | Description |
|-------|-------------|
| `CREATED` | Job definition persisted, not yet scheduled |
| `QUEUED` | Waiting for available resources |
| `RUNNING` | Container is executing |
| `COMPLETED` | Exited successfully (exit code 0) |
| `FAILED` | Exited with non-zero code or container error |
| `CANCELLED` | Cancelled by user before completion |

## Hardware Flavors

| Flavor | vCPU | RAM | Accelerator | GPU Memory | Cost |
|--------|------|-----|-------------|------------|------|
| `cpu-basic` | 2 | 8 GB | None | — | Free tier |
| `cpu-upgrade` | 8 | 32 GB | None | — | Paid |
| `t4-small` | 4 | 16 GB | 1× T4 | 16 GB | Paid |
| `t4-medium` | 8 | 32 GB | 1× T4 | 16 GB | Paid |
| `a10g-small` | 4 | 16 GB | 1× A10G | 24 GB | Paid |
| `a10g-large` | 8 | 32 GB | 1× A10G | 24 GB | Paid |
| `a100` | 8 | 64 GB | 1× A100 | 80 GB | Paid |
| `h100` | 16 | 128 GB | 1× H100 | 80 GB | Paid |

**Zero-cost constraint:** `cpu-basic` is free with usage limits. All GPU
flavors are billed per-second. Always check current pricing at
`hf.co/pricing` before provisioning GPU jobs.

## Key Patterns

### Run with Environment Variables
```bash
hf jobs run python:3.12 \
  --env DATASET=bigcode/the-stack \
  --env BATCH_SIZE=128 \
  -- python process.py
```

### Trigger on Webhook (CI/CD)
Jobs can be triggered automatically by Hub webhooks when a repo changes:
- Model/dataset/Space update → run evaluation job
- New PR comment → run test suite
- Scheduled cron → periodic training/data refresh

### Integration with Spaces
Jobs and Spaces share the same infrastructure. A Space is effectively a
long-running Job with an HTTP server. Jobs can mount Space persistent storage
for checkpoint sharing.

### Integration with Sandboxes
Sandboxes ARE Jobs underneath — a Sandbox is a Job running the `sbx-server`
binary. The Jobs API is the lower-level primitive that Sandboxes build on.

See `references/hf-learnings.md` for the complete deep-dive with architecture
details, practical workflows, and zero-cost optimization strategies.
