---
name: SakThai-gradio-spaces
author: SakThai
license: MIT
description: "Gradio for Hugging Face Spaces — Blocks architecture, event handling, queue management, authentication, theming, ChatInterface, state management, file handling, progress indicators, and the Gradio client libraries (JS + Python). Covers Gradio 5+ features."
version: 1.0.0
tags: [huggingface, spaces, gradio, sdk, ui, demos, blocks, chatinterface]
platforms: [linux, macos, windows]
related_skills: [hf-spaces-docker, spaces-zerogpu, huggingface-hub]
---

# Gradio for Hugging Face Spaces — Advanced Patterns

Gradio is the primary SDK for Hugging Face Spaces — it lets you build ML demos, chatbots, and custom web UIs entirely in Python, with no JS/HTML required.

> **Zero-cost first:** Gradio Spaces on CPU hardware are free-to-create on HF Spaces. ZeroGPU provides free GPU via the `@spaces.GPU` decorator (see `spaces-zerogpu` skill).

---

## Architecture: Three APIs

### 1. `gr.Interface` — Quick demos, single function

Best for: simple input → output ML demos (classification, text generation, image transformation).

```python
import gradio as gr

def greet(name, intensity):
    return f"Hello {name}! " * intensity

demo = gr.Interface(
    fn=greet,
    inputs=[gr.Textbox(label="Name"), gr.Slider(1, 5, value=2)],
    outputs=gr.Textbox(label="Greeting"),
    title="Greeter",
    description="A simple greeter demo.",
)
demo.launch()
```

**Key params:** `fn`, `inputs`, `outputs`, `title`, `description`, `article`, `theme`, `allow_flagging`, `examples`, `cache_examples`.

### 2. `gr.Blocks` — Full control over layout & data flow

Best for: multi-step workflows, dashboards, complex interactions, custom layouts.

```python
import gradio as gr

with gr.Blocks(title="My App", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# My Custom App")
    with gr.Row():
        with gr.Column(scale=1):
            name = gr.Textbox(label="Name")
            age = gr.Slider(1, 100, label="Age")
            greet_btn = gr.Button("Submit")
        with gr.Column(scale=2):
            output = gr.Textbox(label="Output")

    greet_btn.click(fn=lambda n, a: f"Hello {n}, age {a}!",
                    inputs=[name, age], outputs=output)
```

**Layout components:** `gr.Row`, `gr.Column`, `gr.Tab`, `gr.Accordion`, `gr.Group`, `gr.Sidebar`, `gr.Navbar`, `render()`.

### 3. `gr.ChatInterface` — Chatbots in 3 lines

Best for: LLM chatbots, conversational agents, Q&A bots.

```python
import gradio as gr

def respond(message, history):
    return f"You said: {message}"

demo = gr.ChatInterface(
    fn=respond,
    title="Chatbot",
    description="A simple chatbot.",
    theme=gr.themes.Soft(),
)
demo.launch()
```

**Key features:** Built-in streaming, multimodal support, retry/undo/regenerate buttons, chatbot state management.

---

## Event Handling in Blocks

### Event Types

| Event | Description |
|---|---|
| `.click()` | Button/component click |
| `.submit()` | Form submission (Enter key in Textbox) |
| `.change()` | Value changes in any input |
| `.select()` | User selects an option/choice |
| `.key_up()` | Keyboard key press |
| `.upload()` | File upload event |
| `.play()` / `.pause()` | Audio/Video playback |

### Chaining events

```python
# Single input → multiple outputs
btn.click(fn=process, inputs=[text], outputs=[result1, result2])

# Multiple events on same component
textbox.change(fn=on_change, inputs=textbox, outputs=status) \
       .submit(fn=on_submit, inputs=textbox, outputs=output)
```

### Event Data

Access event metadata (e.g., selected index, file info):

```python
def on_select(ev_data: gr.SelectData):
    return f"You selected index {ev_data.index}"

dropdown.select(fn=on_select, outputs=output)
```

Available event data helpers: `gr.EventData`, `gr.SelectData`, `gr.LikeData`, `gr.KeyUpData`, `gr.FileData`, `gr.DeletedFileData`, `gr.RetryData`, `gr.UndoData`, `gr.EditData`, `gr.DownloadData`, `gr.CopyData`.

### Timer Events

Run functions on a schedule within the UI:

```python
timer = gr.Timer(value=5)  # fire every 5 seconds
timer.tick(fn=refresh_data, outputs=status_display)
```

---

## State Management

### `gr.State` — Per-session state

In Blocks, use `gr.State()` for user-specific data that persists across interactions within a session:

```python
with gr.Blocks() as demo:
    counter = gr.State(0)
    btn = gr.Button("Count")
    output = gr.Number(label="Count")

    btn.click(
        fn=lambda x: (x + 1, x + 1),
        inputs=counter,
        outputs=[counter, output]
    )
```

State is Python-serializable (dicts, lists, objects). Each user session gets its own state instance.

### `gr.BrowserState` — Persisted across sessions

Stored in the browser's localStorage:

```python
with gr.Blocks() as demo:
    theme_choice = gr.BrowserState("light")
    # survives page reloads within the same browser
```

---

## Queue Management

Essential for Spaces handling concurrent users:

```python
demo = gr.Interface(...)
demo.queue(default_concurrency=5, max_size=10)
demo.launch()
```

**Parameters:**
- `default_concurrency` — Max parallel function executions (default: 1)
- `max_size` — Max queued requests before rejection
- `status_update_rate` — How often to send queue position updates

Without `.queue()`, only one user can use the app at a time — all others get "too many requests" errors.

### Progress Bar

```python
import gradio as gr
import time

def long_task(progress=gr.Progress()):
    for i in progress.tqdm(range(100)):
        time.sleep(0.1)
    return "Done!"
```

Use `gr.Progress(track_tqdm=True)` to auto-track tqdm progress bars.

---

## Authentication in HF Spaces

### Built-in Authentication

Set the `auth` parameter in `launch()`:

```python
demo = gr.Interface(fn=greet, inputs="textbox", outputs="textbox")
demo.launch(auth=[("admin", "password123"), ("user", "pass456")])
```

### OAuth / HF Login Button

```python
import gradio as gr

with gr.Blocks() as demo:
    login_btn = gr.LoginButton()
    gr.Markdown("## Welcome! Please log in.")
```

The `gr.LoginButton()` component integrates with Hugging Face's OAuth. When a user logs in, you can access their HF profile information via `gr.Request`:

```python
def greet(request: gr.Request):
    return f"Hello {request.username}!"

gr.Interface(fn=greet, inputs=None, outputs="textbox").launch()
```

### Spaces Auth (HF_PROXY_AUTH)

When deployed on HF Spaces, authentication is handled by the Spaces platform. Access user info:

```python
from huggingface_hub import whoami
import os

# HF_TOKEN is injected automatically by Spaces
user_info = whoami(token=os.environ.get("HF_TOKEN"))
```

---

## Theming

### Built-in Themes

```python
with gr.Blocks(theme=gr.themes.Soft()) as demo: ...
with gr.Blocks(theme=gr.themes.Monochrome()) as demo: ...
with gr.Blocks(theme=gr.themes.Default()) as demo: ...
with gr.Blocks(theme=gr.themes.Glass()) as demo: ...
```

### Custom Theme (Gradio 5+)

```python
from gradio.themes import Theme

custom_theme = Theme(
    primary_hue="blue",
    secondary_hue="purple",
    neutral_hue="gray",
    font=("Source Sans Pro", "sans-serif"),
)

with gr.Blocks(theme=custom_theme) as demo:
    ...
```

### Custom CSS

```python
with gr.Blocks(css=".my-class { color: red !important; }") as demo:
    gr.HTML('<p class="my-class">Styled text</p>')
```

Or load from a file:

```python
with gr.Blocks(css="style.css") as demo:
    ...
```

---

## File Handling

### Upload & Download

```python
import gradio as gr

def process_file(file):
    # file is a temp file path (string)
    with open(file.name, "r") as f:
        content = f.read()
    return content

with gr.Blocks() as demo:
    file_input = gr.File(label="Upload a file")
    file_output = gr.File(label="Download result")
    btn = gr.Button("Process")

    def process(file):
        content = process_file(file)
        output_path = "/tmp/result.txt"
        with open(output_path, "w") as f:
            f.write(content)
        return output_path

    btn.click(process, inputs=file_input, outputs=file_output)
```

### `gr.UploadButton` — Custom upload button

```python
upload_btn = gr.UploadButton("Upload Image", file_types=["image"])
upload_btn.upload(fn=process_image, inputs=upload_btn, outputs=image_output)
```

### `gr.DownloadButton` (Gradio 5+)

```python
download_btn = gr.DownloadButton("Download", value="/path/to/file")
```

### `gr.FileExplorer` — Browse server files

```python
file_browser = gr.FileExplorer(root_dir="/data", glob="**/*.csv")
```

### Multimodal Textbox

For chat interfaces that accept text + files:

```python
chat_input = gr.MultimodalTextbox(
    placeholder="Type a message...",
    file_count="multiple",
    file_types=["image", "text", "pdf"],
)
```

---

## Gradio Client — Programmatic Access

### Python Client

```python
from gradio_client import Client

client = Client("user/space-name")
result = client.predict(
    name="Alice",
    api_name="/predict"
)
```

**Key methods:**
- `client.predict(endpoint, **inputs)` — one-shot prediction
- `client.submit(endpoint, **inputs)` — iterator with status updates (queue position, progress)
- `client.view_api()` — inspect available endpoints and their schemas
- `client.duplicate(source, token, private, hardware, timeout)` — duplicate a Space

### JavaScript/TypeScript Client

```javascript
import { Client } from "@gradio/client";

const app = await Client.connect("user/space-name");
const result = await app.predict("/predict", { name: "Alice" });
```

### File upload via `handle_file()`

```python
from gradio_client import Client, handle_file

client = Client("user/space-name")
result = client.predict(
    image=handle_file("path/to/image.png"),
    api_name="/predict"
)
```

Supports: local file paths, URLs, Blobs, Buffers.

---

## Gradio-Specific Patterns for HF Spaces

### 1. Environment Variables in Spaces

```python
import os

HF_TOKEN = os.environ.get("HF_TOKEN")
SPACE_ID = os.environ.get("SPACE_ID")  # "username/space-name"
SPACE_HOST = os.environ.get("SPACE_HOST")
```

### 2. ZeroGPU Integration

```python
import spaces
from gradio import Interface

@spaces.GPU
def generate(prompt):
    # runs on free GPU
    return model.generate(prompt)

demo = Interface(fn=generate, inputs="text", outputs="text")
demo.queue()
demo.launch()
```

### 3. Caching Results

```python
@gr.Cache()  # Gradio 5+
def expensive_function(input_text):
    return model.predict(input_text)
```

Models are cached by input — subsequent identical calls return instantly.

### 4. Static File Serving

```python
from gradio import set_static_paths
set_static_paths(["/data/assets"])
```

### 5. Mounting Gradio in FastAPI

```python
from fastapi import FastAPI
import gradio as gr

app = FastAPI()
demo = gr.Interface(fn=greet, inputs="textbox", outputs="textbox")

app = gr.mount_gradio_app(app, demo, path="/gradio")
```

### 6. Request Object

```python
from gradio import Request

def greet(request: Request):
    return f"Hello {request.client.host}!"

gr.Interface(fn=greet, inputs=None, outputs="textbox").launch()
```

---

## Common Pitfalls

1. **Missing `.queue()`** — Without queue, concurrent users get "too many requests." Always call `demo.queue()` for Spaces.
2. **`/data` persistence** — Data written to disk disappears on restart. Use Storage Buckets or the Hub API.
3. **Gradio version mismatch** — HF Spaces defaults may lag behind latest gradio. Specify `gradio==X.Y.Z` in requirements.txt.
4. **Event handler registration order** — Event handlers (`click`, `change`) must be registered AFTER the components they reference.
5. **State serialization** — `gr.State` must be serializable (no DB connections, file handles, model instances).
6. **Blocking main thread** — Long-running tasks block the UI. Use `demo.queue()` + async functions for non-blocking behavior.

---

## Deployment Checklist for HF Spaces

- [ ] `app.py` with `demo.queue()` and `demo.launch()`
- [ ] `requirements.txt` with gradio and dependencies pinned
- [ ] `README.md` with YAML frontmatter (`sdk: gradio`)
- [ ] `.queue()` enabled for concurrent users
- [ ] Cache-busting via Gradio's `@gr.Cache()` where applicable
- [ ] Secrets stored in Space Settings (not hardcoded)
- [ ] Public variables set in Space Settings if needed
- [ ] Hardware configured (CPU basic free, ZeroGPU for GPU)

---

## Related Resources

- [Gradio Docs](https://www.gradio.app/docs/gradio/blocks)
- [HF Spaces Gradio SDK Docs](https://huggingface.co/docs/hub/en/spaces-sdks-gradio)
- [Gradio on GitHub](https://github.com/gradio-app/gradio)
- [Grading Blocks Guide](https://www.gradio.app/guides/blocks-and-event-listeners)
- [Gradio Themes](https://www.gradio.app/guides/themes-guide)
- [Gradio Python Client](https://www.gradio.app/docs/python-client/introduction)
- [Gradio JS Client](https://www.gradio.app/docs/js-client)
- **Documentation sources:** Load `references/gradio-doc-sources.md` — raw URLs, version info, research fallbacks when web search fails.
- **Cross-topic learnings:** Load `references/hf-learnings.md` under `mlops/huggingface-hub` — cumulative HF insights from daily sessions.
