# Gradio 6.x Deep Dive — MCP Integration, New Components & Ecosystem Changes

**Date:** 2026-07-24
**Topic:** `gradio-6-mcp-and-new-components` — Deepen existing Gradio 5 coverage with Gradio 6.20.0 features
**Author:** SakThai
**License:** MIT

> Current Gradio version: **6.20.0** (stable, published on gradio.app/docs)
> Older docs versions available: 5.49.1, 4.44.1, main (unreleased)
> Latest install wheel: `pip install https://gradio-builds.s3.amazonaws.com/<hash>/gradio-6.20.0-py3-none-any.whl`

---

## 1. Gradio 6.x vs 5.x — What Changed

Gradio 6.20.0 is a major version jump from 5.49.1. The headline addition is **native MCP (Model Context Protocol) server support**, plus a wave of new UI components and client improvements.

### Key Differences

| Area | Gradio 5.x | Gradio 6.20.0 |
|------|-----------|---------------|
| **MCP Server** | Not available | Native `mcp_server=True` in `.launch()` |
| **MCP Primitives** | None | `@gr.mcp.resource`, `@gr.mcp.prompt` decorators |
| **Authentication** | `gr.Request` only | `gr.Header` type annotation for auth headers |
| **New Components** | ~40 components | +11 new: Dialogue, ImageSlider, Navbar, ParamViewer, SimpleImage, Sidebar, LoginButton, DuplicateButton, ClearButton, Timer, FileExplorer |
| **JS Client** | v1.x (basic predict) | v2.3.1 with `handle_file()`, `submit()`, `duplicate()`, `view_api()` |
| **Python Client** | Pre-1.0 | **Version 1 Release** — stable API |
| **Gradio Lite** | Experimental | Production-ready at 6.20.0 |
| **Docs MCP** | None | Official Gradio docs served as MCP server at `gradio-docs-mcp.hf.space` |
| **`gr.api()`** | No | Yes — create pure API endpoints (no UI) for MCP-only tools |

---

## 2. MCP Server Integration (Headline Feature)

Turning any Gradio app into an MCP server is a **one-line change**:

```python
import gradio as gr

def letter_counter(text: str, letter: str) -> str:
    """Count occurrences of a letter in text.
    Args:
        text: The text to search in
        letter: The letter to count
    Returns:
        The count as a string
    """
    return str(text.count(letter))

gr.Interface(
    fn=letter_counter,
    inputs=[gr.Textbox("strawberry"), gr.Textbox("r")],
    outputs=gr.Textbox()
).launch(mcp_server=True)
```

### How It Works

- Every API endpoint is **auto-converted** into an MCP tool
- **Tool name** = function name
- **Tool description** = function docstring (parameters from type hints and parameter docstrings)
- **Default values** = initial values from `gr.Textbox(value=...)`
- MCP server URL: `http://your-server:port/gradio_api/mcp/`
- Schema endpoint: `http://your-server:port/gradio_api/mcp/schema`
- Visible in "View API" → "MCP" tab

### Configuration Methods

1. **Parameter** (recommended):
   ```python
   demo.launch(mcp_server=True)
   ```

2. **Environment variable**:
   ```bash
   export GRADIO_MCP_SERVER=True
   ```

### MCP Client Config for Your App

For streamable HTTP clients (Cursor, Windsurf, Cline):
```json
{
  "mcpServers": {
    "gradio": {
      "url": "https://your-space.hf.space/gradio_api/mcp/"
    }
  }
}
```

For stdio-only clients (Claude Desktop), use `npx mcp-remote`:
```json
{
  "mcpServers": {
    "gradio": {
      "command": "npx",
      "args": ["mcp-remote", "https://your-space.hf.space/gradio_api/mcp/"]
    }
  }
}
```

### Private Spaces with MCP

Add an `Authorization` header:
```json
{
  "mcpServers": {
    "gradio": {
      "url": "https://your-space.hf.space/gradio_api/mcp/",
      "headers": {
        "Authorization": "Bearer <HF_TOKEN>"
      }
    }
  }
}
```

### Performance Note

Set `queue=False` in event handlers to reduce latency by ~10x, at the cost of losing progress notifications:
```python
btn.click(fn=my_func, queue=False)
```

---

## 3. MCP Resources & Prompts (Beyond Tools)

MCP supports three primitives. Gradio exposes all three:

### Tools (default)
Any Gradio function endpoint → MCP tool.

### Resources (`@gr.mcp.resource`)
Expose data at URIs — static or templated:
```python
@gr.mcp.resource(uri="greeting://{name}")
def get_greeting(name: str) -> str:
    return f"Hello, {name}!"

# Binary/image resources with mime_type:
@gr.mcp.resource(uri="logo", mime_type="image/png")
def get_logo() -> str:
    # Return base64-encoded PNG
    return "iVBORw0KGgo..."
```

### Prompts (`@gr.mcp.prompt`)
Reusable prompt templates:
```python
@gr.mcp.prompt()
def greet_user(name: str, style: str = "formal") -> list:
    return [
        {"role": "system", "content": f"You are a {style} assistant."},
        {"role": "user", "content": f"Greet {name}!"}
    ]
```

---

## 4. Customizing Tool Descriptions

Two parameters control MCP tool metadata:

| Parameter | Values | Effect |
|-----------|--------|--------|
| `api_description` | `None` (default) | Auto-generate from docstring |
| | `False` | No description sent to LLM |
| | `str` | Custom description string |
| `show_api` | `True` (default) | Visible in API docs and MCP |
| | `False` | Hidden from API/MCP entirely |

Example:
```python
def fetch_weather(city: str) -> str:
    """..."""
    pass

gr.Interface(
    fn=fetch_weather,
    inputs=gr.Textbox(),
    outputs=gr.Textbox(),
    api_description="Get current weather for a city. Returns temp, humidity, conditions."
).launch(mcp_server=True)
```

---

## 5. Authentication & Credentials

### `gr.Header` — Extract Headers Automatically

New in Gradio 6: annotate a parameter with `gr.Header` to extract any HTTP header:

```python
def make_api_call(prompt: str, x_api_token: gr.Header):
    """Make a call.
    Args:
        prompt: The prompt.
    Returns:
        The response.
    """
    if x_api_token:
        # Use token to call external API
        ...
    return "Result"

gr.Interface(
    fn=make_api_call,
    inputs=[gr.Textbox(label="Prompt")],
    outputs=gr.Textbox()
).launch(mcp_server=True)
```

The MCP connection docs **automatically display required headers** to users.

### `gr.Request` — Full Request Access

Access the Starlette request object (useful for IP, user-agent, etc.):
```python
def echo_headers(x: str, request: gr.Request):
    return str(dict(request.headers))
```

Note: Only Starlette core attributes are present; Gradio-specific attributes (`.session_hash`) are NOT available in MCP context.

### Progress Updates

Custom progress via `gr.Progress` works in MCP context:
```python
def long_task(x, progress=gr.Progress()):
    for i in progress.tqdm(range(100)):
        time.sleep(0.1)
    return "Done"
```

Progress notifications add ~500ms overhead. Disable with `queue=False` if not needed.

---

## 6. MCP-Only Functions via `gr.api()`

For tools that should NOT have a UI component (pure logic returning raw data):

```python
gr.api(
    fn=my_slice_function,
    inputs=[gr.Dataframe(), gr.Slider(0, 1)],
    outputs=gr.JSON(),
    api_name="slice_dataframe"
)
```

Requirements: **fully typed** signature including return value.

---

## 7. File Upload MCP Server

Gradio 6 includes a built-in file upload MCP server. You don't need to write code for it.

**Start from CLI** (requires `uv`):
```bash
uvx gradio upload-mcp <GRADIO_APP_URL> <UPLOAD_DIRECTORY>
```

Or with the gradio binary directly:
```json
{
  "mcpServers": {
    "upload-files": {
      "command": "/path/to/gradio",
      "args": ["upload-mcp", "http://localhost:7860/", "/Users/me/Pictures"]
    }
  }
}
```

The `Upload Directory` should be as **narrow as possible** for security.

---

## 8. New Components in Gradio 6.20.0

| Component | Purpose | Example Use |
|-----------|---------|-------------|
| **Dialogue** | Dialogue/decision trees | Interactive story, choose-your-own-adventure |
| **ImageSlider** | Side-by-side image comparison | Before/after, model comparison |
| **Navbar** | Navigation bar for multi-page apps | App header with links |
| **ParamViewer** | View/edit model parameters | ML model inspection |
| **SimpleImage** | Lightweight image display | Faster than `gr.Image` when no editing needed |
| **Sidebar** | Side panel layout | Navigation, filters, info panel |
| **LoginButton** | Authentication button | Login with HF account |
| **DuplicateButton** | Duplicate a Space | "Make a copy" UX |
| **ClearButton** | Clear/reset action | Reset form fields |
| **Timer** | Timed/periodic events | Auto-refresh, polling, countdown |
| **FileExplorer** | File system browser | Pick files from server |

---

## 9. JS Client v2.3.1 — Key Changes

Install: `npm install @gradio/client` (v2.3.1)

### `handle_file()` — Unified File Input

Handles local file paths, URLs, Blobs, Buffers — automatically uploads:
```ts
import { Client, handle_file } from "@gradio/client";

const app = await Client.connect("user/space-name");
const result = await app.predict("/predict", {
    image: handle_file("path/to/image.png"),
    audio: handle_file("https://example.com/audio.mp3"),
    blend: handle_file(new Blob(["data"])),
});
```

### `submit()` — Async Iteration with Status Updates

```ts
const submission = app.submit("/predict", { name: "Chewbacca" });

for await (const msg of submission) {
    if (msg.type === "data") {
        console.log(msg.data);
    }
    if (msg.type === "status") {
        console.log(`Stage: ${msg.stage}, Queue: ${msg.position}`);
    }
}

// Cancel a running generation
submission.cancel();
```

### `duplicate()` — Duplicate a Space Programmatically

```ts
const app = await Client.duplicate("user/space-name", {
    token: "hf_...",
    private: true,
    timeout: 5,                       // minutes before sleep
    hardware: "a10g-small",          // or "zero-a10g", "t4-medium", etc.
});
```

### `view_api()` + `config`

```ts
const api_info = await app.view_api();
console.log(app.config);             // app config metadata
```

### Status Events

```ts
const app = await Client.connect("user/space-name", {
    events: ["data", "status"],
    space_status: (status) => console.log(status),
});
```

`SpaceStatus` types:
- Normal: `"sleeping" | "running" | "building" | "error" | "stopped"`
- Error: `"space_error"` with detail `"NO_APP_FILE" | "CONFIG_ERROR" | "BUILD_ERROR" | "RUNTIME_ERROR"`

---

## 10. Docs MCP Server (Official)

Gradio provides an official Docs MCP server at:

```
https://gradio-docs-mcp.hf.space/gradio_api/mcp/
```

Two tools:
- `gradio_docs_mcp_load_gradio_docs` — loads full docs summary (llms.txt style)
- `gradio_docs_mcp_search_gradio_docs` — embedding search on docs/guides/demos

Use this via any MCP client to get instant Gradio documentation context in your LLM.

---

## 11. Gradio with FastMCP (Manual Integration)

If Gradio's built-in MCP is insufficient, build a custom FastMCP server:

```python
from mcp.server.fastmcp import FastMCP
from gradio_client import Client

mcp = FastMCP("gradio-spaces")

@mcp.tool()
async def generate_image(prompt: str, space_id: str = "ysharma/SanaSprint") -> str:
    """Generate an image."""
    client = Client(space_id)
    result = client.predict(prompt, api_name="/infer")
    return result

mcp.run(transport='stdio')
```

Useful when you need:
- State persistence between calls
- User identity management
- Lazy loading of multiple Spaces (memory efficiency)

---

## 12. Python Client v1 Release

The Python client (`gradio_client`) hit Version 1 in the Gradio 6 era. Key features:
- Stable, documented API surface
- `Client` class with `predict()`, `submit()`, `view_api()`
- `Job` class for async/complex operations
- ZeroGPU Spaces support built in

---

## Summary of Migration Notes (Gradio 5 → 6)

1. **No breaking changes found** in the 5→6 jump for basic usage patterns
2. **Add MCP with one line**: `demo.launch(mcp_server=True)`
3. **New component imports** work immediately — just use `gr.Dialogue()`, `gr.ImageSlider()`, etc.
4. **JS Client users**: upgrade for `handle_file()` and `submit()` — both simplify file handling
5. **Python Client users**: stable v1 API now
6. **Security**: use `gr.Header` for auth, set upload directories narrowly for file MCP
7. **Performance**: `queue=False` on MCP handlers for 10x speed
8. **Docs**: Use `https://gradio-docs-mcp.hf.space/gradio_api/mcp/` in any MCP client for instant docs
