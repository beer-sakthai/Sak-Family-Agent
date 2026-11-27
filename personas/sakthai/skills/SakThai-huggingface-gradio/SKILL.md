---
name: SakThai-huggingface-gradio
version: 1.0.0
description: Build Gradio web UIs and demos in Python. Use when creating or editing
  Gradio apps, components, event listeners, layouts, or chatbots.
category: mlops
tags:
- components
- customization
- deep
- dive
- gradio
- hf
- huggingface
- media
- mode
- native
- plot
- server
- theme
---

# Gradio

Gradio is a Python library for building interactive web UIs and ML demos. This skill covers the core API, patterns, and examples.

## Guides

Detailed guides on specific topics (read these when relevant):

- [Quickstart](https://www.gradio.app/guides/quickstart)
- [The Interface Class](https://www.gradio.app/guides/the-interface-class)
- [Blocks and Event Listeners](https://www.gradio.app/guides/blocks-and-event-listeners)
- [Controlling Layout](https://www.gradio.app/guides/controlling-layout)
- [More Blocks Features](https://www.gradio.app/guides/more-blocks-features)
- [Custom CSS and JS](https://www.gradio.app/guides/custom-CSS-and-JS)
- [Streaming Outputs](https://www.gradio.app/guides/streaming-outputs)
- [Streaming Inputs](https://www.gradio.app/guides/streaming-inputs)
- [Sharing Your App](https://www.gradio.app/guides/sharing-your-app)
- [Custom HTML Components](https://www.gradio.app/guides/custom-HTML-components)
- [Getting Started with the Python Client](https://www.gradio.app/guides/getting-started-with-the-python-client)
- [Getting Started with the JS Client](https://www.gradio.app/guides/getting-started-with-the-js-client)

## Core Patterns

**Interface** (high-level): wraps a function with input/output components.

```python
import gradio as gr

def greet(name):
    return f"Hello {name}!"

gr.Interface(fn=greet, inputs="text", outputs="text").launch()
```

**Blocks** (low-level): flexible layout with explicit event wiring.

```python
import gradio as gr

with gr.Blocks() as demo:
    name = gr.Textbox(label="Name")
    output = gr.Textbox(label="Greeting")
    btn = gr.Button("Greet")
    btn.click(fn=lambda n: f"Hello {n}!", inputs=name, outputs=output)

demo.launch()
```

**ChatInterface**: high-level wrapper for chatbot UIs.

```python
import gradio as gr

def respond(message, history):
    return f"You said: {message}"

gr.ChatInterface(fn=respond).launch()
```

## Key Components

The most common Gradio components include:

| Component | Description | Primary Use |
|---|---|---|
| `gr.Textbox` | Text area for string input/output | Prompts, chat inputs, string responses |
| `gr.Number` | Numeric field for float/int | Parameter adjustments, counts |
| `gr.Slider` | Bounded range slider | Temperature, top-p, epoch counts |
| `gr.Checkbox` | Boolean toggle | Flags, settings switches |
| `gr.Dropdown` | Single or multi-choice dropdown | Model selection, sampler options |
| `gr.Radio` | Single choice radio list | Modes, categories |
| `gr.Image` | Upload, webcam, clipboard image I/O | Vision models, diffusion generators |
| `gr.Audio` | Microphone or upload audio I/O | Whisper, speech synthesis, TTS |
| `gr.Video` | Webcam or upload video I/O | Video generation, frame analysis |
| `gr.File` | Generic file upload / download | Weights, documents, export archives |
| `gr.Chatbot` | Conversational message history display | LLM assistants, chat agents |
| `gr.Button` | Trigger for event listeners (`.click()`) | Submit, clear, regenerate actions |
| `gr.Markdown` | Rendered markdown display | Explanations, system info |
| `gr.HTML` | Custom raw HTML rendering | Embeds, visualizations |

---

## Deep Dive References

For exhaustive reference specifications, cookbook snippets, and extended documentation:
- [Gradio Component Parameter Signatures](./references/gradio-component-signatures.md)
- [Gradio Custom Components, Listeners & CLI Reference](./references/gradio-custom-components-and-cli.md)

