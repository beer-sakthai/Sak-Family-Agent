---
name: sakthai-hf-gradio
description: "Gradio: the Python library for building interactive UIs behind Hugging Face Spaces — Interface, Blocks, session state, event chaining, theming, MCP servers, and deployment patterns for Gradio 6."
version: 2.0.0
author: SakThai
license: MIT
tags: [huggingface, gradio, spaces, ui, interface, blocks, demo, mcp, gradio6]
platforms: [linux, macos, windows]
---

# Gradio for Hugging Face Spaces

Gradio is the Python library that powers most Hugging Face Spaces demos. It lets you wrap a Python function (model inference, data processing, etc.) into a shareable web UI with minimal code, then deploy it to HF Spaces or run it locally.

> **Version note:** Gradio 6.x is the current stable line (released November 2025). Gradio 5.x is maintenance-only. For a full migration checklist, see [references/gradio-6-migration.md](references/gradio-6-migration.md).

## Interface vs Blocks

### Interface (`gr.Interface`)
The high-level API for simple demos. You declare inputs, outputs, and the function, and Gradio builds the UI automatically.

```python
import gradio as gr

def greet(name):
    return f"Hello {name}!"

demo = gr.Interface(fn=greet, inputs="text", outputs="text")
demo.launch()
```

**Key features:**
- `examples` — pre-filled inputs in the UI for quick testing.
- `article` / `description` — markdown text rendered above/below the demo.
- `css` / `theme` — in Gradio 6, pass these to `demo.launch()` (see Theming below).

### Blocks (`gr.Blocks`)
The low-level API for arbitrary layouts and workflows. Everything is a component, and you wire events manually.

```python
with gr.Blocks() as demo:
    gr.Markdown("# My App")
    name = gr.Textbox(label="Name")
    out = gr.Textbox(label="Greeting")
    btn = gr.Button("Go")
    btn.click(fn=greet, inputs=name, outputs=out)

demo.launch()
```

**When to use Blocks:**
- Multiple steps in one UI (upload → process → download).
- Conditional visibility / tabbed interfaces.
- Custom layouts with Rows / Columns / Tabs / Accordions.
- Chaining events (one click triggers loading, then inference, then plot update).

**Gradio 6 change:** App-level parameters such as `theme`, `css`, `css_paths`, `js`, `head`, and `head_paths` now belong in `demo.launch()`, not in `gr.Blocks()`.

## Core Components

| Component | Typical use |
|-----------|-------------|
| `Textbox` | Text input/output, supports `lines`, `max_lines`, `placeholder`. |
| `Dataframe` | Tabular data; use `row_count` + `row_limits` and `column_count` + `column_limits`. |
| `Image` | Upload or display images; `type="numpy"` returns arrays. |
| `Audio` | Upload/record audio; returns numpy arrays or file paths. |
| `Video` | Upload video; returns file paths or `gr.Video(value=..., subtitles=...)` instances. |
| `File` | Generic file upload; returns temp paths. |
| `Dropdown` | Single/multi-select; accepts `choices`. |
| `CheckboxGroup` / `Radio` | Mutually exclusive multi-choice. |
| `Slider` | Numeric input with min/max/step. |
| `Model3D` | Display .obj / .glb 3D files. |
| `Chatbot` | Chat history. **Gradio 6 only supports `type="messages"`** with dicts `{"role":"user","content":[...]}`. |
| `ChatInterface` | High-level chatbot wrapper; same messages format required. |

## State Management

### `gr.State()`
Holds intermediate data across function calls without rendering a visible UI element.

```python
history = gr.State([])

def respond(message, chat_history):
    bot_msg = "Echo: " + message
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": bot_msg})
    return "", chat_history
```

**Gradio 6 change:** Use structured message dicts, not tuples.

### Session-level state
- Each user session gets its own **independent** state when the app is running locally (`demo.launch()`) or when the Space is not using queuing.
- When `demo.queue()` is enabled, all users share the **same** queue but state is still per-session unless you explicitly use a global variable.
- **Caution:** Global Python variables are shared across all users in a Space. Prefer `gr.State()` or session-scoped storage.

## Events and Queuing

### Event chaining
Events can trigger other events via `.then()`:

```python
load_btn.click(load_model, inputs=[], outputs=[status]).then(
    fn=generate, inputs=[prompt], outputs=[output]
)
```

**Gradio 6 change:** Event listeners no longer accept `show_api`. Use `api_visibility="public"`, `"undocumented"`, or `"private"`.

### Queuing
```python
demo.queue()  # handles long-running tasks, shows progress bar
demo.launch()
```

- `demo.queue()` is required for long-running functions in HF Spaces to avoid 502/504 timeouts.
- Settings: `default_concurrency_limit`, `api_open`, `max_threads` via `gr.Blocks(queue=...)`.

## Theming and Styling

**Gradio 6:** Pass theme, CSS, and JS to `launch()`, not to `gr.Blocks()`.

```python
demo.launch(
    theme=gr.themes.Soft(),
    css=".gr-button { background: orange; }",
    js="console.log('hello');"
)
```

Built-in themes: `Default`, `Soft`, `Glass`, `Monochrome`, `Origin`.

> **Note:** HF Spaces running the Gradio stack use the `gradio` package version bundled in the image. You can pin versions in `requirements.txt`.

## Server-side rendering (SSR)

- SSR is enabled by default on Hugging Face Spaces.
- Disable with `GRADIO_SSR=False` for debugging.
- SSR significantly improves initial page load time.
- See [references/ssr-and-env-vars.md](references/ssr-and-env-vars.md) for env vars.

## MCP (Model Context Protocol) integration

Gradio apps can act as **MCP servers**, letting LLM agents call your demo tools directly.

```python
demo.launch(mcp_server=True)
```

- The app exposes functions as MCP tools automatically.
- Clients can connect to the running Gradio MCP server from external agent frameworks.
- File-upload MCP patterns are documented in the Gradio guides.

## Deployment to HF Spaces

### Minimal `app.py`
```python
# app.py
import gradio as gr

demo = gr.Interface(...)
demo.launch()
```

### `requirements.txt`
```text
gradio>=6.0,<7.0
# torch>=2.0  # uncomment if your app needs PyTorch
```

### Hardware
- **CPU only** — small models / demos.
- **GPU (T4/A10G)** — recommended for LLMs / diffusion.
- **ZeroGPU** — dynamic allocation; add `space: hardware: zero-gpu` in `README.md` metadata if you need it.
- **RAM upgrade** — 16/32 GB for large tokenizers or preprocessing.

### README.md metadata (YAML frontmatter)
```yaml
---
title: My Demo
emoji: 🤖
sdk: gradio
sdk_version: 6.19.0
app_file: app.py
pinned: false
---
```

- `sdk_version` lets you pin the Gradio runtime.
- `pinned: true` keeps the Space at the top of your profile.

### CI and Rebuilds

- HF Spaces auto-rebuilds on every push to the repo.
- `huggingface_hub` Python SDK can create or update Spaces programmatically:
  - `create_repo()`, `upload_file()`, `upload_folder()`.
- Build logs appear under the Space's **Files and versions** tab.

## Chat migration (Gradio 5 → 6)

**Old tuple format (removed):**
```python
chatbot = gr.Chatbot(value=[["Hello", "Hi!"]])
```

**New messages format:**
```python
chatbot = gr.Chatbot(
    value=[
        {"role": "user", "content": [{"type": "text", "text": "Hello"}]},
        {"role": "assistant", "content": [{"type": "text", "text": "Hi!"}]},
    ],
    type="messages",
)
```

- `allow_tags=True` is now the default for `gr.Chatbot` (was `False`).
- `like_user_message` is set on the `gr.Chatbot` constructor, not on `.like()`.

## Key Facts

- Gradio 6.x is the current stable line (first released November 2025).
- Gradio is built on **FastAPI + websockets**; this improves streaming and concurrency.
- `gr.Chatbot` supports streaming updates via generator-style functions or by yielding partial outputs in `queue()`.
- `demo.load()` runs on page load — useful for pre-warming models.
- `demo.invalidate()` clears cached static assets during development.
- HF Spaces' free tier enforces CPU limits; GPU/ZeroGPU require hardware selection in the Space settings or `README.md` metadata.

## Common Patterns

### Streaming text generation
```python
def stream(prompt):
    for word in model.generate(prompt):
        yield word
```

### File download from temporary path
```python
def process(file):
    # file is a temp path; return another temp path
    return "output.zip"
```

### Multiple tabs
```python
with gr.Blocks() as demo:
    with gr.Tab("Tab 1"):
        gr.Interface(...)
    with gr.Tab("Tab 2"):
        gr.Interface(...)
```

## Common Pitfalls

- Do **not** pin Gradio 5 if you need new features; Gradio 6 is the only maintained line.
- Do **not** pass `theme`, `css`, or `js` to `gr.Blocks()` in Gradio 6 — move them to `demo.launch()`.
- Do **not** use tuple chat format; migrate to `{"role":...}` before upgrading.
- `show_api=False` is invalid in Gradio 6 event listeners; use `api_visibility`.
- `cache_examples="lazy"` is invalid; split into `cache_examples=True` + `cache_mode="lazy"`.
- `gr.HTML` padding default is now `False`; explicitly set it if layout breaks.

## Calling any Gradio Space as an API

Every public Gradio Space on Hugging Face is an auto-generated REST API. You do not need to own the Space to invoke it.

**Python (`gradio_client`)**

```python
from gradio_client import Client, handle_file

client = Client("username/space-name", token="hf_...")
result = client.predict("input text", api_name="/predict")

# Files from URL or local path
result = client.predict(audio=handle_file("https://example.com/audio.wav"), api_name="/predict")

# Streaming / generator endpoints
for output in client.submit("prompt", api_name="/generate"):
    print(output)
```

**JavaScript (`@gradio/client`)**

```javascript
import { Client } from "@gradio/client";
const app = await Client.connect("username/space", { token: "hf_..." });
const result = await app.predict("/predict", ["Hello"]);
```

**REST / curl (queue-based two-step)**

```bash
# 1. Submit request
curl -X POST "https://space.hf.space/gradio_api/call/predict" \
  -H "Content-Type: application/json" \
  -d '{"data": ["Hello"]}'
# {"event_id": "abc123"}

# 2. Poll for result (SSE)
curl -N "https://space.hf.space/gradio_api/call/predict/abc123"
```

**OpenAPI schema**  
Every Space exposes: `https://<space-subdomain>.hf.space/gradio_api/openapi.json`

**Calling a Space from another Space**  
Forward `x-ip-token` to preserve auth and quota ownership:

```python
def process(prompt, request: gr.Request):
    x_ip_token = request.headers.get("x-ip-token", "")
    client = Client("owner/zerogpu-space", headers={"x-ip-token": x_ip_token})
    return client.predict(prompt, api_name="/predict")
```

**ZeroGPU quotas**

| Account type | Daily GPU quota | Overage |
|--------------|-----------------|---------|
| Unauthenticated | 2 min | shared pool |
| Free | 5 min | $1 / 10 min |
| PRO | 40 min | $1 / 10 min |

Authenticated calls consume the **owner's** quota.

## References

- Docs: https://www.gradio.app/docs
- Guides: https://www.gradio.app/guides
- HF Spaces docs: https://huggingface.co/docs/hub/spaces
- Gradio 6 Migration Guide: https://gradio.app/main/guides/gradio-6-migration-guide
- Detailed migration notes: [references/gradio-6-migration.md](references/gradio-6-migration.md)
- SSR & env vars: [references/ssr-and-env-vars.md](references/ssr-and-env-vars.md)
- Minimal starter template: [templates/space-app.py](templates/space-app.py)
- Requirements template: [templates/space-requirements.txt](templates/space-requirements.txt)
- Space API invocation patterns: [references/space-api-invocation.md](references/space-api-invocation.md)
