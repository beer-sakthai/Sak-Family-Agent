# Hugging Face Jobs — API Surface & Pricing reference (2025-06)

## Current Python SDK (huggingface_hub v1.20.1+)

Entry points:
- `run_job(image, command, flavor, timeout, volumes, env, secrets, labels, ssh, namespace)`
- `run_uv_job(script, flavor, dependencies, script_args, timeout, volumes, env, secrets, labels)`
- `wait_for_job(job_id, timeout)` — blocks; non-failing even on ERROR/CANCELED.
- `list_jobs()`, `inspect_job(job_id)`, `cancel_job(job_id)`
- `fetch_job_logs(job_id)` — generator yielding log lines.
- `fetch_job_metrics(job_id)` — generator yielding dicts with `cpu_usage_pct`, `cpu_millicores`, `memory_used_bytes`, `memory_total_bytes`, `rx_bps`, `tx_bps`, `gpus`, `replica`.
- `update_job_labels(job_id, labels)` / `update_scheduled_job_labels(scheduled_job_id, labels)`
- `list_jobs_hardware()` — returns full flavor catalog.
- `create_scheduled_job(...)`, `list_scheduled_jobs()`, `inspect_scheduled_job(...)`, `delete_scheduled_job(...)`
- `create_scheduled_uv_job(...)`

## CLI commands

```bash
hf jobs run <image> <command> [--flavor <tier>] [--schedule <cron>] [--timeout <dur>]
hf jobs uv run <script.py|url> [--flavor <tier>] [--image <docker>]
hf jobs list | ps
hf jobs logs|metrics|inspect|wait|ssh|cancel|hardware|labels <id>
hf jobs scheduled run|list|inspect|delete|labels
```

`--schedule` accepts cron strings or aliases: `@hourly`, `@daily`, `@weekly`, `@monthly`, `@yearly`, `@annually`.

`hf jobs wait <id1> <id2>` exits 0 only if all succeeded; good for chaining.

## Hardware flavors (snapshot 2025-06)

| Flavor | Accelerator | vCPU | RAM | Storage | $/hr |
|--------|-------------|------|-----|---------|------|
| cpu-basic | — | 2 | 16 GB | 50 GB | $0.01 |
| cpu-upgrade | — | 8 | 32 GB | 50 GB | $0.03 |
| cpu-performance | — | 32 | 256 GB | 1024 GB | $1.90 |
| cpu-xl | — | 16 | 124 GB | 1000 GB | $1.00 |
| t4-small | 1× T4 16 GB | 4 | 15 GB | 50 GB | $0.40 |
| t4-medium | 1× T4 16 GB | 8 | 30 GB | 100 GB | $0.60 |
| a10g-small | 1× A10G 24 GB | 4 | 15 GB | 110 GB | $1.00 |
| a10g-large | 1× A10G 24 GB | 12 | 46 GB | 200 GB | $1.50 |
| a10g-largex2 | 2× A10G 48 GB | 24 | 92 GB | 1000 GB | $3.00 |
| a10g-largex4 | 4× A10G 96 GB | 48 | 184 GB | 2000 GB | $5.00 |
| a100-large | 1× A100 80 GB | 12 | 142 GB | 1000 GB | $2.50 |
| a100x4 | 4× A100 320 GB | 48 | 568 GB | 4000 GB | $10.00 |
| a100x8 | 8× A100 640 GB | 96 | 1136 GB | 8000 GB | $20.00 |
| h200 | 1× H200 141 GB | 23 | 256 GB | 3000 GB | $5.00 |
| h200x2 | 2× H200 282 GB | 46 | 512 GB | 6000 GB | $10.00 |
| h200x4 | 4× H202 564 GB | 92 | 1024 GB | 12000 GB | $20.00 |
| h200x8 | 8× H200 1128 GB | 184 | 2048 GB | 24000 GB | $40.00 |
| rtx-pro-6000 | 1× RTX PRO 6000 96 GB | 23 | 256 GB | 475 GB | $2.75 |
| rtx-pro-6000x2 | 2× RTX PRO 6000 192 GB | 46 | 512 GB | 950 GB | $5.50 |
| rtx-pro-6000x4 | 4× RTX PRO 6000 384 GB | 92 | 1024 GB | 1900 GB | $11.00 |
| rtx-pro-6000x8 | 8× RTX PRO 6000 768 GB | 184 | 2048 GB | 3800 GB | $22.00 |
| l4x1 | 1× L4 24 GB | 8 | 30 GB | 400 GB | $0.80 |
| l4x4 | 4× L4 96 GB | 48 | 186 GB | 3200 GB | $3.80 |
| l40sx1 | 1× L40S 48 GB | 8 | 62 GB | 380 GB | $1.80 |
| l40sx4 | 4× L40S 192 GB | 48 | 382 GB | 3200 GB | $8.30 |
| l40sx8 | 8× L40S 384 GB | 192 | 1534 GB | 6500 GB | $23.50 |

## Built-in environment variables

- `JOB_ID`
- `ACCELERATOR` (empty on CPU-only)
- `CPU_CORES`
- `MEMORY`

## Volumes

```python
from huggingface_hub import Volume
Volume(type="model", source="owner/repo", mount_path="/path")
Volume(type="dataset", source="owner/repo", mount_path="/path")
Volume(type="bucket", source="owner/bucket", mount_path="/path", read_only=False)
```

Mounts are read/write by default for buckets; `read_only=True` for datasets/models.

## Timeout formats

Numeric seconds or strings with units: `s`, `m`, `h`, `d`. Default: 30 minutes.

## Sources

- Docs: https://huggingface.co/docs/huggingface_hub/en/guides/jobs
- Source: observed via `browser_console` on `huggingface.co/docs` (v1.20.1 main, EN).
