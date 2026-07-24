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
9. **`GRADIO_DEFAULT_CONCURRENCY_LIMIT`** env var sets the default before your code runs.
10. **Cache bypasses queue** — `@gr.Cache()` is free and fast for repeated requests.
