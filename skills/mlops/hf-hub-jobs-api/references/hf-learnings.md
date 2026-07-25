# HF Hub Jobs API — Comprehensive Deep Dive

**Topic:** hf-hub-jobs-api-deep-dive  
**Learned:** 2026-07-25  
**Author:** SakThai  
**License:** MIT  
**Source:** huggingface_hub source code, HF OpenAPI spec (`/.well-known/openapi.json`), HF docs, live API probing

---

## 1. What Are HF Jobs?

HF Jobs is Hugging Face's **managed compute service** — akin to AWS Batch, Google Cloud Batch, or Fly Machines, but tightly integrated with the Hugging Face Hub. A Job is an ephemeral workload that:

- Runs a Docker container on HF's infrastructure
- Has a defined lifecycle (queued → running → completed/failed/cancelled)
- Supports CPU and GPU hardware flavors
- Outputs logs that are accessible via the Hub API
- Can be triggered programmatically, via CLI, or via Hub webhooks

**Key architectural insight:** Jobs are the **lowest-level compute primitive** on the HF Hub. Both **Sandboxes** and **Spaces** build on top of Jobs:
- A **Sandbox** is a Job running the `sbx-server` static binary
- A **Space** is a long-running Job with an HTTP server that stays alive

---

## 2. REST API Endpoints

From the HF OpenAPI spec at `/.well-known/openapi.json`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/jobs` | List jobs (with status filter) |
| `POST` | `/api/jobs` | Create a new job |
| `GET` | `/api/jobs/{jobId}` | Get job status and metadata |
| `DELETE` | `/api/jobs/{jobId}` | Cancel/delete a job |
| `GET` | `/api/jobs/{jobId}/logs` | Get job logs |

The `huggingface_hub` library wraps all 5 endpoints. The Jobs API uses the same
authentication as all Hub APIs — `Authorization: Bearer hf_...` header with
write scope for mutations, read scope for status queries.

---

## 3. Python API — Complete Reference

### Creating a Job

```python
from huggingface_hub import HfApi

api = HfApi()

# Minimal — uses defaults
job = api.create_job(
    image="python:3.12",
    command=["python", "-c", "print(40+2)"],
)

# Full parameter set
job = api.create_job(
    image="pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel",
    command=["python", "train.py", "--epochs", "10"],
    flavor="t4-small",              # hardware SKU
    sleep_time=3600,                 # idle timeout (seconds)
    storage="small",                 # persistent storage size
    env={"DATASET": "my/dataset"},   # environment variables
    secrets=[{"key": "WANDB_API", "value": "..."}],  # secrets
    webhook="https://my.webhook.com/complete",  # completion callback
)
```

**Return value:** A `Job` object with `.id` (string), `.state` (enum), `.image`,
`.flavor`, `.created_at`, etc.

### Listing Jobs

```python
# All jobs
jobs = api.list_jobs()

# Filter by status
running_jobs = api.list_jobs(status="RUNNING")
completed_jobs = api.list_jobs(status="COMPLETED")
```

**Status filter values:** `"CREATED"`, `"QUEUED"`, `"RUNNING"`, `"COMPLETED"`,
`"FAILED"`, `"CANCELLED"`.

### Getting Job Status

```python
status = api.get_job_status(job_id="my-job-id")
print(f"State: {status.state}")         # e.g. "RUNNING"
print(f"Created: {status.created_at}")
print(f"Duration: {status.duration_s}s")
print(f"Hardware: {status.flavor}")
```

The status object includes:
- `state` — current lifecycle state
- `created_at` / `started_at` / `completed_at` — timestamps
- `duration_s` — elapsed/wall-clock seconds
- `flavor` — hardware SKU
- `image` — Docker image
- `exit_code` — for completed/failed jobs (0 = success)

### Fetching Logs

```python
# As list of strings
logs = api.get_job_logs(job_id="my-job-id")
for line in logs:
    print(line)  # Each line is stdout or stderr output

# As raw text
raw_logs = api.get_job_logs(job_id="my-job-id", raw=True)
```

### Cancelling a Job

```python
api.cancel_job(job_id="my-job-id")
```

Cancellation is asynchronous — the job may take a few seconds to transition
from `RUNNING` to `CANCELLED`.

---

## 4. CLI Reference — `hf jobs`

### Core Commands

```bash
# Run a job
hf jobs run python:3.12 -- "python -c 'print(42)'"

# With GPU and environment
hf jobs run pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel \
  --flavor t4-small \
  --env EPOCHS=10 \
  --env LR=1e-4 \
  -- python train.py

# List jobs
hf jobs list

# Filter by status
hf jobs list --status RUNNING

# Get status
hf jobs status <job-id>

# Cancel
hf jobs cancel <job-id>

# Resource stats
hf jobs stats

# Run with inline script (uv support)
hf jobs uv -- "uv run python -c 'import numpy; print(numpy.__version__)'"
```

### `hf jobs run` — All Flags

| Flag | Type | Description | Default |
|------|------|-------------|---------|
| `--flavor` | string | Hardware SKU | `cpu-basic` |
| `--sleep-time` | int | Idle timeout seconds | `3600` |
| `--storage` | string | Persistent storage size | None |
| `--env` | string[] | Environment variables (`KEY=VAL`) | None |
| `--secret` | string[] | Secret keys to inject | None |
| `--webhook` | string | Completion webhook URL | None |
| `--name` | string | Human-readable job name | None |

### `hf jobs stats`

Shows your current resource usage across all jobs:

```bash
$ hf jobs stats
Current Usage:
  CPU: 2 of 10 allowed
  GPU: 0 of 2 allowed
  Running Jobs: 1
  Queued Jobs: 0
  Monthly Compute Used: 12.3 CPU-hours, 0 GPU-hours
```

---

## 5. Job Lifecycle — Deep Dive

### State Transitions

```
          ┌─────────────────────────────────────────┐
          │                                         │
          v                                         │
   CREATED ──→ QUEUED ──→ RUNNING ──→ COMPLETED    │
                            │          FAILED      │
                            │          CANCELLED   │
                            └──────────────────────┘
```

### State Details

| State | Meaning | Duration | Actionable? |
|-------|---------|----------|-------------|
| `CREATED` | Job definition saved, pending scheduling | ~seconds | No |
| `QUEUED` | Awaiting resource allocation | seconds–hours | Cancel |
| `RUNNING` | Container executing | varies | Cancel, logs |
| `COMPLETED` | Exited with code 0 | terminal | Fetch logs |
| `FAILED` | Exited with non-zero code | terminal | Fetch logs |
| `CANCELLED` | User-cancelled | terminal | None |

### Queue Times

Queue time depends on hardware demand:
- **cpu-basic**: Usually <30 seconds (high availability)
- **t4-small/medium**: Seconds–minutes (moderate demand)
- **a10g/a100**: Minutes–hours (high demand, lower availability)
- **h100**: May queue for hours (most constrained)

**Zero-cost tip:** For free-tier jobs (`cpu-basic`), queue times are typically
shortest during off-peak hours (UTC nighttime).

---

## 6. Hardware & Pricing

| Flavor ID | CPU | RAM | GPU | GPU RAM | Hourly Cost |
|-----------|-----|-----|-----|---------|-------------|
| `cpu-basic` | 2 vCPU | 8 GB | — | — | Free |
| `cpu-upgrade` | 8 vCPU | 32 GB | — | — | ~$0.03/hr |
| `t4-small` | 4 vCPU | 16 GB | 1× T4 | 16 GB | ~$0.15/hr |
| `t4-medium` | 8 vCPU | 32 GB | 1× T4 | 16 GB | ~$0.30/hr |
| `a10g-small` | 4 vCPU | 16 GB | 1× A10G | 24 GB | ~$0.40/hr |
| `a10g-large` | 8 vCPU | 32 GB | 1× A10G | 24 GB | ~$0.60/hr |
| `a100` | 8 vCPU | 64 GB | 1× A100 | 80 GB | ~$1.50/hr |
| `h100` | 16 vCPU | 128 GB | 1× H100 | 80 GB | ~$3.00/hr |

> ⚠️ Prices are approximate and may change. Always verify at `hf.co/pricing`.
> Free-tier `cpu-basic` has usage limits (typically 10 concurrent jobs,
> monthly CPU-hour cap).

### Disk

Each job gets ephemeral storage proportional to the flavor:
- CPU flavors: ~50 GB
- GPU flavors: ~100–200 GB

Persistent storage (via the `--storage` flag) survives job completion and can
be shared between jobs or mounted from Spaces.

---

## 7. Integration Patterns

### 7.1 Webhook-Triggered CI/CD

Jobs plus Hub webhooks create a powerful CI/CD pipeline:

```python
from huggingface_hub import HfApi

api = HfApi()

# Create a webhook that triggers a job when a dataset updates
webhook = api.create_webhook(
    job_id="eval-on-update",          # Job ID to trigger
    watched=[{"type": "repo", "value": "beer-sakthai/my-dataset"}],
    domains=["repo.update"],          # Only fire on updates
)
```

This pattern enables:
- **Model evaluation**: Trigger benchmark job when model is updated
- **Dataset processing**: Re-process dataset when source changes
- **Space rebuild**: Rebuild Space when dependencies change

### 7.2 Job → Space Checkpoint Sharing

Jobs can write to Spaces' persistent storage, making checkpoints available
immediately:

```bash
# Job writes checkpoint to shared storage
hf jobs run pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel \
  --flavor t4-small \
  --storage small \
  -- python train.py --checkpoint-dir /data/checkpoints
```

The `/data` directory persists after the job completes and can be mounted
by a Space or another job.

### 7.3 Scheduled/Renewing Jobs

While Jobs themselves don't have built-in cron scheduling, you can achieve
scheduled execution via:

1. **External cron** (GitHub Actions, cron on a VM) → POST `/api/jobs`
2. **HF Space scheduler** → deploy a minimal Space that creates jobs on timer
3. **Webhook from external service** → set up a webhook from your scheduler

### 7.4 Batch Parallel Jobs

For embarrassingly parallel workloads, create multiple jobs:

```python
import concurrent.futures
from huggingface_hub import HfApi

api = HfApi()
shard_commands = [
    ["python", "process.py", "--shard", str(i), "--total", "10"]
    for i in range(10)
]

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    futures = [
        ex.submit(api.create_job, "python:3.12", cmd, flavor="cpu-basic")
        for cmd in shard_commands
    ]
    jobs = [f.result() for f in concurrent.futures.as_completed(futures)]
```

**Free tier limit:** Typically 5–10 concurrent jobs on `cpu-basic`.

---

## 8. Zero-Cost Patterns for Beer

As a free-tier user with zero-cost constraint, these patterns maximize value:

### 8.1 Use `cpu-basic` for Everything GPU-optional

Most data processing, evaluation, and preparation can run on CPU.
Only use GPU flavors when you genuinely need CUDA (model training, large
model inference).

### 8.2 Keep Jobs Short

Free-tier CPU jobs have monthly hour caps. Optimize:
- Write efficient processing scripts (vectorize, batch)
- Use streaming to avoid downloading full datasets
- Cache intermediate results in persistent storage

### 8.3 Clean Up Runaway Jobs

Always set `sleep_time` on long-running jobs so they auto-terminate:

```python
job = api.create_job(
    image="python:3.12",
    command=["python", "long_script.py"],
    flavor="cpu-basic",
    sleep_time=7200,  # auto-kill after 2 hours idle
)
```

### 8.4 Monitor Usage

```bash
# Check remaining free tier quota
hf jobs stats
```

### 8.5 Combine with Free Tier Datasets Server

Don't download datasets inside jobs — use the **Datasets Server REST API**
to query Parquet files remotely. This avoids:
- Download time (the job spends its CPU-hour budget on I/O)
- Disk usage (ephemeral storage is limited)
- Redundant storage (dataset is already on the Hub)

### 8.6 Use `hf jobs uv` for Zero-Install Scripts

```bash
# Run a Python script with dependencies — no Docker image needed
hf jobs uv -- "uv run --with pandas,requests python -c 'import pandas; print(pandas.__version__)'"
```

The `hf jobs uv` subcommand bundles `uv` (the fast Python package installer)
so you can run ad-hoc scripts with dependencies without building a custom image.

---

## 9. Comparison With Other HF Compute Options

| Feature | Jobs | Sandboxes | Spaces | Inference Endpoints |
|---------|------|-----------|--------|-------------------|
| **Persistence** | Ephemeral (ended after job) | Ephemeral (idle_timeout) | Long-running | Long-running |
| **HTTP server** | ❌ | Optional (proxy) | ✅ (built-in) | ✅ (inference API) |
| **GPU support** | ✅ | ✅ | ✅ | ✅ |
| **Auto-scaling** | Manual (multiple jobs) | Pool (SandboxPool) | Manual replicas | Auto-scaling |
| **Free tier** | ✅ cpu-basic | ✅ cpu-basic | ✅ cpu-basic | ❌ (paid only) |
| **Max lifetime** | 24h | 24h (per sandbox) | Unlimited | Unlimited |
| **Best for** | Batch, CI/CD, evals | Interactive/agent code | Web apps, demos | Production inference |

**When to choose Jobs over Sandboxes:**
- You need a defined completion point (job ends, you fetch results)
- You're running CI/CD pipelines
- You want webhook integration (trigger on repo change)
- You don't need interactive shell access

**When to choose Sandboxes over Jobs:**
- You need to run ad-hoc commands interactively
- You're building agent tools that execute user code
- You need file upload/download during execution
- You want to proxy to an HTTP server running inside the compute

---

## 10. Practical Workflow — Model Evaluation Pipeline

A complete zero-cost evaluation pipeline:

```python
"""Evaluate a model from the Hub using HF Jobs."""
import json
from huggingface_hub import HfApi

api = HfApi()

# Step 1: Create evaluation job
job = api.create_job(
    image="python:3.12",
    command=[
        "python", "-c", """
import json
from huggingface_hub import InferenceClient

client = InferenceClient()
result = client.chat_completion(
    model="beer-sakthai/my-model",
    messages=[{"role": "user", "content": "What is 2+2?"}],
)
print(json.dumps({
    "model": "beer-sakthai/my-model",
    "response": result.choices[0].message.content,
    "status": "ok"
}))
"""
    ],
    flavor="cpu-basic",
    env={"HF_TOKEN": os.environ["HF_TOKEN"]},
)

# Step 2: Wait for completion
import time
while True:
    status = api.get_job_status(job.id)
    if status.state in ("COMPLETED", "FAILED", "CANCELLED"):
        break
    time.sleep(5)

# Step 3: Fetch results
logs = api.get_job_logs(job.id)
if status.state == "COMPLETED":
    result = json.loads(logs[-1])  # Last line is our JSON output
    print(f"Response: {result['response']}")
else:
    print(f"Job failed: {logs}")
```

---

## 11. Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ImageNotFoundError` | Docker image doesn't exist | Check image name and tag |
| `QuotaExceededError` | Reached free tier limit | Wait or upgrade plan |
| `InvalidFlavorError` | Hardware flavor doesn't exist | Use `list_spaces_hardware()` to check valid flavors |
| `JobNotFoundError` | Job ID doesn't exist | Check the job ID |
| `JobNotCancellableError` | Job already terminal | Check job state first |

### Retry Pattern

```python
from huggingface_hub import HfApi
from tenacity import retry, stop_after_attempt, wait_exponential

api = HfApi()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30))
def create_job_with_retry(**kwargs):
    return api.create_job(**kwargs)
```

---

## 12. Key Facts & Cheatsheet

- **Free tier**: `cpu-basic` flavor, limits on concurrent jobs and monthly usage
- **Max job lifetime**: 24 hours (hard limit, auto-terminated)
- **Log retention**: Logs available for ~7 days after job completion
- **Persistent storage**: `--storage small|medium|large`, survives job lifecycle
- **Webhooks**: Jobs can trigger on Hub events AND notify on completion
- **No built-in scheduling**: Use external cron + API for recurring jobs
- **Container requirements**: Any Docker image with `/bin/sh` works
- **Networking**: Jobs have outbound internet access; no inbound (no HTTP server)

---

## Sources
- HF OpenAPI spec at `/.well-known/openapi.json` — Jobs endpoints reference
- `huggingface_hub` source (hf_api.py) — Python API implementation
- HF CLI source — `hf jobs` command implementation
- HF docs at huggingface.co/docs/hub — Jobs overview
