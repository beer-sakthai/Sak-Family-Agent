---
name: SakThai-hf-spaces-configuration
description: ">   Complete reference for Hugging Face Spaces YAML configuration system \u2014 \
  \  SDK options, hardware tiers, metadata fields, environment variables,   OAuth,\
  \ preloading, custom headers, and advanced configuration for   Gradio, Streamlit,\
  \ Docker, and Sta"
---

# HF Spaces Configuration Reference

## Overview

Hugging Face Spaces are configured through a YAML block at the top of the `README.md` file. This reference documents every accepted parameter, its type, defaults, and behavior.

## Quick Reference Table

| Parameter | Type | Default | SDK | Description |
|-----------|------|---------|-----|-------------|
| `title` | string | — | all | Display title for the Space |
| `emoji` | string | — | all | Space emoji (emoji-only character) |
| `colorFrom` | string | — | all | Thumbnail gradient start (red/yellow/green/blue/indigo/purple/pink/gray) |
| `colorTo` | string | — | all | Thumbnail gradient end (same palette) |
| `sdk` | string | — | — | `gradio`, `docker`, `static`, or `streamlit` |
| `python_version` | string | `3.10` | gradio/docker | Python version (e.g. `3.9`, `3.11.5`) |
| `sdk_version` | string | latest | gradio | Gradio version to use |
| `suggested_hardware` | string | — | all | Suggested hardware flavor for duplication |
| `suggested_storage` | string | — | all | (Deprecated) Suggested storage size |
| `app_file` | string | `app.py` | gradio/static | Path to main application file |
| `app_build_command` | string | — | static | Build command (e.g. `npm run build`) |
| `app_port` | int | `7860` | docker | Port your application runs on |
| `base_path` | string | `/` | gradio/docker | Initial URL path to render |
| `fullWidth` | bool | `true` | all | Full-width vs fixed-width iframe |
| `header` | string | `default` | all | `mini` for compact header |
| `short_description` | string | — | all | Short description for thumbnail |
| `models` | List[string] | — | all | Linked model IDs |
| `datasets` | List[string] | — | all | Linked dataset IDs |
| `tags` | List[string] | — | all | Descriptive tags |
| `thumbnail` | string | — | all | Custom thumbnail URL |
| `pinned` | bool | `false` | all | Pin Space to top of profile |
| `hf_oauth` | bool | `false` | all | Enable OAuth app |
| `hf_oauth_scopes` | List[string] | — | all | OAuth scopes (openid, profile default) |
| `hf_oauth_expiration_minutes` | int | `480` | all | Token expiry (max 43200 = 30 days) |
| `hf_oauth_authorized_org` | string/list | — | all | Restrict OAuth to org members |
| `disable_embedding` | bool | `false` | all | Block iframe embedding |
| `startup_duration_timeout` | string | `30m` | all | Custom startup timeout (e.g. `1h`) |
| `custom_headers` | Dict | — | all | COEP/COOP/CORP headers for cross-origin isolation |
| `preload_from_hub` | List[string] | — | all | Preload models/files at build time |

## Hardware Flavors

### CPU
| Flavor | vCPU | RAM | Disk | Price |
|--------|------|-----|------|-------|
| `cpu-basic` | 2 | 16 GB | 50 GB | Free |
| `cpu-upgrade` | 8 | 32 GB | 50 GB | $0.03/hr |

### GPU
| Flavor | vCPU | RAM | VRAM | Disk | Price |
|--------|------|-----|------|------|-------|
| `t4-small` | 4 | 15 GB | 16 GB | 50 GB | $0.40/hr |
| `t4-medium` | 8 | 30 GB | 16 GB | 100 GB | $0.60/hr |
| `l4x1` | 8 | 30 GB | 24 GB | 400 GB | $0.80/hr |
| `l4x4` | 48 | 186 GB | 96 GB | 3200 GB | $3.80/hr |
| `l40sx1` | 8 | 62 GB | 48 GB | 380 GB | $1.80/hr |
| `l40sx4` | 48 | 382 GB | 192 GB | 3200 GB | $8.30/hr |
| `l40sx8` | 192 | 1534 GB | 384 GB | 6500 GB | $23.50/hr |
| `a10g-small` | 4 | 15 GB | 24 GB | 110 GB | $1.00/hr |
| `a10g-large` | 12 | 46 GB | 24 GB | 200 GB | $1.50/hr |
| `a10g-largex2` | 24 | 92 GB | 48 GB | 1000 GB | $3.00/hr |
| `a10g-largex4` | 48 | 184 GB | 96 GB | 2000 GB | $5.00/hr |
| `a100-large` | 12 | 142 GB | 80 GB | 1000 GB | $2.50/hr |
| `a100x4` | 48 | 568 GB | 320 GB | 4000 GB | $10.00/hr |
| `a100x8` | 96 | 1136 GB | 640 GB | 8000 GB | $20.00/hr |

## Built-in Environment Variables

Spaces expose these environment variables at runtime:

| Variable | Example | Description |
|----------|---------|-------------|
| `ACCELERATOR` | `t4-medium` or `none` | GPU accelerator type |
| `CPU_CORES` | `4` | Number of CPU cores |
| `MEMORY` | `15Gi` | Available memory |
| `SPACE_AUTHOR_NAME` | `osanseviero` | Space author username |
| `SPACE_REPO_NAME` | `i-like-flan` | Space repository name |
| `SPACE_TITLE` | `I Like Flan` | Space title (from YAML) |
| `SPACE_ID` | `osanseviero/i-like-flan` | Full Space identifier |
| `SPACE_HOST` | `osanseviero-i-like-flan.hf.space` | Public Space hostname |
| `SPACE_CREATOR_USER_ID` | `6032802e...` | Original creator user ID |

With OAuth enabled, additional variables:
| Variable | Description |
|----------|-------------|
| `OAUTH_CLIENT_ID` | OAuth client ID |
| `OAUTH_CLIENT_SECRET` | OAuth client secret |
| `OAUTH_SCOPES` | Authorized scopes |
| `OPENID_PROVIDER_URL` | OpenID provider URL |

## SDK-Specific Behavior

### Gradio Spaces
- Default `sdk: gradio` with auto-detection from `app.py`
- Version pin via `sdk_version` (supports all Gradio versions)
- Gradio 5/6 fully supported
- requires paid plan (except ZeroGPU free tier)

### Docker Spaces
- `sdk: docker` with custom Dockerfile
- `app_port` defaults to 7860
- Full flexibility for any framework
- Requires paid plan

### Static Spaces
- `sdk: static` with `app_file` pointing to HTML
- `app_build_command` runs at build time via Jobs
- Build output stored in `refs/convert/build`
- Free for everyone
- Use `app_file: dist/index.html` with build commands

### Streamlit Spaces
- `sdk: streamlit` (auto-configured)
- Standard Streamlit configuration
- Requires paid plan

## Networking & Lifecycle

- **Ports**: HTTP/HTTPS (80, 443) and 8080 allowed; all others blocked
- **Sleep**: Free Spaces sleep after 48h inactivity; visitors auto-restart
- **Pause**: Manual pause from Settings; not billed; only owner can restart
- **Custom sleep**: Paid Spaces can set custom idle timeout
- **Replicas**: Scale horizontally via API (`POST /api/spaces/{ns}/{repo}/replicas`)

## OAuth Configuration

```yaml
hf_oauth: true
hf_oauth_scopes:
  - openid
  - profile
hf_oauth_expiration_minutes: 480  # max 43200 (30 days)
hf_oauth_authorized_org: your-org-name
```

## Preloading Models at Build Time

```yaml
preload_from_hub:
  - warp-ai/wuerstchen-prior text_encoder/model.safetensors
  - coqui/XTTS-v1
  - openai-community/gpt2 config.json 11c5a3d5811f50298f278a704980280950aedb10
```

Files are cached in `~/.cache/huggingface/hub` during build, reducing cold-start time.

## Custom Headers for Cross-Origin Isolation

```yaml
custom_headers:
  cross-origin-embedder-policy: require-corp
  cross-origin-opener-policy: same-origin
  cross-origin-resource-policy: cross-origin
```

Enables `SharedArrayBuffer` and other powerful features. All values must be lowercase.

## Programmatic Hardware Configuration

Via `huggingface_hub`:
```python
from huggingface_hub import HfApi
api = HfApi()
api.request_space_hardware(
    repo_id="username/my-space",
    hardware="t4-medium"
)
api.duplicate_space(
    from_id="source/space",
    to_id="target/space",
    hardware="cpu-upgrade"
)
```

## Sources
- HF Spaces Configuration Reference: https://huggingface.co/docs/hub/en/spaces-config-reference
- HF Spaces GPU Upgrades: https://huggingface.co/docs/hub/en/spaces-gpus
- HF Spaces Overview: https://huggingface.co/docs/hub/en/spaces-overview
