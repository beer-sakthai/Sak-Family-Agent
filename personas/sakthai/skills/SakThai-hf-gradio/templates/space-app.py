"""Gradio 6 production template for Hugging Face Spaces.

Features:
  - Gradio 6 app-level config (theme, css in launch())
  - Queue with concurrency control
  - SSR (server-side rendering) support
  - Authentication via HF OAuth
  - ChatInterface example (for LLM demos)
  - Blocks example with state
  - Health-check endpoint

Usage:
  1. Copy this file to app.py in your HF Space repo.
  2. Adjust the pinned Gradio version in space-requirements.txt.
  3. Set HF_TOKEN in Space secrets if using authenticated HF Hub calls.
  4. Deploy — Space hardware: CPU free tier works for most demos.
"""

from __future__ import annotations

import os

import gradio as gr

# ── Configuration ──────────────────────────────────────────────────
TITLE = "SakThai Gradio 6 Demo"
DESCRIPTION = "Production-ready Gradio 6 template for Hugging Face Spaces."
THEME = gr.themes.Soft()            # Also: Default(), Monochrome(), Ocean(), Citrus()
CSS = ""                            # Inline CSS or path to a .css file
ALLOW_FLAGGING = "manual"           # "manual" | "never" | "auto"
SERVING_MODE = "interface"          # "interface" | "blocks" | "chatinterface"

# ── Core function (shared by all UIs) ─────────────────────────────

def process_input(text: str, slider: float = 0.5) -> str:
    """Process user input and return a response.

    Args:
        text: User-provided text.
        slider: Confidence / temperature / scaling slider value.

    Returns:
        Markdown-formatted output string.
    """
    if not text.strip():
        return "⚠️ Please enter some text."
    return (
        f"**You said:** {text}\n\n"
        f"**Slider value:** {slider:.2f}\n\n"
        f"**Processed at:** `{os.environ.get('SPACE_HOST', 'localhost')}`"
    )

def chat_response(message: str, history: list) -> str:
    """Simple chat function for ChatInterface.

    Replace this with your actual LLM call (transformers, OpenAI client, etc.).
    """
    return f"Echo: {message}"


# ── Interface mode (gr.Interface) ─────────────────────────────────

def build_interface() -> gr.Interface:
    return gr.Interface(
        fn=process_input,
        inputs=[
            gr.Textbox(label="Input Text", lines=3, placeholder="Type here..."),
            gr.Slider(0.0, 1.0, value=0.5, label="Parameter", step=0.05),
        ],
        outputs=gr.Markdown(label="Output"),
        title=TITLE,
        description=DESCRIPTION,
        allow_flagging=ALLOW_FLAGGING,
        api_name="predict",                     # → /predict endpoint
        examples=[
            ["Hello from Gradio 6!", 0.7],
            ["Test message", 0.3],
        ],
    )


# ── Blocks mode (gr.Blocks) ───────────────────────────────────────

def build_blocks() -> gr.Blocks:
    """Tabbed Blocks UI with state and multi-step workflow."""
    with gr.Blocks(title=TITLE, fill_height=True) as demo:
        gr.Markdown(f"# {TITLE}")
        gr.Markdown(DESCRIPTION)

        with gr.Tabs():
            with gr.Tab("Main"):
                with gr.Row():
                    with gr.Column(scale=2):
                        text_input = gr.Textbox(
                            label="Input", lines=3, placeholder="Type here..."
                        )
                    with gr.Column(scale=1):
                        slider = gr.Slider(0.0, 1.0, value=0.5, label="Parameter")

                submit_btn = gr.Button("Submit", variant="primary")
                output = gr.Markdown(label="Output")

                with gr.Accordion("Advanced Settings", open=False):
                    gr.Markdown("Set environment variables under Space settings → Secrets.")
                    debug_cb = gr.Checkbox(label="Enable debug logging", value=False)

                submit_btn.click(
                    fn=process_input,
                    inputs=[text_input, slider],
                    outputs=output,
                    api_name="predict_blocks",
                    queue=True,
                )

            with gr.Tab("Chat"):
                gr.ChatInterface(
                    fn=chat_response,
                    title="Chatbot",
                    description="Simple echo chatbot — replace with your model.",
                )

        # Footer with API docs link
        gr.Markdown(
            "---\n"
            "🤗 [Deploy on HF Spaces](https://huggingface.co/new-space)  |  "
            "📖 [Gradio 6 Docs](https://www.gradio.app/docs/gradio/blocks)"
        )

    return demo


# ── ChatInterface mode (gr.ChatInterface) ──────────────────────────

def build_chatinterface() -> gr.ChatInterface:
    return gr.ChatInterface(
        fn=chat_response,
        title=TITLE,
        description=DESCRIPTION,
        chatbot=gr.Chatbot(height=450, placeholder="Chat with me!"),
        textbox=gr.Textbox(placeholder="Type your message...", scale=7),
        examples=["Hello!", "What can you do?", "Tell me a joke"],
        cache_examples=True,
        save_history=True,                      # Persist conversations in browser
    )


# ── Build and launch ──────────────────────────────────────────────

if SERVING_MODE == "blocks":
    demo = build_blocks()
elif SERVING_MODE == "chatinterface":
    demo = build_chatinterface()
else:
    demo = build_interface()

if __name__ == "__main__":
    pass
    # ── Gradio 6: theme & css go in launch(), not in the constructor ──
    demo.launch(
        theme=THEME,
        css=CSS,
        # ── Server-side rendering (SSR) ──────────────────────────
        # Space default: True.  Local default: False.
        # ssr_mode=True,
        # ── Queue config ─────────────────────────────────────────
        # Controls concurrent user requests.  Increase for heavy models.
        # concurrency_limit=5,
        # ── Authentication (HF OAuth) ────────────────────────────
        # auth=gr.oauth().  Requires Space secrets to include
        # OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET.
        # auth=gr.oauth(),
        # ── MCP server (expose functions as MCP tools) ────────────
        # mcp_server=True,
        # ── API visibility ───────────────────────────────────────
        # footer_links=["api", "gradio", "settings"],
        # ── Show API docs ────────────────────────────────────────
        show_api=True,
    )
