---
name: SakThai-hf-spaces-docker
author: SakThai
license: MIT
description: "Hugging Face Spaces with Docker SDK — custom Dockerfiles, buildtime vs runtime secrets/variables, GPU support, data persistence via Storage Buckets, permissions, and hardware configuration."
version: 1.0.0
tags: [huggingface, spaces, docker, sdk, secrets, gpu, storage, mlops]
platforms: [linux, macos, windows]
related_skills: [spaces-zerogpu, huggingface-hub]
---

# HF Spaces Docker SDK — Custom Docker Spaces

Docker Spaces allow you to deploy **any app on Hugging Face** beyond Gradio and Streamlit — FastAPI, Go, Phoenix, ML Ops tools, or anything that runs in a container.

> **Zero-cost first:** Docker Spaces require a paid PRO/Team plan to create (except ZeroGPU Gradio Spaces). You can still learn the patterns and use them when you have a plan, or build Docker-based tools locally.

---

## Quick Start

### 1. Configure the Space

Set `sdk: docker` in your Space's `README.md` YAML block:

```yaml
---
title: Basic Docker SDK Space
emoji: 🐳
colorFrom: purple
colorTo: gray
sdk: docker
app_port: 7860
---
```

- `app_port` (default 7860) controls the **external** port. You can expose multiple internal ports via a reverse proxy (e.g., nginx).
- Internally, you can have as many open ports as needed (e.g., Elasticsearch on 9200).

### 2. Create a `Dockerfile`

```dockerfile
# Use any base image
FROM python:3.11-slim

# Set up non-root user (UID 1000 is required)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app

# Install dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY --chown=user . .

CMD ["python", "app.py"]
```

---

## Dockerfile Best Practices

### User Permissions (Critical)

The container **always runs as UID 1000**. Follow this pattern to avoid permission errors:

```dockerfile
# Create user with UID 1000
RUN useradd -m -u 1000 user

# Switch to user
USER user

# Set home and path
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app

# Always use --chown=user for COPY and ADD
COPY --chown=user . .
ADD --chown=user https://example.com/checkpoint checkpoint/
```

> ⚠️ **Never use `chown -R` on copied files** — it creates a new layer duplicating every file. Always use `COPY --chown=user` / `ADD --chown=user` instead.

### For directories needing broad access:

```dockerfile
RUN mkdir -p /data && chmod 777 /data
```

---

## Secrets and Variables Management

Docker Spaces have **different secrets handling** than Gradio/Streamlit Spaces.

### Variables

#### Buildtime
Passed as Docker `build-arg`:

```dockerfile
ARG MODEL_REPO_NAME
RUN predict.py $MODEL_REPO_NAME
```

Set these in Space Settings → Variables. They're **public** and visible in duplicates.

#### Runtime
Injected as regular environment variables. Access via `os.environ.get("VAR_NAME")`.

### Secrets

#### Buildtime
Secrets are **mounted as files** at buildtime. If you created a secret named `SECRET_EXAMPLE`:

```dockerfile
RUN --mount=type=secret,id=SECRET_EXAMPLE,mode=0444,required=true \
    git remote add origin $(cat /run/secrets/SECRET_EXAMPLE)
```

```dockerfile
RUN --mount=type=secret,id=SECRET_EXAMPLE,mode=0444,required=true \
    curl test -H 'Authorization: Bearer $(cat /run/secrets/SECRET_EXAMPLE)'
```

#### Runtime
Access as environment variables: `os.environ.get("SECRET_EXAMPLE")`

See [secret-example Space](https://huggingface.co/spaces/DockerTemplates/secret-example).

---

## GPU Support

### Base Images

Use NVIDIA CUDA base images from Docker Hub:

```dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04
```

Available Spaces GPU hardware (as of mid-2026):

| Hardware | vCPU | RAM | GPU VRAM | Hourly |
|---|---|---|---|---|
| CPU Basic | 2 | 16 GB | — | Free |
| CPU Upgrade | 8 | 32 GB | — | $0.03 |
| T4 small | 4 | 15 GB | 16 GB | $0.40 |
| T4 medium | 8 | 30 GB | 16 GB | $0.60 |
| L4 (1×) | 8 | 30 GB | 24 GB | $0.80 |
| L40S (1×) | 8 | 62 GB | 48 GB | $1.80 |
| A10G small | 4 | 15 GB | 24 GB | $1.00 |
| A100 large | 12 | 142 GB | 80 GB | $2.50 |

### GPU Buildtime Limitation

**No GPU access during `docker build`.** Do not run GPU commands (e.g., `nvidia-smi`, `torch.cuda.is_available()`) in your Dockerfile. GPU is only available at runtime.

### Framework-Specific Setup

**PyTorch:**
```dockerfile
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```
At runtime on GPU hardware, PyTorch auto-detects CUDA.

**TensorFlow:**
Default install works — no special Dockerfile changes needed.

**JAX:**
```dockerfile
RUN pip install -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html jax[cuda12_pip]
```

---

## Data Persistence

Data written to disk is **lost on restart**. Two persistence strategies:

### 1. Storage Buckets (Recommended)

Attach an [HF Storage Bucket](https://huggingface.co/docs/hub/storage-buckets) to your Space:

```bash
# Create a bucket
hf buckets create my-space-data

# Sync from Space to bucket
hf buckets sync /data hf://buckets/username/my-space-data/
```

```python
from huggingface_hub import HfApi
api = HfApi()
# Upload files
api.upload_file(
    path_or_fileobj="local_file.bin",
    path_in_repo="data/file.bin",
    repo_id="username/my-space-data",
    repo_type="bucket",
)
```

> ⚠️ `/data` volume is only available at **runtime**, not during Docker build.

### 2. Datasets Hub + huggingface_hub

For datasets stored via Git LFS:

```python
from huggingface_hub import HfApi
api = HfApi()
api.upload_file(
    path_or_fileobj="output.json",
    path_in_repo="results/output.json",
    repo_id="username/my-dataset",
    repo_type="dataset",
)
```

See [scheduled uploads guide](https://huggingface.co/docs/huggingface_hub/main/en/guides/upload#scheduled-uploads).

### 3. External Storage

Connect to external DB, S3, or any cloud storage from your Docker Space code.

---

## Built-in Environment Variables

HF injects these automatically:

| Variable | Description |
|---|---|
| `HF_API_TOKEN` | Read-write token for the Space's repo |
| `SPACE_ID` | Full Space ID: `username/space-name` |
| `SPACE_TITLE` | Space's display title |
| `SPACE_HOST` | Subdomain host (e.g., `username-space-name.hf.space`) |
| `SPACE_REPO_NAME` | Short repo name |
| `SPACE_AUTHOR_NAME` | Author's HF username |
| `SPACE_SDK` | Always `docker` for Docker Spaces |

---

## Lifecycle & Networking

- **Free tier:** Spaces go to sleep after ~48h inactivity. Visitors auto-wake them.
- **Paid tier:** Indefinite runtime. Custom sleep time configurable in Settings.
- **Networking:** Only ports 80, 443, and 8080 allowed for outbound requests.
- **Billing:** Charged per-minute only when `Starting` or `Running` — **not during build**.

### Pause a Space

Manually pause from Settings → Pause. Paused Spaces don't bill.

### API: Set Sleep Time

```json
POST https://huggingface.co/api/spaces/{namespace}/{repo}/settings
{
  "sleepTime": 15
}
```

### API: Replicas (Scalability)

```json
POST https://huggingface.co/api/spaces/{namespace}/{repo}/replicas
{
  "replicas": 2
}
```

Each replica billed independently. Only available on paid hardware.

---

## Programmatic Hardware Management

Using `huggingface_hub`:

```python
from huggingface_hub import HfApi

api = HfApi()
# Request hardware upgrade
api.request_space_hardware(
    repo_id="username/my-space",
    hardware="t4-small",
)
```

See [manage_spaces guide](https://huggingface.co/docs/huggingface_hub/main/en/guides/manage_spaces).

---

## Streaming Logs & Metrics (SSE)

```bash
# Build logs (last N lines)
curl -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/spaces/{namespace}/{repo}/logs/build?tail=100"

# Run logs
curl -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/spaces/{namespace}/{repo}/logs/run?tail=100"

# Real-time events
curl -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/spaces/{namespace}/{repo}/events"

# Metrics
curl -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/spaces/{namespace}/{repo}/metrics"
```

---

## Duplicating Docker Spaces

When clicking "Duplicate this Space":

- **Public variables** auto-populate from source.
- **Secrets** must be re-entered (they don't transfer).
- Target account needs a paid plan (or ZeroGPU exception).
- Default hardware: CPU Basic.

---

## Comparison: Docker vs Gradio vs Static

| Aspect | Docker | Gradio | Static |
|---|---|---|---|
| Flexibility | Any app — FastAPI, Go, etc. | Python ML demos | HTML/JS/CSS |
| GPU support | Yes (runtime only) | Yes | No |
| Secrets at buildtime | Mounted as files | n/a | n/a |
| Free to create | ❌ (paid plan needed) | ❌ (except ZeroGPU) | ✅ |
| Complexity | High | Medium | Low |
| Data persistence | `/data` at runtime; use buckets | Same | N/A |

---

## Template Examples

- [Basic Docker Space](https://huggingface.co/docs/hub/spaces-sdks-docker-first-demo) — official first demo
- [Docker Templates](https://huggingface.co/SpacesExamples) — example Spaces
- [Secret Example](https://huggingface.co/spaces/DockerTemplates/secret-example) — secrets in Docker Spaces

---

## Related Resources

- [Official Docker Spaces Docs](https://huggingface.co/docs/hub/spaces-sdks-docker)
- [Spaces Overview](https://huggingface.co/docs/hub/spaces-overview)
- [Spaces GPU Hardware](https://huggingface.co/docs/hub/spaces-gpus)
- [Storage Buckets](https://huggingface.co/docs/hub/storage-buckets)
- [huggingface_hub Spaces Guide](https://huggingface.co/docs/huggingface_hub/main/en/guides/manage_spaces)
- [Spaces Pricing](https://huggingface.co/pricing#spaces)
- **Cross-topic learnings:** [Load `hf-learnings.md`](skill_view(name='huggingface-hub', file_path='references/hf-learnings.md')) — cumulative HF insights from daily sessions, under the `huggingface-hub` skill.
