---
name: SakThai-hf-jobs-uv-run
description: "Run Python UV scripts with inline dependencies on Hugging Face Jobs infrastructure\
  \ \u2014 zero setup, free-tier CPU ($0.01/hr), paid GPU options. Covers `hf jobs\
  \ uv run`, `hf jobs run`, `hf jobs ssh`, hardware flavors, and integration patterns\
  \ for the Sak"
---

# 🚀 HF Jobs UV Run — Zero-Infrastructure Remote Compute

## Overview

`hf jobs uv run` lets you run Python scripts on Hugging Face Jobs infrastructure **without setting up any infrastructure**. You write a Python script with inline UV-style dependencies and run it remotely with one command:

```bash
hf jobs uv run my_script.py
```

The script gets uploaded to HF, runs on a remote container, installs deps automatically via UV, streams output back to you, and the machine is destroyed when done.

**Cost:** CPU-basic = **$0.0002/min ($0.01/hr)** — essentially free for short tasks. GPU flavors start at $0.0067/min (T4).

## When to Use

| Scenario | Why HF Jobs UV Run |
|----------|-------------------|
| **Evaluation scripts** | Run LightEval/lm-eval without local GPU |
| **Data processing** | Crunch HF datasets without local storage |
| **Model inference** | Test models on cheap GPU on demand |
| **Training small models** | Fine-tune with TRL/PEFT on $0.40/hr T4 |
| **Batch inference** | Run inference on many models in parallel |
| **CI/CD pipelines** | No infra setup, just `hf jobs uv run` |
| **Quick experiments** | Throwaway script, no venv management |

## How It Works

1. Write a Python script with a **UV inline script** header (dependencies declared at top)
2. Run `hf jobs uv run script.py` — the CLI uploads it to HF Jobs
3. HF Jobs launches a container, installs dependencies via UV (cached per script)
4. Script executes, output streams back to your terminal
5. Container auto-terminates (default idle 10 min, or `--timeout`)

### Inline Dependency Format

Your script must use the [UV inline script metadata format](https://docs.astral.sh/uv/guides/scripts/):

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "torch>=2.0",
#     "transformers>=4.40",
#     "datasets>=3.0",
# ]
# ///
import torch
from transformers import pipeline
print(torch.__version__)
```

## CLI Reference

### Basic Commands

```bash
# Run a local script on free CPU
hf jobs uv run evaluate_model.py

# Run with a custom name
hf jobs uv run --name my-eval evaluate_model.py

# Run with GPU (T4 small = $0.40/hr)
hf jobs uv run --flavor t4-small train.py

# Run with extra dependencies beyond script metadata
hf jobs uv run --with "accelerate>=1.0" train.py

# Mount a model or dataset from HF Hub
hf jobs uv run -v hf://org/model:/data script.py

# Run in background (detached)
hf jobs uv run --detach long_task.py

# Expose a port (e.g., for a web server in the job)
hf jobs uv run --expose 8000 app.py

# Set environment variables
hf jobs uv run -e HF_HUB_OFFLINE=1 script.py
hf jobs uv run --secrets HF_TOKEN benchmark.py

# Set Python version
hf jobs uv run -p 3.12 script.py
```

### Hardware Flavors

| Flavor | vCPU | RAM | GPU | Cost/hr |
|--------|------|-----|-----|---------|
| `cpu-basic` | 2 | 16 GB | — | **$0.01** |
| `cpu-upgrade` | 8 | 32 GB | — | $0.03 |
| `t4-small` | 4 | 15 GB | 1× T4 (16 GB) | $0.40 |
| `t4-medium` | 8 | 30 GB | 1× T4 (16 GB) | $0.60 |
| `a10g-small` | 4 | 15 GB | 1× A10G (24 GB) | $1.00 |
| `l4x1` | 8 | 30 GB | 1× L4 (24 GB) | $0.80 |
| `a100-large` | 12 | 142 GB | 1× A100 (80 GB) | $2.50 |
| `h200` | 23 | 256 GB | 1× H200 (141 GB) | $5.00 |

Full list: `hf jobs hardware`

### Related CLI Commands

```bash
# Run a raw Docker image command
hf jobs run python:3.12 python -c "print('hello')"

# SSH into a running job (needs SSH key on HF settings)
hf jobs run --ssh python:3.12 python -m http.server 8000
# Then: hf jobs ssh <job_id>

# List running jobs
hf jobs ls

# Get logs of a completed job
hf jobs logs <job_id>

# Wait for job completion
hf jobs wait <job_id>

# Cancel a job
hf jobs cancel <job_id>
```

## Real-World Examples

### 1. Quick Model Evaluation with LightEval

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["lighteval", "transformers", "torch"]
# ///
from lighteval import runner
# ... evaluation code ...
```

```bash
hf jobs uv run --flavor a10g-small --timeout 30m eval.py
```

### 2. Dataset Processing

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["datasets>=5.0", "huggingface-hub>=0.27"]
# ///
from datasets import load_dataset
ds = load_dataset("sakthai/my-dataset", split="train")
# Process and push results
ds.push_to_hub("sakthai/processed-dataset")
```

```bash
hf jobs uv run --flavor cpu-upgrade --timeout 10m process_data.py
```

### 3. Fine-Tune with TRL

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["torch", "transformers", "trl>=0.15", "peft", "datasets"]
# ///
from trl import SFTTrainer
# ... training code ...
```

```bash
hf jobs uv run --flavor a10g-small --timeout 2h train.py
```

### 4. Batch Inference from Hub Models

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["torch", "transformers", "datasets"]
# ///
from transformers import pipeline
pipe = pipeline("text-classification", model="sakthai/my-model")
# Process dataset and save results
```

```bash
hf jobs uv run --flavor t4-small -v hf://sakthai/my-model:/model inference.py
```

## Pro Tips

### ⚡ Cost Optimization
- **CPU-basic is essentially free** ($0.01/hr) — use for data processing, evals, and scripting
- **Use `--timeout`** to prevent runaway costs (e.g., `--timeout 30m`)
- **Use `--detach`** for long jobs, then `hf jobs logs <id>` to check results
- **Scripts are cached** — re-running the same script reuses the cached environment

### 🔧 Best Practices
- **Declare ALL dependencies** in the UV header — missing deps cause runtime failures
- **Use `--with` for one-off packages** you don't want in the script header
- **Mount models with `-v`** instead of downloading inside the script for speed
- **Use `--secrets HF_TOKEN`** to pass your HF token for gated model access
- **Keep scripts small** — the script + deps must fit in the container

### 🚫 Known Limitations
- Max job lifetime: 24 hours (hard limit)
- Script + dependencies must install within `--timeout`
- No persistent storage between runs (use HF Hub to save results)
- The `hf jobs uv run` feature is experimental (`HF_HUB_DISABLE_EXPERIMENTAL_WARNING=1` to suppress)

## Verification

```bash
# Quick test — runs on free CPU
hf jobs uv run --name test-jobs --flavor cpu-basic --timeout 30s \
  - <<'EOF'
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# ///
import sys
print(f"Hello from HF Jobs! Python {sys.version}")
EOF
```

## References

- [hf CLI guide](https://huggingface.co/docs/huggingface_hub/guides/cli)
- [huggingface_hub release notes](https://github.com/huggingface/huggingface_hub/releases)
- [UV script format](https://docs.astral.sh/uv/guides/scripts/)
- [HF Jobs documentation](https://huggingface.co/docs/hub/en/jobs)
