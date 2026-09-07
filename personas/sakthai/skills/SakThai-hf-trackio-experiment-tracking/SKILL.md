---
name: SakThai-hf-trackio-experiment-tracking
description: "Comprehensive deep-dive into Trackio — Hugging Faces lightweight, free experiment tracking library built on Storage Buckets and Spaces."
---

# hf-trackio-experiment-tracking

## Description
Comprehensive deep-dive into **Trackio** — Hugging Face's lightweight, free experiment tracking library built on top of Storage Buckets and Spaces. Covers the full API surface, dashboard deployment (local and Spaces), server mode, environment configuration, integrations with Transformers and TRL, migration from WandB, and agent-friendly CLI design.

Trackio is a zero-cost alternative to WandB/MLflow with <3k lines of Python, designed for autonomous ML experiments with LLM-friendly CLI commands and Python APIs.

## Key Concepts
- **Free & Lightweight** — <3,000 lines Python, everything free including HF-hosted dashboard
- **Drop-in WandB replacement** — `import trackio as wandb` for instant migration
- **Storage via Buckets** — Persists to HF Storage Buckets (free tier); Dataset storage deprecated
- **Dashboard on Spaces** — Deploy the Gradio dashboard to HF Spaces for free
- **Self-hosted server** — Optional dedicated trackio server for team use
- **Integrations** — `TrackioCallback` for Transformers, `TrackioTRL` for TRL training
- **Agent-friendly** — CLI commands (`trackio init`, `trackio show`, `trackio dashboard`) designed for LLM use
- **MCP server** — Can be used as an MCP tool for experiment querying

## Core API
| Function | Description |
|----------|-------------|
| `trackio.init(project, config, ...)` | Initialize a run (like wandb.init) |
| `trackio.log(metrics_dict)` | Log metrics (like wandb.log) |
| `trackio.finish()` | End the current run |
| `trackio.show()` | Launch the dashboard |
| `trackio.Artifact(name, type)` | Log artifacts |
| `trackio.Table(dataframe)` | Log tabular data |

## References
- `references/hf-learnings.md` — full research notes with architecture, API reference, and practical patterns

## Metadata
- **author**: SakThai
- **license**: MIT
- **created**: 2026-07-25
- **topic**: hf-trackio-experiment-tracking
