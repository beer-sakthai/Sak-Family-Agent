# HF Hub Spaces Build Configuration — Complete Reference v2

> Researched: 2026-07-26 | Sources: huggingface.co/docs/hub/en/spaces-config-reference, huggingface.co/docs/hub/en/spaces-gpus, huggingface.co/docs/hub/en/spaces-oauth

## Overview

Hugging Face Spaces are configured through a **YAML frontmatter block** at the top of the `README.md` file in the root of the Space repository. This YAML block defines the SDK, runtime, hardware, OAuth, dependencies, preloading, and many other properties.

---

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
| `pinned` | boolean | When `true`, the Space stays pinned to the top of your profile page. |

### SDK & Runtime

| Parameter | Type | Description |
|-----------|------|-------------|
| `sdk` | string | **Required.** Must be `gradio`, `docker`, or `static`. |
| `python_version` | string | Python version `3.x` or `3.x.x`. **Default: `3.10`**. |
| `sdk_version` | string | Gradio version to use. All versions supported. |
| `app_file` | string | Path to main app file, relative to repo root. |
| `app_port` | int | Port for Docker SDK. **Default: `7860`**. |
| `app_build_command` | string | Build command for static Spaces (e.g., `npm run build`). Runs in a Job; output stored in `refs/convert/build`. |
| `base_path` | string | Initial URL for non-static Spaces. Must start with `/`. |
| `fullWidth` | boolean | Full-width vs fixed-width inside iframe. **Default: `true`**. |
| `header` | string | `mini` or `default`. `mini` gives full-screen with floating header. |
| `startup_duration_timeout` | string | Custom startup timeout. Accepts `1h`, `30m`. **Default: `30m`**. |

### Hardware Specs & Pricing

| Parameter | Type | Description |
|-----------|------|-------------|
| `suggested_hardware` | string | **Suggested** hardware for duplicators. Does NOT auto-assign to current Space. |

#### CPU

| Flavor | vCPU | Memory | Disk | Cost |
|--------|------|--------|------|------|
| `cpu-basic` | 2 vCPU | 16 GB | 50 GB | **Free** (paid plan to create) |
| `cpu-upgrade` | 8 vCPU | 32 GB | 50 GB | $0.03/hr |

#### NVIDIA GPU

| Flavor | vCPU | Memory | GPU | Disk | Cost |
|--------|------|--------|-----|------|------|
| `t4-small` | 4 | 15 GB | 16 GB T4 | 50 GB | $0.40/hr |
| `t4-medium` | 8 | 30 GB | 16 GB T4 | 100 GB | $0.60/hr |
| `l4x1` | 8 | 30 GB | 24 GB L4 | 400 GB | $0.80/hr |
| `l4x4` | 48 | 186 GB | 96 GB 4×L4 | 3200 GB | $3.80/hr |
| `l40sx1` | 8 | 62 GB | 48 GB L40S | 380 GB | $1.80/hr |
| `l40sx4` | 48 | 382 GB | 192 GB 4×L40S | 3200 GB | $8.30/hr |
| `l40sx8` | 192 | 1534 GB | 384 GB 8×L40S | 6500 GB | $23.50/hr |
| `a10g-small` | 4 | 15 GB | 24 GB A10G | 110 GB | $1.00/hr |
| `a10g-large` | 12 | 46 GB | 24 GB A10G | 200 GB | $1.50/hr |
| `a10g-largex2` | 24 | 92 GB | 48 GB 2×A10G | 1000 GB | $3.00/hr |
| `a10g-largex4` | 48 | 184 GB | 96 GB 4×A10G | 2000 GB | $5.00/hr |
| `a100-large` | 12 | 142 GB | 80 GB A100 | 1000 GB | $2.50/hr |
| `a100x4` | 48 | 568 GB | 320 GB 4×A100 | 4000 GB | $10.00/hr |
| `a100x8` | 96 | 1136 GB | 640 GB 8×A100 | 8000 GB | $20.00/hr |

> H100 **removed December 2025** — no longer available.

### Storage

| Parameter | Type | Description |
|-----------|------|-------------|
| `suggested_storage` | string | **Deprecated.** Persistent storage removed. Previously `small`, `medium`, `large`. Now **ignored**. |

### Dependencies & Tags

| Parameter | Type | Description |
|-----------|------|-------------|
| `models` | List[string] | HF model IDs used. **Auto-detected from code if omitted.** |
| `datasets` | List[string] | HF dataset IDs used. **Auto-detected from code if omitted.** |
| `tags` | List[string] | Terms describing Space task/scope. Shows in search filters. |

### Embedding & Security

| Parameter | Type | Description |
|-----------|------|-------------|
| `disable_embedding` | boolean | Prevent iframe embedding. **Default: `false`** (embeddable). |
| `custom_headers` | Dict[string, string] | Custom HTTP headers. **Only COEP, COOP, CORP** allowed. All lowercase. See cross-origin isolation section. |

### OAuth / Sign-In with HF

| Parameter | Type | Description |
|-----------|------|-------------|
| `hf_oauth` | boolean | Enable sign-in-with-HF OAuth app. |
| `hf_oauth_scopes` | List[string] | OAuth scopes. `openid` + `profile` always included by default. |
| `hf_oauth_expiration_minutes` | int | Token duration. **Default: `480`** (8h). **Max: `43200`** (30d). |
| `hf_oauth_authorized_org` | string or List[string] | Restrict OAuth to specific org members. |

#### Complete OAuth Scopes

| Scope | Description |
|-------|-------------|
| `openid` | Always. ID token + access token. |
| `profile` | Always. Username, avatar, profile. |
| `email` | User's email address. |
| `read-billing` | Payment method status. |
| `read-repos` | Read personal repos. |
| `gated-repos` | Read public gated repos (not private). |
| `contribute-repos` | Create repos + access created ones. |
| `write-repos` | Write/read personal repos. |
| `manage-repos` | Full access including create/delete. |
| `read-collections` | Read personal collections. |
| `write-collections` | Write/read + create/delete collections. |
| `inference-api` | Inference on behalf of user. |
| `jobs` | Run HF Jobs. |
| `webhooks` | Manage webhooks. |
| `write-discussions` | Discussions, PRs, comments, reactions. Need `read-repos` for private repo PRs. |

#### OAuth Env Vars (injected at runtime)

When `hf_oauth: true`:
- `OAUTH_CLIENT_ID` — public client ID
- `OAUTH_CLIENT_SECRET` — keep confidential
- `OAUTH_SCOPES` — space-separated
- `OPENID_PROVIDER_URL` — metadata at `{url}/.well-known/openid-configuration`

Redirect URIs can target the Space. `SPACE_HOST` env var available.

### Performance: Preloading

| Parameter | Type | Description |
|-----------|------|-------------|
| `preload_from_hub` | List[string] | Repos/files to preload at **build time**. Reduces startup latency. |

**Format variants:**
- `"repo_name"` — entire repo
- `"repo_name file1,file2"` — specific files
- `"repo_name file1,file2 commit_sha256"` — pinned revision

**Caveats:**
- Files saved to `~/.cache/huggingface/hub` (does NOT follow `HF_HOME`)
- Private repos **not supported**
- Preloaded in default cache path only

---

## SDK-Specific Configuration

### Gradio SDK

| Aspect | Detail |
|--------|--------|
| `sdk: gradio` | Default. Most common. |
| `sdk_version` | Pin Gradio version. |
| `app_file` | Python entry point with `demo.launch()`. |
| GPU frameworks | Add `--extra-index-url https://download.pytorch.org/whl/cu113` to `requirements.txt`. |
| Gradio OAuth | `gr.LoginButton` + `gr.OAuthView` or `gr.LoginWhen` pattern. |

**Example Gradio with OAuth:**
```yaml
title: My OAuth App
emoji: 🔐
sdk: gradio
sdk_version: 5.0.0
app_file: app.py
hf_oauth: true
hf_oauth_scopes:
  - read-repos
  - inference-api
```

### Docker SDK

| Aspect | Detail |
|--------|--------|
| `sdk: docker` | Full container control. Needs `Dockerfile`. |
| `app_port` | Default 7860. Space expects app on this port. |
| Customization | Any base image, language, dependencies. |
| GPU | Requires paid plan. Manual CUDA install. |

**Example:**
```yaml
title: Docker Inference
emoji: 🐳
sdk: docker
app_port: 8080
```

### Static SDK

| Aspect | Detail |
|--------|--------|
| `sdk: static` | **Free.** Serves HTML/CSS/JS directly. |
| `app_build_command` | e.g., `npm run build`. Runs during build. |
| `app_file` | Points to built HTML (e.g., `dist/index.html`). |
| Client OAuth | Via `@huggingface/hub` JS SDK. |

**Example:**
```yaml
title: Static Demo
emoji: 📄
sdk: static
app_file: dist/index.html
app_build_command: npm run build
```

---

## Practical Complete Examples

### 1. Minimal Gradio Demo
```yaml
title: My Demo
emoji: 🚀
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 5.0.0
app_file: app.py
pinned: true
```

### 2. Template for Duplication
```yaml
title: Template LLM Chat
emoji: 🤖
sdk: gradio
sdk_version: 5.0.0
suggested_hardware: t4-medium
models: [meta-llama/Llama-3.2-3B-Instruct]
tags: [llm, chat, template]
preload_from_hub:
  - meta-llama/Llama-3.2-3B-Instruct
```

### 3. Organization-Only Internal Tool
```yaml
title: Internal Dashboard
emoji: 🏢
sdk: gradio
app_file: dashboard.py
hf_oauth: true
hf_oauth_scopes: [read-repos]
hf_oauth_expiration_minutes: 1440
hf_oauth_authorized_org: my-org-name
disable_embedding: true
```

### 4. Cross-Origin Isolated WASM Space
```yaml
title: WASM Inference
emoji: ⚡
sdk: static
app_file: index.html
app_build_command: npm run build
custom_headers:
  cross-origin-embedder-policy: require-corp
  cross-origin-opener-policy: same-origin
  cross-origin-resource-policy: cross-origin
header: mini
```

---

## Cross-Origin Isolation with Custom Headers

Enables `SharedArrayBuffer` for multi-threaded WASM inference (llama.cpp WASM, WebLLM, Whisper WASM).

**Allowed headers** (only 3, all lowercase):
- `cross-origin-embedder-policy`: `unsafe-none` | `require-corp`
- `cross-origin-opener-policy`: `unsafe-none` | `same-origin-allow-popups` | `same-origin`
- `cross-origin-resource-policy`: `same-site` | `same-origin` | `cross-origin`

**Minimal isolation:**
```yaml
custom_headers:
  cross-origin-embedder-policy: require-corp
  cross-origin-opener-policy: same-origin
  cross-origin-resource-policy: cross-origin
```

---

## OAuth Integration Patterns

### Gradio Built-In
```python
import gradio as gr
with gr.Blocks() as demo:
    gr.LoginButton()
    gr.LogoutButton()
    gr.OAuthView(gr.Textbox(), user_info="username")
demo.launch()
```

### Manual Flow
1. Redirect: `https://huggingface.co/oauth/authorize?redirect_uri=...&client_id=...&state=...`
2. Handle callback, verify `state`, exchange `code` for tokens via POST to `https://huggingface.co/oauth/token`
3. Access token → scoped API. ID token → user profile.

### Static Space (JS)
```javascript
import { oauthLoginUrl, oauthHandleRedirectIfPresent } from "@huggingface/hub";
const oauthResult = await oauthHandleRedirectIfPresent();
if (!oauthResult) window.location.href = await oauthLoginUrl();
// oauthResult.accessToken, oauthResult.userInfo
```

---

## Zero-Cost Analysis

| Pattern | Cost | Notes |
|---------|------|-------|
| Static Space | **Free** | No compute, no GPU, for everyone |
| Gradio CPU Basic | **Free** compute (paid plan to create) |
| Gradio ZeroGPU | **Free** | Up to 2 Spaces, personal accounts |
| Gradio paid GPU | $0.03–$23.50/hr | CPU upgrade to 8×A100 |
| `preload_from_hub` | **Free** | Build-phase download |
| OAuth | **Free** | Built-in |
| `custom_headers` | **Free** | Config only |
| Auto-sleep | **Free** | Idle → pause, no cost |

---

## Best Practices

1. **Pin `sdk_version`** — prevents Gradio release breakage.
2. **Use `preload_from_hub`** — cuts startup from minutes to seconds.
3. **Set `suggested_hardware` on templates** — duplicators get right defaults.
4. **Isolate only when needed** — `require-corp` blocks third-party resources.
5. **Restrict OAuth by org** — `hf_oauth_authorized_org` for internal tools.
6. **Write `short_description`** — improves discoverability.
7. **Auto-sleep is free** — no cost during idle.
8. **Static Spaces are forever free** — docs, portfolios, demos.

---

## Limitations

| Constraint | Detail |
|------------|--------|
| `suggested_hardware/storage` | **Hints only** — no auto-assignment |
| `preload_from_hub` cache | Always `~/.cache/huggingface/hub` — ignores `HF_HOME` |
| `custom_headers` | Only COEP, COOP, CORP — no arbitrary headers |
| Private repo preloading | **Not supported** |
| `suggested_storage` | Deprecated and **ignored** |
| Creating Spaces | Non-static need paid plan to **create** |
| OAuth redirect | Use `target=_blank` to avoid iframe cookie issues |

---

## Helper Environment Variables

| Variable | Description |
|----------|-------------|
| `SPACE_ID` | `org/space-name` |
| `SPACE_HOST` | `org-space-name.hf.space` |
| `SPACE_TITLE` | Title from YAML |
| `OAUTH_CLIENT_ID` | OAuth client ID |
| `OAUTH_CLIENT_SECRET` | OAuth client secret |
| `OAUTH_SCOPES` | Space-separated scopes |
| `OPENID_PROVIDER_URL` | OpenID provider |

---

## Related Documentation

- [Spaces Overview](https://huggingface.co/docs/hub/en/spaces-overview)
- [Spaces Dependencies](https://huggingface.co/docs/hub/en/spaces-dependencies)
- [Spaces ZeroGPU](https://huggingface.co/docs/hub/en/spaces-zerogpu)
- [Sign-In with HF](https://huggingface.co/docs/hub/en/spaces-oauth)
- [Spaces Docker](https://huggingface.co/docs/hub/en/spaces-docker)
- [Spaces GPU](https://huggingface.co/docs/hub/en/spaces-gpus)
- [HF OAuth](https://huggingface.co/docs/hub/en/oauth)