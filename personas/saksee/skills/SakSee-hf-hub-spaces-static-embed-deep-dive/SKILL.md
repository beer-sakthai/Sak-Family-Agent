---
name: SakSee-SakThai-hf-hub-spaces-static-embed-deep-dive
description: ">-   Complete deep-dive on Hugging Face Hub Static HTML Spaces and embedding   Spaces in external websites. Covers creation, configuration (YAML frontmatter),   build step integration (React, Svelte, Vue), accessing env vars and OAuth from   JavaScri"
---

# Hugging Face Hub — Static HTML Spaces & Embedding Deep Dive

## Overview

Spaces on HF Hub support **four SDK types**: Gradio, Streamlit, Docker, and **Static HTML**. Static HTML Spaces are unique because:

- **They are free for everyone** — no paid plan needed to create them.
- They serve directly without running on compute (no VM, no GPU cost).
- They support a **build step** for modern JS frameworks (React, Svelte, Vue).
- They expose **env vars and OAuth tokens** via `window.huggingface.variables`.
- They can be **embedded** in external websites via iframe or WebComponents.

---

## 1. Creating a Static HTML Space

### README.md YAML frontmatter

Set `sdk: static` in the YAML block at the top of your Space's `README.md`:

```yaml
---
title: My Static Space
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: static
pinned: false
short_description: A minimal static Space
---
```

Then create an **`index.html`** file at the root of the repository. Static Spaces serve exactly one HTML file plus its assets (CSS, JS, images).

### Minimal index.html

```html
<!DOCTYPE html>
<html>
<head>
  <title>My Static Space</title>
</head>
<body>
  <h1>Hello from HF Spaces!</h1>
</body>
</html>
```

---

## 2. Adding a Build Step

Static Spaces support a **custom build command** for frontend frameworks. The build runs automatically when the Space is updated.

### Configuration

Add these fields to your README.md YAML:

```yaml
---
sdk: static
app_build_command: npm run build
app_file: dist/index.html
---
```

- **`app_build_command`** — shell command to run at build time
- **`app_file`** — path to the built HTML file (relative from repo root)

### How it works

1. When you push a commit, HF runs a **Job** that executes `app_build_command`
2. The build output is stored in a special `refs/convert/build` git ref
3. The Space serves files from that ref

### Examples

**React App:**
```yaml
---
sdk: static
app_build_command: npm run build
app_file: build/index.html
---
```

**Svelte App:**
```yaml
---
sdk: static
app_build_command: npm run build
app_file: public/index.html
---
```

**Vue App:**
```yaml
---
sdk: static
app_build_command: npm run build
app_file: dist/index.html
---
```

### Pitfalls

- The build command runs **without an interactive shell** — ensure all deps are declared in `package.json`
- Use `npm ci` instead of `npm install` for reproducible builds
- The build timeout is 30 minutes by default (configurable via `startup_duration_timeout`)
- If you need system dependencies, consider a **Docker Space** instead

---

## 3. Accessing Environment Variables

Static Spaces expose env vars and OAuth tokens through **`window.huggingface.variables`**.

### Reading variables

```javascript
// Access standard env vars
const spaceAuthor = window.huggingface.variables.SPACE_AUTHOR_NAME;
const spaceName = window.huggingface.variables.SPACE_REPO_NAME;
const spaceTitle = window.huggingface.variables.SPACE_TITLE;
const spaceHost = window.huggingface.variables.SPACE_HOST;

// Access custom variables (set in Space Settings → Variables)
const apiUrl = window.huggingface.variables.API_URL;

// Access OAuth variables (if OAuth is enabled)
const oauthClientId = window.huggingface.variables.OAUTH_CLIENT_ID;
const oauthScopes = window.huggingface.variables.OAUTH_SCOPES;
const openidProviderUrl = window.huggingface.variables.OPENID_PROVIDER_URL;
```

### Important notes

- Variables are injected at serve-time, **not build-time** — always read them at runtime
- Not all Python/Gradio env vars are available in static Spaces (only those listed in the [built-in env vars docs](https://huggingface.co/docs/hub/en/spaces-overview#built-in-environment-variables))
- **Secrets** (sensitive values set in Settings → Secrets) are **not available** in static Spaces. Only **Variables** (non-sensitive) are exposed
- For Docker Spaces, use environment variables directly; for Gradio/Streamlit, use `os.getenv()`

---

## 4. OAuth in Static Spaces

Static Spaces can integrate **Sign-In with HF** OAuth.

### Enable OAuth

Add to README.md YAML:

```yaml
---
hf_oauth: true
hf_oauth_scopes:
  - openid
  - profile
---
```

### JavaScript OAuth flow from static Spaces

```javascript
// Read OAuth config from injected variables
const clientId = window.huggingface.variables.OAUTH_CLIENT_ID;
const providerUrl = window.huggingface.variables.OPENID_PROVIDER_URL;

// Use the OpenID provider to initiate login
// The user is redirected to HF, then back to your Space
```

### Restricting OAuth to specific orgs

```yaml
---
hf_oauth: true
hf_oauth_authorized_org: my-organization
---
```

Also works with a list:

```yaml
---
hf_oauth_authorized_org:
  - org-alpha
  - org-beta
---
```

### Token expiration

```yaml
---
hf_oauth_expiration_minutes: 480  # default 8h, max 43200 (30 days)
---
```

---

## 5. Spaces Configuration Reference (All SDKs)

All configuration goes in the YAML frontmatter of `README.md`.

### Required fields

| Field | Type | Description |
|-------|------|-------------|
| `sdk` | `string` | One of: `gradio`, `docker`, `static` |

### Display & branding

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `title` | `string` | - | Display title |
| `emoji` | `string` | - | Emoji for thumbnail |
| `colorFrom` | `string` | - | Gradient start: `red`, `yellow`, `green`, `blue`, `indigo`, `purple`, `pink`, `gray` |
| `colorTo` | `string` | - | Gradient end (same options) |
| `fullWidth` | `boolean` | `true` | Full-width or fixed container |
| `header` | `string` | `default` | `mini` for floating mini header |
| `short_description` | `string` | - | Shown in thumbnail |
| `thumbnail` | `string` | - | Custom social share image URL |
| `pinned` | `boolean` | `false` | Pin to top of profile |

### SDK configuration

| Field | Type | Description |
|-------|------|-------------|
| `sdk_version` | `string` | Gradio/Streamlit version |
| `python_version` | `string` | `3.10` default |
| `app_file` | `string` | Path to main app file (Gradio Python or static HTML) |
| `app_build_command` | `string` | Build command for static Spaces |
| `app_port` | `int` | Port for Docker Spaces (default `7860`) |
| `base_path` | `string` | Initial URL path (non-static) |

### Content linking

| Field | Type | Description |
|-------|------|-------------|
| `models` | `List[string]` | HF model IDs used in the Space |
| `datasets` | `List[string]` | HF dataset IDs used in the Space |
| `tags` | `List[string]` | Tags for discoverability |

### OAuth

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `hf_oauth` | `boolean` | `false` | Enable OAuth |
| `hf_oauth_scopes` | `List[string]` | `["openid", "profile"]` | OAuth scopes |
| `hf_oauth_expiration_minutes` | `int` | `480` | Token lifetime (max 43200) |
| `hf_oauth_authorized_org` | `string` or `List[string]` | - | Restrict to org members |

### Advanced

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `disable_embedding` | `boolean` | `false` | Prevent iframe embedding |
| `startup_duration_timeout` | `string` | `30m` | Build/start timeout (e.g. `1h`) |
| `suggested_hardware` | `string` | - | Suggested hardware for duplication |
| `custom_headers` | `Dict[string, string]` | - | COEP/COOP/CORP headers only |
| `preload_from_hub` | `List[string]` | - | Preload HF artifacts at build time |

### Custom headers for cross-origin isolation

```yaml
---
custom_headers:
  cross-origin-embedder-policy: require-corp
  cross-origin-opener-policy: same-origin
  cross-origin-resource-policy: cross-origin
---
```

Enables `SharedArrayBuffer` and other powerful browser features. All headers and values must be lowercase.

### Preloading models at build time

```yaml
---
preload_from_hub:
  - openai-community/gpt2 config.json 11c5a3d5811f50298f278a704980280950aedb10
  - warp-ai/wuerstchen-prior text_encoder/model.safetensors,prior/diffusion_pytorch_model.safetensors
  - coqui/XTTS-v1
---
```

Format: `"repo_name"`, `"repo_name file1,file2"`, or `"repo_name file1,file2 commit_sha"`. Files are saved to `~/.cache/huggingface/hub`.

---

## 6. Embedding Spaces in External Websites

Spaces can be embedded in any website. The Space must be **public** or **protected** (not private).

### Via iframe (all SDKs)

```html
<iframe
  src="https://<space-subdomain>.hf.space"
  frameborder="0"
  width="850"
  height="450"
></iframe>
```

The subdomain is unique. Find it in the Space's options menu or via the API:

```python
from huggingface_hub import HfApi
subdomain = HfApi().space_info("namespace/repo").subdomain
print(f"https://{subdomain}.hf.space")
```

### Via Gradio WebComponents (Gradio Spaces only)

Faster than iframes, auto-adjusting size:

```html
<script
  type="module"
  src="https://gradio.s3-us-west-2.amazonaws.com/<version>/gradio.js"
></script>
<gradio-app src="https://<space-subdomain>.hf.space"></gradio-app>
```

WebComponents inherit page styling and auto-resize to fit content.

### Protected Spaces

Protected Spaces keep the source code private but the running app is publicly accessible:

| | Public | Protected | Private |
|---|---|---|---|
| Source code | Visible | Private | Private |
| App via embed URL | Yes | Yes | No |
| App via custom domain | Yes | Yes | No |
| Clonable | Yes | No | No |

### Disabling embedding

Add to README.md:

```yaml
---
disable_embedding: true
---
```

This blocks iframe embedding from external domains. The Space still works on HF Hub itself.

---

## 7. Using HuggingFace.js from Static Spaces

The `@huggingface/inference` JS SDK works from static Spaces for browser-side inference calls.

### Installation

```bash
npm install @huggingface/inference
```

### Usage

```javascript
import { HfInference } from '@huggingface/inference';

const hf = new HfInference(window.huggingface.variables.HF_TOKEN || 'fallback');

// Text generation
const response = await hf.textGeneration({
  model: 'gpt2',
  inputs: 'Hello, my name is',
});

// Fill mask
const result = await hf.fillMask({
  model: 'bert-base-uncased',
  inputs: 'The answer to the question is [MASK].',
});
```

**Important:** For static Spaces, you cannot store API tokens in Secrets. Use a custom Variable with a read-only HF token, or use free Inference API endpoints that don't require auth.

---

## 8. Full Example: Static Space with Build + OAuth + Variables

### README.md

```yaml
---
title: AI Demo Dashboard
emoji: 🤖
colorFrom: purple
colorTo: pink
sdk: static
app_build_command: npm run build
app_file: dist/index.html
pinned: true
suggested_hardware: t4-small
models:
  - openai-community/gpt2
  - bert-base-uncased
tags:
  - demo
  - ai
  - dashboard
hf_oauth: true
hf_oauth_scopes:
  - openid
  - profile
custom_headers:
  cross-origin-embedder-policy: require-corp
  cross-origin-opener-policy: same-origin
---
```

### index.html (or built output from framework)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Demo Dashboard</title>
</head>
<body>
  <div id="app">
    <h1>Welcome, <span id="user">Guest</span></h1>
    <p>Space: <span id="space-name"></span></p>
  </div>

  <script>
    // Read HF variables
    const vars = window.huggingface?.variables || {};
    document.getElementById('space-name').textContent =
      vars.SPACE_TITLE || vars.SPACE_REPO_NAME || 'unknown';

    // If OAuth is configured, you could initiate login here
    if (vars.OAUTH_CLIENT_ID) {
      console.log('OAuth available, client ID:', vars.OAUTH_CLIENT_ID);
    }
  </script>
</body>
</html>
```

---

## 9. Best Practices

### Static Spaces

- **Keep it simple** — Static Spaces are best for landing pages, demos, documentation, and interactive visualizations
- **Use build steps wisely** — For complex JS apps, set up a proper build pipeline; for simple pages, just write raw HTML
- **Asset optimization** — Optimize images, minify CSS/JS, use CDN for large libraries
- **Avoid API keys in client code** — Use HF Inference API (free tier) for serverless inference
- **Test locally first** — Run `npm run build` locally before pushing to catch build errors early

### Embedding

- **Use iframe** for non-Gradio Spaces (static, Streamlit, Docker)
- **Use WebComponents** for Gradio Spaces (faster, responsive)
- **Set `disable_embedding: true`** only when necessary (e.g., for Spaces with sensitive UI)
- **Protected Spaces** are ideal for embedding demos while keeping source private
- The embed URL is stable unless you move/rename the Space

### Configuration

- **Always set `title`** for SEO and discoverability
- **Use `models:` and `datasets:`** lists for cross-linking on the Hub
- **Pin your best Spaces** with `pinned: true`
- Full-width (`fullWidth: true`) is the default and usually best
- **Preload models** for faster cold starts on Gradio/Docker Spaces

---

## 10. Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Build fails silently | Missing `package.json` or deps | Run build locally first; check build logs in Space logs |
| `window.huggingface.variables` is undefined | Static Space hasn't injected vars yet | Access on DOMContentLoaded or wrap in try/catch |
| OAuth login doesn't redirect | Missing redirect URI config | Configure allowed redirect URIs in Space Settings |
| Space doesn't update after push | Build cache | Push an empty commit or trigger rebuild from Settings |
| Embed iframe shows blank | `disable_embedding: true` | Remove the flag; check Space visibility (must be public/protected) |
| CORS errors from JS API calls | No custom headers | Add `cross-origin-embedder-policy` header |
| Cross-origin isolation needed | `SharedArrayBuffer` not available | Add all 3 `custom_headers` with correct policy values |

---

## References

- `references/hf-spaces-docs-navigation.md` — URL map, sidebar structure, research notes
- [HF Docs: Static HTML Spaces](https://huggingface.co/docs/hub/en/spaces-sdks-static)
- [HF Docs: Embed your Space](https://huggingface.co/docs/hub/en/spaces-embed)
- [HF Docs: Spaces Configuration Reference](https://huggingface.co/docs/hub/en/spaces-config-reference)
- [HF Docs: Spaces Overview](https://huggingface.co/docs/hub/en/spaces-overview)
- [HF Docs: Spaces Visibility](https://huggingface.co/docs/hub/en/spaces-overview#space-visibility)
- [HF Docs: OAuth for Spaces](https://huggingface.co/docs/hub/en/spaces-oauth)
- [Gradio WebComponents](https://www.gradio.app/docs/guides/embedding-gradio-apps)
- [HuggingFace.js (`@huggingface/inference`)](https://huggingface.co/docs/huggingface.js/inference/README)
