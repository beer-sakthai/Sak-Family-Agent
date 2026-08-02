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

---

# HF Learnings — Gradio Queue & Concurrency Optimization

**Topic:** `hf-gradio-queue-and-concurrency-optimization-deep-dive`
**Date:** 2026-07-24
**Skill:** mlops/gradio-spaces
**Author:** SakThai
**License:** MIT

## Overview

Deep-dive into Gradio's queue system (v6.20.0) — how requests are serialized, parallelized, batched, and prioritized. Covers the `demo.queue()` configuration, per-event `concurrency_limit`, the `batch` mode for grouped inference, client-side status tracking, Spaces-specific throughput optimization, and the internal queue architecture.

**Key insight:** Without `.queue()` on a Spaces deployment, every user beyond the first gets `"Too many requests"` errors — the queue is mandatory for any multi-user deployment.

---

## 1. Queue Architecture — How Requests Flow

```
User Request
    │
    ▼
┌─────────────────────┐
│  FastAPI Endpoint   │  ← always running
│  (api_open=True)    │     bypasses queue
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  Queue (redis-less) │  ← in-process asyncio queue
│  max_size=N         │     rejects if full
│  default_concurrency=1│  default: 1 job at a time
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  Worker Pool        │  ← asyncio tasks
│  (up to concurrency)│     executes fn()
└─────────────────────┘
    │
    ▼
   Response
```

The queue is **in-process** (no Redis dependency). It uses Python's `asyncio.Queue` under the hood. Each Gradio process has one queue instance. For horizontal scaling, each process has its own queue — no shared queue across processes.

### Key parameters (from `gradio.Queue` source — v6.20.0)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status_update_rate` | `float \| "auto"` | `"auto"` | How often to send position/progress updates. "auto" = send after each job finishes. A float = interval in seconds. |
| `api_open` | `bool \| None` | `None` | If True, REST API routes bypass the queue entirely. Requests go straight to the event handler. |
| `max_size` | `int \| None` | `None` | Max queued events. `None` = unlimited. When full, new events are rejected with a "queue is full" message. |
| `default_concurrency_limit` | `int \| None` | `1` | The default concurrency for event listeners that don't specify their own. Also settable via `GRADIO_DEFAULT_CONCURRENCY_LIMIT` env var. |

---

## 2. Basic Queue Configuration

### Minimal (required for multi-user)

```python
demo = gr.Interface(fn=my_fn, inputs="text", outputs="text")
demo.queue()             # enables queue with all defaults
demo.launch()
```

### Tuned for throughput

```python
demo = gr.Interface(fn=my_fn, inputs="text", outputs="text")
demo.queue(
    default_concurrency_limit=5,   # 5 parallel executions
    max_size=20,                    # max 20 queued
    status_update_rate="auto",      # tell users their position
)
demo.launch()
```

### With Blocks

```python
with gr.Blocks() as demo:
    btn = gr.Button("Generate")
    output = gr.Textbox()

    btn.click(fn=generate, inputs=gr.Textbox(), outputs=output)

demo.queue(max_size=10, default_concurrency_limit=3)
demo.launch()
```

---

## 3. Per-Event Concurrency Control

Different events in the same app can have different concurrency limits — critical when mixing fast (text) and slow (image) endpoints.

### concurrency_limit

```python
with gr.Blocks() as demo:
    text_btn = gr.Button("Quick Text")
    image_btn = gr.Button("Slow Image")
    output = gr.Textbox()

    # Fast endpoint — allow parallelism
    text_btn.click(
        fn=quick_text,
        inputs=gr.Textbox(),
        outputs=output,
        concurrency_limit=10,       # up to 10 parallel
    )

    # Slow GPU endpoint — serialize to avoid OOM
    image_btn.click(
        fn=slow_image_gen,
        inputs=gr.Textbox(),
        outputs=output,
        concurrency_limit=1,        # one at a time
    )

demo.queue(default_concurrency_limit=5)
demo.launch()
```

**Important:** `concurrency_limit` on an event cannot exceed the queue's `default_concurrency_limit`. If `default_concurrency_limit=5`, the max per-event is also 5 unless adjusted at the queue level.

### concurrency_id — Group related events

Events sharing the same `concurrency_id` are serialized together — even if they're different endpoints:

```python
btn_1.click(fn=model_a, ..., concurrency_limit=2, concurrency_id="gpu")
btn_2.click(fn=model_b, ..., concurrency_limit=2, concurrency_id="gpu")
# Both share the same GPU pool — combined concurrency is 2
```

---

## 4. Queue Bypass Patterns

### api_open = True — REST routes skip queue

When `api_open=True`, direct REST API calls (e.g., via `gradio_client`) bypass the queue. Use this for trusted internal services where you want low latency at the cost of overloading the server.

```python
demo.queue(api_open=True)
```

### queue=False on individual events

Skip the queue for specific events even when the global queue is enabled:

```python
btn.click(fn=immediate_fn, ..., queue=False)
```

Useful for: UI-only operations (toggle settings, clear fields) that don't need queue sequencing.

---

## 5. Batch Processing Mode

For high-throughput inference, enable `batch=True` — Gradio groups multiple inputs and sends them as a batch to your function.

### How it works

```python
def batch_fn(texts: list[str]) -> list[str]:
    # texts is a list of all pending inputs
    return [t.upper() for t in texts]

with gr.Blocks() as demo:
    inp = gr.Textbox()
    out = gr.Textbox()
    inp.submit(
        fn=batch_fn,
        inputs=inp,
        outputs=out,
        batch=True,                    # enable batching
        max_batch_size=4,              # max inputs per batch
    )

demo.queue(default_concurrency_limit=1)
demo.launch()
```

### Batch parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `batch` | `bool` | `False` | Enable batch processing mode |
| `max_batch_size` | `int` | `4` | Max inputs in a single batch |
| `batch_concurrency` | `int` | `1` (from queue default) | How many batches to process in parallel |

### When to use batching

- **High-throughput, low-latency models** (e.g., text classification, embedding)
- **GPU inference** where batching improves utilization
- **Stateless functions** (no gr.State dependency)

### When NOT to use batching

- Functions that depend on `gr.State` (state is per-session, not batchable)
- Streaming generators (yield doesn't work with batch=True)
- Functions with side effects (logging per request, external API calls)

---

## 6. Progress Tracking with Queue

`gr.Progress()` works hand-in-hand with the queue system:

```python
def long_task(progress=gr.Progress()):
    progress(0, desc="Starting...")
    for i in progress.tqdm(range(100), desc="Processing"):
        time.sleep(0.1)
    return "Done!"

demo = gr.Interface(fn=long_task, inputs=None, outputs="text")
demo.queue()
demo.launch()
```

The queue delivers progress updates to the client at `status_update_rate` intervals. Each client gets their own progress bar — no cross-user interference.

### Client-side status (JS Client)

```javascript
const app = await Client.connect("user/my-space", { events: ["data", "status"] });
const sub = app.submit("/predict", { text: "hello" });

for await (const msg of sub) {
    if (msg.type === "status") {
        console.log(msg.position, msg.eta, msg.stage);
        // { position: 2, eta: 15, stage: "pending" }
        // → "You are #2 in queue, ~15s wait"
    }
    if (msg.type === "data") {
        console.log(msg.data);  // actual result
    }
}
```

### Status payload fields

| Field | Type | Description |
|-------|------|-------------|
| `queue` | `bool` | Whether this request went through the queue |
| `stage` | `"pending" \| "error" \| "complete" \| "generating"` | Current request stage |
| `position` | `int` | Queue position (0 = processing now) |
| `eta` | `int` | Estimated seconds until processing starts |
| `size` | `int` | Total queue size |
| `progress_data` | `array` | Per-task progress from `gr.Progress()` |

---

## 7. Spaces-Specific Queue Optimization

### The `GRADIO_DEFAULT_CONCURRENCY_LIMIT` env var

Set this in your Space's Settings → Repository Secrets:

```
GRADIO_DEFAULT_CONCURRENCY_LIMIT=5
```

This sets the default value before your Python code runs — useful for overriding the default when you can't modify the app code (e.g., third-party Spaces).

### Spaces hardware and concurrency guidance

| Hardware | Recommended default_concurrency_limit | Notes |
|----------|---------------------------------------|-------|
| CPU basic | 2-5 | Lightweight models only; CPU is shared |
| CPU upgrade | 5-10 | More CPU cores available |
| ZeroGPU | 1-3 | GPU is queued separately via `@spaces.GPU` |
| T4 small | 2-4 | Small GPU memory; watch for OOM |
| A10G | 4-8 | Larger GPU; good for batch inference |

### Common anti-patterns on Spaces

1. **Not calling `.queue()`** — Without it, only one concurrent user is supported. Always call `demo.queue()`.
2. **`concurrency_limit > GPU memory allows`** — If your model takes 8GB and you set concurrency_limit=4, you'll hit OOM. Start conservative.
3. **`max_size` too small** — A popular Space may get hundreds of requests. Set `max_size` high enough (or `None`).
4. **Forgetting `GRADIO_DEFAULT_CONCURRENCY_LIMIT` in Docker Spaces** — Environment variables set in Space Settings aren't available at build time, only at runtime.

### Spaces sleep/wake and queue drain

When a Space goes to sleep, queued requests are lost. The client sees the Space as "sleeping" via the `status_callback`. Upon wake, the queue is fresh (empty). Solutions:

- **PRO users** can disable sleeping
- **Client-side retry**: Use the JS Client's `status_callback` to retry after the Space wakes
- **ZeroGPU Spaces** don't sleep (but have GPU queue wait times)

---

## 8. Queue Internals (Source Architecture)

From Gradio v6.20.0 source (`gradio/queueing.py`):

### Queue is asyncio-based

```python
# Simplified architecture
class Queue:
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._events: dict[str, Event] = {}
        self._workers: dict[int, asyncio.Task] = {}

    async def start(self):
        # Spawn worker tasks
        for i in range(self.concurrency_limit):
            worker = asyncio.create_task(self._worker_loop(i))
            self._workers[i] = worker

    async def _worker_loop(self, worker_id):
        while True:
            event = await self._queue.get()
            await self._process_event(event)
```

### Key internal behaviors

- **No priority queue**: FIFO (first-in, first-out) — no priority levels for different event types
- **No preemption**: Once an event starts processing, it runs to completion
- **Per-worker isolation**: Each worker handles one event at a time; events don't share worker state
- **Status broadcast**: After each job completion, the queue broadcasts status updates to ALL connected clients (not just the ones waiting)
- **Cleanup**: Events are removed from `_events` dict after completion to prevent memory leaks

### WebSocket protocol

The queue communicates with the browser via WebSocket:
```
Client → Server: { "type": "send_data", "data": {...}, "fn_index": 0 }
Server → Client: { "type": "estimation", "queue_position": 2, "rank_eta": 15.0 }
Server → Client: { "type": "process_generating" | "process_completed", "output": {...} }
Server → Client: { "type": "progress", "progress_data": [...] }
```

---

## 9. Queue + Streaming

Streaming (generator functions with `yield`) works with the queue but has special behavior:

```python
def stream_fn(message, history):
    for i in range(10):
        time.sleep(0.5)
        yield f"Token {i}"   # streamed via queue WebSocket

demo = gr.ChatInterface(fn=stream_fn)
demo.queue()
demo.launch()
```

**How streaming interacts with concurrency:**
- A streaming function holds its worker slot for the entire duration
- While streaming, no other event can use that worker slot
- If `default_concurrency_limit=1` and one user is streaming, ALL other users wait
- **Fix**: Set `concurrency_limit` higher or use a separate `concurrency_id` for non-streaming events

---

## 10. Queue + `@gr.Cache()` (Gradio 5+)

Cached results bypass the queue entirely:

```python
@gr.Cache()
def expensive_fn(text):
    return model.generate(text)

demo = gr.Interface(fn=expensive_fn, inputs="text", outputs="text")
demo.queue()
demo.launch()
```

When a cached result exists, the user gets it immediately without entering the queue. The cache key is computed from input values.

**Limitations for Spaces:**
- Cache is in-memory (lost on Space restart)
- Cache directory (`GRADIO_CACHE_DIR`) can be pointed to persistent storage
- Not compatible with `batch=True`

---

## 11. Measuring Queue Performance

### Expected throughput formula

```
Throughput (req/s) ≈ concurrency_limit / avg_latency_per_request
```

Example: `concurrency_limit=5`, each request takes 2s → ~2.5 req/s.

### max_size sizing

```
max_size = concurrency_limit × (expected_burst_duration / avg_latency)
```

Example: `concurrency_limit=5`, expect 30-second burst, 2s latency → `max_size = 5 × (30/2) = 75`

### Spawning more workers (Docker Spaces)

In a Docker Space, you can run multiple Gradio processes behind a reverse proxy, each with its own queue. This is the only way to scale beyond a single process's concurrency:

```yaml
# Dockerfile approach — multi-process via supervisord or gunicorn
# Each process has its own queue, HF Spaces LB distributes randomly
```

---

## 12. Decision Matrix

| Scenario | queue() config | Per-event settings |
|----------|---------------|-------------------|
| Single-user demo | Not needed | — |
| Multi-user, fast (<100ms) | `default_concurrency_limit=10` | `concurrency_limit` per event optional |
| Multi-user, GPU-bound | `default_concurrency_limit=2-4` | Set per-event carefully |
| Mixed fast+slow | Moderate base | Low concurrency on GPU, high on CPU |
| High-throughput, tiny model | `batch=True, max_batch_size=16` | `batch_concurrency=2` |
| Streaming chatbot | `default_concurrency_limit=3-5` | Higher for streaming, lower for GPU |
| ZeroGPU Space | `default_concurrency_limit=3` | `@spaces.GPU` controls GPU queue separately |

---

## 13. Quick Reference — Commands

```python
# Enable queue with defaults
demo.queue()

# Full configuration
demo.queue(
    default_concurrency_limit=5,
    max_size=50,
    status_update_rate="auto",
)

# Allow REST API bypass
demo.queue(api_open=True)

# Per-event fine control
btn.click(fn=my_fn, ..., concurrency_limit=3)       # limit parallelism
btn.click(fn=my_fn, ..., concurrency_id="gpu_pool")  # group under one pool
btn.click(fn=my_fn, ..., batch=True, max_batch_size=8)  # batch mode
btn.click(fn=my_fn, ..., queue=False)                # skip queue

# Environment variable
# GRADIO_DEFAULT_CONCURRENCY_LIMIT=5
```

---

## Key Takeaways

1. **Always call `.queue()`** on multi-user Spaces — without it, only one user works at a time.
2. **`default_concurrency_limit`** controls the global parallelism level; start at 1 and increase while watching for OOM.
3. **Per-event `concurrency_limit`** lets you give fast endpoints more workers and slow GPU ones fewer.
4. **`concurrency_id`** groups events that share a resource (same GPU, same API rate limit).
5. **`batch=True`** groups multiple inputs into one function call — great for embedding/classification models.
6. **`api_open=True`** lets programmatic clients bypass the queue (useful for internal services).
7. **Queue is FIFO** — no priority; long-running streaming jobs block the queue for others.
8. **Status updates** flow over WebSocket — client libraries can show queue position + ETA.
10. **`GRADIO_DEFAULT_CONCURRENCY_LIMIT`** env var sets the default before your code runs.
11. **Cache bypasses queue** — `@gr.Cache()` is free and fast for repeated requests.

---

## 2026-07-24: hf-gradio-6-chatinterface-deep-dive

### Summary
Deep dive into `gr.ChatInterface` (Gradio v6.20.0) — Gradio's high-level abstraction for creating chatbot UIs. Covers the full parameter API (30+ parameters), streaming, multimodal input, custom chatbot integration, events (like/submit/retry), history persistence, agent/tool-use patterns, and production configuration (concurrency, caching, API visibility). ChatInterface is the preferred pattern for LLM chatbots on Hugging Face Spaces — replaces manual gr.Chatbot + gr.Textbox wiring in most cases.

### Sources
- Official docs: https://www.gradio.app/docs/gradio/chatinterface
- Gradio changelog: https://github.com/gradio-app/gradio/releases
- Source code: `gradio/chatinterface.py` in `gradio>=6.0`

### Full Parameter API

#### Required
| Parameter | Type | Description |
|-----------|------|-------------|
| `fn` | `Callable` | The chat function. Accepts `(message: str, history: list[dict])` and returns/yields `str` | `gr.Component` | `dict` (openai-style) | `list[dict]`. History format: `[{"role": "user"|"assistant", "content": str | {"path": str} | gr.Component}]` |

#### Input Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `multimodal` | `bool` | `False` | If True, uses `gr.MultimodalTextbox` for file upload support. When True, `fn` receives `{"text": str, "files": list}` instead of plain str |
| `chatbot` | `gr.Chatbot` | `None` | Custom Chatbot instance for fine-grained control (placeholder, avatar_images, latex_delimiters, sanitize_html, render_markdown, bubble_full_width, show_copy_button, etc.) |
| `textbox` | `gr.Textbox` | `gr.MultimodalTextbox` | `None` | Custom text input component instance |

#### Additional Inputs/Outputs
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `additional_inputs` | `str` | `Component` | `list[str | Component]` | `None` | Extra components passed as additional args to `fn` after `history`. If not already in a Blocks context, displayed in an accordion below the chatbot |
| `additional_inputs_accordion` | `str` | `gr.Accordion` | `None` | Custom accordion for additional inputs, defaults to `gr.Accordion(label="Additional Inputs", open=False)` |
| `additional_outputs` | `Component` | `list[Component]` | `None` | Extra output components — `fn` must return additional values for these. Must already exist in Blocks scope |

#### UX & Appearance
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `editable` | `bool` | `False` | Allow users to edit past messages and regenerate responses |
| `title` | `str` | `I18nData` | `None` | Title above chatbot in large font, also used as browser tab title |
| `description` | `str` | `None` | Description below title, accepts Markdown and HTML |
| `fill_height` | `bool` | `True` | Expand to fill window height |
| `fill_width` | `bool` | `False` | Expand horizontally to fill container (default: centered + constrained width) |
| `autofocus` | `bool` | `True` | Auto-focus textbox on page load |
| `autoscroll` | `bool` | `True` | Auto-scroll to bottom on new messages (pauses if user scrolls up) |
| `submit_btn` | `str` | `bool` | `True` | Show submit button. String = custom text, False = hide, True = icon-only |
| `stop_btn` | `str` | `bool` | `True` | Show stop button during generator execution. String = custom text |
| `show_progress` | `Literal["full","minimal","hidden"]` | `"minimal"` | Progress animation level |

#### Examples
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `examples` | `list[str]` | `list[MultimodalValue]` | `list[list]` | `None` | Sample inputs. Strings for text-only, dicts for multimodal. With additional_inputs, each example is a list: `[message, val1, val2, ...]` |
| `example_labels` | `list[str]` | `None` | Labels displayed instead of example values |
| `example_icons` | `list[str]` | `None` | Icon URLs/paths displayed above examples |
| `run_examples_on_click` | `bool` | `True` | Auto-run example through fn on click (False = only populate input) |
| `cache_examples` | `bool` | `None` | Cache example outputs. Default True on HF Spaces, False elsewhere |
| `cache_mode` | `Literal["eager","lazy"]` | `None` | "eager" = cache at launch, "lazy" = cache after first use. Falls back to GRADIO_CACHE_MODE env var, then "eager" |

#### Flagging
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flagging_mode` | `Literal["never","manual"]` | `None` | "never" hides flag button, "manual" shows it |
| `flagging_options` | `list[str]` | `tuple[str,...]` | `("Like","Dislike")` | Flag categories. "Like"/"Dislike" render as thumbs up/down icons per bot message |
| `flagging_dir` | `str` | `".gradio/flagged"` | Directory for flagged data |

#### API & Advanced
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_name` | `str` | `None` | API endpoint name (None = use fn name) |
| `api_description` | `str` | `False` | `None` | API endpoint description (None = use fn docstring, False = hidden) |
| `api_visibility` | `Literal["public","private","undocumented"]` | `"public"` | API docs visibility |
| `concurrency_limit` | `int` | `None` | `Literal["default"]` | Max simultaneous submissions. "default" = queue default (1), None = unlimited |
| `delete_cache` | `tuple[int,int]` | `None` | Auto-delete temp files: `(frequency_seconds, max_age_seconds)`. e.g. `(86400, 86400)` = daily cleanup |
| `save_history` | `bool` | `False` | Save chat to browser localStorage with side panel for previous conversations |
| `validator` | `Callable` | `None` | Input validation function, returns `gr.validate()` objects |
| `analytics_enabled` | `bool` | `None` | Telemetry toggle. Falls back to GRADIO_ANALYTICS_ENABLED env var |

### Events & Methods

ChatInterface inherits event methods from gr.Blocks:

| Method | Description |
|--------|-------------|
| `.submit(fn, inputs, outputs, ...)` | Triggered on message submit |
| `.like(fn, inputs, outputs, ...)` | Attached to Chatbot component — upvote/downvote (only when flagging_options includes "Like"/"Dislike") |
| `.then(fn, inputs, outputs, ...)` | Chain events after submit |
| `.success(fn, inputs, outputs, ...)` | Fire on successful completion |
| `.error(fn, inputs, outputs, ...)` | Fire on error |
| `.queue(default_concurrency_limit=N)` | Enable queue with concurrency control |

**Key difference from gr.Chatbot.like()**: In ChatInterface, `.like()` is wired through the `flagging_options=["Like","Dislike"]` parameter. The `Chatbot.like()` method is separate — it fires on clicking the thumbs-up/thumbs-down icons and passes `(value: LikeDislikeData, message: dict)` to the handler.

### Streaming Patterns

ChatInterface supports streaming natively via Python generators:

```python
import gradio as gr
import time

def stream_response(message, history):
    """Stream tokens one by one"""
    response = f"You said: {message}"
    for i in range(len(response)):
        time.sleep(0.05)
        yield response[:i+1]

gr.ChatInterface(
    fn=stream_response,
    title="Streaming Chatbot",
    type="messages"  # or "tuples" for legacy format
).launch()
```

The `fn` function must use `yield` instead of `return` for streaming. Each `yield` sends incremental output to the UI. The Gradio client libraries handle SSE (Server-Sent Events) automatically for streaming endpoints.

### Multimodal ChatInterface

Enable file uploads with `multimodal=True`:

```python
import gradio as gr

def multimodal_chat(message, history):
    """message = {"text": "describe this", "files": ["/tmp/image.png"]}"""
    if message["files"]:
        return f"Received {len(message['files'])} file(s). Text: {message['text']}"
    return f"You said: {message['text']}"

gr.ChatInterface(
    fn=multimodal_chat,
    multimodal=True,
    title="Multimodal Chat"
).launch()
```

When `multimodal=True`:
- Input uses `gr.MultimodalTextbox` — supports text + file uploads
- `fn` first arg is a dict `{"text": str, "files": list[file_path]}`
- Files are uploaded to server temp directory automatically
- Supported file types depend on `gr.MultimodalTextbox` config (images, audio, video, documents by default)

### Custom Chatbot Component

Pass a pre-configured `gr.Chatbot` for fine control:

```python
import gradio as gr

chatbot = gr.Chatbot(
    placeholder="Ask me anything...",
    avatar_images=("user.png", "bot.png"),
    latex_delimiters=[{"left": "$", "right": "$", "display": False}],
    sanitize_html=False,
    render_markdown=True,
    bubble_full_width=False,
    show_copy_button=True,
)

def respond(message, history):
    return f"Response to: {message}"

gr.ChatInterface(
    fn=respond,
    chatbot=chatbot,
    title="Customized Chat"
).launch()
```

**Custom chatbot + events in Blocks scope** (for `.like()` support):

```python
import gradio as gr

with gr.Blocks() as demo:
    chatbot = gr.Chatbot(placeholder="Chat here...")

    def respond(message, history):
        return f"You said: {message}"

    # Wire chatinterface manually in Blocks
    chat_interface = gr.ChatInterface(
        fn=respond,
        chatbot=chatbot,
    )

    # Attach like/feedback events
    chatbot.like(
        lambda value, msg: print(f"Feedback: {value} on {msg}"),
        None, None
    )
```

### Agent / Tool-Use Patterns

ChatInterface supports OpenAI-style tool messages for agent UIs:

```python
def agent_response(message, history):
    """Agent that can use tools"""
    # ... agent logic ...
    return [
        {"role": "assistant", "content": "Let me look that up..."},
        {"role": "tool", "content": "Tool result", "metadata": {"title": "⚙️ Tool Call"}},
        {"role": "assistant", "content": "Based on my search, the answer is 42."}
    ]
```

The function can return a list of OpenAI-style message dicts. Each dict with `role` and `content` renders as a distinct bubble in the Chatbot. The `metadata` dict supports `title` for tool call labels, and other properties for rich rendering.

### History Format

Two formats supported:

**OpenAI-style (default/recommended)**:
```python
history = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "What's the weather?"},
]
```

**Tuples (legacy, Gradio 4.x)**:
```python
history = [
    ("Hello", "Hi there!"),
    ("What's the weather?", None),  # None = still generating
]
```

Set `type="messages"` (default in v6) for OpenAI-style, `type="tuples"` for legacy.

### Concurrency & Production

```python
gr.ChatInterface(
    fn=respond,
    concurrency_limit=5,            # Allow 5 simultaneous chats
    delete_cache=(3600, 86400),     # Clean temp files hourly if older than 1 day
    api_name="chat",                # Named endpoint for Gradio client
    api_visibility="public",        # Expose in API docs
    save_history=True,              # Browser localStorage persistence
).queue(default_concurrency_limit=5).launch()
```

**Zero-cost note for HF Spaces**: ChatInterface runs on free CPU Spaces out of the box. For GPU chatbots, use `@spaces.GPU` decorator on the fn with ZeroGPU. Queue is always active on HF Spaces (no choice). Concurrency is limited in free tier.

### Key Insights

1. **ChatInterface is declarative** — handles message passing, history management, and UI state internally. Avoids manual `gr.Chatbot` + `gr.Textbox` + event wiring in 90% of cases.
2. **`fn` signature** — `(message, history)` where history is always the *current* history (before the new message is appended). The function doesn't need to manage history appending — Gradio does it.
3. **Streaming via yield** — Use generator functions for token-by-token output. Gradio sends incremental updates over WebSocket.
4. **History mutation** — Modifying the history list in-place and returning it enables editing past messages (when `editable=True`).
5. **`.like()` events** — Only appear when flagging_options includes "Like"/"Dislike". These are rendered as thumbs-up/down icons per bot message.
6. **`save_history=True`** — Enables conversation sidebar in the UI. History persisted in `localStorage` — survives page refreshes but not shared across browsers.
7. **Agents work** — Return multiple message dicts with `role: "tool"` for function-call display. Status messages need `metadata: {"title": "⚙️ Processing..."}` for rendering.
8. **ChatInterface + Blocks** — Wrap in `gr.Blocks` for layout control and additional components, but lose auto-layout convenience.
9. **`cache_examples=True`** on HF Spaces — Caches example outputs at app start so first user doesn't pay cold-start penalty.
10. **API unlisted** — Set `api_visibility="private"` to prevent programmatic access while keeping UI functional.


---

# HF Learnings — Gradio 6 Custom Components: Create, Dev, Build, Publish

**Topic:** `hf-gradio-custom-components-deep-dive`
**Date:** 2026-07-24
**Skill:** mlops/gradio-spaces
**Author:** SakThai
**License:** MIT

## Overview

Deep-dive into Gradio 6's Custom Components system — the full workflow for creating,
developing, building, and publishing reusable Gradio components. Covers the CLI (`gradio cc`),
backend implementation (`preprocess`/`postprocess`/`data_model`), frontend Svelte architecture,
and publishing to PyPI / Hugging Face Spaces.

**Source:** Gradio v6.20.0 official guides at https://github.com/gradio-app/gradio/tree/main/guides/08_custom-components
(5 guides + 1 FAQ + 3 case studies: PDF component, Multimodal Chatbot parts 1-2, Documentation).

## Prerequisites

- Python 3.10+
- Node.js 20+ and npm 9+
- Gradio 5+ (`pip install --upgrade gradio`)
- pip 21.3+

## The 4-Step Workflow

```
gradio cc create MyComponent --template SimpleTextbox   # 1. CREATE
cd mycomponent && gradio cc dev                          # 2. DEVELOP (hot reload)
gradio cc build                                           # 3. BUILD (.whl + .tar.gz)
gradio cc publish                                         # 4. PUBLISH (PyPI + Spaces)
```

### Step 1: Create

`gradio cc create <Name> --template <Template>` bootstraps a component directory:

```
mycomponent/
├── backend/              # Python code
│   └── gradio_mycomponent/
│       ├── __init__.py
│       └── mycomponent.py
├── frontend/             # Svelte/JS code
│   ├── Index.svelte      # Main component view
│   ├── Example.svelte    # Example preview view
│   └── package.json
├── demo/                 # Sample app for development
│   └── app.py
└── pyproject.toml        # Python package config
```

**Templates available:** `SimpleTextbox`, `SimpleDropdown`, `SimpleImage`, `File`, or
any built-in Gradio component (e.g. `--template Chatbot`).

List templates: `gradio cc show`

### Step 2: Develop (Hot Reload)

`gradio cc dev` from the component directory launches:
1. A Vite dev server for the frontend (port 7861 by default) — **hot reloads** on file changes
2. A Python server running the demo app with the custom component

Changes to both `frontend/*.svelte` and `backend/*.py` reflect live without manual restart.

For troubleshooting:
- Check `window.__GRADIO_CC__` in browser console — if empty, CLI can't find the component
- Use `--python-path` and `--gradio-path` to specify exact executables
- Chrome on Windows blocks local Svelte files — use WSL

### Step 3: Build

`gradio cc build` creates a distributable Python package:

- `dist/gradio_mycomponent-X.Y.Z-py3-none-any.whl`
- `dist/gradio_mycomponent-X.Y.Z.tar.gz`

Also auto-generates documentation:
- Interactive Gradio Space (demo + API docs)
- Static README.md with installation guide, type signatures, event tables

Pass `--no-generate-docs` to skip.

### Step 4: Publish

`gradio cc publish` walks through:
1. Upload `.whl`/`.tar.gz` to PyPI (requires PyPI account)
2. Upload demo app to Hugging Face Spaces

Set `pyproject.toml` URLs for auto-linking:
```toml
[project.urls]
repository = "https://github.com/user/repo-name"
space = "https://huggingface.co/spaces/user/space-name"
```

## Backend Architecture

### Inheritance Hierarchy

| Base Class     | When to Use                                      |
|----------------|--------------------------------------------------|
| `Component`    | Default for most custom components               |
| `FormComponent`| When component should group in `Form` layout     |
| `BlockContext` | When other components go "inside" (like `gr.Tab`)|
| `StreamingOutput`| For streaming output components                |

### Required Methods

```python
class MyComponent(Component):

    def preprocess(self, x: Any) -> Any:
        """Convert frontend JSON → Python value for user function."""
        return x

    def postprocess(self, y: Any) -> Any:
        """Convert user function return → frontend JSON."""
        return y

    def example_payload(self) -> Any:
        """Sample input for View API page (JSON-serializable)."""
        return "hello"

    def example_value(self) -> Any:
        """Sample output for default demo (passes through postprocess)."""
        return "hello"

    def api_info(self) -> dict:
        """JSON Schema of value. Only needed without data_model."""
        ...

    def flag(self, x, flag_dir) -> str:
        """Serialize value to CSV/JSON. Only needed without data_model."""
        ...

    def read_from_flag(self, x) -> Any:
        """Deserialize from flag file. Only needed without data_model."""
        ...
```

### The `data_model` — Simplifies Everything

Use Pydantic V2 models to auto-implement `api_info`, `flag`, `read_from_flag`:

```python
from gradio.data_classes import FileData, GradioModel, GradioRootModel

# Standard model — serializes to dict
class VideoData(GradioModel):
    video: FileData
    subtitles: Optional[FileData] = None

# Root model — serializes to raw list (no wrapping dict)
class ChatHistory(GradioRootModel):
    root: list[tuple[str | None, str | None]]

class MyVideoComponent(Component):
    data_model = VideoData
```

**Types:**
- `GradioModel` → serializes as `{"video": {...}, "subtitles": {...}}`
- `GradioRootModel` → serializes as the raw value `[{...}, {...}]`

### Handling Files

**Always use `FileData`** for file upload components:

```python
from gradio.data_classes import FileData

class MyFileData(GradioModel):
    file: FileData
    caption: Optional[str] = None
```

Using `FileData` enables:
- Secure file serving (Gradio blocks arbitrary file access)
- Automatic caching (deduplication)
- Client library auto-upload/download

### Event Triggers

```python
from gradio.events import Events, EventListener

class MyComponent(Component):
    EVENTS = [
        Events.change,                    # Built-in event
        Events.upload,
        EventListener(                    # Custom event with docs
            "bingbong",
            doc="Triggered when the user does a bingbong."
        ),
    ]
```

Events auto-generate methods `my_component.change(fn, ...)`, `my_component.bingbong(fn, ...)`.

## Frontend Architecture

### Directory Structure

```
frontend/
├── Index.svelte        # Main component (required)
├── Example.svelte      # Example preview (required)
├── package.json        # Dependencies & exports
└── gradio.config.js    # Vite/Svelte customization
```

### Index.svelte — Required Props

```typescript
import type { LoadingStatus } from "@gradio/statustracker";
import type { Gradio } from "@gradio/utils";

export let gradio: Gradio<{ change: never; upload: never }>;
export let elem_id = "";
export let elem_classes: string[] = [];
export let scale: number | null = null;
export let min_width: number | undefined = undefined;
export let loading_status: LoadingStatus | undefined = undefined;
export let mode: "static" | "interactive";
export let value: any;  // Your component's data
export let root: string; // Base URL for file uploads/fetching
```

### Minimal Index.svelte

```svelte
<script lang="ts">
    import { Block } from "@gradio/atoms";
    import { StatusTracker } from "@gradio/statustracker";
    import type { Gradio } from "@gradio/utils";
    import type { LoadingStatus } from "@gradio/statustracker";

    export let gradio: Gradio<{ change: never }>;
    export let value = "";
    export let elem_id = "";
    export let elem_classes: string[] = [];
    export let scale: number | null = null;
    export let min_width: number | undefined = undefined;
    export let loading_status: LoadingStatus | undefined = undefined;
    export let mode: "static" | "interactive";
</script>

<Block {visible} {elem_id} {elem_classes} {scale} {min_width}>
    {#if loading_status}
        <StatusTracker autoscroll={gradio.autoscroll}
            i18n={gradio.i18n} {...loading_status} />
    {/if}
    <p>{value}</p>
</Block>
```

### Example.svelte

```typescript
export let value: string;
export let type: "gallery" | "table";
export let selected = false;
export let index: number;
```

### Interactive vs Static Mode

Gradio uses `mode` prop:
- `"interactive"` — User can change the value (e.g. upload, edit)
- `"static"` — Display only (e.g. output display)

Gradio auto-selects based on whether the component is used as event input.

### File Upload in Frontend

```svelte
<script lang="ts">
    import { upload, prepare_files, type FileData } from "@gradio/client";
    import { Upload, ModifyUpload } from "@gradio/upload";
    import { Empty, UploadText, BlockLabel } from "@gradio/atoms";

    async function handle_upload(files: FileList) {
        let file_data = await prepare_files(Array.from(files));
        file_data = await upload(file_data, root);
        value = file_data[0];
        gradio.dispatch("change");  // Notify backend
    }
</script>

<!-- Upload state -->
<Upload filetype="application/pdf" file_count="single" {root}>
    <UploadText type="file" i18n={gradio.i18n} />
</Upload>

<!-- Loaded state with clear button -->
<ModifyUpload i18n={gradio.i18n} on:clear={() => value = null} />
```

For WASM support, get upload function from Svelte context:
```typescript
import { getContext } from "svelte";
const upload_fn = getContext("upload_files");
await upload(file_data, root, upload_fn);
```

### Leveraging Existing Gradio Packages

| npm Package             | Purpose                        |
|-------------------------|--------------------------------|
| `@gradio/atoms`         | Block, BlockLabel, Empty, etc. |
| `@gradio/statustracker` | StatusTracker, LoadingStatus   |
| `@gradio/utils`         | Gradio, FileData types         |
| `@gradio/client`        | upload, prepare_files          |
| `@gradio/upload`        | Upload, ModifyUpload components|
| `@gradio/icons`         | SVG icon components            |
| `@gradio/button`        | Button component               |

### Vite Customization (`gradio.config.js`)

```javascript
// frontend/gradio.config.js
import tailwindcss from "@tailwindcss/vite";

export default {
    plugins: [tailwindcss()],
    // Svelte options:
    // preprocess: [...],
    // extensions: ['.svx'],
    // build: { target: 'es2022' }
};
```

## Packaging & Configuration

### pyproject.toml

```toml
[project]
name = "gradio_mycomponent"
version = "0.1.0"
description = "My custom Gradio component"
dependencies = ["gradio", "numpy"]

[project.urls]
repository = "https://github.com/user/repo"
space = "https://huggingface.co/spaces/user/demo"

[tool.hatch.build]
artifacts = ["/backend/gradio_mycomponent/templates", "*.pyi"]

[tool.hatch.build.targets.wheel]
packages = ["/backend/gradio_mycomponent"]
```

### Custom Package Name

To change from `gradio_mycomponent` to custom name (e.g. `supertextbox`):

1. Update `name` in `pyproject.toml`
2. Replace all `gradio_mycomponent` references in `pyproject.toml`
3. Rename `backend/gradio_mycomponent/` → `backend/supertextbox/`
4. Update import in `demo/app.py`

### Additional Python Exports

```python
# backend/supertextbox/__init__.py
from .mytextbox import MyTextbox, AdditionalClass, additional_function
__all__ = ['MyTextbox', 'AdditionalClass', 'additional_function']
```

## Case Studies

### 1. PDF Component

- **Template:** None (from scratch with `gradio cc create PDF`)
- **Frontend:** Uses `pdfjs-dist` library for rendering PDF pages onto canvas
- **File handling:** Uses `Upload`/`ModifyUpload` from `@gradio/upload`
- **Backend:** Simple `FileData` data_model, mostly pass-through `preprocess`/`postprocess`
- **Key insight:** CSS variables from Gradio core (`var(--size-60)`, `var(--body-text-color-subdued)`) ensure theme compatibility

### 2. Multimodal Chatbot (Part 1 — Chatbot)

- **Template:** `--template Chatbot`
- **Backend:** Custom `data_model` with `MultimodalMessage(text, files[])` — extends chatbot messages with inline media
- **Frontend:** Modifies `shared/Chatbot.svelte` to loop through message files and render audio/video/image/file links inline
- **Key insight:** Always display text first, then loop through files array — this pattern extends the existing chatbot rendering pipeline

## Documentation Generation

### What gets generated at build time

- Interactive Gradio Space with live demo
- Static README.md with:
  - Description, installation instructions, code snippet
  - API docs: `__init__` argument table, `preprocess`/`postprocess` type signatures
  - Event table with descriptions
  - Links to PyPI, GitHub, HF Space

### To get best docs

1. **Type hints** on `__init__` params, `preprocess` return, `postprocess` input
2. **Docstrings** following Google-style:
   ```python
   def __init__(self, value: str | None = None):
       """
       Parameters:
           value: The initial text value.
       """
   ```
3. **Demo in `demo/app.py`** with `if __name__ == "__main__": demo.launch()`
4. **Compact demo** — minimize extraneous UI, no external dependencies if possible
5. **Events doc** — use `EventListener("name", doc="...")` for custom events
6. **`pyproject.toml` URLs** — `repository` and `space` keys for auto-linking

## Key Insights

1. **`data_model` is the key simplification** — using Pydantic V2 models auto-implements 5+ methods (api_info, flag, read_from_flag, example caching). Always use it unless trivial.
2. **`FileData` is mandatory for file components** — without it, file serving, caching, and client uploads break silently.
3. **The `gradio cc dev` hot reload loop is the fastest dev cycle** — frontend Svelte changes reflect in <1s. Backend changes need a restart but the CLI handles it.
4. **Interactive/Static duality** — every component implicitly has two modes. Handle `mode` prop in frontend for proper behavior.
5. **CSS variables** — use Gradio core variables (`--size-*`, `--body-text-color-subdued`, `--block-label-text-color`, `--color-accent`) for automatic theme compatibility.
6. **Svelte + Gradio packages** — `@gradio/upload` and `@gradio/atoms` provide ready-made building blocks for common patterns (upload UI, layout, status tracking).
7. **npm registry** — all Gradio JS packages published on npm. Find docs at `gradio.app/main/docs/js`.
8. **Storybook** — https://gradio.app/main/docs/js/storybook for component design system reference.
9. **Gradio 4 → 5 migration** — must rebuild components. Update `@gradio/preview` via `npm update`, pin `gradio>=4.0,<6.0` in dependencies.
10. **Zero-cost distribution** — publish to PyPI (free) + HF Spaces demo (free with static CPU Space). No paid accounts required.

---

# HF Learnings — Gradio Workflows Subgraph API & Server-Side Execution (v6.18–6.20)

**Topic:** `gradio-workflows-subgraph-api-deep-dive`
**Date:** 2026-07-25
**Skill:** mlops/gradio-spaces
**Author:** SakThai
**License:** MIT

## Overview

Deep-dive into the Gradio Workflow subgraph execution system, added across v6.18–v6.20. Prior to this, workflow graphs ran only client-side in the browser canvas. The new `WorkflowEndpointManager` (in `gradio/workflow_api.py`) ports the canvas's TypeScript orchestration to Python, exposing each output subject as a regular Gradio API endpoint via the standard `/info` + `/call` machinery.

This enables:
- Running workflows headlessly (programmatic API access, no browser needed)
- Each subgraph (upstream sub-DAG of one output subject) as a named API endpoint
- Live updates — graph edits take effect without server restart
- OAuth token injection for downstream HF Hub API calls

## Architecture

```
Gradio Server
├── gr.Workflow canvas (JS front-end)
│   └── workflow-executor.ts — client-side execution
├── workflow.py — Python Workflow class (high-level API)
│   ├── WorkflowCanvas component (front-end bridge)
│   ├── Curated workflow loading from HF Hub dataset
│   ├── HF search (models, spaces, datasets)
│   └── Server functions: call_space, call_model, call_fn, fetch_dataset
└── workflow_api.py — Server-side execution engine (NEW in v6.19)
    ├── WorkflowGraph — parsed graph model (schema v2)
    ├── WorkflowExecutor — runs upstream sub-DAG for a subject
    ├── WorkflowEndpointManager — registers/manages API endpoints
    └── register_workflow_endpoints() — entry point
```

## Key Components

### 1. WorkflowGraph — Graph Model (`gradio/workflow_api.py`)

Parses a schema-v2 workflow JSON dict with four collections:
- **references** — input nodes, data sources, relays
- **operators** — processing nodes (space, model, fn, dataset)
- **subjects** — output nodes (what the user marked as outputs)
- **edges** — connections between nodes

Only schema v2 graphs are executable server-side (the frontend migrates v1→v2 on load).

```python
graph = WorkflowGraph.from_json(workflow_json)
# graph.references, graph.operators, graph.subjects, graph.edges
```

### 2. Graph Algorithms

**`upstream_node_ids(graph, target_id)`** — BFS traversal backward through edges to find all nodes transitively feeding `target_id`. Mirrors `buildUpstreamSubgraph` in `workflow-graph.ts`.

**`topo_sort(node_ids, edges)`** — Kahn's algorithm for topological ordering. Detects cycles that the canvas normally prevents but hand-edited files could create.

**`free_inputs(graph, subgraph_ids)`** — Identifies which reference nodes in the subgraph have no incoming edge (i.e., user must supply them). Returns them in graph declaration order for deterministic API parameters.

**`subject_groups(graph)`** — Groups subjects by weakly-connected component (undirected edge traversal). Each component becomes ONE API endpoint that returns a tuple of outputs — matching Gradio's multi-output convention.

```python
# One subject → single endpoint
# Two connected subjects → one endpoint returning a tuple
# Two disconnected subjects → two separate endpoints
```

### 3. WorkflowExecutor — Server-Side Execution

`WorkflowExecutor.run(subject_id, inputs, request, token)` executes a single subject's upstream sub-DAG.

`WorkflowExecutor.run_many(subject_ids, inputs, request, token)` executes the combined subgraph for multiple subjects in one pass. **Shared nodes run exactly once** — if two outputs share an intermediate operator, it's computed once and cached in `data_map`.

Execution flow:
1. Build subgraph node set via `upstream_node_ids()`
2. Topological sort via `topo_sort()`
3. Iterate nodes in order:
   - **Reference (free input)**: `_seed_input()` — takes value from user-supplied inputs dict
   - **Reference (relay)**: `_relay()` — passes through incoming value
   - **Subject**: `_relay()` — passes through incoming value to output
   - **Operator (space)**: `_run_space()` — calls external Space API via `call_space()`
   - **Operator (model)**: `_run_model()` — calls HF Inference API via `call_model()`
   - **Operator (fn)**: `_run_fn()` — calls Python function via `call_fn()`
   - **Operator (dataset)**: `_run_dataset()` — fetches from HF Datasets via `fetch_dataset()`

The `callers` dict maps operator kind → server function, injected so they can be mocked in tests.

### 4. WorkflowEndpointManager — API Endpoint Registration

Registered endpoints are **live** — `sync()` tears down old endpoints and rebuilds from the current graph, then refreshes `/config` and invalidates `/info` cache. This lets the API track live canvas edits without server restart.

Key method: `sync()` — safe to call repeatedly:
1. `_teardown()` — unrenders old components, removes old event triggers from `blocks.fns`
2. `_register()` — builds hidden components (rendered in `gr.Column(visible=False)`) and wired `gr.Button.click()` triggers with `api_name=`
3. `_refresh_app()` — regenerates `blocks.config`, invalidates `app.api_info`

```python
# Called on every workflow save
manager.sync()  # returns list of api_names
```

### 5. Input/Output Marshalling

**Port type → Gradio component mapping** (for API schema):

| Port Type      | Gradio Component      |
|----------------|----------------------|
| `"text"`       | `gr.Textbox`         |
| `"number"`     | `gr.Number`          |
| `"boolean"`    | `gr.Checkbox`        |
| `"image"`      | `gr.Image(type="filepath")` |
| `"audio"`      | `gr.Audio(type="filepath")` |
| `"video"`      | `gr.Video`           |
| `"file"`       | `gr.File(type="filepath")`  |
| `"gallery"`    | `gr.Gallery`         |
| `"dataframe"`  | `gr.Dataframe`       |
| `"json"`       | `gr.JSON`            |
| `"model3d"/"3d"` | `gr.Model3D`       |

Media ports (image, audio, video, file, gallery, model3d) travel as `{path|url}` dicts internally — `MEDIA_PORT_TYPES` set in `workflow_api.py`.

### 6. Multi-Output Response Selection

`_pick_response_item()` handles the case where a remote API returns multiple values but a port expects one:
1. Explicit `output_index` if set on the port
2. Positional match (port index matches output array index)
3. Shape-match by port type (find first output matching expected type)
4. Fallback to first output

This mirrors the TypeScript `pick_response_item` in `workflow-executor.ts`.

## API Endpoint Naming

Endpoint names are **derived from subject labels** with slugification:

```python
def _slugify(label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (label or "").strip().lower()).strip("_")
    return slug or "endpoint"
```

Deduplication appends `_`, `__`, etc. when subjects share the same slug.

Examples:
- Subject labeled "Generate Image" → `/generate_image`
- Subject labeled "Output" → `/output`
- Two subjects both labeled "Output" → `/output`, `/output_`

## Workflow Server Functions

The four injected server functions (`callers` dict):

| Kind      | Function         | Purpose                                       |
|-----------|------------------|-----------------------------------------------|
| `space`   | `call_space`     | Call a remote HF Space's API endpoint         |
| `model`   | `call_model`     | Call HF Inference API (text-gen, etc.)        |
| `fn`      | `call_fn`        | Execute a bundled Python function             |
| `dataset` | `fetch_dataset`  | Fetch rows from a HF Dataset                   |

Each receives `(data: list, request, token)` and returns a JSON string (list of outputs or `{"error": ...}` dict).

## Curated Workflow System

The `Workflow` class supports **curated workflows** loaded from a HF Dataset (`gradio/workflow-curated`):

- **Local bundled snapshot**: `_workflow_curated_snapshot.json` in the gradio package
- **Live fetch from Hub**: `_fetch_curated_from_hub()` downloads `curated.json` from the dataset
- **TTL caching**: 3600s cache in `_CURATED_CACHE` dict with threading lock
- **Search integration**: `search_curated()` runs curated workflows through the search system

## v6.18–6.20 Workflow Ecosystem Evolution

### v6.18.0
- **Drag selection** — select multiple nodes in the workflow canvas by dragging
- **Local HF token** — Workflow uses local HF token via write-token auth model
- **Preserve dropdown/radio/checkbox inputs** across workflow edits
- **Optional params don't render nodes** on spawn (cleaner canvas)
- Every component dispatches `change` event on value change

### v6.19.0
- **Subgraph API** — `gr.Workflow` subgraphs run via the Gradio API, each exposed as a named endpoint
- **"View API" panel** — see workflow endpoints in the API browser
- **Runtime language switching** — i18n choices display names update immediately

### v6.20.0
- **Auto-add node** — click on output port to auto-create and wire a compatible node
- **Model validation** — validate model ID before invoking inference client
- **Token injection** — `_token` forwarded to bound functions when no request session
- **Subgraph I/O** — show downstream output on subgraph run
- **Workflow UX** — improved input change handling, pipeline UX

## Key Insights

1. **Subgraphs share execution** — `run_many()` with overlapping upstream nodes executes shared operators once, not once per output. Critical for workflows where a single model feeds multiple output subjects.

2. **Live refresh without restart** — `WorkflowEndpointManager.sync()` tears down old hidden components and rebuilds them, then refreshes `/config` and invalidates `/info` cache. Graph edits are reflected immediately.

3. **Hidden component rendering** — Endpoint components are rendered inside `gr.Column(visible=False)` so they register in the Gradio Blocks dependency graph without appearing in the UI. The column container prevents layout pollution.

4. **Schema v2 only** — Only workflow schema v2 is executable server-side. The frontend auto-migrates v1→v2 on load, so saved files are always v2. `WorkflowGraph.from_json()` returns `None` for non-v2.

5. **Token propagation** — The endpoint function signature auto-injects `request` and `OAuthToken` via `special_args`, which the executor passes down to `call_space` / `call_model` / `call_fn` / `fetch_dataset`.

6. **Five operator kinds** — space, model, fn, dataset + the default "space" fallback for unknown kinds. Each has dedicated `_run_*` method with node-specific input resolution.

7. **Security model** — The endpoint manager uses Gradio's built-in event system (hidden `gr.Button` + `.click()`), inheriting the platform's authentication and rate-limiting.

## When to Use

| Scenario | How |
|----------|-----|
| Headless workflow execution | Call endpoint via `gradio_client.Client` |
| CI/CD pipeline with workflow | Hit `/subgraph_name` programmatically |
| Live workflow as API | Enable workflow + endpoint auto-registers |
| Complex multi-output pipeline | One endpoint per disconnected component |
| Zero-cost deployment | CPU Space (free) with workflow + inference |

## Resources
- Source: `gradio/workflow_api.py` (885 lines) and `gradio/workflow.py` (1880 lines)
- GitHub: https://github.com/gradio-app/gradio
- Gradio Workflows guide: https://www.gradio.app/guides/creating-a-workflow
- Gradio API: https://www.gradio.app/docs/workflow
| Changelog: https://github.com/gradio-app/gradio/blob/main/CHANGELOG.md

---

## 2026-07-25: hf-gradio-6-render-decorator-deep-dive — Gradio 6 `@gr.render()` Decorator: Dynamic Layouts & Reactive Rendering

### Summary
Deep-dive into **Gradio 6's `@gr.render()` decorator** — the reactive rendering system that enables dynamic component layouts in Blocks apps. Unlike traditional Gradio where component trees are declared once at build time, `@gr.render()` re-runs the function body on every input change, rebuilding components and event listeners dynamically. Covers the full API (inputs, triggers, trigger_mode, queue, concurrency), component key preservation (`key` + `preserved_by_key`), event listener keys across re-renders, integration with Sidebar/Navbar components, and five production-worthy patterns for zero-cost Spaces.

### Sources
- Gradio docs — `@gr.render`: https://www.gradio.app/docs/gradio/render
- Gradio docs — Blocks layout: https://www.gradio.app/docs/gradio/blocks
- Gradio docs — Sidebar component: https://www.gradio.app/docs/gradio/sidebar
- Gradio docs — Navbar component: https://www.gradio.app/docs/gradio/navbar
- Gradio docs — Server: https://www.gradio.app/docs/gradio/server
- Gradio source: https://github.com/gradio-app/gradio

---

### 1. What `@gr.render()` Does

`@gr.render()` is a **reactive layout decorator** for Gradio Blocks. It transforms a regular Python function into a dynamically re-rendering UI generator:

```python
import gradio as gr

with gr.Blocks() as demo:
    textbox = gr.Textbox(label="Enter text")
    @gr.render(inputs=textbox)
    def show_message(text):
        if not text:
            gr.Markdown("Please enter some text.")
        else:
            gr.Markdown(f"You entered: **{text}**")
demo.launch()
```

**Key behavior:**
- Every time **any input** changes (or a **trigger** fires), the decorated function is called again
- Inside the function body, components **created each call** replace the previous render's components
- Components created **outside** the `@gr.render()` scope persist across re-renders (static)
- The function receives the **current values** of all inputs as arguments

### 2. Full API Reference

#### `@gr.render(inputs, triggers, queue, trigger_mode, concurrency_limit, concurrency_id, show_progress)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `inputs` | `list[Component] \| Component \| None` | `None` | Input components whose `.change()` triggers re-render. If the function takes no args, use empty list. |
| `triggers` | `list[Trigger] \| Trigger \| None` | `None` | Explicit triggers (e.g. `[btn.click, number.change]`). If `None`, listens to `.change()` of all inputs. |
| `queue` | `bool` | `True` | Whether to place the render on the queue (for rate-limited Spaces). |
| `trigger_mode` | `'once' \| 'multiple' \| 'always_last' \| None` | `'always_last'` | Concurrency for re-renders. `'once'` blocks until complete; `'multiple'` allows concurrent re-renders; `'always_last'` queues subsequent triggers. |
| `concurrency_limit` | `int \| None \| 'default'` | `None` | Max simultaneous render executions. `None` = unlimited. `'default'` = use queue default (typically 1). |
| `concurrency_id` | `str \| None` | `None` | Group this render with other events sharing the same ID for concurrency limiting. |
| `show_progress` | `'full' \| 'minimal' \| 'hidden'` | `'full'` | Progress animation style during re-render. |

#### Trigger Sources

The **`triggers`** parameter is more flexible than inputs alone:

```python
btn = gr.Button("Refresh")
number = gr.Number(value=5)

# Re-render only on button click, not on number change
@gr.render(inputs=number, triggers=[btn.click])
def my_layout(n):
    gr.Markdown(f"Count: {n}")
```

Without `triggers`, the default is `.change()` on all `inputs`. With explicit triggers, you control **exactly** when re-renders fire.

### 3. Component Key Preservation

This is the most nuanced part of `@gr.render()`. Every re-render **replaces all components** in the function body. Without key preservation, user state (text typed, slider position, etc.) is **lost** on every re-render.

#### The `key` Parameter

Each component inside `@gr.render()` can take a `key` parameter:

```python
@gr.render(inputs=items_count)
def dynamic_form(count):
    for i in range(count):
        # key preserves this Textbox across re-renders
        gr.Textbox(label=f"Item {i+1}", key=f"item_{i}")
```

When Gradio re-renders, if a component has the **same key** as one from the previous render, it reuses the DOM node — preserving user input, scroll position, and focus.

**Rules:**
- Keys must be **unique** within a render scope
- Keys are **scoped** to the `@gr.render()` function (two render functions can use the same keys without conflict)
- Keys can be `int`, `str`, or `tuple[int | str, ...]`
- Components without a `key` are **destroyed and recreated** on every render

#### The `preserved_by_key` Parameter

Some component parameters are **not preserved across re-renders** even when `key` is set. Use `preserved_by_key` to whitelist specific parameters:

```python
gr.Textbox(
    value="default",
    label="Name",
    key="name_field",
    preserved_by_key=["value"]  # Keep user-typed value across re-renders
)
```

Without `preserved_by_key=["value"]`, the `value` parameter would be **reset** to `"default"` on every re-render. Only parameters listed in `preserved_by_key` retain user-modified state.

**Supported by:** All components with user-modifiable state (Textbox, Slider, Dropdown, Checkbox, Radio, Number, etc.)

#### Event Listener Key Preservation

Event listeners inside `@gr.render()` can also have keys:

```python
@gr.render(inputs=textbox)
def ui(text):
    btn = gr.Button("Submit", key="submit_btn")
    output = gr.Textbox(label="Result", key="output")

    btn.click(
        fn=handle_submit,
        inputs=textbox,
        outputs=output,
        key="submit_event"  # Preserves this listener across re-renders
    )
```

The `key` on `.click()` (and other event listeners) ensures the event binding persists across re-renders, preventing stale closures and double-binding.

### 4. Integration with New Gradio 6 Components

#### `gr.Sidebar` Inside Render

Sidebar can be used within `@gr.render()` for dynamic collapsible panels:

```python
with gr.Blocks() as demo:
    mode = gr.Radio(["simple", "advanced"], label="Mode", value="simple")

    @gr.render(inputs=mode)
    def dynamic_sidebar(mode):
        with gr.Sidebar(position="left", open=True):
            gr.Markdown("## Controls")
            if mode == "advanced":
                gr.Slider(0, 1, value=0.5, label="Threshold")
                gr.Checkbox(label="Normalize")
            else:
                gr.Number(value=42, label="Value")
        gr.Markdown("## Main Content")
        gr.Textbox(label="Result")
```

Sidebar inside `@gr.render()` enables context-sensitive control panels that morph based on user selection.

#### `gr.Navbar` and Multipage with Render

Navbar + Render = dynamic page routing:

```python
with gr.Blocks() as demo:
    page_state = gr.State("home")

    with gr.Row():
        home_btn = gr.Button("Home")
        about_btn = gr.Button("About")

    @gr.render(inputs=page_state, triggers=[home_btn.click, about_btn.click])
    def router(page):
        if page == "home":
            gr.Markdown("# Home Page")
            gr.Textbox(label="Search")
        elif page == "about":
            gr.Markdown("# About Page")
            gr.HTML("<p>Version 1.0</p>")
```

This pattern enables **SPA-like routing** in Gradio without page reloads — all state lives in memory.

### 5. Five Production Patterns

#### Pattern 1: Configurable Form Builder

```python
@gr.render(inputs=field_count)
def build_form(n):
    fields = []
    for i in range(n):
        t = gr.Textbox(label=f"Field {i+1}", key=f"field_{i}")
        fields.append(t)
    submit = gr.Button("Submit", key="submit_btn")
    output = gr.JSON(label="Output", key="output")

    submit.click(
        lambda *vals: {f"field_{i}": v for i, v in enumerate(vals)},
        inputs=fields,
        outputs=output,
        key="submit_action"
    )
```

#### Pattern 2: Multi-Step Wizard

```python
@gr.render(inputs=step)
def wizard(step):
    if step == 1:
        gr.Markdown("### Step 1: Name")
        name = gr.Textbox(label="Your name", key="name")
        next_btn = gr.Button("Next", key="next1")
        next_btn.click(lambda: 2, None, step, key="go_step2")
    elif step == 2:
        gr.Markdown("### Step 2: Confirm")
        gr.Markdown(f"Name: {name.value}")
        back = gr.Button("Back", key="back2")
        confirm = gr.Button("Confirm", key="confirm2")
        back.click(lambda: 1, None, step, key="back_step1")
        confirm.click(lambda: 3, None, step, key="go_step3")
```

**Note:** Accessing `name.value` across renders requires `key` preservation + `gr.State` or storing values outside render scope.

#### Pattern 3: Live Data Dashboard

```python
@gr.render(inputs=refresh_btn, triggers=[refresh_btn.click])
def dashboard():
    import json, urllib.request
    data = json.loads(urllib.request.urlopen("https://api.example.com/status").read())
    gr.Number(value=data["cpu"], label="CPU %", key="cpu")
    gr.Number(value=data["memory"], label="Memory %", key="mem")
    gr.JSON(value=data, label="Full", key="full")
```

Re-render on button click fetches fresh data and rebuilds the dashboard.

#### Pattern 4: Dynamic Chat Interface Overlay

```python
@gr.render(inputs=use_chat)
def chat_or_form(use_chat):
    if use_chat:
        gr.ChatInterface(fn=chat_fn, key="chat")
    else:
        gr.Textbox(label="Message", key="msg")
        gr.Button("Send", key="send")
```

#### Pattern 5: Conditional Sidebar Configuration

```python
@gr.render(inputs=config_mode)
def config_panel(mode):
    with gr.Sidebar(position="left", open=mode != "view"):
        gr.Markdown(f"### {mode.title()} Mode")
        if mode == "edit":
            gr.Textbox(label="Title", key="title")
            gr.ColorPicker(label="Color", key="color")
        elif mode == "view":
            gr.Markdown("Read-only mode — click Edit to change")
```

### 6. Zero-Cost Deployment Considerations

For free CPU Spaces:

| Concern | Mitigation |
|---------|-----------|
| **Frequent re-renders** — each re-render re-executes the function | Keep render functions lightweight; move heavy computation outside (use `gr.State` or cached helpers) |
| **Queue pressure** — queued renders compete with other events | Set `concurrency_limit=1` and `trigger_mode='always_last'` to drop stale renders |
| **Component count** — many components per render increases memory | Use `key` + `.unrender()` patterns; Gradio reuses DOM nodes with keys |
| **Sidebar inside render** — Sidebar animation on every re-render | Keep Sidebar outside render if it doesn't change; only wrap the inner content |
| **State loss** — re-render resets component values | Always use `preserved_by_key` on user-modifiable components |

### 7. Render vs. `gr.on` / `change()` — When to Use Which

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| `@gr.render()` | Dynamic component **count**, structure, layout | Re-runs entire function; higher overhead |
| `gr.on(...).then(...)` | Single value **updates** without layout change | Only updates outputs; can't add/remove components |
| `component.change(fn, ...)` | Individual component reactivity | Manual wiring; no structural changes |
| `gr.Blocks.load()` | Initial layout setup only | Runs once at app start |

**Rule of thumb:** If you need to **show/hide** or **add/remove** components, use `@gr.render()`. If you just need to update values, use `.change()` or `gr.on()`.

### 8. Known Limitations (Gradio 6.20)

1. **No async render functions** — The decorated function cannot be `async def`. For async work, move awaits inside a sync wrapper.
2. **One render function per `inputs` scope** — You CAN have multiple `@gr.render()` functions in the same Blocks app, but each must have distinct inputs/triggers.
3. **`gr.State` inside render** — `gr.State` declared inside `@gr.render()` is recreated on each render. Declare persistent state **outside** the render scope.
4. **No streaming outputs inside render** — `gr.Chatbot` with streaming works, but `gr.Textbox` with `streaming=True` inside render may conflict with re-render.
5. **SSR / Gradio Lite** — `@gr.render()` works in Gradio Lite (Pyodide/WASM) but re-render performance depends on browser memory.

### Resources
- Gradio render docs: https://www.gradio.app/docs/gradio/render
- Gradio Source: https://github.com/gradio-app/gradio
- Gradio Blocks guide: https://www.gradio.app/guides/blocks-and-event-listeners
- Dynamic apps guide: https://www.gradio.app/guides/dynamic-apps-with-the-render-decorator
- Sidebar docs: https://www.gradio.app/docs/gradio/sidebar
- Navbar docs: https://www.gradio.app/docs/gradio/navbar
