# Gradio Custom Components, Listeners & CLI Reference

If a task requires significant customization of an existing component or a component that doesn't exist in Gradio, you can create one with `gr.HTML`. It supports `html_template` (with `${}` JS expressions and `{{}}` Handlebars syntax), `css_template` for scoped styles, and `js_on_load` for interactivity — where `props.value` updates the component value and `trigger('event_name')` fires Gradio events. For reuse, subclass `gr.HTML` and define `api_info()` for API/MCP support. See the [full guide](https://www.gradio.app/guides/custom-HTML-components).

Here's an example that shows how to create and use these kinds of components:

```python
import gradio as gr

class StarRating(gr.HTML):
    def __init__(self, label, value=0, **kwargs):
        html_template = """
        <h2>${label} rating:</h2>
        ${Array.from({length: 5}, (_, i) => `<img class='${i < value ? '' : 'faded'}' src='https://upload.wikimedia.org/wikipedia/commons/d/df/Award-star-gold-3d.svg'>`).join('')}
        """
        css_template = """
            img { height: 50px; display: inline-block; cursor: pointer; }
            .faded { filter: grayscale(100%); opacity: 0.3; }
        """
        js_on_load = """
            const imgs = element.querySelectorAll('img');
            imgs.forEach((img, index) => {
                img.addEventListener('click', () => {
                    props.value = index + 1;
                });
            });
        """
        super().__init__(value=value, label=label, html_template=html_template, css_template=css_template, js_on_load=js_on_load, **kwargs)

    def api_info(self):
        return {"type": "integer", "minimum": 0, "maximum": 5}


with gr.Blocks() as demo:
    gr.Markdown("# Restaurant Review")
    food_rating = StarRating(label="Food", value=3)
    service_rating = StarRating(label="Service", value=3)
    ambience_rating = StarRating(label="Ambience", value=3)
    average_btn = gr.Button("Calculate Average Rating")
    rating_output = StarRating(label="Average", value=3)
    def calculate_average(food, service, ambience):
        return round((food + service + ambience) / 3)
    average_btn.click(
        fn=calculate_average,
        inputs=[food_rating, service_rating, ambience_rating],
        outputs=rating_output
    )

demo.launch()
```

## Event Listeners

All event listeners share the same signature:

```python
component.event_name(
    fn: Callable | None | Literal["decorator"] = "decorator",
    inputs: Component | Sequence[Component] | set[Component] | None = None,
    outputs: Component | Sequence[Component] | set[Component] | None = None,
    api_name: str | None = None,
    api_description: str | None | Literal[False] = None,
    scroll_to_output: bool = False,
    show_progress: Literal["full", "minimal", "hidden"] = "full",
    show_progress_on: Component | Sequence[Component] | None = None,
    queue: bool = True,
    batch: bool = False,
    max_batch_size: int = 4,
    preprocess: bool = True,
    postprocess: bool = True,
    cancels: dict[str, Any] | list[dict[str, Any]] | None = None,
    trigger_mode: Literal["once", "multiple", "always_last"] | None = None,
    js: str | Literal[True] | None = None,
    concurrency_limit: int | None | Literal["default"] = "default",
    concurrency_id: str | None = None,
    api_visibility: Literal["public", "private", "undocumented"] = "public",
    time_limit: int | None = None,
    stream_every: float = 0.5,
    key: int | str | tuple[int | str, ...] | None = None,
    validator: Callable | None = None,
) -> Dependency
```

Supported events per component:

- **AnnotatedImage**: select
- **Audio**: stream, change, clear, play, pause, stop, pause, start_recording, pause_recording, stop_recording, upload, input
- **BarPlot**: select, double_click
- **BrowserState**: change
- **Button**: click
- **Chatbot**: change, select, like, retry, undo, example_select, option_select, clear, copy, edit
- **Checkbox**: change, input, select
- **CheckboxGroup**: change, input, select
- **ClearButton**: click
- **Code**: change, input, focus, blur
- **ColorPicker**: change, input, submit, focus, blur
- **Dataframe**: change, input, select, edit
- **Dataset**: click, select
- **DateTime**: change, submit
- **DeepLinkButton**: click
- **Dialogue**: change, input, submit
- **DownloadButton**: click
- **Dropdown**: change, input, select, focus, blur, key_up
- **DuplicateButton**: click
- **File**: change, select, clear, upload, delete, download
- **FileExplorer**: change, input, select
- **Gallery**: select, upload, change, delete, preview_close, preview_open
- **HTML**: change, input, click, double_click, submit, stop, edit, clear, play, pause, end, start_recording, pause_recording, stop_recording, focus, blur, upload, release, select, stream, like, example_select, option_select, load, key_up, apply, delete, tick, undo, retry, expand, collapse, download, copy
- **HighlightedText**: change, select
- **Image**: clear, change, stream, select, upload, input
- **ImageEditor**: clear, change, input, select, upload, apply
- **ImageSlider**: clear, change, stream, select, upload, input
- **JSON**: change
- **Label**: change, select
- **LinePlot**: select, double_click
- **LoginButton**: click
- **Markdown**: change, copy
- **Model3D**: change, upload, edit, clear
- **MultimodalTextbox**: change, input, select, submit, focus, blur, stop
- **Navbar**: change
- **Number**: change, input, submit, focus, blur
- **ParamViewer**: change, upload
- **Plot**: change
- **Radio**: select, change, input
- **ScatterPlot**: select, double_click
- **SimpleImage**: clear, change, upload
- **Slider**: change, input, release
- **State**: change
- **Textbox**: change, input, select, submit, focus, blur, stop, copy
- **Timer**: tick
- **UploadButton**: click, upload
- **Video**: change, clear, start_recording, stop_recording, stop, play, pause, end, upload, input

## Prediction CLI

The `gradio` CLI includes `info` and `predict` commands for interacting with Gradio apps programmatically. These are especially useful for coding agents that need to use Spaces in their workflows.

### `gradio info` — Discover endpoints and parameters

```bash
gradio info <space_id_or_url>
```

Returns a JSON payload describing all endpoints, their parameters (with types and defaults), and return values.

```bash
gradio info gradio/calculator
# {
#   "/predict": {
#     "parameters": [
#       {"name": "num1", "required": true, "default": null, "type": {"type": "number"}},
#       {"name": "operation", "required": true, "default": null, "type": {"enum": ["add", "subtract", "multiply", "divide"], "type": "string"}},
#       {"name": "num2", "required": true, "default": null, "type": {"type": "number"}}
#     ],
#     "returns": [{"name": "output", "type": {"type": "number"}}],
#     "description": ""
#   }
# }
```

File-type parameters show `"type": "filepath"` with instructions to include `"meta": {"_type": "gradio.FileData"}` — this signals the file will be uploaded to the remote server.

### `gradio predict` — Send predictions

```bash
gradio predict <space_id_or_url> <endpoint> <json_payload>
```

Returns a JSON object with named output keys.

```bash
# Simple numeric prediction
gradio predict gradio/calculator /predict '{"num1": 5, "operation": "multiply", "num2": 3}'
# {"output": 15}

# Image generation
gradio predict black-forest-labs/FLUX.2-dev /infer '{"prompt": "A majestic dragon"}'
# {"Result": "/tmp/gradio/.../image.webp", "Seed": 1117868604}

# File upload (must include meta key)
gradio predict gradio/image_mod /predict '{"image": {"path": "/path/to/image.png", "meta": {"_type": "gradio.FileData"}}}'
# {"output": "/tmp/gradio/.../output.png"}
```

Both commands accept `--token` for accessing private Spaces.

## Additional Reference

- [End-to-End Examples](examples.md) — complete working apps
