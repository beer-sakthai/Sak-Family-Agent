# HF Hub Spaces Build Configuration — Complete Reference

> Researched: 2026-07-25 | Source: huggingface.co/docs/hub/en/spaces-config-reference

## Overview

Hugging Face Spaces are configured through a **YAML frontmatter block** at the top of the `README.md` file in the root of the Space repository. This YAML block defines the SDK, runtime, hardware, OAuth, and many other properties.

## Complete Parameter Reference

### Identity & Display

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | string | Display title for the Space. Shown in the browser tab and thumbnail. |
| `emoji` | string | Single emoji character displayed on the Space thumbnail card. |
| `colorFrom` | string | Start color for thumbnail gradient. One of: `red`, `yellow`, `green`, `blue`, `indigo`, `purple`, `pink`, `gray`. |
| `colorTo` | string | End color for thumbnail gradient. Same options as `colorFrom`. |
| `thumbnail` | string | URL for a custom thumbnail image used in social sharing previews. |
| `short_description` | string | Brief description shown on the Space's thumbnail card. |
| `pinned` | boolean | When `true`, the Space stays pinned to the top of your profile page. Useful for highlighting your best Space among many. |

### SDK & Runtime

| Parameter | Type | Description |
|-----------|------|-------------|
| `sdk` | string | **Required.** The framework type. Must be one of: `gradio`, `docker`, `static`. Determines how the Space is built and served. |
| `python_version` | string | Python version. Any valid `3.x` or `3.x.x` format. **Default: `3.10`**. |
| `sdk_version` | string | Version of the SDK (Gradio) to use. All Gradio versions are supported. Not used for `docker` or `static`. |
| `app_file` | string | Path to the main application file, relative to repo root. For Gradio: Python file with Gradio code. For static: the HTML entry point. |
| `app_port` | int | Port for the application (Docker SDK only). **Default: `7860`**. |
| `app_build_command` | string | Build command for static Spaces (e.g., `npm run build`). Runs in a Job; output stored in `refs/convert/build`. Used with `app_file` pointing to the built artifact. |
| `base_path` | string | Initial URL path for non-static Spaces. Must start with `/`. For static Spaces, use `app_file` instead. |
| `fullWidth` | boolean | Whether the Space renders in full-width vs. fixed-width ("container" CSS) inside the iframe. **Default: `true`**. |
| `header` | string | Header style: `mini` (full-screen with mini floating header) or `default`. |
| `startup_duration_timeout` | string | Custom startup timeout before the Space is flagged unhealthy. Accepts durations like `1h`, `30m`. **Default: `30m`**. |

### Hardware

| Parameter | Type | Description |
|-----------|------|-------------|
| `suggested_hardware` | string | **Suggested** hardware for users who duplicate this Space. Does NOT auto-assign hardware to the current Space. Use for template Spaces. |

**Valid hardware flavors:**

| Category | Flavors |
|----------|---------|
| **CPU** | `cpu-basic`, `cpu-upgrade` |
| **NVIDIA T4** | `t4-small`, `t4-medium` |
| **NVIDIA L4** | `l4x1`, `l4x4` |
| **NVIDIA L40S** | `l40sx1`, `l40sx4`, `l40sx8` |
| **NVIDIA A10G** | `a10g-small`, `a10g-large`, `a10g-largex2`, `a10g-largex4` |
| **NVIDIA A100** | `a100-large`, `a100x4`, `a100x8` |

### Storage

| Parameter | Type | Description |
|-----------|------|-------------|
| `suggested_storage` | string | **Deprecated.** Persistent storage is no longer available. Previously accepted `small`, `medium`, `large`. Now ignored. |

### Dependencies & Tags

| Parameter | Type | Description |
|-----------|------|-------------|
| `models` | List[string] | HF model IDs used (e.g., `openai-community/gpt2`). Auto-detected from code if omitted. |
| `datasets` | List[string] | HF dataset IDs used (e.g., `mozilla-foundation/common_voice_13_0`). Auto-detected from code if omitted. |
| `tags` | List[string] | Terms describing the Space's task or scope. Appears in search filters. |

### Embedding & Security

| Parameter | Type | Description |
|-----------|------|-------------|
| `disable_embedding` | boolean | When `true`, prevents the Space iframe from being embedded in external websites. **Default: `false`** (embeddable). |
| `custom_headers` | Dict[string, string] | Custom HTTP headers added to all responses. Currently only `cross-origin-embedder-policy` (COEP), `cross-origin-opener-policy` (COOP), and `cross-origin-resource-policy` (CORP) are allowed. All keys and values must be **lowercase**. Example enables cross-origin isolation for `SharedArrayBuffer`. |

### OAuth / Sign-In with HF

| Parameter | Type | Description |
|-----------|------|-------------|
| `hf_oauth` | boolean | Whether a connected OAuth app is associated with this Space. |
| `hf_oauth_scopes` | List[string] | Authorized OAuth scopes. `openid` and `profile` are authorized by default. |
| `hf_oauth_expiration_minutes` | int | OAuth token duration in minutes. **Default: `480`** (8h). **Max: `43200`** (30 days). |
| `hf_oauth_authorized_org` | string or List[string] | Restrict OAuth access to members of specific organizations by name. |

### Performance: Preloading

| Parameter | Type | Description |
|-----------|------|-------------|
| `preload_from_hub` | List[string] | List of HF Hub repos/files to preload at build time. Optimizes startup by downloading files during build instead of at runtime. |

**Format:** `"repo_name"` (all files), `"repo_name file1,file2"` (specific files), or `"repo_name file1,file2 commit_sha256"` (specific revision).

Files are saved in the default `huggingface_hub` disk cache at `~/.cache/huggingface/hub`. Does NOT follow `HF_HOME` overrides. Private repos are **not** supported yet.

**Example:**
```yaml
preload_from_hub:
  - warp-ai/wuerstchen-prior text_encoder/model.safetensors,prior/diffusion_pytorch_model.safetensors
  - coqui/XTTS-v1
  - openai-community/gpt2 config.json 11c5a3d5811f50298f278a704980280950aedb10
```

## SDK-Specific Notes

| SDK | Key Constraints |
|-----|-----------------|
| **Gradio** | Requires Python. `sdk_version` to pin Gradio version. `app_file` points to Python entry point. Default framework for Spaces. |
| **Docker** | Uses `app_port` (default 7860). Full control over environment. Supports custom Dockerfile. Requires paid plan for GPU. |
| **Static** | Free for everyone. `app_build_command` for pre-build. `app_file` points to HTML entry. Zero compute cost. |

## Zero-Cost Patterns

- **Static Spaces** are completely free — use for documentation sites, landing pages, dashboards with static data.
- **Gradio Spaces on ZeroGPU** — free personal accounts get up to 2 Gradio Spaces on ZeroGPU hardware. Good for demos and light inference.
- **Use `preload_from_hub`** to avoid runtime download costs — files are loaded during the free build phase.
- **`disable_embedding: false`** (default) allows embedding your Space anywhere for free distribution.
- **Hardware auto-sleep** — Spaces that go unused will pause and free compute. No cost for idle time.

## Common Patterns

1. **Template Spaces for duplication**: Use `suggested_hardware` + `suggested_storage` so duplicators get the right defaults.
2. **Cross-origin isolation for ML demos**: Set `custom_headers` to enable `SharedArrayBuffer` for multi-threaded WASM inference.
3. **Branded Spaces**: Combine `title`, `emoji`, `colorFrom`/`colorTo`, and `thumbnail` for a polished appearance.
4. **Fast-starting Spaces**: Use `preload_from_hub` to download models during build. Large models that would take 2+ minutes at runtime load in seconds at startup.
5. **Organization-only OAuth**: Restrict login via `hf_oauth_authorized_org` for internal tools.

## Limitations & Constraints

- `suggested_hardware` and `suggested_storage` are **hints for duplicators** — they don't auto-assign hardware to the current Space.
- `preload_from_hub` does NOT follow `HF_HOME` or custom cache paths — always writes to `~/.cache/huggingface/hub`.
- `custom_headers` supports exactly 3 header keys: COEP, COOP, CORP — no other custom headers are allowed.
- Private repo preloading is not yet supported.
- `suggested_storage` is deprecated and ignored since persistent storage was removed.

## Related Documentation

- [Spaces Overview](https://huggingface.co/docs/hub/en/spaces-overview)
- [Handling Spaces Dependencies](https://huggingface.co/docs/hub/en/spaces-dependencies)
- [Spaces ZeroGPU](https://huggingface.co/docs/hub/en/spaces-zerogpu)
- [Spasign-In with HF button](https://huggingface.co/docs/hub/en/spaces-oauth)
- [Run Spaces with Docker](https://huggingface.co/docs/hub/en/spaces-docker)
