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

---

# HF Space Logs, Monitoring & Debugging — Complete Deep Dive

**Date:** 2026-07-24
**Topic:** `hf-spaces-logs-monitoring-and-debugging-deep-dive` — Programmatic log access, build/runtime debugging, sleep/wake lifecycle monitoring, zero-cost troubleshooting
**Author:** SakThai
**License:** MIT

> On free-tier HF Spaces, containers sleep after inactivity, build logs expire, and runtime crashes produce no alert. This doc covers every available tool for monitoring and debugging Spaces *without spending money*.

---

## 1. The Two Log Streams

Every Space has **two independent log streams**:

| Stream | When | What it contains | Available where |
|--------|------|-------------------|-----------------|
| **Build logs** | During `docker build` | Package installs, download progress, compilation errors, `Dockerfile` failures | `fetch_space_logs(build=True)` — available during and after build |
| **Runtime logs** | While app is running | Python stdout/stderr, Gradio server output, application print/log statements | `fetch_space_logs(build=False)` — live when Space is RUNNING |

**Key insight:** If your Space shows `BUILD_ERROR` status, the runtime logs will be *empty* — you must read the **build logs** to see what went wrong. Conversely, if it shows `RUNNING` but the app doesn't respond, the **runtime logs** are where you look.

---

## 2. Programmatic Log Access with `huggingface_hub`

The primary API is `HfApi.fetch_space_logs()`:

```python
from huggingface_hub import HfApi

api = HfApi()
repo_id = "your-username/your-space-name"

# 1. Read runtime logs (drain mode — like `docker logs`)
for line in api.fetch_space_logs(repo_id=repo_id):
    print(line, end="")

# 2. Read build logs (for BUILD_ERROR debugging)
for line in api.fetch_space_logs(repo_id=repo_id, build=True):
    print(line, end="")

# 3. Stream runtime logs in real time (follow mode, like `tail -f`)
# Blocks until the server closes the stream — Ctrl-C to stop
for line in api.fetch_space_logs(repo_id=repo_id, follow=True):
    print(line, end="")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `repo_id` | str | required | `"namespace/space-name"` |
| `build` | bool | `False` | Get build logs instead of runtime logs |
| `follow` | bool | `False` | Stream new logs in real time instead of draining |
| `token` | str | cached | HF token (needed for private spaces) |

**Limitations:**
- Build logs are **not available indefinitely** — they expire after the next successful build or after some time (exact TTL undocumented)
- There is no pagination/offset parameter — you get the entire available log output
- No structured/JSON format — plain text only

---

## 3. CLI Log Access via `hf spaces logs`

The `huggingface_hub` CLI provides the same functionality:

```bash
# Drain runtime logs
hf spaces logs username/my-space

# Read build logs
hf spaces logs username/my-space --build

# Stream in real time
hf spaces logs username/my-space -f

# Last 50 lines only
hf spaces logs username/my-space -n 50

# With token explicitly
hf spaces logs username/my-space --token hf_xxxxx
```

This is the fastest way to debug during development without opening a browser.

---

## 4. Debugging by Space Status

The Spaces API returns a `runtime` status. Map status → diagnostic action:

| Status | Meaning | What to check |
|--------|---------|---------------|
| `NO_APP_FILE` | Missing `app.py` or wrong `app_file` path | Check README.yaml `app_file:` setting |
| `BUILDING` | Docker image being built | Wait; check logs if it stays here >15 min |
| `BUILD_ERROR` | Docker build failed | **Read build logs** (`build=True`) — this is the #1 source of truth |
| `RUNNING` | App is live | Check runtime logs if app isn't responding |
| `RUNNING_BUILDING` | App serving while new build deploys | Normal during updates |
| `PAUSED` | Manually stopped by user | Restart via API or UI |
| `SLEEPING` | Free-tier space went to sleep due to inactivity | Wake by sending an HTTP request |
| `STOPPED` | Space was deleted/stopped | Check if it still exists |

Check status programmatically:

```python
info = api.space_info(repo_id)
print(f"Status: {info.runtime}")
print(f"Hardware: {info.hardware}")
print(f"SDK: {info.sdk}")
```

If the Space's status URL isn't available from `space_info`, you can also fetch it from the runtime API:

```python
import requests
resp = requests.get(f"https://huggingface.co/api/spaces/{repo_id}")
data = resp.json()
print(f"Status: {data.get('runtime', {}).get('stage', 'unknown')}")
```

---

## 5. Pause / Restart / Wake Lifecycle Management

Essential for zero-cost monitoring — you must manage the Space lifecycle programmatically:

```python
from huggingface_hub import HfApi
api = HfApi()

# Pause a Space (stops billing for paid tiers, reduces resource usage)
api.pause_space(repo_id)

# Restart a Space (rebuilds container)
api.restart_space(repo_id)

# Request hardware (wakes a sleeping space if CPU is already assigned)
api.request_space_hardware(repo_id, hardware="cpu-basic")
```

**Wake-up detection pattern (sleep → active):**

```python
import time
from huggingface_hub import HfApi

api = HfApi()
repo_id = "username/my-space"

# Trigger a wake by sending a request to the Space
import requests
try:
    requests.get(f"https://{repo_id.replace('/', '-')}.hf.space", timeout=5)
except:
    pass  # Space might be sleeping — that's expected

# Poll until running
for i in range(30):
    info = api.space_info(repo_id)
    stage = getattr(info, 'runtime', '') or ''
    if 'RUNNING' in str(stage):
        print(f"Space is awake after {i*2} seconds")
        break
    time.sleep(2)
```

---

## 6. Monitoring Build Status on Commit (CI Pattern)

When pushing code to a Space repo, you can poll for a successful build:

```python
from huggingface_hub import HfApi
import time

api = HfApi()
repo_id = "username/my-space"
MAX_WAIT = 300  # 5 minutes

for elapsed in range(0, MAX_WAIT, 10):
    info = api.space_info(repo_id)
    stage = str(getattr(info, 'runtime', ''))
    
    if 'BUILD_ERROR' in stage:
        # Read build logs for the error
        logs = list(api.fetch_space_logs(repo_id, build=True))
        raise RuntimeError(f"Build failed:\n{''.join(logs[-50:])}")
    
    if 'RUNNING' in stage or 'RUNNING_BUILDING' in stage:
        print(f"Build succeeded ({elapsed}s)")
        break
    
    time.sleep(10)
else:
    print(f"Build timeout after {MAX_WAIT}s")
```

---

## 7. Environment Variables for Introspection

Every running Space gets built-in environment variables for self-monitoring:

```bash
SPACE_ID=username/my-space          # Full repo ID
SPACE_AUTHOR_NAME=username          # Owner
SPACE_REPO_NAME=my-space            # Repo name
SPACE_HOST=username-my-space.hf.space  # Public hostname
SPACE_TITLE=My Space                # Display title
SPACE_CREATOR_USER_ID=6032...       # Numeric user ID
ACCELERATOR=none                    # 'none' for CPU, 't4-medium' etc.
CPU_CORES=4                         # vCPU count
MEMORY=15Gi                         # RAM
```

Use these inside your app to log context-aware debug info:

```python
import os
print(f"Starting {os.environ.get('SPACE_ID')} on {os.environ.get('ACCELERATOR', 'unknown')}")
```

---

## 8. Dev Mode — Live SSH Debugging (PRO Feature)

**Note: Dev Mode requires a PRO account.** Documented here for completeness but not available on free tier.

```bash
# SSH into a running Space
hf spaces ssh username/my-space

# Auto-enable Dev Mode
hf spaces ssh username/my-space --auto
```

Dev Mode mounts the Space's `/app` directory and lets you:
- Edit code live and restart the app
- Install packages via `pip`
- Run `top`, `htop` for resource monitoring
- Inspect files and directories

Changes are NOT persisted unless you `git add && git commit && git push` from within the container.

---

## 9. Free-Tier Troubleshooting Strategies

Since free accounts don't have Dev Mode or persistent logs, use these workarounds:

### 9a. Self-logging to a Dataset (zero-cost persistence)

```python
import os
import json
from huggingface_hub import HfApi

api = HfApi()
LOG_DATASET = "username/space-logs"  # Create a dataset repo

def log_to_hub(event: str, details: dict = None):
    """Append a log entry to a dataset on the Hub."""
    entry = {
        "space": os.environ.get("SPACE_ID", "unknown"),
        "event": event,
        "details": details or {},
        "timestamp": __import__("datetime").datetime.utcnow().isoformat()
    }
    # Upload as a new line to a shared JSONL file
    api.upload_file(
        path_or_fileobj=json.dumps(entry) + "\n",
        path_in_repo="logs.jsonl",
        repo_id=LOG_DATASET,
        repo_type="dataset",
    )
```

### 9b. Health check endpoint pattern

Embed a health check in your Gradio app:

```python
import gradio as gr

def health_check():
    return {"status": "ok", "accelerator": os.environ.get("ACCELERATOR", "none")}

with gr.Blocks() as demo:
    # ... your app ...
    
    # Hidden health endpoint (accessible via API)
    health_btn = gr.Button("Check Health", visible=False)
    health_output = gr.JSON()
    health_btn.click(fn=health_check, outputs=health_output)

demo.launch()
```

Then call it from an external monitoring script:

```python
from gradio_client import Client
client = Client("username/my-space")
status = client.predict(api_name="/health_check")
```

### 9c. Startup self-check

Add a startup log that writes to a dataset to confirm the build succeeded:

```python
import httpx  # or requests

def notify_startup():
    try:
        httpx.post("https://huggingface.co/api/datasets/username/space-logs", ...)
    except:
        pass  # Don't crash the app if logging fails
```

---

## 10. Key Takeaways

1. **Always check `build=True` logs first for BUILD_ERROR** — runtime logs will be empty
2. **`fetch_space_logs()` is drain-mode by default** — use `follow=True` for tailing
3. **Build logs expire** — grab them immediately on failure
4. **Free-tier Spaces sleep after inactivity (~15-30 min)** — send a request to wake, then poll
5. **No native log retention on free tier** — DIY logging to a dataset is the only zero-cost persistence
6. **`space_info()` for status + `fetch_space_logs()` for content** = complete debugging toolkit
7. **CLI is faster than API for interactive debugging** — `hf spaces logs` with flags
8. **`startup_duration_timeout`** can be configured up to 1h in README.yaml for slow-starting apps
9. **`preload_from_hub`** speeds up startup by downloading models at build time instead of runtime
10. **No GPU during Docker build** — build commands cannot access CUDA hardware
8. **Docs**: Use `https://gradio-docs-mcp.hf.space/gradio_api/mcp/` in any MCP client for instant docs
