# Gradio Space Deployment — Production Checklist

> Bridging static Spaces → interactive Gradio 6 Spaces on Hugging Face

## When to use Gradio vs Static SDK

| Criteria | Gradio SDK | Static SDK |
|----------|-----------|------------|
| **Interactivity** | Forms, buttons, sliders, chat | Read-only content |
| **ML inference** | Python function → UI | Only if client-side JS |
| **Chatbots** | Built-in ChatInterface | Not supported natively |
| **Cost** | Free CPU tier | Free |
| **Build pipeline** | Installs deps, runs app.py | Just hosts static files |
| **API endpoint** | Automatic REST API per function | Manual |

## Space YAML Frontmatter (README.md)

When creating a new Gradio Space, include this frontmatter in your README.md:

```yaml
---
title: My Gradio Demo
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.20.0          # Pin to latest stable
app_file: app.py              # Entry point (default: app.py)
pinned: false
tags:
  - gradio
  - demo
  - llm
---
```

**Key fields:**
- `sdk: gradio` — tells HF Spaces to run a Gradio app
- `sdk_version` — pins the Gradio version. Match this with requirements.txt
- `app_file` — Python file to execute (default: app.py)
- `pinned` — show on profile if true

## Gradio 6 Migration Checklist

From the official [migration guide](https://gradio.app/main/guides/gradio-6-migration-guide):

| Before (Gradio 5) | After (Gradio 6) |
|-------------------|-----------------|
| `gr.Blocks(theme=..., css=...)` | `demo.launch(theme=..., css=...)` |
| `show_api=False` | Use `api_visibility="private"` |
| `api_name=False` | Use `api_visibility="private"` |
| `row_count=(5, "fixed")` | `row_count=5, row_limits=(5,5)` |
| Tuple `[[user, bot], ...]` | OpenAI dicts `{"role":"user","content":[...]}` |
| `gr.HTML(padding=True)` | `gr.HTML(padding=False)` (default changed) |
| `cache_examples="lazy"` | `cache_examples=True, cache_mode="lazy"` |
| `like_user_message` in `.like()` | `gr.Chatbot(like_user_message=True)` |

## Environment Variables

Configure these via Space Settings → Repository secrets:

| Variable | Purpose | Required |
|----------|---------|----------|
| `HF_TOKEN` | Access private models/datasets | For private resources |
| `OAUTH_CLIENT_ID` | HF OAuth authentication | For `auth=gr.oauth()` |
| `OAUTH_CLIENT_SECRET` | HF OAuth secret | For `auth=gr.oauth()` |
| `GRADIO_SSR` | Toggle SSR (`True`/`False`) | Optional |

## Queue Configuration

Gradio uses a queue system to manage concurrent requests:

```python
demo.queue(
    default_concurrency_limit=5,     # Max concurrent requests per user
    max_size=10,                      # Max queue size
)
```

- **CPU free tier:** Keep `default_concurrency_limit` ≤ 5 for responsiveness
- **ZeroGPU:** Can handle higher concurrency
- **Heavy models:** Lower to 1-2 to prevent OOM

## Authentication Options

### Option 1: HF OAuth (recommended)
```python
demo.launch(auth=gr.oauth())
```
Requires `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` secrets.

### Option 2: Password list
```python
demo.launch(auth=[("user1", "pass1"), ("user2", "pass2")])
```

### Option 3: Function-based
```python
def check_auth(username, password):
    return username == "admin" and password == "secret"

demo.launch(auth=check_auth)
```

## SSR (Server-Side Rendering)

SSR makes apps load almost instantly:

```python
demo.launch(ssr_mode=True)  # Default on Spaces
```

To disable SSR (useful for debugging):
```bash
export GRADIO_SSR=False
```

## MCP Server

Expose Gradio functions as MCP tools for agent frameworks:

```python
demo.launch(mcp_server=True)
```

## Going Live Checklist

- [ ] Requirements.txt pins Gradio >=6.0 to avoid 5.x defaults
- [ ] App-level params (theme, css) are in `launch()`, not `gr.Blocks()`
- [ ] Chat history format uses OpenAI-style dicts (for ChatInterface/6.x)
- [ ] `api_name` uses meaningful names (not `/predict` for every function)
- [ ] Queue is configured with appropriate concurrency limits
- [ ] HF Token is set in Space secrets if accessing private resources
- [ ] Space YAML frontmatter is correct (`sdk: gradio`)
- [ ] README.md has been enriched with ecosystem cross-links
