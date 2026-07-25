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
