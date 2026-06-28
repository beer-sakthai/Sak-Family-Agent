---
name: hf-jobs
description: "Hugging Face Jobs: run compute workloads (scripts, Docker, UV) on HF infrastructure with GPU/TPU/CPU, scheduling, webhooks, and the Jobs CLI / Python SDK."
tags: [huggingface, hf, jobs, compute, infrastructure, docker, uv, scheduling, webhooks, mlops]
platforms: [linux, macos, windows]
---

# Hugging Face Jobs

Run compute workloads on Hugging Face infrastructure using a familiar **UV- and Docker-like interface**. Jobs let AI builders, data engineers, and agents run fine-tuning, inference, data processing, and custom workloads without managing their own cloud accounts.

## Core Concepts

A job is defined by:
1. **Command to run** — a UV command, Python script, or arbitrary Docker command.
2. **Hardware flavor** — CPU, GPU, or TPU.
3. **Docker image** (optional) — from Hugging Face Spaces or Docker Hub.

Jobs run on Hugging Face-managed infrastructure and are billed per-second for the hardware used.

## Three Ways to Run Jobs

### 1. HF CLI
```bash
# UV-like interface for Python workloads
hf jobs uv run train.py --gpu

# Docker-like interface for any workload
hf jobs run pytorch/pytorch:latest python train.py --gpu
```

The CLI supports common job operations:
```bash
hf jobs list                    # List recent jobs
hf jobs logs <job-id>           # Stream logs
hf jobs metrics <job-id>        # Resource usage (was 'stats' in older docs)
hf jobs inspect <job-id>        # Inspect job definition
hf jobs cancel <job-id>         # Cancel a running job
hf jobs wait <id1> <id2>        # Block until terminal; exit 0 only if all succeeded
hf jobs uv run train.py --gpu   # UV-based Python workload
hf jobs run ... --schedule "*/5 * * * *"  # Scheduled job
```

### 2. Python SDK (`huggingface_hub`)
```python
from huggingface_hub import run_job, run_uv_job, wait_for_job

# Standard Docker-based job
run_job(
    image="python:3.12",
    command=["python", "train.py"],
    flavor="a10g-small",
)

# UV-based job (self-contained Python with inline dependencies)
run_uv_job(
    "train.py",
    flavor="a10g-small",
    dependencies=["transformers", "torch"],
)
```

### 3. HTTP API
The Jobs service exposes an OpenAPI-compatible HTTP endpoint for integrations that cannot use the CLI or Python client.

## Workload Types

### UV Workloads (Python)
The simplest path for Python users. `hf jobs uv run` installs dependencies and runs the script in one step:
```bash
hf jobs uv run train.py --gpu
```
Self-contained UV scripts are also supported:
```bash
hf jobs uv run script.py
```

### Docker Workloads
For maximum flexibility, pass a Docker image and command:
```bash
hf jobs run <image> <command>
```
Useful when you need specific frameworks (e.g., `vllm/vllm-openai`, custom PyTorch builds) or non-Python runtimes.

## Hardware Options

- **CPU** — cheap, good for data preprocessing and lightweight tasks.
- **GPU** — standard choice for fine-tuning LLMs, diffusion, and inference. Supported variants include A100s.
- **TPU** — available via Hugging Face infrastructure for compatible workloads.

## Scheduling & Webhooks

### Scheduled Jobs
Run jobs on a cron schedule:
```bash
hf jobs run <image> <command> --schedule "*/5 * * * *"
```
Supported aliases: `@hourly`, `@daily`, `@weekly`, `@monthly`.

### Webhook-Triggered Jobs
Trigger jobs automatically when a repository is updated. For example:
- Re-evaluate a model whenever a new version is uploaded.
- Re-run data processing when a dataset changes.

Webhook payloads contain enough context (e.g., updated model repo) for the job to act on the event.

## Pay-As-You-Go Pricing

- Compute is billed **per second** for the selected hardware.
- No long-term reservations or minimums required.
- Ingress and egress follow standard Hub pricing and cloud-provider rates.

## Ideal Use Cases

| Scenario | Why HF Jobs |
|----------|--------------|
| Fine-tuning models | Spin up a GPU job, pay only for training time |
| Batch inference / evaluation | Parallelize across many jobs |
| Data ingestion & processing | CPU/GPU preprocessing without infra |
| Automated retraining pipelines | Schedule jobs or react to webhooks |
| Prototyping without cloud accounts | No AWS/GCP/Azure setup required |

## Key Facts

- Hugging Face Jobs provide compute for AI and data workflows on HF-managed infrastructure.
- Two primary interfaces: **UV-like** for Python workloads (`hf jobs uv run`) and **Docker-like** for anything else (`hf jobs run`).
- Supports **CPU, GPU, and TPU** hardware.
- Jobs can be **scheduled** with cron syntax or triggered by **webhooks** on repository updates.
- Billing is **per-second**, making it cost-effective for short or intermittent workloads.
- Accessible via **HF CLI**, **huggingface_hub Python client**, or **HTTP API**.

## References

- **Docs**: https://huggingface.co/docs/huggingface_hub/en/guides/jobs
- **Quickstart**: https://huggingface.co/docs/huggingface_hub/en/guides/jobs
- **Pricing**: https://huggingface.co/docs/hub/main/en/jobs-pricing
- **Python SDK**: https://huggingface.co/docs/huggingface_hub/package_reference/jobs
- **GitHub**: https://github.com/huggingface/hub-docs
- **Detailed API surface & pricing table**: [references/api-surface-and-pricing-2025.md](references/api-surface-and-pricing-2025.md)
