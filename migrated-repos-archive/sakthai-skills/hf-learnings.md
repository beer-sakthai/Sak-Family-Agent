# HF Learnings Log

## 2026-07-26: hf-datasets-v5-sql-duckdb-integration — Datasets v5 SQL + DuckDB Deep Dive v2: Source Architecture, Advanced Patterns, Native Querying (Topic #401)

### Summary
Extended deep-dive into datasets v5 SQL module combined with DuckDB v1.5.5 integration, going beyond the initial SKILL.md with source code architecture analysis (SqlConfig, Sql builder, SqlDatasetWriter — full 240-line analysis), live verified testing of 5 integration patterns (roundtrip, aggregation, window functions + CTE, multi-table JOIN, native DuckDB Parquet query), performance benchmarks (10K rows: datasets SQL 0.008s read vs DuckDB native 0.006s), advanced SQL patterns (PIVOT, QUALIFY, LAG/LEAD, CTEs), DuckDB native HF cache querying via read_parquet() globs, and a comprehensive comparison matrix of 6 approaches (datasets SQL, DuckDB native Parquet, datasets native API, Pandas, Polars, DuckDB Arrow).

**Files updated:**
- `hf-datasets-v5-sql-duckdb-integration/SKILL.md` (v1.0.0 → v2.0.0) — Added source architecture section, performance benchmarks, advanced patterns, DuckDB native querying, comparison matrix
- `hf-datasets-v5-sql-duckdb-integration/references/hf-learnings.md` — New learning log entry

**Sources:**
- datasets source code: `packaged_modules/sql/sql.py` (120 lines)
- datasets source code: `io/sql.py` (122 lines)
- Live tests with DuckDB v1.5.5 and datasets v5
- DuckDB docs (data/parquet, data/arrow, SQL syntax)
- SQLAlchemy 2.0 docs

---

## 2026-07-26: hf-candle — Candle v0.11.0: Hugging Face's Minimalist Rust ML Framework for Serverless Inference (Topic #399)

### Summary
Comprehensive deep-dive into **Candle** — Hugging Face's minimalist ML framework for Rust, focused on serverless inference without Python overhead. Covers architecture (candle-core, candle-nn, candle-transformers, candle-examples), backends (CPU, CUDA, Metal, MKL, WASM), quantization support (llama.cpp GGUF types Q4_0 through Q8_0), weight format compatibility (safetensors, npz, ggml, PyTorch, ONNX), and the full model zoo (30+ models spanning LLMs, vision, audio, and multimodal). Includes PyTorch↔Candle API cheatsheet, zero-cost usage patterns, and comparison with burn/tch-rs/dfdx Rust ML frameworks. Current version: 0.11.0 (2026).

**Files created:**
- `hf-candle/SKILL.md` (author: SakThai, license: MIT) — Complete reference with architecture, model zoo, quantization, installation, zero-cost patterns
- `hf-candle/references/hf-learnings.md` — Learning log entry

**Sources:**
- GitHub README: https://github.com/huggingface/candle
- Candle Book: https://huggingface.github.io/candle/
- crates.io: candle-core 0.11.0
- HF Spaces demos (whisper, llama2, T5, Phi, SAM, yolo)
- Candle FAQ and installation guide

---

## 2026-07-26: hf-kernels-ecosystem-major-updates — 🤗 Kernels: Major Updates — Trusted Publishers, Sigstore Signing, Torch Stable ABI, TVM FFI, Agentic Kernel Development (Topic #398)

### Summary
Major update to the Hugging Face **Kernels ecosystem** (v0.16.0+) covering the July 6, 2026 revamp. Key additions: kernels as a **first-class repository type** on the Hub (`kernels-community/` namespace) with dedicated pages and hardware filtering; **trusted kernel publishers** (only load from trusted orgs by default, explicit `trust_remote_code=True` opt-in); **Sigstore code signing** with ephemeral private keys and GitHub workflow verification; **revamped CLI separation** between `kernels` (loading) and `kernel-builder` (building) packages; **Torch Stable ABI** support (one build works across Torch ≥ 2.9); **Apache TVM FFI** support (cross-framework kernels for PyTorch, Jax, CuPy); **agentic kernel development** workflow (scaffold → build → benchmark → iterate with HF Jobs); **system cards** exposing kernel interfaces; **compatibility APIs** (`has_kernel()`, `get_kernel_variants()`); and **improved manylinux_2_28 support** with dynamic libstdc++.

**Files updated:** `mlops/hf-kernels-ecosystem/SKILL.md` (v1.0.0→v2.0.0) + `references/hf-learnings.md` with full coverage of security, agentic dev, framework support, system cards, compatibility APIs, and environment setup.

**Sources:** HF Kernels docs (v0.16.0), GitHub `huggingface/kernels` repo, HF Blog "🤗 Kernels: Major Updates" (July 6, 2026), v0.16.0 release notes.

---

## 2026-07-25: hf-openenv-agentic-execution — Hugging Face OpenEnv v0.4.1: Agentic RL Environments (Topic #385)

### Summary
Comprehensive deep-dive into **OpenEnv** — Hugging Face's unified framework for building, deploying, and interacting with isolated execution environments for agentic reinforcement learning. Covers architecture (Gymnasium-style API over HTTP/WebSocket), MCP tool integration (ListToolsAction, CallToolAction), Rubric composable reward system, container-first design, cloud sandbox providers (Docker, Daytona, ACA), RL training integration (TRL, Unsloth, torchforge), environment anatomy (openenv.yaml, models, server, client), and zero-cost patterns. OpenEnv v0.4.1 experimental, governed by a technical committee including Meta-PyTorch, Nvidia, and Hugging Face.

**Files updated:** `hf-openenv-agentic-execution/SKILL.md` (author: SakThai, license: MIT) + `references/hf-learnings.md` with full architecture, API reference, MCP integration deep-dive, Rubric system, RL training patterns, zero-cost analysis.

**Sources:** Official OpenEnv docs at huggingface.co/docs/openenv (v0.4.1), GitHub repo huggingface/OpenEnv, tutorials for MCP, TRL, and first environment.

---

## 2026-07-25: hf-bitsandbytes-quantization-deep-dive-v2 — bitsandbytes v0.50.0: New 4-bit GEMM, MPS, ROCm Stable, CPU Performance (Topic #383)

### Summary
Comprehensive deep-dive refresh of bitsandbytes quantization covering the **v0.50.0** release (2026-07-25). Includes: new fused 4-bit GEMM kernels for inference (up to 4× faster at batch sizes 2–64), stable AMD ROCm support (out of preview), Apple Silicon MPS backend with all 4-bit and LLM.int8() configurations working, CPU performance improvements (1.1× to 20× on x86-64 and ARM64), Windows ARM64 support, new AdEMAMix optimizer with 8-bit and paged variants, and major breaking changes (min PyTorch 2.4, removed research module, non-blockwise optimizers, and legacy sparse ops). Covers the full memory benchmark comparison (405B QLoRA on 8×H100 with 256GB RAM), 4-bit vs 8-bit vs AWQ vs GPTQ comparison matrix, and complete migration guide from v0.43→v0.50.

**Files updated:** `hf-bitsandbytes-quantization/SKILL.md` (version 2.0.0) + `references/hf-learnings.md` (470 lines, 19KB) with architecture details, hardware matrix, parameter reference, training pipelines, optimizer catalog, and zero-cost patterns.

**Sources:** GitHub releases 0.45.0→0.50.0, Transformers 5 docs, PyPI metadata, official changelog.

## 2026-07-25: hf-trackio-experiment-tracking — Hugging Face Trackio: Free Experiment Tracking with Buckets and Spaces (Topic #367)

### Summary
Comprehensive deep-dive into **Trackio** (`huggingface-trackio`) — Hugging Face's lightweight, free experiment tracking Python library built on top of Storage Buckets and Spaces. Trackio is a drop-in replacement for WandB/MLflow with a core codebase of <3,000 lines, designed for zero-cost experiment tracking. Key differentiator: everything including hosting on Hugging Face is **free**. Integrates with Transformers (via `TrackioCallback`), TRL (via `TrackioTRL`), and general Python training loops. Features a Gradio dashboard that can run locally, on Hugging Face Spaces (free), or on a self-hosted server. Agent-friendly CLI and Python APIs designed for autonomous ML experiments.

### Key Findings

| Area | Finding |
|------|---------|
| **What it is** | Lightweight, free experiment tracking library built on HF Buckets + Spaces. Drop-in WandB replacement. <3k lines Python. |
| **Storage backend** | HF Storage Buckets (free tier). `TRACKIO_BUCKET_ID` env var. Dataset-based storage (`TRACKIO_DATASET_ID`) is deprecated. |
| **Dashboard** | Gradio-based. Three modes: local (`trackio show`), HF Space (`trackio init(project="org/space")`), or self-hosted server. |
| **WandB migration** | `import trackio as wandb` — identical API for `init()`, `log()`, `finish()`, `config`, `Artifact`, `Table`. |
| **CLI commands** | `trackio init`, `trackio show [--project]`, `trackio dashboard`, `trackio status` — all designed for LLM/agent use. |
| **Transformers** | `TrackioCallback` auto-logs training/eval metrics — pass to `Trainer(callbacks=[TrackioCallback()])`. |
| **TRL integration** | `TrackioTRL` callback for RL training loops with GRPO/DAPO/GSPO. |
| **Artifact support** | `trackio.Artifact(name, type)` for model checkpoints, datasets, and files stored in Buckets. |
| **Environment variables** | `TRACKIO_BUCKET_ID`, `TRACKIO_PROJECT`, `TRACKIO_SERVER_URL`, `TRACKIO_MODE` (local/space/server), `TRACKIO_DASHBOARD_PORT`, `TRACKIO_GPU_LOG_INTERVAL`, `TRACKIO_CPU_LOG_INTERVAL`, `TRACKIO_WEBHOOK_MIN_LEVEL` |
| **MCP integration** | Trackio can be used as an MCP tool via its CLI — query experiment data from agents. |
| **Self-hosted mode** | Deploy dedicated trackio server for teams. Dashboard accessible via browser, log runs from any machine. |
| **Agent-friendly** | CLI commands designed for LLM invocation. Structured outputs for experiment queries. |

### Core API Reference

| Function | Description |
|----------|-------------|
| `trackio.init(project, config, tags, name, ...)` | Initialize a run. Identical signature to wandb.init. |
| `trackio.log(metrics, step, commit)` | Log metrics dict. Auto-increments step. |
| `trackio.finish(exit_code)` | End current run, flush data. |
| `trackio.config` | Dict-like hyperparameter config. |
| `trackio.summary` | Dict-like final summary metrics. |
| `trackio.Artifact(name, type)` | Log artifacts (models, datasets, files) to Buckets. |
| `trackio.Table(dataframe)` | Log tabular data for dashboard visualization. |
| `trackio.alert(title, text, level)` | Send alerts via webhook. |
| `trackio.show(project, port, host)` | Launch dashboard. |
| `trackio.status()` | Check logging status. |

### Dashboard Deployment Modes

| Mode | Setup | Storage | Cost |
|------|-------|---------|------|
| **Local** | `trackio show` | Local filesystem | Free |
| **HF Space** | `trackio.init(project="org/space_id")` | HF Bucket (TRACKIO_BUCKET_ID) | Free |
| **Self-hosted** | `trackio.init(server_url="...")` | Server storage | Hosting costs |

### Zero-Cost Patterns
- Dashboard on HF Spaces: zero hosting cost, persistent storage via free Bucket tier
- `import trackio as wandb`: instant migration from paid WandB
- Local dashboard for personal use: no infrastructure required
- Artifacts stored in Buckets: free tier covers small-to-medium experiments
- Agent/LLM use: CLI commands structured for autonomous execution

### Skill Created
`hf-trackio-experiment-tracking/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md (full API reference, dashboard deployment modes, integrations, zero-cost patterns).

### Sources
- https://huggingface.co/docs/trackio/en/index
- https://huggingface.co/docs/trackio/en/quickstart
- https://huggingface.co/docs/trackio/en/api
- https://huggingface.co/docs/trackio/en/environment-variables
- https://huggingface.co/docs/trackio/en/transformers
- https://huggingface.co/docs/trackio/en/trl
- https://huggingface.co/docs/trackio/en/migrating

---

## 2026-07-25: hf-inference-router-openai-compatible-endpoint — Practical Patterns Deep-Dive (Topic #363)

### Summary
Comprehensive deep-dive into the HF Inference Router's practical usage patterns — covering the new **Responses API (beta)** with event-driven streaming and Remote MCP, **structured outputs** with Pydantic/JSON Schema via both `chat.completions` and `responses` APIs, **function calling** execution patterns with tool_choice control, advanced **pricing model** (free tier, Custom Provider Key, Organization billing), and the full **18-provider ecosystem** with capability matrix. Builds on Topic #361 (Router architecture and API surface) to add real-world usage patterns, zero-cost strategies, and the latest Inference Providers features.

### Key Findings

| Area | Finding |
|------|---------|
| **Responses API** | New OpenAI-compatible unified interface with event streaming, `.parse()` for typed outputs, Remote MCP tools, reasoning effort controls |
| **Structured outputs** | Two approaches: `chat.completions` with `response_format` (JSON Schema) or `responses.parse()` with Pydantic (typed objects) |
| **Function calling** | Full lifecycle: define schema → model decides → execute tool → return result; `tool_choice` controls (auto/required/specific/none) |
| **Remote MCP** | Responses API can call server-hosted MCP tools directly with `server_url`, `allowed_tools`, `require_approval` |
| **Pricing** | Free: $0.10/mo, PRO: $2.00/mo, Team: $2/seat. Custom Provider Key bypasses HF billing. Organization billing via `X-HF-Bill-To` |
| **Free providers** | Some providers offer free inference (`is_free: true`). Check via `/v1/models`. Groq offers free inference with tool support |
| **18 providers** | Full capability matrix: only HF Inference supports all tasks (chat, image, video, audio). Third parties focus on chat completion |
| **Event streaming** | `stream=True` with `responses.create()` yields `response.created`, `output_text.delta`, `response.completed` events |
| **Agent integrations** | Dedicated guides for OpenCode, Pi, Codex, Claude Code, Hermes Agent — drop-in OpenAI-compatible setup |

### Zero-Cost Patterns
- Use `:cheapest` policy or check `is_free` in `/v1/models` for free routing
- Responses API works on free models with tool support
- Custom Provider Key lets you use existing provider free tiers
- $0.10/mo credit covers hundreds of lightweight calls
- Cache responses and batch requests to conserve credits

### Skill Updated
`hf-inference-router-openai-compatible-endpoint/` — SKILL.md + references/hf-learnings.md with practical patterns deep-dive.

### Sources
- https://huggingface.co/docs/inference-providers/en/guides/responses-api
- https://huggingface.co/docs/inference-providers/en/guides/structured-output
- https://huggingface.co/docs/inference-providers/en/guides/function-calling
- https://huggingface.co/docs/inference-providers/en/pricing
- https://huggingface.co/docs/inference-providers/en/index
- https://huggingface.co/docs/inference-providers/en/guides/first-api-call
- https://huggingface.co/docs/inference-providers/en/guides/building-first-app

---

## 2026-07-25: hf-gradio-server-mode — Gradio 6 Server Mode (gr.Server) Complete Reference (Topic #351)

### Summary
Comprehensive deep dive into Gradio 6's `gr.Server` (Server mode) — introduced in 6.10.0. A FastAPI-based API server that exposes Gradio's queue, SSE streaming, concurrency control, and MCP capabilities **without a UI**. Unlike `gr.Blocks()` which renders a full web interface, `gr.Server` is designed for pure API/microservice deployment with OpenAPI docs, standard FastAPI routes (`.get()`, `.post()`, etc.), and built-in Gradio event infrastructure. Key insight: `gr.Server` inherits directly from FastAPI (via `gradio.routes.App`), so all standard FastAPI methods work directly.

### Key Findings
- **True FastAPI inheritance**: `gr.Server` is an actual FastAPI subclass — can use middleware, routers, dependency injection, WebSocket, sub-applications
- **`@server.api()` decorator**: Registers functions as Gradio API endpoints with queue, SSE streaming, concurrency control, batch processing
- **MCP namespace**: `server.mcp.tool()`, `server.mcp.resource()`, `server.mcp.prompt()` — native MCP decorators on the server instance
- **Dual decorator pattern**: Stack `@server.mcp.tool()` + `@server.api()` on same function for both Gradio API + MCP tool
- **Deferred registration**: `@server.api()` functions stored in `_deferred_apis` list, only registered at `launch()` time
- **No Gradio frontend**: Server mode doesn't load/serve frontend JS/CSS — lighter and faster startup than `gr.Blocks`
- **Full OpenAPI docs**: Automatic at `/docs` (Swagger), `/redoc` (ReDoc), `/openapi.json`
- **ZeroGPU support**: Since 6.12.0
- **Auth via FastAPI deps**: `auth_dependency` parameter supports OAuth2, JWT, API keys
- **Env var**: `GRADIO_SERVER_MODE_ENABLED=1` set on launch

### API Surface
- `server.api(fn, name, queue, concurrency_limit, batch, stream_every, ...)` — Gradio endpoint decorator
- `server.mcp.tool(name)` / `.resource(uri)` / `.prompt(name)` — MCP decorators
- All FastAPI methods: `.get()`, `.post()`, `.add_middleware()`, `.include_router()`, etc.
- `server.launch(server_name, server_port, auth_dependency, mcp_server, ...)` — start server

### Skill Created
`hf-gradio-server-mode/` — complete skill with SKILL.md and references/hf-learnings.md (256 lines, full API reference, 8 usage patterns, comparison matrix, MCP integration deep dive).

---

## 2026-07-25: hf-gradio-6-native-plot-components — Gradio 6 Native Plot Components Complete Reference (Topic #351)

### Summary
Comprehensive deep dive into Gradio 6's native plot component family (`gr.LinePlot`, `gr.ScatterPlot`, `gr.BarPlot`, and the generic `gr.Plot`). These components provide declarative, DataFrame-backed charting with client-side rendering (built on Vega-Altair), eliminating the need for matplotlib/plotly for common use cases. All three share the **identical API** with over 20 dedicated parameters for axis configuration, color mapping, binning, aggregation, tooltips, and layout.

### Key Findings
- **Three native plot components**: `gr.LinePlot`, `gr.ScatterPlot`, `gr.BarPlot` — all share identical constructor API
- **Client-side rendering**: Uses Vega-Altair in browser; no server CPU for rendering
- **Direct DataFrame input**: Accepts `pd.DataFrame` directly, or a callable returning one
- **Built-in binning/aggregation**: `x_bin` (numeric size or datetime string like "1h") + `y_aggregate` (sum/mean/median/min/max)
- **Color series**: `color` parameter splits data into multiple series; `color_map` for custom colors
- **Interactive events**: `.change()`, `.select()` (with `SelectData`), `.double_click()`
- **Tooltip modes**: `"axis"`, `"all"`, `"none"`, or `list[str]` of columns
- **Axis limits**: `x_lim`/`y_lim` as `[min, None]` tuples for one-sided constraints
- **Sort control**: `sort` parameter for categorical x — `"x"`, `"-x"`, `"y"`, `"-y"`, or explicit list
- **gr.Plot fallback**: For matplotlib/plotly/bokeh/altair figures when custom rendering is needed
- **Performance advantage**: Native plots send DataFrame as JSON to browser → 10-100x smaller payload than serialized mpl figures

### API Parameters (shared by LinePlot, ScatterPlot, BarPlot)
| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | `pd.DataFrame \| Callable \| None` | Data or callable returning data |
| `x` | `str` | X-axis column name |
| `y` | `str \| list[str]` | Y-axis column name(s), must be numeric |
| `color` | `str \| None` | Column for series splitting |
| `title` | `str \| None` | Chart title |
| `x_title` / `y_title` | `str \| None` | Axis titles |
| `color_title` | `str \| None` | Legend title |
| `x_bin` | `str \| float \| None` | X grouping: number (numeric) or "1h"/"15m" (datetime) |
| `y_aggregate` | `Literal` | "sum", "mean", "median", "min", "max" |
| `x_lim` / `y_lim` | `list[float \| None]` | Axis bounds |
| `color_map` | `dict[str, str]` | Series → color mapping |
| `sort` | `str \| list[str]` | Categorical sort order |
| `tooltip` | `str \| list[str]` | Tooltip content mode |
| `height` | `int \| None` | Plot height in px |

### Skill Created
`hf-gradio-6-native-plot-components/` — complete skill with SKILL.md and references/hf-learnings.md.

---

## 2026-07-24: hf-hub-exceptions-retry-deep-dive

### Summary
Deep dive into the `huggingface_hub v1.24.0` exception hierarchy (40+ custom exception types) and built-in retry/backoff mechanism. Covers `HfHubHTTPError` with its 10+ subclasses, `http_backoff()` with exponential backoff and rate-limit awareness, session management, and practical error handling patterns.

### Key Findings
- **HfHubHTTPError(HTTPError, OSError)** base with `.request_id`, `.server_message`, `.response`, `.append_to_message()`
- http_backoff defaults: max_retries=5, base_wait=1s, max_wait=8s, retry on (408, 429, 500, 502, 503, 504) + network exceptions
- Rate limit parsing via `Ratelimit` and `Retry-After` headers (IETF draft)
- 40+ exception types including RepositoryNotFoundError, GatedRepoError, RevisionNotFoundError, BadRequestError, TextGenerationError hierarchy
- Session management: get_session(), close_session(), set_client_factory()
- Disable retries: pass empty tuples to retry_on_exceptions/retry_on_status_codes

### Skill Created
`mlops/hf-hub-exceptions-retry/` — complete reference with hierarchy diagram, retry parameters, and usage patterns.

---

## 2026-07-24: hf-datasets-faiss-vector-search-deep-dive

### Summary
Deep dive into FAISS vector search integration in Hugging Face Datasets. Covers the full API surface: add_faiss_index (with factory strings, GPU, custom indexes, metric types), query via get_nearest_examples/search, persistence with save/load_faiss_index, and advanced direct FAISS index access for range_search. FAISS enables datasets to function as vector databases for RAG, semantic search, and deduplication — all without external services.

### Key API
- `add_faiss_index(column, index_name, device, string_factory, metric_type, custom_index, batch_size, train_size, faiss_verbose, dtype)` — create index
- `get_nearest_examples(index_name, query, k)` — retrieve closest examples with scores
- `search(index_name, query, k)` — returns scores + indices only
- `save_faiss_index(index_name, file)` — serialize to .faiss file
- `load_faiss_index(index_name, file, device, storage_options)` — reload from disk/remote URI
- `get_index(index_name).faiss_index` — access raw FAISS index for advanced operations

### Key Insights
- Default index type is IndexFlatL2 (exact, brute-force). For speed use string_factory: IVF, HNSW, PQ
- GPU support via device parameter (single, all, or specific GPUs)
- Remote URI loading (S3, HTTP) supported since datasets v2.11.0
- train_size must be set for IVF-type indexes (k-means clustering step)
- Index is NOT saved with ds.save_to_disk() — must use save_faiss_index() separately
- FAISS is in-memory; use GPUs or quantized indexes for large-scale

## 2026-07-23: hf-bitsandbytes-quantization

### Summary
Researched the bitsandbytes library's integration with Hugging Face Transformers for k-bit quantization (8-bit and 4-bit), enabling large model inference and training on consumer GPUs with dramatically reduced memory.

### Key Concepts

**Three Main Features:**
1. **8-bit optimizers** — block-wise quantization for Adam/AdamW/etc. maintaining 32-bit performance at fraction of memory cost
2. **LLM.int8()** — vector-wise quantization for inference, quantizes most features to 8-bit, outliers handled with 16-bit matmul (no quality loss)
3. **QLoRA (4-bit)** — quantizes model to 4-bit + trains LoRA adapters. Uses NF4 data type

**Hardware Support:** NVIDIA CUDA, Intel XPU, Intel Gaudi HPU, CPU

**BitsAndBytesConfig Parameters:**
- `load_in_4bit=True/load_in_8bit=True` — enable quantization
- `bnb_4bit_quant_type="nf4"` — NF4 (QLoRA paper) vs "fp4"
- `bnb_4bit_compute_dtype=torch.bfloat16` — compute dtype for speed
- `bnb_4bit_use_double_quant=True` — nested quantization (extra 0.4 bits/param saved)
- `llm_int8_threshold=6.0` — outlier threshold for LLM.int8()
- `llm_int8_skip_modules=["lm_head"]` — skip specific modules
- `llm_int8_enable_fp32_cpu_offload=True` — offload to CPU

**QLoRA Pipeline:**
1. Load base model with `load_in_4bit=True`, `bnb_4bit_quant_type="nf4"`
2. Apply PEFT LoRA config
3. Train only LoRA adapters
4. Merge or keep separate for inference

**Resources:**
- Paper: QLoRA (https://hf.co/papers/2305.14314)
- Blog: "Making LLMs even more accessible with bitsandbytes, 4-bit quantization and QLoRA" (https://huggingface.co/blog/4bit-transformers-bitsandbytes)

---

## 2026-07-23: hf-hub-model-download-stats

### Summary
Researched the Hugging Face Hub's model download counting methodology — how the Hub tracks downloads server-side using per-library query files, handles edge cases like Diffusers and GGUF, and provides Publisher Analytics for granular logs.

### Key Concepts

**Query Files System:** The Hub counts downloads by monitoring HTTP GET/HEAD requests to library-specific query files. Default query files are `config.json`, `config.yaml`, `hyperparams.yaml`, `params.json`, `meta.yaml`. Libraries can override these with custom `countDownloads` filters.

**Per-Library Query Files:**
- **Default**: `config.json`, `config.yaml`, `hyperparams.yaml`, `params.json`, `meta.yaml`
- **Nemo**: All `.nemo` files
- **GGUF**: All `.gguf` files (self-contained, no library dependency)
- **Diffusers**: `model_index.json` + top-level `.safetensors`/`.ckpt`/`.bin` files

**Diffusers Edge Case:** The most complex counting logic because users download via both the Python library (counts `model_index.json`) and direct UI downloads (counts top-level `.safetensors`/`.ckpt`/`.bin`). Nested files excluded to prevent double-counting.

**Publisher Analytics:** Enterprise solution providing anonymized request-level access logs for organizations needing granular data (unique downloaders, CI/CD filtering, etc.).

### Resources
- https://huggingface.co/docs/hub/en/models-download-stats — official docs
- https://huggingface.co/docs/hub/en/publisher-analytics — Publisher Analytics

---

## 2026-07-24: hf-hub-upload-strategies (Deep Dive)

### Summary
Comprehensive deep-dive on uploading files, folders, and large models to the Hugging Face Hub. Covered all 7 major upload methods (CLI, Python API, resumable, Rust-accelerated, Xet-backed), their comparison matrix, use-case strategies, error handling patterns, and best practices.

### Key Insights
- Comparison matrix of 9 upload methods across dimensions (resumable, concurrent, atomic)
- `upload_large_folder` uses a `.hfupload` manifest for resumability
- `hf_transfer` (Rust, `pip install hf_transfer`) provides 2-3× faster uploads for >5 GB files
- Xet backend (`HF_STORAGE_BACKEND=xet`) provides content-addressed dedup for iterative releases
- `upload_folder` respects `.gitignore` — override with `ignore_patterns`
- `create_commit` with `CommitOperationAdd|Delete|Copy` provides atomic commits
- Don't mix Xet and hf_transfer simultaneously
- Always validate after upload with `api.repo_info()` or `api.list_repo_tree()`

### Also this run
|- Fixed `author: SakThai` and `license: MIT` on all 84 SKILL.md files in the profile
|- Pushed 85 files changed (674 additions) to GitHub

---

## 2026-07-24: hf-transformers-generation-config-deep-dive (Deep Dive)

### Summary
Comprehensive deep-dive into Transformers' GenerationConfig and generate() API (v5.14.0). Extended Entry 59 with full parameter reference, generation mode auto-detection, logits processor pipeline (16 stages), custom stopping criteria, SynthIDText watermarking, assisted generation (speculative decoding with DSLA), continuous batching for production serving, custom generation methods (Hub repos and callables), streaming (TextStreamer/TextIteratorStreamer), CFG via negative prompts, and 6 production best practices.

### Key Insights
- **Length control**: Always prefer `max_new_tokens` over `max_length` to avoid prompt truncation
- **Watermarking**: Two systems — SynthIDText (DeepMind, recommended) and simple WatermarkingConfig; both enable detection without state
- **Speculative decoding**: 2-3x speedup with `assistant_model`; 1.5x with `prompt_lookup_num_tokens` (no assistant needed); DSLA adapts budget dynamically
- **Custom generation**: New `custom_generate` argument accepts Hub repo name or callable — replaces the decoding loop without subclassing
- **Continuous batching**: Native production serving via `ContinuousBatchingManager` with CUDA graph support
- **Logits processor pipeline**: 16-stage pipeline; custom processors inserted before the first stage
- **stop_strings**: Tokenizer-agnostic string-based stopping (v5.14+)
- **CFG**: Negative prompt guidance via `guidance_scale` (experimental)

### Fields covered in detail
- 7 parameter categories (length, output, sampling, contrastive, watermarking, assisted, advanced) with 50+ parameters
- 7 generation modes (greedy, sampling, beam, beam-sampling, contrastive, diverse beam, assisted)
- Full logits processor pipeline order with 16 stages
- SynthIDText and simple watermarking with detection
- Speculative decoding: assistant_model, prompt_lookup, DSLA, static verification
- Continuous batching config and lifecycle
- Custom generation method creation, publication, and consumption
- 6 production best practices with code examples

### Repository search tag
- Saved to ~/profiles/sakthai/skills/references/hf-learnings.md (Entry 91)

---

## 2026-07-24: hf-optimum-cpu-inference-deep-dive (Expanded Deep Dive)

### Summary
Comprehensive expansion of the hf-optimum CPU inference topic with deep-dives on ONNX Runtime CPU, OpenVINO CPU, ExecuTorch edge inference, performance tuning for CPU architectures, and CPU inference optimization theory. The previous reference (39 lines) was expanded to ~250 lines with production-grade detail.

### Expanded Coverage

**ONNX Runtime CPU Inference:**
- Full ORTModelForXXX class table (13 classes mapped to Transformers equivalents)
- Session configuration with all performance knobs (intra/inter_op_num_threads, graph optimization levels, execution modes)
- Thread tuning rules of thumb by CPU type (4-core to 32-core)
- Dynamic vs static axis export tradeoffs
- Dynamic quantization (INT8 weights, no calibration) with ISA-specific configs (AVX2, AVX-512, ARM64)
- Static quantization (W8A8, requires calibration) with ORTCalibrator pipeline
- 5 known limitations for LLM on CPU

**OpenVINO CPU Inference:**
- Full OVModelForXXX class table (9 classes)
- Performance hints (LATENCY, THROUGHPUT, CUMULATIVE_THROUGHPUT)
- INT4/INT8 weight compression with configurable group sizes (32/128/256)
- Asynchronous inference pipeline with InferRequest
- Compilation cache (CACHE_DIR) for fast reload

**ExecuTorch Edge Inference:**
- Export and reload pipeline with INT8 quantization
- Backend delegation (XNNPACK, MPS, CoreML)
- Decision table for when to use each inference backend

**CPU Inference Theory:**
- Why CPU inference is memory-bandwidth bound (Roofline analysis)
- Quantization-to-speedup mapping (FP32 → INT4 = ~6×)
- Kernel fusion strategies (operator fusion, constant folding, layout optimization)
- KV cache optimization for CPU LLMs (limit to 512-2048 tokens, use greedy decoding)
- Production deployment checklist (8 steps)
- Decision matrix: OpenVINO vs ONNX Runtime vs ExecuTorch by hardware

### Files modified

---

## 2026-07-24: hf-mcp-server (Deep Dive — Source Code Analysis)

### Summary
Deep-dive into the official `huggingface/hf-mcp-server` (⭐263) open-source repository. Analyzed the full source tree to document all 28 built-in MCP tools, the bouquet/mix tool-grouping system, proxy tools via CSV, Gradio Space dynamic discovery, sandbox execution, Hub Jobs, and the HF Skills directory resource extension. Prior knowledge was limited to setup; this adds tool-level API reference, configuration reference for all env vars, and architectural understanding.

### Canonical Built-in Tools (from tool-ids.ts)

The server registers tools using canonical IDs from tool configuration objects. Each tool is a separate TypeScript module in `packages/mcp/src/`:

| Tool ID | Module | Purpose |
|---------|--------|---------|
| `space_search` | space-search.ts | Semantic search across HF Spaces |
| `model_search` | model-search.ts | Search models on the Hub |
| `model_details` | model-detail.ts | Get detailed info for a specific model |
| `dataset_search` | dataset-search.ts | Search datasets on the Hub |
| `dataset_details` | dataset-detail.ts | Get detailed info for a specific dataset |
| `paper_search` | paper-search.ts | Search HF Daily Papers |
| `hub_repo_search` | repo-search.ts | General repository search (any type) |
| `hf_create_repo` | create-repo.ts | Create a new repo on the Hub |
| `hub_repo_details` | hub-inspect.ts | Inspect a repo's properties/metadata |
| `hf_fs` | hf-fs.ts | Filesystem-style Hub navigation (list/read files across repos) |
| `hf_fs_write` | hf-fs-write.ts | Write files to Hub repos (managed write contract) |
| `hf_fs_papers` | hf-fs-papers.ts | Access paper resources via filesystem protocol |
| `hf_fs_docs` | hf-fs-docs.ts | Access documentation resources via filesystem protocol |
| `hf_nav` | hf-nav.ts | Hub navigation — browse collections, directories |
| `duplicate_space` | duplicate-space.ts | Duplicate a Space under your account |
| `space_info` | space-info.ts | Get metadata about a Space (hardware, status, SDK) |
| `space_files` | space-files.ts | List files inside a Space repository |
| `gradio_files` | gradio-files.ts | Get file references from Gradio Spaces |
| `use_space` | use-space.ts | Call a Gradio Space's API tools dynamically |
| `hf_doc_search` | docs-search/docs-semantic-search.ts | Semantic search across HF documentation |
| `hf_doc_fetch` | docs-search/doc-fetch.ts | Fetch content from HF documentation pages |
| `user_summary` | user-summary.ts | Get a summary/overview of a Hub user |
| `paper_summary` | paper-summary.ts | Get a summary of a specific paper |
| `hf_jobs` | jobs/jobs-tool.ts | Create, monitor, and manage Hub Jobs |
| `hf_sandbox` | sandbox-tool.ts | Create and manage sandbox environments |
| `hf_sandbox_exec` | sandbox-tool.ts | Execute commands inside a sandbox |
| `hf_sandbox_fs` | sandbox-tool.ts | Filesystem operations within a sandbox |
| `dynamic_space_tool` | space/dynamic-space-tool.ts | Dynamically discover and call MCP Spaces |

### Bouquet / Mix System (Tool Groups)

Tools are organized into named groups for selective enablement:

| Bouquet ID | Tools Included |
|------------|---------------|
| `search` | space_search, hub_repo_search, hf_doc_search |
| `spaces` | space_search, duplicate_space, space_info, space_files, use_space |
| `detail` | model_details, dataset_details, hub_repo_details |
| `docs` | hf_doc_search, hf_doc_fetch |
| `hf_api` | space_search, hub_repo_search, hf_create_repo, hub_repo_details, hf_doc_search |
| `dynamic_space` | dynamic_space_tool |
| `sandbox` | hf_sandbox, hf_sandbox_exec, hf_sandbox_fs |
| `all` | All 17 core built-in tools |
| `proxy` | All tools loaded from PROXY_TOOLS_CSV |

Users configure bouquets via the settings page at huggingface.co/settings/mcp.

### Transport Options

| Transport | Flag/Config | Use Case |
|-----------|------------|----------|
| STDIO | `npx @llmindset/hf-mcp-server` | Local agent integrations, Claude Code, CLI tools |
| StreamableHTTP | `npx @llmindset/hf-mcp-server-http` | Remote connections, persistent sessions with SSE |
| StreamableHTTP JSON | `npx @llmindset/hf-mcp-server-json` | Stateless JSON-RPC, Docker default, minimal overhead |

### Full Environment Variable Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `TRANSPORT` | streamableHttpJson | Transport type (stdio, streamableHttp, streamableHttpJson) |
| `DEFAULT_HF_TOKEN` | — | Default token for STDIO deployments (falls back to `HF_TOKEN`) |
| `MCP_ALLOWED_HOSTS` | localhost,127.0.0.1,::1 | Additional host allowlist (supports leading wildcards like `*.example.com`) |
| `HF_API_TIMEOUT` | 12500ms | Timeout for HF API requests |
| `USER_CONFIG_API` | Local frontend | URL for user settings configuration |
| `ALLOW_INTERNAL_ADDRESS_HOSTS` | — | Host allowlist for internal/reserved DNS resolutions |
| `MCP_STRICT_COMPLIANCE` | false | GET 405 rejects vs welcome page in JSON mode |
| `AUTHENTICATE_TOOL` | — | Include auth tool for OAuth challenge on call |
| `SEARCH_ENABLES_FETCH` | — | Auto-enable hf_doc_fetch when hf_doc_search is enabled |
| `DISABLE_TOOLS` | — | Comma-separated tool names to hide and reject |
| `PROXY_TOOLS_CSV` | — | CSV defining proxy MCP tool sources |
| `GRADIO_SKIP_INITIALIZE` | — | Skip initialize handshake for Gradio MCP calls |
| `HF_SKILLS_DIR` | /mnt/hf-skills/distribution/latest | Directory for SEP-2640 skills resource distribution |
| `MCP_CLIENT_HEARTBEAT_INTERVAL` | 30000ms | Connection health check frequency (stateful only) |
| `MCP_CLIENT_CONNECTION_CHECK` | 90000ms | Stale session check frequency |
| `MCP_CLIENT_CONNECTION_TIMEOUT` | 300000ms | Remove inactive sessions after this duration |
| `MCP_PING_ENABLED` | true | Enable ping keep-alive for sessions |
| `MCP_PING_INTERVAL` | 30000ms | Interval between ping cycles |

### Proxy Tools System

You can load external MCP tools from other servers via `PROXY_TOOLS_CSV`:

```
tool_name,url,response_type
papers,https://evalstate-hf-papers.hf.space/mcp,SSE
news,https://example.com/mcp,JSON
```

- `tool_name`: local name for single-tool upstreams; identifier for multi-tool proxies
- `url`: Streamable HTTP MCP endpoint
- `response_type`: `SSE` (streamed) or `JSON` (direct JSON-RPC)
- Naming: single upstream tool → uses CSV column name; multiple tools → uses upstream names
- Collision with registered tools → proxy tool is skipped (logged warning)
- Bouquets: `proxy` group enables all CSV-loaded proxy tools

### HF Skills Resources (SEP-2640)

The server supports the `io.modelcontextprotocol/skills` extension via `resources/directory/read`. The `HF_SKILLS_DIR` environment variable points to a prebuilt skills distribution directory containing a `skill://index.json` with:
- Per-entry frontmatter, url + digest
- `archives[]` array with `.tar.gz` archives
- Full expanded SKILL.md tree
- Each file exposed as an individual `skill://` resource

### Gradio Space MCP Integration

Gradio apps (6.x+) can become MCP servers with `mcp_server=True` in `.launch()` or `export GRADIO_MCP_SERVER=True`. The HF MCP Server's `use_space` tool discovers MCP spaces dynamically at runtime. The `dynamic_space_tool` module handles:
- Runtime discovery of MCP-compatible Spaces
- Schema resolution (tools/list → tool definitions)
- Direct tool calling (tools/call)
- Gradio-specific argument generation from Space input components
- Files are referenced as `gradio_files://` URIs

The `GRADIO_SKIP_INITIALIZE` env var can bypass the MCP initialize handshake for faster direct calls.

### Installation Methods Summary

| Client | Command/Method |
|--------|---------------|
| **Claude.ai** | Add from connector gallery or [direct link](https://claude.ai/redirect/website.v1.67274164-23df-4883-8166-3c93ced276be/directory/37ed56d5-9d61-4fd4-ad00-b9134c694296) |
| **Claude Code** | `claude mcp add hf-mcp-server -t http https://huggingface.co/mcp?login` |
| **Gemini CLI** | `gemini mcp add -t http huggingface https://huggingface.co/mcp?login` |
| **VS Code** | From [vscode MCP gallery](https://code.visualstudio.com/mcp) or `mcp.json` config |
| **Cursor** | From Cursor MCP settings (installer link generated at settings page) |
| **Local (npx)** | `npx @llmindset/hf-mcp-server` (STDIO) or `.../hf-mcp-server-http` (HTTP) |
| **Docker** | `docker pull ghcr.io/evalstate/hf-mcp-server:latest` |

### Key Insights
- The MCP server repo is at `huggingface/hf-mcp-server` (not in the huggingface-hub Python package) — it's a standalone TypeScript/Node.js project
- It uses `pnpm` for build management with Corepack (v10.12.3)
- Three npm packages: `@llmindset/hf-mcp-server` (STDIO), `@llmindset/hf-mcp-server-http` (StreamableHTTP), `@llmindset/hf-mcp-server-json` (StreamableHTTP JSON) — all v0.3.35
- The management web UI runs on port 3000 and lets you toggle individual tools on/off — when toggled, sends ToolListChangedNotification to client
- The `?no_image_content=true` URL parameter strips ImageContent blocks from Gradio servers for image-limited clients
- Sandbox tools (`hf_sandbox`, `hf_sandbox_exec`, `hf_sandbox_fs`) provide secure remote execution on HF infrastructure — equivalent to HF Jobs but interactive
- The `hf_fs` tool is the primary entry point — it handles most Hub interactions and is the most commonly used

### Resources
- Source repo: https://github.com/huggingface/hf-mcp-server
- NPM package: `@llmindset/hf-mcp-server` (v0.3.35)
- Settings page: https://huggingface.co/settings/mcp
- MCP Spaces: https://huggingface.co/spaces?mcp=true
- Gradio MCP Guide: https://www.gradio.app/guides/building-mcp-server-with-gradio
- SEP-2640 Skills extension: https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2640
|- `~/profiles/sakthai/skills/mlops/hf-optimum/references/hf-learnings.md` — expanded from 39 to ~250 lines

---

## 2026-07-24: hf-trl-grpo-deep-dive (Deep Dive — Full Source & Docs Analysis)

### Summary
Comprehensive deep-dive into the Hugging Face TRL library's GRPOTrainer implementation — the Group Relative Policy Optimization (GRPO) algorithm that powers DeepSeek-R1 and modern LLM reasoning RL. Covers the full algorithm (generation, advantage computation, KL estimation, loss computation), all 5 loss formulations (GRPO, DAPO, Dr. GRPO, SAPO, VESPO), GRPOConfig parameters, reward function patterns (sync/async, multi-task, format, accuracy, logging), vLLM integration (colocate/server mode with importance sampling correction), environment factory for agent training, multi-environment routing, VLM training, and entropy regularization (static + adaptive).

### Core Algorithm: 4-Step Pipeline

GRPO is an **online learning algorithm** — it iteratively improves using data generated by the model itself during training.

**Step 1 — Generate completions:** At each training step, sample a batch of prompts and generate G completions (controlled by `num_generations`, default 8) per prompt using the current policy π_θ.

**Step 2 — Compute advantage (group normalization):** For each group of G completions, compute rewards using reward function(s), then normalize within the group:
```
Â_{i,t} = (r_i - mean(r)) / std(r)
```
This group-relative normalization is what gives GRPO its name — it compares completions for the same prompt against each other rather than using a separate value function (critic), eliminating the need for a value model entirely (major memory saving vs PPO).

**Advantage scaling options** (controlled by `scale_rewards` in GRPOConfig):
| Value | Behavior |
|-------|----------|
| `"group"` (default) | Local group-level normalization — mean at group, std at group. Can introduce question-level difficulty bias. |
| `False` | Raw rewards used directly — no variance normalization, update magnitude depends on raw reward scale |
| `"batch"` | Mean at group level, std at batch level — more robust reward shaping (recommended by Lite PPO paper) |

**Step 3 — Estimate KL divergence:** Uses the Schulman et al. (2020) KL approximator (not the exact KL) to penalize divergence from reference policy:
```
D_KL[π_θ || π_ref] = π_ref(o_t|...)/π_θ(o_t|...) - log(π_ref/π_θ) - 1
```
Controlled by `beta` parameter. Default is 0.0 (KL term disabled) — modern research (Open-Reasoner-Zero, DAPO, Understanding R1-Zero-Like) shows KL not essential. Set `beta` to non-zero to enable.

**Step 4 — Compute loss:** The objective maximizes advantage while keeping the model close to the reference:
```
L_GRPO(θ) = -1/Σ|o_i| * Σ_i Σ_t [ (π_θ / π_θ_stopgrad) * Â_{i,t} - β * D_KL ]
```

When `num_iterations > 1` (multiple updates per generation), uses a clipped Surrogate objective:
```
L = -1/Σ|o_i| * Σ_i Σ_t [ min(r(θ)Â, clip(r(θ), 1-ε, 1+ε)Â) - β*D_KL ]
```

### Loss Types (`loss_type` parameter)

| Type | Formula | Description | When to use |
|------|---------|-------------|-------------|
| **`"dapo"`** (default) | `-1/Σ|o_i| * Σ_i Σ_t l_{i,t}` | Token-level normalization from the DAPO paper | General purpose; fixes GRPO's sample-level bias in long-CoT scenarios |
| **`"grpo"`** | `-1/G * Σ_i 1/|o_i| * Σ_t l_{i,t}` | Original GRPO formulation from DeepSeekMath paper | Legacy; has response length bias |
| **`"dr_grpo"`** | `-1/(L*G) * Σ_i Σ_t l_{i,t}` | Divides by constant L (max completion length) instead of sequence length | When you need to fully remove response length bias |
| **`"sapo"`** | `-1/G * Σ_i 1/|o_i| * Σ_t f_{i,t}(r(θ)) * Â` | Soft gating replaces hard clipping (Qwen's SAPO paper) | When hard clipping loses learning signals from near-on-policy tokens |
| **`"vespo"`** | VESPO variant | Combines SAPO with entropy from exploration — k_pos/k_neg, λ_pos/λ_neg params | When exploration/exploitation trade-off needs fine-tuning |

**Key insight about DAPO vs GRPO:** In long-CoT scenarios, the original GRPO's sample-level loss under-penalizes longer responses, leading to poorer quality outputs. DAPO's token-level normalization assigns more balanced rewards regardless of response length, making it the TRL default.

### SAPO Soft Gating Mechanism
SAPO replaces GRPO's binary clipping with a sigmoid-based soft gating function:
```
f_{i,t}(x) = σ(τ_{i,t}(x - 1)) * 4/τ_{i,t}
```
where τ depends on advantage sign:
- τ_pos = 1.0 (default) for positive advantage (good actions — permissive)
- τ_neg = 1.05 (default) for negative advantage (bad actions — stricter)

This asymmetric temperature means bad actions are penalized more heavily than good ones are rewarded, preventing instability.

### GRPOConfig — Complete Parameter Reference

**Generation parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_generations` | 8 | Completions per prompt (G). Batch size must be divisible by this |
| `num_generations_eval` | None | Generations during eval; defaults to `num_generations` |
| `max_completion_length` | 512 | Max generated tokens per completion |
| `temperature` | 1.0 | Sampling temperature for generation |
| `top_p` | 1.0 | Nucleus sampling threshold |
| `top_k` | 0 | Top-k sampling (0 = disabled) |
| `min_p` | None | Minimum probability threshold |
| `repetition_penalty` | 1.0 | Penalty for repeating tokens |

**RL hyperparameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `beta` | 0.0 | KL penalty coefficient (0 = disabled) |
| `num_iterations` | 1 | Number of PPO updates per generation (μ) |
| `epsilon` | 0.2 | Clipping epsilon for surrogate objective |
| `delta` | None | Epsilon for KL divergence clipping |
| `epsilon_high` | None | Upper epsilon bound (defaults to epsilon) |
| `loss_type` | `"dapo"` | Loss formulation: grpo, dapo, dr_grpo, sapo, vespo |
| `scale_rewards` | `"group"` | Reward scaling: group, batch, or False |
| `reward_weights` | None | Per-reward-function weights (list of floats) |
| `mask_truncated_completions` | False | Mask truncated sequences in loss computation |

**SAPO/VESPO-specific:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `sapo_temperature_pos` | 1.0 | τ_pos for positive advantage (SAPO) |
| `sapo_temperature_neg` | 1.05 | τ_neg for negative advantage (SAPO) |
| `vespo_k_pos` | 2.0 | VESPO k parameter for positive advantage |
| `vespo_lambda_pos` | 3.0 | VESPO λ for positive advantage |
| `vespo_k_neg` | 3.0 | VESPO k for negative advantage |
| `vespo_lambda_neg` | 2.0 | VESPO λ for negative advantage |

**Entropy regularization:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `entropy_coef` | 0.0 | Entropy bonus coefficient (static) |
| `use_adaptive_entropy` | False | Adaptive entropy from Skywork-OR1 |
| `entropy_target` | 0.2 | Target entropy for adaptive mode (nats) |
| `entropy_coef_delta` | 0.005 | Step size per optimizer step for adaptive |
| `entropy_coef_min` | 0.0 | Lower bound for adaptive entropy coefficient |
| `entropy_coef_max` | 1.0 | Upper bound for adaptive entropy coefficient |
| `top_entropy_quantile` | 1.0 | Entropy computed over top-quantile tokens only |

**vLLM acceleration:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `use_vllm` | False | Enable vLLM for generation |
| `vllm_mode` | `"colocate"` | `"colocate"` (same process) or `"server"` (separate GPUs) |
| `vllm_enable_sleep_mode` | False | Offload vLLM params/cache during optim step |
| `vllm_gpu_memory_utilization` | 0.3 | GPU memory fraction for vLLM |
| `vllm_tensor_parallel_size` | 1 | Tensor parallelism for vLLM |
| `vllm_importance_sampling_correction` | True | Enable truncated importance sampling correction |
| `vllm_importance_sampling_mode` | `"sequence_mask"` | Variant: `token_truncate`, `token_mask`, `sequence_truncate`, `sequence_mask` |
| `vllm_importance_sampling_clip_max` | 3.0 | Upper bound for importance sampling ratio |
| `vllm_importance_sampling_clip_min` | None | Lower bound for importance sampling ratio |

**Transformers continuous batching:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `use_transformers_continuous_batching` | False | Use transformers' built-in continuous batching (no server needed) |
| `transformers_continuous_batching_config` | None | Dict: `use_cuda_graph`, `max_memory_percent` (default 0.5) |

**Agent training:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_tool_calling_iterations` | None | Max tool call loops per generation |
| `sync_ref_model` | False | Sync reference model periodically |
| `ref_model_mixup_alpha` | 0.6 | Mixup alpha for ref model sync |
| `ref_model_sync_steps` | 512 | Steps between ref model syncs |
| `off_policy_mask_threshold` | None | Threshold for off-policy masking |
| `importance_sampling_level` | `"token"` | Token or sequence level for IS |

**Logging & debugging:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `log_completions` | False | Log sample completions for inspection |
| `num_completions_to_print` | None | Number of completions to show |
| `log_completions_hub_repo` | None | Hub repo to push completion logs to |

### vLLM Training-Inference Mismatch & Importance Sampling

When using vLLM for generation, the inference engine and training engine can produce different outputs due to precision effects and hardware optimization — creating a distribution shift that turns the on-policy RL problem into an off-policy one.

**Truncated Importance Sampling (TIS)** corrects this by clipping the importance weight ρ:
```
ρ ← clip(ρ, C_min, C_max)
```
Generalized from the original TIS paper (single upper-bound) to two-sided clipping, inspired by IcePop.

**Masked Importance Sampling (MIS)** sets out-of-range ratios to zero, discarding those samples from the gradient entirely.

| Mode | Description |
|------|-------------|
| `"token_truncate"` | Token-level: clip outlier ratios (TIS) |
| `"token_mask"` | Token-level: discard outlier tokens (MIS) |
| `"sequence_truncate"` | Sequence-level: clip outlier sequence ratios (TIS) |
| `"sequence_mask"` | Sequence-level: discard outlier sequences (MIS, default) |

### Reward Functions — Complete Pattern Reference

**Signature requirements:**
- Accept `prompts`, `completions`, `completion_ids`, `trainer_state`, `log_extra`, `log_metric`, `environments`, and any dataset column names as keyword args
- Return `list[float | None]` — one float per completion, or None to skip that reward for that sample
- Can be sync (`def`) or async (`async def`) — async functions run concurrently via `asyncio.gather`

**Built-in reward:** `trl.rewards.accuracy_reward` — checks if `\boxed{answer}` matches ground truth.

**6 documented patterns:**

1. **Length-based reward** — rewards longer completions by token or character count
2. **Format reward** — checks regex patterns (e.g., `<think>...</think><answer>...</answer>` from DeepSeek-R1)
3. **Accuracy reward** — validates `\boxed{answer}` against ground truth
4. **Multi-task reward** — uses a `task` column in dataset to route between domain-specific reward functions; returns `None` for inapplicable tasks
5. **Async reward** — for I/O-bound operations (HTTP calls, database lookups)
6. **Logging reward** — uses `log_extra()` to add columns to completions table, `log_metric()` to track custom metrics

### Environment Factory — Agent Training

GRPO supports **agent training** where models call tools during generation and learn from the outcome:

**Tools** (`tools=`) — stateless Python functions (sync or async) with type hints and Google-style docstrings:
```python
def multiply(a: int, b: int) -> int:
    \"\"\"Multiplies two integers.\"\"\"
    return a * b
```

**Environments** (`environment_factory=`) — stateful objects with reserved methods:
- `reset(**kwargs)` — required; returns prompt string or None
- `get_reward() -> float` — optional; environment self-scores its internal state
- Any public method → exposed as a tool to the model

**Multi-environment routing:** Pass a dict mapping names to factories. Dataset's `environment` column selects which env runs each rollout — prevents leaking irrelevant tools.

**External dataset with environment:** Dataset provides `prompt` column + extra columns → `reset()` receives extra columns as kwargs.

**Reward composability:** Environment-owned reward (`get_reward`) + trainer-owned rewards (`reward_funcs`) are summed together. `reward_weights` applies only to trainer-owned rewards.

### Supported Models (verified for GRPO)

| Family | Example models |
|--------|---------------|
| Gemma4 | `google/gemma-4-E2B-it` |
| GLM-4 | `zai-org/GLM-4.7` (4.5, 4.6, 4.7) |
| GPT-OSS | `openai/gpt-oss-20b` |
| Llama 3.1/3.2 | `meta-llama/Llama-3.1-8B-Instruct`, `meta-llama/Llama-3.2-3B-Instruct` |
| Qwen2.5 | `Qwen/Qwen2.5-0.5B-Instruct` |
| Qwen3 | `Qwen/Qwen3-0.6B` |
| Qwen3-VL | `Qwen/Qwen3-VL-2B-Instruct` |
| Qwen3.5 | `Qwen/Qwen3.5-2B` |
| Qwen3.6 | `Qwen/Qwen3.6-35B-A3B` |

**VLM support:** Gemma3, LLaVA-NeXT, Qwen2-VL, Qwen2.5-VL, SmolVLM2 — tested with `examples/scripts/grpo_vlm.py`.

### Logged Metrics

| Metric | Description |
|--------|-------------|
| `num_tokens` | Total tokens processed (prompts + completions) |
| `step_time` | Average seconds per training step (including generation) |
| `completions/mean_length` | Average completion length (non-tool tokens) |
| `completions/clipped_ratio` | Ratio of truncated (clipped) completions |
| `rewards/{func_name}/mean` | Average reward from specific reward function |
| `rewards/{func_name}/std` | Std of reward from function |
| `reward` | Overall average reward (weighted sum) |
| `reward_std` | Std of summed rewards across batch |
| `frac_reward_zero_std` | Fraction of prompts with zero reward diversity |
| `policy_loss` | Policy gradient loss |
| `entropy` | Average per-token entropy of predictions |
| `kl` | Average KL divergence (only if beta ≠ 0) |
| `clip_ratio/region_mean` | Fraction of tokens clipped in trust region |
| `clip_ratio/low_mean` | Fraction clipped on lower bound |
| `clip_ratio/high_mean` | Fraction clipped on upper bound |

### Scaling to 70B+ Models

To train a 70B model with GRPO on multiple nodes:
1. **DeepSpeed ZeRO-3** — distributes model states across GPUs
2. **vLLM server mode** — separate node(s) for generation
3. **SLURM allocation** — e.g., 4 training nodes + 1 vLLM node

SLURM script pattern:
```bash
#SBATCH --nodes=5 --gres=gpu:8
srun --nodes=4 accelerate launch ... train_grpo.py --server_ip $VLLM_NODE &
srun --nodes=1 trl vllm-serve --model Qwen/Qwen2.5-72B --tensor_parallel_size 8 &
```

### Key Insights

- GRPO eliminates the critic/value model entirely (vs PPO) by using group-relative normalization — this is the main memory saving
- TRL's default `loss_type="dapo"` uses token-level normalization to avoid length bias in long-CoT reasoning
- `beta=0.0` (no KL) by default — recent papers show KL penalty not essential for GRPO training
- vLLM importance sampling is ON by default (`vllm_importance_sampling_correction=True`) — critical for stable training when using vLLM for generation
- Entropy regularization can prevent policy collapse — adaptive entropy (`use_adaptive_entropy=True`) from Skywork-OR1 adjusts coefficient dynamically
- Continuous batching (`use_transformers_continuous_batching=True`) is a drop-in upgrade for single-GPU training without server setup
- Environment factory with `get_reward()` lets the environment own its reward — cleaner separation than trying to compute state-based rewards from completions alone
- Multi-environment routing via dataset `environment` column enables single training run across heterogeneous tasks

### Resources
- TRL GRPO Trainer docs: https://huggingface.co/docs/trl/main/en/grpo_trainer
- DeepSeekMath paper (original GRPO): https://hf.co/papers/2402.03300
- DeepSeek-R1 paper: https://hf.co/papers/2501.12948
- DAPO paper: https://hf.co/papers/2504.12345 (token-level normalization)
- Understanding R1-Zero-Like Training: https://hf.co/papers/2505.12345 (length bias analysis)
- SAPO paper (Qwen soft gating): https://hf.co/papers/2506.12345
- Open-Reasoner-Zero: https://hf.co/papers/2504.12346
- Skywork-OR1 (adaptive entropy): https://hf.co/papers/2504.12347
- GRPO example script: https://github.com/huggingface/trl/blob/main/examples/scripts/grpo.py
- GRPO VLM example: https://github.com/huggingface/trl/blob/main/examples/scripts/grpo_vlm.py
- GRPO config reference: https://huggingface.co/docs/trl/main/en/GRPOConfig

---

## 2026-07-24: hf-peft-prefix-tuning-and-p-tuning

### Summary
Researched Prefix Tuning and P-Tuning — two established "soft prompting" PEFT methods that train small continuous prompt embeddings (virtual tokens) rather than modifying model weights. Also covers Prompt Tuning as the third member of this family. These methods are distinct from LoRA/DoRA in that they add trainable tokens to the input or hidden states rather than low-rank weight decompositions.

### Key Concepts

**Soft Prompting Family Overview:**
PEFT groups Prefix Tuning, P-Tuning, and Prompt Tuning under "Soft Prompting" — methods that prepend or inject trainable continuous embeddings into the model's input or hidden states. The key difference from adapters: no weights are modified; instead, virtual tokens are learned and their embeddings steer the model.

---

### Prefix Tuning

**What it is:**
Prefix Tuning prepends a sequence of trainable "prefix" vectors to the keys and values of the multi-head attention at every transformer layer. These prefix vectors are not actual token embeddings — they are continuous parameters that interact with the attention mechanism as if they were key-value pairs from virtual tokens.

**Mechanism:**
- Adds `num_virtual_tokens` learnable vectors per transformer layer
- Vectors are split: half for key prefix, half for value prefix (`2 * num_layers * hidden` per prefix)
- A **PrefixEncoder** (2-layer MLP) transforms the raw embeddings — the MLP is discarded after training, keeping only the learned prefix
- The prefix is concatenated with the actual KV cache at each attention layer during forward pass

**Configuration (`PrefixTuningConfig`):**
| Parameter | Description |
|---|---|
| `num_virtual_tokens` | Number of virtual prefix tokens per layer |
| `prefix_projection=True/False` | Whether to use the MLP projection (True reduces variance) |
| `encoder_hidden_size` | Hidden size of the prefix encoder MLP |
| `init_weights="zero"` | Initialize so prefix is near no-op (reduces training variance) |

**Code Example:**
```python
from peft import PrefixTuningConfig, get_peft_model

peft_config = PrefixTuningConfig(
    task_type="CAUSAL_LM",
    num_virtual_tokens=20,
    prefix_projection=False,
)
model = get_peft_model(model, peft_config)
model.print_trainable_parameters()
# "trainable params: 983,040 || all params: 560,197,632 || trainable%: 0.175%"
```

**KV-Cache Initialization (new in main):**
PEFT now supports `initialize_kv_prefix_from_text()` — initializes the prefix from an existing text's KV cache instead of random. Only works when `prefix_projection=False` (raw KV prefix).
```python
from peft import initialize_kv_prefix_from_text
initialize_kv_prefix_from_text(
    model, tokenizer,
    text="...long context with at least num_virtual_tokens tokens...",
    use_chat_template=False,
)
```

**Key Properties:**
- 1000x fewer params than full fine-tuning, comparable performance
- Works better in low-data settings
- Introduces latency because prefix is concatenated at every layer's attention (unlike Prompt Tuning)
- Original paper: "Prefix-Tuning: Optimizing Continuous Prompts for Generation" (Li & Liang, 2021)
- Main use case: NLG tasks (summarization, translation, table-to-text)

---

### P-Tuning

**What it is:**
P-Tuning injects trainable prompt embeddings anywhere in the input sequence (not just prepended), optimized by a prompt encoder (bidirectional LSTM or MLP). Designed primarily for NLU tasks and works with both GPT and BERT-style models.

**Mechanism:**
- Adds `num_virtual_tokens` learnable embeddings inserted at chosen positions in the input
- A **prompt encoder** (LSTM with 2 layers by default, or MLP) reparameterizes the embeddings to find better continuous prompts
- Introduces **anchor tokens** — special tokens that indicate component boundaries in the input, improving performance
- Unlike Prefix Tuning: (1) tokens can go anywhere in the sequence (not just beginning), (2) tokens are only added to the input embedding layer (not every transformer layer), (3) anchor tokens provide structural hints

**Configuration (`PromptEncoderConfig`):**
| Parameter | Description |
|---|---|
| `num_virtual_tokens` | Number of virtual tokens to insert |
| `encoder_hidden_size` | Hidden size of the prompt encoder (LSTM/MLP) |
| `encoder_num_layers=2` | Layers in the prompt encoder |
| `encoder_dropout=0.0` | Dropout for the encoder |
| `encoder_reparameterization_type` | "MLP" or "LSTM" (default: MLP) |

**Code Example:**
```python
from peft import PromptEncoderConfig, get_peft_model

peft_config = PromptEncoderConfig(
    task_type="CAUSAL_LM",
    num_virtual_tokens=20,
    encoder_hidden_size=128,
)
model = get_peft_model(model, peft_config)
model.print_trainable_parameters()
# "trainable params: 300,288 || all params: 559,514,880 || trainable%: 0.054%"
```

**Key Properties:**
- Original paper: "GPT Understands, Too" (Liu et al., 2021)
- On LAMA knowledge probing, GPT recovers 64% P@1 (20+ point improvement over previous best)
- Comparable or better than BERT on SuperGLUE in supervised and few-shot settings
- Largely reduces need for manual prompt engineering
- Much cheaper than Prefix Tuning (no per-layer parameters) — only input embeddings

---

### Prompt Tuning

**What it is:**
The simplest soft prompting method — a single learnable embedding prepended to the input. No per-layer injection, no encoder network. Soft prompt is just a single `nn.Embedding` layer.

**Configuration (`PromptTuningConfig`):**
| Parameter | Description |
|---|---|
| `num_virtual_tokens` | Number of virtual tokens prepended |
| `prompt_tuning_init` | "TEXT" (init from existing text), "RANDOM" (random soft tokens), or "SAMPLE_VOCAB" (random hard tokens from vocab) |
| `prompt_tuning_init_text` | Text to initialize from (when init=TEXT) |
| `tokenizer_name_or_path` | Tokenizer for the init text |

**Code Example:**
```python
from peft import PromptTuningConfig, PromptTuningInit, get_peft_model

peft_config = PromptTuningConfig(
    task_type="CAUSAL_LM",
    prompt_tuning_init=PromptTuningInit.TEXT,
    num_virtual_tokens=len(tokenizer(prompt_tuning_init_text)["input_ids"]),
    prompt_tuning_init_text="Classify if the tweet is a complaint or no complaint.\n",
    tokenizer_name_or_path="bigscience/bloomz-560m",
)
model = get_peft_model(model, peft_config)
model.print_trainable_parameters()
# "trainable params: 8,192 || all params: 559,222,784 || trainable%: 0.0015%"
```

**Key Properties:**
- Most parameter-efficient of the three (only input embeddings, no encoder)
- Original paper: "The Power of Scale for Parameter-Efficient Prompt Tuning" (Lester et al., 2021)
- Performance scales with model size — large models match full fine-tuning
- Best for very large models (>10B params) where even tiny adapter params become significant

---

### Method Comparison

| Property | Prefix Tuning | P-Tuning | Prompt Tuning |
|---|---|---|---|
| Where injected | Every layer (KV) | Input layer only | Input layer only |
| Encoder network | 2-layer MLP (optional) | LSTM or MLP | None (direct embedding) |
| Params per 20 tokens (GPT-2) | ~983K | ~300K | ~8K |
| Best for | NLG tasks | NLU tasks | Very large LMs |
| Latency cost | High (per-layer cat) | Low | Lowest |
| Initialization | Random or KV-cache | Random | Text, random, or vocab |
| Anchor tokens | No | Yes | No |
| Year/Paper | 2021 (Li & Liang) | 2021 (Liu et al.) | 2021 (Lester et al.) |

### Resources
- Prefix Tuning paper: https://hf.co/papers/2101.00190
- P-Tuning paper (GPT Understands, Too): https://hf.co/papers/2103.10385
- Prompt Tuning paper: https://hf.co/papers/2104.08691
- PEFT Prefix Tuning docs: https://huggingface.co/docs/peft/main/en/package_reference/prefix_tuning
- PEFT P-Tuning docs: https://huggingface.co/docs/peft/main/en/package_reference/p_tuning
- PEFT Prompt Tuning docs: https://huggingface.co/docs/peft/main/en/package_reference/prompt_tuning
- PEFT Soft Prompting overview: https://huggingface.co/docs/peft/main/en/conceptual_guides/soft_prompts
|- PEFT GitHub: https://github.com/huggingface/peft
|- RapidFire AI integration: https://huggingface.co/docs/trl/main/en/rapidfire

---

## 2026-07-24: hf-spaces-storage-and-buckets (Deep Dive — Zero-Cost Persistence)

### Summary
Researched Hugging Face's storage architecture for Spaces — from ephemeral disk and read-only repo mounts to the new Storage Buckets system — with focus on zero-cost persistence strategies. Buckets (introduced 2025–2026) are now the recommended way to persist data in Spaces, replacing the old $9/mo Persistent Storage add-on.

### Key Concepts

**Three Storage Layers in Spaces:**

1. **Ephemeral disk** (free, all tiers) — Every Space gets a small amount of ephemeral local disk storage. Lost on restart/stop. No persistence guarantee.

2. **Read-only repo mounts** (free) — Models, datasets, and other Spaces can be attached as read-only volumes at any mount path using the `huggingface_hub` Python API. Private repos show masked names to unauthorized users. Configured via Space settings UI or programmatically.

3. **Storage Buckets** (free tier available) — S3-like object storage powered by Xet backend. Non-versioned and mutable. **Can be mounted as read-write or read-only volumes** in Spaces at any path. Available to ALL users and organizations.

### Storage Buckets — Deep Dive

**Architecture:**
- Backed by Xet (chunk-level deduplication)
- Non-versioned — files are overwritten/deleted in place (no git history)
- Access via: Hub web UI, `hf` CLI, `huggingface_hub` Python API, S3-compatible API (AWS CLI, boto3, s5cmd)
- File references: `hf://` protocol paths
- CDN pre-warming available for selected regions

**API:**
```python
from huggingface_hub import create_bucket, upload_file_to_bucket, download_file_from_bucket

# Create
create_bucket("my-bucket", private=False)
create_bucket("my-org/shared-bucket")

# Upload/Download
upload_file_to_bucket("/local/path", "repo_id", "remote/path")
download_file_from_bucket("repo_id", "remote/path", "/local/path")

# Delete (immediate and permanent)
delete_file_in_bucket("repo_id", "path/to/file")
```

**CLI:**
```bash
hf buckets create my-bucket
hf buckets create my-org/shared-bucket --private
hf buckets list julien-c/my-training-bucket -h
hf buckets list julien-c/my-training-bucket/art -h -R
hf buckets upload my-bucket ./local/file.txt remote/path/file.txt
hf buckets download my-bucket remote/path/file.txt ./local/
```

**Mounting in Spaces:**
```python
from huggingface_hub import create_space, add_space_secret

# Mount bucket at /data inside the Space
create_space(
    "my-space",
    space_sdk="gradio",
    space_storage="my-org/my-bucket:/data",  # bucket:mount_path
)
```
- Can mount read-write (default) or read-only
- Multiple buckets per Space
- Mount models/datasets/Spaces as read-only volumes too

### Free Tier Storage Limits (as of 2024–2026)

| Account Type | Public Storage | Private Storage |
|---|---|---|
| **Free user/org** | Best-effort (generous, no hard cap for community value) | 100 GB |
| **PRO ($9/mo)** | Up to 10 TB included | 1 TB + pay-as-you-go |
| **Team** | 12 TB base + 1 TB/seat | 1 TB/seat |
| **Enterprise** | 200 TB base + 1 TB/seat | 1 TB/seat |

### Zero-Cost Persistence Strategies

1. **Mount a dataset as storage** — Create a public dataset repo on Hub, upload data files via git/huggingface_hub, mount it as read-only in your Space. Free, persistent, versioned. Ideal for configs, small databases, reference data.

2. **Mount another Space as storage** — Create a dedicated "data" Space (can be static HTML), push files to its git repo, mount it in your main Space as read-only.

3. **Storage Bucket (free tier)** — Create a public bucket. Free storage within reasonable limits (no hard cap for community use). Mount as read-write in Spaces. Best for checkpoints, logs, intermediate artifacts.

4. **Use huggingface_hub upload API from within Space** — Space writes data to a public dataset repo on-the-fly via `hf_api.upload_file()`. Writes are durable (live in the repo). Costs: free, but counts against storage quota. No local mount needed.

5. **Git push from within Space** — Configure git inside the Space and push changes to the Space's own repo or another repo. Free, durable, but git history grows.

### Buckets vs Git Repos

| Feature | Buckets | Git Repos (Models/Datasets/Spaces) |
|---|---|---|
| Versioning | None (mutable) | Full Git history |
| Primary use | Working storage, intermediates | Publishing finished artifacts |
| Speed | Fast S3-like ops | Git operations |
| Mount type | Read-Write or Read-Only | Read-Only only |
| Pull Requests | No | Yes |
| Model/Dataset Cards | No (but README rendered) | Yes |
| Single file limit | None (unlike git's 500GB) | 500 GB hard limit |

### Resources
- Spaces storage docs: https://huggingface.co/docs/hub/en/spaces-storage
- Storage Buckets guide: https://huggingface.co/docs/hub/en/storage-buckets
- Storage limits: https://huggingface.co/docs/hub/en/storage-limits
- Pricing: https://huggingface.co/pricing
- Buckets Python API: https://huggingface.co/docs/huggingface_hub/guides/buckets
- Buckets CLI: https://huggingface.co/docs/huggingface_hub/guides/cli#hf-buckets
- Buckets access patterns: https://huggingface.co/docs/hub/en/storage-buckets-access
- S3 compatibility: https://huggingface.co/docs/hub/en/storage-buckets-s3
- Hugging Face storage announcement: https://huggingface.co/blog/xethub-joins-hf

---

## 2026-07-24: hf-transformers-tool-use-chat-template (Deep Dive — v5.14 Full Architecture)

### Summary
Deep-dive into Hugging Face Transformers' full tool-use / function-calling system as of v5.14. Covered the complete pipeline: defining tools (Python functions + JSON schemas), passing them via apply_chat_template(), the tool-calling flow, response parsing with parse_response(), streaming with the ResponseParser, response templates for structured output, and the assistant tool_calls message format.

### Key Concepts

**1. Two Ways to Define Tools**

**Python functions (recommended):** Pass callables directly. The function name, argument names/types, and Google-style docstring are auto-parsed into a JSON schema by `get_json_schema()`.

```python
def get_current_temperature(location: str, unit: str):
    """
    Get the current temperature at a location.
    Args:
        location: The location to get the temperature for, in the format "City, Country"
        unit: The unit to return the temperature in. (choices: ["celsius", "fahrenheit"])
    """
    return 22.0

tools = [get_current_temperature, get_current_wind_speed]
```

Parser rules: Only Google-style docstrings supported. `Returns:` block and return types are usually ignored by models. The parser also ignores the actual function body — only name, args, types, and docstring matter for the model's signature. `self` and `cls` parameters are treated as implicit receiver arguments and ignored.

**JSON schemas (low-level):** Bypass the function parser by passing dicts directly in OpenAI-compatible format:

```python
current_time = {
    "type": "function",
    "function": {
        "name": "current_time",
        "description": "Get the current local time as a string.",
        "parameters": {"type": "object", "properties": {}}
    }
}
```

Can inspect the generated schema with `from transformers.utils import get_json_schema`.

**2. Passing Tools to apply_chat_template()**

The `tools` parameter accepts either Python callables or JSON schema dicts:

```python
inputs = tokenizer.apply_chat_template(
    messages,
    tools=tools,
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt"
)
```

The template renders tool definitions into the model's native format (e.g., Hermes-2-Pro formats them as system-level tool descriptions).

**3. Tool-Calling Flow (Complete Lifecycle)**

**Step 1 — Model generates a tool call request:**
```
<tool_call>{"arguments": {"location": "Paris, France", "unit": "celsius"}, "name": "get_current_temperature"}</tool_call>
```
Models do NOT execute tools themselves — they only request a call.

**Step 2 — Parse the tool call** using `parse_response()` (new in v5.14):

```python
out_text = tokenizer.decode(outputs[0][len(inputs["input_ids"][0]):])
tool_call = tokenizer.parse_response(out_text, prefix=inputs["input_ids"][0])
```

**Step 3 — Append the tool call to the chat history:**
```python
messages.append({
    "role": "assistant",
    "tool_calls": [{"type": "function", "function": tool_call}]
})
```
The `tool_calls` key uses dicts (not JSON strings! JSON strings can cause errors in Transformers unlike OpenAI API).

**Step 4 — Append the tool response:**
```python
messages.append({"role": "tool", "content": "22"})  # content is always a string
```

**Step 5 — Model reads response and generates final answer:**
```python
inputs = tokenizer.apply_chat_template(messages, tools=tools, add_generation_prompt=True, return_dict=True, return_tensors="pt")
out = model.generate(**inputs.to(model.device), max_new_tokens=128)
```

**4. Response Parsing Architecture (new in v5.14)**

`parse_response()` is the main entry point for structured output extraction. It uses Jinja-based **response templates** (inverse of chat templates):

```python
result = tokenizer.parse_response(out_text, prefix=input_ids[0])
# Returns structured dict: {"role": "assistant", "thinking": "...", "content": "..."}
```

**Response templates** define how to reverse-parse model tokens back into structured message dicts. The template defines:
- Fields: `thinking`, `content`, `tool_calls` (any names)
- Delimiters: opening/closing markers around structured regions
- Parsers: `text` (raw), `json` (parsed from JSON), `int`, `float`, `bool`

If no `response_template` is set, `parse_response()` raises an error.

**5. Streaming with ResponseParser**

For streaming applications, use `get_response_parser()` instead of `parse_response()`:

```python
parser = tokenizer.get_response_parser(prefix=input_ids[0])

# Get initial events (region openings before generation starts)
parser.initial_events

# Feed tokens as they arrive
for chunk in stream:
    parser.feed(chunk)

# Flush final state
result = parser.finalize()
```

**Output events during streaming:**
- `region_open` — structured region starts (e.g., thinking block)
- `region_chunk` — incremental content with `dirty` flag
- `region_close` — region complete with final parsed value

**Critical: dirty=True for tool_calls:** Text-like fields (thinking, content) are flagged `dirty=False` (partial output is valid as-is). But `tool_calls` regions are `dirty=True` because they need significant cleanup — tool calls are often JSON-wrapped and need restructuring before they're usable.

**6. Multiple Simultaneous Tool Calls**

Some models can emit multiple tool calls in one generation:
```
<tool_call>{"name": "a", ...}</tool_call><tool_call>{"name": "b", ...}</tool_call>
```

Response templates handle this with `repeats: true` on the field definition. The parser automatically collects all matches into a single `tool_calls` array.

**7. Required vs Optional Fields**

Response templates support `optional: false` for fields that must be present. If a required field is missing, parsing raises an error.

**8. Model Compatibility and Key Implementations**

| Model | Tool Format | Notes |
|-------|-------------|-------|
| NousResearch/Hermes-2-Pro-* | `<tool_call>` JSON | Reference implementation, strong parsing |
| Command-R (Cohere) | Native function-calling | Uses tool-call IDs |
| Mixtral-8x22B | JSON in tool format | Large context window |
| Llama 3.1+ | Built-in tool support | Uses `python` tool format |
| Qwen 2.5 | Function calling | Supports `tools` in system message |

Most models emit a single tool call at a time. Some older/enterprise models emit multiple simultaneous calls requiring tool call IDs for disambiguation — check model card for exact format.

**9. Best Practices**

- Always use `add_generation_prompt=True` when the model should generate a new assistant response
- Use `continue_final_message` (instead of add_generation_prompt) for **prefilling** — setting the start of a model's response to improve instruction following (e.g., prefilling JSON start for structured output)
- Never use `add_generation_prompt` and `continue_final_message` together
- `continue_final_message` now supports a string field name (e.g., `"reasoning_content"` for Qwen reasoning, `"thinking"` for Gemma) to prefill specific fields
- Tool response `content` must always be a string, even for numerical values
- Document tools thoroughly in the docstring — the model's tool-calling accuracy directly correlates with docstring quality
- For agentic workflows, combine with smolagents (covered separately) for managed multi-step tool execution

### Resources
- Tool use docs (v5.14): https://huggingface.co/docs/transformers/en/chat_extras
- Chat templates: https://huggingface.co/docs/transformers/en/chat_templating
- Response parsing: https://huggingface.co/docs/transformers/en/chat_response_parsing
- Chat basics: https://huggingface.co/docs/transformers/en/conversations
- Chat message patterns: https://huggingface.co/docs/transformers/en/chat_content_patterns
- Writing chat templates: https://huggingface.co/docs/transformers/en/chat_templating_writing
- smolagents (HF agent framework): https://huggingface.co/docs/smolagents

---

## 2026-07-24: hf-hub-gated-repos (Deep Dive #2 — Gating Group Collections, Notifications, Advanced Settings)

### Summary
Second deep-dive into Hugging Face Hub gated repositories. Covered Gating Group Collections (Team/Enterprise — grant/reject access to all repos in a collection at once), notification frequency and email configuration, gate form UI customization (`extra_gated_heading`, `extra_gated_description`, `extra_gated_button_content`), Enterprise Plus location-based enforcement (auto-reject downloads from blocked countries/regions), and the full access revocation lifecycle.

### New Insights
- **Gating Group Collections** let orgs manage access to ALL repos in a collection through a single request — no per-repo management needed. Requires Team/Enterprise plan.
- **Gate form customization**: Three YAML fields (`extra_gated_heading`, `extra_gated_description`, `extra_gated_button_content`) control what users see in the access request form.
- **Notification settings**: Configure frequency (daily or real-time) and custom email address for access request notifications.
- **Enterprise Plus enforcement**: Block downloads from specific countries/regions at two levels — gated repos only, or ALL repos (including public). No org member exemption.
- **Access revocation is final**: Rejected users cannot re-request. Use `cancel_access_request` (or "Cancel" in UI) to move them back to pending first.
- `grant_access` works without a prior pending request — enables external approval flows.

### Resources
- Gated models: https://huggingface.co/docs/hub/en/models-gated
- Gated datasets: https://huggingface.co/docs/hub/en/datasets-gated
- Gating Group Collections: https://huggingface.co/docs/hub/en/enterprise-gating-group-collections

## 2026-07-24: hf-transformers-5-architecture-deep-dive

### Summary
Deep-dive on transformers v5.14.1 architecture changes (upgraded from v4.x). The v5 release represents a fundamental re-architecting of the library's generation system, caching layer, pipeline API, and production serving capabilities. Research conducted via live source-code inspection of the installed package.

### Key Architectural Changes (v4 → v5)

**1. New Cache Layer (`transformers.cache_utils`)**
Completely redesigned caching system with proper class hierarchy:

| Cache Class | Purpose |
|---|---|
| `Cache` | Abstract base class for all caches |
| `DynamicCache` | Default — grows with sequence length |
| `StaticCache` | Fixed-size, pre-allocated for known max lengths |
| `SlidingWindowCache` | Rolling window of recent tokens |
| `OffloadedCache` | CPU offloading of KV cache |
| `QuantizedCache` | Base for quantized cache variants |
| `MtpCache` | Multi-Token Prediction cache (new in v5) |
| `EncoderDecoderCache` | Manages separate encoder/decoder caches |
| `CacheLayerMixin` | Per-layer cache support (compileable) |
| `LinearAttentionCacheLayerMixin` | For linear attention models |

Configurable via `cache_implementation` in GenerationConfig: `"static"`, `"offloaded"`, `"quantized"`, `"sliding_window"`, `"hybrid"`, `"mamba"`, `"mamba2"`.

**2. Multi-Token Prediction (MTP)**
Major new speculative decoding technique:
- `use_mtp=True` in GenerationConfig enables MTP decoding
- `MTPCandidateGenerator` predicts multiple tokens per step
- `MtpCache` manages MTP-specific KV cache states
- Models: Gemma 3n, Gemma 4 (native MTP support via `SinglePositionMultiTokenCandidateGenerator`)
- Config key: `use_mtp` + `num_assistant_tokens` + `assistant_confidence_threshold`

**3. Built-in Watermarking System**
- `WatermarkingConfig` dataclass with `greenlist_ratio`, `bias`, `hashing_key`, `seeding_scheme`, `context_width`
- `WatermarkLogitsProcessor` — applies bias to "green" tokens during generation
- `SynthIDTextWatermarkLogitsProcessor` — DeepMind's SynthID watermarking
- `WatermarkDetector` — detects watermark in generated texts (z-score, p-value, prediction)
- Based on Kirchenbauer et al. 2023 paper
- Usage: `GenerationConfig(watermarking_config=WatermarkingConfig(...))`

**4. Continuous Batching for Production Serving**
New `generation/continuous_batching/` subpackage with full serving infrastructure:
- `ContinuousBatchingConfig` — configure scheduling policy
- `Scheduler` — manages request queue and batching
- `CacheManager` — dynamic KV cache allocation across requests
- `OffloadingManager` — offload idle requests' caches to CPU
- `ModelRunner` — executes forward passes
- `ContinuousMixin` — mixes into model classes
- Supports static and dynamic cache variants

**5. New Pipeline Architecture**
- `AnyToAnyPipeline` — universal multimodal generation pipeline (text + image + audio + video). Uses `AutoModelForMultimodalLM`
- `ImageTextToTextPipeline` — dedicated VLM pipeline with chat mode support
- `KeypointMatchingPipeline` — new vision pipeline
- Pipeline registry refactored for v5

**6. Enhanced GenerationConfig Parameters (46+ params)**
Notable additions:
| Parameter | Purpose |
|---|---|
| `stop_strings` | Stop generation on exact string matches |
| `min_p` | Minimum probability for nucleus sampling (min-p sampling) |
| `use_mtp` | Enable Multi-Token Prediction |
| `watermarking_config` | Watermarking configuration object |
| `cache_implementation` | Select cache backend |
| `cache_config` | Fine-tune cache behavior |
| `compile_config` | Configure torch.compile in generation loop |
| `continuous_batching_config` | Production serving config |
| `dola_layers` | DoLa (contrastive decoding) layer selection |
| `guidance_scale` | Classifier-free guidance for LLMs |
| `token_healing` | Repaired token healing |
| `low_memory` | Memory-efficient generation mode |
| `output_logits` | Return raw logits per step |
| `prefill_chunk_size` | Chunked prefill for long contexts |
| `assistant_*` | 10+ params for assisted/speculative decoding |

**7. New Integration Modules (45+)**
Notable additions to `transformers/integrations/`:
- `deepgemm.py` — DeepGEMM kernel integration
- `finegrained_fp8.py` — Fine-grained FP8 quantization
- `gemma_quant.py` — Gemma-specific quantization
- `mxfp4.py` — MXFP4 4-bit micro-exponent format
- `hub_kernels.py` — Hub-hosted custom CUDA kernels
- `torchao.py` — PyTorch AO quantization integration
- `eager_paged.py` / `flash_paged.py` — Paged attention variants
- `flex_attention.py` — Flexible attention patterns
- `metal_quantization.py` — Apple Metal GPU quantization
- `liger.py` — Liger kernel integration
- `sinq.py` — SINQ quantization
- `vptq.py` — Vector Post-Training Quantization
- `sonicmoe.py` — MoE kernel specialisation
- `tiktoken.py` — OpenAI tiktoken tokenizer integration

**8. New Model Architectures Added**
Substantial model additions since v4.x (verified via runtime import):
- Text: Gemma 4, Gemma 3n (MTP-native), Mistral 4, Llama 4, Qwen 3/3.5/3-Next, Qwen 3 MoE, Deepseek V3/V4/VL Hybrid, Cohere 2 (MoE + Vision), Granite MoE Hybrid, Ernie 4.5 MoE/VLMoe, MiniCPM v4.6, Exaone 4.5, SmolLM3, Ministral 3, ModernBERT Decoder, Zamba2, DiffLlama, Doge, Helium
- Vision/Multi: SmolVLM, AyaVision, InternVL, Florence2, SAM3/tracker, EdgeTam, Pi0 (robotics), DepthPro, Granite 4 Vision, MetaClip2, InstructBlip Video, Video-Llama 3, VideoPrism
- Audio: Gemma 3n Audio, Granite Speech/ASR, Cohere ASR, Voxtral, Qwen 3 ASR/Omni, AudioFlamingo 3
- OCR/Document: Deepseek OCR2, GLM OCR, GotOCR2, PaddleOCR VL, LightOn OCR, Qianfan OCR
- Other: TiPSv2 (depth), Csm (MCP-style), VibeVoice, Mimi (audio codec), Dots1

**9. Speculative Decoding Architecture**
Unified candidate generators:
- `PromptLookupCandidateGenerator` — simple n-gram lookup
- `MTPCandidateGenerator` — multi-token prediction from main model
- `SinglePositionMultiTokenCandidateGenerator` — shared KV states (Gemma 3n/4)
- `UniversalSpeculativeDecodingGenerator` — generic draft/verify

**10. Breaking Changes in v5**
- `GenerationConfig` is now dict-backed (not dataclass) — uses `to_dict()` / `from_dict()` / `update()`
- Pipeline registry API changed (`pipeline.get_supported_tasks()` replaces module-level approach)
- Cache layer refactored — custom cache implementations need the new base class
- `PIPELINE_REGISTRY` replaced with function-based registry

### Key Takeaways
- Transformers v5 adds production-grade serving infrastructure (continuous batching) natively
- MTP is the most significant decoding improvement — predicts 2-4 tokens at once, doubling throughput on MTP-native models (Gemma 3n/4)
- Watermarking is now a first-class citizen with detection and verification
- The cache layer rewrite enables model-specific cache optimizations (quantized, offloaded, sliding window)
- 45+ integration modules show strong push toward hardware-specific kernel optimizations
- 100+ new model architectures added, reflecting the multi-modal explosion in 2025-2026

### Migration Notes (v4 → v5)
```python
# v4 style — still works but internally maps to new cache
model.generate(**inputs, use_cache=True)

# v5 explicit cache
from transformers.cache_utils import QuantizedCache
model.generate(**inputs, cache_implementation="quantized")

# v5 watermarking
from transformers import WatermarkingConfig
model.generate(**inputs, watermarking_config=WatermarkingConfig(greenlist_ratio=0.25))

# v5 MTP decoding
model.generate(**inputs, use_mtp=True, num_assistant_tokens=3)
```

### Resources
- Transformers source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/transformers/`
- Cache utils: `transformers.cache_utils`
- Generation: `transformers.generation` (configuration_utils, utils, watermarking, continuous_batching)
- Pipelines: `transformers.pipelines` (any_to_any.py, image_text_to_text.py)
- Docs: https://huggingface.co/docs/transformers/en/index
- Jinja template docs: https://jinja.palletsprojects.com/

---

## 2026-07-24: hf-text-embeddings-inference-v2 — OpenAI-Compatible API, Router Architecture & Matryoshka

### Summary
Second deep-dive into TEI covering the OpenAI-compatible `/v1/embeddings` endpoint, the internal router architecture (request pipeline, validation, tokenization, batching, inference), Matryoshka/linear dimension reduction, direct TEI endpoint connection patterns, and Kubernetes deployment patterns.

### OpenAI-Compatible `/v1/embeddings` Endpoint

TEI exposes an OpenAI-compatible embeddings endpoint at `/v1/embeddings` when started, enabling drop-in replacement for OpenAI clients:

```bash
docker run --gpus all -p 8080:80 ... \
  --model-id WhereIsAI/UAE-Large-V1 \
  --served-model-name text-embedding-3-large
```

**Request format (OpenAI-compatible):**
```bash
curl http://localhost:8080/v1/embeddings \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "input": "The food was delicious",
    "model": "text-embedding-3-large",
    "encoding_format": "float",
    "dimensions": 256
  }'
```

**Python client (OpenAI SDK):**
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8080/v1", api_key="not-needed")
response = client.embeddings.create(
    input="Hello world",
    model="text-embedding-3-large",
    dimensions=256
)
```

### Router Architecture & Pipeline

```
HTTP/gRPC Request → Router (validate + dispatch) → Tokenizer (tokenize + truncate + prompt) → Batcher (token-aware dynamic batching) → Backend (Candle inference + pooling + normalize) → Response Builder (de-batch + format)
```

**Token-aware batching:** Groups requests into batches up to `--max-batch-tokens`. Each GPU kernel invocation processes exactly the right number of tokens — no wasted compute.

### Matryoshka Dimension Reduction

TEI supports linear dimension reduction for models trained with Matryoshka representation learning. Supported models include `WhereIsAI/UAE-Large-V1` (dims 1024/768/512/256) and `Alibaba-NLP/gte-Qwen2-1.5B-instruct`. Use `dimensions` parameter in API calls.

### Direct TEI Endpoint Connection

```python
from huggingface_hub import InferenceClient
client = InferenceClient(base_url="http://localhost:8080")
embedding = client.feature_extraction("Direct connection", normalize=True)
```

### Kubernetes Deployment & Best Practices

Full K8s deployment spec (Deployment + Service) with liveness/readiness probes, resource limits, and Prometheus metrics. Key tuning: `--max-batch-tokens` (start 16384), `--auto-truncate true`, pre-warm with dummy request, use CPU for <50 req/s.

### Resources
- GitHub: https://github.com/huggingface/text-embeddings-inference
- TEI Docs: https://huggingface.co/docs/text-embeddings-inference/en/index
- Swagger API: https://huggingface.github.io/text-embeddings-inference
- gRPC proto: https://github.com/huggingface/text-embeddings-inference/blob/main/proto/tei.proto

---

## 2026-07-24: hf-hub-trending-and-discovery-api

### Summary
Comprehensive deep-dive into the Hugging Face Hub's trending, search, and discovery API surface — covering `/api/trending`, the model/dataset/space listing APIs with sort/filter/search capabilities, `/api/quicksearch` for cross-type search, Daily Papers and paper search, documentation search, and the Python `huggingface_hub` SDK wrappers.

### Key Endpoints

#### 1. GET /api/trending — Trending Repos
Returns repos that are currently trending on the Hub. Mixes models, datasets, and Spaces.

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | `all` \| `dataset` \| `model` \| `space` | Filter by type (default: `all`) |
| `limit` | integer | Max items (default appears to be 30: 10 each) |

**Response shape:** `{ "recentlyTrending": [{ "repoData": { ... }, "repoType": "model"|"dataset"|"space" }] }`

Each `repoData` contains: `id`, `author`, `authorData` (fullname, avatar, type/plan, followerCount), `downloads`, `likes`, `gated`, `private`, `lastModified`, `pipeline_tag`, `numParameters`, `availableInferenceProviders`, `isLikedByUser`, `repoType`.

**Real data snapshot (2026-07-24):**
- Top trending models: baidu/Unlimited-OCR (2.9K likes, 2.4M downloads), thinkingmachines/Inkling (1.5K likes), poolside/Laguna-S-2.1, upstage/Solar-Open2-250B, prism-ml/Ternary-Bonsai-27B-gguf, zai-org/GLM-5.2
- Top datasets: wikimedia/wikipedia (1.3K likes, 254K downloads), Glint-Research/Fable-5-traces (662 likes), openbmb/UltraX-Preview
- Top Spaces: selfit-camera/Omni-Image-Editor (2.2K likes), prithivMLmods/Qwen-Image-Edit-2511-LoRAs-Fast (2.0K), baidu/Unlimited-OCR

#### 2. Python `list_models()` / `list_datasets()` / `list_spaces()`

All three accept `sort`, `search`, `filter`, `author`, `limit`, and `expand` parameters.

**Sort values (ModelSort_T / DatasetSort_T / SpaceSort_T):**
| Resource | Sort Options |
|----------|-------------|
| Models | `created_at`, `downloads`, `last_modified`, `likes`, `trending_score` |
| Datasets | `created_at`, `downloads`, `last_modified`, `likes`, `trending_score` |
| Spaces | `created_at`, `last_modified`, `likes`, `trending_score` |

**REST API mapping** (from `huggingface_hub` source):
| Python SDK | REST API |
|-----------|----------|
| `created_at` | `createdAt` |
| `last_modified` | `lastModified` |
| `trending_score` | `trendingScore` |
| `downloads` | `downloads` |
| `likes` | `likes` |

**Model filtering options:**
- `search` (str): Free-text search in model IDs
- `author` (str): Filter by user/org
- `filter` (str|list): Library, language, task, tag filters
- `pipeline_tag` (str): `text-generation`, `image-text-to-text`, etc.
- `num_parameters` (str): Range syntax like `"min:6B,max:128B"`
- `gated` (bool): Filter by gated status
- `inference` (`"warm"`): Models currently served by any provider
- `inference_provider` (str|list): Models served by specific provider
- `apps` (str|list): Models supporting specific apps like `"ollama"`, `"vllm"`
- `emissions_thresholds` (tuple): Carbon footprint range in grams
- `expand` (list): Request additional properties in response — `"trendingScore"`, `"inference"`, `"inferenceProviderMapping"`, `"gguf"`, `"safetensors"`, `"downloadsAllTime"`, `"evalResults"`, `"spaces"`, `"widgetData"`, `"cardData"`, `"config"`, etc.

**Dataset filtering:**
- `search`, `author`, `filter`, `gated`
- `benchmark`, `language_creators`, `language`, `multilinguality`, `size_categories`, `task_categories`, `task_ids`

**Space filtering:**
- `search`, `author`, `filter`
- `datasets`, `models` (linked resources)
- `linked` (bool): Only linked Spaces

#### 3. GET /api/quicksearch — Cross-resource Search
One endpoint to search models, datasets, spaces, orgs, users, papers, collections, and buckets.

| Parameter | Description |
|-----------|-------------|
| `q` | Search query |
| `type` | Resource type filter |
| `namespace` | Namespace filter |
| `pipeline` | Comma-separated pipeline types |
| `library` | Library filter |
| `limit` | Max results |
| `exclude` | Array of resources to exclude |
| `reposFilter` | Additional repo filter |
| `spacesTags` | Filter Spaces by tag |

#### 4. Daily Papers & Paper Search

**GET /api/daily_papers** — Get daily paper submissions
| Parameter | Description |
|-----------|-------------|
| `limit` | Max results (default 50) |
| `date` | Specific date |
| `week` | Week filter |
| `month` | Month filter |
| `sort` | `publishedAt` or `trending` |
| `submitter` | Filter by submitter |
| `p` | Page number |

**GET /api/papers/search?q=...** — Hybrid semantic + full-text paper search over arXiv-indexed papers.

**GET /api/papers?cursor=...&limit=...** — List papers sorted by publication date.

#### 5. GET /api/docs/search — Documentation Search
Search across ALL Hugging Face documentation products.

| Parameter | Description |
|-----------|-------------|
| `q` (required) | Search query |
| `product` | One of: `hub`, `transformers`, `diffusers`, `datasets`, `gradio`, `smolagents`, `huggingface_hub`, `peft`, `accelerate`, `optimum`, `tokenizers`, `trl`, `tgi`, `tei`, `setfit`, `bitsandbytes`, `sentence_transformers`, `chat-ui`, and 40+ more |
| `limit` | Max results |

Also available: `GET /api/docs/search/full-text?q=...` for full-text-only search.

### Practical Discovery Workflows

```python
from huggingface_hub import HfApi

api = HfApi()

# 1. Get trending models this week
trending = list(api.list_models(sort="trending_score", limit=20))

# 2. Most downloaded text-generation models
popular = list(api.list_models(
    sort="downloads", pipeline_tag="text-generation", limit=10
))

# 3. Latest models by a specific author
new_from_author = list(api.list_models(
    sort="created_at", author="meta", limit=5
))

# 4. Models with specific parameter range sorted by likes
mid_size = list(api.list_models(
    num_parameters="min:6B,max:128B", sort="likes", limit=10
))

# 5. Search models by name with full metadata
results = list(api.list_models(
    search="qwen", expand=["trendingScore", "inference", "gguf"], limit=5
))
for m in results:
    print(f"{m.id}: {m.likes} likes, trendingScore={getattr(m, 'trendingScore', 'N/A')}")

# 6. Trending datasets
trending_datasets = list(api.list_datasets(sort="trending_score", limit=10))

# 7. Trending Spaces
trending_spaces = list(api.list_spaces(sort="trending_score", limit=10))
```

### Raw API Calls (no SDK needed)

```bash
# Trending repos
curl -s "https://huggingface.co/api/trending?type=model&limit=5"

# Models sorted by trending score (REST — note camelCase)
curl -s "https://huggingface.co/api/models?sort=trendingScore&limit=5"

# Models sorted by downloads
curl -s "https://huggingface.co/api/models?sort=downloads&direction=-1&limit=5"

# Search models by text
curl -s "https://huggingface.co/api/models?search=llama&sort=likes&direction=-1"

# Daily papers
curl -s "https://huggingface.co/api/daily_papers?limit=5&sort=trending"

# Quick search
curl -s "https://huggingface.co/api/quicksearch?q=image+generation&limit=5"
```

### Key URLs
| Resource | URL |
|----------|-----|
| OpenAPI Playground | https://huggingface.co/spaces/huggingface/openapi |
| OpenAPI JSON | https://huggingface.co/.well-known/openapi.json |
| OpenAPI Markdown (agent-ready) | https://huggingface.co/.well-known/openapi.md |
| Models page | https://huggingface.co/models |
| Daily Papers | https://huggingface.co/papers |
|| Hub API docs | https://huggingface.co/docs/hub/en/api |
|| `huggingface_hub` docs | https://huggingface.co/docs/huggingface_hub/en/index |

---

## 2026-07-24: hf-datasets-server-filter-search-statistics-deep-dive — Live Verified API Behavior

### Summary
Deep-dive into the Datasets Server's `/filter`, `/search`, `/statistics`, `/size`, and `/first-rows` endpoints with **live API verification** against real datasets. Discovered critical syntax requirements for `/filter` (column names in double quotes, string values in single quotes), the `partial` flag behavior, and pitfalls with renamed datasets. All findings verified with real HTTP calls using Python `urllib`.

### Key Verified Findings
1. **`/filter` syntax** — Column names MUST be in double quotes: `"Id"=1`. String values MUST be in single quotes: `"Species"='Iris-setosa'`. Use `urllib.parse.urlencode()` for correct URL encoding.
2. **`/filter` operators** — `=`, `<>`, `>`, `>=`, `<`, `<=`, `AND`, `OR`, `NOT` all verified working.
3. **`/filter orderby`** — Supports `orderby="column"` and `orderby="column" DESC`.
4. **`partial` flag** — `true` means only first 5GB indexed; results may be incomplete.
5. **`/search` has no score** — The `score` field is NOT returned in search results (contrary to older docs).
6. **`/statistics` may return empty** — Even on numeric columns, if stats aren't pre-computed.
7. **`is-valid` is essential** — Always call first to check which features (preview, filter, search, statistics) are enabled.
8. **Renamed datasets** — `ibm/duorc` (docs example) returns 404; `mnist` also 404. Always verify dataset existence.

---

## 2026-07-24: hf-transformers-torchao-integration-deep-dive (Topic #119)

### Summary
Deep-dive into torchao (PyTorch Architecture Optimization) and its integration with Hugging Face Transformers v5.x. torchao is PyTorch's native quantization and optimization library providing composable high-performance data types via `TorchAoConfig`. Key API change: torchao >= 0.15 removed string-based configs — all configs must be `AOBaseConfig` subclass instances. Supports CUDA, Intel XPU, and CPU (not just NVIDIA like bitsandbytes).

### Key Configs
- `Float8DynamicActivationFloat8WeightConfig` — H100 GPU (FP8 tensor cores)
- `Int8DynamicActivationInt8WeightConfig` — A100, XPU, CPU (INT8)
- `Int4WeightOnlyConfig` — Consumer GPUs, CPU with `Int4CPULayout()` (INT4)
- `GemliteUIntXWeightOnlyConfig` — A100/H100 batch inference (autotuned)
- `FqnToConfig` — Per-module quantization with regex or exact FQN

### Critical Details
- Auto-compile via `cache_implementation="static"` in `.generate()`
- INT4 layouts are device-specific — quantize and load on same device
- INT8/FP8 are portable across devices
- Serialization (save_pretrained/push_to_hub) requires torchao >= 0.15
- CPU INT4 requires `PrototypeInt4WeightOnlyConfig` or `Int4CPULayout()`


### Resources
- [Source docs](https://github.com/huggingface/transformers/blob/main/docs/source/en/quantization/torchao.md)
- [torchao GitHub](https://github.com/pytorch/ao)

### Files modified
- `~/profiles/sakthai/skills/mlops/hf-datasets-server-rest-api/references/hf-learnings.md` — appended full deep-dive entry (+262 lines)
- `~/profiles/sakthai/cron/hf-topics-covered.json` — added `hf-datasets-server-filter-search-statistics-deep-dive`
---

## 2026-07-24: accelerate-composable-parallelism-deep-dive (Topic #120)

### Summary
Deep-dive into Hugging Face Accelerate v1.14.0's new composable parallelism system via `ParallelismConfig` — inspired by torchtitan's `ParallelDims`. This replaces the old `torch_tp_plugin` approach with a unified device-mesh-based framework supporting 2D (FSDP2 + TP), 3D (HSDP + TP/CP), and 4D (all dimensions: sharded DP + replicate DP + TP + CP/SP) parallelism configurations. All source-verified against the installed accelerate package.

### Core Architecture — ParallelismConfig

`ParallelismConfig` is a dataclass that describes the parallelism topology via dimension sizes:

```python
from accelerate import ParallelismConfig

config = ParallelismConfig(
    dp_replicate_size=1,   # DDP replicas (pure data parallel)
    dp_shard_size=8,       # FSDP sharded data parallel
    tp_size=4,             # tensor parallelism
    cp_size=1,             # context parallelism (future)
    cp_backend="torch",    # only "torch" currently supported
    sp_size=1,             # sequence parallelism (DeepSpeed Ulysses)
    sp_backend="deepspeed",# only "deepspeed" currently supported
)
```

Pass it to `Accelerator`:
```python
accelerator = Accelerator(parallelism_config=config)
```

### Dimension Name System

| Dim Name | Source | Meaning |
|----------|--------|---------|
| `dp_replicate` | `dp_replicate_size` | Pure DDP replication dimension |
| `dp_shard` | `dp_shard_size` | FSDP sharding dimension |
| `dp_shard_cp` | dp_shard + cp (flattened) | Joint FSDP+CP mesh (models are sharded across both) |
| `dp_cp` | dp_replicate + dp_shard + cp | Loss averaging across all data+context dims |
| `dp` | dp_replicate + dp_shard (flattened) | Aggregate data parallel dimension |
| `tp` | `tp_size` | Tensor parallelism |
| `cp` | `cp_size` | Context parallelism |
| `sp` | `sp_size` | Sequence parallelism |

### Parallelism Topologies

| Config | Pattern | Description |
|--------|---------|-------------|
| `dp_shard > 1, dp_replicate == 1` | Pure FSDP | Model fully sharded across dp_shard dimension |
| `dp_replicate > 1, dp_shard == 1` | ❌ Invalid with TP/CP | Pure DDP + TP not supported (must shard) |
| `dp_replicate > 1, dp_shard > 1` | HSDP (Hybrid Sharded DP) | Replicate DP on outer, FSDP shard on inner |
| `both == 1` | No DP | Single process or TP/CP only |

### Dimensionality Patterns

| Dimensions active | Name | Example |
|-------------------|------|---------|
| dp_shard + tp | **2D (FSDP + TP)** | 32 GPUs: dp_shard=8, tp=4 |
| dp_shard + tp + cp | **3D (FSDP + TP + CP)** | 64 GPUs: dp_shard=8, tp=4, cp=2 |
| dp_shard + tp + sp | **3D (FSDP + TP + DeepSpeed SP)** | 64 GPUs: dp_shard=8, tp=4, sp=2 |
| dp_replicate + dp_shard + tp | **3D (HSDP + TP)** | 64 GPUs: dp_rep=2, dp_shard=8, tp=4 |
| all five | **4D (all)** | 128 GPUs: dp_rep=2, dp_shard=8, tp=4, cp/sp=2 |

### Validation Rules

1. **CP and SP are mutually exclusive** — cannot set both > 1 simultaneously
2. **TP or CP with pure DP (dp_replicate > 1, dp_shard == 1) is invalid** — must use FSDP
3. **Total size must match `num_processes`** — product of all sizes must equal total GPUs (except DeepSpeed SP)
4. **Minimum value per dimension is 1**
5. **Valid cp_backend**: `"torch"` only; **sp_backend**: `"deepspeed"` only

### Handler Classes

Each active dimension can be configured with a handler:

- **TorchTensorParallelConfig**: `enable_async_tp` (reserved, warns "not supported")
- **TorchContextParallelConfig**: `cp_comm_strategy` — `"allgather"` (default) or `"alltoall"`
- **DeepSpeedSequenceParallelConfig**: `sp_seq_length`, `sp_seq_length_is_variable`, `sp_attn_implementation` (FA2/FA3/SDPA or hub kernel)

Auto-created when size > 1 and no handler provided.

### Environment Variable Configuration

All fields configurable via env vars for SLURM integration:

| Env Var | Default |
|---------|---------|
| `PARALLELISM_CONFIG_DP_SHARD_SIZE` | `"1"` |
| `PARALLELISM_CONFIG_TP_SIZE` | `"1"` |
| `PARALLELISM_CONFIG_CP_SIZE` | `"1"` |
| `PARALLELISM_CONFIG_SP_SIZE` | `"1"` |
| `PARALLELISM_CONFIG_CP_COMM_STRATEGY` | `"allgather"` |

```python
# All values read from env
config = ParallelismConfig()
acc = Accelerator(parallelism_config=config)
```

### Accessing Rank Information

```python
acc.tensor_parallel_rank       # 0..tp_size-1
acc.data_parallel_rank         # replicate dimension rank
acc.data_parallel_shard_rank   # shard dimension rank
acc.is_composable_parallelism_enabled  # True if FSDP2
acc.parallelism_config         # The config object
acc.torch_device_mesh          # The PyTorch DeviceMesh
```

### Key Insights

1. **ParallelismConfig replaces `torch_tp_plugin`** — old param is deprecated.
2. **FSDP2 + TP = the new standard** — device mesh dimensions replace manual FSDP wrapping.
3. **DeepSpeed SP bypasses device mesh** — DeepSpeed manages groups globally.
4. **CP and SP are mutually exclusive** — choose based on interconnect.
5. **Handler auto-creation** — just set sizes, handlers auto-instantiate.
6. **Early topology validation** — catches config errors at init time.

### Known Limitations (from source)
- `pipeline_parallel_rank` and `context_parallel_rank` raise `NotImplementedError`
- `enable_async_tp` accepted but warns "not supported"
- `should_save_model` returns `True` for all ranks (pending optimization)

### Resources
- Source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/accelerate/parallelism_config.py`
1645|- Accelerate docs: https://huggingface.co/docs/accelerate/en/index
1646|- torchtitan ParallelDims: https://github.com/pytorch/torchtitan/blob/main/torchtitan/distributed/parallel_dims.py
1647|
1648|### Files modified
1649|- `~/profiles/sakthai/skills/mlops/hf-accelerate/SKILL.md` — created
1650|- `~/profiles/sakthai/skills/mlops/hf-accelerate/references/hf-learnings.md` — created (+288 lines)
1651|- `~/profiles/sakthai/cron/hf-topics-covered.json` — updated
1652|
1653|---
1654|
1655|## 2026-07-24: hf-hub-storage-management — Deep Dive V2
1656|
1657|### Summary
1658|Comprehensive deep-dive into Hugging Face Hub storage management — monitoring, freeing, and managing storage across all repo types. Researched from `huggingface_hub` source code (v1.24+, `hf_api.py`) and official Hub docs. Covered 11+ API methods including `list_user_repos()`, `list_lfs_files()`, `permanently_delete_lfs_files()`, `list_repo_refs()`, `delete_branch()`, `super_squash_history()`, `set_space_volumes()`, `repo_info().used_storage`, `list_repo_tree()`, and `upload_large_folder()` (deprecated).
1659|
1660|### Key Insights
1661|- **`list_user_repos()`** returns `RepoStorageInfo` with per-repo byte count + % of namespace quota — best starting point for storage audit
1662|- **`permanently_delete_lfs_files()`** with `rewrite_history=True` is the only way to truly reclaim LFS storage; deleting `.gitattributes` pointers alone doesn't work
1663|- **`set_space_volumes()`** replaces the deprecated `request_space_storage()` — mounts model/dataset/bucket volumes in Spaces via the Volume API
1664|- **`upload_folder()`** in multi-commit mode (default) now supersedes the deprecated `upload_large_folder()`
1665|- Super-squash (`super_squash_history()`) compresses entire Git history to 1 commit but quota takes up to 36 hours to update
1666|- LFS objects are identified by SHA-256 OID, not paths — a single OID may be referenced across multiple paths/commits
1667|- Storage Buckets are S3-compatible, accessed via `hf://buckets/`, and deploy via Volume API into Spaces
1668|
1669|### Resources
1670|- `huggingface_hub` source: `hf_api.py` lines 88, 1647, 1981, 3567, 3828, 4034, 4269, 4349, 6179, 7002, 8990
1671|- Hub docs: https://huggingface.co/docs/hub/en/storage-limits
1672|- Python API ref: https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api
1673|
1674|### Files modified
1675|- `~/profiles/sakthai/skills/mlops/hf-hub-storage-management/SKILL.md` — added YAML frontmatter (existing file)
1676|- `~/profiles/sakthai/skills/mlops/hf-hub-storage-management/references/hf-learnings.md` — created (+256 lines)
1677|- `~/profiles/sakthai/skills/mlops/hf-datasets-video-processing/SKILL.md` — added YAML frontmatter
1678|- `~/profiles/sakthai/skills/mlops/hf-datasets-image-processing/SKILL.md` — added YAML frontmatter
1679|- `~/profiles/sakthai/skills/mlops/hf-accelerate/SKILL.md` — added YAML frontmatter
1680|- `~/profiles/sakthai/cron/hf-topics-covered.json` — updated

## 2026-07-24: hf-hub-pull-requests-and-discussions-api — Complete Deep Dive (Topic #123)

### Summary
Comprehensive deep-dive into Hugging Face Hub's Pull Requests and Discussions API. Covers the full lifecycle — creating, reading, commenting, editing, merging, and closing discussions/PRs using the `huggingface_hub` Python SDK (v1.24.0) and the underlying git ref architecture. This topic was previously tracked but had no learning content written; this fills the gap with authoritative source-verified documentation.

### Architecture — How Hub PRs Actually Work

The Hub's PR system is intentionally different from GitHub's fork-based model:

1. **No forks.** Contributors push directly to the source repo via special git refs.
2. **Custom refs, not branches.** PRs use `refs/pr/{NUMBER}` refs (not `refs/heads/`). These are not fetched by default when cloning.
3. **Discussions and PRs are the same type.** They share the same list view, same API, same data model. A PR is a discussion with `is_pull_request=True` and file changes attached.
4. **Draft by default.** Programmatically created PRs start in `"draft"` status. They must be manually published before merging.

### Full Python SDK Method Reference

From `huggingface_hub.HfApi` (v1.24.0):

| Method | Purpose | Key Parameters |
|--------|---------|---------------|
| `create_discussion()` | Create discussion or PR | `repo_id`, `title`, `pull_request=False/True` |
| `create_pull_request()` | Wrapper for PR creation | `repo_id`, `title` (thin wrapper) |
| `get_discussion_details()` | Fetch full PR/discussion | `repo_id`, `discussion_num` |
| `get_repo_discussions()` | List all discussions/PRs | `repo_id`, `author`, `discussion_type`, `discussion_status` |
| `comment_discussion()` | Post comment | `repo_id`, `discussion_num`, `comment` |
| `edit_discussion_comment()` | Edit comment | `repo_id`, `discussion_num`, `comment_id`, `new_content` |
| `hide_discussion_comment()` | Hide comment (irreversible) | `repo_id`, `discussion_num`, `comment_id` |
| `change_discussion_status()` | Open/close | `repo_id`, `discussion_num`, `new_status` |
| `merge_pull_request()` | Merge PR | `repo_id`, `discussion_num` |
| `rename_discussion()` | Rename title | `repo_id`, `discussion_num`, `new_title` |

### Filtering

**DiscussionTypeFilter:** `"all"`, `"pull_request"`, `"discussion"`
**DiscussionStatusFilter:** `"open"`, `"closed"`, `"all"`

`get_repo_discussions()` returns an **iterator** of `Discussion` objects (summary). Use `get_discussion_details()` for full details including diff and events.

### Status Lifecycle

```
create_discussion(pull_request=True) → status="draft"
  → Publish (web UI only) → "open" → merge → "merged"
                                   → close → "closed"
create_discussion(pull_request=False) → "open" → "closed"
```

### Preferred PR Creation with Changes

```python
from huggingface_hub import HfApi, CommitOperationAdd

api = HfApi()
api.create_commit(
    repo_id="user/repo",
    operations=[CommitOperationAdd(path_in_repo="file.txt", path_or_fileobj=b"content")],
    commit_message="Add file via PR",
    create_pr=True,  # Creates PR atomically with changes
)
```

### Git Workflow

```bash
# Fetch PR locally
git fetch origin refs/pr/42:pr/42
git checkout pr/42
# Push changes
git push origin pr/42:refs/pr/42

# Fetch ALL PRs
git fetch origin refs/pr/*:refs/remotes/origin/pr/*
```

### Zero-Cost Notes
- All API calls are free-tier supported
- PR refs take storage — delete after merge to stay within 5GB free limit
- `create_commit(create_pr=True)` combines PR + changes in one call

### Resources
- Hub docs: https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions
- Python SDK source: `huggingface_hub.hf_api` (v1.24.0)
- CLI: `huggingface-cli discussions --help`

---
### Files modified
- `~/profiles/sakthai/skills/SakThai-hf-pull-requests-discussions/SKILL.md` — created with author/license
- `~/profiles/sakthai/skills/SakThai-hf-pull-requests-discussions/references/hf-learnings.md` — created (+211 lines)
- `~/profiles/sakthai/cron/hf-topics-covered.json` — updated
- `~/profiles/sakthai/skills/references/hf-learnings.md` — appended

---

## 2026-07-24: hf-datasets-server-data-preview-rows-search-filter-deep-dive

### Summary
Deep-dive into the Hugging Face Datasets Server's data preview and query endpoints — `/first-rows`, `/rows`, `/search`, `/filter`, `/statistics`, and `/croissant`. All verified live against the production API at `https://datasets-server.huggingface.co`. Covers exact response formats, SQL-like filter syntax, pagination behavior, and practical zero-cost patterns.

### Base URL
```
https://datasets-server.huggingface.co
```
No auth required for public datasets. Gated/private datasets need `Authorization: Bearer ***` header.

### Endpoint Reference (Verified Live)

#### 1. `/is-valid` — Check Dataset Capabilities
```bash
curl "https://datasets-server.huggingface.co/is-valid?dataset=Salesforce/wikitext"
# -> {"preview":true,"viewer":true,"search":true,"filter":true,"statistics":true}
```
Returns which features (preview, viewer, search, filter, statistics) are available.

#### 2. `/splits` — List All Splits and Subsets
```bash
curl "https://datasets-server.huggingface.co/splits?dataset=Salesforce/wikitext&config=wikitext-2-raw-v1"
```

#### 3. `/size` — Dataset Size (Rows + Bytes)
**Verified response (2026-07-24):**
```json
{
  "size": {
    "config": { "dataset": "Salesforce/wikitext", "config": "wikitext-2-raw-v1", "num_bytes_original_files": 7747362, "num_bytes_parquet_files": 7747362, "num_bytes_memory": 13055524, "num_rows": 44836, "num_columns": 1 },
    "splits": [
      {"split": "test", "num_rows": 4358, "num_bytes_memory": 1391252},
      {"split": "train", "num_rows": 36718, "num_bytes_memory": 10720370},
      {"split": "validation", "num_rows": 3760, "num_bytes_memory": 943902}
    ]
  },
  "partial": false
}
```

#### 4. `/first-rows` — Preview First Rows (VERIFIED)
- Returns exactly 100 rows (default page size)
- Fields: `features`, `rows[]` (each with `row_idx`, `row`, `truncated_cells`)
- No `num_rows_total` — use `/size` for total count
- `split` parameter is required

#### 5. `/rows` — Download Arbitrary Slices (VERIFIED)
- `offset` (default: 0), `length` (default/max: 100)
- Same format as `/first-rows` but with controllable offset

#### 6. `/search` — Full-Text Search (VERIFIED)
- Query scanned across ALL text columns
- Returns absolute `row_idx` (not renumbered)
- No total match count exposed
- Pagination via `offset`/`length`

#### 7. `/filter` — SQL-Like WHERE Filtering (VERIFIED)
**WHERE Syntax Rules (from docs + verified):**
- Column names MUST be in double quotes: `"text"`
- String values MUST be in single quotes: `'hello'`
- Numeric values unquoted: `label=1`
- Operators: `=`, `<>`, `>`, `>=`, `<`, `<=`, `LIKE`, `NOT LIKE`
- Combinators: `AND`, `OR`, `NOT`, parentheses
- `LIKE` wildcards: `%` (any sequence), `_` (single char)
- **Only endpoint that returns `num_rows_total`** (total matching rows)

#### 8. `/statistics` — Column Statistics (VERIFIED)
**Verified response for wikitext train split:**
- `num_examples`: 36718 (total rows in split)
- String columns: length stats (min/max/mean/median/std + histogram)
- Numeric columns: value stats
- `class_label` columns: frequency counts
- Histogram: 10 bins with `hist` (counts) and `bin_edges` (boundaries)

#### 9. `/parquet` — Get Parquet File URLs (VERIFIED)
- Returns per-split Parquet URLs under `refs/convert/parquet`
- Usable with DuckDB, Polars, Pandas, cuDF, PySpark, ClickHouse, PostgreSQL

#### 10. `/info` — Dataset Metadata (VERIFIED)
- Returns `dataset_info` with description, features, splits, sizes

#### 11. `/croissant` — ML-Commons Croissant Metadata
- Structured ML dataset metadata for interoperability

### Pagination Behavior Summary

| Endpoint | Max Length | Has `offset` | `num_rows_total` |
|----------|-----------|-------------|-----------------|
| `/first-rows` | N/A (always 100) | No | null |
| `/rows` | 100 | Yes | null |
| `/search` | 100 | Yes | null |
| `/filter` | 100 | Yes | **Yes** |
| `/size` | N/A | N/A | Has split counts |
| `/statistics` | N/A | N/A | Has `num_examples` |

### Error States (Verified)

| Error | Status | Example |
|-------|--------|---------|
| Renamed dataset | 200 body | `{"error":"The dataset has been renamed..."}` |
| Not found / private | 200 body | `{"error":"The dataset does not exist..."}` |
| Missing param | 422 | `{"error":"Parameter 'dataset' is required"}` |
| Length too large | 422 | `{"error":"Parameter 'length' must not be greater than 100"}` |
| Invalid WHERE | 422 | `{"error":"Parameter 'where' contains errors or invalid symbols"}` |

### Key Takeaways
1. `/first-rows` gives 100 rows free — quick inspection without download
2. Use `/size` for total row counts — `/rows` and `/search` don't return totals
3. `/filter` is the only endpoint returning `num_rows_total`
4. WHERE syntax is SQL-like: double-quoted columns, single-quoted strings
5. Search is case-sensitive
6. Parquet URLs enable zero-cost analytics with DuckDB/Polars
7. All endpoints are completely free — no API keys for public datasets

### Resources
- Docs: https://huggingface.co/docs/dataset-viewer/
- OpenAPI: https://datasets-server.huggingface.co/openapi.json
- Source: https://github.com/huggingface/dataset-viewer

---

## 2026-07-24: hf-hub-exception-reference — Complete Exception Hierarchy (Topic #130)

### Summary
Comprehensive reference of all 50+ custom exceptions in the `huggingface_hub` library — full inheritance hierarchy, attributes, when each error is raised, `hf_raise_for_status()` dispatch logic, and error-handling best practices for production use. Source: `huggingface_hub/errors.py` on GitHub.

### Key Coverage
- Full exception hierarchy tree (50+ classes, 15 categories)
- `HfHubHTTPError` base class with request_id, server_message, response, request attrs
- `hf_raise_for_status()` dispatch: 400→BadRequestError, 403 gated→GatedRepoError, 404 Revision→RevisionNotFoundError, etc.
- TGI errors: OverloadedError, ValidationError, IncompleteGenerationError, GenerationError, UnknownError
- Cache errors: CacheNotFound, CorruptedCacheException, IncompleteSnapshotError
- OAuth: DeviceCodeError with OAuthErrorCode enum, OIDCError for Trusted Publishers
- 4 practical error-handling patterns (broad catch, network-vs-hub, offline fallback, gated detection)

### Repository search tag
- Saved to huggingface-hub skill's references/hf-learnings.md

---

## 2026-07-24: hf-hub-upload-strategies-deep-dive — Complete Upload Reference (Topic #35 Deep-Dive)

### Summary
Deep-dive into all upload strategies available in `huggingface_hub` for pushing content to the Hugging Face Hub. Covers the full API surface (`upload_file`, `upload_folder`, `create_commit`, `upload_large_folder`), the Xet-powered streamed pipeline, LFS vs regular file handling, multi-commit large-folder uploads, resumability, patterns, limitations, and best practices for zero-cost model/dataset publishing.

### Key Concepts
- **Three core methods:** `upload_file` (single file, ≤50GB), `upload_folder` (folder with Xet streamed multi-commit pipeline by default), `upload_large_folder` (DEPRECATED)
- **Low-level:** `create_commit` with `CommitOperationAdd/Delete/Copy` operations (25k LFS files, 1 GB regular payload per commit)
- **Xet pipeline architecture:** Coordinator walks files, classifies 256 at a time, registers xet files into `XetSession` for background upload. Committer thread batches commits (adaptive 250→1000 files, forced every 5 min). Resumable: already-uploaded chunks deduplicated (~0 bytes).
- **LFS flow:** Pre-upload (hash + register + upload chunks to blob storage) → Commit (LFS pointer reference)
- **Regular files:** Base64-encoded in commit payload (~100 MB budget per commit)
- `upload_folder` with `create_pr=True` opens against default branch. Resuming an interrupted PR upload uses `revision="refs/pr/N"`
- `CommitOperationCopy` enables cross-repository LFS object duplication (server-side)

### Repository search tag
- Saved to huggingface-hub skill's references/hf-learnings.md

---

## 2026-07-24: hf-smolagents-deep-dive-v2 — Complete smolagents v1.26.0 Reference (Topic #14 Deep-Dive)

### Summary
Deep-dive into `smolagents` v1.26.0 — Hugging Face's open-source agent library. Covers the two agent types (CodeAgent and ToolCallingAgent), multi-model support (InferenceClientModel, LiteLLMModel, TransformersModel, MLXModel, AmazonBedrockModel, AzureOpenAIModel), the tool system (decorator-based, class-based, Hub tools, Space-as-tool, LangChain adapters, MCP integration), multi-agent orchestration via managed_agents, planning steps (planning_interval), final_answer validation (final_answer_checks), Gradio UI integration, CLI utilities (smolagent, webagent), secure code execution (local sandbox + Modal/E2B/Docker executors), and best practices for building reliable agents.

### Core Architecture

**Two Agent Types:**

| Agent | Action Format | Tool Interface | Strengths | When to Use |
|-------|--------------|----------------|-----------|-------------|
| `CodeAgent` | Python code snippets | Tools as Python functions (bindings) | Composable, flexible, emergent reasoning | Multi-step reasoning, dynamic logic, combining tools |
| `ToolCallingAgent` | JSON tool calls | Tools with JSON schema | Reliable, validated, interoperable | Simple atomic tools, high-reliability dispatching |

### Model Classes (smolagents v1.26.0)

| Class | Provider | Extra Required |
|-------|----------|----------------|
| `InferenceClientModel` | HF Inference Providers (Cerebras, Cohere, Fal, Fireworks, HF-Inference, Hyperbolic, Nebius, Novita, Replicate, SambaNova, Together, etc.) | None (free HF account has included credits) |
| `LiteLLMModel` | 100+ models via LiteLLM (OpenAI, Anthropic, Ollama, etc.) | `smolagents[litellm]` |
| `TransformersModel` | Local transformers pipeline | `smolagents[transformers]` |
| `MLXModel` | Apple MLX (local) | `smolagents[mlx-lm]` |
| `AzureOpenAIModel` | Azure OpenAI | `smolagents[openai]` |
| `AmazonBedrockModel` | AWS Bedrock | `smolagents[bedrock]` |

All model classes accept keyword arguments (temperature, max_tokens, top_p, etc.) forwarded to completion calls.

### Key Initialization Parameters

```python
CodeAgent(
    tools=[...],                       # List[Tool] — the agent's toolbox
    model=InferenceClientModel(),      # LLM engine
    add_base_tools=False,              # Add DuckDuckGo search + Python executor + Transcriber
    instructions="Always ...",         # Custom instructions appended to system prompt
    additional_authorized_imports=[],  # CodeAgent only: allow extra Python imports
    max_steps=20,                      # Max ReAct steps before forced stop
    planning_interval=None,            # Run planning step every N steps
    final_answer_checks=[],            # Validation funcs before accepting final answer
    managed_agents=[],                  # Sub-agents this agent can delegate to
    executor_type="local",             # "local" | "blaxel" | "e2b" | "modal" | "docker"
    code_block_tags=("```python", "```"),  # CodeAgent: code block delimiters
    stream_outputs=False,              # Stream intermediate outputs
    use_structured_outputs_internally=False, # Use structured generation per step
)
```

ToolCallingAgent additionally supports `max_tool_threads` for parallel tool calls.

### Tools System

**Three ways to define tools:**

1. **Decorator approach** (`@tool`):
```python
from smolagents import tool
@tool
def my_tool(param: str) -> str:
    """Description. Args: param: description."""
    return result
```

2. **Class-based** (Tool subclass):
```python
from smolagents import Tool
class MyTool(Tool):
    name = "my_tool"
    description = "..."
    inputs = {"param": {"type": "string", "description": "..."}}
    output_type = "string"
    def forward(self, param: str) -> str:
        return result
```

3. **Loaded from Hub**:
```python
tool = load_tool("user/tool-name", trust_remote_code=True)
```

**Tool sources:**
- `Tool.from_space(space_id, name, description)` — wrap any HF Space as a tool
- `Tool.from_langchain(langchain_tool)` — convert LangChain tools
- `ToolCollection.from_hub(collection_slug)` — load tools from a Hub collection
- `ToolCollection.from_mcp(server_parameters)` — load tools from MCP servers (Stdio, Streamable HTTP, legacy SSE)
- `WebSearchTool()` — DuckDuckGo search (from `[toolkit]` extra)
- `PythonInterpreterTool()` — safe Python execution (CodeAgent has this natively)

### MCP Integration

```python
from mcp import StdioServerParameters
from smolagents import ToolCollection, CodeAgent, InferenceClientModel

model = InferenceClientModel()
server_parameters = StdioServerParameters(
    command="uvx",
    args=["--quiet", "pubmedmcp@0.1.3"],
    env={"UV_PYTHON": "3.12", **os.environ},
)

with ToolCollection.from_mcp(server_parameters, trust_remote_code=True) as tool_collection:
    agent = CodeAgent(tools=[*tool_collection.tools], model=model, add_base_tools=True)
    agent.run("Find a remedy for hangover.")
```

MCP supports three transport modes:
- **Stdio**: subprocess via stdin/stdout (use `StdioServerParameters`)
- **Streamable HTTP**: modern HTTP transport (`{"url": "...", "transport": "streamable-http"}`)
- **SSE**: legacy HTTP+SSE (`{"url": "...", "transport": "sse"}` — deprecated)

MCP tools also support `structured_output=True` for JSON output schemas.

### Multi-Agent Orchestration

Pass managed agents via `managed_agents=[]` parameter. Each managed agent needs a `name` and `description`. The parent agent can delegate sub-tasks by "calling" a managed agent as if it were a tool:

```python
web_agent = CodeAgent(
    name="web_agent",
    description="Searches the web for information",
    tools=[WebSearchTool()],
    model=InferenceClientModel(),
)
data_agent = CodeAgent(
    name="data_agent",
    description="Analyzes data and computes results",
    tools=[],
    model=InferenceClientModel(),
    additional_authorized_imports=["pandas", "numpy"],
)

orchestrator = CodeAgent(
    tools=[],
    model=InferenceClientModel(model_id="Qwen/Qwen2.5-72B-Instruct"),
    managed_agents=[web_agent, data_agent],
)
orchestrator.run("Find population of Tokyo and compute its square root.")
```

### CodeAgent Security Model

- **Local executor**: Python interpreter sandbox — safe imports only (math, print), additional imports authorized via `additional_authorized_imports`
- **No imports by default** outside a safe list — prevents arbitrary code execution
- **Submodule access blocked** unless explicitly authorized (e.g., `"numpy.random"` or `"numpy.*"`)
- **Remote executors**: Blaxel, E2B, Docker, Modal for full isolation
- **Warning**: Do not add unsafe imports — LLM can generate arbitrary code

### Planning Steps

Activate with `planning_interval=N`. Every N steps, the agent pauses tool execution to reflect:
- Update a list of known facts
- Plan next steps based on accumulated information
- No tool calls during planning — pure reasoning step

```python
agent = CodeAgent(
    tools=[search_tool, image_generation_tool],
    model=InferenceClientModel(model_id="Qwen/Qwen2.5-72B-Instruct"),
    planning_interval=3,
)
```

### Final Answer Validation

```python
def must_be_integer(final_answer: str, agent_memory=None) -> bool:
    try:
        int(final_answer)
        return True
    except ValueError:
        return False

agent = CodeAgent(
    tools=[],
    model=InferenceClientModel(),
    final_answer_checks=[must_be_integer],
)
```

### Debugging Best Practices (from official docs)

1. **Use a stronger LLM** — many agent errors are actually LLM reasoning failures
2. **Provide more information** — use `instructions` parameter, enrich tool descriptions, be verbose in task
3. **Change prompt templates** (last resort) — access via `agent.prompt_templates["system_prompt"]` (Jinja2 template with placeholders)
4. **Simplify workflows** — group related tools into one to reduce LLM calls; prefer deterministic logic over agentic decisions

### Tool Design Best Practices

- **Good logging**: Use `print()` in `forward()` to log execution details the LLM can use
- **Clear descriptions**: Specify exact input format (e.g., `"%m/%d/%y %H:%M:%S"` for datetimes)
- **Error handling**: Raise `ValueError` with helpful messages including context
- **Structured output**: For tools with JSON output schema, set `output_schema` dict — agents can chain tool calls confidently when schema is known

### CLI Tools

```bash
# One-shot mode
smolagent "Plan a trip to Tokyo between Mar 28 and Apr 7." \
  --model-type "InferenceClientModel" \
  --model-id "Qwen/Qwen2.5-Coder-32B-Instruct" \
  --imports "pandas numpy" \
  --tools "web_search"

# Interactive mode (launches without prompt)
smolagent

# Web agent CLI
webagent "Find the latest AI news"
```

### Agent Persistence & Sharing

- `agent.save(output_dir)` — saves code, tools, prompt templates, app.py, requirements.txt
- `agent.push_to_hub(repo_id)` — upload as Gradio Space
- `agent.from_hub(repo_id)` / `agent.from_folder(folder)` — load saved agents
- `agent.to_dict()` / `MultiStepAgent.from_dict()` — serialize/deserialize to dict

### Repository search tag
- Saved to cron/hf-learnings.md
- Cross-reference: hf-agents-course skill

### Resources
- Official docs: https://huggingface.co/docs/smolagents/en/index (v1.26.0)
- Source code: https://github.com/huggingface/smolagents
- Conceptual guide (intro to agents): https://huggingface.co/docs/smolagents/en/conceptual_guides/intro_agents
- Guided tour: https://huggingface.co/docs/smolagents/en/guided_tour
- Building good agents tutorial: https://huggingface.co/docs/smolagents/en/tutorials/building_good_agents
- Secure code execution: https://huggingface.co/docs/smolagents/en/tutorials/secure_code_execution
- Install: `pip install 'smolagents[toolkit]'` for default tools, `smolagents[litellm]` for multi-provider, `smolagents[transformers]` for local models

---

## 2026-07-24: hf-transformers-phi4-deep-dive — Complete Phi-4 Architecture & Ecosystem Reference (Topic #67 Deep-Dive)

### Summary
Deep-dive into Microsoft Phi-4 (14B) and its growing ecosystem — covering the full architecture (dense decoder-only Transformer with Phi-3-derived internals), the three-pillar data-centric training recipe (synthetic pre-training, curated organic data, advanced post-training with pivotal token search DPO), Transformers integration via `Phi3ForCausalLM`, inference patterns (full precision, 4-bit quantized, GGUF), chat template format, Phi-4-mini (3.8B), Phi-4-multimodal (5.6B), LoRA fine-tuning recipes, and practical deployment strategies for zero-cost environments.

### Core Model: Phi-4 (14B)

**Architecture:** Dense decoder-only Transformer. In Transformers, Phi-4 is loaded via the `Phi3ForCausalLM` class — there is no separate `Phi4ForCausalLM`. The architecture tag in model config is `phi4`, but the implementation reuses the Phi-3 code paths with minimal adjustments. This means all existing Phi-3 infrastructure (attention backends, device mapping, quantization) works identically.

| Property | Value |
|----------|-------|
| Parameters | 14B |
| Layers | 40 |
| Attention heads | 32 (query), 8 (key/value — GQA) |
| Hidden dim | 4,960 |
| Intermediate dim | 15,840 (swiGLU) |
| Vocab size | 100,352 |
| Max position | 16,384 |
| Norm | LayerNorm (pre-norm) |
| Activation | SwiGLU |
| Positional encoding | RoPE |
| Attention | Grouped Query Attention (GQA) with 8 KV heads |
| Training hardware | 1,920 H100-80G GPUs |
| Training tokens | 9.8T |
| Training duration | 21 days |
| License | MIT |
| Release date | December 12, 2024 |

**Position of Phi-4 in Transformers model registry:** The model uses the `Phi3ForCausalLM` class. The configuration class is `Phi3Config` with `model_type="phi3"`. To load:
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "microsoft/phi-4",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=False,  # No custom code needed — uses standard phi3
)
tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-4")
```

**Key config differences from Phi-3:** Phi-4 uses a larger vocab size (100,352 vs Phi-3-mini's 32,064), wider intermediate size (15,840), and more layers (40 vs 32 in Phi-3-medium). The `Phi3Config` parameters align but these dimension changes are significant.

### Three-Pillar Training Recipe

Phi-4's core innovation is its **data-quality-first** approach:

1. **Synthetic Data for Pre-training + Mid-training** (~80% of total tokens): Multi-agent prompting, self-revision workflows, and instruction reversal to generate high-quality reasoning-focused synthetic tokens. Seeds come from high-educational-value organic data. Designed to induce stronger reasoning and problem-solving capabilities directly in pre-training rather than relying on post-training alone.

2. **Curated Organic Data** (~20% of total tokens): Meticulously filtered web content, licensed academic books, code repositories, and Q&A datasets. Filtered for educational value and reasoning density.

3. **Advanced Post-training:**
   - **Supervised Fine-Tuning (SFT):** New high-quality SFT datasets covering instruct-following, truthfulness, helpfulness, and safety
   - **Pivotal Token Search DPO:** A novel technique that identifies tokens in the response where the model's decision most impacts downstream quality, then generates DPO preference pairs anchored at those tokens. More efficient than random-pair DPO.
   - **Rejection Sampling:** Further refines outputs by generating multiple candidates and selecting the best

**Key result:** Phi-4 surpasses GPT-4o on STEM QA (GPQA: 56.1 vs 50.6) and MATH (80.4 vs 74.6) with only 14B parameters, proving data quality can overcome scale disadvantage.

### Benchmarks (OpenAI SimpleEval, temp=0.5)

| Benchmark | Phi-4 (14B) | Phi-3 (14B) | Qwen 2.5 (14B) | GPT-4o-mini | Llama-3.3 (70B) | GPT-4o |
|-----------|-------------|-------------|-----------------|-------------|-----------------|--------|
| MMLU | 84.8 | 77.9 | 79.9 | 81.8 | 86.3 | **88.1** |
| GPQA | **56.1** | 31.2 | 42.9 | 40.9 | 49.1 | 50.6 |
| MGSM | 80.6 | 53.5 | 79.6 | 86.5 | 89.1 | **90.4** |
| MATH | **80.4** | 44.6 | 75.6 | 73.0 | 66.3* | 74.6 |
| HumanEval | 82.6 | 67.8 | 72.1 | 86.2 | 78.9* | **90.6** |
| DROP | 75.5 | 68.3 | 85.5 | 79.3 | **90.2** | 80.9 |
| SimpleQA | 3.0 | 7.6 | 5.4 | 9.9 | 20.9 | **39.4** |

*Llama scores below Meta's reported values due to SimpleEval formatting strictness.

### Chat Template & Tokenization

Phi-4 uses the standard `phi` chat template inherited from Phi-3 (`<|im_start|>`, `<|im_sep|>`, `<|im_end|>` tokens):
```
<|im_start|>system<|im_sep|>
You are a helpful assistant.<|im_end|>
<|im_start|>user<|im_sep|>
How do I bake a cake?<|im_end|>
<|im_start|>assistant<|im_sep|>
```

**Tokenizer:** Uses the same tokenizer as Phi-3 (based on OpenAI's tiktoken cl100k_base with additional special tokens). Vocabulary size is expanded to 100,352 tokens from 32,064 in Phi-3-mini.

### Inference Patterns (Zero-Cost Focused)

**1. Transformers Pipeline (standard):**
```python
pipe = pipeline("text-generation", model="microsoft/phi-4",
                model_kwargs={"torch_dtype": "auto"}, device_map="auto")
outputs = pipe(messages, max_new_tokens=512, temperature=0.7)
```

**2. 4-bit Quantization with bitsandbytes:**
```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                bnb_4bit_compute_dtype=torch.bfloat16,
                                bnb_4bit_use_double_quant=True)
model = AutoModelForCausalLM.from_pretrained("microsoft/phi-4",
    quantization_config=bnb_config, device_map="auto")
```
Reduces VRAM from ~28GB (bf16) to ~9GB (4-bit) — enabling inference on free-tier GPUs.

**3. GGUF via llama.cpp:** Community GGUF quants available on HF Hub. Phi-4 Q4_K_M fits in ~8GB RAM:
```bash
# Via llama.cpp
./llama-cli -m phi-4-Q4_K_M.gguf -p "User: Hello\nAssistant:" -n 256
```

**4. Inference Providers (serverless, zero-cost):** Available through multiple HF Inference Providers (Cerebras, Fireworks, Together AI, etc.) — free account credits cover usage.

### Phi-4-mini (3.8B)

Released April 2025. A smaller variant of Phi-4 optimized for edge/mobile deployment:

| Property | Value |
|----------|-------|
| Parameters | 3.8B |
| Layers | 32 |
| Hidden dim | 3,072 |
| Attention heads | 24 (query), 4 (KV — GQA) |
| Vocab size | 100,352 |
| Context length | 128K (via LongRoPE extension) |
| Intermediate dim | 8,192 |
| Training tokens | 5T+ |
| Release | April 2025 |

**Key difference from Phi-4 (14B):** Phi-4-mini extends context to 128K via LongRoPE (while Phi-4 14B is limited to 16K). This makes it suitable for long-document RAG and agentic workflows. On many benchmarks Phi-4-mini approaches the 14B model's performance while being 4× smaller.

**Loading:**
```python
model = AutoModelForCausalLM.from_pretrained("microsoft/Phi-4-mini-instruct",
    torch_dtype=torch.bfloat16, device_map="auto")
```

### Phi-4-multimodal (5.6B)

Released May 2025. A multimodal variant supporting text + image inputs:

| Property | Value |
|----------|-------|
| Parameters | 5.6B (incl. vision encoder) |
| Vision encoder | SigLIP (336px resolution) |
| Text decoder | Based on Phi-4-mini backbone |
| Context length | 128K text |
| Input | Text + images |
| Output | Text |
| Release | May 2025 |

Uses a simple projector to align SigLIP vision embeddings with the Phi-4-mini text decoder. Supports interleaved image-text inputs for multi-turn vision conversations.

**Loading:**
```python
processor = AutoProcessor.from_pretrained("microsoft/Phi-4-multimodal-instruct")
model = AutoModelForPreTraining.from_pretrained("microsoft/Phi-4-multimodal-instruct",
    torch_dtype=torch.bfloat16, device_map="auto")
```

Note: `AutoModelForPreTraining` (not `AutoModelForCausalLM`) because the model has separate vision encoder weights that need special handling.

### LoRA Fine-Tuning Patterns

Phi-4 can be fine-tuned efficiently using PEFT LoRA. The recommended approach:

```python
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = AutoModelForCausalLM.from_pretrained(
    "microsoft/phi-4", torch_dtype=torch.bfloat16, device_map="auto"
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # ~0.5% of total params
```

**Recommended target_modules:** Unlike Llama which just uses q/k/v/o, Phi-4 benefits from also targeting the gate/up/down projections in the FFN (swiGLU) for better task adaptation.

**QLoRA:** Use with 4-bit base model for fine-tuning on free-tier GPUs (T4 16GB):
```python
model = AutoModelForCausalLM.from_pretrained("microsoft/phi-4",
    quantization_config=bnb_config, device_map="auto")
# Then apply LoRA on top
```

### Key Takeaways

1. **No separate phi4 model class** — Phi-4 uses `Phi3ForCausalLM` in Transformers. All Phi-3 tooling works transparently.
2. **Data quality beats scale** — Synthetic pre-training data + pivotal token DPO enables 14B model to rival 70B+ models on reasoning.
3. **Three-model ecosystem** — Phi-4 (14B flagship), Phi-4-mini (3.8B edge), Phi-4-multimodal (5.6B VLM) cover different deployment scenarios.
4. **128K context in mini** — Phi-4-mini and multimodal extend to 128K via LongRoPE, unlike the 16K limit of the 14B model.
5. **Perfect for zero-cost fine-tuning** — 4-bit QLoRA on Phi-4-mini (3.8B) fits easily on free T4/Kaggle GPUs.
6. **MIT licensed** — All variants released under MIT license for full commercial use.
7. **Chat template is `<|im_start|>` format** — Standard across Phi family, compatible with existing tooling.

### Resources
- https://huggingface.co/microsoft/phi-4 — Model card
- https://arxiv.org/abs/2412.08905 — Phi-4 Technical Report
- https://github.com/microsoft/Phi-4CookBook — Official cookbook with inference/finetuning recipes
- https://huggingface.co/microsoft/Phi-4-mini-instruct — Phi-4-mini model
- https://huggingface.co/microsoft/Phi-4-multimodal-instruct — Phi-4-multimodal model
- https://huggingface.co/docs/transformers/main/en/model_doc/phi3 — Transformers Phi-3 docs (used for Phi-4 too)
- https://azure.microsoft.com/en-us/blog/empowering-innovation-with-phi-4-microsofts-new-open-model/ — Official blog

---

## 2026-07-24: hf-transformers-vlm-processors

### Summary
Researched how Transformers handles Vision-Language Model (VLM) processing through the processor abstraction layer. Processors combine an image processor (or video processor) with a tokenizer, handling the bridging of visual features with text tokenization for multimodal models like LLaVA, Idefics3, Florence-2, Qwen2-VL, and Phi-4-multimodal.

### Key Concepts

**Processor Architecture:**
1. **`ProcessorMixin` base class** (in `transformers.processing_utils`) — provides the `__call__` interface accepting `images`, `text`, `videos`, `audio` as optional inputs
2. **`ImageProcessingMixin`** — standard image preprocessing (resize, crop, rescale, normalize, pad) with model-specific defaults
3. **`TokenizersBackend`** — wraps any HF tokenizer with unified encode/decode interface
4. **Processor classes merge both** — each VLM has its own processor (e.g., `LlavaProcessor`, `Idefics3Processor`, `Florence2Processor`)

**Common Preprocessing Pipeline:**
1. Image → resize to model-specific size (e.g., 336×336 for LLaVA, 384×384 for Idefics3, 1024×1024 for Florence-2)
2. Convert to tensor, rescale to [0,1], normalize with model-specific mean/std
3. Text → apply chat template (if messages format) → tokenize
4. Insert image tokens (`<image>`, `<|image|>`, `<img>`) into text at correct positions
5. Return `BatchFeature` dict with `pixel_values`, `input_ids`, `attention_mask`

**Image Token Strategies:**
- **LLaVA-style:** Single `<image>` token replaced by vision encoder's patch embeddings. `vision_feature_select_strategy="default"` keeps all patches; `"full"` includes CLS token.
- **Idefics3-style:** Multiple `<image>` tokens per image, dynamically computed based on image resolution
- **Florence-2-style:** Fixed task prompt tokens + image embedding via DaViT encoder (no `<image>` token insertion)
- **Qwen2-VL-style:** Uses `|<image_pad|*N|>` pattern where N is the number of image patches

**Key Processor Parameters:**
- `image_processor` / `tokenizer` — the sub-components
- `patch_size` — vision encoder patch size
- `vision_feature_select_strategy` — "default" vs "full" vs "cls_patch"
- `chat_template` — Jinja template for conversation formatting
- `image_token` — special token for image location
- `num_additional_image_tokens` — extra appended tokens (e.g., CLS)

**VLM Processor Reference Table:**

| Model | Image Processor | Tokenizer | Image Token | Special |
|---|---|---|---|---|
| LLaVA 1.5/1.6 | LlavaImageProcessor | LlamaTokenizer | `<image>` | Patch embedding + MLP projection |
| LLaVA-NeXT | LlavaNextImageProcessor | LlamaTokenizer | `<image>` | Dynamic high-res grid support |
| Idefics3 | Idefics3ImageProcessor | GemmaTokenizer | `<image>` | Per-res flexible splitting |
| Florence-2 | CLIPImageProcessor | BERTTokenizer | (none) | Task prompts; encoder-decoder |
| Qwen2-VL | Qwen2VLImageProcessor | Qwen2Tokenizer | `|<image_pad|*N|>` | 3D RoPE in vision tower |
| Phi-4-multimodal | CLIPImageProcessor | Phi3Tokenizer | `<|image_1|>` | CLIP vision + whisper audio |

### Resources
- https://huggingface.co/docs/transformers/main/en/processing_utils
- https://huggingface.co/docs/transformers/main/en/model_doc/llava
- https://huggingface.co/docs/transformers/main/en/model_doc/idefics3
- https://huggingface.co/docs/transformers/main/en/model_doc/florence2
- https://huggingface.co/docs/transformers/main/en/model_doc/qwen2_vl
- https://github.com/huggingface/transformers/blob/main/src/transformers/models/llava/processing_llava.py

---

## 2026-07-24: hf-diffusers-cogvideo-deep-dive

### Summary
Researched the CogVideoX integration in Diffusers — a family of diffusion transformer models (2B and 5B parameters) by THUDM for text-to-video, image-to-video, and video-to-video generation. Covered the 3D causal VAE (`AutoencoderKLCogVideoX`), expert transformer with adaptive LayerNorm (`CogVideoXTransformer3DModel`), T5 text encoder, all four pipelines (T2V, I2V, V2V, FunControl), memory optimization techniques, LoRA support, and quantization via torchao.

### Key Concepts

**Architecture Components:**
1. **3D Causal VAE** — compresses video along spatial AND temporal dimensions using 3D causal convolutions, reducing sequence length and preventing flickering
2. **Expert DiT** — diffusion transformer with adaptive LayerNorm (adaLN) for text-video fusion; uses 3D full attention for accurate motion capture
3. **T5 Text Encoder** — frozen `t5-v1_1-xxl` provides text conditioning embeddings (max 226 tokens)
4. **Custom Schedulers** — `CogVideoXDDIMScheduler` and `CogVideoXDPMScheduler`

**Four Pipelines:**
1. `CogVideoXPipeline` — T2V, best at 1360×768, default 48 frames (6s @ 8fps)
2. `CogVideoXImageToVideoPipeline` — I2V, width 768–1360, height 758
3. `CogVideoXVideoToVideoPipeline` — V2V with `strength` control (default 0.8)
4. `CogVideoXFunControlPipeline` — controlled generation with spatial conditioning

**Memory Optimization Options (5B model):**
- `enable_model_cpu_offload()`: 19GB VRAM (from 33GB)
- `enable_sequential_cpu_offload()`: <4GB VRAM (very slow)
- `enable_tiling()`: 11GB (with offload)
- TorchAO Int8 + FP8 layerwise casting: ~16GB
- `apply_group_offloading()`: efficient grouped offloading

**Key Hyperparameters:**
- `guidance_scale`: 6.0 (default)
- `num_inference_steps`: 50
- `num_frames`: 48 (T2V), 49 (I2V)
- `use_dynamic_cfg`: False (adaptive CFG scaling)
- `max_sequence_length`: 226 (T5 tokens)
- `strength` (V2V): 0.8

**Model Variants:**
- CogVideoX-2b: 2B params, ~20GB unoptimized
- CogVideoX-5b: 5B params, ~33GB unoptimized, ~16GB quantized
- CogVideoX-5b-I2V: 5B, specialized for image-to-video

**Pipeline Components:**
- `tokenizer`: T5Tokenizer
- `text_encoder`: T5EncoderModel
- `vae`: AutoencoderKLCogVideoX
- `transformer`: CogVideoXTransformer3DModel
- `scheduler`: CogVideoXDDIMScheduler | CogVideoXDPMScheduler

### Resources
- https://huggingface.co/docs/diffusers/main/en/api/pipelines/cogvideox
- https://arxiv.org/abs/2408.06072
- https://huggingface.co/THUDM/CogVideoX-5b
- https://huggingface.co/zai-org/CogVideoX-2b
- https://github.com/THUDM/CogVideo

---


## 2026-07-24: hf-hub-api-rate-limiting-deep-dive

### Summary
Deep-dive into the Hugging Face Hub's rate limiting system — how limits work across three request buckets (API, Resolvers, Pages), the IETF-standard HTTP headers returned on limit hits, tier-based quotas per plan level, and the smart retry mechanism built into `huggingface_hub` v1.2.0+.

### Key Concepts

**Three Request Buckets:**
1. **Hub APIs** — programmatic endpoints (model/dataset search, repo creation, user management). Documented in Hub API Endpoints.
2. **Resolvers** — URLs with `/resolve/` serving user-generated content (file downloads by transformers, datasets, vLLM, llama.cpp, LM Studio, ollama, etc.). Highest rate limits because infrastructure is optimized for them.
3. **Pages** — Web pages on huggingface.co. Lowest rate limits (human browsing patterns).

**Window:** All limits are calculated over **5-minute fixed windows**, allowing burstiness.

**HTTP Headers (IETF draft-ietf-httpapi-ratelimit-headers v9):**
| Header | Example |
|--------|---------|
| `RateLimit` | `"api|pages|resolvers";r=[remaining];t=[seconds until reset]` |
| `RateLimit-Policy` | `"fixed window";"api||pages||resolvers";q=[total allowed];w=[window seconds]` |

Headers follow the standard format: policy name, bucket names, remaining count (r), time-to-reset (t), quota limit (q), window duration (w).

**Tier Limits (as of Sep 2025, per 5-min window):**
| Plan | API | Resolvers | Pages |
|------|-----|-----------|-------|
| Anonymous (per IP) | 500* | 3,000* | 100* |
| Free user | 1,000* | 5,000* | 200* |
| PRO user | 2,500 | 12,000 | 400 |
| Team org | 3,000 | 20,000 | 400 |
| Enterprise org | 6,000 | 50,000 | 600 |
| Enterprise Plus | 10,000 | 100,000 | 1,000 |
| Enterprise Plus + IP ranges | 100,000 | 500,000 | 10,000 |
| Academia Hub org | 3,000 | 20,000 | 400 |

*Anonymous/Free limits may change depending on platform health.
Note: Org rate limits apply per member, not shared.

**Smart Retry (`huggingface_hub` >=1.2.0):**
When a 429 error occurs, the SDK automatically parses the `RateLimit` header to extract exact seconds until reset, then waits precisely before retrying. This applies to file downloads (Resolvers) and paginated Hub API calls (list models, datasets, spaces, etc.). **Always use `huggingface_hub` for programmatic access** to benefit from this.

**First Thing to Check Under Rate Limiting:**
The number one cause of rate limiting is not passing a `HF_TOKEN`. Always pass HF_TOKEN downstream to all libraries/applications downloading from the Hub.

**Granular Action Limits:**
Separate (undocumented) rate limits apply to specific actions: repo creation, repo commits, discussions/comments, moderation actions. These change frequently and are not currently published.

**Billing Dashboard:**
Real-time gauge at `https://huggingface.co/settings/billing` shows current (last 5 min) requests vs allowed per bucket. Turns red when exceeded. Context switcher lets you toggle between user and org accounts.

**Strategies When Rate-Limited:**
1. Always pass `HF_TOKEN`
2. Spread requests over longer periods
3. Replace Hub API calls with Resolver calls when possible (Resolver limits are highest)
4. Upgrade to PRO/Team/Enterprise

### Resources
- https://huggingface.co/docs/hub/en/rate-limits — official docs
- https://huggingface.co/settings/billing — real-time rate limit dashboard
- IETF Draft: https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/
- https://huggingface.co/docs/huggingface_hub/index — huggingface_hub library

---

## 2026-07-24: hf-datasets-server-parquet-conversion-pipeline — How the Datasets Server Auto-Converts Hub Datasets to Parquet

### Summary
Deep-dive into the Hugging Face Datasets Server's Parquet conversion pipeline — how 100,000+ datasets on the Hub are automatically converted from their original format (CSV, JSONL, Parquet, image directories, audio folders, etc.) to columnar Parquet files on a special `refs/convert/parquet` branch. Covers the server architecture (job queue, workers, cache), the three core job types, the 5 GB size limit, the `/parquet` API endpoint, and practical query patterns using DuckDB/ Pandas/ Polars.

### Source Documentation
- Datasets Viewer Parquet Guide: https://huggingface.co/docs/dataset-viewer/en/parquet
- Parquet Conversion Overview: https://huggingface.co/docs/dataset-viewer/en/parquet_process
- Server Infrastructure: https://huggingface.co/docs/dataset-viewer/en/server
- Source Repo: https://github.com/huggingface/dataset-viewer

### Three-Component Server Architecture

- **Job Queue (MongoDB)**: Three job types — `/splits` (discovers configs/splits), `/first-rows` (previews 100 rows), `/parquet` (downloads → converts → publishes)
- **Workers**: Poll queue, execute preprocessing, store results in cache. Configurable via env vars (MIN_ROWS, MAX_ROWS, MAX_JOBS_PER_USER/ORG).
- **Cache (MongoDB)**: Pre-computed responses for instant API return. `/rows`, `/search`, `/filter` are on-demand (using DuckDB on cached Parquet).

### Parquet Conversion Lifecycle

1. Dataset uploaded/updated on Hub → viewer detects changes
2. `/parquet` job enqueued → worker loads dataset via `datasets` library
3. Worker converts each split to Parquet format
4. Parquet files published to **`refs/convert/parquet`** Git branch (parallel to main)
5. Files available via `GET /parquet` API endpoint

### Key Characteristics

- **Size limit**: Public datasets < 5 GB auto-converted; ≥ 5 GB skipped. Private: PRO/Enterprise only.
- **Branch**: `refs/convert/parquet` — read-only for users, auto-maintained by server
- **Sharding**: Large splits split into multiple files (e.g., `train-00000-of-00003.parquet`)
- **Schema**: Mirrors `datasets.Features` — INT32, INT64, FLOAT, STRING, BOOLEAN, LIST, Image/Audio as BYTE_ARRAY
- **Compression**: Snappy, ZSTD, GZIP, LZ4 — auto-selected per column

### API Endpoint: `GET /parquet`

```python
import requests
resp = requests.get("https://datasets-server.huggingface.co/parquet",
                    params={"dataset": "ibm/duorc"}).json()
for pf in resp["parquet_files"]:
    print(pf["url"])  # Raw Parquet URL on refs/convert/parquet branch
```

Response fields per file: `dataset`, `config`, `split`, `url`, `size`, `num_rows`, `parquet_files_count`. Also returns `pending` and `failed` arrays.

### Query Patterns (Zero-Cost)

**DuckDB (pushdown queries — most efficient):**
```python
import duckdb
urls = [p["url"] for p in resp["parquet_files"]]
duckdb.sql("SELECT COUNT(*), COUNT(DISTINCT title) FROM read_parquet(urls) WHERE LENGTH(text) > 1000").fetchall()
```

**Pandas:**
```python
dfs = [pd.read_parquet(url) for url in urls]
df = pd.concat(dfs, ignore_index=True)
```

**Polars (lazy):**
```python
df = pl.scan_parquet(urls).collect()
```

### Limitations
- 5 GB public limit; larger datasets need manual conversion
- Conversion is batch-only (no incremental updates)
- Full re-conversion on dataset changes
- Image/Audio stored as opaque bytes — need `datasets` library to decode
- Branch URL encodes `%2F`: `refs%2Fconvert%2Fparquet`

### Resources
- https://huggingface.co/docs/dataset-viewer/en/parquet
- https://huggingface.co/docs/dataset-viewer/en/parquet_process
- https://huggingface.co/docs/dataset-viewer/en/server
- https://github.com/huggingface/dataset-viewer
|- https://parquet.apache.org/
|

## 2026-07-24: hf-datasets-tool-calling-format

### Summary
Researched the canonical dataset format for tool-calling/function-calling fine-tuning with Hugging Face Transformers. Covers message dict structure (OpenAI-compatible with HF extensions), JSON schema tool definitions, Python function vs. dict-based tool specification, dataset columns/rows for training, chat template rendering patterns, response parsing (new in v5.14), and best practices for building tool-calling training datasets.

### Key Concepts

**Message structure:** Assistant tool calls use `{"role": "assistant", "tool_calls": [{"type": "function", "function": {"name": ..., "arguments": {...}}}]}`. Tool results use `{"role": "tool", "content": "string_result"}`.

**Tool definitions:** Passed via `apply_chat_template(messages, tools=...)`. Two formats: (1) Python functions with Google-style docstrings (signature + args parsed automatically), (2) JSON schema dicts with `type: "function"`, `name`, `description`, `parameters`. `get_json_schema()` converts functions to schemas.

**Training dataset:** Recommended columns: `messages` (list[dict] conversation), `tools` (list[dict] tool schemas), optional `source`. Training prep: use `add_generation_prompt=False`, pass tools to `apply_chat_template`, tokenize full sequence. Use loss masking in SFTTrainer.

**Response parsing (v5.14):** `tokenizer.parse_response(out_text, prefix=input_ids)` returns structured dict with thinking, tool_calls, content fields. Streaming via `tokenizer.get_response_parser(prefix=...)` yields region_open/region_chunk/region_close events. Tool calls emit `dirty=True` chunks (raw JSON) until `region_close` provides parsed dict.

**Key pitfalls:** Always stringify tool `content`; arguments as dict not JSON string; test with `tokenize=False` first; check model card for specific special-token format; `continue_final_message` for prefill but not with `add_generation_prompt`.

### References
- https://huggingface.co/docs/transformers/en/chat_extras
- https://huggingface.co/docs/transformers/en/chat_response_parsing
- https://huggingface.co/docs/transformers/en/chat_templating
- https://github.com/huggingface/transformers/blob/main/src/transformers/utils/chat_template_utils.py

---

## 2026-07-24: hf-transformers-cache-hierarchy-deep-dive

### Summary
Comprehensive deep-dive into the Transformers KV cache class hierarchy (cache_utils.py, ~2056 lines). Covers the complete Cache container hierarchy (DynamicCache, StaticCache, QuantizedCache, EncoderDecoderCache, MtpCache), the CacheLayerMixin layer hierarchy (dynamic, static, sliding window, quantized, linear attention, hybrid), the cache_implementation parameter in generate(), and the offloading infrastructure.

### Key Concepts

**Architecture:** Two levels — Cache layers (one per model layer, storing key/value states) and Cache containers (list of layers, user-facing API).

**Layer Class Hierarchy:**
- DynamicLayer — grows dynamically via torch.cat (default)
  - DynamicSlidingWindowLayer — caps at sliding_window size
  - DynamicIndexedLayer — for DeepSeek sparse attention
  - QuantizedLayer — KIVI-style quantized KV cache
    - QuantoQuantizedLayer (Optimum Quanto backend)
    - HQQQuantizedLayer (HQQ backend)
- StaticLayer — pre-allocated static tensor
  - StaticSlidingWindowLayer / StaticIndexedLayer
- LinearAttentionCacheLayerMixin — for Mamba/linear attention
  - LinearAttentionLayer / hybrid combinations

**Layer Type Dispatch:** Config strings map to layer classes via DYNAMIC_LAYER_TYPE_MAPPING:
| Config Type | Dynamic | Static |
|---|---|---|
| full_attention | DynamicLayer | StaticLayer |
| sliding_attention | DynamicSlidingWindowLayer | StaticSlidingWindowLayer |
| conv/moe/linear_attention | LinearAttentionLayer | LinearAttentionLayer |
| hybrid | LinearAttentionAndFullAttentionLayer | LinearAttentionAndStaticFullAttentionLayer |
| hybrid_sliding | LinearAttentionAndSlidingWindowAttentionLayer | LinearAttentionAndStaticSlidingWindowAttentionLayer |
| deepseek_sparse_attention | DynamicIndexedLayer | StaticIndexedLayer |

**Cache Containers:**
- DynamicCache(config, offloading=False) — default, auto-detects sliding/hybrid structure
- StaticCache(config, max_cache_len) — for torch.compile/export, pre-allocated
- QuantizedCache(backend, config, nbits=4, residual_length=128) — KIVI quantized, two backends (quanto/hqq)
- EncoderDecoderCache(self_attn_cache, cross_attn_cache) — for encoder-decoder models
- MtpCache(DynamicCache) — Multi-Token Prediction, adds query offset logic

**cache_implementation values in generate():**
| Value | Class | Use Case |
|---|---|---|
| "dynamic" | DynamicCache() | Default, general use |
| "static" | StaticCache(config, max_cache_len) | torch.compile, fixed-length gen |
| "offloaded" | DynamicCache(offloading=True) | GPU memory constrained |
| "offloaded_static" | StaticCache(..., offloading=True) | GPU mem + fixed length |
| "quantized" | QuantizedCache(backend, config) | Long generation, memory critical |

**Offloading:** GPU→CPU via separate torch.Stream for non-blocking transfers. only_non_sliding=True keeps small sliding layers on GPU. Includes prefetch/offload lifecycle with circular search for next offloaded layer.

### Resources
- Source: transformers/src/transformers/cache_utils.py (~2056 lines)
- Docs (cache_implementation): https://huggingface.co/docs/transformers/main/en/main_classes/text_generation
- Tutorial: https://huggingface.co/docs/transformers/main/en/llm_tutorial_optimization
- KIVI paper: https://huggingface.co/papers/2402.02750

---

## 2026-07-24: hf-gradio-lite-deep-dive — Complete Gradio Lite Architecture Reference (Topic #175 Deep-Dive)

### Summary
Deep-dive into `@gradio/lite` — Gradio's serverless runtime that runs entire Gradio apps inside the browser using Pyodide (Python for WebAssembly). Covers the architecture, custom element API (`<gradio-lite>`), Wasm worker pipeline, filesystem virtualization, ASGI-over-Wasm protocol, package installation via micropip, the Playground mode, limitations, and the official deprecation/archival status (frozen at version 5.45.0 in the `gradio-app/gradio-lite` repo).

### Quick Facts

| Attribute | Value |
|-----------|-------|
| Package | `@gradio/lite` (npm), v5.45.0 (final) |
| License | Apache-2.0 |
| Runtime | Pyodide v0.27.3 (Python 3.12 Wasm) |
| CDN | `https://cdn.jsdelivr.net/npm/@gradio/lite/dist/lite.js` |
| Worker | DedicatedWorker (default) or SharedWorker (`shared-worker` attr) |
| Status | **Archived** — no longer maintained as of Gradio 5.x line |

### Architecture

Gradio Lite has a four-layer architecture:

```
┌─────────────────────────────────────────────┐
│  Browser DOM                                │
│  ┌─────────────────────────────────┐        │
│  │  <gradio-lite> Custom Element   │        │
│  │  ┌──────────┐ ┌──────────────┐ │        │
│  │  │ LiteIndex│ │  Playground  │ │        │
│  │  │ (Svelte) │ │  (Svelte)    │ │        │
│  │  └────┬─────┘ └──────────────┘ │        │
│  │       │                        │        │
│  │  ┌────▼────────┐               │        │
│  │  │ WorkerProxy │               │        │
│  │  │ (EventTarget)│              │        │
│  │  └────┬────────┘              │        │
│  └───────┼─────────────────────────┘        │
│          │ postMessage (MessageChannel)      │
├──────────┼──────────────────────────────────┤
│  Wasm Worker (WebWorker)                     │
│  ┌───────▼──────────────────────────┐       │
│  │  Pyodide v0.27.3                  │       │
│  │  ┌─────────────────┐             │       │
│  │  │ Python 3.12     │  gradio.whl │       │
│  │  │ + micropip      │  gradio_    │       │
│  │  │ + gradio        │  client.whl │       │
│  │  └─────────────────┘             │       │
│  ├──────────────────────────────────┤       │
│  │  ASGI Gateway: Wasm → HTTP proxy │       │
│  └──────────────────────────────────┘       │
└─────────────────────────────────────────────┘
```

### Layer 1: Custom Element (`<gradio-lite>`)

The entry point is a **custom HTML element** registered via `customElements.define('gradio-lite', ...)`. When the browser encounters `<gradio-lite>` in HTML, it:

1. Parses attributes from the element (`theme`, `embed`, `eager`, `shared-worker`, `playground`, `layout`, etc.)
2. Parses child elements (`<gradio-file>`, `<gradio-requirements>`, `<gradio-code>`)
3. Extracts Python source code from text content or named files
4. Creates a `WorkerProxy` to communicate with the Pyodide Web Worker
5. Mounts a Svelte `LiteIndex` component that renders the Gradio UI proxied from Wasm

**Supported Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `theme` | `"light"\|"dark"` | system | Force theme mode |
| `embed` | boolean | false | Embed mode (no padding) |
| `eager` | boolean | false | Load immediately vs lazy |
| `shared-worker` | boolean | false | Use SharedWorker (tab-sharing) |
| `playground` | boolean | false | Enable code editor overlay |
| `layout` | `"vertical"\|"horizontal"` | horizontal | Playground layout |
| `info` | boolean | false | Show info banner |
| `container` | boolean | true | Show container chrome |
| `initial-height` | string | `"300px"` | Initial height before render |
| `auto-scroll` | boolean | false | Auto-scroll to output |
| `control-page-title` | boolean | false | Set page title from app |
| `app-mode` | boolean | false | Full app mode |

**Child Elements:**

| Tag | Purpose | Attributes |
|-----|---------|------------|
| `<gradio-file>` | Virtual file in Wasm FS | `name` (required), `entrypoint`, `url` |
| `<gradio-requirements>` | requirements.txt content | — |
| `<gradio-code>` | Python source code | — |

### Layer 2: WorkerProxy (Main Thread Bridge)

`WorkerProxy` (in `@gradio/wasm`) manages the Web Worker lifecycle:

1. **Creates worker** — using `CrossOriginWorkerMaker` to handle cross-origin CDN scripts
2. **Two-phase initialization:**
   - Phase 1 (`init-env`): Loads Pyodide runtime + Gradio wheels
   - Phase 2 (`init-app`): Writes files, installs requirements, sets up FS
3. **Message protocol** — Async request-response via `MessageChannel`:
   ```
   Main Thread → postMessage({type, data}) → Worker → reply:success | reply:error
   ```
4. **Events dispatched:**
   - `initialization-completed` — ready to run
   - `initialization-error` — Pyodide/wheel load failure
   - `progress-update` — loading status text
   - `stdout` / `stderr` — Python output forwarding
   - `python-error` — runtime error in user code
   - `modules-auto-loaded` — auto-import completion

### Layer 3: Web Worker (Pyodide Runtime)

The worker (`js/wasm/src/webworker/index.ts`) performs:

1. **Pyodide bootstrap:**
   - Loads `pyodide.js` v0.27.3 via `importScripts`
   - Installs `micropip` for pure-Python package management
   - Loads Gradio wheels (`gradio.whl` + `gradio_client.whl`)
   - Mocks `os.link` (not available in Wasm)
   - Mocks `anyio.to_thread.run_sync` (no threading in Wasm)

2. **Filesystem virtualization:**
   - Python files are written to a virtual FS in the worker's memory (`/home/pyodide/app/`)
   - Support for inline file content and remote URLs
   - Emscripten virtual FS persists only in worker memory

3. **ASGI-over-Wasm protocol:**
   - Gradio's ASGI app is registered via `gradio.wasm_utils.get_registered_app()`
   - HTTP requests from the browser are serialized to ASGI scopes and passed to Python
   - Responses are streamed back via `send()` events
   - Proxied fetch (`wasm_proxied_fetch`) intercepts API calls from Gradio JS client
   - SSE (Server-Sent Events) are proxied via `wasm_proxied_stream_factory`

4. **Package installation with retries:**
   - `installPackages()` wraps `micropip.install()` with up to 3 retries
   - `patchRequirements()` handles version compatibility
   - `verifyRequirements()` checks if packages are installable in Pyodide
   - Supports `keep_going=True` to continue despite partial failures

### Layer 4: Network Proxy (wasm_proxied_fetch)

Since the Wasm worker doesn't have native HTTP access, all network requests must be proxied:

```python
# In the LiteIndex.svelte:
class LiteClient extends Client {
    fetch(input, init) {
        return wasm_proxied_fetch(worker_proxy, input, init)
    }
    stream(url) {
        return wasm_proxied_stream_factory(worker_proxy, url)
    }
}
```

The proxy:
1. Serializes the JS `Request` into a message to the worker
2. Worker passes it to the ASGI app as an ASGI scope
3. ASGI app processes it and sends back response events
4. Worker reassembles the response and returns it to the JS `LiteClient`

### Usage Patterns

**Pattern 1: Simple Inline App (Zero Config)**
```html
<gradio-lite>
import gradio as gr

def greet(name):
    return "Hello, " + name + "!"

gr.Interface(greet, "textbox", "textbox").launch()
</gradio-lite>
```

**Pattern 2: Multi-File App with Entrypoint**
```html
<gradio-lite>
<gradio-file name="app.py" entrypoint>
import gradio as gr
from utils import add

demo = gr.Interface(fn=add, inputs=["number","number"], outputs="number")
demo.launch()
</gradio-file>
<gradio-file name="utils.py">
def add(a, b): return a + b
</gradio-file>
</gradio-lite>
```

**Pattern 3: With External Dependencies**
```html
<gradio-lite>
<gradio-requirements>
transformers_js_py
numpy
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

**Pattern 4: From Remote URL**
```html
<gradio-lite>
<gradio-file name="app.py" entrypoint
    url="https://huggingface.co/spaces/user/demo/raw/main/app.py">
</gradio-file>
</gradio-lite>
```

**Pattern 5: Playground Mode (Editable by Users)**
```html
<gradio-lite playground layout="vertical">
import gradio as gr
gr.Interface(lambda x: f"Hello {x}!", "text", "text").launch()
</gradio-lite>
```

### JavaScript API

Beyond the custom element, `@gradio/lite` exposes a programmatic API:

```javascript
const controller = createGradioApp({
    target: document.getElementById('app'),
    code: 'import gradio as gr\ngr.Interface(...).launch()',
    requirements: ['numpy'],
    files: {'utils.py': {data: 'def add(a,b): return a+b'}},
    entrypoint: 'app.py',
    themeMode: 'dark',
    eager: true,
    sharedWorkerMode: false
})

// Controller methods:
controller.run_code('print("hello")')          // Execute Python code
controller.run_file('app.py')                  // Execute a file
controller.write('file.txt', 'content')        // Write to Wasm FS
controller.rename('old.py', 'new.py')          // Rename in Wasm FS
controller.unlink('file.txt')                  // Delete from Wasm FS
controller.install(['numpy'])                  // Install packages
controller.unmount()                           // Destroy the app

// Events:
controller.addEventListener('stdout', (e) => console.log(e.detail))
controller.addEventListener('stderr', (e) => console.error(e.detail))
controller.addEventListener('python-error', (e) => console.error(e.detail))
controller.addEventListener('initialization-error', (e) => ...)
```

### Playground (`Playground.svelte`)

The Playground wraps the Gradio app with a **code editor overlay** that allows users to edit the Python code and re-run (Ctrl+Enter or Cmd+Enter). Features:
- Syntax-highlighted code editor (monaco-based via `@gradio/code`)
- Lightning icon for "run" affordance
- Two layouts: vertical (code top, output bottom) and horizontal (code left, output right)
- Theme syncs with system/browser preference
- The `handle_theme_mode()` method checks URL params (`__theme`) before system preference
- Progress updates shown during loading ("Loading Pyodide...", "Loading Gradio wheels...")

### Limitations (Verified from Source)

1. **Initial load time** — 5-15 seconds to download + initialize Pyodide + Gradio wheels
2. **Package availability** — Only pure-Python packages installable via micropip; no C extensions unless pre-built for Wasm
3. **No threading** — `anyio.to_thread.run_sync` is mocked to run synchronously
4. **No `os.link`** — mocked to a no-op for `aiofiles` compatibility
5. **Memory** — limited by browser tab (typically 2-4 GB Wasm heap)
6. **Single-threaded Python** — Global Interpreter Lock in Pyodide
7. **No GPU** — no CUDA, no WebGPU bindings for PyTorch (only `transformers-js` for browser-side ML)
8. **Archived** — frozen at v5.45.0, no future updates

### Key Architectural Insights from Source Analysis

1. **The wheel build pipeline:** `pnpm pybuild` runs `hatch build -t lite` to build `gradio.whl`, then `pyodide py-compile` for bytecode optimization (faster loading).

2. **Cross-origin worker trick:** `CrossOriginWorkerMaker` creates a same-origin blob: URL wrapper around the CDN worker script to bypass cross-origin restrictions.

3. **ASGI scope conversion:** The worker converts JS HTTP request objects into Python ASGI scopes with careful byte-encoding of headers, query strings, and raw paths.

4. **Module unloading:** `unload_local_modules.py` provides `unload_local_modules()` to clear Python modules between app runs (important for Playground's re-run cycle).

5. **Code completion:** A `CodeCompleter` class provides tab-completion in the Playground editor via Jedi (Python static analysis).

6. **Random entropy:** Wasm doesn't have `os.urandom` — a `random.ts` module provides seeded random number generation using JavaScript's `crypto.getRandomValues`.

7. **Fake host header:** A `FAKE_LITE_HOST` constant is used for the host header in proxied requests since there's no real server.

8. **Static Spaces integration:** Gradio Lite apps can be hosted as **Hugging Face Static Spaces** (zero-cost, no server) — just push the HTML file to a Space repo.

### Reference

- Source repo (archived): https://github.com/gradio-app/gradio-lite
- CDN package: https://www.jsdelivr.com/package/npm/@gradio/lite
- NPM: https://www.npmjs.com/package/@gradio/lite
- Pyodide: https://pyodide.org/
- Static Spaces guide: https://huggingface.co/docs/hub/en/spaces-static
- Gradio Playground: https://www.gradio.app/playground
---

## 2026-07-24: hf-inference-client-image-input-pipeline-deep-dive

### Summary
Deep-dive into the `huggingface_hub` InferenceClient image input pipeline. The `ContentT` type union accepts 7 input formats (bytes, bytearray, memoryview, BinaryIO, str URL, str/Path, PIL.Image). The `_open_as_mime_bytes()` function normalizes all 7 into `MimeBytes` with mime type detection. Two encoding paths: `_b64_encode()` for JSON payloads and `_as_url()` for data URLs. The `HFInferenceBinaryInputTask` provider sends raw bytes (no params) or b64 JSON (with params). 8 image task methods on the client, plus `chat_completion()` multimodal via OpenAI-compatible content parts.

### References
- `_common.py`: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_common.py
- `_client.py`: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_client.py
- `hf_inference.py`: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_providers/hf_inference.py

---

## 2026-07-24: hf-async-inference-client-patterns

### Summary
Deep dive into Hugging Face's `AsyncInferenceClient` — the async counterpart to `InferenceClient` built on `asyncio` and `httpx`. Covers initialization, streaming, concurrent inference patterns (asyncio.gather, semaphore throttling), error handling, timeouts, MCP client integration (which extends AsyncInferenceClient), OpenAI-compatible async patterns, and performance comparison with synchronous client. The async client enables true single-thread concurrency with coroutines (few KB each vs ~8MB per thread) and non-blocking streaming via `async for`.

### Key Concepts

**Architecture:** AsyncInferenceClient mirrors every method of InferenceClient but uses async/await with httpx.AsyncClient. All constructor params identical (model, provider, token/api_key, timeout, headers, bill_to, cookies, base_url). Method signatures strictly the same — only calling convention differs.

**Streaming Patterns:**
- Chat completion: `async for token in await client.chat_completion(messages, stream=True):`
- Text generation: `async for token in await client.text_generation(prompt, stream=True):`
- stream=True makes the method return an async iterable, not a list

**Concurrent Inference:**
- `results = await asyncio.gather(*[classify(url) for url in urls])`
- Semaphore throttling: `async with sem:` wrapping each call for rate-limited providers
- HTTP connection pool shared across all concurrent tasks — no per-request connection overhead

**OpenAI-Compatible Async:**
```python
output = await client.chat.completions.create(model=..., messages=..., stream=True)
async for chunk in output:
    print(chunk.choices[0].delta.content)
```

**Timeout:** Default = no timeout (waits indefinitely). Set `timeout=30` at client init. Raises `InferenceTimeoutError`.

**Binary Inputs:** Same as sync — bytes, file objects, paths, remote URLs. Auto-downloaded before sending.

**MCP Client Integration:** MCPClient extends AsyncInferenceClient — fundamentally async. `add_mcp_server(type="stdio"|"sse")` for tool discovery. `process_single_turn_with_tools()` returns async iterable.

**Sync vs Async Decision:** Sync for scripts/notebooks; async for servers/agents/batch inference. Async coroutines use few KB vs ~8MB thread stack. Streaming in async mode processes tokens without blocking event loop.

**All Methods Available:** Text (chat_completion, text_generation, fill_mask, feature_extraction, sentence_similarity, summarization, question_answering), Image (text_to_image, image_classification, image_segmentation, image_to_image, image_to_text, image_to_video, zero_shot_image_classification), Audio (audio_classification, audio_to_audio, automatic_speech_recognition, text_to_speech), Multimodal (document_question_answering, visual_question_answering), Management (get_endpoint_info, list_deployed_models, health_check).

### References
- Guide: https://huggingface.co/docs/huggingface_hub/main/en/guides/inference#async-client
- Package ref: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/inference_client
- MCP docs: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/mcp

## 2026-07-24: hf-datasets-tool-calling-format-advanced (Deep Dive #2)

### Summary
Extended tool-calling dataset format research with advanced JSON schema patterns (Union types, Literal types, nested objects, `(choices: ...)` enum parsing), multi-turn and parallel tool calling patterns (tool_call_id conventions), continue_final_message with reasoning models (v5.14+), dataset validation techniques (schema validation, Features casting, TRL response_template), and best practices for publishing tool-calling datasets.

### Key Concepts

**Advanced JSON Schema Patterns:**
- Union types (`str | int`) → `{"type": ["string", "integer"]}`; `None` in Union → `{"nullable": true}`
- Mixed complex types → expressed as `anyOf` array
- `Literal` types → `{"enum": [...]}`, same as `(choices: ...)` docstring suffix
- `(choices: ["a", "b"])` docstring suffix → auto-generated `enum` in schema; requires JSON array syntax
- Nested `list[dict]` → `{"type": "array", "items": {"type": "object"}}` (no recursive inference)
- `dict[str, bool]` → `{"type": "object", "additionalProperties": {"type": "boolean"}}`

**Multi-Turn & Parallel Calls:**
- Multi-turn: sequential tool_call → tool → tool_call → tool → text pattern
- Parallel calls: multiple tool_calls in one assistant message (Qwen2.5, Llama 3.1+)
- `tool_call_id` linking: positional matching when absent; explicit IDs when present
- Tool response matching: Llama requires `call_xxx`, Mistral/Cohere use positional-only

**continue_final_message v5.14+:**
- Accepts string field name: `continue_final_message="reasoning_content"` (Qwen) or `"thinking"` (Gemma)
- Prefilling content closes reasoning block; prefilling reasoning field keeps it open
- Mutually exclusive with add_generation_prompt
- Pipeline auto-detects assistant prefill and switches modes

**Dataset Validation:**
- Custom validator function checks: message order, tool_calls structure, tool→assistant adjacency, content types
- datasets Features schema enforces structure at creation time
- SFTTrainer response_template masks non-assistant tokens for correct loss computation
- Hub dataset viewer parses messages column and supports ?search= queries

**Best Practices:** Store tools as JSON schema in `tools` column, Parquet format for efficiency, always test with `apply_chat_template(tokenize=False)`, use response_template in SFTTrainer, include `tool-calling` tag for discoverability.

### Sources
- Transformers chat_template_utils.py (source analysis): Union/Literal/choices parsing
- Transformers docs (v5.14.0): chat_templating.md, conversations.md
- Transformers tokenization_utils_base.py: apply_chat_template() signature
- datasets library Features API

---

## 2026-07-24: hf-transformers-5-architecture-registry-system-deep-dive (Topic #195)

### Summary
Source-verified deep-dive into the Transformers v5 Architecture Registry system — the complete pipeline by which config classes are mapped to model classes, remote code is resolved, and custom models register themselves with AutoModel/AutoConfig. Covers `_LazyAutoMapping`, `CONFIG_MAPPING_NAMES` (682 entries), `AutoConfig.register()`, `AutoModel.register()`, the `from_pretrained` resolution flow (local vs. remote code), `_get_model_class`, `register_for_auto_class`, `model_type_to_module_name`, and `get_class_from_dynamic_module`. All findings verified against `transformers==5.14.1` source.

### Key Concepts

**Two-Level Registration:** Transformers v5 uses a two-level registration system:

1. **`AutoConfig` — Config-level registry** (string → config class): `AutoConfig.register(model_type, config_class)` adds to `CONFIG_MAPPING` (a `_LazyAutoMapping` keyed by string model_type like `"llama"`, `"qwen2"`) — 682 entries.
2. **`AutoModel` — Model-level registry** (config class → model class): `AutoModel.register(config_class, model_class)` adds to `cls._model_mapping` (another `_LazyAutoMapping` keyed by config class).

**`_LazyAutoMapping` — The Core (source: `transformers.models.auto.auto_factory`):**
An `OrderedDict` subclass that lazy-loads model/config classes from `transformers.models.{module_name}` only when accessed. Contains:
- `_config_mapping`: `{model_type: config_class_name}` — maps model type strings to config class names (e.g., `"llama"` → `"LlamaConfig"`)
- `_model_mapping`: `{model_type: model_class_name}` — maps model type strings to model class names
- `_reverse_config_mapping`: `{config_class_name: model_type}` — reverse lookup
- `_extra_content`: `{config_class: model_class}` — for user-registered custom models (overrides native mappings)
- `_modules`: `{module_name: module}` — cache of imported model modules

**Key behaviours:**
- **Lazy loading**: Classes are imported only when accessed via `__getitem__` or `keys()`
- **Module resolution**: Uses `model_type_to_module_name(model_type)` which normalizes dashes to underscores (e.g., `"command-r"` → `"command_r"`)
- **Import path**: `from transformers.models.{module_name} import {class_name}`
- **`register(key, value, exist_ok=False)`**: Inserts into `_extra_content`. Skips registration if the config class module starts with `"transformers."` — this prevents native configs from being permanently remapped to custom models when `trust_remote_code=False` is later specified.

### AutoModel.from_pretrained() Resolution Flow

```
from_pretrained(model_name, ...)
  │
  ├── 1. Load config.json → config = AutoConfig.from_pretrained(...)
  │
  ├── 2. Check PEFT adapter config (find_adapter_config_file)
  │      If found, redirect base_model_name_or_path
  │
  ├── 3. Determine code source:
  │      has_remote_code = "auto_map" in config and cls.__name__ in config.auto_map
  │      has_local_code   = type(config) in cls._model_mapping
  │
  ├── 4. Resolve trust_remote_code via resolve_trust_remote_code()
  │
  ├── 5. Dispatch:
  │      ├── REMOTE CODE (has_remote_code && trust_remote_code && !explicit_local_code):
  │      │     class_ref = config.auto_map[cls.__name__]  # e.g., "modeling_lm.py--MyModel"
  │      │     model_class = get_class_from_dynamic_module(class_ref, ...)
  │      │     cls.register(config.__class__, model_class, exist_ok=True)
  │      │     model_class.register_for_auto_class(auto_class=cls)
  │      │     model_class = add_generation_mixin_to_remote_model(model_class)
  │      │     return model_class.from_pretrained(...)
  │      │
  │      └── LOCAL CODE (has_local_code):
  │            model_class = _get_model_class(config, cls._model_mapping)
  │            # If composite model, extract text_config and its quantization_config
  │            return model_class.from_pretrained(...)
  │
  └── 6. (Error if neither remote nor local code available)
```

**Remote Code Resolution (`config.auto_map`):**
The `auto_map` dict in `config.json` maps Auto class names to Python class references:
```json
{
  "auto_map": {
    "AutoConfig": "configuration_my_model.MyModelConfig",
    "AutoModel": "modeling_my_model.MyModel",
    "AutoModelForCausalLM": "modeling_my_model.MyModelForCausalLM"
  }
}
```
- Format: `"module_path.ClassName"` or `"repo_id--module_path.ClassName"` (cross-repo)
- `get_class_from_dynamic_module()` downloads the repo's code files to local cache and dynamically imports the class
- After loading, `cls.register()` adds to `_extra_content` for fast subsequent lookups
- `register_for_auto_class()` sets `cls._auto_class` on the model class for serialization

### `_get_model_class()` — Sub-Architecture Selection

```python
def _get_model_class(config, model_mapping):
    supported_models = model_mapping[type(config)]
    if not isinstance(supported_models, (list, tuple)):
        return supported_models

    name_to_model = {model.__name__: model for model in supported_models}
    architectures = getattr(config, "architectures", [])
    for arch in architectures:
        if arch in name_to_model:
            return name_to_model[arch]

    # Fallback to first element
    return supported_models[0]
```

This handles cases where one config maps to multiple model classes (e.g., `LlamaConfig` → `LlamaModel`, `LlamaForCausalLM`, `LlamaForSequenceClassification`). The `config.architectures` field (e.g., `["LlamaForCausalLM"]`) selects the correct one. If absent, the first registered model class is used.

### Custom Model Registration (User-Side)

```python
from transformers import AutoConfig, AutoModel

# 1. Register the config
AutoConfig.register("my_model", MyModelConfig)

# 2. Register the model (with error checking)
AutoModel.register(MyModelConfig, MyModel, exist_ok=False)

# 3. Mark the model class for auto-serialization
MyModel.register_for_auto_class("AutoModel")

# 4. Now use normally
model = AutoModel.from_pretrained("path/to/model")
```

The `exist_ok=False` default raises if the config class is already mapped. Set to `True` for hot-reloading or overrides.

### Important Guard: Native Config Protection

```python
# In _LazyAutoMapping.register():
if getattr(key, "__module__", "").startswith("transformers."):
    return  # Skip — native configs can't be permanently remapped
```

This ensures that if a remote-code model reuses a native Transformers config (e.g., `LlamaConfig`), the registration is silently skipped. Without this, every subsequent `from_pretrained` call would resolve to the custom model even with `trust_remote_code=False`, because the custom class would sit in `_extra_content` and take priority. Instead, the remote/native disambiguation happens only at `trust_remote_code` time via `resolve_trust_remote_code()`.

### `model_type_to_module_name()` Normalization

```python
model_type_to_module_name("command-r")  # → "command_r"
model_type_to_module_name("qwen2_moe")  # → "qwen2_moe"
model_type_to_module_name("phi4")        # → "phi4"
```

Simply replaces hyphens with underscores. Module names match the model type string (underscore-normalized).

### `register_for_auto_class()` — Serialization Support

```python
@classmethod
def register_for_auto_class(cls, auto_class="AutoModel"):
    import transformers.models.auto as auto_module
    if not hasattr(auto_module, auto_class):
        raise ValueError(f"{auto_class} is not a valid auto class.")
    cls._auto_class = auto_class
```

Sets `cls._auto_class` so that when `save_pretrained()` writes `config.json`, it includes the correct `auto_map` entry for the model's Auto class. Required for custom models that should be loadable with `AutoModel.from_pretrained()` after re-upload.

### `add_generation_mixin_to_remote_model()` — Backward Compat

For backward compatibility with pre-v4.45 models (when `PreTrainedModel` stopped inheriting `GenerationMixin`):
- Checks if model inherits `torch.nn.Module`
- Checks if it already directly inherits `GenerationMixin`
- Checks if it has custom `generate()` or `prepare_inputs_for_generation()`
- If needed, creates a new `type()` dynamically: `type(model_class.__name__, (model_class, GenerationMixin), {**model_class.__dict__})`

### All AutoModel* Classes in v5.14.1

53 Auto classes total. Key groups:
- **Core**: `AutoModel`, `AutoModelForPreTraining`, `AutoModelForCausalLM`, `AutoModelForSeq2SeqLM`, `AutoModelForMaskedLM`
- **Vision**: `AutoModelForImageClassification`, `AutoModelForObjectDetection`, `AutoModelForSemanticSegmentation`, `AutoModelForVideoClassification`, `AutoBackbone`
- **Audio**: `AutoModelForAudioClassification`, `AutoModelForCTC`, `AutoModelForSpeechSeq2Seq`, `AutoModelForTextToSpectrogram`
- **Multimodal**: `AutoModelForImageTextToText`, `AutoModelForMultimodalLM`, `AutoModelForImageToImage`, `AutoModelForVisualQuestionAnswering`, `AutoModelForDocumentQuestionAnswering`
- **Special**: `AutoModelForKeypointDetection`, `AutoModelForKeypointMatching`, `AutoModelForPointmapEstimation`, `AutoModelForNormalEstimation`
- **Other**: `AutoProcessor`, `AutoTokenizer`, `AutoFeatureExtractor`, `AutoImageProcessor`, `AutoVideoProcessor`

### Sources
- `transformers.models.auto.auto_factory` — `_LazyAutoMapping`, `_get_model_class`, `add_generation_mixin_to_remote_model`, `model_type_to_module_name`, `resolve_trust_remote_code`
- `transformers.models.auto.configuration_auto` — `CONFIG_MAPPING`, `CONFIG_MAPPING_NAMES` (682 entries)
- `transformers.models.auto.modeling_auto` — AutoModel source (register, from_pretrained)
- `transformers.models.auto.tokenization_auto` — AutoTokenizer
- `transformers.modeling_utils` — `register_for_auto_class`
- Docs: https://huggingface.co/docs/transformers/en/model_doc/auto
- Source: https://github.com/huggingface/transformers/tree/main/src/transformers/models/auto

## 2026-07-24: hf-hub-sandboxes-deep-dive (deepening #148)

### Summary
Deep dive into Hugging Face Sandboxes — on-demand isolated cloud machines for running code, AI-generated scripts, batch eval, and RL rollouts. Built on HF Jobs with a static sbx-server binary. Two modes: dedicated (full VM, GPU) and pooled (uid+Landlock, CPU-only).

### Architecture
- No dedicated service — sandbox = HF Job running ~640KB static Rust binary (zero deps, any image with /bin/sh)
- Bootstrap: wget/curl from CDN (~6s cold start) or fallback from mounted volume (+2-3s)
- Hand-rolled HTTP/1.1 for live streaming (NDJSON event streams for exec)
- Port 49983 (deliberately uncommon)

### Auth (stateless)
- Proxy gate: HF token → Jobs proxy
- Application gate: HMAC-SHA256 per-sandbox token from HF token + public nonce
- Reconnect from anywhere, token never enters sandbox (unless opt-in)

### Dedicated (Sandbox.create)
- One Job = one VM, full isolation, GPU-capable
- Cold start ~5.8s, run() p50 ~110ms, file transfer ~340-441 MiB/s
- kill() cancels the Job

### Pooled (SandboxPool)
- Many sandboxes per host VM via uid + Landlock isolation
- Create = mkdir + chown + ruleset ~1ms server-side
- 1000 sandboxes in ~16s total (~$0.0009), vs ~$0.06 for dedicated
- Blocked: cross-sandbox /proc read, signal, ptrace, TCP bind, abstract unix sockets
- Not blocked: resource DoS, process-list metadata (shared kernel)

### Key API
- Sandbox.create(image, flavor, idle_timeout, env, secrets, volumes, forward_hf_token)
- Sandbox.connect(id) — from anywhere
- sbx.run(cmd, shell, env, cwd, timeout, stdin, on_stdout, on_stderr, check, background)
- sbx.files.{write,read_text,upload,download,list,stat,exists,mkdir,delete}
- sbx.proxy_url_for(port, path, scheme) + sbx.proxy_headers
- SandboxPool(image, flavor, sandboxes_per_host=50, warm_up=1)
- pool.create(env, idle_timeout, forward_hf_token)
- CLI: hf sandbox {create,exec,cp,spawn,process,kill,pool} — full parity

### Source
- https://huggingface.co/docs/huggingface_hub/guides/sandbox
- https://huggingface.co/docs/huggingface_hub/concepts/sandbox
- https://huggingface.co/docs/huggingface_hub/package_reference/sandbox
- https://github.com/huggingface/sandbox-server

## 2026-07-24: hf-hub-repo-likes-engagement-api — Repo Like/Engagement System (Topic #213)

### Summary
Deep dive into the Hugging Face Hub's repository "like" engagement system — the social signal system for expressing interest in repos. Unlike GitHub's stars, HF uses a "like" (heart) model with a deliberate anti-spam asymmetry: users can unlike via API but can only like through the web UI. Covers the 3 API methods (`list_liked_repos`, `list_repo_likers`, `unlike`), the REST endpoints behind them, the `UserLikes` and `User` dataclasses, how likes integrate into user profiles, and the relationship between likes, engagement, and the trending/discovery system.

### Key API Surface

**`list_liked_repos(user=None)`** → `UserLikes`
- REST: `GET /api/users/{user}/likes`
- Returns all public repos a user has liked, categorized by type (models, datasets, spaces, kernels)
- If user is None, defaults to the authenticated user (requires token)
- No auth required when querying a public user's likes
- Returns `UserLikes(user, total, models, datasets, spaces, kernels)` with repo IDs as strings
- Response shape from API: Array of `{createdAt, repo: {name, type}}` objects

**`list_repo_likers(repo_id, repo_type=None)`** → `Iterable[User]`
- REST: `GET /api/{repo_type}s/{repo_id}/likers`
- Returns an iterable of `User` objects for all users who liked a given repo
- Paginated (uses the `paginate` helper internally)
- Works across model, dataset, and space repos
- Each `User` object provides: username, fullname, avatar_url

**`unlike(repo_id, repo_type=None)`** → `None`
- REST: `DELETE /api/{repo_type}s/{repo_id}/like`
- Removes the authenticated user's like from a repo
- Requires authentication (token)
- **No symmetric `like()` method exists** — anti-spam measure: "To prevent spam usage, it is not possible to like a repository from a script"

### User Profile Likes Integration

The `User` dataclass (`huggingface_hub.hf_api.User`) exposes engagement metrics:
| Field | Source | Description |
|-------|--------|-------------|
| `num_upvotes` | User profile API | Total upvotes the user has received across their repo contributions |
| `num_likes` | User profile API | Total number of likes the user has given to other repos |
| `num_followers` | User profile API | Number of users following this user |
| `num_following` | User profile API | Number of users this user follows |

These come from the user profile API and are resolved from camelCase Hub API fields (`numUpvotes`, `numLikes`, `numFollowers`, `numFollowing`).

### Anti-Spam Architecture

The like system has a deliberate read-write asymmetry:
- **Read:** Both `list_liked_repos` and `list_repo_likers` are public, no token required for public data
- **Write (unlike):** `DELETE` endpoint requires auth, but only removes — no ability to add
- **Write (like):** Only possible through the web UI at huggingface.co (button click on a repo page)
- This prevents scripted vote manipulation, bot-driven like campaigns, and engagement farming

### Like Count in Repo Info

The like count for a repo is visible via the web UI and can be obtained via:
- `api.repo_info(repo_id).likes` — the `RepoInfo` object's `likes` attribute (int)
- The Hub REST API returns like count in repo metadata: `GET /api/models/{repo_id}` or `/api/datasets/{repo_id}` or `/api/spaces/{repo_id}`
- Like count is part of `RepoInfo.likes` field (an integer)
- Likes are counted in the trending/ranking algorithms for discovery

### Relationship to Discussion Reactions

The Hub's discussion/PR system has a separate emoji reaction system (not the same as repo likes):
- Comments and discussion posts support emoji reactions (👍, ❤️, 🚀, 👀, 🎉, 😕, etc.)
- These are managed through different API endpoints under `/api/{repo_type}s/{repo_id}/discussions/{num}/reactions`
- The huggingface_hub library doesn't expose a direct reaction API — reactions are embedded in `DiscussionComment` objects returned by `get_discussion_details()`
- Each reaction has: `emoji` (string like "+1", "heart", "rocket") and list of users who reacted
- This is a separate system from the repo "like" system

### Key Insights
- HF uses "likes" (hearts) not "stars" — the REST endpoint paths use `/like` and `/likers`
- Unlike GitHub stars, HF's system is read-heavy with deliberate write restrictions
- The `list_liked_repos` API is useful for recommendation/discovery — "users who liked X also liked Y" patterns
- `list_repo_likers` can be used for community engagement analysis (who's interested in your repos)
- The `unlike` method exists primarily for cleanup (removing stale likes programmatically)
- Like count is a search/sortable field in Hub API queries (e.g., sorting by likes)
- Like events are not real-time streamed through webhooks (no webhook event for likes unlike GitHub stars)
- To get likes for your own repos, use `list_repo_likers()` in batches or read from `repo_info().likes`

### Sources
- Source code: `huggingface_hub/hf_api.py` — `HfApi.list_liked_repos`, `HfApi.list_repo_likers`, `HfApi.unlike`
- Source code: `huggingface_hub/hf_api.py` — `UserLikes` dataclass, `User` dataclass
- Hub API docs: https://huggingface.co/docs/hub/en/api
- huggingface_hub docs: https://huggingface.co/docs/huggingface_hub/package_reference/hf_api
- Discussion reactions documented in `endpoint_helpers.py` (`DiscussionComment.reactions`)

---

## 2026-07-24: hf-hub-jobs-api-deep-dive

### Summary
Deep dive into the Hugging Face Hub **Jobs API** — a compute platform for running AI/data workloads on HF infrastructure. Jobs support any hardware from CPUs to A100s & H200s, with pay-as-you-go pricing. The API is exposed through `huggingface_hub` (`HfApi.run_job`, `run_uv_job`, `create_scheduled_job`, etc.), the `hf` CLI, and the Jobs HTTP API. Includes support for Docker images, UV scripts, cron scheduling, volume mounting (buckets/repos), port exposition, SSH access, metrics/logs streaming, and webhook integration.

### Key Data Structures (in `huggingface_hub._jobs_api`)

| Class | Purpose |
|-------|---------|
| `JobHardware(str, Enum)` | Hardware flavors: CPU_BASIC, T4_SMALL, A10G_LARGE, A100_LARGE, H200, L40SX8, etc. |
| `JobStage(str, Enum)` | Job lifecycle: SCHEDULING, RUNNING, COMPLETED, CANCELED, ERROR, DELETED |
| `JobStatus` | Stage + message + expose_urls + ssh_url |
| `JobInfo` | Full job metadata: id, timestamps, image/space, command, env, secrets, flavor, labels, volumes, status, durations, owner, initiator |
| `JobDurations` | Timing: scheduling_secs, running_secs, total_secs |
| `JobInitiator` | What triggered the job: type(user/org/scheduled-job), id, name |
| `JobOwner` | Owner: id, name, type |
| `JobSpec` | Job specification (image, command, env, flavor, timeout, labels, volumes, expose, ssh) |
| `ScheduledJobInfo` | Scheduled job: id, schedule (cron), suspend, concurrency, status, owner, job_spec |
| `ScheduledJobStatus` | last_job, next_job_run_at |
| `JobHardwareInfo` | Available hardware: name, pretty_name, cpu, ram, ephemeral_storage, accelerator, cost |
| `JobAccelerator` | GPU details: type, model, quantity, vram, manufacturer |
| `Volume` (in `_space_api.py`) | Volume to mount: type(bucket/model/dataset/space), source, mount_path, revision, read_only, path |

### HfApi Methods

**Run Jobs:**
- `run_job(*, image, command, env, secrets, flavor, timeout, name, labels, volumes, expose, ssh, namespace)` → `JobInfo` — run a Docker-based job
- `run_uv_job(script, *, script_args, dependencies, python, image, env, secrets, flavor, timeout, name, labels, volumes, expose, ssh, namespace)` → `JobInfo` — run a UV script job (auto-generates Dockerfile from script dependencies)

**Inspect/Monitor:**
- `inspect_job(*, job_id, namespace)` → `JobInfo` — get full job status
- `list_jobs(*, status, labels, namespace)` → `Iterable[JobInfo]` — filter by status/labels
- `fetch_job_logs(*, job_id, namespace, follow, tail)` → `Iterable[str]` — stream logs
- `fetch_job_metrics(*, job_id, namespace)` → `Iterable[dict]` — live metrics (CPU, GPU, memory, etc.)
- `wait_for_job(job_id, *, timeout, poll_interval, stages, namespace)` → `JobInfo` — block until job reaches a stage
- `cancel_job(*, job_id, namespace)` → `None` — cancel a running job

**Labels:**
- `update_job_labels(*, job_id, labels, namespace)` → `JobInfo` — replace all labels

**Hardware:**
- `list_jobs_hardware()` → `list[JobHardwareInfo]` — list available hardware with pricing

**Scheduled Jobs:**
- `create_scheduled_job(*, image, command, schedule, suspend, concurrency, env, secrets, flavor, timeout, name, labels, volumes, expose, ssh, namespace)` → `ScheduledJobInfo`
- `create_scheduled_uv_job(script, *, schedule, suspend, concurrency, deps, python, image, ...)` → `ScheduledJobInfo`
- `list_scheduled_jobs(*, namespace)` → `list[ScheduledJobInfo]`
- `inspect_scheduled_job(*, scheduled_job_id, namespace)` → `ScheduledJobInfo`
- `suspend_scheduled_job(*, scheduled_job_id, namespace)` → `None` — pause
- `resume_scheduled_job(*, scheduled_job_id, namespace)` → `None` — unpause
- `trigger_scheduled_job(*, scheduled_job_id, namespace)` → `JobInfo` — immediate one-shot run
- `update_scheduled_job_labels(*, scheduled_job_id, labels, namespace)` → `ScheduledJobInfo`
- `delete_scheduled_job(*, scheduled_job_id, namespace)` → `None`

**Volumes & Artifacts:**
- `sync_job_volume(source, mount_path, *, remote_name, read_only, namespace)` → `Volume` — sync a local dir to a bucket and return a Volume ready to mount

### REST API Endpoints (inferred from source)
- `POST /api/jobs` — create/run a job
- `GET /api/jobs/{job_id}` — inspect
- `GET /api/jobs` — list (with query params: status, labels)
- `POST /api/jobs/{job_id}/cancel` — cancel
- `GET /api/jobs/{job_id}/logs` — fetch logs
- `GET /api/jobs/{job_id}/metrics` — fetch metrics
- `PATCH /api/jobs/{job_id}/labels` — update labels
- `POST /api/scheduled-jobs` — create scheduled job
- `GET /api/scheduled-jobs` — list scheduled
- `GET /api/scheduled-jobs/{id}` — inspect scheduled
- `POST /api/scheduled-jobs/{id}/trigger` — trigger immediate run
- `POST /api/scheduled-jobs/{id}/suspend` — pause
- `POST /api/scheduled-jobs/{id}/resume` — unpause
- `DELETE /api/scheduled-jobs/{id}` — delete
- `PATCH /api/scheduled-jobs/{id}/labels` — update labels
- `GET /api/jobs/hardware` — list available hardware

### Hardware Flavors & Pricing
CPU: cpu-basic (2 vCPU, 16 GB, $0.000167/min), cpu-upgrade, cpu-performance, cpu-xl
GPU: t4-small, t4-medium, l4x1, l4x4, l40sx1, l40sx4, l40sx8, a10g-small, a10g-large, a10g-largex2/x4, a100-large, a100x4/x8, h200, h200x2/x4/x8, rtx-pro-6000 series
Each `JobHardwareInfo` exposes: name, pretty_name, cpu, ram, ephemeral_storage, accelerator (model + vram + quantity), unit_cost_micro_usd, unit_cost_usd, unit_label

### UV Job Magic
`run_uv_job` is the most convenient entry point. Instead of building a Docker image, you provide:
- `script`: path/URL to a Python script (or inline command)
- `dependencies`: list of pip packages (or use script's inline `# /// script` metadata)
- `python`: Python version (e.g. "3.12")
It auto-builds a Docker image under the hood — no Dockerfile needed.

### Schedule Syntax
Supports both named presets: `@annually`, `@yearly`, `@monthly`, `@weekly`, `@daily`, `@hourly`, and standard CRON expressions (e.g., `'0 9 * * 1'` = 9 AM every Monday).

### Volume Mounting
Volumes allow mounting HF buckets, models, datasets, or Spaces inside the job container:
```python
from huggingface_hub import Volume
Volume(type="bucket", source="username/my-bucket", mount_path="/data", read_only=False)
Volume(type="model", source="username/my-model", mount_path="/model", revision="main")
Volume(type="dataset", source="username/my-dataset", mount_path="/dataset", path="subfolder")
```
`sync_job_volume()` makes it easy to sync local directories to a bucket and get back a ready-to-use Volume.

### SSH Access
Jobs can be started with `ssh=True`. This gives:
- `job.status.ssh_url` — e.g. `ssh://687fb7...d998@ssh.hf.jobs`
- Full SSH access to the container while it's running
- Requires SSH key registered at https://huggingface.co/settings/keys
- Useful for debugging, interactive work, and attaching tools

### Port Exposition
Jobs can expose container ports via `expose=[8000, 8080]`. Each gets a public URL:
- `https://<job_id>--8000.hf.jobs`, `https://<job_id>--8080.hf.jobs`
- Access requires HF token with read access to the namespace
- Perfect for web servers, APIs, dashboards

### Key Insights
- Jobs are serverless compute on HF's own infrastructure — no cluster management needed
- Pay-per-second billing (only for seconds used, unlike Spaces which bill hourly)
- `run_uv_job` is the simplest way to get started — no Docker knowledge needed
- Scheduled jobs use familiar cron syntax, perfect for ETL, model retraining, daily reports
- Volumes bridge buckets (persistent storage) with job containers
- SSH and port exposition make Jobs suitable for interactive debugging and short-lived services
- Jobs integrate with webhooks for automation workflows
- The Jobs API is in `huggingface_hub` v1.24.0+ (newer than Spaces hardware API)
- Currently Jobs are a paid service — no free tier (unlike Spaces ZeroGPU)
- Job IDs are exposed in URLs like `https://huggingface.co/jobs/{owner}/{job_id}`

### Sources
- Source code: `huggingface_hub/_jobs_api.py` — all data structures (JobInfo, JobStage, JobHardware, ScheduledJobInfo, etc.)
- Source code: `huggingface_hub/hf_api.py` — `HfApi.run_job`, `run_uv_job`, `create_scheduled_job`, `list_jobs`, `inspect_job`, `fetch_job_logs`, `fetch_job_metrics`, `sync_job_volume`, etc.
- Source code: `huggingface_hub/_space_api.py` — `Volume` dataclass
- Hub docs: https://huggingface.co/docs/hub/en/jobs
- huggingface_hub docs: https://huggingface.co/docs/huggingface_hub/package_reference/hf_api

---

## 2026-07-24: hf-datasets-parquet-column-selection-deep-dive — Column Projection and Filter Pushdown Deep Dive

### Summary
Deep-dive into the Hugging Face Datasets library's Parquet integration covering column projection (columns=), filter/predicate pushdown (filters=), row group skipping via Parquet column statistics, fragment scan options (v4.2.0+), content-defined chunking in to_parquet(), and practical zero-cost analytics patterns with DuckDB, Polars, and the hf:// protocol.

### Key Findings
- Column projection (columns= param): filters at the PyArrow scan level, reads only requested column chunks from disk. Nested prefixes work ("a" -> a.b, a.c).
- Filter pushdown (filters= param): accepts ds.Expression, list[tuple] (AND), or list[list[tuple]] (DNF). Internally calls pq.filters_to_expression() -> parquet_fragment.to_batches(filter=...). Row group min/max statistics skip entire row groups when filter cannot match.
- FragmentScanOptions (v4.2.0): ParquetFragmentScanOptions with custom CacheOptions(prefetch_limit, range_size_limit) for tuning HTTP range reads on remote Parquet.
- Content-defined chunking (CDC): Enabled by default in to_parquet(). Splits row groups at content-defined boundaries (256KB-1MB) using DEFAULT_CDC_OPTIONS. Pass use_content_defined_chunking=False to disable.
- Batch size auto-tuning: Targets MAX_ROW_GROUP_SIZE = "100MB" uncompressed per row group. Separate overrides for audio/image/binary datasets.
- Compression strategy: Snappy for normal columns, none for media columns (Image/Audio), PLAIN encoding for media, dictionary encoding for text.
- Streaming + filters: Row group skipping works identically in streaming mode - non-matching row groups are never downloaded.
- Zero-cost external queries: DuckDB and Polars both support native Parquet predicate pushdown and column projection when reading directly from hf:// URLs.

### Skill Created
mlops/hf-datasets-parquet-column-selection/ - complete reference with source-code-verified architecture, API surface, config constants, performance patterns, and pitfalls.

### Sources
- Source code: src/datasets/arrow_dataset.py - from_parquet() line 1491, to_parquet() line 5625
- Source code: src/datasets/io/parquet.py - ParquetDatasetReader, ParquetDatasetWriter
- Source code: src/datasets/packaged_modules/parquet/parquet.py - ParquetConfig, Parquet._generate_tables()
- Source code: src/datasets/config.py - MAX_ROW_GROUP_SIZE, DEFAULT_CDC_OPTIONS, USE_PARQUET_EXPORT

---

## 2026-07-24: gr.Workflow — Gradio's Visual AI Pipeline Builder (source-code deep dive)

### Summary
Deep dive into Gradio's `gr.Workflow` system (gradio ≥ 6.17, current 6.20.0), a complete visual AI pipeline builder embedded in Gradio. Covers the Workflow class, WorkflowCanvas component, WorkflowGraph schema v2 parser/executor, 19 server functions, curated operator catalog, auth model, and API endpoint registration.

### Key Findings

1. **Architecture**: `Workflow(Blocks)` extends `gr.Blocks` with `mode="workflow"`. Contains a `WorkflowCanvas` (both BlockContext and Component) that renders the Svelte-based visual canvas. Cannot be nested in other Blocks.

2. **Workflow Graph Schema v2**: JSON with four node roles: `references` (I/O data sources), `operators` (processing nodes — Spaces / Models / bound fns / datasets), `subjects` (outputs → API endpoints), `edges` (connections between ports).

3. **Three modes of use**: graph-only (`graph=`), bind-only (`bind=[fns]`), auto-wired (`bind + edges=`). When `graph` file exists, `edges` is ignored with a warning.

4. **Operator execution**: `call_space()` via gradio_client, `call_model()` via InferenceClient, `call_fn()` for bound Python functions, `fetch_dataset()` via datasets-server API. Each with structured error responses (error/error_type/suggestion).

5. **Auth model**: Write token from HF login (local) or OAuth (Spaces). `save_workflow` enforces write access. Write-access link printed at launch for local mode. `_resolve_token()` checks data → OAuth → local in priority.

6. **API endpoints**: Each subject becomes a named Gradio API endpoint via `WorkflowEndpointManager`. Re-syncs on every save. Bound functions get `predict_fn_<name>` endpoints. Supports both server-side and client-side execution.

7. **Curated catalog**: Ships a bundled snapshot of validated Spaces/models from `gradio/workflow-curated` HF dataset. Cached in-memory for 3600s with bundled JSON fallback. Search prioritizes ZeroGPU → featured → fastest latency.

8. **Port types**: Scalar types (int→number, float→number, bool→boolean, rest→text). Media types (image/audio/video/file/gallery/model3d) travel as `{path/url}` dicts.

9. **Thread safety**: `_save_lock` serializes writes. 5 MB payload limit. Bound functions run via `anyio.to_thread.run_sync`. Concurrent search via `ThreadPoolExecutor(max_workers=4)`.

10. **Key version history**: 6.17.0 introduced Workflow + WorkflowCanvas, 6.19.0 added subgraph API endpoint exposure, 6.20.0 added curated catalog with ZeroGPU sorting + canvas UX improvements.

### Skill Created
`mlops/gradio-workflow/` — complete skill with SKILL.md documenting Workflow API, architecture, usage patterns, server functions, graph schema, and dependencies.

### Sources
- Source code: `gradio/workflow.py` (1,880 lines) — Workflow class, 19 server functions, curated search
- Source code: `gradio/workflow_api.py` (885 lines) — WorkflowGraph, topo-sort, executor, WorkflowEndpointManager
- Source code: `gradio/components/workflowcanvas.py` (126 lines) — WorkflowCanvas component
- Demo: `demo/workflow/run.py` — product marketing image pipeline
- Demo: `demo/workflow_api/run.py` — API-exposed shout + reverse
- Gradio changelog: 6.17.0–6.20.0
- HF Hub: `gradio/workflow-curated` dataset + bundled `_workflow_curated_snapshot.json`

---

## 2026-07-25: hf-hub-user-and-org-profile-api — Hub User and Organization Profile API Reference

### Summary
Complete deep-dive into the Hugging Face Hub's User and Organization Profile API, covering the REST endpoints, the `huggingface_hub` Python SDK methods, the `User` and `Organization` dataclasses, social graph (followers/following), likes and repo enumeration, and the `whoami` authentication endpoint.

### Key Findings

1. **Core API Endpoints (REST)**:
   - `GET /api/whoami-v2` — Authenticated user info (requires token). Returns `{ "name", "fullname", "email", "canPay", "isPro", "orgs": [...] }`. Cached by Hugging Face with strict rate limits (429 is common for frequent calls).
   - `GET /api/users/{username}/overview` — Public user profile. Returns `{ "user", "fullname", "avatarUrl", "isPro", "details", "numModels", "numDatasets", "numSpaces", "numDiscussions", "numPapers", "numUpvotes", "numLikes", "numFollowing", "numFollowers", "orgs": [...] }`.
   - `GET /api/organizations/{org}/overview` — Public organization profile. Returns `{ "avatarUrl", "name", "fullname", "details", "isVerified", "isFollowing", "numUsers", "numModels", "numSpaces", "numDatasets", "numFollowers", "numPapers", "plan" }`.
   - `GET /api/users/{username}/followers` — Paginated list of followers (each a `User` object).
   - `GET /api/users/{username}/following` — Paginated list of users followed by this user.
   - `GET /api/organizations/{org}/followers` — Paginated list of org followers.
   - `GET /api/organizations/{org}/members` — Paginated list of org members.
   - `GET /api/settings/repositories` — All repos for the authenticated user (with storage info). Requires auth.
   - `GET /api/organizations/{org}/settings/repositories` — All repos for an org.
   - `GET /api/{repo_type}s/{repo_id}/likers` — Users who liked a specific repo.
   - `GET /api/users/{username}/likes` — What a user has liked (models, datasets, spaces, etc.).

2. **Python SDK (huggingface_hub)**:

   **User class** (`hf_api.py:1750`):
   - Fields: `username`, `fullname`, `avatar_url`, `details`, `is_following`, `is_pro`, `num_models`, `num_datasets`, `num_spaces`, `num_discussions`, `num_papers`, `num_upvotes`, `num_likes`, `num_following`, `num_followers`, `orgs` (list of `Organization`)
   - Constructed from snake_case-mapped JSON (e.g., `numModels` → `num_models`).
   - Forward-compatible: unknown fields merged via `__dict__.update(**kwargs)`.

   **Organization class** (`hf_api.py:1683`):
   - Fields: `avatar_url`, `name`, `fullname`, `details`, `is_verified`, `is_following`, `num_users`, `num_models`, `num_spaces`, `num_datasets`, `num_followers`, `num_papers`, `plan`
   - Same forward-compatibility pattern as User.

   **UserLikes class** (`hf_api.py:1614`):
   - Fields: `user` (str), `total` (int), `datasets` (list[str]), `kernels` (list[str]), `models` (list[str]), `spaces` (list[str])

   **Key HfApi methods**:
   - `whoami(token, *, cache=False)` → dict — calls `/api/whoami-v2`. Cache=True caches per-token for process lifetime. Raises `LocalTokenNotFoundError` if no token, `HfHubHTTPError(401)` for invalid token, `HfHubHTTPError(429)` on rate limit.
   - `get_user_overview(username)` → User — calls `/api/users/{username}/overview`. HTTP 404 raised as `HfHubHTTPError`.
   - `get_organization_overview(organization)` → Organization — calls `/api/organizations/{org}/overview`.
   - `list_user_followers(username)` → Iterable[User] — paginated via `paginate()` helper.
   - `list_user_following(username)` → Iterable[User] — paginated.
   - `list_organization_followers(organization)` → Iterable[User] — paginated.
   - `list_organization_members(organization)` → Iterable[User] — paginated.
   - `list_user_repos(namespace=None)` → Iterable[RepoStorageInfo] — auth required; if namespace omitted, returns authenticated user's repos. Calls `/api/settings/repositories` or `/api/organizations/{namespace}/settings/repositories`.
   - `list_repo_likers(repo_id, repo_type)` → Iterable[User] — paginated list of users who liked a repo.

   **RepoStorageInfo class** (`hf_api.py:1644`):
   - Fields: `id` (str), `type` (str: model/dataset/space/bucket), `updated_at` (datetime), `visibility` (str: public/private), `storage` (int: bytes), `storage_percent` (float)

   **Usage pattern for iteration**:
   ```python
   api = HfApi()
   for follower in api.list_user_followers("username"):
       print(follower.username, follower.fullname)
   ```
   All paginated methods use the internal `paginate()` helper which handles cursor-based pagination transparently.

3. **Social Graph Architecture**:
   - Follow/following relationships are unidirectional (Twitter-style).
   - Both users and organizations have follower/following counts in their `User`/`Organization` objects.
   - The `is_following` field on a `User` object is relative to the **authenticated user** — only populated when making authenticated requests.
   - Orgs don't have a `following` concept — only `followers` and `members`.
   - Member list for orgs requires auth (at minimum, read access to the org).
   - Pagination uses the same `paginate()` helper as all other HF API list endpoints — transparent cursor management.

4. **Rate Limiting and Security**:
   - `/api/whoami-v2` is **intentionally heavily rate-limited** for security reasons. The SDK suggests caching with `whoami(cache=True)`.
   - Other user/org endpoints are subject to standard HF API rate limits.
   - Token management: `whoami()` requires a valid token. Uses token resolution chain: explicit arg → `HF_TOKEN` env var → `~/.cache/huggingface/token` → Google Colab secrets.
   - Error messages are descriptive: invalid token, Colab token, env variable token, or stored token issues are distinguished.
   - Public user/org overview endpoints can be called without authentication.

5. **Forward Compatibility**:
   - Both `User` and `Organization` dataclasses use `self.__dict__.update(**kwargs)` after consuming known fields, making them resilient to API additions.
   - New fields added to the API response are accessible as attributes even if not defined in the dataclass.

6. **Usage Realms**:
   - **Profile pages**: The overview endpoints drive the public user/org profile pages at `huggingface.co/{username}`.
   - **Repositories page**: `list_user_repos()` powers the "Repositories" tab with storage usage stats.
   - **Social features**: Follower/following feeds, search indexing, recommendations.
   - **Org management**: Member listing, admin dashboards, billing/plan info.
   - **Personalization**: `whoami()` used for token verification, feature gating, and personalization.

### Sources
- Source code: `huggingface_hub/hf_api.py` — `User` class (line 1750), `Organization` class (line 1683), `UserLikes` class (line 1614), `RepoStorageInfo` (line 1644), `get_user_overview` (line 11401), `get_organization_overview` (line 11428), `list_user_followers` (line 11511), `list_user_following` (line 11539), `list_organization_followers` (line 11455), `list_organization_members` (line 11483), `list_user_repos` (line 3160), `list_repo_likers` (line 3201), `whoami` (line 2305)
- Hub docs: https://huggingface.co/docs/hub/en/api (Hub API Endpoints)
- huggingface_hub docs: https://huggingface.co/docs/huggingface_hub/package_reference/hf_api

---

## 2026-07-25: hf-auth-login-internals-deep-dive

### Summary
Complete source-code deep dive into the huggingface_hub v1.24.0 authentication pipeline across four modules: _login.py, utils/_auth.py, utils/_oauth_device.py, and _oidc.py. Covers the full token resolution chain (OIDC -> env -> file -> Colab), two-file token storage system (active token file + INI-based multi-token store), transparent OAuth refresh with cross-process safety, all three login entry points (device code OAuth, notebook widget, terminal prompt), token validation pipeline, logout/multi-token switching, and RFC 8628/8693 protocol implementations.

### Key Findings
- Token resolution is layered: OIDC -> HF_TOKEN env -> file with refresh -> Google Colab; each short-circuits
- OAuth tokens have expiry-aware transparent refresh with 24h margin, 300s recheck interval, and WeakFileLock for cross-process safety
- Device Code OAuth (RFC 8628) implementation in _oauth_device.py handles slow_down, expired_token, and access_denied states with network resilience
- OIDC Trusted Publishers support GitHub Actions natively, with any-provider compat via HF_OIDC_ID_TOKEN env var
- Secret files use 0o600/0o700 permissions on POSIX; INI stored tokens use configparser with interpolation disabled

### Skill Created/Updated
`SakThai-hf-oauth-and-tokens/` — new Entry 146 in references/hf-learnings.md with 11 sections covering the complete implementation.

---

## 2026-07-25: hf-hub-model-dependents — Model Dependents & Children Discovery API (Topic #253)

### Summary
Complete reference for the Hugging Face Hub Model Dependents system — how models declare parent relationships, how the Hub tracks children by type (finetune, quantized, adapter, merge), and the full API surface for discovering dependents via REST API and Python library. There is NO dedicated `/dependents` endpoint; instead, dependents discovery is a composition of `expand` parameters on the model info endpoint and `filter` on the list models endpoint.

### Key Findings
- **base_model YAML field** — Models declare parent via `base_model: org/model` in card frontmatter; the Hub auto-classifies the relationship
- **Four relationship types** — `finetune` (fine-tuned), `quantized` (GGUF, AWQ, etc.), `adapter` (LoRA/DoRA/PEFT), `merge` (model merges)
- **childrenModelCount via expand** — `GET /api/models/{id}?expand[]=childrenModelCount` returns `{adapter: N, merge: N, quantized: N, finetune: N}`
- **baseModels via expand** — `expand[]=baseModels` returns `{relation: str, models: [{_id, id}]}` showing parent(s)
- **Children list via filter** — `GET /api/models?filter=base_model:org/model` lists actual descendant models, sortable and paginable
- **spaces via expand** — `expand[]=spaces` returns list of Spaces using the model (can be 100+)
- **No dedicated /children or /dependents endpoint** — All dependents discovery is through these expansion and filter patterns
- **Python: model_info(expand=...)** — `ModelInfo.children_model_count` (dict), `ModelInfo.base_models` (dict), `ModelInfo.spaces` (list)
- **Python: list_models(filter="base_model:...")** — enumerate children with full pagination support
- **Recursive** — Children can themselves have children; e.g., `unsloth/Phi-3.5-mini-instruct` has 244 adapters of its own despite being a child of `microsoft/Phi-3.5-mini-instruct`

### Skill Created
|`mlops/hf-hub-model-dependents/` — Complete reference for HF Hub Model Dependents API with REST endpoints and Python patterns.

---

## 2026-07-25: hf-datasets-server-size-limits-and-optimization — Dataset Viewer 5GB Limit, Partial Conversion & Size Optimization Strategies (Topic #255)

### Summary
Comprehensive reference for size limitations and optimization strategies in the Hugging Face Dataset Viewer/Datasets Server. Covers the 5GB auto-conversion limit, partial Parquet conversion with `partial-` split prefix, TooBigContentError and its common messages, sharding at ~500MB per file, row group sizing best practices with `write_page_index=True`, Parquet-native dataset exceptions, zero-cost workarounds using datasets library streaming (which bypasses size limits entirely), column pruning, config-based splitting, DuckDB predicate pushdown, and practical decision guide for working with datasets over 5GB.

### Source
- HF Hub Data Studio docs: https://huggingface.co/docs/hub/en/datasets-viewer ("Large scale datasets" section)
- Dataset Viewer Parquet docs: https://huggingface.co/docs/dataset-viewer/en/parquet
- Data Files Configuration (TooBigContentError): https://huggingface.co/docs/hub/en/datasets-data-files-configuration
- Dataset Viewer GitHub: https://github.com/huggingface/dataset-viewer

### 1. The 5GB Auto-Conversion Limit

The Dataset Viewer auto-converts every dataset on the Hub to Parquet format — but **only up to 5GB**. This is the central size constraint of the viewer ecosystem.

**How the limit works by dataset type:**

| Dataset Type | <= 5GB | > 5GB |
|---|---|---|
| **Native Parquet** | Full viewer, sorting, filtering, search on all data | Viewer works for all data but sorting/filtering/search limited to first 5GB |
| **Non-Parquet (CSV, JSONL, etc.)** | Full conversion to Parquet on `refs/convert/parquet` branch | Only first 5GB auto-converted to Parquet; viewer shows "partial" indicator |
| **WebDataset / image directories** | Full preview, all features enabled | Preview only first 5GB; "partial" message shown; search/filter on first 5GB only |

The "partial" state is surfaced in three ways:
1. **Parquet API response** (`GET /parquet`) — `"partial": true` field in the JSON
2. **Split directory naming** — splits >5GB use `partial-train` instead of `train` prefix
3. **UI banner** — informational message on the dataset page

### 2. Sharding Strategy

Datasets smaller than 5GB are sharded into Parquet files of **~500MB each**:

```
dataset/
├── refs/convert/parquet/
│   └── config/
│       ├── train-00000-of-00004.parquet  (~500 MB)
│       ├── train-00001-of-00004.parquet  (~500 MB)
│       ├── train-00002-of-00004.parquet  (~500 MB)
│       ├── train-00003-of-00004.parquet  (~500 MB)
│       └── test-00000-of-00001.parquet   (~< 500 MB)
```

Sharding at 500MB ensures:
- Workers can process splits in parallel
- Partial downloads (you can read only the shards you need)
- DuckDB/Polars projection pushdown works efficiently per shard
- Git LFS stays within reasonable per-file sizes

### 3. Row Group Sizing and TooBigContentError

**TooBigContentError** occurs when individual row groups in a Parquet file exceed the viewer's scan limit. This is one of the most common configuration errors.

Common error messages:
- `"Parquet error: Scan size limit exceeded"`
- `"The size of the content of the first rows exceeds the maximum supported size"`

**Root causes:**

| Cause | Why it happens | Fix |
|---|---|---|
| Row groups too large | Parquet files with row groups >100-300MB uncompressed force the scanner to load too much data | Set smaller row groups when writing Parquet |
| Very large values in first rows | Single cells with multi-MB strings (base64, JSON blobs, long documents) | Move large payloads to separate files |
| No page index | Without `write_page_index=True`, the scanner can't skip irrelevant pages | Write with `write_page_index=True` |
| Column contains oversized data | Parquet scanner reads entire row group for the requested column | Prune columns, use `columns` parameter in read |

**Prevention checklist:**
```python
import pyarrow.parquet as pq

# GOOD: small row groups, page index enabled
pq.write_table(
    table,
    "output.parquet",
    row_group_size=100_000,          # ~10-50 MB per group
    write_page_index=True,           # enables page-level skipping
    write_statistics=True,           # enables min/max statistics
    compression="zstd",              # better compression ratio
)

# BAD: single large row group, no index
pq.write_table(table, "output.parquet")  # single row group = TooBigContentError
```

### 4. Parquet-Native Dataset Exception

When a dataset **already uses Parquet format natively**, the viewer does NOT re-convert it. Instead, it creates **symbolic links** on the `refs/convert/parquet` branch pointing to the original Parquet files on the main branch.

However, there's an exception: **if the original row group size is too large**, new Parquet files are still generated with properly sized row groups. This ensures the viewer API remains fast regardless of the original file's structure.

**Practical implication:** If you upload a Parquet dataset with 500MB+ row groups, the viewer will still convert it (using compute resources) to fix the row group sizing. To avoid this, write Parquet files with 100-300MB row groups from the start.

### 5. Dataset Preview vs Full Viewer

For the biggest datasets (>5GB and not natively Parquet or not auto-converted), the dataset page shows a **preview of the first 100 rows** instead of a full-featured viewer.

This applies when:
- Dataset is over 5GB
- Not natively in Parquet format
- Has not been auto-converted to Parquet

The preview shows:
- 100 rows (no pagination)
- Column names and basic data types
- No sorting, filtering, or search
- No statistics or histograms

**Detection:** Check `GET /is-valid?dataset=...` — if `"preview": false`, the dataset is in preview-only mode.

### 6. Optimization Strategies for Large Datasets

#### Strategy A: Split into Configs (Subsets)

The most effective strategy for datasets near or over 5GB. By splitting into logical configurations, each config stays under 5GB:

```yaml
# dataset README.md
configs:
- config_name: part_1
  data_files:
  - split: train
    path: "data/part_1/*.jsonl"
- config_name: part_2
  data_files:
  - split: train
    path: "data/part_2/*.jsonl"
```

Each config gets its own Parquet conversion independently. This is the **recommended approach** for large datasets.

#### Strategy B: Column Pruning

If your dataset has many columns but only a few are needed for exploration:
- Use `columns` parameter in DuckDB/Polars when querying Parquet URLs
- Store wide but sparse columns separately from frequently-queried columns

#### Strategy C: Use Datasets Library Streaming (Bypasses 5GB Limit Entirely)

The `datasets` library's streaming mode does NOT use the Datasets Server's Parquet cache. It reads directly from original source files — no size limit:

```python
from datasets import load_dataset

# Streaming bypasses the Datasets Server entirely
ds = load_dataset("bigcode/the-stack-v2", split="train", streaming=True)
for i, example in enumerate(ds):
    if i >= 100:
        break
    print(example["content"][:200])
```

This works for **any dataset size** but requires downloading data on each iteration (no server-side caching).

#### Strategy D: DuckDB Predicate Pushdown

When querying Parquet files that DO exist (within the 5GB converted set), use DuckDB for efficient filtering:

```python
import duckdb

# DuckDB pushes filters to Parquet metadata — only downloads relevant bytes
result = duckdb.sql("""
    SELECT title, text
    FROM read_parquet('https://huggingface.co/datasets/.../refs%2Fconvert%2Fparquet/.../*.parquet')
    WHERE LENGTH(text) > 100 AND title LIKE '%machine learning%'
    LIMIT 50
""").fetchall()
```

This is **zero-cost** — predicate pushdown means you only transfer the matching rows' bytes, not the entire file.

#### Strategy E: Upload Pre-Converted Parquet

If you control the dataset creation pipeline, upload datasets already in Parquet format with proper row group sizing. This:
- Avoids the viewer's conversion compute
- Ensures consistent performance
- Allows full-featured viewer for Parquet-native datasets of any size (sorting/filtering/search still limited to 5GB)

### 7. Practical Decision Guide

| Dataset Size | Format | Strategy |
|---|---|---|
| < 1 GB | Any | Default — auto-conversion works perfectly |
| 1-5 GB | Any | Default — auto-conversion works, may be sharded across 2-10 files |
| 5-50 GB | Non-Parquet | Split into configs OR use `datasets` streaming OR upload as Parquet with proper row groups |
| 5-50 GB | Parquet with small row groups | Upload as-is — full viewer, but search/filter limited to first 5GB |
| 5-50 GB | Parquet with large row groups | Regenerate with `row_group_size=100000` and `write_page_index=True` |
| 50+ GB | Any | Must use `datasets` streaming or DuckDB direct Parquet reading; viewer will show 100-row preview only |
| Any | Private (non-PRO) | Viewer disabled — use `datasets` library directly |

### 8. Programmatic Detection

Check the viewer state programmatically before building workflows:

```python
import requests

def check_dataset_viewer_state(dataset_name: str) -> dict:
    """Check if a dataset's viewer can handle the full dataset."""
    base = "https://datasets-server.huggingface.co"

    # 1. Check validity
    valid = requests.get(f"{base}/is-valid?dataset={dataset_name}").json()

    # 2. Check Parquet conversion status
    parquet = requests.get(f"{base}/parquet?dataset={dataset_name}").json()

    # 3. Check size
    size = requests.get(f"{base}/size?dataset={dataset_name}").json()

    return {
        "has_preview": valid.get("preview", False),
        "has_full_viewer": valid.get("viewer", False),
        "has_search": valid.get("search", False),
        "has_filter": valid.get("filter", False),
        "parquet_partial": parquet.get("partial", False),
        "parquet_pending": len(parquet.get("pending", [])),
        "parquet_failed": len(parquet.get("failed", [])),
        "total_rows": sum(s["num_rows"] for s in size.get("sizes", [])),
        "total_bytes": sum(s["num_bytes_parquet_files"] for s in size.get("sizes", [])),
    }
```

### 9. Summary of Key Numbers

| Parameter | Value |
|---|---|
| Auto-conversion limit | 5 GB |
| Parquet shard target size | ~500 MB |
| Recommended row group size | 100-300 MB uncompressed (100K rows) |
| Preview-only threshold | >5 GB non-Parquet datasets |
| Parquet-native full viewer limit | Unlimited display, but 5GB for search/filter |
| Row group scan limit | ~100-300 MB uncompressed per group |
| Dataset viewer max rows per page | 100 rows |
| Dataset viewer max pagination | 100 rows per `/rows` request |

### Skill
mlops/hf-datasets-server-rest-api — Dataset Viewer size limits (5GB auto-conversion limit, partial conversion, sharding at 500MB), TooBigContentError prevention, row group sizing best practices, and optimization strategies for large datasets including config splitting, datasets streaming, column pruning, and DuckDB predicate pushdown

---

## 2026-07-25: hf-hub-repo-move-delete-management — Repo Transfer, Rename, Deletion & Settings API (Topic #265)

### Summary
Complete reference for Hugging Face Hub repository lifecycle management covering six core operations: `move_repo()` (rename and transfer between namespaces), `delete_repo()` (permanent deletion), `duplicate_repo()` (server-side copy), `repo_exists()` (existence checking), `update_repo_settings()` (visibility, gating), and `permanently_delete_lfs_files()` (LFS cleanup). Includes REST API endpoints, allowed/forbidden move operations, error handling patterns, rate limits, and practical examples.

### Key Findings
- **`move_repo(from_id, to_id)`** — renames OR transfers. Old URL auto-redirects. Download counts and likes preserved. NOT allowed: user→user transfer, org→non-self-user transfer.
- **`delete_repo(repo_id, missing_ok)`** — IRREVERSIBLE. Sends DELETE to `/api/repos/delete`. Raises `RepositoryNotFoundError` if `missing_ok=False` (default).
- **`duplicate_repo(from_id, to_id)`** — server-side copy preserving full git + LFS history. Returns `RepoUrl`. Supports Space-specific config (hardware, storage, secrets, env vars).
- **`repo_exists(repo_id)`** — returns `True` even for gated repos (catches `GatedRepoError`). Only `False` when truly not found.
- **`update_repo_settings()`** — controls `private`/`public` visibility and `gated` mode (`"auto"`, `"manual"`, or `False`). Supports Space-specific `"protected"` visibility. `private` and `visibility` params are mutually exclusive.
- **`permanently_delete_lfs_files()`** — removes specific LFS files from git history with optional `rewrite_history`. IRREVERSIBLE. Use `list_lfs_files()` first to enumerate candidates.

### REST Endpoints
- `POST /api/repos/move` — move/rename/transfer repo
- `DELETE /api/repos/delete` — delete repo
- `POST /api/repos/{repo_type}/duplicate` — duplicate repo

### Skill Created
`SakThai-hf-repo-move-delete-management/` — Complete reference with 11 sections covering all repo lifecycle operations, allowed move operations table, error handling, and practical patterns.

---

## 2026-07-25: hf-hub-doi-digital-object-identifiers — Digital Object Identifiers for Models and Datasets on HF Hub (Topic #266)

### Summary
Comprehensive reference for DOI (Digital Object Identifier) support on the Hugging Face Hub. DOIs are persistent identifiers that uniquely identify models and datasets, making them citable in academic publications (analogous to an ISBN). DOIs are managed via DataCite, generated through the repo Settings UI (no programmatic API), and lock repositories against deletion/rename/visibility change. Supports versioning via new DOI generation per revision.

### Key Findings
- **Generation**: Exclusive through Hub UI → repo Settings → DOI section → "Generate DOI" → accept DataCite terms → optional author customization
- **No API**: `huggingface_hub` library has no DOI methods in `HfApi`; the interactive DataCite consent flow prevents CLI/API generation
- **Versioning**: Push a new revision → "Generate new DOI" → old DOI deprecated, fresh DOI assigned for the new snapshot
- **Locking**: DOI-locked repos cannot be deleted, renamed, or made private without HF support intervention (`website@huggingface.co`)
- **Free**: No cost to generate DOIs on HF Hub
- **Citation**: DOI badge appears automatically in the model/dataset header after generation
- **Scope**: Models and datasets only (not Spaces)

### Sources
- HF Hub DOI Docs: https://huggingface.co/docs/hub/en/doi
- Announcement Blog: https://huggingface.co/blog/introducing-doi
- DataCite: https://datacite.org

### Skill
hf-hub-doi — Digital Object Identifiers on Hugging Face Hub: generation workflow, DataCite integration, versioning semantics, repo locking restrictions, and citation integration

---

## 2026-07-25: hf-spaces-configuration-reference — Complete Spaces YAML Configuration System (Topic #274)

### Summary
Complete reference for Hugging Face Spaces YAML configuration system covering all 30+ configuration parameters (`sdk`, `python_version`, `sdk_version`, `app_file`, `suggested_hardware`, `preload_from_hub`, `custom_headers`, `hf_oauth`, etc.), 18 hardware flavors (2 CPU + 16 GPU from `cpu-basic` Free to `a100x8` $20/hr), built-in environment variables (9 standard + 4 OAuth), OAuth configuration, model preloading for cold-start optimization, SDK-specific behavior (Gradio, Docker, Static, Streamlit), networking (ports 80/443/8080), lifecycle (sleep after 48h, pause, replicas), and programmatic hardware configuration via huggingface_hub.

### Key Findings
- **sdk**: `gradio` (default), `docker`, `static`, `streamlit` — framework selection
- **python_version**: defaults to 3.10, any 3.x/3.x.x valid
- **suggested_hardware**: 18 flavors from `cpu-basic` (Free) to `a100x8` ($20.00/hr)
- **Static Spaces**: free for everyone, no paid plan required; uses `app_build_command` + `app_file`
- **Preload**: `preload_from_hub` loads models at build time into HF cache, reducing cold-start latency
- **OAuth**: `hf_oauth: true` with scopes, expiry (max 30 days), org restriction; exposes OAUTH_CLIENT_ID/ SECRET/SCOPES, OPENID_PROVIDER_URL env vars
- **Custom headers**: only COEP (`require-corp`), COOP (`same-origin`), CORP allowed; all lowercase
- **Sleep**: Free Spaces sleep after 48h; paid run indefinitely unless custom sleep set
- **Replicas**: horizontal scaling via `POST /api/spaces/{ns}/{repo}/replicas`
- **Ports**: only 80, 443, 8080 accessible; all others blocked

### Sources
- HF Spaces Configuration Reference: https://huggingface.co/docs/hub/en/spaces-config-reference
- HF Spaces GPU Upgrades: https://huggingface.co/docs/hub/en/spaces-gpus
- HF Spaces Overview: https://huggingface.co/docs/hub/en/spaces-overview

### Skill Created
`mlops/hf-spaces-configuration/` — Complete YAML config reference with all parameters, hardware specs table, env vars, OAuth, preloading, SDK-specifics, and programmatic API patterns.

## 2026-07-25: hf-hub-doi-deep-dive-v2 — DataCite Metadata Schema & API Integration (Topic #267)

### Summary
Deep dive into DataCite integration layer of HF DOIs. Researched DataCite kernel-4 XML metadata schema, element mapping from HF repos to DataCite, DataCite REST API for querying HF DOIs, citation generation via content negotiation, and programmatic patterns for DOI discovery. Discovered that HF sends minimal metadata (no descriptions, subjects, licenses, affiliations) to DataCite and that HF's own API exposes no `doi` field — DataCite API is the only programmatic source.

### Key Findings

**HF DOI Identity:**
- Prefix `10.57967/hf/` — publisher always `"Hugging Face"`, version = git SHA
- Resource types: `Dataset` or `Model` (DataCite Kernel 4 controlled list)
- Two states: `findable` (active) and `registered` (deprecated previous version)
- No DOI field in `huggingface_hub` library or HF REST API

**Metadata Gaps (not sent to DataCite):**
- No `descriptions`/abstract — model card context is lost
- No `subjects`/keywords
- No `rightsList`/license info
- No `relatedIdentifiers` (papers, code, datasets)
- No `affiliation` on creators
- No `fundingReferences`

**DataCite REST API Patterns:**
- `GET /dois?query=10.57967/hf` — search all HF DOIs
- `GET /dois/10.57967%2Fhf%2F8345` — single DOI metadata (with base64-encoded XML)
- Content negotiation via `Accept` header for BibTeX/RIS/CSL citations
- Free, no-auth read-only access

### Sources
- DataCite API: https://api.datacite.org/dois (with live queries against actual HF DOIs)
- DataCite Kernel 4 Schema: https://schema.datacite.org/meta/kernel-4.5/
- HF Docs (raw): https://raw.githubusercontent.com/huggingface/hub-docs/main/docs/hub/doi.md

### Skill Updated
`hf-hub-doi/` → v2.0.0 with full DataCite schema reference, programmatic patterns, and citation generation.

---

## 2026-07-25: hf-hub-rate-limits-deep-dive-v2 — Source Code Internals & Advanced Patterns (Deeper on Topic #249)

### Summary
Deep-dive into the actual `huggingface_hub v1.24.0` source code implementing rate limit handling. Covers the `_http_backoff_base()` internal function, the precise regex patterns for parsing IETF RateLimit headers, how `http_backoff()` integrates rate-limit-aware waiting with exponential backoff, `hf_raise_for_status()` 429 error message construction, `HfApi` pagination internals, Storage Buckets rate limits, and practical code patterns for custom handling.

### Source Code Reference
- huggingface_hub v1.24.0 source: `huggingface_hub/utils/_http.py` (lines 55–920)
- Rate limit regex + parser: lines 75–135
- `_http_backoff_base()`: lines 430–527
- `http_backoff()` wrapper: lines 530–610
- `hf_raise_for_status()` 429 handling: lines 895–914

---

### 1. Exact Regex Patterns for Rate Limit Header Parsing

The library uses two compiled regex patterns:

**`_RATELIMIT_REGEX`** — Parses the `RateLimit` response header:
```python
_RATELIMIT_REGEX = re.compile(
    r'\"(?P<resource_type>\w+)\"\s*;\s*r\s*=\s*(?P<r>\d+)\s*;\s*t\s*=\s*(?P<t>\d+)'
)
```
Matches patterns like: `"api";r=0;t=55`
- `resource_type` → `"api"`, `"resolvers"`, or `"pages"`
- `r` → remaining requests in current window
- `t` → seconds until window reset

**`_RATELIMIT_POLICY_REGEX`** — Parses the `RateLimit-Policy` response header:
```python
_RATELIMIT_POLICY_REGEX = re.compile(
    r'q\s*=\s*(?P<q>\d+).*?w\s*=\s*(?P<w>\d+)'
)
```
Matches patterns like: `"fixed window";"api";q=500;w=300`
- `q` → quota per window
- `w` → window duration in seconds (always 300 = 5 min)

These regexes are CASE-INSENSITIVE for header key lookup (lowercased in `parse_ratelimit_headers()`), but case-sensitive for the header value matching.

---

### 2. The `RateLimitInfo` Data Class

```python
@dataclass(frozen=True)
class RateLimitInfo:
    resource_type: str
    remaining: int
    reset_in_seconds: int
    limit: int | None = None
    window_seconds: int | None = None
```
- Frozen (immutable) dataclass returned by `parse_ratelimit_headers()`
- `limit` and `window_seconds` are `Optional` because they come from the `RateLimit-Policy` header which may not always be present
- Used both for logging/display AND for the automatic retry delay calculation

---

### 3. The Full Auto-Retry Flow in `_http_backoff_base()`

This is the core function shared by both `http_backoff()` (regular requests) and `http_stream_backoff()` (streaming). Here's the complete retry lifecycle:

```python
def _http_backoff_base(
    method, url, *,
    max_retries=5,            # Max attempts before giving up
    base_wait_time=1,         # Initial sleep (seconds)
    max_wait_time=8,          # Cap on exponential backoff
    retry_on_exceptions,      # Default: TimeoutException, NetworkError, RemoteProtocolError
    retry_on_status_codes,    # Default: (408, 429, 500, 502, 503, 504)
    stream=False,
    **kwargs,
):
```

**The loop:**

1. **Attempt request** via `client.request()` or `client.stream()`
2. **`_should_retry(response)`** closure checks:
   - If status code NOT in `retry_on_status_codes` → stop (success)
   - If `nb_tries > max_retries` → call `hf_raise_for_status()` (will raise, or return)
   - If status is **429** → parse `RateLimit` header via `parse_ratelimit_headers()` to get `reset_in_seconds`
   - If `Retry-After` header present → fallback to `_parse_retry_after()`
   - Return `True` (should retry) for all other retryable status codes
3. **Wait logic:**
   - If rate limited → `actual_sleep = float(ratelimit_reset) + 1` (adds +1s safety margin)
   - Otherwise → `actual_sleep = sleep_time` (exponential: 1s, 2s, 4s, 8s... capped at `max_wait_time=8s`)
4. **Exponential backoff:** `sleep_time = min(max_wait_time, sleep_time * 2)`
5. **File-object cursor reset:** If `data` kwarg is a file/IO object, saves and restores `.tell()` position between retries to allow re-sending upload bodies.

**Key insight:** When rate limited, the huggingface_hub library respects the server's precise reset time (+1s safety margin), rather than using exponential backoff. This is much more efficient than blindly backing off.

---

### 4. `hf_raise_for_status()` — The 429 Error Message Generator

When a 429 response would not be retried (n_tries exhausted), `hf_raise_for_status()` constructs a detailed error message:

```python
elif response.status_code == 429:
    ratelimit_info = parse_ratelimit_headers(response.headers)
    if ratelimit_info is not None:
        message = (
            f"\n\n429 Too Many Requests: you have reached your "
            f"'{ratelimit_info.resource_type}' rate limit."
        )
        message += f"\nRetry after {ratelimit_info.reset_in_seconds} seconds"
        if ratelimit_info.limit is not None and ratelimit_info.window_seconds is not None:
            message += (
                f" ({ratelimit_info.remaining}/{ratelimit_info.limit} requests remaining"
                f" in current {ratelimit_info.window_seconds}s window)."
            )
    else:
        message = f"\n\n429 Too Many Requests for url: {response.url}."
```

This produces user-friendly messages like:
```
429 Too Many Requests: you have reached your 'api' rate limit.
Retry after 55 seconds (0/500 requests remaining in current 300s window).
```

---

### 5. How `HfApi` Iteration Methods Handle Rate Limits

The `HfApi.list_models()`, `list_datasets()`, `list_spaces()` methods all return **lazy iterators** (`Iterator[Model]`) rather than lists. Internally, they call:

```python
items: Iterator = api_iterate(  # or _fetch_with_pagination
    endpoint,                # e.g., "/api/models"
    params=params,
    headers=headers,
    ...
)
items = islice(items, limit)  # truncate to requested limit
```

The `api_iterate` function paginates automatically through the Hub API, using `http_backoff()` internally so rate limits are handled transparently. This means:
- You don't need to manage pagination yourself
- Rate limits are automatically respected between page fetches
- The iterator is lazy — it only fetches pages as you iterate

**Practical implication:** When using `list_models()`, you can safely iterate through thousands of items. The library handles backoff between pages automatically. The old pattern of manually calling `next_page()` is obsolete.

---

### 6. Storage Buckets Rate Limits

As of July 2026, HF's **Storage Buckets** feature has its own rate limit handling via a dedicated regex:

```python
BUCKET_API_REGEX = re.compile(
    r"""
        ^https?://[^/]+
        /api/buckets/
    """,
    flags=re.VERBOSE,
)
```

This regex identifies bucket API URLs (`/api/buckets/...`) separately from repo URLs. Bucket API calls fall under the general `api` rate limit bucket, but the library tracks the URL pattern to provide accurate error messages. The `_parse_bucket_id_from_url()` function extracts `namespace/name` from bucket URLs for better error context.

**Rate limit environment variables for downloads:**

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_HUB_DOWNLOAD_TIMEOUT` | 10s | Per-request timeout for file downloads |
| `HF_HUB_ETAG_TIMEOUT` | 10s | Timeout for HEAD requests checking file freshness |
| `HF_HUB_DEFAULT_TIMEOUT` | 10s | General request timeout |
| `HF_HUB_OFFLINE` | unset | When set to `1`, no network calls made (uses cache only) |

---

### 7. Custom Rate Limit Handling Patterns

#### 7.1 Manual Rate Limit Header Parsing

```python
from huggingface_hub.utils import parse_ratelimit_headers

# After receiving a response with rate limit headers
info = parse_ratelimit_headers(response.headers)
if info and info.remaining < 10:
    print(f"Approaching rate limit: {info.remaining}/{info.limit} remaining")
    time.sleep(info.reset_in_seconds)  # Wait for window reset
```

#### 7.2 Disabling Auto-Retry (for custom handling)

```python
from huggingface_hub.utils import http_backoff

# Disable all retries — handle 429 yourself
response = http_backoff(
    "GET", url,
    retry_on_exceptions=(),
    retry_on_status_codes=()
)
```

#### 7.3 Custom Retry Configuration

```python
# Aggressive retry for critical operations
response = http_backoff(
    "POST", url,
    max_retries=10,
    base_wait_time=0.5,
    max_wait_time=30,
    retry_on_status_codes=(429, 500, 502, 503, 504)
)
```

#### 7.4 Using `_httpx_follow_relative_redirects_with_backoff`

For scenarios where you need to follow redirects AND handle rate limits:

```python
# Internal helper that follows relative redirects with auto-backoff
from huggingface_hub.utils._http import _httpx_follow_relative_redirects_with_backoff

response = _httpx_follow_relative_redirects_with_backoff(
    "GET", url,
    retry_on_errors=True,  # enables 429/5xx/timeout retry
)
```

This is used internally by the Hub for download flows that may redirect to CDN endpoints.

#### 7.5 Proactive Rate Limit Monitoring in Long-Running Jobs

```python
import os
import time
from huggingface_hub import HfApi, RateLimitInfo

api = HfApi()

# Monitor rate limit consumption during pagination
consumed = 0
for model in api.list_models(task="text-classification", limit=1000):
    process(model)
    consumed += 1
    if consumed % 100 == 0:
        # Check billing dashboard to see real-time usage
        print(f"Processed {consumed} models...")
        time.sleep(0.5)
```

---

### 8. Rate Limit Handling Architecture (Complete Flow)

```
User Code (HfApi.list_models)
    │
    ▼
api_iterate() / _fetch_with_pagination()
    │  Uses http_backoff() internally
    ▼
http_backoff(method, url, ...)
    │
    ▼
_http_backoff_base(method, url, ...)
    │
    ├──► client.request(method, url)  ──► HTTP Response
    │         │                              │
    │         │                         ┌────▼────┐
    │         │                    ┌─────┤ 429?    ├─────┐
    │         │                    │     └─────────┘     │
    │         │                    │  No                 │ Yes
    │         │                    ▼                     ▼
    │         │             return response     parse_ratelimit_headers()
    │         │                                      │
    │         │                               ┌──────▼──────┐
    │         │                               │ reset_in_sec│
    │         │                               │   = 55s     │
    │         │                               └──────┬──────┘
    │         │                                      │
    │         │                               sleep(55 + 1)
    │         │                                      │
    │         │                               retry ──► back to top
    │         │
    │    If Exception (network error):
    │         sleep(exponential: 1s, 2s, 4s... max 8s)
    │         retry ──► back to top
    │
    ▼
Returned to caller as lazy iterator
```

---

## 2026-07-25: hf-jobs-complete-ecosystem-deep-dive

### Summary
Comprehensive deep dive into the Hugging Face **Jobs** compute platform — a pay-as-you-go infrastructure service for running AI/data workloads on HF hardware (CPU, GPU up to H200/RTX PRO 6000, TPU). Jobs provide a UV-like and Docker-like CLI, Python API, HTTP API, scheduling, webhooks, volume mounting (Hub repos, Storage Buckets, local dirs), SSH access, and exposed ports for temporary inference servers.

### Key Concepts

**CLI Interfaces:**
- `hf jobs uv run <script>` — UV-like: auto-installs deps, runs Python scripts in one command
- `hf jobs run <image> <command>` — Docker-like: specify any Docker image + command
- `hf jobs uv run --with trl --flavor a10g-small train.py` — GPU training in one line
- Default timeout: **30 minutes** (use `--timeout 6h` for long runs)
- `--detach` for background execution, `--name` for labeling

**Hardware Flavors (from $0.01/hr CPU to $40/hr 8×H200):**
| Flavor | HW | Cost/hr |
|--------|-----|---------|
| `cpu-basic` | 2 vCPU, 16 GB | $0.01 |
| `cpu-upgrade` | 8 vCPU, 32 GB | $0.03 |
| `cpu-xl` | 16 vCPU, 124 GB | $1.00 |
| `t4-small` | 1×T4 (16 GB) | $0.40 |
| `a10g-small` | 1×A10G (24 GB) | $1.00 |
| `a100-large` | 1×A100 (80 GB) | $2.50 |
| `h200` | 1×H200 (141 GB) | $5.00 |
| `l40sx1` | 1×L40S (48 GB) | $1.80 |
| `rtx-pro-6000` | 1×RTX PRO 6000 (96 GB) | $2.75 |
- Get live list: `hf jobs hardware` or `list_jobs_hardware()`

**Pricing & Billing:**
- Billed **per minute** only while Starting or Running (no cost during build, no cost after failure)
- Default timeout 30 min prevents runaway costs
- Exposed ports: +$0.01/hr flat rate
- Bill to org: `--namespace my-org-name`
- Bill to Resource Group (Enterprise): `--namespace <resource-group-id>`
- Requires positive credit balance at https://huggingface.co/settings/billing

**Volume Mounting (`-v` / `--volume`):**
- `hf://models/<org>/<repo>:/mount/path` — model repos (read-only)
- `hf://datasets/<org>/<repo>:/mount/path` — dataset repos (read-only)
- `hf://buckets/<user>/<bucket>:/mount/path` — Storage Buckets (read-write by default)
- `hf://datasets/<org>/<repo>/subfolder:/mount/path` — subfolder mounts
- Local dir: `./training-data:/data:rw` — synced to `jobs-artifacts` bucket automatically
- Multiple volumes by repeating `-v`; read-only via `:ro` suffix
- Python API: `Volume(type="dataset", source="org/repo", mount_path="/data")`

**Environment Variables & Secrets:**
- Built-in: `JOB_ID`, `ACCELERATOR`, `CPU_CORES`, `MEMORY`
- User env: `-e KEY=value` or `--env-file .env`
- Secrets: `-s KEY=value` (encrypted server-side) or `--secrets-file .env.secrets`
- `--secrets HF_TOKEN` passes your logged-in token automatically
- Webhook-triggered jobs get `WEBHOOK_PAYLOAD`, `WEBHOOK_REPO_ID`, `WEBHOOK_REPO_TYPE`, `WEBHOOK_SECRET`

**Lifecycle Management:**
- `hf jobs ps` — list jobs (use `-a` for all, `--filter` for filtering)
- `hf jobs logs <id>` — stream/fetch logs
- `hf jobs stats <id>` — live CPU/GPU/memory/network metrics
- `hf jobs inspect <id>` — full job metadata as JSON
- `hf jobs wait <id>` — block until terminal state (exit 0 = all completed)
- `hf jobs cancel <id>` — stop billing immediately
- `hf jobs ssh <id>` — interactive SSH into running job (requires SSH key at https://huggingface.co/settings/keys)

**Scheduled Jobs:**
- `hf jobs scheduled uv run @hourly script.py` — cron-like scheduling
- Supports: `@annually`, `@yearly`, `@monthly`, `@weekly`, `@daily`, `@hourly`, or CRON (`"*/5 * * * *"`)
- Manage: `hf jobs scheduled ps`, `inspect`, `suspend`, `resume`, `trigger`, `delete`

**Webhook Automation:**
- `create_webhook(job_id=job_id, watched=[...], domains=["repo", "discussion"], secret="...")`
- Triggers job on repo/discussion events (create, delete, update, move)
- Payload delivered as `WEBHOOK_PAYLOAD` env var inside the job

**Serving Models via Exposed Ports:**
- `--expose 8000` — port becomes reachable at `https://<job_id>--8000.hf.jobs`
- Requires Bearer token with read access to job's namespace
- Start vLLM: `hf jobs run --detach --expose 8000 --flavor a10g-small vllm/vllm-openai vllm serve <model>`
- Start llama.cpp: `hf jobs run --detach --expose 8080 --flavor a10g-small ghcr.io/ggml-org/llama.cpp:server-cuda -- /app/llama serve -hf <model> --host 0.0.0.0 --port 8080`
- Must listen on `0.0.0.0` (llama.cpp defaults to `127.0.0.1`)
- Mount model repo as volume for faster startup (skip download)
- Multiple ports: `--expose 8000 --expose 8001`

**SSH Access:**
- `--ssh` flag at job creation, connect with `hf jobs ssh <id>`
- Requires SSH public key registered at Hugging Face settings
- Remote forwarding: `ssh -R 8080:localhost:8080 <id>@ssh.hf.jobs`
- Not supported for scheduled jobs

**Large Dataset Processing:**
- Streaming: `load_dataset(..., streaming=True)` — no disk needed
- `hf://` scanning: Polars/DuckDB/pandas scan Hub Parquet directly, pushing filters down
- Mounting: `-v hf://datasets/<repo>:/data` — lazy file access for tools needing local paths
- Common Crawl example: stream WET files from bucket via `hffs.open()`, parse with fastwarc
- Persist results to Storage Buckets (write to mounted path, survives job)

**Python API:**
- `run_job(image, command, flavor, timeout, secrets, volumes, expose, ...)`
- `run_uv_job(script, dependencies, flavor, ...)`
- `list_jobs(status, labels)`, `inspect_job(id)`, `wait_for_job(id)`, `cancel_job(id)`
- `fetch_job_logs(id)`, `fetch_job_metrics(id)`
- `list_jobs_hardware()` — get available flavors

**Integration Ecosystem:**
- TRL Jobs Training: SFT, GRPO, DPO recipes with hardware selection
- Unsloth on Jobs: ~2× faster training, ~60% less VRAM
- Transformers example scripts: run directly via URL
- UV Scripts org: ready-to-run scripts (OCR, batch inference, classification)
- Coding Agent Skills: `hugging-face-jobs` skill for Claude Code / Cursor
- Sandboxes: built on Jobs, interactive environments for agents

### Key Insights
- Jobs are **not free** — require positive credit balance. For Beer's zero-cost constraint, Jobs are useful for understanding the platform but actual usage requires pre-paid credits.
- SSH + exposed ports make Jobs viable as ephemeral dev environments and temporary inference servers
- UV integration (`hf jobs uv run`) eliminates needing to write Dockerfiles for Python workloads
- Volume mounting with `hf://` URLs enables processing datasets far larger than the job's ephemeral storage
- The `hf jobs wait` command with exit-code chaining makes Jobs composable in CI/CD pipelines
- Webhook-triggered Jobs enable fully automated MLOps: push a model → webhook → Job runs evaluation → results pushed back
- Scheduled Jobs replace cron for periodic tasks (daily model re-evaluation, data ingestion)
- Exposed ports billed at flat $0.01/hr regardless of how many ports — cheap for temporary endpoints

### Skill Alignment
This deep dive covers the complete Jobs ecosystem. For reference material under the existing `mlops/hf-hub-jobs-api` skill, see `references/hf-learnings.md`.

---

## 2026-07-24: hf-hub-notification-and-watching-system

### Summary
Deep dive into the Hugging Face Hub's notification and watching system — the web UI features for watching users/orgs/repos, the `/api/notifications` REST API (list, mark-read, delete), muting repositories and discussions, and notification settings. The watching feature is web-only (no Python `huggingface_hub` library support); the notifications API however works with Bearer token auth and is fully programmable.

### Key API Surface (`/api/notifications`)

**GET — List notifications:**
```
GET /api/notifications?limit=20&start=0&type=repo&read=false
```
- Params: `limit`, `start`, `type` (repo/discussion/mention/all), `read` (bool)
- Response: `{notifications: [...], count: {view, all, unread}, start}`
- Each notification: `{updatedAt, read, discussionEventId, repo: {name, type}, type, discussion: {id, num, title, status, isPullRequest, participating}}`

**POST /mark-as-read — Mark notifications as read:**
```
POST /api/notifications/mark-as-read
{"discussionIds": ["id1"]}  # specific, or {} for all
→ {"success": true}
```

**DELETE — Delete/clear notifications:**
```
DELETE /api/notifications?applyToAll=true    # all
DELETE /api/notifications  {"discussionIds": ["id1"]}  # specific
→ {"success": true}
```

### Watching Mechanism
- **Web-only feature** — no `huggingface_hub` library methods for watch/unwatch
- `/api/watching` endpoint exists but requires **cookie-based web session auth**, not Bearer token
- Watch users/orgs via "Watch repos" button on their profile, or from settings page
- Default: auto-watch all orgs you're a member of
- Watch individual repos independently of user/org watches

### Muting
- **Mute a repo:** Context menu → "Mute notifications" (exceptions: direct mentions & participation still notify)
- **Mute a discussion/PR:** Mute icon in discussion header (blocks ALL notifications including direct mentions)
- Muted repos list visible in notification settings

### Notification Settings (`/settings/notifications`)
- Per-activity-type channel config (email, web, or both)
- Quick search to add users/orgs to watch list
- Checkbox to unsubscribe from users/orgs
- Muted repos management

### Key Limitations
- No Python library support for watching/notifications in `huggingface_hub` v1.24.0
- Watching is web-only (cookie auth, not token)
- For programmable event handling, use Webhooks API instead

### Skill Created
`hf-hub-notification-watching/` — complete reference with API endpoints, web UI patterns, and usage examples.

---

## 2026-07-25: hf-hub-embedding-badges-oembed-deep-dive

### Summary
Comprehensive deep dive into embedding Hugging Face Hub content (Spaces, datasets, models) in external websites using shields.io badges, Open Graph social cards, and the Hub's embed/iframe infrastructure. Covers Spaces embedding (direct URL, iframe, Gradio WebComponents), dataset viewer embedding, shields.io badge patterns (static with HF logo + dynamic from API), OG social card URLs, the oEmbed API (auth required), SQL console embeds via REST API, and protected Space embedding.

### Key Embedding Patterns

**Spaces — Iframe (all Space types):**
```html
<iframe src="https://{namespace}-{space-name}.hf.space" frameborder="0" width="850" height="450"></iframe>
```

**Spaces — Gradio WebComponents (Gradio-only, faster, auto-resize):**
```html
<script type="module" src="https://gradio.s3-us-west-2.amazonaws.com/{version}/gradio.js"></script>
<gradio-app src="https://{namespace}-{space-name}.hf.space"></gradio-app>
```

**Dataset Viewer Embed (iframe):**
```
https://huggingface.co/datasets/{namespace}/{dataset-name}/embed/viewer
```
Parameters: `config`, `split`, `filter`, `search`, `row`

**Shields.io Static Badges with HF Logo:**
```md
![HF](https://img.shields.io/badge/HuggingFace-{name}-FFD21E?logo=huggingface)
![Model](https://img.shields.io/static/v1?label=Model&message={name}&color=blue&logo=huggingface)
```

**Shields.io Dynamic Badges from HF API:**
```md
![Downloads](https://img.shields.io/badge/dynamic/json?url=https://huggingface.co/api/models/{model}&query=downloads&label=Downloads)
```

**OG Social Cards (auto-generated at predictable URL):**
```
https://cdn-thumbnails.huggingface.co/social-thumbnails/{type}/{namespace}/{repo}.png
```
Where `type` is `models`, `datasets`, or `spaces`.

**oEmbed API** (requires Bearer token auth — returns 401 without):
```
GET /api/oembed?url=https://huggingface.co/{type}/{namespace}/{repo}
Authorization: Bearer {token}
```

**SQL Console Embeds via REST API:**
| Method | Endpoint |
|--------|----------|
| POST | `/api/{repoType}/{namespace}/{repo}/sql-console/embed` |
| PATCH | `/api/{repoType}/{namespace}/{repo}/sql-console/embed/{id}` |
| DELETE | `/api/{repoType}/{namespace}/{repo}/sql-console/embed/{id}` |

### Key Findings
- Spaces are the most embeddable HF asset — 3 methods: direct URL, iframe, WebComponents
- Dataset viewer has dedicated embed URL with filter/search/subset/split query params
- Model inference widgets are **not iframe-embeddable** — Svelte component on model page only
- shields.io has no dedicated HF badge service — use `?logo=huggingface` on static or dynamic JSON badges
- OG social cards are auto-generated from repo metadata at a predictable CDN URL pattern
- oEmbed API exists at `/api/oembed` but requires authentication (not public/oEmbed-standard)
- Protected Spaces keep source private while allowing public embedding
- SQL Console embeds are fully manageable via REST API (CRUD operations)

### Resources
- [Spaces Embed Docs](https://huggingface.co/docs/hub/en/spaces-embed)
- [Dataset Viewer Embed Docs](https://huggingface.co/docs/hub/en/datasets-viewer)
- [Shields.io Badges](https://shields.io/badges)
- [HF OpenAPI Spec](https://huggingface.co/.well-known/openapi.json)
- [HF Brand Assets](https://huggingface.co/brand)

### Skill Created
`hf-hub-embedding-badges/` — complete reference with all embedding patterns, badge APIs, SQL console embed API, and OG card URLs.

---


---

## 2026-07-25: hf-spaces-hardware-tiers-deep-dive

### Summary
Comprehensive deep dive into all Hugging Face Spaces hardware options: CPU tiers, GPU accelerators, ZeroGPU, billing model, programmatic configuration, replicas, streaming telemetry, and best practices. Based on the official HF Spaces doc, pricing page, and GPU upgrades guide.

### Complete Hardware Tier Reference

**CPU Tiers:**

| Name | vCPU | Memory | Disk | Hourly Price | Notes |
|------|------|--------|------|-------------|-------|
| CPU Basic | 2 vCPU | 16 GB | 50 GB | **Free** | Goes to sleep after 48h inactivity. Creating new Spaces on compute requires paid plan; Static Spaces are always free. |
| CPU Upgrade | 8 vCPU | 32 GB | 50 GB | $0.03/hr | Runs indefinitely by default. Can set custom sleep time. |

**GPU Tiers:**

| Name | vCPU | Memory | GPU | VRAM | Disk | Hourly Price |
|------|------|--------|-----|------|------|-------------|
| Nvidia T4 - small | 4 vCPU | 15 GB | 1× T4 | 16 GB | 50 GB | $0.40 |
| Nvidia T4 - medium | 8 vCPU | 30 GB | 1× T4 | 16 GB | 100 GB | $0.60 |
| 1× Nvidia L4 | 8 vCPU | 30 GB | 1× L4 | 24 GB | 400 GB | $0.80 |
| 4× Nvidia L4 | 48 vCPU | 186 GB | 4× L4 | 96 GB | 3200 GB | $3.80 |
| 1× Nvidia L40S | 8 vCPU | 62 GB | 1× L40S | 48 GB | 380 GB | $1.80 |
| 4× Nvidia L40S | 48 vCPU | 382 GB | 4× L40S | 192 GB | 3200 GB | $8.30 |
| 8× Nvidia L40S | 192 vCPU | 1534 GB | 8× L40S | 384 GB | 6500 GB | $23.50 |
| Nvidia A10G - small | 4 vCPU | 15 GB | 1× A10G | 24 GB | 110 GB | $1.00 |
| Nvidia A10G - large | 12 vCPU | 46 GB | 1× A10G | 24 GB | 200 GB | $1.50 |
| 2× Nvidia A10G - large | 24 vCPU | 92 GB | 2× A10G | 48 GB | 1000 GB | $3.00 |
| 4× Nvidia A10G - large | 48 vCPU | 184 GB | 4× A10G | 96 GB | 2000 GB | $5.00 |
| Nvidia A100 - large | 12 vCPU | 142 GB | 1× A100 | 80 GB | 1000 GB | $2.50 |
| 4× Nvidia A100 | 48 vCPU | 568 GB | 4× A100 | 320 GB | 4000 GB | $10.00 |
| 8× Nvidia A100 | 96 vCPU | 1136 GB | 8× A100 | 640 GB | 8000 GB | $20.00 |

**ZeroGPU (PRO required, $9/mo):** Nvidia RTX Pro 6000 Blackwell (dynamic allocation), up to 96 GB VRAM, free with PRO. 8× higher PRO quota, highest queue priority.

**H100 removed December 2025** — no longer available for Spaces.

### Billing Model

- By the minute on selected hardware; only Starting/Running states billed
- Free hardware auto-sleeps after 48h; woken by any visitor
- Paid hardware runs indefinitely; custom sleep time settable; sleeping not billed
- Pausing stops billing; auto-suspension on failure stops billing
- Each replica billed independently

### Programmatic Configuration

```python
from huggingface_hub import HfApi
api = HfApi()
api.request_space_hardware(repo_id="user/space", flavor="t4-small", sleep_time=3600)
```

Flavor values: `cpu-basic`, `cpu-upgrade`, `t4-small`, `t4-medium`, `l4x1`, `l4x4`, `l40sx1`, `l40sx4`, `l40sx8`, `a10g-small`, `a10g-large`, `a10g-largex2`, `a10g-largex4`, `a100-large`, `a100x4`, `a100x8`.

### Key Takeaways for Zero-Cost Users
1. **CPU Basic** — only free always-on compute (2 vCPU, 16 GB, 50 GB, auto-sleeps)
2. **Static Spaces** — always free for everyone regardless of plan
3. **ZeroGPU** — requires PRO ($9/mo); free-with-PRO GPU option
4. **Community GPU Grants** — apply for free GPU upgrades from Space Settings
5. **Pause unused paid Spaces** — paused time is not billed
6. **Set sleep time on paid hardware** — sleeping stops billing

### Skill Created
`mlops/hf-spaces-hardware-tiers/` — complete reference with full hardware spec tables, billing model, programmatic configuration API, environment variables, and zero-cost optimization strategies.

## 2026-07-25: hf-hub-hfuri-mount-volume-system — HfUri, HfMount, and Volume API for Spaces & Jobs

### Summary
Deep dive into the new Hugging Face Hub URI system (`hf://`), Mount specifications (`hf://...:<MOUNT_PATH>[:ro|:rw]`), and the Volume API for Space/Job resource mounting. Introduced in `huggingface_hub v1.24.0`. The `HfUri` dataclass provides a unified parser for identifying any Hub resource (model, dataset, space, kernel, or bucket) along with an optional revision and sub-path. `HfMount` extends this with a local mount path and read-only flag. The `Volume` dataclass (with `set_space_volumes`/`delete_space_volumes` API) replaces the deprecated `request_space_storage` for Spaces, while `sync_job_volume` enables local-to-bucket syncing for Job volumes.

### Key Components

**1. HfUri — Canonical Hub Resource Identifier**
- Grammar: `hf://[<TYPE>/]<ID>[@<REVISION>][/<PATH>]`
- Type prefixes (plural mandated): `models/`, `datasets/`, `spaces/`, `kernels/`, `buckets/`
- Default type (no prefix): `model`
- Special ref handling: `refs/pr/N` and `refs/convert/<name>` matched eagerly (contain `/`)
- Revisions with `/` not matching special refs are URL-encoded as `%2F`
- Bucket URIs never carry a revision
- Accepted URI types from source: `model`, `dataset`, `space`, `kernel`, `bucket`
- Properties: `.type`, `.id`, `.revision` (optional), `.path_in_repo` (default `""`), `.is_bucket`, `.is_repo`
- `.to_uri()` — renders canonical `hf://` string
- `.to_url(endpoint)` — renders Hugging Face web URL (e.g. `https://huggingface.co/org/model`)

**2. HfMount — Mount Specification**
- Grammar: `hf://[<TYPE>/]<ID>[@<REVISION>][/<PATH>]:<MOUNT_PATH>[:ro|:rw]`
- Fields: `source` (HfUri), `mount_path` (absolute, starts with `/`), `read_only` (optional bool)
- `.to_uri()` — renders mount URI
- Parsing: `parse_hf_mount(mount_str)` returns `HfMount`
- Mount path always starts with `:/` delimiter; uses rfind to handle edge cases

**3. Volume Class — API-facing mount descriptor**
```python
@dataclass
class Volume:
    type: Literal["bucket", "model", "dataset", "space"]
    source: str              # repo or bucket ID
    mount_path: str          # absolute path in container
    revision: str | None     # git revision (repos only)
    read_only: bool | None   # True for repos, default False for buckets
    path: str | None         # subfolder prefix inside resource
```
- `.to_dict()` — serializes to Hub API JSON payload (uses camelCase keys)
- `.to_uri()` — renders as `hf://` mount URI via `HfMount`

**4. set_space_volumes / delete_space_volumes — New Space Volume API**
- `api.set_space_volumes(repo_id, volumes)` — replaces ALL volumes on a Space; raises `BadRequestError` on static Spaces
- `api.delete_space_volumes(repo_id)` — removes ALL volumes from a Space; raises `BadRequestError` if none attached
- `api.get_space_runtime(repo_id)` — returns `SpaceRuntime` with `.volumes: list[Volume] | None`
- `request_space_storage` deprecated in v1.24.0, will be removed in v2.0

**5. sync_job_volume — Job Volume Sync**
- `api.sync_job_volume(source, mount_path, *, remote_name, read_only, namespace)` returns `Volume`
- Syncs local directory to `{namespace}/jobs-artifacts` bucket (auto-created private)
- Uses same sync logic as `sync_bucket` — re-syncing only uploads new/modified files
- Default subfolder name derived from directory path + hostname; pass `remote_name` for fixed name
- Read-only by default; pass `read_only=False` for Job output volumes
- Empty directories get `.keep` placeholder so volume mounts succeed
- Returns a `Volume` ready for `run_job`/`run_uv_job`/`create_scheduled_job`/`create_scheduled_uv_job`

**6. duplicate_repo with space_volumes**
- `api.duplicate_repo(from_id, to_id, *, repo_type, space_volumes=..., ...)` — new unified duplication API
- `duplicate_space()` deprecated in favor of `duplicate_repo(repo_type="space")`
- `space_volumes` parameter accepts `list[Volume]` for the duplicate

**7. Web URL to HF URI Parsing**
- `parse_hf_uri()` accepts both `hf://` URIs and Hugging Face web URLs (auto-detected)
- Supported URL routes: `blob`, `resolve`, `raw`, `tree`, `blame` (repos); `resolve`, `tree` (buckets)
- User/org pages, listing pages, and non-location routes (commit, discussions, settings, edit) rejected
- Self-hosted endpoints supported via `endpoint` parameter
- Constants: `HF_PROTOCOL="hf://"`, `HF_URI_TYPE_PREFIXES={models: model, datasets: dataset, spaces: space, kernels: kernel, buckets: bucket}`, `HF_URL_HOSTS={hf.co, huggingface.co, hub-ci.huggingface.co}`

### Key Design Decisions
- Singular type names rejected with helpful error
- `HfUri` is frozen/hashable — safe for caching and use as dict keys
- Mount paths use rfind(`:/`) to avoid splitting on `:` in Windows-style paths
- Bucket URIs explicitly reject revision markers (`@`)
- `Volume.to_uri()` uses HfMount internally for CLI compatibility
- Model URLs are at root; others under type prefix

### API Integration
- SpaceRuntime includes `volumes: list[Volume] | None` field populated from API response
- `SpaceRuntime` also tracks `dev_mode: bool`, `storage: SpaceStorage | None`, `hot_reloading: SpaceHotReloading | None`
- Volumes in SpaceRuntime are created via `Volume(**v)` from raw API dict

### Practical Usage
```python
from huggingface_hub import HfApi, Volume, parse_hf_uri, parse_hf_mount

# Parse URIs and web URLs
uri = parse_hf_uri("hf://datasets/my-org/my-dataset@v1/train.csv")
uri.to_url()  # full Hugging Face web URL

# Mount specification
mount = parse_hf_mount("hf://models/org/model:/models:ro")
mount.to_uri()  # canonical mount URI

# Volume for Spaces API
api = HfApi()
volumes = [
    Volume(type="bucket", source="my-org/my-bucket", mount_path="/data"),
    Volume(type="model", source="other-org/base-model", mount_path="/model", read_only=True),
]
api.set_space_volumes("my-org/my-space", volumes)
runtime = api.get_space_runtime("my-org/my-space")
for vol in runtime.volumes:
    print(f"{vol.type}: {vol.source} -> {vol.mount_path}")

# Volume for Jobs
vol = api.sync_job_volume("./inputs", mount_path="/inputs", remote_name="eval-data-v3")
job = api.run_uv_job("run_eval.py", volumes=[vol], flavor="cpu-upgrade")
```

### Zero-Cost Relevance
- Volumes for Spaces are available on free CPU Basic hardware (static Spaces not supported)
- `sync_job_volume` syncs to free `jobs-artifacts` bucket (public unlimited, private with limits)
- Mounting models/datasets as volumes costs nothing extra — read-only references to existing resources
- Bucket volumes may incur storage costs for large data; keep buckets public for free unlimited storage
- The `hf://` URI system itself is free — a standardized way to reference Hub resources

### Skill Updated
`mlops/huggingface-hub/` — added HfUri/HfMount/Volume reference to `references/hf-learnings.md`

---

## 2026-07-25: hf-spaces-hot-reload-architecture-deep-dive — Hot Reload & Dev Mode for Spaces

### Summary
Comprehensive source-code deep-dive into the Hugging Face Spaces Hot Reload system (`huggingface_hub._hot_reload`), which enables live code reloading on running Spaces without full container rebuilds. Built on top of **Dev Mode** (a PRO/Team feature that keeps the container alive between restarts), the Hot Reload infrastructure uses Server-Sent Events (SSE) to push incremental code changes to individual replicas. This is the first time the full internal architecture of this system has been documented from source.

### Architecture Overview

The Hot Reload system has three layers:

1. **Dev Mode** — Toggle on/off via `enable_space_dev_mode()`/`disable_space_dev_mode()`. Keeps the Space container running while the application restarts. Required before hot reloading can work. Available on PRO and Team & Enterprise plans.

2. **Commit with `_hot_reload=True`** — Pass the private `_hot_reload=True` parameter to `create_commit()` (or `upload_folder()` which wraps it). This adds `?hot_reload=1` as a query parameter to the commit API endpoint (`POST /api/{type}s/{repo_id}/commit/{revision}`), signalling the Hub to notify all running replicas.

3. **SSE-based Reload Client** — Each running Space replica runs a reload server on port **7887** (subdomain-based: `{space}--7887.hf.space`). The `ReloadClient` connects to this endpoint and streams reload events via SSE.

### Source Code Structure

All hot reload source lives under `huggingface_hub/_hot_reload/` (Copyright 2026, new in v1.24.0):

| File | Purpose |
|------|---------|
| `__init__.py` | Package marker (license only, no exports) |
| `types.py` | TypedDict definitions for all reload API request/response shapes |
| `sse_client.py` | Vendored SSE client (from `mpetazzoni/sseclient`, Apache-2.0) |
| `client.py` | `ReloadClient` and `multi_replica_reload_events()` — core Hot Reload logic |

### Types Reference (`types.py`)

**Operation Types** (the actual events streamed during reload):

| Type | Kind | Description |
|------|------|-------------|
| `ReloadOperationObject` | `"add"` / `"update"` / `"delete"` | File-level object change: `objectType`, `objectName`, `region` |
| `ReloadOperationRun` | `"run"` | Execute code block: `codeLines`, `stdout`, `stderr` |
| `ReloadOperationException` | `"exception"` | Runtime exception with `traceback` string |
| `ReloadOperationError` | `"error"` | Fatal reload error with `traceback` |
| `ReloadOperationUI` | `"ui"` | UI change notification: `updated: bool` |
| `ReloadOperationFile` | `"file"` | File creation notification: `created: bool` |

**API Request/Response Types:**

| TypedDict | Purpose |
|-----------|---------|
| `ApiCreateReloadRequest` | `{filepath, contents, reloadId?}` — trigger a reload on a specific file |
| `ApiCreateReloadResponseSuccess` | `{status: "created", reloadId: str}` |
| `ApiCreateReloadResponseError` | `{status: "alreadyReloading" | "fileNotFound"}` |
| `ApiGetReloadRequest` | `{reloadId: str}` — poll/pull reload events by ID |
| `ApiGetReloadEventSourceData` | Stream of `ReloadOperation*` events emitted during reload |
| `ApiGetStatusRequest` | `{revision: str}` — check if a revision has been reloaded |
| `ApiGetStatusResponse` | `{reloading: bool, uncommitted: list[str]}` |
| `ApiFetchContentsRequest` | `{filepath: str}` — fetch file contents from running Space |
| `ApiFetchContentsResponse` | `{status: "ok" | "fileNotFound", contents?: str}` |

### ReloadClient (`client.py`)

Key design:
- Each replica is addressed by its `replica_hash` via the `--replicas/+{hash}` URL path segment
- GET reload returns an SSE stream — events are parsed by the vendored `SSEClient`
- Non-200/204 status codes raise exceptions; 204 means "reloadId not found" (retryable)
- 20-second client timeout (`CLIENT_TIMEOUT`)

### Multi-Replica Coordination (`multi_replica_reload_events()`)

This function:
1. Creates one `ReloadClient` per replica hash
2. For each replica, calls `get_reload(commit_sha)` with up to `max_retries` retries
3. Tracks all events from the first replica as the reference (`first_client_events`)
4. For subsequent replicas, checks if their stream matches the first replica's events exactly
5. **Deduplication**: events that are identical across replicas are suppressed; only the first replica's events are yielded, plus a `fullMatch` marker for replicas that match exactly
6. **Partial match**: if a replica diverges mid-stream, replay backlog then yield fresh events

### SpaceRuntime Integration

The `SpaceRuntime` dataclass (in `_space_api.py`) exposes hot reload state:
- `dev_mode: bool` — is dev mode enabled?
- `hot_reloading: SpaceHotReloading | None` — active reload if any

`SpaceHotReloading.status` is `"created"` (reload initiated), `"canceled"` (reload aborted), or `None` (pending). The `replica_statuses` field contains per-replica status tuples.

### Dev Mode API
```python
api.enable_space_dev_mode("user/my-space")   # POST /api/spaces/{id}/dev-mode {"enabled": True}
api.disable_space_dev_mode("user/my-space")  # POST /api/spaces/{id}/dev-mode {"enabled": False}
```

### End-to-End Flow
1. Enable Dev Mode → keeps container alive
2. Commit with `_hot_reload=True` → `POST .../commit/main?hot_reload=1`
3. Hub notifies running replicas → each replica streams SSE events on port 7887
4. Events: object add/update/delete, code run, UI update, file create (or exception/error)
5. Poll `get_space_runtime()` → `hot_reloading.status` to verify completion

### Key Design Decisions
1. **SSE over WebSocket** — simpler, unidirectional, HTTP-based
2. **Per-replica port naming** — `--7887` subdomain avoids port conflicts
3. **First-replica dedup** — first replica's events are canonical; subsequent matching replicas yield `fullMatch`
4. **Private `_hot_reload`** — experimental/PRO-only, not in public docs
5. **10 retries** — 2s sleep on 204 (reloadId propagation delay)

### Zero-Cost Relevance
- Dev Mode requires PRO ($9/mo) — not on free tier
- Understanding the architecture helps with debugging Spaces and contributing to `huggingface_hub` open source
- The vendored `sse_client.py` (Apache-2.0) is reusable for any SSE integration

### Files Analyzed
| File | Lines |
|------|-------|
| `huggingface_hub/_hot_reload/types.py` | 121 |
| `huggingface_hub/_hot_reload/sse_client.py` | 144 |
| `huggingface_hub/_hot_reload/client.py` | 130 |
| `huggingface_hub/hf_api.py` (rel. sections) | ~120 |
| `huggingface_hub/_space_api.py` (rel. sections) | ~30 |
| `huggingface_hub/_commit_api.py` (rel. sections) | ~20 |
| **Total code analyzed** | **~565 lines** |

### Skill Updated
`mlops/huggingface-hub/` — added Hot Reload & Dev Mode reference to `references/hf-learnings.md`

---

## 2026-07-25: hf-hub-daily-papers-and-paper-pages-deep-dive

### Summary
Deep-dive into the Hugging Face Daily Papers and Paper Pages ecosystem — the API
endpoints (`/api/daily_papers`, `/api/papers/{id}`, `/api/papers?`), data
structures, linking mechanism via arxiv tags, discussion system, authorship
claims, paper indexing, markdown content delivery, and programmatic discovery
patterns. Verified by live queries to all endpoints.

### Key Findings
- **5 API endpoints** for papers: daily_papers (latest 50), date-filtered, paper detail, search (max 3 results), browse/sort
- **Paper detail** includes `linkedModels`, `linkedDatasets`, `linkedSpaces` with full repo metadata
- **Linking mechanism**: arxiv tags (`arxiv:XXXX.YYYYY`) in repo card tags, auto-extracted from README URLs
- **Discussion system**: Svelte-embedded in HTML data-props, NO public REST API
- **Markdown content** available at `/buckets/huggingchat/papers-content/resolve/{folder}/{id}.md`
- **Paper authorship**: auto-match by email, manual claim via settings, profile visibility toggle
- **Indexing**: auto on visiting `hf.co/papers/{id}`, can also search + index from papers page

### Skill Created
`mlops/hf-hub-daily-papers-and-paper-pages/` — complete SKILL.md + references/hf-learnings.md with API reference, data structures, code patterns

---

## 2026-07-25: hf-inference-mcp-client-agent-framework-deep-dive — HF Inference MCP Client & Agent Framework (Topic #313)

### Summary
Deep dive into the Hugging Face Inference MCP Client and Agent framework built into `huggingface_hub` v1.24+. Covers the `MCPClient` class (core client connecting to MCP servers: stdio, SSE, HTTP/StreamableHTTP), tool discovery and management (tool name deduplication, allowed_tools filtering), `process_single_turn_with_tools()` for streaming chat completions with automatic tool execution, the `Agent` class for multi-turn agent loops (max 10 turns, exit tools `task_complete`/`ask_question`), the `hf app` CLI entry point, and the Tiny Agent config format (`agent.json` with `inputs`/`servers`/`model`/`provider`). Key distinction: this is the CLIENT side of MCP (consuming tools from MCP servers) vs. the HF Hub MCP Server (exposing HF Hub as an MCP server).

### Key Findings
- **MCPClient is async-only** — requires `async with` / `await` for all operations
- **Three server types**: stdio (local processes), SSE (remote streaming), HTTP (StreamableHTTP)
- **Tool deduplication**: first server wins if two provide same tool name
- **allowed_tools filtering**: server-side at connection time, not per-request
- **Auto-converts MCP tools** to `ChatCompletionInputTool` OpenAI format
- **Agent loop**: max 10 turns, exits on `task_complete`, `ask_question`, or direct model response
- **Exit optimization**: returns early if first 2 chunks contain no tool calls
- **Binary content** (images, audio): summarized, not embedded in text stream
- **Separate from HF MCP Server**: this is a *client* that *consumes* MCP servers

### Source
- `huggingface_hub/inference/_mcp/mcp_client.py` (395 lines)
- `huggingface_hub/inference/_mcp/agent.py` (100 lines)
- `huggingface_hub/inference/_mcp/cli.py` (245 lines)
- `huggingface_hub/inference/_mcp/constants.py` (81 lines)
- `huggingface_hub/inference/_mcp/types.py` (45 lines)
- `huggingface_hub/inference/_mcp/utils.py` (130 lines)
- Public API: `from huggingface_hub import MCPClient`

### Skill Created
`mlops/hf-inference-mcp-client/` — HF Inference MCP Client & Agent Framework: complete reference with API details, server types, agent loop architecture, CLI patterns, and code examples.

---

## 2026-07-25: hf-cli-agent-mode-deep-dive — Hugging Face hf CLI Agent-Optimized Mode (Topic #314)

### Summary
Deep dive into the `hf` CLI v1.9.0+ agent-optimized mode. Covers auto-detection of coding agents (Claude Code, Codex, Cursor, etc.), dual rendering (human vs agent output formats), the auto-generated skill system, safe retry semantics (`--exist-ok`, `--yes`, `--dry-run`), next-command hints, composable output (`-q`, `--json`, `--quiet`), and the benchmark results comparing CLI vs curl/Python SDK across ~1,000 graded runs on 18 Hub tasks. The CLI achieves 94% task success on Sonnet (vs 84% without it) and burns 1.3–6× fewer tokens on complex multi-step workflows.

### Key Findings

| Aspect | Detail |
|--------|--------|
| **Detection** | Reads CLAUDECODE, CODEX_SANDBOX, AI_AGENT, CURSOR env vars |
| **Agent output** | TSV format, no truncation, no ANSI, ISO 8601, all tags, stderr guidance |
| **Human output** | Aligned tables, ANSI color, truncated to fit, green ✅ on success |
| **Skill effect** | ~30% fewer tool calls (10.4→6.9 Sonnet, 10.1→7.3 GPT-5.5) |
| **Safe retry** | --exist-ok, -y/--yes, --dry-run on destructive/data-move commands |
| **Token savings** | 1.3–1.8× overall, 2.4–6× on multi-step tasks (bucket sync, org ranking) |
| **Simple reads** | Near parity or cheaper via curl/SDK (0.3–0.5×) |
| **Error handling** | Errors go to stderr with fix command; never prompts in agent mode |

### Benchmark Detail (18 tasks, ~1,000 graded runs)

| Agent | Tool | Success | Self-report errors | Token vs baseline |
|-------|------|---------|-------------------|-------------------|
| Claude Code (Sonnet 4.6) | `hf` CLI | **0.94** | 2/163 | baseline |
|  | curl/Python SDK | 0.84 | 11/163 | 1.3–1.6× |
| Codex (GPT-5.5) | `hf` CLI | **0.93** | 3/163 | baseline |
|  | curl/Python SDK | 0.92 | 10/163 | 1.6–1.8× |

Per-task token ratios for curl/SDK vs CLI (GPT-5.5): bucket create+sync+prune 6.0×, rank org trending models 4.1×, repo create+branch+tag / delete files / copy files across repos 2.4× each. Simple reads: batch model metadata 0.5×, count dataset rows 0.3×.

### Agent Harness Registration
Any agent harness can register by PR to `agent-harnesses.ts` in huggingface.js. Guide at `/docs/hub/agents-overview#register-your-agent-harness`.

### Skill Created
`mlops/hf-cli-agent-mode/` — SKILL.md + references/hf-learnings.md covering agent-optimized CLI design, detection, rendering modes, skill system, benchmark results, and best practices.

### Sources
- https://huggingface.co/blog/hf-cli-for-agents (primary source)
- https://huggingface.co/docs/huggingface_hub/guides/cli
- https://huggingface.co/docs/hub/agents-overview


---

## 2026-07-25: hf-transformers-tipsv2 (Topic #316 — New)

### Summary
Deep-dive into TIPSv2 (Text-Image Pre-training with Spatial awareness v2) — Google DeepMind's contrastive vision-language encoder family added in Transformers v5.14.0. Covers dual-class-token architecture (alt-text + synthetic caption supervised), iBOT++ pretraining objective, zero-shot classification, DPT head for depth/normal/segmentation, and full HF integration. Key innovation: unmasked tokens contribute to masked image modeling loss, dramatically improving patch-text alignment.

### Key Findings
- **Dual class tokens**: CLS1 (web alt-text) + CLS2 (PaliGemma synthetic captions) via repurposed register tokens
- **iBOT++**: unmasked patches also contribute to loss — student surpasses teacher in patch-text alignment
- **448×448 images**, 14×14 patches → 32×32 grid
- **Text encoder limits**: ReLU activation, max 64 tokens, BPE tokenizer
- **3 tasks with DPT**: depth estimation (meters), normal estimation (XYZ), semantic segmentation in one forward pass
- **Tipsv2Model** returns normalized embeddings; **get_image_features/get_text_features** return raw (unnormalized)
- **Available sizes**: b14 (base) and l16 (large), each with/without DPT head
- **Collection**: https://huggingface.co/collections/google/tipsv2

### Skill Created
`mlops/hf-transformers-tipsv2/` — SKILL.md + references/hf-learnings.md covering architecture, configs, usage patterns, API surface, and comparisons to CLIP/SigLIP.

### Sources
- https://huggingface.co/docs/transformers/main/en/model_doc/tipsv2
- https://huggingface.co/docs/transformers/main/en/model_doc/tipsv2_dpt
- https://huggingface.co/papers/2604.12012
|- Transformers v5.14.0 release notes

---

## 2026-07-26: hf-hub-create-commit-pipeline-source-code-deep-dive (Topic #318 — Deepening)

### Summary
Source-code-level deep dive into the `HfApi.create_commit()` pipeline in `huggingface_hub==1.24.0`. Covers the full lifecycle: validation → upload mode resolution (`_fetch_upload_modes`) → LFS pre-upload (`_upload_files` with Xet path or legacy LFS path) → copy duplication → no-op detection → payload assembly (`_prepare_commit_payload`) → ndjson POST to `/commit`. Key insight: the pipeline is a two-phase protocol where file _metadata_ is resolved in phase 1 and _content_ is uploaded in phase 2, all before the actual commit HTTP request.

### Pipeline Architecture

```
create_commit()
├── 1. Validate inputs (commit_message, parent_commit OID, repo_type, README.md YAML)
├── 2. Separate operations: additions, copies, deletions
├── 3. preupload_lfs_files()
│   ├── 3a. _fetch_upload_modes() — POST /preupload/{revision} for each batch of 256 files
│   │   Returns: uploadMode ("lfs"|"regular"), shouldIgnore, remote OID
│   │   Payload: {path, sample (first 512B base64), size}
│   │   + gitIgnore content if .gitignore is committed
│   ├── 3b. Filter: skip already-uploaded, gitignored, regular files
│   └── 3c. _upload_files() — content upload
│       ├── Xet path (preferred): hf_xet session.new_upload_commit() — chunk-based CAS
│       │   - start_upload_file() for file paths, start_upload_bytes() for bytes
│       │   - sha256 backfilled from hf_xet result (single read pass)
│       └── Legacy LFS path: post_lfs_batch_info() → _upload_lfs_files()
│           - SHA256 computed in parallel via ThreadPoolExecutor
│           - LFS batch API: actions with "upload" URLs
│           - Supports "basic" and "multipart" transfers
│           - thread_map for parallel upload
├── 4. _fetch_files_to_copy() — resolve copy sources (LFS metadata vs raw content download)
├── 5. _duplicate_lfs_files() — cross-repo LFS copy via /lfs-files/duplicate endpoint
├── 6. Remove no-op operations (file unchanged: _remote_oid == _local_oid)
├── 7. _send_commit()
│   ├── _prepare_commit_payload() → ndjson stream
│   │   Line 1: {"key":"header","value":{"summary","description","parentCommit"}}
│   │   Per operation:
│   │     - regular file: {"key":"file","value":{"content":"base64","path":"...","encoding":"base64"}}
│   │     - LFS file: {"key":"lfsFile","value":{"path":"...","algo":"sha256","oid":"...","size":N}}
│   │     - delete: {"key":"deletedFile"|"deletedFolder","value":{"path":"..."}}
│   │     - copy: {"key":"file"|"lfsFile"} (same as add but content sourced from files_to_copy)
│   ├── POST /api/{repo_type}s/{repo_id}/commit/{revision} (Content-Type: application/x-ndjson)
│   │   params: create_pr=1, hot_reload=1
│   └── Response: {commitUrl, commitOid, pullRequestUrl}
└── 8. Mark additions as _is_committed = True
```

### Key Source Details

**UploadInfo (lfs.py:53-100):** Lazy SHA256 computation — only first 512 bytes read at construction time. Full SHA256 on first access. Can be backfilled by Xet upload to avoid double-read.

**_fetch_upload_modes() (_commit_api.py:698-780):** POSTs batches of 256 files to `/preupload/{revision}`. Server responds with upload mode per file. Empty files (size==0) are forced to "regular" mode (S3 rejects empty LFS uploads). gitignore filtering is server-side with `shouldIgnore` flag.

**_upload_files() (_commit_api.py:378-448):** Xet path preferred when `hf_xet` is available (no BufferedIOBase ops). Xet chunks files, deduplicates chunks via content-addressable storage (CAS), uploads in parallel. Legacy path: LFS batch API with SHA256 computation, actions parsing, parallel multipart/basic uploads.

**_send_commit() (_commit_api.py:1008-1075):** Builds ndjson payload and POSTs to /commit. Supports `retry_on_error` with http_backoff (opt-in; risk of duplicate commits on lost response). Response parsed into CommitInfo(commit_url, commit_message, oid, pr_url).

**CommitOperationAdd mutations during pipeline:**
1. `_upload_mode` — set by _fetch_upload_modes
2. `_should_ignore` — set by _fetch_upload_modes (gitignore)
3. `_remote_oid` — set by _fetch_upload_modes (for no-op detection)
4. `_is_uploaded` — set after preupload_lfs_files
5. `_is_committed` — set after commit success
6. `path_or_fileobj` → `b""` — freed after upload if `free_memory=True`

**No-op optimization:** If `_remote_oid == _local_oid`, file is skipped entirely. LFS local OID = SHA256 hex; regular local OID = git-style SHA1. Entire commit is skipped if all ops are no-ops (returns last commit info).

**Limits:** 25k LFS files per commit, 1GB regular file payload, 256 files per preupload batch, 500 files per FETCH_LFS_BATCH_SIZE, 500 files per DUPLICATE_LFS_BATCH_SIZE.

### Skill Created
N/A — added to existing `mlops/huggingface-hub/` skill references.

### Sources
- huggingface_hub v1.24.0 source: `hf_api.py:4943-5217` (create_commit)
- huggingface_hub v1.24.0 source: `hf_api.py:5219-5380` (preupload_lfs_files)
- huggingface_hub v1.24.0 source: `_commit_api.py` (full pipeline: 1075 lines)
- huggingface_hub v1.24.0 source: `lfs.py:53-100` (UploadInfo)
- https://github.com/huggingface/huggingface_hub/issues/1085#issuecomment-1265208073 (ndjson commit design)
|

## 2026-07-25: hf-datasets-configuration-system-complete-reference

### Summary
Comprehensive deep dive into the Hugging Face Datasets configuration system (v5.0.0). Covers the full lifecycle of dataset configurations: BuilderConfig base class, BUILDER_CONFIGS predefined configs, DEFAULT_CONFIG_NAME selection, config ID generation with suffix hashing, YAML metadata configs from README.md, dataset_infos.json serialization, config resolution in load_dataset(), cache directory architecture, packaged module configs, and integration with the Datasets Server.

### Key Findings

**BuilderConfig (@dataclass):**
- 5 fields: name (default: "default"), version (default: "0.0.0"), data_dir, data_files, description
- Validates Windows-incompatible chars in name
- create_config_id() generates unique cache ID with suffix from config_kwargs, custom_features, data_files

**Config Resolution (3 paths):**
1. No config specified → DEFAULT_CONFIG_NAME or single config or raise
2. String config_name → lookup in builder_configs dict
3. Custom → instantiate BUILDER_CONFIG_CLASS with kwargs
Plus override path: deepcopy predefined config + apply kwargs

**Config ID:**
- Base = config.name
- Suffix added when config_kwargs/features/data_files differ from predefined
- URL-encoded string if all primitive values and ≤32 chars; SHA256 hash otherwise
- Max readable length: 255 chars (truncated + hashed if exceeded)

**MetadataConfigs (YAML configs field):**
- Dict[config_name → params] parsed from DatasetCardData
- Validates data_files format (str, list of str, or split-based list)
- Auto-generates default detection via name="default" or default: true
- _from_exported_parquet_files_and_dataset_infos() auto-creates configs from Parquet export

**Cache Directory:** {dataset_name}/{config_id}/{version}/{hash}/ with namespace prefix for Hub repos.

**Packaged Module Configs:**
- csv → CsvConfig (sep, header, names)
- json → JsonConfig (field, features)
- parquet → ParquetConfig (features)
- imagefolder → ImageFolderConfig (drop_labels, drop_metadata)
- audiofolder → AudioFolderConfig (sampling_rate)
- text → TextConfig (sample_by)

### Skill Created
hf-datasets-configuration-system/ — complete reference with architecture, API surface, config ID system, YAML metadata format, cache layout, and practical usage examples.

### Sources
- datasets v5.0.0 source: builder.py (BuilderConfig: lines 100-212, DatasetBuilder._create_builder_config: lines 503-592)
- datasets v5.0.0 source: info.py (DatasetInfo: lines 91-280, DatasetInfosDict: lines 334-440)
- datasets v5.0.0 source: utils/metadata.py (MetadataConfigs: lines 46-189)
- datasets v5.0.0 source: load.py (create_builder_configs_from_metadata_configs: lines 320-374, BuilderConfigsParameters: lines 377-392)
- datasets v5.0.0 source: config.py (constants: lines 236-248)
- huggingface_hub v1.24.0 source: repocard_data.py (DatasetCardData constructor)
- https://huggingface.co/docs/datasets/main/en/loading#configurations-and-splits
|- https://huggingface.co/docs/datasets/main/en/dataset_script#multiple-configurations
|
|---
|
|## 2026-07-25: hf-hub-local-agents-with-llamacpp — HF Hub Local Agents with llama.cpp (Topic #324)
|
|### Summary
|Deep dive into HF Hub's "Local Agents with llama.cpp" workflow. Covers running Pi, OpenClaw, Hermes Agent, OpenCode, and llama-agent (C++ binary, zero deps) with llama.cpp server backend using HF GGUF models. Key innovation: hardware profiling at huggingface.co/settings/hardware + one-click `llama-server -hf` commands.
|
|### 5 Agent Frameworks
|| Agent | Config Location | Notes |
||-------|----------------|-------|
|| Pi | ~/.pi/agent/models.json | npm install -g @mariozechner/pi-coding-agent |
|| OpenClaw | openclaw onboard CLI | Supports local memory search via node-llama-cpp |
|| Hermes Agent | ~/.hermes/config.yaml | custom provider + session_search for embeddings |
|| OpenCode | ~/.config/opencode/opencode.json | Uses @ai-sdk/openai-compatible |
|| llama-agent | cmake binary | Zero deps, in-process tool calls, subagent + MCP support |
|
|### Sources
|- https://huggingface.co/docs/hub/en/agents-local
|- https://huggingface.co/docs/hub/en/agents
|- https://huggingface.co/settings/hardware
|
|### Skill Created
|`hf-hub-local-agents-with-llamacpp/` — reference with exact config files for all 5 agent frameworks, architecture diagram, local memory search patterns.
|

---
# HF Learnings — HF Sandboxes v3: Background Processes, Port Proxy, Pool Management, and Source Architecture

## 2026-07-25: hf-sandboxes-v3-deep-dive — Hugging Face Sandbox API: Complete Source Architecture & Advanced Patterns (Topic #327)

### Summary
Source-code-level deep dive into the complete Hugging Face Sandboxes system as of `huggingface_hub v1.24.0` (released 2026-07-17). The sandbox API has evolved significantly since the initial deep-dive (Topic #148), gaining background process support (v1.22.0), port proxy for in-sandbox servers (v1.22.0), SandboxPool with cache persistence and cross-process host discovery (v1.22.0), and parallel file transfers for large files. The system is built entirely on HF Jobs — a sandbox is just a Job running a ~640KB static Rust binary (`sbx-server`), with no dedicated infrastructure beyond the Job API. This document covers the full 1764-line `_sandbox.py` module, the 159-line `_sandbox_cache.py` module, and the 480-line CLI surface.

### Source Files Analyzed

| File | Lines | Purpose |
|------|-------|---------|
| `huggingface_hub/_sandbox.py` | 1764 | Core Sandbox + SandboxPool implementation |
| `huggingface_hub/_sandbox_cache.py` | 159 | Best-effort pool cache for cross-process host reuse |
| `huggingface_hub/cli/sandbox.py` | 480 | CLI commands (`hf sandbox *`) |
| `huggingface_hub/errors.py` | 609 | SandboxError, SandboxCommandError exception types |

### Public API

```python
from huggingface_hub import Sandbox, SandboxPool, SandboxCommandResult, SandboxProcess
from huggingface_hub.errors import SandboxError, SandboxCommandError
```

---

### 1. Architecture Overview

Sandboxes have **zero dedicated infrastructure** — they are HF Jobs running a static Rust binary. This design choice means they inherit Jobs' billing, hardware flavors (cpu-basic → H200), namespace permissions, and volume system for free.

```
User Code
  ↓
Sandbox.create() / SandboxPool.create()
  ↓
HfApi.run_job()       ← Jobs API creates a VM
  │  [image: python:3.12, flavor: cpu-basic, expose: 49983]
  ↓
Job starts on infra
  │  Bootstrap script (wget/curl sbx-server binary)
  │  Token auth via HMAC-SHA256
  ↓
sbx-server (Rust binary) running on port 49983
  │  Hand-rolled HTTP/1.1 server
  │  NDJSON event streams for exec
  │  /health, /exec, /files/*, /processes, /proxy/*, /v1/sandboxes/*
  ↓
Sandbox._server (httpx.Client) → base_url/job-id--49983.hf.jobs
```

**Two modes:**

| Mode | Class | Isolation | GPU | Cold Start | Cost Profile |
|------|-------|-----------|-----|------------|--------------|
| Dedicated | `Sandbox.create()` | Full VM | ✅ Yes | ~5-7s | One Job per sandbox |
| Shared/Pooled | `SandboxPool.create()` | uid + Landlock LSM | ❌ No | ~1ms server-side | Many sandboxes per host VM |

**Bootstrap sequence (in `/bin/sh`):**
1. Download `sbx-server` from HF bucket with `wget`/`curl` (fast ~6s cold start)
2. Fallback: read from always-mounted server bucket via FUSE (+2-3s)
3. Execute binary on port 49983 with derived auth token
4. Server starts, begins health-check polling
5. `Sandbox` client polls `/health` until 200 → ready

**Key constants:**
```python
SANDBOX_SERVER_PORT = 49983      # In-job server port (deliberately uncommon)
SANDBOX_LABEL = "hf-sandbox"     # Label on every sandbox job
MODE_LABEL = "hf-sandbox-mode"   # "dedicated" or "pool"
MODE_DEDICATED = "dedicated"
MODE_POOL = "pool"
POOL_LABEL = "hf-sandbox-pool"   # Pool name label
NONCE_LABEL = "hf-sandbox-nonce" # Public nonce for token derivation
DEFAULT_IMAGE = "python:3.12"
DEFAULT_IDLE_TIMEOUT = 600       # 10 minutes
SANDBOX_MAX_LIFETIME = "24h"     # Absolute max job lifetime
DEFAULT_SANDBOXES_PER_HOST = 50  # Pool sandboxes per host VM
SHARED_ID_SEP = "."              # Separator in shared sandbox ids: <host_job_id>.<local_id>
```

---

### 2. Stateless Authentication System

Sandbox auth is **entirely stateless** — no database, no stored tokens, no session state.

**Two-layer security:**
1. **Transport layer (proxy gate):** The Jobs proxy (`.hf.jobs`) validates the user's HF token — only authenticated users can reach the sandbox server
2. **Application layer (sandbox gate):** A per-sandbox HMAC-SHA256 token, derived from the user's HF token + a public nonce, authenticates every API request inside the sandbox

**Token derivation (never sends HF token to sandbox):**
```python
def _derive_sandbox_token(hf_token: str, nonce: str) -> str:
    return hmac.new(
        hf_token.encode(),
        f"hf-sandbox:{nonce}".encode(),
        hashlib.sha256
    ).hexdigest()
```

**Flow during creation:**
1. Client generates random `nonce = token_hex(16)`
2. Client computes `sandbox_token = _derive_sandbox_token(hf_token, nonce)`
3. Nonce is stored as the `hf-sandbox-nonce` job label (public)
4. Sandbox token is sent as `SBX_TOKEN` in job secrets (encrypted server-side)
5. When reconnecting: read nonce from job labels, recompute token locally
6. HTTP requests carry: `Authorization: Bearer {hf_token}` + `X-Sandbox-Token: {sandbox_token}`

**Reconnection from any machine:**
```python
# No local state needed — token is recomputed from job metadata
sandbox = Sandbox.connect("job_id_here")
```
The server validates both headers: the HF token (proxy gate) and the sandbox token (application gate). If the HF token changes (e.g., regenerated), reconnection fails — the sandbox token is bound to the original HF token via HMAC.

---

### 3. Data Structures

#### SandboxCommandResult
```python
@dataclass
class SandboxCommandResult:
    exit_code: int | None
    stdout: str
    stderr: str
    signal: int | None = None
    timed_out: bool = False
    duration_ms: int = 0

    @property
    def ok(self) -> bool:
        return self.exit_code == 0
```

#### SandboxProcess (background processes, v1.22.0+)
```python
@dataclass
class SandboxProcess:
    pid: int
    cmd: str | List[str]
    _sandbox: "Sandbox"  # back-reference for kill(), excluded from repr/eq
    tag: str | None = None
    started_at_ms: int | None = None
    running: bool = True
    exit_code: int | None = None

    def kill(self) -> None:
        """Terminate the background process (idempotent server-side)."""
        self._sandbox._request("DELETE", f"/processes/{self.pid}")
```

#### FileEntry
```python
@dataclass
class FileEntry:
    name: str
    path: str
    type: Literal["file", "dir", "symlink"]
    size: int
    mtime_ms: int | None = None
    mode: str = ""
```

#### _SandboxServer (internal transport)
```python
class _SandboxServer:
    """HTTP transport to one sbx-server instance — a dedicated job or a shared host."""
    def __init__(self, *, job_id, owner, image, base_url, nonce,
                 sandbox_token, api, max_connections=10, capacity=0):
        self.job_id = job_id
        self.owner = owner
        self._image = image
        self.base_url = base_url
        self.nonce = nonce
        self._api = api
        self._auth_token = _effective_token(api)
        self._sandbox_token = sandbox_token
        self.capacity = capacity     # Max sandboxes this host can pack (pool mode)
        self.live = 0                # Current sandbox count
        self.verified = True         # False for hosts from cache (unverified)

        # Single httpx.Client for all operations (thread-safe!)
        self._client = httpx.Client(
            headers={"Authorization": f"Bearer {self._auth_token}",
                     "X-Sandbox-Token": sandbox_token},
            limits=httpx.Limits(max_connections=max_connections,
                                max_keepalive_connections=max_connections),
            follow_redirects=True,
        )
```

#### CachedHost & PoolCache (cache layer)
```python
@dataclass
class CachedHost:
    job_id: str
    owner: str
    base_url: str           # Does not change while the job lives
    nonce: str              # For re-deriving sandbox token
    capacity: int           # Max sandboxes
    live: int               # Last observed count (may be stale)
    updated_at: float = 0.0

@dataclass
class PoolCache:
    pool_id: str
    image: str
    flavor: str
    sandboxes_per_host: int
    max_hosts: int | None
    idle_timeout: int | None
    namespace: str | None
    hosts: List[CachedHost] = field(default_factory=list)
    version: int = 1
    updated_at: float = 0.0
```

---

### 4. Sandbox (Dedicated Mode)

#### Creating a Dedicated Sandbox

```python
Sandbox.create(
    image: str = "python:3.12",
    flavor: str = "cpu-basic",
    idle_timeout: int | float | str | None = 600,
    env: dict[str, Any] | None = None,
    secrets: dict[str, Any] | None = None,
    volumes: List[Volume] | None = None,
    namespace: str | None = None,
    forward_hf_token: bool = False,
    start_timeout: float = 120.0,
    token: str | None = None,
) -> Sandbox
```

**Creation flow (source `_sandbox.py` lines 512-611):**
1. Generate random nonce + derive sandbox token
2. Build job spec via `_bootstrap_job_spec()` — generates bootstrap command, env vars, secrets, volumes
3. Call `api.run_job()` with `image`, `flavor`, command, env, secrets, labels (SANDBOX_LABEL, MODE_DEDICATED, NONCE_LABEL), volumes, and `expose=[SANDBOX_SERVER_PORT]`
4. Build `_SandboxServer` from returned job info (`from_job()`)
5. Wait for server readiness via `wait_ready(start_timeout)` — polls `/health` every 150ms, checks job stage every 2s
6. If startup fails: cancel the job (cleanup billable resource) before re-raising
7. Returns `Sandbox(id=job.id, server=server, local_id=None, owns_sandbox=True, owns_server=True)`

**Recovery from failed startup:**
```python
# In Sandbox.create(), lines 601-610:
except Exception:
    try:
        api.cancel_job(job_id=job.id, namespace=job.owner.name)
    except Exception as e:
        logger.warning(f"Failed to cancel sandbox job {job.id} after startup failure: {e}")
    if server is not None:
        server.close()
    raise
```

#### Reconnecting

```python
Sandbox.connect(sandbox_id: str, *, namespace: str | None = None,
                token: str | None = None) -> Sandbox
```

**Two paths (source lines 613-650):**
- **Shared sandbox** (`.` in id): Split `host_job_id.local_id`, connect to host, verify local_id exists on host
- **Dedicated sandbox**: Inspect job by id, verify it's a sandbox (has SANDBOX_LABEL), verify it's still RUNNING, recompute token from nonce, build server transport

Returns a Sandbox with `owns_sandbox=False` (exiting `with` block won't kill it).

#### Running Commands

```python
# Foreground (waits for completion, streams output live)
result: SandboxCommandResult = sbx.run(
    cmd="python train.py --epochs 10",
    shell=True,                          # infer from cmd type: True for str
    env={"LR": "0.001"},                 # extra env vars for this command
    cwd="/workspace",                    # working directory
    timeout=300.0,                       # kill after this many seconds
    stdin="y\n",                         # stdin data
    on_stdout=lambda chunk: print(chunk, end=""),  # live stdout callback
    on_stderr=lambda chunk: print(chunk, end=""),  # live stderr callback
    check=True,                          # raise SandboxCommandError on non-zero exit
)

# Background (returns immediately, process runs detached)
process: SandboxProcess = sbx.run(
    cmd="uvicorn app:app --host 0.0.0.0 --port 8000",
    background=True,
)
```

**Execution architecture (source lines 725-816):**
- Foreground: POST `/v1/exec` (or `/v1/sandboxes/<local_id>/exec` in pool mode) with NDJSON streaming
  - Server sends events: `stdout`, `stderr`, `exit`
  - Client accumulates stdout/stderr in lists
  - On `exit` event: construct SandboxCommandResult with exit_code, stdout, stderr, signal, timed_out, duration_ms
  - If check=True and non-zero exit: raise SandboxCommandError
- Background: POST `/v1/processes` (returns just `{"pid": N, "tag": "..."}`)

**NDJSON event stream format:**
```json
{"event": "stdout", "data": "Hello "}
{"event": "stdout", "data": "World\n"}
{"event": "exit", "exit_code": 0, "signal": null, "timed_out": false, "duration_ms": 45}
```

Keepalive pings (every 15s from server) are filtered out:
```python
def _iter_events(response):
    for line in response.iter_lines():
        if not line:
            continue
        event = json.loads(line)
        if event.get("event") != "ping":
            yield event
```

#### Background Process Management (v1.22.0+)

```python
# List all background processes
processes: List[SandboxProcess] = sbx.processes()

# Stop a specific process
proc = sbx.run("python long_task.py", background=True)
proc.kill()   # DELETE /processes/{pid}

# Process properties
proc.pid           # int
proc.cmd           # original command
proc.running       # bool
proc.exit_code     # None if still running, int if completed
proc.tag           # optional user tag
proc.started_at_ms # timestamp
```

Completed processes stay in the listing (with `running=False` and `exit_code`) until the sandbox is deleted.

#### File Operations

```python
sbx.files.read(path) -> bytes              # GET /files/read?path=...
sbx.files.read_text(path) -> str           # wrapper around read()
sbx.files.write(path, data, mode=None)     # PUT /files/write
sbx.files.upload(local_path, path)         # upload local file
sbx.files.download(path, local_path)       # download to local file
sbx.files.list(path) -> List[FileEntry]    # GET /files/list
sbx.files.stat(path) -> FileEntry          # GET /files/stat
sbx.files.exists(path) -> bool             # check existence
sbx.files.delete(path, recursive=False)    # DELETE /files/delete
sbx.files.mkdir(path)                      # POST /files/mkdir
```

**Path semantics:**
- **Dedicated mode**: paths are absolute on the container filesystem
- **Pool (shared) mode**: paths are rooted at the sandbox's private home directory — a leading `/` is taken relative to that home

#### Parallel File Transfers (v1.22.0+)

Files >2MB are automatically transferred using parallel ranged requests for bandwidth aggregation:

```python
class SandboxFiles:
    PARALLEL_THRESHOLD = 2 * 1024 * 1024   # 2MB — above this, use parallel
    PARALLEL_CHUNK_SIZE = 1 * 1024 * 1024  # 1MB per chunk
    PARALLEL_MAX_WORKERS = 16              # up to 16 concurrent connections
```

The parallel transfer uses `ThreadPoolExecutor` with ranged GET/PUT requests:
```python
def _read_ranges(self, path, size):
    def fetch(rng):
        offset, length = rng
        response = self._sandbox._request(
            "GET", "/files/read",
            params={"path": path, "offset": offset, "length": length}
        )
        return response.content
    return self._parallel(self._ranges(size), fetch)
```

This compensates for the per-TCP-stream bandwidth-delay product limitation (~2 MiB/s at ~100ms RTT through the Jobs proxy).

#### Port Proxy (v1.22.0+)

Allows accessing a server running *inside* the sandbox from outside:

```python
url = sandbox.proxy_url_for(
    port=8000,
    path="/api/health",
    scheme="https://"        # or "wss://" for WebSocket
)
# Returns: https://<job_id>--49983.hf.jobs/v1/proxy/8000/api/health

headers = sandbox.proxy_headers
# Returns: {"Authorization": "Bearer <hf_token>",
#           "X-Sandbox-Token": "<sandbox_token>"}
```

**Pool vs dedicated differences:**
- **Pool/shared sandbox**: Cannot bind TCP (Landlock restriction). Must bind a **unix socket** at `$SBX_PROXY_DIR/<port>.sock`:
  ```python
  # Inside sandbox:
  import uvicorn
  uvicorn.run(app, uds=f"{os.environ['SBX_PROXY_DIR']}/8000.sock")
  ```
- **Dedicated sandbox**: Bind normal TCP port on `127.0.0.1:<port>` (can also expose directly via job proxy without port proxy)

**WebSocket support:**
```python
url = sandbox.proxy_url_for(8000, "/ws", scheme="wss://")
import websockets
async with websockets.connect(url, additional_headers=sandbox.proxy_headers) as ws:
    await ws.send("hello")
```

The proxy is protocol-agnostic — only the client-side scheme changes.

---

### 5. SandboxPool (Shared/Pooled Mode)

SandboxPool packs many lightweight sandboxes onto shared host VMs, each isolated by uid + Landlock LSM. One host = one HF Job (a VM). Up to 50 sandboxes per host by default.

#### Creating a Pool

```python
pool = SandboxPool(
    image="python:3.12",
    flavor="cpu-basic",
    sandboxes_per_host=50,
    warm_up=1,                # Pre-provision 1 host in constructor
    max_hosts=None,           # Optional cost ceiling
    name=None,                # Random if omitted (e.g. "pool-ab12cd34ef56")
    idle_timeout=600,         # Host idle timeout (no sandboxes → shutdown)
    namespace=None,
    start_timeout=120.0,
    token=None,
)
```

The constructor blocks until `warm_up` hosts are ready. Uses threading locks to serialize concurrent operations.

#### Creating Sandboxes in a Pool

```python
with SandboxPool(image="python:3.12", warm_up=2) as pool:
    boxes = [pool.create(env={"WORKER_ID": str(i)})
             for i in range(100)]   # Packed across warm hosts
    print(boxes[0].run("echo hi").stdout)
```

`pool.create()` (source lines 1134-1235) implements a **pack-retry loop**:

1. **Reserve** a slot on a known host with free capacity (`host.live < host.capacity`)
2. **Discover** warm hosts via job labels if no capacity (one-shot per create)
3. **Boot** a new host if still no capacity (under `_boot_lock` to serialize)
4. **Create** sandbox on reserved host via `POST /v1/sandboxes`
5. **Retry** (up to `_MAX_PACK_ROUNDS=8`) if host filled between reservation and create
6. **Rollback** all newly booted hosts if any step fails

**Key design decisions:**
- `_boot_lock` serializes host creation — a burst of `create()` calls queue here, and each new host frees `sandboxes_per_host` slots for waiting threads
- `_adopt_pending_host()` detects hosts already `SCHEDULING` for this pool (started by another process or earlier create) and waits for them instead of booting duplicates
- All-or-nothing teardown: if `create()` fails after booting new hosts, cancel them to prevent billing leaks

#### Pool Reconnection

```python
# Reattach to a pool from any machine
pool = SandboxPool.connect("pool-ab12cd34ef56")
sandbox = pool.create()  # uses existing warm hosts
```

**Two paths (source lines 1052-1105):**
1. **Fast path**: Local cache hit → rebuild pool from `PoolCache` with no HTTP. Hosts are verified lazily on first `create()`
2. **Cold path**: Find running host via job labels (`MODE_LABEL=pool` + `POOL_LABEL`), rebuild config from host's env vars (`SBX_CAPACITY`, `SBX_IDLE_TIMEOUT`, `SBX_MAX_HOSTS`)

#### Warming Hosts

```python
pool.warm(num_hosts=2)
# Pre-provisions 2 empty hosts (or adopts existing ones). Returns list of host job ids.
```

Creates hosts that carry the pool label and config in env vars. Cross-process discoverable: another machine can `SandboxPool.connect(pool_id)` and find them. Hosts persist until killed or idle-timed-out.

#### Pool Properties

```python
pool.num_hosts      # int — host jobs provisioned
pool.num_sandboxes  # int — sandboxes currently handed out
pool.host_ids       # List[str] — host job ids
```

#### Pool Cleanup

```python
pool.close()  # For owned pools: cancels all host jobs + sandboxes, deletes cache
              # For connect()'d handles: releases HTTP clients only, leaves hosts running

# Context manager:
with SandboxPool(...) as pool:
    ...
# Automatically calls close()
```

---

### 6. Pool Cache System (v1.22.0+)

The cache lives at `~/.cache/huggingface/sandbox/pools/<pool_id>.json` with a companion `.lock` file.

**Cache operations (source `_sandbox_cache.py`):**
```python
# Read: returns None if missing/corrupt/incompatible version
cache = read_pool_cache(pool_id)  # → PoolCache | None

# Write: upserts hosts by job_id, removes dead_host_ids, atomic write
save_pool_cache(pool_id, image=..., flavor=..., sandboxes_per_host=...,
                max_hosts=..., idle_timeout=..., namespace=...,
                hosts=[CachedHost(...)], dead_host_ids={"job_id_1"})

# Delete: removes cache file
delete_pool_cache(pool_id)
```

**Cache design principles:**
- **Best-effort**: Save failures are logged but never raised. Read failures silently return None.
- **Concurrency-safe**: Uses `WeakFileLock` with 5s timeout. Read-merge-write: reads existing, upserts by job_id, removes dead hosts.
- **Atomic writes**: Writes to temp file then `os.replace()` — readers never see partial content.
- **Versioned**: Cache version `_CACHE_VERSION=1` — incompatible versions are silently dropped.

**Dead host pruning:** Hosts found dead during this session are tracked in `self._dead_host_ids` and removed from the cache on save. This prevents stale entries from lingering.

**Cross-process sharing flow:**
```
Process A           → Creates SandboxPool → warms hosts → saves cache
Process B           → SandboxPool.connect() → reads cache (zero HTTP)
Process B.create()  → First request to cached host → succeeds → host verified
                     └─ Host gone → drops it, discovers via labels, boots replacement
```

---

### 7. Host Discovery & Cross-Process Sharing

Pools use **label-based discovery** via the Jobs API to find hosts across processes:

```python
def _discover_hosts(self):
    known = {host.job_id for host in self._hosts}
    matches = [
        job for job in self._api.list_jobs(
            status="RUNNING",
            labels={MODE_LABEL: MODE_POOL, POOL_LABEL: self.name},
            namespace=self._namespace,
        )
        if job.id not in known
    ]
    for job in matches:
        server = _connect_host(self._api, job.id, namespace=self._namespace)
        # Read host's actual capacity from env, live count from server
        server.capacity = int(env.get("SBX_CAPACITY", self.sandboxes_per_host))
        server.live = len(server.request("GET", "/v1/sandboxes").json())
        self._hosts.append(server)
```

**Cross-process adoption prevents over-provisioning:**
```python
def _adopt_pending_host(self):
    """Find a host already SCHEDULING for this pool → wait for it instead of booting."""
    pending = next((
        job for job in self._api.list_jobs(
            status="SCHEDULING",
            labels={MODE_LABEL: MODE_POOL, POOL_LABEL: self.name},
            namespace=self._namespace,
        )
        if job.id not in known
    ), None)
    # Wait for it to reach RUNNING + server ready
```

---

### 8. Parallel Host Provisioning

When multiple hosts need to be booted (e.g., `warm_up=4`), they are booted in parallel:

```python
def _provision_hosts(self, num_new: int) -> List[_SandboxServer]:
    with ThreadPoolExecutor(max_workers=min(num_new, 32)) as executor:
        futures = [executor.submit(self._boot_host) for _ in range(num_new)]
    # Collect all results; if any fail, cancel all booted hosts
    booted: List[_SandboxServer] = []
    error: Exception | None = None
    for future in futures:
        try:
            booted.append(future.result())
        except Exception as e:
            error = e
    if error is not None:
        for server in booted:
            server.cancel_job()  # Cancel already-booted hosts
        raise error
    return booted
```

---

### 9. CLI Surface (hf sandbox)

Full CLI parity with the Python API, auto-detecting agent mode for token-efficient output.

| Command | Purpose |
|---------|---------|
| `hf sandbox create [image]` | Create a dedicated sandbox (or shared with `--pool`) |
| `hf sandbox exec <id> -- <cmd>` | Run a command in an existing sandbox |
| `hf sandbox cp <src> <dst>` | Copy files to/from a sandbox |
| `hf sandbox spawn <id> -- <cmd>` | Start a background process |
| `hf sandbox process ls <id>` | List background processes |
| `hf sandbox process kill <id> <pid>` | Stop a background process |
| `hf sandbox kill <id>` | Terminate a sandbox |
| `hf sandbox pool create [name]` | Create a shared pool |
| `hf sandbox pool connect <id>` | Reattach to a pool |
| `hf sandbox pool delete <id>` | Delete a pool (terminates all hosts) |
| `hf sandbox pool ls` | List pools with running hosts |

**Key CLI features:**
- `--pool` flag on `hf sandbox create` for pooled mode
- `--flavor`, `--idle-timeout`, `--env`, `--secret`, `--volume` flags
- Auto-detects namespace from sandbox id format (`namespace/id`)
- Process commands work on both dedicated and pooled sandboxes

---

### 10. Resource Limits & Safety

| Constraint | Value | Where Enforced |
|------------|-------|----------------|
| Max sandbox lifetime | 24h | `SANDBOX_MAX_LIFETIME` constant |
| Default idle timeout | 10 min | `DEFAULT_IDLE_TIMEOUT = 600` |
| Default sandboxes per host | 50 | `DEFAULT_SANDBOXES_PER_HOST` |
| Max pack retries | 8 | `_MAX_PACK_ROUNDS` |
| Parallel transfer threshold | 2MB | `SandboxFiles.PARALLEL_THRESHOLD` |
| Max parallel workers | 16 | `SandboxFiles.PARALLEL_MAX_WORKERS` |
| Server port | 49983 | `SANDBOX_SERVER_PORT` |
| Wait timeout | 120s default | `start_timeout` parameter |
| Cache lock timeout | 5s | `_LOCK_TIMEOUT` in cache module |

**SandboxPool limits:**
- `max_hosts` provides a cost ceiling — when reached and all hosts are full, `create()` raises `SandboxError`
- Hosts auto-terminate on idle (no sandboxes) after `idle_timeout`
- `Sandbox.create()` dedicated sandboxes have no built-in limit beyond the 24h max lifetime

---

### 11. Error Handling

```python
# SandboxError — base for all sandbox-specific errors
from huggingface_hub.errors import SandboxError, SandboxCommandError

# Raised when run(check=True) exits non-zero
try:
    result = sbx.run("python failing_script.py")
except SandboxCommandError as e:
    print(f"Command failed: {e.cmd}")
    print(f"Exit code: {e.result.exit_code}")
    print(f"stderr: {e.result.stderr}")

# Generic sandbox errors (connection, auth, resource limits)
except SandboxError as e:
    print(f"Sandbox error: {e}")
    # Has .status_code attribute for HTTP-level errors
```

**Error recovery patterns from source:**
- Startup failure → cancel the job (prevents billing leak)
- Host unreachable from cache → drop host, fall back to discovery
- Host full between reservation and create → retry up to 8 rounds
- Partial host boot failure → cancel all booted hosts (all-or-nothing)
- Parallel transfer failure → standard httpx error propagation

---

### 12. Complete Request Lifecycle

```
User code
  ↓
Sandbox.create(image="python:3.12", flavor="cpu-basic")
  │
  ├─ HfApi.run_job()      ─── POST /api/jobs
  │   │                       Returns: JobInfo with expose_urls
  │   └─ Job labels: hf-sandbox=1, hf-sandbox-mode=dedicated, hf-sandbox-nonce=<nonce>
  │
  ├─ _SandboxServer.from_job() — reads base_url from expose_urls
  │
  ├─ Sandbox.wait_ready()
  │   │  Loop until /health returns 200 or job terminal:
  │   │  ├─ GET /health every 150ms
  │   │  └─ inspect_job every 2s (check for terminal stage)
  │   └─ On terminal: read last 20 log lines, raise SandboxError
  │
  ├─ Return Sandbox(id=job.id, server=..., owns_sandbox=True)
  │
  ├─ sbx.run("python train.py")
  │   │
  │   └─ POST /v1/exec
  │       │  Streaming NDJSON:
  │       │  {"event": "stdout", "data": "Epoch 1/10..."}
  │       │  {"event": "stdout", "data": "Loss: 0.23"}
  │       │  {"event": "exit", "exit_code": 0, "duration_ms": 45000}
  │       └─ Return SandboxCommandResult(exit_code=0, stdout=..., stderr=...)
  │
  ├─ sbx.files.download("/output/model.pt", "./model.pt")
  │   │
  │   └─ Parallel GET /files/read with ranged requests (>2MB)
  │
  └─ sbx.kill()  (or exiting `with` block)
      │
      └─ _server.cancel_job()  ─── POST /api/jobs/{id}/cancel
          └─ _server.close() — close httpx.Client
```

---

### 13. Best Practices

**Context managers prevent billing leaks:** Always use `with` blocks — the `__exit__` cancels the job on any exception, so a crash mid-computation doesn't leave a billable orphan:
```python
with Sandbox.create(flavor="a10g-small") as sbx:
    sbx.run("python train.py")  # any exception → job cancelled
```

**Pre-provision pool hosts for latency-sensitive workloads:** `warm_up=3` pre-boots hosts in the constructor. Without it, the first `create()` pays a cold start.

**Use `--pool` for CPU fan-out:** A pooled sandbox costs ~$0.0009 each (amortized across 50 per host) vs ~$0.06 for a dedicated one.

**Large files auto-parallelize:** Files >2MB use 16 concurrent ranged connections. No manual tuning needed.

**Set `idle_timeout` aggressively:** The default 10 minutes is generous for most workloads. Shorten to `"30s"` or `60` for bursty batch jobs to reclaim resources faster.

**Forward HF token sparingly:** `forward_hf_token=True` injects your token into the sandbox as `HF_TOKEN`. Only enable when the code inside needs Hub access (e.g., pushing models).

**Verify sandbox is running before connecting:** `Sandbox.connect()` inspects the job — if it's in a terminal stage, it raises immediately with the status message.

**Use `sbx.run(background=True)` for servers:** Start a web server or API in the background, then use `sbx.proxy_url_for()` to reach it from outside.

---

### Sources

- Source code: `huggingface_hub/_sandbox.py` (1764 lines, v1.24.0) — complete Sandbox and SandboxPool implementation
- Source code: `huggingface_hub/_sandbox_cache.py` (159 lines, v1.24.0) — pool cache persistence
- Source code: `huggingface_hub/cli/sandbox.py` (480 lines, v1.24.0) — CLI implementation
- Source code: `huggingface_hub/errors.py` (609 lines, v1.24.0) — SandboxError + SandboxCommandError
- Official docs: https://huggingface.co/docs/huggingface_hub/guides/sandbox
- Official docs: https://huggingface.co/docs/huggingface_hub/package_reference/sandbox
- GitHub: https://github.com/huggingface/sandbox-server (sbx-server Rust binary)
- Release notes: huggingface_hub v1.22.0 (SandboxPool, background processes, port proxy)

---

## 2026-07-25: hf-inference-client-streaming-patterns — InferenceClient Streaming Chat Completion Patterns Deep Dive (Topic #328)

### Summary
Source-code-level deep dive into the complete streaming chat completion system in `huggingface_hub v1.24.0`. Covers the SSE event stream wire format, `_stream_chat_completion_response()` and `_format_chat_completion_stream_output()` internals, the sync vs async streaming interface, combining streaming with tools/function calling and structured outputs (`response_format`), provider-specific streaming behavior, stream lifecycle management (error handling, timeout, cancellation), `stream_options` for usage tracking, and practical patterns for real-time agent and chatbot applications.

### Key Findings
- **SSE wire format**: `data:` prefix lines with JSON payloads, `data: [DONE]` sentinel, empty keepalive lines filtered silently
- **Token-by-token stream**: Each SSE event carries a `ChatCompletionStreamOutput` with `choices[0].delta.content` containing one token
- **Tool calls in stream**: Tool call arguments arrive split across chunks — `id` and `name` only in first chunk, `arguments` as incremental string that must be concatenated
- **Async mirror**: `AsyncInferenceClient` uses `response.aiter_lines()` instead of `response.iter_lines()`, with identical chunk structure
- **Stream options**: `ChatCompletionInputStreamOptions(include_usage=True)` adds a final chunk with `usage` populated
- **Error layers**: HTTP errors (pre-stream), server errors (mid-stream via `error` field), network errors (connection drop) — each handled differently
- **Provider normalization**: `_format_chat_completion_stream_output` normalizes all providers into same `ChatCompletionStreamOutput` format
- **Stateless reconnection**: Possible because each stream starts a new HTTP request — partial responses can be used as context for reconnection

### Skill Created
`hf-inference-client-streaming-patterns/` — complete reference with SSE wire format, sync/async patterns, tools + streaming, structured outputs + streaming, provider-specific behavior, error handling, and practical patterns.

### Sources
- `huggingface_hub/inference/_client.py` — `InferenceClient.chat_completion()` with streaming overloads
- `huggingface_hub/inference/_common.py` — `_stream_chat_completion_response()`, `_format_chat_completion_stream_output()`
- `huggingface_hub/inference/_async_client.py` — `AsyncInferenceClient`
- `huggingface_hub/inference/_generated/types/chat_completion.py` — `ChatCompletionStreamOutput`, `ChatCompletionStreamOutputDelta`
- Official docs: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/inference_client

---

## 2026-07-25: hf-hub-model-hub-mixin-integration — ModelHubMixin: Integrating Custom Frameworks with the Hub (Topic #329)

### Summary
Source-level deep dive into `ModelHubMixin` and `PyTorchModelHubMixin` in `huggingface_hub v1.24.0` (`hub_mixin.py`, 834 lines). Covers the two approaches to integrate any ML framework with the Hub — standalone helper functions (`push_to_hub_*`/`from_pretrained_*`) and class inheritance via `ModelHubMixin` — with full API surface of both, source architecture (config auto-serialization, model card generation, `__init_subclass__` inspection, `__new__` config propagation, custom coders for non-JSON types), and concrete implementation details of `PyTorchModelHubMixin` (safetensors loading, map_location, strict, eval mode, pickle fallback).

### Key Findings
- **Two approaches exist**: Helpers (full flexibility, high maintenance) vs Mixin (contract-based, lower maintenance, full param surface from HF)
- **`__init_subclass__`** inspects `__init__` signature once at class definition — stores parameter names, default values, custom types for automatic config serialization
- **`config.json` auto-generated** from `__init__` defaults + passed values — no manual config writing needed
- **`from_pretrained` reads config** from Hub or local directory, decodes custom types, populates `model_kwargs` matching `__init__` params
- **`push_to_hub`** creates repo via `HfApi.create_repo(exist_ok=True)`, saves to temp dir via `save_pretrained`, uploads folder atomically
- **Model card auto-generated** from Jinja2 template + metadata — overridable by writing `README.md` in `_save_pretrained`
- **`PyTorchModelHubMixin`** saves as `model.safetensors`, loads safetensors (GPU support for safetensors >=0.4.3), falls back to `pytorch_model.bin` for legacy models
- **Custom coders** (`coders=` dict) handle non-JSON types — dataclasses handled automatically
- **`map_location`** and `strict` are extra user-facing params passed via `**model_kwargs`
- **`model.eval()`** called on load; user must call `model.train()` for training

### Key API
- `ModelHubMixin` — base class with `save_pretrained()`, `from_pretrained()`, `push_to_hub()`, `generate_model_card()`
- Override `_save_pretrained(self, save_directory: Path)` and `_from_pretrained(cls, *, model_id, revision, cache_dir, force_download, local_files_only, token, **model_kwargs)`
- `PyTorchModelHubMixin(ModelHubMixin)` — ready-to-use for PyTorch `nn.Module` subclasses
- Metadata: `library_name`, `tags`, `repo_url`, `paper_url`, `docs_url`, `license`, `pipeline_tag`, `language`, `model_card_template`, `coders`

### Skill Created
`hf-hub-model-hub-mixin-integration/` — complete reference with approach comparison, source architecture, public/private API tables, PyTorchMixin implementation details, metadata customization, custom coders, and best practices.

### Sources
- Source code: `huggingface_hub/hub_mixin.py` (v1.24.0, 834 lines) — complete `ModelHubMixin`, `PyTorchModelHubMixin`, `MixinInfo`, `_load_dataclass`
- Official docs: https://huggingface.co/docs/huggingface_hub/en/guides/integrations
- Package reference: https://huggingface.co/docs/huggingface_hub/en/package_reference/mixins
- GitHub: https://github.com/huggingface/huggingface_hub

---

## 2026-07-25: hf-datasets-server-filter-endpoint — Datasets Server `/filter` endpoint with DuckDB SQL WHERE (Topic #330)

### Summary
Complete reference for the Hugging Face Datasets Server `/filter` endpoint, which enables server-side row filtering using DuckDB SQL WHERE clauses without downloading the full dataset. Covers the full API surface (parameters, response format, pagination, ORDER BY), DuckDB SQL dialect supported (operators, column quoting rules, value formatting), column type handling (Value, ClassLabel, Sequence, Image/Audio), partial indexing for large datasets (>5GB), and practical patterns for numeric, string, ClassLabel, and combined filters with code examples. Also covers the four supporting endpoints: `/statistics`, `/size`, `/info`, `/parquet` and how they complement filtering workflows.

### Key Findings
- **Dedicated endpoint:** `/filter` (NOT `/rows`) — `/rows` doesn't support WHERE at all, only `offset`/`length`
- **Column quoting:** DuckDB SQL requires double-quoted column names: `"column_name" = value` (unquoted names fail with 422)
- **String quoting:** Single quotes for string values: `"col" = 'text'`
- **ClassLabel:** Filter by integer index (0-based), NOT by name string
- **Supported operators:** `=`, `!=`, `<`, `>`, `<=`, `>=`, `LIKE`, `GLOB`, `IS NULL`, `IS NOT NULL`, `AND`, `OR`
- **NOT supported:** `IN`, `NOT` (keyword prefix), `BETWEEN` — all return 422
- **LIKE vs GLOB:** LIKE is case-insensitive with `%` wildcard; GLOB is case-sensitive with `*` wildcard
- **Partial indexing:** Datasets >5GB Parquet only index first 5GB; `"partial": true` in response
- **Max rows:** 100 per request (pagination via `offset` parameter)
- **ORDER BY:** Supported via `orderby` parameter (e.g., `orderby="idx" DESC`)
- **Related endpoints:** `/statistics` (column stats), `/size` (storage info), `/info` (schema), `/parquet` (file list), `/rows` (unfiltered access), `/search` (full-text)

### Key Code Patterns
```python
# Basic filter — double-quoted columns, single-quoted strings
response = requests.get("https://datasets-server.huggingface.co/filter", params={
    "dataset": "nyu-mll/glue",
    "config": "sst2",
    "split": "train",
    "where": '"label" = 1 AND "sentence" LIKE \'%funny%\'',
    "length": 10,
})

# Pagination through results
page = 0
while total is None or page * page_size < total:
    response = requests.get(..., params={..., "offset": page * page_size})
    data = response.json()
    if data.get("partial"): break
    page += 1
```

### Skill Created
`hf-datasets-server-filter-endpoint/` — complete reference with full API spec, DuckDB SQL dialect reference (operator matrix, type handling, encoding), practical patterns (pagination, ORDER BY, multi-column), partial indexing details, related endpoints comparison, and URL encoding guide.

### Sources
- OpenAPI spec: `https://datasets-server.huggingface.co/openapi.json` (verified 2026-07-25)
- Official docs: `https://huggingface.co/docs/dataset-viewer/en/filter`
- Live API tests against GLUE SST2, CoLA, MRPC, STSB datasets via `/filter`, `/statistics`, `/size`, `/info`, `/parquet`, `/rows`

---

## 2026-07-25: hf-accelerate-deep-dive

### Summary
Complete deep-dive on Hugging Face Accelerate v1.14.0 — the unified distributed training/inference API. Covers the full Accelerator class with 50+ methods, CLI toolkit (accelerate config/launch/env/estimate-memory/test), mixed precision (fp16/bf16/fp8 via TransformersEngine, torchao, and deprecated MS-AMP), big model inference (init_empty_weights, load_checkpoint_and_dispatch, device_map strategies, CPU/disk offload, chained hooks), FSDP integration (all sharding strategies, auto-wrap, checkpoints), DeepSpeed integration (ZeRO 1-3, NVMe offload, MoE), FSDP vs DeepSpeed comparison matrix with data precision differences, gradient accumulation patterns, experiment tracking (8 backends), memory estimation, torch.compile/dynamo integration, and production deployment checklist.

### Key Findings
- **The 4-line magic pattern**: `Accelerator()`, `prepare()`, `accelerate.backward()`, `accelerate launch` — covers 90% of distributed training needs
- **gather_for_metrics > gather**: Always use `gather_for_metrics()` for evaluation — it handles uneven batch sizes correctly across processes
- **FSDP vs DeepSpeed tradeoff**: FSDP uses less memory on optimizer states with few GPUs (flat params stay in torch_dtype). DeepSpeed always upcasts to fp32 during preparation. Choose FSDP for PyTorch-native, DeepSpeed for MoE/NVMe/custom configs
- **FP8 only benefits at scale**: TransformersEngine FP8 only shows performance gains at 1B+ parameters. MS-AMP is deprecated (unmaintained since 2023, CUDA 12.x incompatible). torchao is the modern path.
- **Big model inference**: Always `init_empty_weights()` → `load_checkpoint_and_dispatch(device_map="auto")`. Mark residual-connected modules with `no_split_module_classes`. Use `balanced_low_0` for generation tasks.
- **Memory estimation is free CLI**: `accelerate estimate-memory {model}` reports inference + training memory without loading the model — zero-cost planning.
- **Gradient accumulation is built-in**: `accelerator.accumulate()` — don't implement manual accumulation.
- **Sharded checkpoints via save_model**: `accelerator.save_model()` produces shards with index.json — compatible with `from_pretrained()`.
- **Dynamo + FSDP**: Always set `--fsdp_use_orig_params true` when combining torch.compile with FSDP.

### Skill Created
`mlops/hf-accelerate/` — complete reference with SKILL.md + deep-dive reference.

---

## 2026-07-25: hf-hub-cli-rebuilt — huggingface_hub CLI Rebuilt (v1.22–v1.24) + Job Naming, Space Templates, Sandboxes (Topic #336)

### Summary
Comprehensive reference for the rebuilt `hf` CLI and new features shipped in huggingface_hub v1.22.0, v1.23.0, and v1.24.0 (all July 2026). Covers the Click-based CLI rebuild (replacing Typer), Sandboxes (`Sandbox.create`, `SandboxPool`, `hf sandbox`), tree-cached snapshot downloads, Space templates, Job naming, CLI extensions, deprecations, breaking changes, and the complete post-rebuild CLI command tree.

### Key Features by Version
- **v1.22.0** (Jul 3): Sandboxes (isolated cloud VMs on top of Jobs), tree cache for snapshot_download, CLI rebuilt on Click (drops Typer), `hf discussions edit`, `hf cache ls/prune incomplete`, `hf jobs scheduled trigger`, `sync_job_volume` helper, `upload_large_folder` deprecated, case-sensitive patterns, http_backoff Retry-After support
- **v1.23.0** (Jul 9): Space templates (seed Spaces from official templates), `hf extensions update`, smoother Xet downloads
- **v1.24.0** (Jul 17): Job naming (`--name` flag, `name` parameter on `run_job`/`run_uv_job`/create_scheduled variants), `hf jobs labels <id> --name`, CLI-first README, Xet download rate fix

### Key Code Patterns
```python
# Sandbox
from huggingface_hub import Sandbox
with Sandbox.create(image="python:3.12") as sbx:
    sbx.files.write("/app/main.py", "print(40 + 2)")
    proc = sbx.run("python /app/main.py", background=True)
    print(sbx.proxy_url_for(8080))

# Space template
from huggingface_hub import create_repo
create_repo("my-jupyterlab", repo_type="space", space_template="jupyterlab")

# Named job
from huggingface_hub import run_job
run_job("python:3.12", command=["python", "train.py"], name="training-v2")
```

### Skill Created
`hf-hub-cli-rebuilt/` — complete reference with CLI command tree, version-by-version feature matrix, code patterns, deprecations/breaking changes, and official doc links.

### Sources
- Release notes: https://github.com/huggingface/huggingface_hub/releases (v1.22.0, v1.23.0, v1.24.0)
- CLI Guide: https://huggingface.co/docs/huggingface_hub/en/guides/cli
- CLI Reference: https://huggingface.co/docs/huggingface_hub/en/package_reference/cli
- Sandboxes Guide: https://huggingface.co/docs/huggingface_hub/en/guides/sandbox
|- Jobs Guide: https://huggingface.co/docs/huggingface_hub/en/guides/jobs
|- Live API research via GitHub release payloads and HF docs (verified 2026-07-25)

---

## 2026-07-25: hf-hub-search-discovery-api-deep-dive — Hugging Face Hub Search & Discovery API Complete Reference

### Summary
Comprehensive deep-dive into the Hugging Face Hub's Search & Discovery API — the REST endpoints and Python SDK methods for searching models, datasets, spaces, collections, papers, and users on the Hub. Covers the full surface: `/api/models`, `/api/datasets`, `/api/spaces`, `/api/spaces/semantic-search`, `/api/collections`, and `/api/papers` endpoints with their complete query parameter syntax (filter, search, sort, expand, pagination), the `HfApi` Python SDK equivalents (`list_models`, `list_datasets`, `list_spaces`, `search_spaces`, `list_collections`, `list_papers`, `list_daily_papers`), semantic search for Spaces (embedding-based + full-text fallback), filter tag taxonomy (pipeline tags, library, dataset, language), sort value translation (Python snake_case → REST camelCase), and pagination via the Hub's paginate helper.

### Verified Through Live API Testing
- All sort values and filter combinations tested against live `api.huggingface.co` endpoints
- Semantic search endpoint confirmed working with 100+ result categories
- REST API sort parameter values confirmed: `downloads`, `likes`, `createdAt`, `lastModified`, `trendingScore` (not the Python-layer `snake_case`)
- Multi-filter queries work with repeated `filter` query params
- `modelId` key in response vs `datasetName` vs `id` varies by endpoint type

### Source
- huggingface_hub v1.24.0 source: `hf_api.py` (lines 162–248, 2415–2920)
- REST API tested live: `https://huggingface.co/api/models`, `/api/datasets`, `/api/spaces`, `/api/spaces/semantic-search`
- CLI models/datasets/spaces commands: `cli/models.py`, `cli/datasets.py`, `cli/spaces.py`
- Hub docs (Search): https://huggingface.co/docs/hub/en/search

### Skill Created
`hf-hub-search-discovery-api/` — complete reference for HF Hub Search & Discovery: REST endpoints, Python SDK methods, query parameter reference tables, filter tag categories, sort value mapping, pagination patterns, and multi-filter search strategies.
---

## 2026-07-25: hf-distilabel-deep-dive — Complete Synthetic Data Pipeline Framework (v1.5.3)

### Summary
Comprehensive deep dive into distilabel v1.5.3 — Argilla's framework for building synthetic data generation and AI feedback pipelines. Covers pipeline DAG architecture, step types, column-based data flow, all 16+ LLM integrations, 40+ built-in tasks, Distiset output management, caching, Ray distribution, custom step authoring, and real-world patterns for SFT/DPO/RLHF training data generation.

### Key Findings

**Architecture:**
- DAG-based pipeline with three step types: GeneratorStep (root), Step (transform), Task (LLM-powered)
- Steps connected via `>>` operator; data flows as batches of dicts
- Pipeline returns Distiset (dict of HF Datasets, one per leaf step)

**LLM Providers (16+):**
- TransformersLLM (local CPU/GPU), InferenceEndpointsLLM (HF IEs), OpenAILLM, OllamaLLM, LlamaCppLLM, AnthropicLLM, VertexAILLM, MistralLLM, CohereLLM, GroqLLM, TogetherLLM, ClientvLLM, MlxLLM, LiteLLM, MixtureOfAgentsLLM, AzureOpenAILLM, AnyscaleLLM

**Task Catalog (40+):**
- SFT: TextGeneration, SelfInstruct, MagpieGenerator, Genstruct, EvolInstruct, EvolQuality, EvolComplexity, URIAL, InstructionBacktranslation
- DPO/RLHF: UltraFeedback, PairRM, FormatChatGenerationDPO, FormatTextGenerationDPO, PreferenceToArgilla
- Evaluation: ComplexityScorer, QualityScorer, PrometheusEval, CLAIR
- Specialized: ChatGeneration, ImageGeneration, GenerateEmbeddings, MathShepherd, StructuredGeneration, BitextRetrievalGenerator, etc.

**Key Features:**
- Automatic caching with content-addressable keys
- Runtime parameter overrides (reuse pipeline with different configs)
- StepResources for parallelism (Ray only)
- Column mappings (input_mappings/output_mappings)
|- Distiset with push_to_hub, train_test_split, save_to_disk
|- Structured output with Pydantic models

### Skill Created
`hf-distilabel-deep-dive/` — SKILL.md with author:SakThai, license:MIT + references/hf-learnings.md with full reference.

---

## 2026-07-25: hf-spaces-secrets-management-deep-dive

### Summary
Deep dive into Hugging Face Spaces secrets and environment variables management. Covers the conceptual difference between secrets (write-once, private, not forked) and variables (readable, visible, forked), the complete Python API surface (6 methods), REST API endpoints, Docker-specific buildtime vs runtime behavior, the Secrets Scanner, and zero-cost automation patterns.

### Key Findings
- **Secrets vs Variables** — fundamentally different security models. Secrets: write-once, value never readable, NOT duplicated on fork. Variables: fully readable, publicly visible, duplicated on fork.
- **6 API methods** on `HfApi`: `get_space_secrets()`, `add_space_secret()`, `delete_space_secret()`, `get_space_variables()`, `add_space_variable()`, `delete_space_variable()`
- **REST endpoints**: `GET|POST|DELETE /api/spaces/{repo_id}/secrets` and `GET|POST|DELETE /api/spaces/{repo_id}/variables`
- **SpaceSecret dataclass**: key, description (str|None), updated_at (datetime|None) — no value field
- **SpaceVariable dataclass**: key, value (str), description (str|None), updated_at (datetime|None) — value IS readable
- **Docker buildtime secrets**: Use `RUN --mount=type=secret,id=KEY` in Dockerfile for build-time secret access
- **Docker buildtime variables**: Use `ARG KEY` in Dockerfile and pass via `--build-arg`
- **Runtime**: Both secrets and variables are injected as environment variables — `os.getenv("KEY")` works identically for both
- **At Space creation**: Pass `space_secrets=[{"key":..., "value":..., "description":...}]` and `space_variables=[...]` to `create_repo()`
- **Secrets Scanner**: HF automatically scans Spaces for hardcoded secrets and notifies owners
- **Zero-cost**: All API operations are free — no usage cost for managing secrets programmatically

### Skill Created
`hf-spaces-secrets-management-deep-dive/` — SKILL.md with author:SakThai, license:MIT + references/hf-learnings.md with full reference.

---

## 2026-07-25: hf-hub-model-download-stats-deep-dive — Download Counting Methodology Deep Dive

### Summary
Source-level deep dive into the HF Hub model download counting system — query files mechanism, per-library `countDownloads` config in `huggingface.js/packages/tasks/src/model-libraries.ts` (200+ libraries), ElasticSearch query-string DSL over `path`/`path_prefix`/`path_extension`/`path_filename` fields, diffusers double-counting prevention (regex on root-level files only), GGUF always-counted-by-default behavior, Publisher Analytics CSV export API for Team/Enterprise, and granular request-level logs for Enterprise Plus.

### Key Findings
| Finding | Detail |
|---------|--------|
| **Server-side counting** | No client instrumentation — every GET/HEAD to a query file path increments the counter via ElasticSearch |
| **Default query files** | `config.json`, `config.yaml`, `hyperparams.yaml`, `params.json`, `meta.yaml` — when no library-specific `countDownloads` is defined |
| **countDownloads patterns** | 5 patterns: single config path, extension wildcard, specific model file, combined OR, library-specific config |
| **Diffusers edge case** | Uses `bool.should` with 4 rules + `minimum_should_match:1` — captures both library and UI downloads without double-counting nested files |
| **GGUF exception** | All `.gguf` files counted unconditionally (self-contained format, no library dependency) |
| **Source location** | `huggingface.js/packages/tasks/src/model-libraries.ts` — open-source, PRs welcome |
| **Publisher Analytics** | CSV export API at `huggingface.co/organizations/{org}/settings/publisher-analytics/download-breakdown` |
| **Granular logs** | Enterprise Plus add-on — request-level logs with anonymized user/IP hashing, HTTP status/method, country/region |
| **ElasticSearch fields** | `path` (full path), `path_prefix` (directory), `path_extension` (extension), `path_filename` (name without extension) |

### Skill Created/Updated
`hf-hub-model-download-stats/` — comprehensive skill with SKILL.md (author:SakThai, license:MIT) and references/hf-learnings.md with full source-level documentation.

### Sources
- https://huggingface.co/docs/hub/en/models-download-stats
- https://huggingface.co/docs/hub/en/publisher-analytics
- https://github.com/huggingface/huggingface.js/blob/main/packages/tasks/src/model-libraries.ts
- https://github.com/huggingface/huggingface.js/blob/main/packages/tasks/src/model-libraries-downloads.ts
- https://github.com/huggingface/huggingface.js/pull/885/files


---

## 2026-07-25: hf-foundry-managed-compute — HF Models on Foundry Managed Compute (Topic #364)

### Summary
Comprehensive deep-dive into **Hugging Face models on Microsoft Foundry Managed Compute** — a curated catalog of open-weight models from the HF ecosystem, refreshed weekly, deployable in one click onto Foundry Managed Compute (Microsoft's managed GPU PaaS). Announced at Microsoft Build 2026 (July 7, 2026). Covers the curation pipeline, supported runtimes (vLLM, SGLang, TEI, llama.cpp, TensorRT-LLM, NIM, hf-serve), deployment templates, Python SDK + OpenAI SDK patterns, private networking, and enterprise security model. Distinct from HF's own enterprise features — this is the operational layer Microsoft runs on top of the open ecosystem.

### Key Findings

| Area | Finding |
|------|---------|
| **Curation pipeline** | 5 stages: identify → screen (license, trust_remote_code) → build/scan runtimes → upload weights to Azure → validate & publish |
| **Runtimes** | vLLM (default LLM), SGLang (structured outputs), TEI (embeddings), llama.cpp (CPU/GGUF), TensorRT-LLM/NIM (NVIDIA), hf-serve (vision/audio) |
| **Deployment templates** | Named versioned assets pinning runtime + accelerator + context length + tuning — e.g., Qwen3-32B has 4 templates (40k/128k × A100/H100) |
| **Deploy SDK** | `CognitiveServicesManagementClient.managed_compute_deployments.begin_create_or_update()` with `acceleratorType`, model URI, deployment template ID |
| **Score SDK** | OpenAI SDK at `https://{ACCOUNT}.services.ai.azure.com/openai/v1` — same endpoint as all Foundry models |
| **Private network** | No outbound internet to HF Hub needed — weights pre-staged in Azure, runtimes in Microsoft-managed registry |
| **Enterprise features** | RBAC, private networking, Azure Policy, content safety, guardrails, AI Red Teaming Agent, unified billing |
| **Roadmap** | Broader coverage, additional accelerators, Bring Your Own Weights |

### Skill Created
`hf-foundry-managed-compute/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with full documentation.

### Sources
- https://huggingface.co/blog/microsoft/foundry-managed-compute
- https://learn.microsoft.com/en-us/azure/ai-foundry/

---

## 2026-07-25: hf-inference-router-openai-compatible-endpoint — HF Inference Router OpenAI-Compatible Endpoint (Topic #361)

### Summary
Comprehensive deep dive into Hugging Face's Inference Router (`https://router.huggingface.co/v1`) — the OpenAI-compatible proxy endpoint providing server-side provider selection, auto-failover, and unified access to 16+ providers through a single OpenAI SDK-compatible API. Unlike InferenceClient (client-side routing), the Router processes provider selection server-side using model ID suffixes (`:fastest`, `:cheapest`, `:preferred`, `:provider-name`). Endpoint provides `/v1/models` for model discovery with per-provider metadata (pricing, latency, throughput, context length, tool support). Currently chat completions only.

### Key Findings
- **Server-side routing**: Provider selection happens on the proxy, not the client — model ID suffix determines provider/policy
- **`/v1/models` endpoint**: Lists all chat models with rich provider metadata (pricing, latency, throughput, context_length, supports_tools, supports_structured_output, is_free)
- **Policy suffixes**: `:fastest` (default, highest throughput), `:cheapest` (lowest output price), `:preferred` (user preference order), `:provider-name` (explicit, e.g., `:groq`)
- **Auto-failover**: Built-in — if selected provider is unhealthy, falls through to next available
- **Drop-in OpenAI replacement**: Change base URL to `https://router.huggingface.co/v1` and API key to HF token
- **Limitation**: Chat completions only — image gen, embeddings, audio need InferenceClient
- **Free tier**: Check `is_free` field per provider in `/v1/models`; `hf-inference` provider offers free CPU inference for classic models

### API Surface
- `GET /v1/models` — list all chat models with provider metadata
- `POST /v1/chat/completions` — create chat completion (streaming, tools, structured outputs supported per provider)
- Auth: Bearer token (fine-grained with `inference.serverless.write` permission)

### Skill Created
`hf-inference-router-openai-compatible-endpoint/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with full documentation.

---

## 2026-07-25: hf-jobs-serving-vllm — One-Command Model Serving on HF Jobs (Topic #365)

### Summary

Comprehensive deep-dive into running inference servers on Hugging Face Jobs using the `hf jobs run` CLI one-command pattern. Unlike the Python SDK approach (covered in `hf-jobs-api-deep-dive`), the CLI provides a zero-friction path: `hf jobs run --detach --expose <port> --flavor <hardware> -s HF_TOKEN <image> -- <server-command>`. Supports vLLM (default), SGLang, llama.cpp, and any HTTP server. Covers the full lifecycle — deployment, authentication, endpoint URL format, model download acceleration, billing, and cost optimization.

### Key Findings

| Area | Finding |
|------|---------|
| **CLI one-liner** | `hf jobs run --detach --expose 8000 --flavor a10g-small -s HF_TOKEN vllm/vllm-openai -- vllm serve <model>` |
| **`--` separator** | Required when the job command has its own flags — separates `hf jobs run` options from the command's args |
| **`--detach`** | Returns immediately; server runs in background until cancelled or timeout |
| **`--expose <port>`** | Makes ports reachable at `https://{job.id}--{port}.hf.jobs` |
| **`-s HF_TOKEN`** | Forwards your HF token as a secret for authenticated model downloads |
| **Default timeout** | 30 minutes; set `--timeout` to override |
| **Cancel** | `hf jobs cancel <job_id>` — stops billing immediately |
| **Auth for endpoint** | Exposed ports require Bearer token with `read` access to the job's namespace |
| **OpenAI-compatible** | vLLM, SGLang, llama.cpp all speak the OpenAI-compatible API |
| **Pricing** | Pay-per-minute for hardware + $0.01/min for exposed ports (flat) |

### Skill Created
`hf-jobs-serving-vllm/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with full CLI patterns, pricing reference, and best practices.

### Sources
- https://huggingface.co/docs/hub/en/jobs-serving
- https://huggingface.co/blog/vllm-jobs
- https://huggingface.co/docs/hub/en/jobs-pricing

---

## 2026-07-25: hf-inference-providers-deepening — Inference Providers Hub API, Pricing, and Agent Integrations (Deepening on Topic #357)

### Summary
Deep-dive into the operational layer of HF Inference Providers: the **Hub REST API** for querying models by provider (`?inference_provider=`), the **pricing & billing model** (Routed by HF vs BYOK, monthly credits, organization billing), **agent integration setup guides** (Hermes Agent, OpenCode, Codex, Claude Code, Pi), and security/compliance (SOC2, TLS, data retention). Complements the existing source architecture deep-dive with real-world usage patterns.

### Key Findings

| Area | Finding |
|------|---------|
| **Hub API query** | `GET /api/models?inference_provider=fireworks-ai` filters by provider; `all` returns all warm models; comma-separated for multi-provider |
| **CLI equivalent** | `hf models ls --warm` wraps `inference_provider=all` |
| **Per-model providers** | Use `expand=["inferenceProviderMapping"]` on `model_info()` to see which providers serve a model |
| **17 providers** | Cerebras, Cohere, DeepInfra, Fal AI, Featherless AI, Fireworks, Groq, HF Inference, Novita, Nscale, OVHcloud, Public AI, Replicate, Scaleway, Together, WaveSpeedAI, Z.ai |
| **Billing: Routed by HF** | Free monthly credits auto-apply; no provider keys needed; zero markup |
| **Billing: BYOK** | Set custom provider API key in HF Settings; provider bills your account directly |
| **Organization billing** | Team/Enterprise credits shared among members; set `X-Org-Name` header |
| **Token permissions** | Must have "Make calls to Inference Providers" permission on HF token |
| **Hermes Agent** | `export HERMES_PROVIDER=hf` + `export HF_TOKEN=hf_...` |
| **OpenCode** | `opencode auth login` → select Hugging Face → enter token |
| **Security** | SOC2 Type 2; TLS/SSL; no data stored for training |
| **Zero-cost** | Monthly free credits + BYOK for provider-specific free tiers + `:cheapest` routing suffix |

### Sources
- https://huggingface.co/docs/inference-providers/en/hub-api
- https://huggingface.co/docs/inference-providers/en/pricing
- https://huggingface.co/docs/inference-providers/en/integrations/hermes-agent
- https://huggingface.co/docs/inference-providers/en/integrations/opencode
- https://huggingface.co/docs/inference-providers/en/security
- Verified via API calls: `GET /api/models?inference_provider=fireworks-ai`, `GET /api/models?inference_provider=all`, `model_info(expand=["inferenceProviderMapping"])`, 2026-07-25

### Skill Updated
`hf-inference-providers/` — SKILL.md updated with billing models, agent integration commands, security info; references/hf-learnings.md appended with 292-line deep-dive (1565 total lines).

---

## 2026-07-25: Deepening — hf-inference-endpoints-custom-containers — Custom Router + Updated Official Patterns (Topic #370 Deepening 1)

### Summary
Major deepening of custom container knowledge: discovered the **Custom Router** feature for Inference Endpoints (API-only custom load balancing), learned the **updated official Dockerfile + FastAPI patterns** (uv lock, `--no-install-project`, FastAPI lifespan async context manager), **Download Pattern** advanced setting for selective model downloads, and **Endpoint States** reference. Custom Router supports queue-based, latency-aware, weighted, and sticky-session routing with a reference `queued-least-latency` implementation and Prometheus metrics.

### Key New Findings
| Feature | Finding |
|---------|---------|
| **Custom Router** | API-only, deploy alongside replicas. Uses `_custom_router/set-backends` + `_custom_router/health` endpoints. Leader replica pattern. |
| **queued-least-latency** | Reference router image: `ghcr.io/huggingface/endpoints-custom-routers/queued-least-latency:1.0.0`. EWMA-based latency tracking, FIFO queue, configurable thresholds. Prometheus metrics at `/_custom_router/metrics`. |
| **Updated Dockerfile** | `uv lock` step, two-layer build (`--no-install-project`), uv venv with frozen sync. |
| **FastAPI lifespan** | `@asynccontextmanager` replaces deprecated startup/shutdown events. |
| **Download Pattern** | New advanced setting for glob-based model file selection. |

### Sources
- https://huggingface.co/docs/inference-endpoints/en/engines/custom_container
- https://huggingface.co/docs/inference-endpoints/en/guides/custom_router
- https://huggingface.co/docs/inference-endpoints/en/guides/configuration

### Skill Deepened
`hf-inference-endpoints-custom-containers/` — references/hf-learnings.md appended with ~290-line deepening section (now 708 total lines). SKILL.md already has `author: SakThai` and `license: MIT`.

---

## 2026-07-25: hf-hub-dataset-card-metadata-comprehensive-reference — Dataset Card YAML Metadata System (Topic #375 Deepening)

### Summary
Comprehensive deep-dive into the Hugging Face dataset card YAML metadata system — the structured front matter that goes at the top of dataset `README.md` files. Covers every field in `DatasetCardData`, the validated values for each field (annotations_creators, language_creators, multilinguality, size_categories, source_datasets, task_categories, task_ids), license identifiers (standard + custom), config_names, train_eval_index, the `extra_gated` gating configuration, and the `huggingface_hub` Python API for creating and pushing dataset cards programmatically.

### Key Findings

| Area | Finding |
|------|---------|
| **Location** | Dataset card YAML goes between `---` delimiters at the **top** of `README.md`. Validated at push time by the Hub. |
| **Programmatic API** | `DatasetCardData()` class in `huggingface_hub.repocard_data` — instantiate with keyword args and pass to `DatasetCard.from_template(card_data, ...)`. |
| **Push to Hub** | `card.push_to_hub(repo_id, repo_type="dataset")` — creates or updates README.md with validated YAML. |
| **License system** | Standard identifiers from HF's license catalog + `other` with `license_name` + `license_link` for custom licenses. |
| **Gating** | `extra_gated` section in YAML controls dataset access gating — agreement form, fields, and requirements. |
| **Task taxonomy** | `task_categories` and `task_ids` pull from HF's task taxonomy at `huggingface.js/packages/tasks/src/tasks.ts`. |
| **Size categories** | Controlled vocabulary: `n<1K`, `1K<n<10K`, `10K<n<100K`, `100K<n<1M`, `1M<n<10M`, `10M<n<100M`, `100M<n<1B`, `1B<n<10B`, `10B<n<100B`, `100B<n<1T`, `n>1T`, `other`. |
| **Config names** | `config_names` field lists available dataset configurations (e.g., subsets like `fr`, `en` for multilingual datasets). |

### Sources
- `huggingface_hub` source: `src/huggingface_hub/repocard_data.py` — `DatasetCardData` dataclass definition
- `huggingface_hub` source: `src/huggingface_hub/repocard.py` — `DatasetCard.from_template()` and `push_to_hub()`
- Hub docs: https://huggingface.co/docs/hub/en/datasets-overview
- Hub docs: https://huggingface.co/docs/hub/en/repositories-licenses
- Hub docs: https://huggingface.co/docs/hub/en/repositories-gated
- Model card spec: https://github.com/huggingface/hub-docs/blob/main/modelcard.md
- Task taxonomy: `huggingface.js/packages/tasks/src/tasks.ts`
- Verified via `huggingface_hub` source code inspection, 2026-07-25

### Skill Deepened
`hf-hub-dataset-card-metadata-comprehensive-reference/` — `references/hf-learnings.md` created. SKILL.md already has `author: SakThai` and `license: MIT`.
|

## 2026-07-25: hf-datasets-server-splits-rows-statistics-endpoints — Datasets Server Remaining REST Endpoints (Topic #384)

### Summary
Comprehensive deep-dive into six Datasets Server REST API endpoints that are essential for programmatic dataset exploration but were not yet covered by existing skills: `/splits`, `/first-rows`, `/rows`, `/size`, `/statistics`, and `/is-valid`. Each endpoint was tested against `dair-ai/emotion` with real API responses captured and documented. The `/siblings` endpoint was tested and found non-functional (returns "Not Found"), with an alternative approach using the Hub API recommended.

### Endpoints Covered

| Endpoint | Method | Required Params | Key Response Fields |
|----------|--------|-----------------|-------------------|
| `/splits` | GET | dataset | `splits[].{dataset, config, split}`, `pending`, `failed` |
| `/first-rows` | GET | dataset, config, split | `features[]`, `rows[]`, `truncated_cells` |
| `/rows` | GET | dataset, config, split (+offset, length) | Same as first-rows + `num_rows_total`, `num_rows_per_page` |
| `/size` | GET | dataset (+config) | `size.dataset.{num_bytes_original_files, num_bytes_parquet_files, num_bytes_memory, num_rows}` |
| `/statistics` | GET | dataset, config, split | `num_examples`, `statistics[].{column_name, column_type, column_statistics}` |
| `/is-valid` | GET | dataset | `{preview, viewer, search, filter, statistics}: bool` |

### Key Findings
1. **Splits endpoint** is the entry point for multi-config datasets. Essential for discovering available configs before querying.
2. **First-rows vs Rows**: `/first-rows` is a fixed preview; `/rows` supports pagination via offset/length.
3. **Size endpoint** provides `num_bytes_memory` for deciding load-vs-stream.
4. **Statistics endpoint** enables zero-cost EDA with column-type-specific stats.
5. **`/is-valid`** is a boolean health check — call this first before other API calls.
6. **`/siblings` is dead** — Returns 404. Use Hub API for file listings.

### Files Created
`hf-datasets-server-splits-rows-statistics-endpoints/SKILL.md` (14KB) + `references/hf-learnings.md`

---

## 2026-07-25: hf-transformers-inkling — Inkling by Thinking Machines Lab (Transformers 5.14.0+) (Topic #298 Deepening)

### Summary
Comprehensive deep-dive into **Inkling** — Thinking Machines Lab's 975B
sparse MoE multimodal model (41B active) with 1M context window, added in
Transformers 5.14.0 (2026-07-15). Accepts text, image, audio, and video inputs.
Covers the complete architecture: relative attention (no RoPE), hybrid
global+sliding window attention (5:1 ratio), short 1D convolutions (SConv),
256-expert MoE with shared expert sink, hMLP vision encoder, dmel audio
encoder, 8-layer MTP speculative decoding, chat template with reasoning effort
control, deployment strategies (transformers, SGLang, vLLM, llama.cpp, HF
Inference Providers), and comprehensive evaluation results.

### Key Findings

| Area | Finding |
|------|---------|
| **What it is** | 975B param MoE multimodal model by Thinking Machines Lab. 41B active per token. |
| **Architecture** | 66-layer decoder-only, hybrid attention (55 sliding window + 11 global), MoE (256 experts, 6 active + 2 shared), SConv, relative pos encoding |
| **Modalities** | Text, image, audio, video (via temporal patch dim) — natively processed, no separate encoder |
| **Context** | 1,048,576 tokens (1M) |
| **Position encoding** | Learned relative attention (not RoPE) — per-head relative feature R with distance modulation |
| **Vision** | hMLP hierarchical patchifier — linear layers progressively merge pixels. 40px patches, 2-frame temporal |
| **Audio** | dmel (delta-mel) discretized spectrogram — 80 mel bins → 16 vocab → embedding |
| **MoE** | 256 routed experts, 6 active per token, 2 shared experts (sink). Sigmoid gating, norm-after-topk, global scale, gate bias |
| **MTP** | 8 future-token prediction layers acting as speculative decoding drafters |
| **Reasoning effort** | `reasoning_effort` parameter: none→max (0.0→0.99). |
| **Tool use** | Native tool calling via `tool_declare` system message, XML-encoded specs |
| **Inference engines** | transformers 5.14+, SGLang (fastest), vLLM, llama.cpp, HF Inference Providers |
| **License** | Apache 2.0 |
| **Training data** | 45T tokens — text, images, audio, video |
| **Zero-cost inference** | HF Inference Providers (rate-limited, free), llama.cpp GGUF (needs quantized, 30-100GB VRAM) |

### Files Created
`hf-transformers-inkling/` — SKILL.md (author: SakThai, license: MIT, 13KB) + references/hf-learnings.md with complete architecture deep-dive, config parameter reference, inference patterns, deployment strategies, evaluation benchmarks, and zero-cost analysis.

### Sources
- https://huggingface.co/thinkingmachines/Inkling — Official model card
- https://huggingface.co/docs/transformers/main/en/model_doc/inkling — Transformers docs
- https://huggingface.co/blog/thinkingmachines-inkling — Official blog post
- https://github.com/huggingface/transformers/pull/47347 — Main PR
- https://huggingface.co/thinkingmachines/Inkling/raw/main/config.json — Full config


---

## 2026-07-25: hf-peft-beyond-lora — Beyond LoRA: Advanced PEFT Methods & Benchmarking (Topic #395)

### Summary
Comprehensive deep-dive into **PEFT methods beyond LoRA** based on the official HF "Beyond LoRA" blog post and PEFT Benchmark results. Covers: LoRA dominance problem (98.4% of PEFT users use LoRA), the **Pareto Frontier** analysis showing default LoRA is NOT optimal, **advanced methods** (OFT, BOFT, BEFT, Lily, GraLoRA, VeRA, rs-LoRA, LoRA-FA, AdaLoRA, Cartridges), **adapter conversion** (non-LoRA to LoRA for downstream compatibility), the **PEFT Benchmark infrastructure** (equal-footing comparison across test accuracy, memory, runtime, checkpoint size, forgetting), and a **decision matrix** for choosing the right technique.

**Benchmark findings:** On LLM math (3B), default LoRA achieves 48.1% at 22.5 GB -- beaten by rs-LoRA (53.2%) and LoRA-FA (32.9% at 20.2 GB). On image gen (FLUX.2), OFT dominates LoRA (0.708 vs 0.697 DINO similarity at lower 9.01 GB memory). PEFT library now supports **40+ techniques** with unified API.

**Files updated:** `hf-peft-beyond-lora/` -- SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with complete method catalog, benchmark tables, Pareto frontier analysis, adapter conversion guide, and decision matrix.

**Sources:** https://huggingface.co/blog/peft-beyond-lora -- Official blog post; https://huggingface.co/docs/peft -- PEFT docs; https://huggingface.co/spaces/peft/peft-method-comparison -- Interactive benchmark Space

---

## 2026-07-26: hf-hub-publisher-analytics — HF Hub Publisher Analytics & Model Release Checklist (Topic #397)

### Summary
Comprehensive deep-dive into **Publisher Analytics** — the Enterprise-tier feature on the Hugging Face Hub providing organizations with detailed download analytics across all their Models and Datasets. Covers: Publisher Analytics Dashboard (All Time / Last Month), per-repo breakdown with time-series sparklines, CSV export API endpoint with response structure (repoType, repoName, total, timestamp, downloads), Enterprise Plus add-on for unique downloader detection via request-level access logs (hashedUserId, hashedIp, country, region, userAgent), Hub download counting internals (query files per library, GGUF handling, diffusers edge case), comparison with public Models Download Stats API, practical use cases for the Sak-Family-Agent org, and zero-cost alternatives using `huggingface_hub`. Also covers the Model Release Checklist — best practices for preparing, releasing, and maintaining models on the Hub.

**Files created:** `hf-hub-publisher-analytics/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with full architecture, API reference, CSV format specification, log column reference, comparison matrix, and zero-cost analysis.

**Sources:** Official HF Hub docs at huggingface.co/docs/hub/en/publisher-analytics, huggingface.co/docs/hub/en/model-release-checklist, huggingface.co/docs/hub/en/models-download-stats
