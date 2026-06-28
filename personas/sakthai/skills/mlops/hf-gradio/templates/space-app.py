"""Minimal Gradio 6 template for Hugging Face Spaces."""
import gradio as gr


def predict(text: str) -> str:
    return f"Processed: {text}"


demo = gr.Interface(
    fn=predict,
    inputs=gr.Textbox(label="Input", lines=3),
    outputs=gr.Markdown(label="Output"),
    title="Minimal Gradio 6 Demo",
    description="A simple demo ready for Hugging Face Spaces.",
)

if __name__ == "__main__":
    demo.launch()
