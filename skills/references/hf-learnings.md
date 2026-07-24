# HF Learnings Log

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
