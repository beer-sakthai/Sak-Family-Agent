# HF Learnings Log

---

## 2026-07-24: gr.Workflow — Gradio's Visual AI Pipeline Builder

### Summary
Deep dive into Gradio's `gr.Workflow` system (gradio ≥ 6.17, current 6.20), a complete visual AI pipeline builder embedded in Gradio. Covers the Workflow class, WorkflowCanvas component, WorkflowGraph schema v2 parser/executor, 19 server functions, curated operator catalog, auth model, and API endpoint registration.

### Key Findings

1. **Architecture**: `Workflow(Blocks)` extends `gr.Blocks` with `mode="workflow"`. Contains a `WorkflowCanvas` (both BlockContext and Component) that renders the Svelte-based visual canvas. Cannot be nested in other Blocks.

2. **Workflow Graph Schema v2**: JSON with four node roles:
   - `references` — I/O data sources (input data nodes)
   - `operators` — processing nodes (Space / Model / bound fn / dataset)
   - `subjects` — output display nodes (become API endpoints)
   - `edges` — connections between node ports

3. **Three modes of use**:
   - **graph only**: `Workflow(graph="pipeline.json")` — pure visual, user connects Spaces
   - **bind functions**: `Workflow(bind=[fn1, fn2, ...])` — local Python functions as canvas nodes
   - **auto-wired**: `Workflow(bind=[...], edges=[...])` — auto-generates graph from bind + edges

4. **Operator execution**:
   - `call_space()`: uses `gradio_client` to call any HF Space endpoint
   - `call_model()`: uses `InferenceClient` for Inference API models
   - `call_fn()`: calls bound Python functions with JSON args
   - `fetch_dataset()`: fetches rows via the HF datasets-server API

5. **Auth model**: Write token from HF login (local) or OAuth (Spaces). `save_workflow` enforces write access via `has_write_access()`. The write-access link is printed at launch for local mode.

6. **API endpoint registration**: Each workflow subject becomes a named Gradio API endpoint via `WorkflowEndpointManager`. Re-syncs automatically on every `save_workflow()`. Bound functions get `predict_fn_<name>` endpoints.

7. **Curated catalog**: Gradio ships a curated snapshot of validated Spaces/models from `gradio/workflow-curated` dataset. Cached in-memory for 3600s, with bundled JSON fallback. Search prioritizes ZeroGPU → featured → fastest latency.

8. **Thread safety**: Concurrent save requests serialized via `_save_lock`. Workflow payload capped at 5 MB. Bound functions run through Gradio's `anyio.to_thread.run_sync` with app limiter.

9. **Port type system**: Scalar types (int→number, float→number, bool→boolean, everything else→text). Media types (image, audio, video, file, gallery, model3d) travel as dicts with path/url.

10. **Error handling**: Structured responses with `error`, `error_type`, `suggestion` fields. `_classify_error()` categorizes: auth, not_found, rate_limit, quota, overloaded, api, connection, timeout, oauth, unknown.

### Skill Created
`mlops/gradio-workflow/` — complete skill with SKILL.md documenting Workflow API, architecture, usage patterns, server functions, graph schema, and dependencies.

### Sources
- Source code: `gradio/workflow.py` (1,880 lines) — Workflow class, server functions, curated search
- Source code: `gradio/workflow_api.py` (885 lines) — WorkflowGraph, topo-sort, executor, endpoint registration
- Source code: `gradio/components/workflowcanvas.py` (126 lines) — WorkflowCanvas component
- Demo: `demo/workflow/run.py` — visual pipeline with describe_product + craft_marketing_prompt
- Demo: `demo/workflow_api/run.py` — API-exposed workflow with shout + reverse
- Gradio changelog: 6.17.0 introduced Workflow, 6.19.0 added subgraph API endpoints, 6.20.0 added curated catalog & improved canvas UX
- Hugging Face Hub: `gradio/workflow-curated` dataset (bundled in `_workflow_curated_snapshot.json`)

---

## 2026-07-25: Gradio Events & Callbacks Deep Dive — Complete Event System Architecture

### Summary
Deep dive into Gradio's event system (v6.20) — the complete architecture of event listeners, event data classes, trigger modes, chaining, cancellation, and the registration pipeline. Covers all 36+ events defined in `gradio/events.py`, 10 EventData subclasses, the `Dependency` chaining object, `gr.on()` multi-trigger pattern, and the metaclass-driven component event method generation.

### Core Architecture

1. **`EventListener`** — The fundamental unit. A subclass of `str` that represents a named event (`"click"`, `"change"`, `"select"`, etc.) with metadata: `has_trigger`, `show_progress`, `connection`, `event_specific_args`, `trigger_after`, `trigger_only_on_success/failure`, `doc`, `callback`, `config_data`. The `EventListener._setup()` method creates the actual `event_trigger` callable at runtime.

2. **`EventListenerMethod`** — A lightweight dataclass pairing a `Block | None` with an `event_name: str`. Represents a concrete trigger target (e.g. `button.click` → `EventListenerMethod(button, "click")`).

3. **All Events (the `Events` class)** — 36+ predefined event listeners:
   - **Value changes**: `change`, `input`, `clear`, `apply`
   - **Interaction**: `click`, `double_click`, `submit`, `release`, `focus`, `blur`, `select`
   - **Media**: `play`, `pause`, `stop`, `end`, `start_recording`, `pause_recording`, `stop_recording`
   - **File operations**: `upload`, `download`, `delete`, `copy`
   - **Chatbot-specific**: `like`, `retry`, `undo`, `edit`
   - **Streaming**: `stream` (connection="stream", not "sse")
   - **Timing**: `tick` (show_progress="hidden")
   - **Layout**: `expand`, `collapse`, `load`
   - **Keyboard**: `key_up`, `option_select`, `example_select`

4. **`EventData` Subclasses** — 10 classes carrying rich event payload:
   - `EventData` — `.target` (the triggering Block)
   - `SelectData` — `.index`, `.value`, `.row_value`, `.col_value`, `.selected`
   - `KeyUpData` — `.key`, `.input_value`
   - `DeletedFileData` — `.file` (FileData)
   - `LikeData` — `.index`, `.value`, `.liked`
   - `RetryData` — `.index`, `.value`
   - `UndoData` — `.index`, `.value`
   - `EditData` — `.index`, `.previous_value`, `.value`
   - `DownloadData` — `.file` (FileData)
   - `CopyData` — `.value`

### Component Event Declaration

Components declare events via `EVENTS` list at class level. The `ComponentMeta` metaclass:
1. Scans `EVENTS` for string/EventListener entries
2. Copies each via `.copy()` and calls `.set_doc(component=...)`
3. Attaches the `.listener` callable directly as an attribute on the class
4. Auto-generates `.pyi` stub files with typed signatures via `create_or_modify_pyi()`

Example component event sets:
| Component | Events |
|-----------|--------|
| `Button` | change, click |
| `Textbox` | change, input, select, submit, focus, blur, stop, copy |
| `Dropdown` | change, input, select, focus, blur, key_up |
| `Image` | change, input, select, upload, clear, edit |
| `Audio` | change, input, select, upload, clear, play, pause, stop, start_recording, stop_recording, pause_recording |
| `Video` | change, input, select, upload, clear, play, pause, stop |
| `Chatbot` | change, select, like, retry, undo, edit, copy |
| `File` | change, input, select, upload, delete, download |
| `Dataframe` | change, input, select |
| `Gallery` | change, select, upload |
| `Slider` | change, input, release |
| `Timer` | tick |

### Event Registration Pipeline

1. Component method call (e.g. `btn.click(fn, inputs, outputs)`)
2. `EventListenerMethod(block, "click")` is created
3. `EventListener._setup()` → `event_trigger()` inner function invoked
4. `event_trigger()` calls `root_block.set_event_trigger()` which creates a `BlockFunction` instance
5. `BlockFunction` stores: fn, inputs, outputs, preprocess, postprocess, batch, concurrency, trigger_mode, api_name, cancels, etc.
6. Returns `Dependency` object with `.then()`, `.success()`, `.failure()` chain methods

### BlockFunction Deep Dive

`BlockFunction.__init__()` stores ~35 parameters:
- `fn`, `_id`, `inputs`, `outputs`, `preprocess`, `postprocess`
- `tracks_progress`, `concurrency_limit`, `concurrency_id`
- `batch`, `max_batch_size`, `total_runtime`, `total_runs`
- `targets` (list of `(block_id, event_name)` tuples)
- `api_name`, `api_description`, `js`, `show_progress`, `show_progress_on`
- `cancels`, `collects_event_data`, `trigger_after`, `trigger_only_on_success/failure`
- `trigger_mode` ("once", "multiple", "always_last")
- `queue`, `scroll_to_output`
- `api_visibility` ("public", "private", "undocumented")
- `types_generator` (detected from fn)
- `is_cancel_function`, `connection` ("sse"/"stream"), `time_limit`, `stream_every`
- `event_specific_args`, `component_prop_inputs`
- `key` (for gr.render() identity)
- `validator` (optional validation function)
- `spaces_auto_wrap()` for deployment on HF Spaces

### Dependency Chaining

`Dependency.__init__()` stores:
- `self.fn` — the original function
- `self.then` — `EventListener("then", trigger_after=dep_index)` → fires regardless
- `self.success` — `EventListener("success", trigger_only_on_success=True)` → fires only on success
- `self.failure` — `EventListener("failure", trigger_only_on_failure=True)` → fires only on failure

All three use `partial()` on the `EventListener.listener` bound to the original trigger block.

### gr.on() — Multi-Trigger Listener

`gr.on()` accepts `triggers: Sequence[Trigger] | Trigger | None`:

```python
gr.on(triggers=[btn.click, input.submit], fn=lambda x: x, inputs=[input], outputs=[output])
```

Key behaviors:
- Creates a single API endpoint shared by all triggers
- `triggers=None` means "run on app load and changes to any inputs"
- Supports decorator pattern: `@gr.on(triggers=[...])`
- JS-only mode: if `fn=None` and `js=str`, registers a frontend-only event
- Decorator wrapper cleans up any JS-only pre-registration

### Cancellation System

`set_cancel_events()` handles two types:
1. **Timer cancellation**: If `cancels` contains Timer components, generates a lambda that sets them to `Timer(active=False)`
2. **Regular cancellation**: Creates a cancel function with `is_cancel_function=True`, no fn, no queue, no preprocess, visibility="private"

The `/cancel` route uses `fn_indices_to_cancel` from `get_cancelled_fn_indices()`.

### Streaming Events

The `.stream()` event uses special configuration:
- `connection="stream"` (not standard "sse")
- `show_progress="minimal"`
- Has `stream_every: float = 0.5` and `time_limit: float | None = None` as event-specific args
- Only components with `"stream"` in their events (`StreamingInput` subclasses) can use it
- `check_streamable()` validates component supports streaming

### Trigger Modes

| Mode | Behaviour | Default For |
|------|-----------|-------------|
| `"once"` | Cannot submit while pending | Most events (click, select, etc.) |
| `"multiple"` | Unlimited submissions allowed | — (opt-in) |
| `"always_last"` | Only latest submission runs | change, key_up |

### Connection Types

| Type | Protocol | Used For |
|------|----------|----------|
| `"sse"` | Server-Sent Events | Standard event triggers |
| `"stream"` | persistent stream | Streaming input components (e.g. microphone) |

### Event-Specific Args

The `event_specific_args` list on `EventListener` allows components to define custom parameters per event:
```python
event_specific_args=[
    {"name": "stream_every", "type": "float = 0.5", "doc": "..."},
    {"name": "time_limit", "type": "float | None = None", "doc": "...", "component_prop": "false"},
]
```
These appear as function parameters in the `.pyi` stub and the event trigger signature. `component_prop="false"` means the arg is not included in the component's config JSON.

### Key Insights

- **Event names are strings**, `EventListener` subclasses `str` — they serialize directly as JSON event names to the frontend
- **Meta class magic**: `ComponentMeta.__new__()` dynamically attaches event listener methods to every component class at definition time
- **BlockFunction serialization**: `.get_config()` emits `_id` for inputs/outputs/targets, making the event dependency graph reconstructable on the frontend
- **JS frontend-only events**: When `fn=None` and `js=str`, a function-less event is registered that runs entirely in browser JS. The decorator pattern cleans up these placeholder registrations
- **Validator pattern**: An event can have a pre-validation function that runs with `queue=False`; only if it passes does the main fn execute
- **Spaces auto-wrap**: `BlockFunction.spaces_auto_wrap()` automatically wraps fn with `spaces.gradio_auto_wrap` when deployed on Hugging Face Spaces

### Sources
- Source: `gradio/events.py` — EventListener, Dependency, EventData, all event subclasses, `gr.on()`, Events class
- Source: `gradio/block_function.py` — BlockFunction class (~35 params, get_config serialization)
- Source: `gradio/blocks.py` — Block, BlockContext, set_event_trigger, Block.constructor_args
- Source: `gradio/blocks_events.py` — BlocksMeta metaclass for Blocks events (load)
- Source: `gradio/component_meta.py` — ComponentMeta metaclass, create_or_modify_pyi, updateable decorator
- Source: `gradio/components/base.py` — Component base with empty EVENTS list
- Docs: https://www.gradio.app/docs/gradio/event-listeners
- Docs: https://www.gradio.app/docs/gradio/eventdata
