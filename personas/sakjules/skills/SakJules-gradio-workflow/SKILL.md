---
name: SakJules-SakThai-gradio-workflow
description: A skill for Gradio Workflow.
...
---

# Gradio Workflow (`gr.Workflow`)

author: SakThai
license: MIT
**domain:** gradio, workflow, visual-pipeline, ai-canvas  
**Hermes skill name:** `Gradio-Workflow`  
**tags:** `gradio`, `workflow`, `visual-programming`, `hf-spaces`, `pipeline`

## Description

`gr.Workflow` is Gradio's visual AI pipeline builder (introduced in Gradio 6.17, stable through 6.20). It provides a drag-and-drop canvas for connecting Hugging Face Spaces, Inference API models, and local Python functions into multi-step pipelines — all from the browser.

The system comprises three core modules:
- **`gradio/workflow.py`** (1,880 lines) — high-level `Workflow(Blocks)` class with `bind`, `graph`, `edges`, server functions for space/model/dataset orchestration
- **`gradio/components/workflowcanvas.py`** (126 lines) — `WorkflowCanvas(BlockContext, Component)` visual canvas component
- **`gradio/workflow_api.py`** (885 lines) — `WorkflowGraph` parser, topo-sort, subgraph extraction, executor, and endpoint registration

## Quick Start

```python
import gradio as gr

def shout(text: str) -> str:
    return (text or "").upper()

def reverse(text: str) -> str:
    return (text or "")[::-1]

demo = gr.Workflow(graph="workflow.json", bind={"shout": shout, "reverse": reverse})
demo.launch()
```

## Key Concepts

### Workflow Graph Schema (v2)

The visual pipeline is represented as JSON with four node roles:

1. **references** — input/output data sources (Text, Image, Audio, etc.)
2. **operators** — processing nodes (HF Spaces, Inference models, bound functions)
3. **subjects** — output display nodes (the final outputs)
4. **edges** — connections wiring nodes together

Each node has typed ports (`inputs`/`outputs`) with port types: `text`, `number`, `boolean`, `image`, `audio`, `video`, `file`, `gallery`, `model3d`.

### `gr.Workflow()` Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `graph` | `str\|None` | Path to workflow JSON file. Defaults to `workflow.json` alongside the caller script. Created on first save. |
| `bind` | `dict[str, Callable]\|list[Callable]\|None` | Python functions callable from the canvas. List auto-names by `__name__`. |
| `edges` | `list[tuple[str, str]]` | Wire nodes together when generating graph from `bind`. Format: `("fn_name.port", "fn_name.port")`. |

### Three Operator Kinds

| Kind | Backend | Use Case |
|------|---------|----------|
| `space` | `call_space()` | Hugging Face Space via `gradio_client`, auto-detects endpoints |
| `model` | `call_model()` | Inference API model via `InferenceClient` |
| `fn` | `call_fn()` | Local bound Python function |
| `dataset` | `fetch_dataset()` | Dataset viewer — fetch rows from any HF dataset |

### Server Functions Available to Canvas

The canvas frontend can call 19 registered server functions:

| Function | Purpose |
|----------|---------|
| `get_token` | Resolve HF token (local/oauth) |
| `get_write_access` | Check write permission |
| `get_oauth_available` | Check OAuth status |
| `call_space` | Execute a Space endpoint via `gradio_client` |
| `call_model` | Execute an Inference API model |
| `fetch_dataset` | Fetch dataset rows via datasets-server |
| `search_spaces` | Browse curated Spaces catalog |
| `search_models` | Browse curated models catalog |
| `search_datasets` | Search HF Hub datasets |
| `search_quick` | Quick search (cached, 30s TTL) |
| `resolve_repo` | Resolve URL/ID to repo info |
| `is_curated` | Check if repo is in curated catalog |
| `curated_modalities` | List available modalities |
| `curated_modality_tasks` | List tasks for a modality |
| `get_dataset_schema` | Get dataset schema via first-rows |
| `list_bound_fns` | List bound function signatures |
| `get_workflow_api` | Describe API endpoints for View API panel |
| `get_model_endpoints` | Enumerate model endpoints/tasks |
| `save_workflow` | Save the graph JSON (requires write token) |

### Curated Operator Catalog

Gradio maintains a curated list of validated Spaces and models at `gradio/workflow-curated` on the Hub. A bundled snapshot is shipped in `_workflow_curated_snapshot.json` as fallback. The canvas surface displays curated operators ordered by:
1. ZeroGPU Spaces first
2. Featured entries
3. By latency (fastest first)

### Token Resolution & Auth

- **Local mode**: write token from HF login, printed as a write-access link at launch
- **Spaces mode**: OAuth-based, auto-detects write access from OAuth token
- `_resolve_token()` checks data payload → OAuth token → local saved token in priority order
- `save_workflow` enforces write access via `has_write_access()`

### API Endpoints

Each workflow subject (output node) is exposed as a Gradio API endpoint:
- Registered via `WorkflowEndpointManager.register_workflow_endpoints()`
- Uses `/info` + `/call` machinery for each subgraph
- Re-syncs on every `save_workflow()` call
- Supports both server-side and client-side execution
- Bound functions get `predict_fn_<name>` endpoints

## Usage Patterns

### Pattern 1: Visual Pipeline with Spaces Only

```python
# No bind, pure visual — user connects HF Spaces in the canvas
demo = gr.Workflow(graph="my_pipeline.json")
demo.launch()
```

### Pattern 2: Hybrid — Local Functions + Spaces

```python
def clean_text(text: str) -> str:
    return text.strip().lower()

def describe_product(image) -> str:
    # Call a VLM via gradio_client
    ...

demo = gr.Workflow(
    graph="workflow.json",
    bind=[clean_text, describe_product],
)
demo.launch()
```

### Pattern 3: Auto-Wired from Edges

```python
def shout(text: str) -> str:
    return text.upper()

def reverse(text: str) -> str:
    return text[::-1]

# Auto-generates the workflow graph with wired connections
demo = gr.Workflow(
    bind=[shout, reverse],
    edges=[("shout", "reverse")],  # shout output → reverse input
)
demo.launch()
```

### Pattern 4: Programmatic API Access (Headless)

```python
# Each subject is automatically a named API endpoint
client = Client("http://127.0.0.1:7860/")
result = client.predict(
    "hello world",
    api_name="/subject_id"  # matches the subject's node id
)
```

## Architecture Notes

- **`Workflow(Blocks)`** — extends `gr.Blocks` with `mode="workflow"`, cannot be nested inside other Blocks
- **`WorkflowCanvas`** — both `BlockContext` and `Component`, hosts the Svelte canvas UI
- **Collaborative editing** — the workflow JSON file persists edits; multiple browser sessions share the same file
- **Error handling** — structured errors with `error`, `error_type`, `suggestion` fields, classified by `_classify_error()`
- **Media handling** — image/audio/video outputs go through `_save_tmp()` → served as `/gradio_api/file=...` URLs
- **File size limit** — 5 MB max for workflow payload in `save_workflow`
- **Thread safety** — `_save_lock` ensures serialized writes to the workflow file
- **Bound function thread safety** — Gradio's `anyio.to_thread.run_sync` with app limiter

## Dependency Chain

```
gr.Workflow()
├── WorkflowCanvas (component)
├── workflow.json (persistence)
├── _workflow_curated_snapshot.json (bundled curated catalog)
├── gradio_client (Space calling)
├── huggingface_hub (token, API calls)
└── gradio/workflow_api.py
    ├── WorkflowGraph (parser + validator)
    ├── topo_sort() (Kahn's algorithm)
    ├── subgraph extraction
    └── WorkflowEndpointManager (API registration)
```

## References

- Source: `gradio/workflow.py` (gradio ≥ 6.17)
- Source: `gradio/workflow_api.py`
- Source: `gradio/components/workflowcanvas.py`
- Demo: `demo/workflow/run.py`
- Demo: `demo/workflow_api/run.py`
- Curated catalog: `gradio/workflow-curated` (HF dataset)
- Formally documented at: `https://www.gradio.app/docs/gradio/workflow`

## Learnings

See `references/hf-learnings.md` for the full learning report.
