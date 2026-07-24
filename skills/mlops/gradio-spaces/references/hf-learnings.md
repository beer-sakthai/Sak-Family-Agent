# HF Learnings — Gradio 6: `@gr.render` Decorator & Streaming Patterns

**Topic:** `hf-gradio-6-render-and-streaming-deep-dive`
**Date:** 2026-07-24
**Skill:** mlops/gradio-spaces
**Author:** SakThai
**License:** MIT

## Overview

Deep-dive into three major Gradio 6 features that transform how dynamic UIs and chatbots are built:
1. **`@gr.render` decorator** — dynamic creation/removal of components and event listeners at runtime
2. **Streaming generators** — token-by-token streaming via `yield` in chat functions
3. **`gr.ChatInterface` v2** — multimodal support, additional inputs/outputs, `gr.load_chat`

These are sourced from the official Gradio docs (guides/03_building-with-blocks/04_dynamic-apps-with-render-decorator.md and guides/05_chatbots/01_creating-a-chatbot-fast.md on Gradio main branch, mid-2026).

---

## 1. The `@gr.render` Decorator

Introduced in Gradio 6, `@gr.render` lets you create and destroy components and event listeners dynamically at runtime based on state changes.

### Basic Pattern

```python
import gradio as gr

with gr.Blocks() as demo:
    input_text = gr.Textbox(label="Type something")
    
    @gr.render(inputs=[input_text])
    def render_ui(text):
        """Creates one Textbox per character in the input."""
        for char in text:
            gr.Textbox(value=char, label=f"Char: '{char}'")
```

**How it works:**
1. Decorate a function with `@gr.render(inputs=[...])`
2. The function runs automatically when any input component changes
3. All components created *inside* the function are rendered in order where the `@gr.render` is placed
4. On re-render, all previously rendered components are replaced with new ones
5. The `.load` listener and `.change` listener on inputs trigger re-renders by default

### Custom Triggers

Override the default trigger to only re-render on specific events:

```python
with gr.Blocks() as demo:
    input_text = gr.Textbox(label="Enter text")
    submit_btn = gr.Button("Submit")
    
    @gr.render(inputs=[input_text], triggers=[submit_btn.click])
    def render_on_submit(text):
        """Only renders when Submit is clicked, not on every keystroke."""
        gr.Markdown(f"**You submitted:** {text}")
        gr.Textbox(value=f"Length: {len(text)}", label="Analysis")
```

**Important:** If using custom triggers and you want an initial render on page load, add `demo.load` to the trigger list:
```python
@gr.render(inputs=[...], triggers=[submit_btn.click, demo.load])
```

### Preserving Component State with `key=`

When components are re-rendered, their state is lost unless you assign a `key=`:

```python
with gr.Blocks() as demo:
    add_btn = gr.Button("Add Textbox")
    text_count = gr.State(0)
    
    @gr.render(inputs=[text_count])
    def render_textboxes(count):
        textboxes = []
        for i in range(count):
            tb = gr.Textbox(label=f"Textbox {i+1}", key=f"tb_{i}")
            textboxes.append(tb)
        
        merge_btn = gr.Button("Merge", key="merge_btn")
        output = gr.Textbox(label="Merged Output")
        
        def merge(*values):
            return " | ".join(values)
        
        merge_btn.click(
            merge, inputs=textboxes, outputs=output, key="merge_handler"
        )
    
    add_btn.click(
        lambda c: c + 1, inputs=text_count, outputs=text_count
    )
```

**Key rules for `key=`**:
- Components with the same `key=` across re-renders preserve their values
- Parent layout elements (e.g., nested `gr.Row`) must also be keyed consistently
- Event listeners can also be keyed: `button.click(key='my_handler')` — prevents issues when events finish processing after a re-render
- Without `key=`, all component values reset on every re-render

### Dynamic Event Listeners Inside Render

Event listeners that reference components created within a render function **must also be defined inside that function**:

```python
@gr.render(inputs=[text_count])
def render_textboxes(count):
    textboxes = []
    for i in range(count):
        tb = gr.Textbox(label=f"Textbox {i+1}", key=f"tb_{i}")
        textboxes.append(tb)
    
    merge_btn = gr.Button("Merge")
    output = gr.Textbox(label="Output")  # defined outside = accessible
    
    def merge(*values):
        return " | ".join(values)
    
    # listener INSIDE the render function — OK
    merge_btn.click(merge, textboxes, output)
```

### Render with State Variables

When reacting to a list/dict state variable:

```python
@gr.render(inputs=[tasks_state])
def render_todo(tasks):
    """Renders a to-do list from a state variable."""
    for i, task in enumerate(tasks):
        with gr.Row(key=f"row_{i}"):
            gr.Markdown(f"- {task['text']}", key=f"md_{i}")
            done_btn = gr.Button("✓", key=f"done_{i}")
            del_btn = gr.Button("✗", key=f"del_{i}")
            
            # FREEZE the loop variable with default argument
            done_btn.click(
                lambda task=task: mark_done(task), 
                None, tasks_state
            )
            del_btn.click(
                lambda task=task: delete_task(task), 
                None, tasks_state
            )
```

**Critical pattern:** Use `task=task` as default argument to "freeze" loop variables — without this, all listeners capture the *last* iteration's value.

---

## 2. Streaming Chatbots with Generators

Gradio 6 streams chatbot responses token-by-token when your chat function uses `yield`.

### Simple Streaming

```python
import time
import gradio as gr

def slow_echo(message, history):
    for i in range(len(message)):
        time.sleep(0.3)
        yield "You typed: " + message[: i+1]

gr.ChatInterface(
    fn=slow_echo, 
).launch()
```

**How it works:**
- Each `yield` replaces the previous response in the chatbot UI
- Gradio sends only the "diff" between yields over the network (reduces latency/data)
- The Submit button turns into a Stop button during streaming — users can cancel mid-generation

### Streaming with Additional Inputs

```python
def echo(message, history, system_prompt, tokens):
    response = f"System: {system_prompt}\nMessage: {message}"
    for i in range(min(len(response), int(tokens))):
        time.sleep(0.05)
        yield response[: i+1]

with gr.Blocks() as demo:
    system_prompt = gr.Textbox("You are helpful AI.", label="System Prompt")
    slider = gr.Slider(10, 100, render=False)
    
    gr.ChatInterface(
        echo, 
        additional_inputs=[system_prompt, slider],
    )
```

### Streaming Audio Responses

Gradio 6 supports streaming audio output with `gr.Audio(streaming=True, autoplay=True)`:

```python
def response(state: AppState):
    """Stream audio chunks as they're generated."""
    for mp3_bytes in speaking(audio_buffer.getvalue()):
        yield mp3_bytes, state  # yields audio chunk + updated state
```

Combined with `input_audio.stream()` for continuous audio capture:

```python
stream = input_audio.stream(
    process_audio,
    [input_audio, state],
    [input_audio, state],
    stream_every=0.5,    # capture in 0.5s chunks
    time_limit=30,
)
```

---

## 3. `gr.ChatInterface` v2 (Gradio 6)

### Multimodal Chat

`multimodal=True` enables file uploads (images, audio, video, documents):

```python
def count_images(message, history):
    num_images = len(message["files"])
    total_images = 0
    for msg in history:
        for content in msg["content"]:
            if content["type"] == "file":
                total_images += 1
    return f"You just uploaded {num_images} images, total: {total_images+num_images}"

demo = gr.ChatInterface(
    fn=count_images, 
    multimodal=True,
    textbox=gr.MultimodalTextbox(
        file_count="multiple", 
        file_types=["image"], 
        sources=["upload", "microphone"]
    )
)
```

**Message format with multimodal:**
```python
# The `message` parameter becomes a dict:
{
    "text": "user input", 
    "files": [
        "path/to/uploaded_file1.jpg",
        "path/to/uploaded_file2.pdf", 
    ]
}

# History uses OpenAI-style format:
[
    {"role": "user", "content": [
        {"type": "file", "file": {"path": "image.png"}},
        {"type": "text", "text": "What's in this image?"}
    ]},
    {"role": "assistant", "content": [
        {"type": "text", "text": "I see a cat."}
    ]}
]
```

### Additional Outputs

Return multiple values to update separate components:

```python
def chat_fn(message, history):
    response = "Some text with ```python\nprint('hello')\n``` code"
    code_block = "print('hello')"
    yield response, code_block  # updates chatbot + code component

with gr.Blocks() as demo:
    code_output = gr.Code(label="Extracted Code")
    
    gr.ChatInterface(
        chat_fn,
        additional_outputs=[code_output],
    )
```

### `gr.load_chat` — Instant OpenAI-Compatible Endpoint

One-line chatbot for any OpenAI-compatible API (Ollama, vLLM, etc.):

```python
import gradio as gr
gr.load_chat(
    "http://localhost:11434/v1/",  # Ollama endpoint
    model="llama3.2",
    token="***"  # optional
).launch()
```

Also works with hosted providers by setting the token parameter.

### Returning Complex Types from Chat

Beyond strings, these Gradio components can be returned inside chat messages:

| Component | Use Case |
|-----------|----------|
| `gr.Image` | Generated/analyzed images |
| `gr.Audio` | Spoken responses, audio clips |
| `gr.Video` | Generated video clips |
| `gr.File` | Document downloads |
| `gr.Plot` | Matplotlib/Plotly charts |
| `gr.HTML` | Custom rendered HTML |
| `gr.Gallery` | Multiple images |

**Example — returning an image in chat:**
```python
def chat_response(message, history):
    # Generate an image
    img_path = generate_image(message)
    return gr.Image(value=img_path)
```

---

## 4. Event Data & Validation

### Gathering Event Data

Use `gr.SelectData` to capture what the user selected:

```python
with gr.Blocks() as demo:
    textbox = gr.Textbox("The quick brown fox jumped.")
    output = gr.Textbox(label="Selected Text")
    
    def show_selection(evt: gr.SelectData):
        return f"Selected: '{evt.value}' at index {evt.index}"
    
    textbox.select(show_selection, None, output)
```

### Input Validation with `validator`

```python
with gr.Blocks() as demo:
    age = gr.Number(label="Age", value=25)
    name = gr.Textbox(label="Name")
    submit = gr.Button("Submit")
    output = gr.Textbox(label="Result")
    
    def process(age, name):
        return f"Hello {name}, age {age}"
    
    def validate(age, name):
        errors = []
        if age < 0 or age > 150:
            errors.append(gr.validate(False, "Age must be 0-150"))
        else:
            errors.append(gr.validate(True))
        if len(name.strip()) == 0:
            errors.append(gr.validate(False, "Name is required"))
        else:
            errors.append(gr.validate(True))
        return errors
    
    submit.click(
        process, [age, name], output,
        validator=validate
    )
```

**Benefits of validator:**
- Runs immediately, bypasses queue — near-instant feedback
- Returns validation status per input (granular control)
- Errors displayed differently in UI vs generic exceptions

### Timer-Based Events

```python
with gr.Blocks() as demo:
    timer = gr.Timer(5)  # fires every 5 seconds
    timestamp = gr.Textbox(label="Current Time")
    
    def update_time():
        import datetime
        return str(datetime.datetime.now())
    
    timer.tick(update_time, None, timestamp)
```

Or use `every=` on a component:
```python
timer = gr.Timer(5)
textbox = gr.Textbox(update_time, inputs=[], every=timer)
```

---

## 5. Zero-Cost Patterns for Gradio 6 on HF Spaces

1. **CPU Spaces are free** — All Gradio 6 features work on free CPU hardware
2. **Streaming reduces perceived latency** — Yield partial responses immediately instead of waiting for full generation
3. **`gr.load_chat` with local endpoints** — Point to a free Ollama instance running in a separate Space or locally
4. **`@gr.render` for memory efficiency** — Only render what's needed, reduce DOM size on long conversations
5. **Multimodal with small models** — Use free HF Inference API models (e.g., Phi-4, Llama 3.2 Vision) for image analysis
6. **`gr.Timer` for auto-refresh** — Poll free data sources without JS

---

## Source Code References

- `@gr.render`: Gradio Python source — `gradio/blocks.py` (BlockContext._render)
- `gr.ChatInterface`: `gradio/chat_interface.py`
- `gr.load_chat`: `gradio/chat_interface.py` — wraps OpenAI-compatible API
- `gr.SelectData`: `gradio/event_data.py`
- `gr.validate`: `gradio/validation.py`
- `gr.Timer`: `gradio/timer.py`

## Resources

- [Dynamic Apps with Render Decorator](https://www.gradio.app/guides/dynamic-apps-with-render-decorator)
- [Creating a Chatbot Fast](https://www.gradio.app/guides/creating-a-chatbot-fast)
- [ChatInterface Examples](https://www.gradio.app/guides/chatinterface-examples)
- [Building Conversational Chatbots](https://www.gradio.app/guides/building-conversational-chatbots-with-gradio)
- [Gradio API Reference](https://www.gradio.app/docs/gradio/chatinterface)
