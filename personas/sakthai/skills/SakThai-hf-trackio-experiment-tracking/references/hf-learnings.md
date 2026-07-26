# HF Learnings: hf-trackio-experiment-tracking

## 2026-07-25: hf-trackio-experiment-tracking — Hugging Face Trackio: Free Experiment Tracking with Buckets and Spaces (Topic #367)

### Summary
Comprehensive deep-dive into **Trackio** (`huggingface-trackio`) — Hugging Face's lightweight, free experiment tracking Python library built on top of Storage Buckets and Spaces. Trackio is a drop-in replacement for WandB/MLflow with a core codebase of <3,000 lines, designed for zero-cost experiment tracking. Key differentiator: everything including hosting on Hugging Face is **free**. Integrates with Transformers (via `TrackioCallback`), TRL (via `TrackioTRL`), and general Python training loops. Features a Gradio dashboard that can run locally, on Hugging Face Spaces (free), or on a self-hosted server. Agent-friendly CLI and Python APIs designed for autonomous ML experiments.

### Key Findings

| Area | Finding |
|------|---------|
| **What it is** | Lightweight, free experiment tracking library built on HF Buckets + Spaces. Drop-in WandB replacement. <3k lines Python. |
| **Storage backend** | HF Storage Buckets (free tier). `TRACKIO_BUCKET_ID` env var. Dataset-based storage (`TRACKIO_DATASET_ID`) is deprecated. |
| **Dashboard** | Gradio-based. Three modes: local (`trackio show`), HF Space (`trackio init(project="org/space")`), or self-hosted server. |
| **WandB migration** | `import trackio as wandb` — identical API for `init()`, `log()`, `finish()`, `config`, `Artifact`, `Table`. |
| **CLI commands** | `trackio init`, `trackio show [--project]`, `trackio dashboard`, `trackio status` — all designed for LLM/agent use. |
| **Transformers** | `TrackioCallback` auto-logs training/eval metrics — pass to `Trainer(callbacks=[TrackioCallback()])`. |
| **TRL integration** | `TrackioTRL` callback for RL training loops with GRPO/DAPO/GSPO. |
| **Artifact support** | `trackio.Artifact(name, type)` for model checkpoints, datasets, and files stored in Buckets. |
| **Environment variables** | `TRACKIO_BUCKET_ID`, `TRACKIO_PROJECT`, `TRACKIO_SERVER_URL`, `TRACKIO_MODE` (local/space/server), `TRACKIO_DASHBOARD_PORT`, `TRACKIO_GPU_LOG_INTERVAL`, `TRACKIO_CPU_LOG_INTERVAL`, `TRACKIO_WEBHOOK_MIN_LEVEL` |
| **MCP integration** | Trackio can be used as an MCP tool via its CLI — query experiment data from agents. |
| **Self-hosted mode** | Deploy dedicated trackio server for teams. Dashboard accessible via browser, log runs from any machine. |
| **Agent-friendly** | CLI commands designed for LLM invocation. Structured outputs for experiment queries. |

### Core API Reference

| Function | Signature | Description |
|----------|-----------|-------------|
| `trackio.init()` | `init(project, config=None, tags=None, name=None, id=None, resume=None, reinit=None, anonymous=None, group=None, job_type=None, mode=None, bucket_id=None, server_url=None, dashboard_port=None, gpu_log_interval=None, cpu_log_interval=None, webhook_min_level=None)` | Initialize a run. Identical signature to wandb.init. Sets up logging context. |
| `trackio.log()` | `log(metrics, step=None, commit=None)` | Log metrics dict to current run. Auto-increments step. |
| `trackio.finish()` | `finish(exit_code=None)` | End current run, flush remaining data. |
| `trackio.config` | Property | Dict-like config for hyperparameters. |
| `trackio.summary` | Property | Dict-like summary metrics (final values). |
| `trackio.Artifact()` | `Artifact(name, type, description=None, metadata=None)` | Log artifacts (models, datasets, files). |
| `trackio.Table()` | `Table(dataframe, columns=None, rows=None)` | Log tabular data. |
| `trackio.alert()` | `alert(title, text, level=AlertLevel.INFO)` | Send alerts via webhook. |
| `trackio.show()` | `show(project=None, port=None, host=None)` | Launch dashboard. |
| `trackio.status()` | `status()` | Check logging status. |

### Dashboard Deployment Modes

| Mode | Command/Config | Storage | Cost |
|------|---------------|---------|------|
| **Local** | `trackio show` | Local filesystem | Free |
| **HF Space** | `trackio.init(project="org/space_id")` | HF Bucket via TRACKIO_BUCKET_ID | Free (Spaces + Buckets free tier) |
| **Self-hosted** | `trackio.init(server_url="...")` | Server's storage | Server hosting costs |

### Integration Quickstart

**Basic usage (WandB-compatible):**
```python
import trackio as wandb  # drop-in replacement

wandb.init(project="my-experiment", config={"lr": 1e-4, "epochs": 10})
for epoch in range(10):
    train_loss = compute_loss()
    wandb.log({"train/loss": train_loss, "epoch": epoch})
wandb.finish()
```

**With Transformers:**
```python
from trackio.integrations.transformers import TrackioCallback
from transformers import Trainer, TrainingArguments

trainer = Trainer(
    model=model,
    args=TrainingArguments(output_dir="./output"),
    callbacks=[TrackioCallback()],
)
trainer.train()
```

**With TRL (GRPO/DAPO/GSPO):**
```python
from trackio.integrations.trl import TrackioTRL

trainer = GRPOTrainer(..., callbacks=[TrackioTRL()])
trainer.train()
```

### Zero-Cost Patterns
- Dashboard on HF Spaces: zero hosting cost, persistent storage via free Bucket tier
- `import trackio as wandb`: instant migration from paid WandB to free tracking
- Local dashboard for personal use: no infrastructure required
- Artifacts stored in Buckets: free tier covers small-to-medium experiments
- Agent/LLM use: CLI commands structured for autonomous execution

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRACKIO_BUCKET_ID` | None | HF Storage Bucket ID for persistence |
| `TRACKIO_PROJECT` | None | Default project name |
| `TRACKIO_SERVER_URL` | None | Self-hosted server URL |
| `TRACKIO_MODE` | `local` | `local`, `space`, or `server` |
| `TRACKIO_DASHBOARD_PORT` | 7860 | Dashboard port |
| `TRACKIO_HOST` | 127.0.0.1 | Dashboard host |
| `TRACKIO_GPU_LOG_INTERVAL` | 10 | GPU metrics logging interval (steps) |
| `TRACKIO_CPU_LOG_INTERVAL` | 10 | CPU metrics logging interval (steps) |
| `TRACKIO_WEBHOOK_MIN_LEVEL` | `INFO` | Minimum alert level for webhook |
| `TRACKIO_VERBOSE` | True | Enable verbose logging |

### Skill Created
`hf-trackio-experiment-tracking/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md covering Trackio architecture, API reference (10+ functions), dashboard deployment modes (local/space/server), integrations (Transformers, TRL), CLI commands, environment variables (11 vars), zero-cost patterns, and WandB migration guide.

### Sources
- https://huggingface.co/docs/trackio/en/index
- https://huggingface.co/docs/trackio/en/quickstart
- https://huggingface.co/docs/trackio/en/dashboard
- https://huggingface.co/docs/trackio/en/server
- https://huggingface.co/docs/trackio/en/api
- https://huggingface.co/docs/trackio/en/environment-variables
- https://huggingface.co/docs/trackio/en/transformers
- https://huggingface.co/docs/trackio/en/trl
- https://huggingface.co/docs/trackio/en/migrating
