# SSR and Environment Variables — condensed reference

Enabling SSR (server-side rendering) on HF Spaces makes apps load almost instantly.

## SSR control
- `GRADIO_SSR=False` disables SSR (useful for debugging).
- Space default: `True`.
- Local default: `False`.

## Other env vars
| Var | Purpose |
|-----|---------|
| `GRADIO_DEBUG` | Keep main thread alive for Colab debugging. |
| `GRADIO_CACHE_EXAMPLES` | Default `cache_examples` behavior (`"true"`/`"false"`). |
| `GRADIO_SERVER_PORT` | Override listen port. |
| `FORWARDED_ALLOW_IPS` | Trust reverse proxy IPs for `X-Forwarded-For` (uvicorn). |

## MCP server flag
```python
demo.launch(mcp_server=True)
```
Exposes the app's functions as MCP tools for agent frameworks.
