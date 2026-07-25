# HF Learnings Log — hf-spaces-dependencies-and-sdks

## 2026-07-25: Hugging Face Spaces — Dependencies, SDKs, & Configuration Complete Reference

### Summary
Comprehensive deep-dive into Hugging Face Spaces dependency management, SDK selection, hardware configuration, build optimization, and environment management. Researched official HF docs (spaces-overview, spaces-dependencies, spaces-sdks-docker, spaces-sdks-gradio, spaces-sdks-static, spaces-sdks-streamlit, spaces-config-reference, spaces-gpus, spaces-zerogpu, spaces-storage, spaces-settings). Covers all SDK types, dependency files, hardware tiers, ZeroGPU free tier, storage options, and optimization strategies for zero-cost deployments.

### Key Findings

#### 1. Spaces SDK Options — Four Flavours

| SDK | Use Case | Compute Required | Cost |
|-----|----------|-----------------|------|
| **Gradio** | ML demos with UI components (images, audio, video, text, plots) | CPU basic or GPU | Free tier: 2 ZeroGPU Spaces for personal accounts; otherwise PRO+ |
| **Docker** | Custom containers (FastAPI, Go, Node, Phoenix, etc.) | CPU basic or GPU | Same as Gradio — requires paid plan to create |
| **Streamlit** | Data app dashboards, simpler ML demos | CPU basic or GPU | Same as Gradio |
| **Static** | HTML/CSS/JS sites, SPAs, static content | None (CDN-served) | **Completely free** — no compute needed |

**Key constraint**: Free personal accounts can host up to **2 Gradio/Docker Spaces running on ZeroGPU**. Static Spaces are always free.

**Python version** defaults to **3.10**. Override with `python_version: 3.x` or `python_version: 3.x.x` in README YAML.

---

#### 2. Dependency Management by SDK

##### Gradio & Streamlit Spaces

**Default pre-installed packages** (no requirement needed):
- `huggingface_hub` — Hub API, Inference Providers access
- `requests` — third-party API calls
- `datasets` — fetch/display datasets from Hub
- `gradio` (for Gradio SDK) — specific version via `sdk_version` in YAML
- Common Debian packages: `ffmpeg`, `cmake`, `libsm6`, and others

**Adding Python packages** — create `requirements.txt` at repo root:
```
transformers
torch
accelerate
sentencepiece
```

**Pre-install dependencies** — create `pre-requirements.txt` (runs before `requirements.txt`, useful for upgrading pip itself):
```
pip>=24.0
setuptools>=68.0
```

**Adding system packages** — create `packages.txt` at repo root (one package per line, installed via `apt-get install`):
```
libsndfile1
espeak-ng
ffmpeg
git-lfs
```

##### Docker Spaces

Dependencies are managed entirely through the `Dockerfile`. Best practices:

**User setup** (container runs as user ID 1000):
```dockerfile
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app
```

**Installing Python packages**:
```dockerfile
RUN pip install --no-cache-dir --upgrade pip
COPY --chown=user . $HOME/app
RUN pip install --no-cache-dir -r requirements.txt
```

**Buildtime vs Runtime variables**:
- **Buildtime**: Passed as `ARG` / `--build-arg` to Dockerfile. Access with `ARG VAR_NAME`.
- **Runtime**: Injected as environment variables. Access with `os.environ.get("VAR_NAME")`.

**Buildtime secrets** (Docker BuildKit):
```dockerfile
RUN --mount=type=secret,id=SECRET_NAME,mode=0444,required=true \
    git init && git remote add origin $(cat /run/secrets/SECRET_NAME)
```

**Runtime secrets**: Available as environment variables (same as Gradio).

**Port configuration**: Default is `7860`, override with `app_port: PORT` in README YAML. Internal multi-port works (e.g., Elasticsearch on 9200 internally), expose via reverse proxy.

##### Static Spaces

Dependencies managed via `app_build_command` (e.g., `npm run build`) and `app_file: dist/index.html`. Build runs in a Job, output stored in `refs/convert/build`.

---

#### 3. Hardware Tiers — Complete Reference

| Hardware | vCPU | RAM | GPU Memory | Hourly Price |
|----------|------|-----|------------|-------------|
| **CPU Basic** (default) | 2 | 16 GB | — | **FREE** |
| CPU Upgrade | 8 | 32 GB | — | $0.03 |
| Nvidia T4-small | 4 | 15 GB | 16 GB | $0.40 |
| Nvidia T4-medium | 8 | 30 GB | 16 GB | $0.60 |
| 1x Nvidia L4 | 8 | 30 GB | 24 GB | $0.80 |
| 4x Nvidia L4 | 48 | 186 GB | 96 GB | $3.80 |
| 1x Nvidia L40S | 8 | 62 GB | 48 GB | $1.80 |
| 4x Nvidia L40S | 48 | 382 GB | 192 GB | $8.30 |
| 8x Nvidia L40S | 192 | 1534 GB | 384 GB | $23.50 |
| Nvidia A10G-small | 4 | 15 GB | 24 GB | $1.00 |
| Nvidia A10G-large | 12 | 46 GB | 24 GB | $1.50 |
| 2x A10G-large | 24 | 92 GB | 48 GB | $3.00 |
| 4x A10G-large | 48 | 184 GB | 96 GB | $5.00 |
| Nvidia A100-large | 12 | 142 GB | 80 GB | $2.50 |
| 4x Nvidia A100 | 48 | 568 GB | 320 GB | $10.00 |
| 8x Nvidia A100 | 96 | 1136 GB | 640 GB | $20.00 |

**Default disk**: 50 GB ephemeral (lost on restart). Persist via Storage Buckets.

---

#### 4. ZeroGPU — Free GPU for Personal Accounts

**What it is**: Shared infrastructure dynamically allocating NVIDIA RTX Pro 6000 Blackwell GPUs. Free GPU time for eligible accounts.

**GPU sizes**:
| Size | Hardware | VRAM | Quota Cost |
|------|----------|------|-----------|
| `large` (default) | Half RTX Pro 6000 Blackwell | 48 GB | 1× |
| `xlarge` | Full RTX Pro 6000 Blackwell | 96 GB | 2× |

**Daily quotas**:
| Account Type | Daily GPU Quota | Queue Priority |
|-------------|----------------|---------------|
| Unauthenticated | 2 minutes | Low |
| Free account (good standing) | 5 minutes | Medium |
| PRO | 40 minutes (extensible) | Highest |
| Team member | 40 minutes (extensible) | Highest |
| Enterprise member | 60 minutes (extensible) | Highest |

**Free personal account requirements for hosting**:
- Verified email
- Account older than 30 days
- Maximum **2 ZeroGPU Spaces**
- **Gradio SDK only** (no Docker/Streamlit ZeroGPU support yet)

**Usage in code**:
```python
import spaces

@spaces.GPU(duration=120)  # default 60s
def predict(image):
    return model(image)
```

**Limitations**:
- `torch.compile` not supported (use AOT compilation instead, torch 2.8+)
- Gradio 4+ only
- PyTorch 2.8.0+
- Python 3.10.13 or 3.12.12
- `xlarge` has higher queue probability and longer wait times

**Extending quota** (PRO/Team/Enterprise): $1 per 10 GPU minutes via pre-paid credits.

---

#### 5. README YAML Configuration — Complete Reference

```yaml
---
title: My Space                 # Display title
emoji: 🤗                       # Emoji for thumbnail
colorFrom: blue                 # Gradient start: red/yellow/green/blue/indigo/purple/pink/gray
colorTo: purple                 # Gradient end
sdk: gradio                     # gradio | docker | streamlit | static
python_version: 3.10            # Any 3.x or 3.x.x; default 3.10
sdk_version: 5.0                # Gradio version (all versions supported)
app_file: app.py                # Main application file
app_port: 7860                  # Port (Docker only, default 7860)
app_build_command: npm run build  # Build command (Static only)
base_path: /app                 # Initial URL path (non-static)
fullWidth: true                 # Full-width iframe (default: true)
header: mini                    # mini | default
short_description: "My demo"    # Short description for thumbnail
models:                         # Linked HF model IDs
  - openai-community/gpt2
datasets:                       # Linked HF dataset IDs
  - mozilla-foundation/common_voice_13_0
tags: [demo, nlp]               # Descriptive tags
pinned: true                    # Pin to profile top
thumbnail: https://example.com/thumb.png  # Custom social thumbnail

# OAuth settings
hf_oauth: true
hf_oauth_scopes: [openid, profile]
hf_oauth_expiration_minutes: 480  # Default 8h, max 43200 (30d)
hf_oauth_authorized_org: my-org   # Restrict OAuth to org members

# Embedding & security
disable_embedding: false         # Prevent iframe embedding
custom_headers:                  # COEP/COOP/CORP headers (lowercase only)
  cross-origin-embedder-policy: require-corp
  cross-origin-opener-policy: same-origin

# Performance
startup_duration_timeout: 30m    # Max startup time before unhealthy (default 30m)
suggested_hardware: t4-small     # Suggested hardware for duplicators
preload_from_hub:                # Preload models/datasets at build time
  - warp-ai/wuerstchen-prior text_encoder/model.safetensors
  - openai-community/gpt2
---
```

---

#### 6. Environment Variables

**Built-in variables** (automatically available):
| Variable | Example | Description |
|----------|---------|-------------|
| `ACCELERATOR` | `t4-medium` | GPU type, or `none` for CPU |
| `CPU_CORES` | `4` | CPU core count |
| `MEMORY` | `15Gi` | RAM allocation |
| `SPACE_AUTHOR_NAME` | `osanseviero` | Space owner username |
| `SPACE_REPO_NAME` | `i-like-flan` | Space repo name |
| `SPACE_TITLE` | `I Like Flan` | Title from README YAML |
| `SPACE_ID` | `osanseviero/i-like-flan` | Full Space ID |
| `SPACE_HOST` | `osanseviero-i-like-flan.hf.space` | Space subdomain |
| `SPACE_CREATOR_USER_ID` | `6032802e...` | User ID of original creator |

**OAuth variables** (when enabled):
| Variable | Description |
|----------|-------------|
| `OAUTH_CLIENT_ID` | OAuth app client ID (public) |
| `OAUTH_CLIENT_SECRET` | OAuth app client secret |
| `OAUTH_SCOPES` | Always `"openid profile"` |
| `OPENID_PROVIDER_URL` | OpenID provider URL |

**Custom variables & secrets**: Configured in Space Settings → Variables (public, viewable) / Secrets (private, hidden after set).

**Access in Static Spaces**: Via `window.huggingface.variables` (client-side JS).

**Access in other SDKs**: Via `os.environ.get("VAR_NAME")`.

---

#### 7. Storage & Persistence

| Type | Capacity | Persistence | Cost |
|------|----------|-------------|------|
| **Ephemeral disk** | 50 GB | Lost on restart | Free |
| **Storage Bucket** | Small/Medium/Large | Survives restarts | Free tier available (storage buckets docs) |

**Mounting models/datasets as volumes**: Use `huggingface_hub` Python API to attach repos as read-only volumes. Can mount private repos (masked in UI for unauthorized users).

**Persistent storage for Docker Spaces**: `/data` volume available at runtime only (not during build). Use Storage Buckets for persistence across restarts.

---

#### 8. Networking

- Ports open: **80 (HTTP)**, **443 (HTTPS)**, **8080** (additional)
- All other ports blocked
- For multi-service Docker Spaces, use reverse proxy (Nginx) on port 7860

---

#### 9. Lifecycle Management

- **Free hardware**: Space sleeps after inactivity (auto-pause)
- **Paid hardware**: Space runs indefinitely
- **Manual pause**: From Settings tab (billing stops for paused time)
- **Dev Mode**: For debugging — see Spaces Dev Mode docs
- **Build triggers**: Every push to the repo triggers rebuild + restart

---

#### 10. Optimization Strategies for Zero-Cost

1. **Choose Static Spaces** when possible — zero compute cost, CDN-served
2. **ZeroGPU for ML demos** — 5 min/day free GPU for personal accounts in good standing (verified email, >30 days old)
3. **Use `preload_from_hub`** to download models at build time (reduces cold start latency, avoids runtime download delays)
4. **Pin Gradio version** with `sdk_version` to avoid unexpected breaking changes on rebuild
5. **Split dependencies** — `pre-requirements.txt` for pip upgrades, `requirements.txt` for app packages
6. **Use `huggingface_hub` inference** instead of loading models locally when possible — saves RAM and compute
7. **Keep Docker images lean** — multi-stage builds, `--no-cache-dir`, avoid `chown` when possible (prefer `COPY --chown=user`)
8. **Mount models as volumes** instead of downloading at every cold start
9. **Set `suggested_hardware`** for Spaces meant to be duplicated — guides users to correct hardware
10. **Set `startup_duration_timeout`** to appropriate value (default 30m is generous) to fail fast on misconfiguration

### Impact & Use Cases
- **Zero-cost deployment**: Choose the right SDK + hardware combination to minimize costs (Static = free, ZeroGPU = free GPU with daily quota)
- **Build optimization**: Proper dependency management reduces rebuild time and failures
- **Docker Space creation**: Complete reference for Dockerfile setup, user permissions, secrets, and buildtime/runtime variable management
- **Space duplication**: YAML config with `suggested_hardware` and `preload_from_hub` ensures duplicated Spaces work correctly
- **Hardware selection**: Choose appropriate GPU tier based on model size and budget

### Skill Created
`hf-spaces-dependencies-and-sdks/` — new skill with SKILL.md (author: SakThai, license: MIT) and this learnings reference. Covers the complete Spaces dependency, SDK, hardware, and configuration ecosystem.

### Sources
- HF Docs: https://huggingface.co/docs/hub/en/spaces-overview
- HF Docs: https://huggingface.co/docs/hub/en/spaces-dependencies
- HF Docs: https://huggingface.co/docs/hub/en/spaces-sdks-gradio
- HF Docs: https://huggingface.co/docs/hub/en/spaces-sdks-docker
- HF Docs: https://huggingface.co/docs/hub/en/spaces-sdks-static
- HF Docs: https://huggingface.co/docs/hub/en/spaces-sdks-streamlit
- HF Docs: https://huggingface.co/docs/hub/en/spaces-config-reference
- HF Docs: https://huggingface.co/docs/hub/en/spaces-gpus
- HF Docs: https://huggingface.co/docs/hub/en/spaces-zerogpu
- HF Docs: https://huggingface.co/docs/hub/en/spaces-storage
- HF Docs: https://huggingface.co/docs/hub/en/spaces-settings
