# HF Learnings Log — hf-hub-docker-registry

## 2026-07-25: hf-hub-docker-registry — Hugging Face Hub Docker Registry Complete Reference (Topic #254)

### Summary
Comprehensive deep-dive on the Hugging Face Hub Docker Container Registry — the standard Docker V2 registry at `registry.hf.space` that powers Docker-based Spaces, Jobs batch inference, and local development workflows. Covers registry authentication (HF tokens), Docker Spaces build/runtime constraints, Jobs popular images (vLLM, TRL), secrets management, local execution with `docker run`, storage persistence patterns, and zero-cost pathways for development.

### Source
- HF Docker Spaces SDK: https://huggingface.co/docs/hub/en/spaces-sdks-docker
- HF Run Spaces with Docker: https://huggingface.co/docs/hub/en/spaces-run-with-docker
- HF Jobs Popular Images: https://huggingface.co/docs/hub/en/jobs-popular-images
- Docker Registry V2 API: https://distribution.github.io/distribution/
- Registry endpoint: `registry.hf.space` (verified responding with Docker V2 auth challenge)

### 1. What Is the HF Docker Registry?

The Hugging Face Hub Docker Registry is a standard **Docker Distribution V2 registry** that allows users to store, share, and deploy container images alongside models, datasets, and Spaces on the HF Hub. It is accessed at:

```
registry.hf.space
```

The registry uses the standard Docker V2 API protocol and supports:
- `docker login` / `docker logout` — authentication
- `docker pull` — download images
- `docker push` — upload images (requires authentication)
- Bearer token authentication (standard `WWW-Authenticate: Bearer` challenge)

### 2. Authentication

Authenticate to the HF Docker registry using your Hugging Face username and a **User Access Token** with `write` scope:

```bash
# Login
docker login registry.hf.space -u <your-hf-username> --password-stdin
# Then paste your HF token (or use -p but that's less secure)
```

Alternatively:
```bash
echo <HF_TOKEN> | docker login registry.hf.space -u <username> --password-stdin
```

The token must have at least `read` scope for pulling public images, and `write` scope for pushing images. Token management is at https://huggingface.co/settings/tokens.

### 3. Use Case: Docker Spaces

Docker Spaces are the primary consumer of the HF Docker registry. When you create a Space with `sdk: docker`, Hugging Face builds your Docker image and stores it in the registry, then deploys it.

**Dockerfile requirements:**
- The container runs as **UID 1000** — you must create a matching user in your Dockerfile:

```dockerfile
RUN useradd -m -u 1000 -s /bin/bash appuser
USER appuser
```

- **No GPU access during build time** — `nvidia-smi`, `torch.cuda.is_available()`, or any GPU-dependent commands will fail in the Dockerfile. Only use GPUs at runtime.
- **Secrets at build time** — expose via `RUN --mount=type=secret`:

```dockerfile
RUN --mount=type=secret,id=SECRET_EXAMPLE \
    git clone https://$(cat /run/secrets/SECRET_EXAMPLE)@github.com/...
```

**CPU/GPU base images:**
- Use `nvidia/cuda:12.4.1-runtime-ubuntu22.04` or similar from Docker Hub as base for GPU Spaces
- Use `python:3.11-slim` or similar for CPU-only Spaces

**Persistence:**
- Data written to disk is **lost on restart** — use Storage Buckets or HF Hub repos for persistence
- Attach a Storage Bucket via environment variables for checkpoint/log persistence

**SDK choices for Docker Spaces:**
- FastAPI, Go, Phoenix, ML Ops tools, JupyterLab, Streamlit, Gradio (wrapped in Docker), Plotly Dash, Panel, Tabby, Langfuse, etc.

### 4. Use Case: Jobs — Popular Images

Hugging Face **Jobs** provides ready-to-use Docker images (stored in the HF registry or proxied from Docker Hub) for batch inference and training:

| Image | Use Case | Example |
|-------|----------|---------|
| `vllm/vllm-openai` | LLM batch inference with vLLM | `uv run --image vllm/vllm-openai --flavor l4x4 generate-responses.py` |
| `huggingface/trl` | Post-training (SFT, GRPO, DPO) | `uv run --image huggingface/trl --flavor a100-large train.py` |

The `uv` tool handles pulling these images from the registry and managing Python environments inside the containers.

### 5. Use Case: Running Spaces Locally with Docker

You can run any HF Space locally using Docker for testing and development:

```bash
# Clone the Space repository
git clone https://huggingface.co/spaces/<owner>/<space-name>
cd <space-name>

# Build and run locally
docker build -t my-space .
docker run -p 7860:7860 my-space
```

**For Spaces requiring authentication** to the HF Docker registry:
```bash
docker login registry.hf.space -u <username>
```

### 6. Registry API Details

The HF Docker registry at `registry.hf.space` follows the Docker Distribution V2 specification:

- **`GET /v2/`** — Registry version check (returns 401 with auth challenge)
- **`GET /v2/auth`** — Bearer token endpoint (realm in `WWW-Authenticate`)
- **`GET /v2/<image>/manifests/<tag>`** — Fetch image manifest
- **`GET /v2/<image>/blobs/<digest>`** — Fetch image layer
- **`PUT /v2/<image>/manifests/<tag>`** — Push image manifest
- **`PUT /v2/<image>/blobs/uploads/...`** — Upload image layers

The registry uses Hugging Face's Xet storage backend for efficient blob storage with deduplication.

### 7. Security Considerations

- **Tokens are sensitive** — never hardcode tokens in Dockerfiles or commit them to git
- **Use Secrets** in Spaces settings for tokens/API keys (not environment variables for sensitive values)
- **Secrets at build time** use Docker BuildKit's `--mount=type=secret` — the secret value is NOT stored in the image layers
- **Secrets Scanner** — HF scans Spaces for hard-coded secrets and warns owners
- **Networking** — Spaces can only access ports 80, 443, and 8080 for outbound connections

### 8. Zero-Cost Pathways

- **Static Spaces** are free (HTML/CSS/JS only, no backend)
- **Docker Spaces** require a paid plan for compute (CPU Basic is free for Gradio/Streamlit, but Docker Spaces need at minimum a paid plan)
- **Local development** with Docker is free — build and test locally before deploying
- **ZeroGPU** (NVIDIA RTX Pro 6000 Blackwell) is free for personal accounts — but only works with Gradio SDK, not Docker SDK
- **Jobs** pricing varies by hardware — free tiers exist for CPU-only jobs

### Practical Workflow Summary

```bash
# 1. Authenticate
echo $HF_TOKEN | docker login registry.hf.space -u $HF_USERNAME --password-stdin

# 2. Pull a public image (if needed)
docker pull registry.hf.space/<namespace>/<image>:<tag>

# 3. Test a Space locally
git clone https://huggingface.co/spaces/owner/space-name
cd space-name
docker build -t test-space .
docker run -p 7860:7860 test-space

# 4. For Jobs, use uv
uv run --image vllm/vllm-openai --flavor l4x4 my-script.py
```

### Key Differences from Other Registries

| Feature | Docker Hub | HF Registry (registry.hf.space) |
|---------|-----------|------|
| Auth | Docker ID + PAT | HF username + User Access Token |
| Storage | Docker-managed | HF Xet-backed |
| V2 API | Yes | Yes (standard) |
| GPU builds | Yes | No (use at runtime only) |
| Free tier | Public images only | Public images + Static Spaces |
| Integration | General purpose | Spaces, Jobs, Hub ecosystem |

---

## 2026-07-25: hf-hub-docker-registry-deep-dive-v2 — Docker Registry V2 API Architecture & Spaces/Jobs Deep-Dive (Topic #259)

### Summary
Deep-dive on the Hugging Face Docker Container Registry's V2 API implementation, authentication flow, and how it powers Docker Spaces and Jobs. Covers the full Bearer token auth handshake (WWW-Authenticate challenge → token exchange), Docker V2 API endpoint structure (manifests, blobs, tags, catalog), Docker Spaces configuration (SDK setup, build-time secrets via `--mount=type=secret`, runtime env vars, multi-port internal networking, UID 1000 runtime user, no-GPU-during-build constraint), Jobs popular images (vLLM, TRL) with GPU framework image requirements (CUDA toolkit, nvcc, NCCL), local development workflow, and zero-cost pathways for development and testing.

### Source
- Docker Spaces Docs: https://huggingface.co/docs/hub/en/spaces-sdks-docker
- Jobs Popular Images: https://huggingface.co/docs/hub/en/jobs-popular-images
- Docker Distribution V2 Spec: https://distribution.github.io/distribution/
- Registry endpoint (verified): `registry.hf.space`
- API version check: `GET /v2/` → 401 `WWW-Authenticate: Bearer realm="https://registry.hf.space/v2/auth"`
- hf CLI for Jobs: `hf jobs uv run --image <image> --flavor <gpu> <script>`

### Skill
hf-hub-docker-registry — Hugging Face Hub Docker Registry deep-dive: full Docker V2 API implementation, Bearer auth flow, Spaces SDK (docker/app_port/secrets/buildtime-mounts), Jobs popular images (vLLM/TRL), GPU framework image requirements, local development with docker build/run, multi-port networking, and zero-cost pathways

---

### 1. Registry V2 API Architecture

The HF Docker Registry at `registry.hf.space` is a **compliant Docker Distribution V2 API** implementation. It uses the standard OAuth2-style Bearer token authentication mandated by the Docker V2 spec.

#### 1.1 Authentication Flow (Handshake)

```
Client → Registry: GET /v2/
Registry → Client: 401 WWW-Authenticate: Bearer realm="https://registry.hf.space/v2/auth",service="registry.hf.space",scope="repository:<ns>/<img>:pull"
Client → Auth:     GET https://registry.hf.space/v2/auth?service=registry.hf.space&scope=repository:<ns>/<img>:pull  [Authorization: Bearer <HF_TOKEN>]
Auth → Client:     {"token":"<short-lived-bearer-token>","expires_in":300,"issued_at":"..."}
Client → Registry: GET /v2/<ns>/<img>/manifests/<tag> [Authorization: Bearer <short-lived-token>]
Registry → Client: 200 {manifests...}
```

Key characteristics:
- Short-lived tokens (300 seconds / 5 minutes)
- HF user access tokens are exchanged for registry-scoped tokens
- Scopes are per-repository (`repository:<namespace>/<image>:pull,push`)
- No anonymous access — all registry operations require authentication

#### 1.2 V2 API Endpoint Structure

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/v2/` | GET | API version check | Yes (returns 401 challenge) |
| `/v2/_catalog` | GET | List all repositories | Yes |
| `/v2/<ns>/<repo>/tags/list` | GET | List tags for a repository | Yes |
| `/v2/<ns>/<repo>/manifests/<tag>` | GET | Get image manifest (by tag) | Yes |
| `/v2/<ns>/<repo>/manifests/<digest>` | GET | Get image manifest (by digest) | Yes |
| `/v2/<ns>/<repo>/manifests/<tag>` | PUT | Push image manifest | Yes (write scope) |
| `/v2/<ns>/<repo>/blobs/<digest>` | GET | Download blob layer | Yes |
| `/v2/<ns>/<repo>/blobs/<digest>` | HEAD | Check blob existence | Yes |
| `/v2/<ns>/<repo>/blobs/uploads/` | POST | Start blob upload | Yes (write scope) |
| `/v2/<ns>/<repo>/blobs/uploads/<uuid>` | PUT | Complete blob upload (monolithic) | Yes |
| `/v2/<ns>/<repo>/blobs/uploads/<uuid>` | PATCH | Upload blob chunk | Yes |
| `/v2/auth` | GET | Token exchange endpoint | Yes (HF token) |

#### 1.3 Image Naming Convention

Images in the HF registry follow: `registry.hf.space/<hf-username-or-org>/<image-name>:<tag>`

For **Spaces**, the image name corresponds to the Space name. When you push a Docker Space, your image goes to `registry.hf.space/<your-username>/<space-name>:latest` (or your specific tag).

For **Jobs**, popular prebuilt images are available:
- `vllm/vllm-openai` — vLLM inference engine with CUDA toolkit
- `huggingface/trl` — TRL training library

These images are pulled automatically by the Jobs system when specified with `--image`.

---

### 2. Docker Spaces — Custom Containers

#### 2.1 SDK Configuration (README.md YAML)

```yaml
---
title: My Docker Space
emoji: 🐳
colorFrom: purple
colorTo: gray
sdk: docker
app_port: 7860
---
```

- `sdk: docker` — tells the HF platform to build and run a Docker container
- `app_port: 7860` — the port to expose externally (default: 7860)
- Multiple internal ports can be used (e.g., Elasticsearch on 9200) but only one external port
- For multi-port exposure, use Nginx reverse proxy inside the container

#### 2.2 Build-time vs Runtime Variables

| Variable Type | Build-time | Runtime |
|---------------|-----------|---------|
| Variables | `ARG` in Dockerfile | Env vars in container |
| Secrets | `--mount=type=secret` (Docker BuildKit) | Env vars via `os.environ` |

**Build-time Variables:** Passed as Docker `--build-arg`. Declared with `ARG` in the Dockerfile:
```dockerfile
ARG MODEL_REPO_NAME
FROM python:latest
RUN predict.py $MODEL_REPO_NAME
```

**Build-time Secrets:** Use Docker BuildKit `--mount=type=secret`:
```dockerfile
# Mount secret and use its value
RUN --mount=type=secret,id=SECRET_EXAMPLE,mode=0444,required=true \
    git init && \
    git remote add origin $(cat /run/secrets/SECRET_EXAMPLE)
```

Secrets are created in the Space Settings tab. Build-time secrets are NOT available as env vars — they must be mounted as files.

#### 2.3 Container Runtime Constraints

| Constraint | Detail |
|-----------|--------|
| **No GPU during build** | `docker build` runs on CPU only. CUDA/torch calls in Dockerfile will fail. |
| **Runtime user** | UID 1000 (not root). Create user in Dockerfile: `RUN useradd -m -u 1000 appuser` |
| **No bind mounts** | `/data` is persisted; all other paths are ephemeral |
| **Network** | Outbound HTTPS allowed; inbound on `app_port` only |
| **Memory** | Varies by Space hardware tier; Static: 512MB, ZeroGPU: 16GB, Paid: up to 192GB |
| **Disk** | Varies by tier; persistent storage via `/data` (see Spaces Disk Usage) |

#### 2.4 GPU at Runtime

Docker Spaces **do support GPUs at runtime** (unlike during build):
- **ZeroGPU Spaces** — free GPU runtime (NVIDIA A100) with `spaces-zero-gpu` tag
- **Paid GPU upgrades** — dedicated GPU (T4, L4, L40S, A100, H100)

For ZeroGPU Spaces specifically:
```dockerfile
FROM nvidia/cuda:12.1-runtime-ubuntu22.04
# ... install your app
```
The ZeroGPU system injects `CUDA_VISIBLE_DEVICES` and mounts the GPU device automatically.

#### 2.5 Local Development

```bash
# Clone the Space repo
git clone https://huggingface.co/spaces/<owner>/<space-name>
cd <space-name>

# Build and test locally
docker build -t test-space .
docker run -p 7860:7860 test-space

# Access at http://localhost:7860
```

---

### 3. Jobs Integration — Popular Images

#### 3.1 The `--image` Flag

Jobs use the `hf jobs uv run` command with `--image` to specify a Docker image from the HF registry:

```bash
hf jobs uv run --image vllm/vllm-openai --flavor l4x4 generate-responses.py
hf jobs uv run --image huggingface/trl --flavor a100-large -s HF_TOKEN train.py
```

#### 3.2 Why GPU Framework Images Matter

GPU libraries need more than a Python package — they need **system-level CUDA infrastructure**:

| Component | What it provides |
|-----------|-----------------|
| CUDA toolkit | `nvcc`, `ptxas`, CUDA runtime libraries |
| NCCL | Multi-GPU communication |
| cuDNN | Deep neural network primitives |
| FlashInfer | Prebuilt JIT kernels for attention |

Without `--image`, `hf jobs uv run` uses a bare Python image (`ghcr.io/astral-sh/uv:python3.12-bookworm`) that has no CUDA toolkit. This causes errors like:
```
RuntimeError: Could not find nvcc and default cuda_home='/usr/local/cuda' doesn't exist
```

The framework image (`vllm/vllm-openai`, `huggingface/trl`) provides the system stack. UV still installs your script dependencies from PyPI, but they run against the image's pre-configured CUDA environment.

#### 3.3 Available Framework Images (2026-07-25)

| Image | Framework | Use Case | GPU Required |
|-------|-----------|----------|-------------|
| `vllm/vllm-openai` | vLLM | Batch inference, OpenAI-compatible serving | Yes (L4/A100/H100) |
| `huggingface/trl` | TRL | SFT, GRPO, DPO training | Yes (A100) |

Images are stored in the HF Docker Registry and regularly updated.

---

### 4. Zero-Cost Pathways

| Pathway | Cost | Details |
|---------|------|---------|
| **Static Docker Spaces** | Free | Always-on, no GPU. Use for APIs, websites, databases |
| **ZeroGPU Docker Spaces** | Free | GPU on-demand (A100). Include `spaces-zero-gpu` in SDK tags |
| **Local development** | Free | `docker build` + `docker run` on your machine |
| **Jobs (CPU)** | Free tier | `hf jobs uv run` without `--flavor` (CPU only, limited quota) |
| **Jobs (GPU)** | Paid | Requires PRO subscription + GPU quota |

---

### 5. Registry Limitations & Workarounds

| Limitation | Workaround |
|-----------|-----------|
| No anonymous pull | Always authenticate via `docker login` or HF token |
| No GPU during Space build | Use multi-stage builds: build CPU parts, copy GPU binaries |
| Single external port | Nginx reverse proxy to route to internal services |
| Build-time secrets require BuildKit | Ensure `DOCKER_BUILDKIT=1` in local env |
| No custom domains on free tier | Use subdomain under `hf.space` |
| No `docker push` without write token | Create HF token with `write` or `fine-grained` scope |
| 5-min token expiry | Registry re-authenticates transparently on each API call |

---

### 6. Debugging & Troubleshooting

```bash
# 1. Verify registry connectivity
curl -sI https://registry.hf.space/v2/
# Expected: HTTP/2 401 with WWW-Authenticate header

# 2. Authenticate
echo $HF_TOKEN | docker login registry.hf.space -u $HF_USERNAME --password-stdin

# 3. Pull an image
docker pull registry.hf.space/<namespace>/<image>:<tag>

# 4. Check Docker Space build logs (in Space settings)
# Look for "Build logs" tab

# 5. Test Space locally
docker build --no-cache -t test-space . 2>&1
docker run --rm -p 7860:7860 test-space

# 6. Check runtime logs (Space → Logs tab)
# Real-time streaming available for running Spaces
|