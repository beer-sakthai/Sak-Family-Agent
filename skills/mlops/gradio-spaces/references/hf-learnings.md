# HF Learnings — Gradio Lite: Serverless Gradio in the Browser with Pyodide/WebAssembly

**Topic:** `hf-gradio-lite`
**Date:** 2026-07-24
**Skill:** mlops/gradio-spaces
**Author:** SakThai
**License:** MIT

## Overview

Deep-dive into Gradio Lite (`@gradio/lite` v5.45.0) — the JavaScript library that runs Gradio apps entirely in the browser via Pyodide (Python compiled to WebAssembly). No server, no backend, no Docker — pure client-side Gradio.

## Source
- npm: `@gradio/lite` v5.45.0 — https://www.npmjs.com/package/@gradio/lite
- CDN: https://cdn.jsdelivr.net/npm/@gradio/lite/dist/lite.js + lite.css
- Pyodide: https://pyodide.org/en/stable/
- HF Static Spaces: https://huggingface.co/docs/hub/en/spaces-overview
- Playground: https://www.gradio.app/playground

## Architecture

```
Browser
├── HTML with <gradio-lite> custom element
├── Pyodide runtime (WebAssembly, ~8-15 MB)
│   ├── CPython interpreter compiled to WASM
│   ├── gradio + pre-loaded packages
│   └── user Python code (from <gradio-lite> or <gradio-file> tags)
└── ONNX Runtime Web (for transformers-js)
```

Pyodide uses Emscripten to compile CPython to WebAssembly, allowing Python bytecode to execute in the browser's JavaScript engine. Gradio Lite wraps this into a custom HTML element (`<gradio-lite>`) that bootstraps the runtime and renders the Gradio UI.

## CDN Setup — Minimal Example

Single-file Gradio app in one HTML page:

```html
<html>
  <head>
    <script type="module" crossorigin src="https://cdn.jsdelivr.net/npm/@gradio/lite/dist/lite.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@gradio/lite/dist/lite.css" />
  </head>
  <body>
    <gradio-lite>
import gradio as gr

def greet(name):
    return "Hello, " + name + "!"

gr.Interface(greet, "textbox", "textbox").launch()
    </gradio-lite>
  </body>
</html>
```

Open the HTML file directly — no web server, no install, no backend.

## Multi-File Projects with `<gradio-file>`

Split app code across multiple Python files, each in its own `<gradio-file>` tag. One must be marked `entrypoint`:

```html
<gradio-lite>

<gradio-file name="app.py" entrypoint>
import gradio as gr
from utils import add

demo = gr.Interface(fn=add, inputs=["number", "number"], outputs="number")
demo.launch()
</gradio-file>

<gradio-file name="utils.py">
def add(a, b):
    return a + b
</gradio-file>

</gradio-lite>
```

Files are importable via standard Python import — `<gradio-file name="utils.py">` creates a `utils` module that `app.py` can import.

## Dependency Management

Additional packages install via `<gradio-requirements>`, which wraps Pyodide's `micropip`:

```html
<gradio-lite>

<gradio-requirements>
transformers_js_py
numpy
scikit-learn
</gradio-requirements>

<gradio-file name="app.py" entrypoint>
from transformers_js import import_transformers_js
import gradio as gr

transformers = await import_transformers_js()
pipe = await transformers.pipeline('sentiment-analysis')

async def classify(text):
    return await pipe(text)

gr.Interface(classify, "textbox", "json").launch()
</gradio-file>

</gradio-lite>
```

### Known Compatible Packages
- `gradio` (pre-installed)
- `numpy`, `scikit-learn`, `matplotlib`, `Pillow`
- `transformers_js_py` (ONNX Runtime Web-based models)
- Pure-Python packages on Pyodide's index

Check https://pyodide.org/en/stable/usage/packages-in-pyodide.html for the full list.

## Hugging Face Static Spaces — Free Hosting

**Static Spaces** are the recommended deployment target for Gradio Lite apps. They serve static HTML/JS/CSS with no server-side compute — making them **completely free forever**.

**How to deploy:**
1. Go to https://huggingface.co/new-space
2. Pick "Static HTML" as the Space SDK
3. Upload your `index.html` (and any assets)
4. Your app is live at `https://huggingface.co/spaces/YOUR_USER/SPACE_NAME`

**Zero-cost architecture:** No CPU, no GPU, no Docker, no cold-boot — just a CDN serving your HTML. The Pyodide runtime and model run in the visitor's browser.

Live demo: https://huggingface.co/spaces/abidlabs/gradio-lite-classify

## Theming

```html
<gradio-lite theme="dark">
  <!-- Python code -->
</gradio-lite>

<gradio-lite theme="light">
  <!-- Python code -->
</gradio-lite>
```

Default respects `prefers-color-scheme` (system theme).

## Key Benefits for Zero-Cost Use

| Benefit | Why It Matters for Beer |
|---------|------------------------|
| **Serverless** | No GPU/CPU compute bills — zero infrastructure cost |
| **Static Spaces** | Free hosting on HF, scales to any number of visitors |
| **Privacy** | User data stays in-browser — no server-side compliance needed |
| **Simple Deploy** | Upload a single HTML file — no CI/CD, no Docker |
| **Offline-capable** | After initial load, can work without internet |

## Limitations

1. **Cold start**: 5-15 seconds initial load while Pyodide downloads (~8-15 MB)
2. **Package compatibility**: Only Pyodide's wheel index works (no arbitrary pip installs)
3. **No GPU**: WebAssembly can't access CUDA, DirectML, or Metal — CPU-only
4. **Browser memory ceiling**: ~2 GB per tab; large models will crash
5. **Single-threaded Python**: GIL + main thread; async I/O only, no parallelism
6. **No persistent filesystem**: Pyodide's MEMFS is in-memory and resets on refresh

## Browser ML with transformers-js

`transformers_js_py` wraps Hugging Face's Transformers.js (ONNX Runtime Web) for in-browser ML:

Supported pipelines: `sentiment-analysis`, `text-classification`, `zero-shot-classification`, `feature-extraction`, `question-answering`, `summarization`, `translation`

Pattern:
```python
from transformers_js import import_transformers_js
transformers = await import_transformers_js()
pipe = await transformers.pipeline('sentiment-analysis')
result = await pipe(text)  # async
```

## Best Practices for Gradio Lite

1. **Async all the way**: ML inference via transformers-js is async — use `async def` handlers
2. **Minimize deps**: Each `<gradio-requirements>` entry adds load time
3. **Loading state**: Show a spinner or "Loading Python runtime..." message
4. **Small models only**: Models under 500 MB work best in browser memory
5. **Test cross-browser**: Safari has different WASM limits than Chrome/Firefox
6. **Static Space over Docker**: Docker Spaces need paid plans; Static Spaces are free

## When to Use

| Scenario | Tool |
|----------|------|
| Zero-cost demo, no backend | Gradio Lite + Static Space |
| Model too large for browser | Gradio + ZeroGPU (free GPU) |
| Production API with auth | Gradio + Docker Space |
| CPU-only, small model, offline | Gradio Lite |
| Heavy PyTorch/CUDA dependency | Gradio + Docker + GPU |

---

# HF Learnings — Gradio Chatbot Multimodal: Inputs, Outputs, Thoughts & Agents

**Topic:** `hf-gradio-chatbot-multimodal-deep-dive`
**Date:** 2026-07-24
**Skill:** mlops/gradio-spaces
**Author:** SakThai
**License:** MIT

## Overview

Deep-dive into Gradio 5/6's multimodal chatbot capabilities — how `gr.ChatInterface`
and `gr.Chatbot` handle text, images, audio, video, and files in the same conversation,
plus intermediate thought/tool-usage display and agent UIs. Sourced from the official
Gradio docs (gradio.app main branch, v6.20.0, July 2026).

---

## 1. Multimodal Input (`multimodal=True`)

Pass `multimodal=True` to `gr.ChatInterface` to enable file uploads alongside text.

### How it changes the chat function signature

Normally: `def chat(message: str, history: list[dict]) -> str`

With multimodal:
```python
def chat(message: dict, history: list[dict]) -> str:
    # message = {"text": "user input", "files": ["/path/to/file1", ...]}
    text = message["text"]
    files = message.get("files", [])
    ...
```

### History format with files

When files are present in history, each message's `content` is a list of content blocks:
```python
[
    {"role": "user", "content": [
        {"type": "file", "file": {"path": "cat1.png"}},
        {"type": "file", "file": {"path": "cat2.png"}},
        {"type": "text", "text": "What's the difference?"}
    ]}
]
```

### Customizing the textbox

Use `gr.MultimodalTextbox` for fine-grained control:
```python
gr.ChatInterface(
    fn=chat_fn,
    multimodal=True,
    textbox=gr.MultimodalTextbox(
        file_count="multiple",        # "single" or "multiple"
        file_types=["image", "audio"], # restrict allowed types
        sources=["upload", "microphone", "clipboard"]  # where files come from
    )
)
```

### Multimodal examples

Examples in multimodal mode use dict format instead of strings:
```python
examples=[
    {"text": "What's in this image?", "files": ["cheetah.jpg"]},
    {"text": "No files", "files": []}
]
```

---

## 2. Multimodal Output — Returning Files & Components

Your chat function can return these Gradio components directly, rendered inline in the chatbot:

| Component     | Usage                           |
|---------------|----------------------------------|
| `gr.Image`    | `return gr.Image("photo.png")`  |
| `gr.Audio`    | `return gr.Audio("sound.wav")`  |
| `gr.Video`    | `return gr.Video("clip.mp4")`   |
| `gr.File`     | `return gr.File("doc.pdf")`     |
| `gr.Plot`     | `return gr.Plot(fig)`           |
| `gr.HTML`     | `return gr.HTML("<b>bold</b>")` |
| `gr.Gallery`  | `return gr.Gallery(images)`     |

### Returning multiple messages

Return a list to send the user multiple assistant messages:
```python
def echo_multimodal(message, history):
    response = [f"You wrote: '{message['text']}' and uploaded:"]
    for file in message.get("files", []):
        response.append(gr.File(value=file))
    return response
```

---

## 3. The `gr.ChatMessage` Dataclass — Thoughts, Tools & Nested Reasoning

`gr.ChatMessage` enables rich assistant messages with intermediate thought accordions
and nested tool-call traces.

### Schema (v6.20.0)

```python
MessageContent = Union[str, FileDataDict, FileData, Component]

@dataclass
class ChatMessage:
    content: MessageContent | list[MessageContent]
    role: Literal["user", "assistant"]
    metadata: MetadataDict = None
    options: list[OptionDict] = None

class MetadataDict(TypedDict):
    title:     NotRequired[str]                        # displayed as accordion header
    id:        NotRequired[int | str]                   # for nesting
    parent_id: NotRequired[int | str]                   # nest under another thought
    log:       NotRequired[str]                         # subtitle next to title
    duration:  NotRequired[float]                       # shown as "(2.3s)"
    status:    NotRequired[Literal["pending", "done"]]  # spinner vs closed

class OptionDict(TypedDict):
    label: NotRequired[str]
    value: str                                          # value sent on click
```

### Basic thought display

```python
from gradio import ChatMessage
import time

def chat_fn(message, history):
    # Show a thinking step
    thought = ChatMessage(
        role="assistant",
        content="Searching the knowledge base...",
        metadata={"title": "🧠 Thinking", "status": "pending"}
    )
    yield thought

    time.sleep(1)

    # Mark as done
    thought.metadata["status"] = "done"
    thought.metadata["duration"] = 1.0
    yield thought

    # Final answer
    yield ChatMessage(
        role="assistant",
        content="Here's what I found..."
    )
```

### Nested thoughts (agent tool traces)

Use `id` and `parent_id` to nest tool calls inside a reasoning step:
```python
ChatMessage(
    role="assistant",
    content="Calling weather API...",
    metadata={"title": "🌤️ get_weather", "id": 1, "status": "pending"}
)
ChatMessage(
    role="assistant",
    content="Parsing response...",
    metadata={"title": "parse_response", "id": 2, "parent_id": 1, "status": "done"}
)
```

### Preset response options

Provide clickable buttons the user can choose:
```python
ChatMessage(
    role="assistant",
    content="Would you like more details?",
    options=[
        {"label": "Yes, tell me more", "value": "tell me more"},
        {"label": "No, thanks", "value": "no thanks"}
    ]
)
```

---

## 4. Streaming Chatbots

Use `yield` in your chat function for token-by-token streaming. Gradio sends
diffs (not full messages) over the network — efficient even for long generations.

```python
def slow_echo(message, history):
    for i in range(len(message)):
        time.sleep(0.3)
        yield "You typed: " + message[: i+1]
```

While streaming, the Submit button becomes a Stop button to halt generation.

---

## 5. Chat History Persistence (`save_history=True`)

Enable per-user conversation history stored in the browser's local storage:

```python
gr.ChatInterface(
    fn=chat_fn,
    save_history=True
)
```

- Each user gets their own private history (no interference between users)
- Conversations are stored locally in the browser
- Side panel shows previous conversations for easy switching
- Works on HF Spaces with multiple concurrent users

---

## 6. User Feedback (Flagging)

```python
gr.ChatInterface(
    fn=chat_fn,
    flagging_mode="manual",      # show thumbs up/down
    flagging_options=["Like", "Spam", "Inappropriate", "Other"],
    flagging_dir="flagged_logs"  # where CSV files are saved
)
```

- `"Like"` shows a thumbs-up icon (case-sensitive)
- Other options appear in a dropdown under a flag icon
- Entire chat history + flagged response saved to CSV

---

## 7. Chatbot Component Customization

```python
gr.ChatInterface(
    fn=chat_fn,
    chatbot=gr.Chatbot(
        height=400,
        placeholder="<strong>Ask me anything</strong><br>I'm here to help!",
        label="Assistant",
        avatar_images=(None, "https://example.com/bot.png"),
        show_copy_button=True,
    ),
    textbox=gr.Textbox(placeholder="Type here...", container=False, scale=7),
)
```

The `placeholder` accepts Markdown/HTML and is shown centered before any messages.

---

## 8. Additional Inputs & Outputs

### Additional Inputs

Expose extra controls (system prompt, temperature slider, etc.):
```python
with gr.Blocks() as demo:
    system_prompt = gr.Textbox("You are helpful.", label="System Prompt")
    temperature = gr.Slider(0, 2, value=1.0, label="Temperature")

    gr.ChatInterface(
        fn=chat_fn,
        additional_inputs=[system_prompt, temperature]
    )
```

- Unrendered components appear in an accordion below the chatbot
- Already-rendered components (in the Blocks context) stay where they are

### Additional Outputs

Return extra values rendered in separate components:
```python
with gr.Blocks() as demo:
    code_out = gr.Code(render=False)  # render after ChatInterface

    with gr.Row():
        with gr.Column():
            gr.ChatInterface(
                chat_fn,
                additional_outputs=[code_out]
            )
        with gr.Column():
            code_out.render()
```

```python
def chat_fn(message, history):
    if "python" in message.lower():
        return "Here's the code:", gr.Code(language="python", value="print('hello')")
    else:
        return "Ask about Python.", None
```

---

## 9. Direct Chatbot Value Manipulation

Modify the chatbot value with custom events (e.g., a dropdown to prefill history):

```python
with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    prefill = gr.Radio(["Conversation A", "Conversation B"])

    def load_conversation(choice):
        convos = {
            "Conversation A": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            ...
        }
        return gr.Chatbot(value=convos[choice])

    prefill.change(load_conversation, prefill, chatbot)
```

---

## 10. API Endpoint

Every `gr.ChatInterface` exposes a REST API at `/fn_name` (default `/chat`):

```python
gr.ChatInterface(chat_fn, api_name="chat")  # endpoint: /chat
```

Use the Gradio Python/JS Client to call it:

```python
from gradio_client import Client
client = Client("user/my-chat-space")
result = client.predict("/chat", {"message": "Hello"})
```

---

## 11. Single-Line Chat from OpenAI-Compatible Endpoint

```python
gr.load_chat("http://localhost:11434/v1/", model="llama3.2", token="***").launch()
```

Works with Ollama, vLLM, TGI, or any OpenAI-compatible server.

---

## Key Takeaways

1. `multimodal=True` + `gr.MultimodalTextbox` = users can send text + files together
2. Chat function returns `gr.Image`, `gr.Audio`, `gr.Video`, `gr.File`, etc. inline
3. `gr.ChatMessage` with `metadata={"title": ...}` = collapsible thought accordion
4. Nested thoughts via `id`/`parent_id` for agent tool traces
5. `save_history=True` = per-user local-storage persistence (free, no backend)
6. `flagging_mode="manual"` = thumbs up/down feedback, CSV saved locally
7. Streaming via `yield` — diffs sent over network, Stop button built in
8. Additional inputs/outputs for extra controls and side panels
9. Direct chatbot value manipulation for prefill/clear buttons
10. `gr.load_chat()` for instant OpenAI-compatible endpoints
