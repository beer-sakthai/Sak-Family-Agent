# Gradio Documentation Sources (mid-2026)

Sources discovered during research when web search (Composio/Exa) timed out. These raw URLs load fast and work without JS rendering.

## Official API Docs (JS-rendered — use browser or curl to grab page HTML)

| Source | URL |
|---|---|
| Gradio API docs (all versions) | `https://www.gradio.app/docs/gradio/blocks` |
| Gradio Python Client docs | `https://www.gradio.app/docs/python-client/introduction` |
| Gradio JS Client docs | `https://www.gradio.app/docs/js-client` |
| Gradio Guides | `https://www.gradio.app/guides/` |
| HF Spaces Gradio SDK docs | `https://huggingface.co/docs/hub/en/spaces-sdks-gradio` |

## Raw Markdown (curl-friendly)

These are served directly as plain text from GitHub — no JS, no HTML wrapper.

| Content | Raw URL |
|---|---|
| Gradio Quickstart guide | `https://raw.githubusercontent.com/gradio-app/gradio/main/guides/01_getting-started/01_quickstart.md` |
| HF Spaces overview | `https://huggingface.co/docs/hub/en/spaces-overview` (HTML but loads clean) |

## Version Info

- **Current Gradio version (mid-2026):** 6.20.0 (shown at `/docs/gradio/blocks` version selector)
- **Gradio 5.49.1** and **4.44.1** also available in docs version selector
- **`main`** branch docs available but may contain unreleased features

For quick check: `curl -sL "https://www.gradio.app/docs/gradio/blocks" | grep -oP 'option value="\K[^"]+'`

## Research Fallback When Web Search Fails

1. Try known Raw GitHub URLs (guides, code examples)
2. Fetch HF docs via `huggingface.co/docs/hub/en/` + topic path
3. For JS-rendered sites (gradio.app), `curl` + `grep` for version selectors or data embedded in page HTML
4. GitHub API (`api.github.com/repos/gradio-app/gradio`) — but watch for rate limits
