# HF Learnings: Serving Models on HF Jobs — One-Command Patterns

**author:** SakThai
**license:** MIT

## 2026-07-25: hf-jobs-serving-vllm — One-Command Model Serving on HF Jobs (Topic #365)

### Summary

Comprehensive deep-dive into running inference servers on **Hugging Face Jobs** using the `hf jobs run` CLI one-command pattern. Unlike the Python SDK approach (covered in `hf-jobs-api-deep-dive`), the CLI provides a zero-friction path: `hf jobs run --detach --expose <port> --flavor <hardware> -s HF_TOKEN <image> -- <server-command>`. Supports vLLM (default), SGLang, llama.cpp, and any HTTP server. Covers the full lifecycle — deployment, authentication, endpoint URL format, model download acceleration, billing, and cost optimization. Designed for ephemeral inference: cancel the job, the endpoint disappears, billing stops.

### Key Findings

| Area | Finding |
|------|---------|
| **CLI one-liner** | `hf jobs run --detach --expose 8000 --flavor a10g-small -s HF_TOKEN vllm/vllm-openai -- vllm serve <model>` |
| **`--` separator** | Required when the job command has its own flags — separates `hf jobs run` options from the command's args |
| **`--detach`** | Returns immediately; server runs in background until cancelled or timeout |
| **`--expose <port>`** | Makes ports reachable at `https://{job.id}--{port}.hf.jobs` |
| **`-s HF_TOKEN`** | Forwards your HF token as a secret for authenticated model downloads (gated models, higher rate limits) |
| **Default timeout** | 30 minutes; set `--timeout` to override |
| **Cancel** | `hf jobs cancel <job_id>` — stops billing immediately |
| **Auth for endpoint** | Exposed ports require Bearer token with `read` access to the job's namespace |
| **OpenAI-compatible** | vLLM, SGLang, llama.cpp all speak the OpenAI-compatible API — drop into any OpenAI client |
| **Model download** | Jobs auto-forward HF token for downloads; gated/private models work without extra config |
| **Pricing** | Pay-per-minute for hardware + $0.01/min for exposed ports (flat rate per job) |

### 1. The One-Command Pattern

The core pattern is simpler than the Python SDK equivalent:

```bash
# Start a vLLM server with LFM2.5 on an A10G
hf jobs run \
  --detach \
  --expose 8000 \
  --flavor a10g-small \
  -s HF_TOKEN \
  vllm/vllm-openai \
  -- \
  vllm serve LiquidAI/LFM2.5-8B-A1B --max-model-len 8192
```

**What happens:**
1. An A10G-small GPU instance spins up
2. The `vllm/vllm-openai` Docker image starts
3. vLLM loads LFM2.5-8B-A1B (model downloaded via authenticated HF token)
4. Port 8000 is exposed at `https://{job.id}--8000.hf.jobs`
5. Job runs in background (`--detach`)

**The `--` separator:** Everything after `--` is the command run inside the container. Without it, vLLM's flags (like `--max-model-len`) would be parsed as `hf jobs run` options.

### 2. The Endpoint URL

```
https://{job.id}--{port}.hf.jobs
```

- Each exposed port gets its own URL
- Requires an HF token with `read` permission to the job's namespace
- Slots directly into any OpenAI-compatible client as the `base_url`:
  ```python
  from openai import OpenAI
  client = OpenAI(
      base_url="https://abc123--8000.hf.jobs/v1",
      api_key="hf_your_token"
  )
  ```
- These URLs work from scripts, notebooks, and agents — everywhere you'd use OpenAI-compatible API
- They cannot be opened directly in a browser

### 3. Supported Server Images

| Server | Image | Use Case |
|--------|-------|----------|
| **vLLM** | `vllm/vllm-openai` | Default high-throughput LLM serving; any Transformers model |
| **SGLang** | `lmsysorg/sglang` | Structured outputs, constrained generation |
| **llama.cpp** | `ghcr.io/ggml-org/llama.cpp:server-cuda` | GGUF-quantized models, CPU/GPU |
| **Any HTTP server** | Custom image | Any server that speaks HTTP |

### 4. Serving GGUF Models with llama.cpp

```bash
hf jobs run \
  --detach \
  --expose 8080 \
  --flavor a10g-small \
  -s HF_TOKEN \
  -v hf://ggml-org/gemma-4-E4B-it-GGUF:/model:ro \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -- \
  /app/llama serve --host 0.0.0.0 --port 8080 -ngl 99
```

Key differences from vLLM:
- Uses **volume mount** (`-v hf://repo:/path:ro`) to pull GGUF files from the Hub
- The volume mount reads directly from the GGUF repo (`ggml-org/gemma-4-E4B-it-GGUF`)
- `-ngl 99` offloads all layers to GPU
- Alternatively, llama.cpp can pull models inline: `/app/llama serve -hf ggml-org/gemma-4-E4B-it-GGUF`

### 5. Lifecycle Management

```bash
# List running jobs
hf jobs list

# Get job status and logs
hf jobs logs <job-id>

# Cancel a job (stops billing)
hf jobs cancel <job-id>

# Set custom timeout (default: 30m)
hf jobs run --timeout 2h ...
```

**Billing lifecycle:**
- Charged per minute only while status is `Starting` or `Running`
- No cost during Docker image build phase
- Billing stops immediately when you cancel the job or timeout is reached
- Exposed ports add $0.01/min flat rate per job (not per port)

### 6. Pricing Reference (USD per hour)

| Flavor | vCPU | RAM | GPU Memory | Storage | Price/hr |
|--------|------|-----|-----------|---------|---------|
| CPU Basic | 2 | 16 GB | — | 50 GB | $0.01 |
| CPU Upgrade | 8 | 32 GB | — | 50 GB | $0.03 |
| Nvidia T4-small | 4 | 15 GB | 16 GB | 50 GB | $0.40 |
| Nvidia T4-medium | 8 | 30 GB | 16 GB | 100 GB | $0.60 |
| **1x Nvidia L4** | **8** | **30 GB** | **24 GB** | **400 GB** | **$0.80** |
| **Nvidia A10G-small** | **4** | **15 GB** | **24 GB** | **110 GB** | **$1.00** |
| **Nvidia A10G-large** | **12** | **46 GB** | **24 GB** | **200 GB** | **$1.50** |
| 1x Nvidia L40S | 8 | 62 GB | 48 GB | 380 GB | $1.80 |
| Nvidia A100-large | 12 | 142 GB | 80 GB | 1000 GB | $2.50 |
| Nvidia H200 | 23 | 256 GB | 141 GB | 3000 GB | $5.00 |
| Exposed ports (flat) | — | — | — | — | **+$0.01/min** |

**Most practical for small models:** T4-small ($0.40/hr) or A10G-small ($1.00/hr)

### 7. Best Practices for Zero-Cost Operation

- **CPU Basic ($0.01/hr):** For testing endpoints with small GGUF models via llama.cpp. A quantized 0.5B–1.5B model runs fine on CPU.
- **T4-small ($0.40/hr):** Cheapest GPU option. Use with quantized 7B models or smaller.
- **Short timeouts:** Set `--timeout 5m` for quick tests so jobs auto-cancel if forgotten.
- **`--detach` always:** Without it, the CLI blocks — if your terminal disconnects, the job keeps running (and billing). Detach and cancel explicitly.
- **Monitor with `hf jobs list`** to catch orphaned jobs.
- **Pre-pull models locally** if testing multiple times — Jobs downloads the model each time.
- **Use the `/v1/models` endpoint** to confirm your server loaded correctly:
  ```bash
  curl -H "Authorization: Bearer $HF_TOKEN" https://{job.id}--8000.hf.jobs/v1/models
  ```

### 8. Comparison: CLI vs Python SDK

| Aspect | CLI (`hf jobs run`) | Python SDK (`run_job()`) |
|--------|-------------------|-------------------------|
| Setup | Zero — CLI built into `huggingface_hub` | Import `run_job` from `huggingface_hub` |
| One-liner | Yes | 5+ lines |
| Detach mode | `--detach` flag | Must manage yourself |
| Auth forwarding | `-s HF_TOKEN` | `secrets={"HF_TOKEN": ...}` in code |
| Volume mounts | `-v hf://repo:/path` | `Volume` dataclass |
| Best for | Ad-hoc, interactive, quick tests | Programmatic, automated, CI/CD |

### 9. Sources

- https://huggingface.co/docs/hub/en/jobs-serving — official Serve Models docs
- https://huggingface.co/blog/vllm-jobs — "Run a vLLM Server on HF Jobs in One Command" blog post (June 26, 2026)
- https://huggingface.co/docs/hub/en/jobs-pricing — hardware pricing table
- https://huggingface.co/docs/hub/en/jobs-quickstart — Jobs quickstart guide
- https://huggingface.co/docs/hub/en/jobs-manage — job lifecycle management

---

