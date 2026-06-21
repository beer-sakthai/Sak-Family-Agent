---
name: hf-gradio
description: "Gradio: the Python library for building interactive UIs behind Hugging Face Spaces — Interface, Blocks, session state, event chaining, theming, and deployment patterns."
version: 1.0.0
author: SakThai
license: MIT
tags: [huggingface, gradio, spaces, ui, interface, blocks, demo]
platforms: [linux, macos, windows]
---

# Gradio for Hugging Face Spaces

Gradio is the Python library that powers most Hugging Face Spaces demos. It lets you wrap a Python function (model inference, data processing, etc.) into a shareable web UI with minimal code, then deploy it to HF Spaces or run it locally.

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
- `css` / `theme` — quick styling without touching Blocks.

### Blocks (`gr.Blocks`)
The low-level API for arbitrary layouts and workflows. Everything is a component, and you wire events manually.

```python
with gr.Blocks() as demo:
    name = gr.Textbox(label="Name")
    out = gr.Textbox(label="Greeting")
    btn = gr.Button("Greet")
    btn.click(fn=greet, inputs=name, outputs=out)

demo.launch()
```

**When to use Blocks:**
- Multiple steps in one UI (upload → process → download).
- Conditional visibility / tabbed interfaces.
- Custom layouts with Rows / Columns / Tabs / Accordions.
- Chaining events (one click triggers loading, then inference, then plot update).

## Core Components

| Component | Typical use |
|-----------|-------------|
| `Textbox` | Text input/output, supports `lines`, `max_lines`, `placeholder`. |
| `Dataframe` | Tabular data; supports editable, selected cells. |
| `Image` | Upload or display images; `type="numpy"` returns arrays. |
| `Audio` | Upload/record audio; returns numpy arrays or file paths. |
| `Video` | Upload video; returns file paths. |
| `File` | Generic file upload; returns temp paths. |
| `Dropdown` | Single/multi-select; accepts `choices`. |
| `CheckboxGroup` / `Radio` | Mutually exclusive multi-choice. |
| `Slider` | Numeric input with min/max/step. |
| `Model3D` | Display .obj / .glb 3D files. |
| `Chatbot` | Chat history list of `[user_msg, bot_msg]` pairs. |

## State Management

### `gr.State()`
Holds intermediate data across function calls without rendering a visible UI element.

```python
history = gr.State([])

def respond(message, chat_history):
    bot_msg = "Echo: " + message
    chat_history.append((message, bot_msg))
    return "", chat_history
```

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

### Queuing
```python
demo.queue()  # handles long-running tasks, shows progress bar
demo.launch()
```

- `demo.queue()` is required for long-running functions in HF Spaces to avoid 502/504 timeouts.
- Settings: `default_concurrency_limit`, `api_open`, `max_threads` via `gr.Blocks(queue=...)`.

## Theming and Styling

```python
demo = gr.Blocks(theme=gr.themes.Soft())
```

Built-in themes: `Default`, `Soft`, `Glass`, `Monochrome`, `Origin`.

Custom CSS:
```python
demo = gr.Blocks(css=".gr-button { background: orange; }")
```

> **Note:** HF Spaces running on the new Gradio 4+ stack use the `gradio` package version bundled in the image. You can pin versions in `requirements.txt`.

## Deployment to HF Spaces

### Minimal `app.py`
```python
# app.py
import gradio as gr

demo = gr.Interface(...)
demo.launch()
```

### `requirements.txt`
```
gradio==4.44.0
torch==2.4.0
transformers==4.44.0
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
sdk_version: 4.44.0
app_file: app.py
pinned: false
---
```

- `sdk_version` lets you pin the Gradio runtime.
- `pinned: true` keeps the Space at the top of your profile.

## CI and Rebuilds

- HF Spaces auto-rebuilds on every push to the repo.
- `huggingface_hub` Python SDK can create or update Spaces programmatically:
  - `create_repo()`, `upload_file()`, `upload_folder()`.
- Build logs appear under the Space's **Files and versions** tab.

## Key Facts

- Gradio 4.x uses **FastAPI + websockets** under the hood rather than Flask; this improves streaming and concurrency.
- The `gr.Chatbot` component supports streaming updates via `generator`-style functions or by yielding partial outputs in `queue()`.
- `demo.load()` runs on page load — useful for pre-warming models.
- `demo.invalidate()` clears cached static assets during development.
- HF Spaces' free tier enforces CPU limits; GPU/ZeroGPU require hardware selection in the Space settings or `README.md` metadata.
- Lite models (`gr.Lite`) and mobile-optimized UIs are emerging but not yet stable.

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

## References

- Docs: https://www.gradio.app/docs
- Guides: https://www.gradio.app/guides
- HF Spaces docs: https://huggingface.co/docs/hub/spaces
- Blocks docs: https://www.gradio.app/docs/gradio/blocks