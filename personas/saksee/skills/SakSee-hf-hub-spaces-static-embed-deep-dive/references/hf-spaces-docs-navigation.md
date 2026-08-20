# HF Spaces Docs — URL Map & Research Notes

## Canonical docs URLs (HF Hub Spaces)

Discovered 2026-07-30 by web scraping the HF docs sidebar.

| Page | URL |
|------|-----|
| Spaces Overview | https://huggingface.co/docs/hub/en/spaces-overview |
| Gradio Spaces | https://huggingface.co/docs/hub/en/spaces-sdks-gradio |
| Streamlit Spaces | https://huggingface.co/docs/hub/en/spaces-sdks-streamlit |
| Static HTML Spaces | https://huggingface.co/docs/hub/en/spaces-sdks-static |
| Docker Spaces | https://huggingface.co/docs/hub/en/spaces-docker |
| Spaces Configuration Reference | https://huggingface.co/docs/hub/en/spaces-config-reference |
| Embed your Space | https://huggingface.co/docs/hub/en/spaces-embed |
| Spaces Dev Mode | https://huggingface.co/docs/hub/en/spaces-dev-mode |
| Spaces GPU Upgrades | https://huggingface.co/docs/hub/en/spaces-gpu-upgrade |
| Spaces ZeroGPU | https://huggingface.co/docs/hub/en/spaces-zero-gpu |
| Spaces Disk Usage & Storage | https://huggingface.co/docs/hub/en/spaces-disk-usage |
| Spaces Custom Domain | https://huggingface.co/docs/hub/en/spaces-custom-domain |
| Spaces as MCP Servers | https://huggingface.co/docs/hub/en/spaces-as-mcp-servers |
| Spaces as Agent Tools | https://huggingface.co/docs/hub/en/spaces-as-agent-tools |
| Spaces as API Endpoints | https://huggingface.co/docs/hub/en/spaces-as-api-endpoints |
| Sign-In with HF button | https://huggingface.co/docs/hub/en/spaces-oauth |
| Spaces Changelog | https://huggingface.co/docs/hub/en/spaces-changelog |

## URL pattern

The HF Hub docs use: `https://huggingface.co/docs/hub/en/<kebab-case-slug>`

Slugs for Spaces pages follow `spaces-<topic>` pattern. The SDK sub-pages use `spaces-sdks-<sdk>`.

## Key research findings (scraped 2026-07-30)

### Static HTML Spaces
- Set `sdk: static` in README.md YAML
- Serve from `index.html` at repo root
- Free — no paid plan needed
- Build step via `app_build_command` + `app_file`
- Build output stored in `refs/convert/build` git ref
- Env vars via `window.huggingface.variables` (NOT `os.getenv` — JS only)
- Secrets NOT available in static Spaces (only Variables)
- OAuth available for static Spaces

### Embedding
- Public or Protected Spaces can be embedded
- Private Spaces cannot be embedded
- **Iframe**: works for all SDKs — `<iframe src="https://<subdomain>.hf.space">`
- **WebComponents**: Gradio only — `<gradio-app src="...">` (faster, auto-sizing)
- Protected Spaces = source private, app public via embed URL
- `disable_embedding: true` blocks external iframe embed

### Built-in env vars available to ALL Spaces
```
ACCELERATOR, CPU_CORES, MEMORY, SPACE_AUTHOR_NAME, SPACE_REPO_NAME,
SPACE_TITLE, SPACE_ID, SPACE_HOST, SPACE_CREATOR_USER_ID
```

### OAuth env vars (when enabled)
```
OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_SCOPES, OPENID_PROVIDER_URL
```

## Gradio WebComponent embed Snippet
```html
<script type="module" src="https://gradio.s3-us-west-2.amazonaws.com/<version>/gradio.js"></script>
<gradio-app src="https://<space-subdomain>.hf.space"></gradio-app>
```

## Getting subdomain programmatically
```python
from huggingface_hub import HfApi
info = HfApi().space_info("namespace/repo")
print(info.subdomain)  # e.g., "namespace-repo"
```

## Sidebar structure insight
The HF docs sidebar is a nested tree, NOT reflected in URL structure. Each section header ("Spaces", "Models", "Repositories") expands sub-items that exist at flat URLs like `spaces-embed`. There is no URL nesting like `spaces/embed`. The sidebar state is controlled by JS — the active page is highlighted but the collapsed/expanded state is client-side only.
