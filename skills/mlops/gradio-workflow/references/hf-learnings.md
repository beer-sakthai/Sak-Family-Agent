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
