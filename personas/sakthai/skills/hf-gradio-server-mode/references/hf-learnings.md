# HF Learnings — Gradio 6 Server Mode (gr.Server) Deep Dive

## 2026-07-25: hf-gradio-server-mode — Gradio 6 Server Mode Complete Reference (Topic #352)

### Summary

Comprehensive deep dive into Gradio 6's `gr.Server` (Server mode) — introduced in Gradio 6.10.0 (PR #13117) and evolving through 6.17.0+ (ZeroGPU support, analytics tracking). Unlike `gr.Blocks()` which creates a full web UI with Gradio frontend, `gr.Server` exposes a **pure FastAPI application** with Gradio's queue engine, SSE streaming, concurrency management, and MCP decorator namespace — but **no Gradio UI components**. It's designed for microservice/API deployments where you want Gradio's infrastructure (queue, streaming, MCP) without the Gradio frontend.

Key insight: `gr.Server` inherits from `gradio.routes.App` which itself inherits from `FastAPI`. This means **all standard FastAPI methods work directly**: `.get()`, `.post()`, `.put()`, `.delete()`, `.add_middleware()`, `.include_router()`, `.mount()`, OpenAPI docs at `/docs`, etc.

### Architecture

```
gr.Server (inherits FastAPI → App → FastAPI)
    │
    ├── @server.api() decorator ───→ Gradio API endpoints
    │     ├── queue=True (default, via Gradio queue)
    │     ├── SSE streaming (stream_every=0.5s)
    │     ├── Concurrency control (limit, id, batch)
    │     └── OpenAPI schema integration
    │
    ├── @server.get(), .post(), etc. ───→ Standard HTTP routes
    │     ├── No Gradio overhead
    │     ├── No queue
    │     └── FastAPI-native
    │
    ├── server.mcp ───→ MCP decorator namespace
    │     ├── server.mcp.tool(name)
    │     ├── server.mcp.resource(uri)
    │     └── server.mcp.prompt(name)
    │
    └── server.launch() ───→ Boot sequence
          ├── Creates internal Blocks (mode="server")
          ├── Registers deferred APIs via gr_api()
          ├── Sets GRADIO_SERVER_MODE_ENABLED=1
          └── Calls blocks.launch(_app=self, ...)
```

**Key Design Decision:** `launch()` creates a hidden `Blocks` context internally with `mode="server"`. This prevents Gradio UI from rendering while still providing the queue, SSE, and event infrastructure. All `@server.api()` decorated functions are deferred until `launch()` is called, then registered via `gradio.events.api()`.

### Complete API Reference

#### Constructor Parameters

`gr.Server()` accepts **all FastAPI constructor parameters** plus no additional required params. Key parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `debug` | `bool` | `False` | Detailed error tracebacks |
| `title` | `str` | `"FastAPI"` | OpenAPI schema title |
| `summary` | `str \| None` | `None` | OpenAPI schema summary |
| `description` | `str` | `""` | Markdown description for OpenAPI |
| `version` | `str` | `"0.1.0"` | API version |
| `openapi_url` | `str \| None` | `"/openapi.json"` | OpenAPI schema URL (None to disable) |
| `docs_url` | `str \| None` | `"/docs"` | Swagger UI URL (None to disable) |
| `redoc_url` | `str \| None` | `"/redoc"` | ReDoc URL (None to disable) |
| `root_path` | `str` | `""` | Path prefix for proxy deployments |
| `separate_input_output_schemas` | `bool` | `True` | Separate schemas in OpenAPI |

#### `@server.api()` Decorator

The primary decorator for registering Gradio API endpoints:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str \| None` | `None` | API endpoint name/route |
| `description` | `str \| None` | `None` | Description for OpenAPI docs |
| `concurrency_limit` | `int \| None \| "default"` | `"default"` | Max concurrent calls (None=unlimited) |
| `concurrency_id` | `str \| None` | `None` | Group ID for shared concurrency limits |
| `queue` | `bool` | `True` | Whether to use Gradio's queue |
| `batch` | `bool` | `False` | Enable batched processing |
| `max_batch_size` | `int` | `4` | Max items per batch |
| `api_visibility` | `"public" \| "private" \| "undocumented"` | `"public"` | API endpoint visibility |
| `time_limit` | `int \| None` | `None` | Max seconds for endpoint execution |
| `stream_every` | `float` | `0.5` | SSE stream update interval (seconds) |

Can be used with or without parentheses:
```python
@app.api
def hello(name: str) -> str: ...

# or
@app.api(name="hello", queue=True)
def hello(name: str) -> str: ...
```

#### `server.mcp` Namespace

Three decorators for marking functions as MCP tools/resources/prompts:

| Decorator | Purpose | Key Parameters |
|-----------|---------|---------------|
| `@server.mcp.tool(name, description)` | Mark function as an MCP tool callable by LLMs | `name` (required), `description` |
| `@server.mcp.resource(uri, name, description, mime_type)` | Expose a static/dynamic resource | `uri` (required), `name` |
| `@server.mcp.prompt(name, description)` | Mark function as an MCP prompt template | `name` (required), `description` |

These are the same as `from gradio import mcp`'s `mcp.tool()`, `mcp.resource()`, `mcp.prompt()`.

#### `server.launch()` Parameters

Inherits most `Blocks.launch()` parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `server_name` | `str \| None` | `None` | Host to bind (default: 127.0.0.1) |
| `server_port` | `int \| None` | `None` | Port to bind (default: 7860) |
| `share` | `bool \| None` | `None` | Create public share link |
| `debug` | `bool` | `False` | Debug mode |
| `max_threads` | `int` | `40` | Max worker threads |
| `auth` | various | `None` | Authentication (callable, tuple, or list) |
| `auth_dependency` | `Callable[[Request], str \| None]` | `None` | FastAPI dependency for auth |
| `ssl_keyfile` / `ssl_certfile` | `str \| None` | `None` | TLS configuration |
| `root_path` | `str \| None` | `None` | Path prefix for reverse proxy |
| `max_file_size` | `str \| int \| None` | `None` | Max upload size ("10mb", etc.) |
| `mcp_server` | `bool \| None` | `None` | Enable MCP server protocol |
| `ssr_mode` | `bool \| None` | `None` | Server-side rendering mode |
| `theme` | various | `None` | Theme configuration |
| `quiet` | `bool` | `False` | Suppress startup messages |

Returns: `(fastapi_app, local_url, share_url)`

### Usage Patterns

#### 1. Basic API Server

```python
from gradio import Server

app = Server(title="My API", version="1.0.0")

@app.api(name="hello")
def hello(name: str) -> str:
    return f"Hello, {name}!"

@app.api(name="add")
def add(a: int, b: int) -> int:
    return a + b

if __name__ == "__main__":
    app.launch(server_port=8000)
    # OpenAPI docs at http://localhost:8000/docs
```

#### 2. Mixed Gradio API + FastAPI Routes

```python
from gradio import Server
from fastapi.responses import JSONResponse

app = Server()

# Gradio endpoint (queued, SSE streaming)
@app.api(name="compute")
def compute(x: float) -> dict:
    return {"result": x ** 2, "sqrt": x ** 0.5}

# Standard FastAPI route (no Gradio overhead)
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

# Standard FastAPI route with path params
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id, "name": f"User {user_id}"}

if __name__ == "__main__":
    app.launch()
```

#### 3. Server with MCP Tools

```python
from gradio import Server

app = Server(title="Calculator MCP Server")

# Both Gradio API + MCP tool (dual-registration)
@app.mcp.tool(name="add")
@app.api(name="add")
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@app.mcp.tool(name="multiply")
@app.api(name="multiply")
def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b

# MCP-only endpoint (no Gradio API)
@app.mcp.tool(name="power")
def power(base: float, exp: float) -> float:
    """Raise base to the power of exp."""
    return base ** exp

if __name__ == "__main__":
    app.launch(mcp_server=True)
```

#### 4. Server with Custom OpenAPI + Auth

```python
from gradio import Server
from fastapi import Request

app = Server(
    title="Private API",
    description="Internal microservice with auth",
    version="2.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
    openapi_url="/openapi.json",
)

@app.api(name="process", concurrency_limit=5)
def process(text: str) -> dict:
    return {"length": len(text), "words": text.split()}

# Auth via dependency
async def verify_token(request: Request) -> str | None:
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token == "my-secret-token":
        return "authenticated"
    return None

if __name__ == "__main__":
    app.launch(auth_dependency=verify_token, server_port=8000)
```

#### 5. Streaming Server (Generator)

```python
from gradio import Server
import time

app = Server()

@app.api(name="count", stream_every=0.25)
def count_to(limit: int):
    """Streams numbers from 1 to limit."""
    for i in range(1, limit + 1):
        yield i
        time.sleep(0.25)

@app.api(name="stream_text")
def stream_text(text: str):
    """Streams text character by character."""
    for char in text:
        yield char
        time.sleep(0.05)

if __name__ == "__main__":
    app.launch()
```

#### 6. Batched Server Endpoint

```python
from gradio import Server

app = Server()

@app.api(name="batch_process", batch=True, max_batch_size=8)
def batch_process(texts: list[str]) -> list[int]:
    """Process multiple texts in a single call."""
    return [len(t) for t in texts]

if __name__ == "__main__":
    app.launch()
```

#### 7. Using Gradio Client from Another App

```python
# In a separate Python process:
from gradio_client import Client

client = Client("http://localhost:7860")

# Predict via Gradio API endpoint
result = client.predict("/hello", {"name": "World"})
print(result)  # "Hello, World!"

# Predict via streaming endpoint
for chunk in client.predict("/count", {"limit": 5}):
    print(chunk)  # 1, 2, 3, 4, 5 (streaming)
```

#### 8. Full Demo (from official gradio repo)

```python
from gradio import Server
from fastapi.responses import HTMLResponse

app = Server()

@app.mcp.tool(name="add")
@app.api(name="add")
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@app.mcp.tool(name="multiply")
@app.api(name="multiply")
def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b

@app.get("/", response_class=HTMLResponse)
async def homepage():
    return """
<!DOCTYPE html>
<html>
<head><title>Calculator</title></head>
<body>
  <h1>Gradio Server Calculator</h1>
  <p>Use /docs for API reference</p>
  <p>Use /add, /multiply as Gradio API endpoints</p>
</body>
</html>"""

if __name__ == "__main__":
    app.launch(mcp_server=True)
```

### Server vs Blocks Comparison

| Dimension | `gr.Server` | `gr.Blocks` |
|-----------|:-----------:|:-----------:|
| **Primary purpose** | API/microservice | Web UI + API |
| **FastAPI inheritance** | Direct (App → FastAPI) | Indirect (wraps FastAPI) |
| **Gradio UI rendering** | ❌ None | ✅ Full UI |
| **Standard HTTP routes** | ✅ `.get()`, `.post()`, etc. | ❌ (use `gr.Request`) |
| **OpenAPI schema** | ✅ Built-in (/docs, /redoc) | ❌ (custom API page) |
| **Gradio queue** | ✅ | ✅ |
| **SSE streaming** | ✅ via `.api()` | ✅ via events |
| **MCP decorators** | ✅ server.mcp.tool() | ✅ via `mcp.tool()` |
| **Component rendering** | ❌ No components | ✅ All components |
| **`gr.render()` support** | ❌ Not designed for it | ✅ |
| **ZeroGPU support** | ✅ (since 6.12.0) | ✅ |
| **Startup time** | Faster (no frontend) | Slower (builds UI) |
| **Deployment** | Ideal for microservices | Ideal for demos/UIs |
| **Multiple routes** | ✅ True routing | ❌ Single-page app |

### MCP Integration Deep Dive

Server mode natively supports three MCP primitives:

**1. Tools** — `@server.mcp.tool(name)`
- Type-annotated Python functions become callable by MCP clients
- Docstrings become tool descriptions
- Parameters become JSON Schema inputs
- Return type annotation determines output schema
- Can be stacked with `@server.api()` for dual Gradio+MCP registration

**2. Resources** — `@server.mcp.resource(uri)`
- Static resources: `@server.mcp.resource("static://config")` returns a fixed value
- Dynamic resources: the decorated function receives the URI parameters
- `mime_type` parameter controls content type

**3. Prompts** — `@server.mcp.prompt(name)`
- Template functions that accept arguments and return prompt messages
- Results are rendered as ChatMessage arrays
- Useful for LLM prompt templates exposed via MCP

**Enabling MCP**: Pass `mcp_server=True` to `launch()`:
```python
app.launch(mcp_server=True)
```

### Gradio Queue Integration

Even without a UI, `@server.api()` endpoints go through Gradio's queue system:

- **Default queue**: Requests are queued and processed sequentially per session
- **Concurrency limits**: Set `concurrency_limit=N` to allow N parallel executions
- **Concurrency IDs**: Group endpoints under the same concurrency ID to share a limit pool
- **Batching**: Enable `batch=True` + `max_batch_size=N` for automatic request batching
- **SSE streaming**: Generator functions stream tokens via Server-Sent Events at `stream_every` intervals
- **Time limits**: `time_limit=N` kills long-running executions after N seconds

The queue is the **same infrastructure** used by `gr.Blocks` — Server mode simply exposes it via a pure API surface.

### Key Insights

1. **True FastAPI inheritance** — `gr.Server` is a proper subclass of FastAPI (via `App` → `FastAPI`). You can use any FastAPI feature: middleware, routers, dependency injection, background tasks, WebSocket, sub-applications, OpenAPI extensions. This is fundamentally different from `gr.Blocks` which only wraps FastAPI.

2. **Deferred API registration** — Functions decorated with `@server.api()` are NOT immediately registered. They're stored in `_deferred_apis` list. Only when `launch()` is called does it create an internal `Blocks(mode="server")` and register everything via `gr_api()`. This means you can define all your endpoints first, then launch.

3. **No Gradio frontend assets** — Server mode doesn't load or serve the Gradio frontend JavaScript/CSS bundle. This makes it significantly lighter and faster to start than `gr.Blocks`. The `_frontend=False` parameter is passed internally.

4. **Dual decorator pattern** — `@server.mcp.tool()` and `@server.api()` can be stacked on the same function. This registers the function as BOTH a Gradio API endpoint (callable via HTTP/gradio-client) AND an MCP tool (callable by LLMs). This is the recommended pattern for maximum flexibility.

5. **OpenAPI documentation** — Since Server mode inherits FastAPI, it automatically gets full OpenAPI 3.1 docs at `/docs` (Swagger UI), `/redoc` (ReDoc), and `/openapi.json`. Gradio API endpoints appear alongside standard FastAPI routes — all with auto-generated schemas from Python type annotations.

6. **Authentication via FastAPI dependencies** — Unlike `gr.Blocks` which has a separate auth system, Server mode supports FastAPI's native `auth_dependency` parameter. This lets you use standard FastAPI patterns: OAuth2, JWT, API keys, session cookies, etc.

7. **GRADIO_SERVER_MODE_ENABLED env var** — After `launch()`, the environment variable `GRADIO_SERVER_MODE_ENABLED` is set to `"1"`. This can be checked by middleware, logging, or health checks to know the server is running in API-only mode.

8. **Use Cases** — Server mode is ideal for:
   - Microservice architecture (replace Flask/FastAPI-only services)
   - ML model serving with Gradio's queue and streaming
   - MCP tool servers for LLM agents
   - Internal APIs that need Gradio's batching/concurrency
   - Hybrid apps (FastAPI routes for CRUD + Gradio routes for ML)

9. **Not for UI apps** — If you need Gradio UI components, use `gr.Blocks` or `gr.Interface`. Server mode cannot render components — it's API-only.

10. **Evolution** — Server mode was introduced in 6.10.0 (PR #13117). Subsequent versions added:
    - 6.12.0: ZeroGPU support, batch processing fixes
    - 6.14.0: Server-specific analytics tracking
    - 6.17.0: Server mode analytics as its own kind (`mode="server"`)
    - 6.10.0: Original MCP decorator namespace

### Source Documentation

- Gradio Docs: https://www.gradio.app/docs/gradio/server
- Source code: `gradio/server.py` in gradio-app/gradio repo
- Guide: "Server Mode" at https://www.gradio.app/guides/server-mode
- Demo: `demo/server_app/` in gradio-app/gradio repo
- PR #13117 (original): https://github.com/gradio-app/gradio/pull/13117

### Key Differences from gr.Blocks

- Server mode does **NOT** create Gradio's frontend HTML
- Server mode exposes **every** standard FastAPI method directly on the instance
- Server mode uses **decorator-based API registration** (`@server.api()`) instead of event listeners
- Server mode has **no component rendering** — it's purely an API engine
- Server mode's `launch()` creates an **internal, hidden Blocks** context that's never rendered
- Server mode is **lighter** — no frontend assets loaded
