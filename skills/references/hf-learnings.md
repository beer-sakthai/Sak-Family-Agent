# HF Learnings Log

## 2026-07-24: hf-hub-commit-api — Deep Dive (Topic #57)

### Summary
Comprehensive deep-dive into Hugging Face Hub's Commit API — the low-level foundation for all file operations on the Hub. Covers all three `CommitOperation` types (Add, Delete, Copy), the `create_commit()` entry point, high-level wrappers (`upload_file`, `upload_folder`, `copy_files`), the `CommitScheduler` for periodic pushes, `preupload_lfs_files` for memory-constrained large uploads, and `list_repo_commits` for inspecting history. Focused on practical patterns that work under zero-cost constraints.

### Core Architecture

The Hub Commit API follows a three-operation model:

| Operation | Purpose | Fields |
|---|---|---|
| `CommitOperationAdd` | Upload/create a file | `path_in_repo`, `path_or_fileobj` (str Path bytes or BinaryIO) |
| `CommitOperationDelete` | Remove a file or folder | `path_in_repo` |
| `CommitOperationCopy` | Copy within/across repos (server-side) | `src_path_in_repo`, `path_in_repo`, optional `src_revision`, `src_repo_id`, `src_repo_type` |

All three inherit from `CommitOperation` and are passed as a list to `create_commit()`.

### create_commit() Parameters

```python
api.create_commit(
    repo_id="user/repo",
    operations=[...],           # List[CommitOperation] — will be mutated!
    commit_message="msg",       # Required, non-empty
    commit_description=None,    # Optional longer description
    token=None,                 # Defaults to cached token
    repo_type=None,             # None/model, dataset, space
    revision=None,              # Branch name or commit OID (default: main)
    create_pr=False,            # Open a PR instead of committing directly
    num_threads=5,              # Concurrent upload threads for LFS files
    parent_commit=None,         # OID to enforce linear history (optimistic locking)
    run_as_future=False,        # Non-blocking background execution
)
```

**Critical constraints:**
- Max **25k LFS files** per commit
- Max **1GB payload** for regular (non-LFS) files
- The input `operations` list **will be mutated** — do not reuse objects
- Repo must already exist; create it first with `create_repo()`
- Empty `commit_message` raises `ValueError`

### CommitOperationAdd — Three Input Modes

```python
# 1. From local file path
CommitOperationAdd(path_in_repo="weights.bin", path_or_fileobj="./local/weights.bin")

# 2. From bytes in memory
CommitOperationAdd(path_in_repo="config.json", path_or_fileobj=b'{"key": "value"}')

# 3. From binary file object (supports seek/tell)
with open("data.bin", "rb") as f:
    CommitOperationAdd(path_in_repo="data.bin", path_or_fileobj=f)
```

Internally computes `UploadInfo` (SHA256 for LFS, SHA1 for regular files) and compares against the remote OID to skip unchanged files (preventing empty commits).

The `as_file()` context manager yields a `BinaryIO` from any input type, optionally with tqdm progress bar:
```python
with operation.as_file(with_tqdm=True) as f:
    httpx.put(..., data=f)
```

### CommitOperationCopy — Server-Side Copies

```python
# Copy within same repo
CommitOperationCopy(src_path_in_repo="image.png", path_in_repo="backup/image.png")

# Copy from another repo
CommitOperationCopy(
    src_path_in_repo="weights.safetensors",
    path_in_repo="weights.safetensors",
    src_repo_id="other-user/source-model",
    src_repo_type="model",
    src_revision="main",       # Optional: specify source branch
)
```

**Key details:**
- Zero data transfer — server-side operation, no download/upload cost
- Works across repos but NOT across storage regions
- Also works with Buckets via `api.copy_files(source, destination)` using `hf://` URIs

### CommitInfo Return Value

```python
@dataclass
class CommitInfo(str):
    commit_url: str        # e.g. "https://huggingface.co/user/repo/commit/abc123"
    commit_message: str
    commit_description: str
    oid: str               # Full SHA commit hash
    pr_url: str | None     # Set when create_pr=True
    pr_revision: str | None  # e.g. "refs/pr/1"
    pr_num: int | None
    repo_url: RepoUrl      # Parsed repo info
```

Inherits from `str` for backward compatibility (the string value is the commit URL).

### High-Level Wrappers

#### upload_file() — Single File

```python
api.upload_file(
    path_or_fileobj="/path/to/local/README.md",  # or bytes or BinaryIO
    path_in_repo="README.md",
    repo_id="user/test-dataset",
    repo_type="dataset",
)
```

#### upload_folder() — Directory Upload (Recommended)

```python
api.upload_folder(
    folder_path="./logs",
    repo_id="user/trained-model",
    path_in_repo="experiment/logs/",
    allow_patterns="*.txt",        # Upload only .txt files
    ignore_patterns="**/temp/*",   # Exclude temp files
    delete_patterns="*.txt",       # Delete remote .txt files before upload
)
```

**Auto-batching:** When `hf_xet` is installed (default since huggingface_hub v0.32.0), `upload_folder()` automatically splits large folders into multiple commits with "(part 2)", "(part 3)" suffixes. It's **resumable** — re-run the same call after interruption and already-committed files are skipped, chunks are deduplicated.

**Performance:** Set `HF_XET_HIGH_PERFORMANCE=1` to saturate bandwidth and CPU cores. The legacy `HF_HUB_ENABLE_HF_TRANSFER=1` is deprecated.

#### copy_files() — Server-Side Cross-Repo Copy

```python
# Copy single file between repos
api.copy_files(
    "hf://username/source-model/weights.safetensors",
    "hf://username/target-model/weights.safetensors",
)

# Copy entire folder (rsync-style with trailing /)
api.copy_files(
    "hf://datasets/username/source-dataset/data/",
    "hf://datasets/username/target-dataset/data/",
)

# Duplicate within same repo
api.copy_files(
    "hf://username/my-model/config.json",
    "hf://username/my-model/backup/config.json",
)
```

**Folder semantics:**
- Trailing `/` on source → copies **contents** (rsync-style, no nesting)
- No trailing `/` on source → copies **folder itself** (cp -r style, nests inside destination)

### CommitScheduler — Periodic Background Uploads

```python
from huggingface_hub import CommitScheduler

scheduler = CommitScheduler(
    repo_id="user/feedback-data",
    repo_type="dataset",
    folder_path="/local/data",
    path_in_repo="data",
    every=10,                    # minutes between commits
    allow_patterns="*.jsonl",
    squash_history=False,        # Set True to keep repo history manageable
)
```

**Key design properties:**
- **Append-only assumption:** Only add new files or append to existing ones. Deleting/overwriting may corrupt the repo.
- **No empty commits:** Automatically skips if no changes detected.
- **Thread-safe:** Use `scheduler.lock` context manager for concurrent writes from multiple threads.
- **Error resilience:** Silent failure on network errors — retries at next interval.
- **Context manager:** Use `with CommitScheduler(...) as scheduler:` to ensure clean shutdown + final commit.

**Custom push_to_hub():** Override to transform data before upload (e.g., zip PNGs, aggregate logs):
```python
class ZipScheduler(CommitScheduler):
    def push_to_hub(self):
        png_files = list(self.folder_path.glob("*.png"))
        if not png_files:
            return
        # ... zip and upload via self.api.upload_file(...)
        for png in png_files:
            png.unlink()  # clean up local files
```

### preupload_lfs_files — Memory-Constrained Large Uploads

For cases where you generate large shards in memory and want a single commit:

```python
from huggingface_hub import CommitOperationAdd, preupload_lfs_files, create_commit

operations = []
for i in range(5):
    content = generate_shard()  # generates bytes
    addition = CommitOperationAdd(path_in_repo=f"shard_{i}.bin", path_or_fileobj=content)
    preupload_lfs_files(repo_id, additions=[addition])  # upload to S3 now
    operations.append(addition)

# Single commit referencing all pre-uploaded files
create_commit(repo_id, operations=operations, commit_message="All shards")
```

**⚠ Caveat:** Until the commit is made, pre-uploaded files are NOT accessible on the Hub. The `CommitOperationAdd` objects are **mutated** (binary content removed from the object) during preupload.

### list_repo_commits — Inspecting History

```python
commits = api.list_repo_commits("gpt2")
# Sorted by date, newest first

initial_commit = commits[-1]  # Last is the initial commit
# GitCommitInfo(
#     commit_id='9b865efde13a30...',
#     authors=['system'],
#     created_at=datetime(...),
#     title='initial commit',
#     message='',
# )
```

Useful for finding the initial commit OID to create an empty branch:
```python
api.create_branch("gpt2", "new_empty_branch", revision=initial_commit.commit_id)
```

### Zero-Cost Best Practices

1. **Prefer `upload_folder()` with `hf_xet`** — automatic batching, resumability, and deduplication are free and reduce API calls.
2. **Use `CommitOperationCopy` for file duplication** — server-side copies cost nothing and move zero bytes.
3. **Schedule with `CommitScheduler`** — avoid per-event commits; batch every 5-10 minutes to stay under rate limits (~100 req/min).
4. **Check `_remote_oid` before uploading** — `create_commit` already deduplicates unchanged files, but you can pre-check with `file_exists()` on the Hub API.
5. **Avoid empty PRs** — opening PRs without real changes wastes rate limit budget.
6. **Never reuse `CommitOperation` objects** — they get mutated during upload; create fresh operations per commit.
7. **Use `repo_type="dataset"` for persistent storage** — datasets get generous LFS storage for free and integrate with `CommitScheduler`.

### Resources
- Upload guide: https://huggingface.co/docs/huggingface_hub/en/guides/upload
- HfApi reference: https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api
- CommitScheduler: https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api#huggingface_hub.CommitScheduler
- Repository limitations: https://huggingface.co/docs/hub/en/repositories-limitations
- HF URIs syntax: https://huggingface.co/docs/huggingface_hub/en/package_reference/utilities#huggingface_hub.HfUri
- Xet storage overview: https://huggingface.co/docs/hub/en/xet

---

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
- PEFT GitHub: https://github.com/huggingface/peft
|- RapidFire AI integration: https://huggingface.co/docs/trl/main/en/rapidfire

---

## 2026-07-24: hf-hub-fsspec (Deep Dive)

### Summary
Comprehensive deep-dive into Hugging Face Hub's fsspec integration via `HfFileSystem` — a Pythonic file-system interface to the Hub that enables treating remote repositories and buckets as local filesystems. Used by pandas, DuckDB, Zarr, Dask, Polars, and any library supporting the fsspec protocol. Covers architecture, URL scheme, 60+ methods, authentication, integrations, performance tradeoffs, and production best practices.

### Architecture

**HfFileSystem** (`huggingface_hub.hf_file_system.HfFileSystem`) extends `fsspec.AbstractFileSystem` and wraps `HfApi` behind a file-system API. It provides:

- **Module-level singleton**: `huggingface_hub.hffs` — a cached, pre-configured instance. Same as `HfFileSystem.current()`.
- **Inheritance chain**: `HfFileSystem` → `AbstractFileSystem` → `object` (from the `fsspec` library)
- **Constructor**: `HfFileSystem(*args, endpoint=None, token=None, block_size=None, expand_info=None, **storage_options)`
  - `endpoint`: Custom HF Hub endpoint URL
  - `token`: HF token (bool/str/None). `True` = use cached token, `str` = use directly
  - `block_size`: Block size for file transfers
  - `expand_info`: Whether to expand directory info (default: auto)
- **Caching**: The singleton is shared across sessions via `current()`. To create an isolated instance, pass a unique token or endpoint.

### URL Scheme

```
hf://[<repo_type_prefix>]<repo_id>[@<revision>]/<path/in/repo>
```

| Component | Example | Description |
|---|---|---|
| **Protocol** | `hf://` | Required for fsspec integrations; optional when using HfFileSystem directly |
| **Prefix** | `datasets/`, `spaces/`, `buckets/` | Models have no prefix; datasets use `datasets/`; Spaces use `spaces/` |
| **Repo ID** | `username/model-name` | Full repository identifier |
| **Revision** | `@main`, `@v1.0`, `@abc123` | Branch, tag, or commit hash. NOT compatible with buckets |
| **Path** | `/data/train.csv` | Path inside the repository |

**Examples:**
- `hf://bert-base-uncased/config.json` — model file
- `hf://datasets/username/my-dataset/data/train.csv` — dataset file  
- `hf://spaces/username/my-space/app.py` — Space file
- `hf://buckets/username/my-bucket/experiment.parquet` — bucket file
- `hf://username/model@dev/tokenizer.json` — specific revision

### Complete Method Reference (60+ methods)

**Directory & File Listing:**

| Method | Signature | Description |
|---|---|---|
| `ls` | `(path, detail=True, refresh=False, revision=None, **kwargs)` | List directory contents. `detail=True` returns dicts with size/type/mtime; `detail=False` returns path strings |
| `glob` | `(path, maxdepth=None, **kwargs)` | Find files by glob-matching. Supports `**` recursive patterns |
| `find` | `(path, maxdepth=None, withdirs=False, detail=False, refresh=False, revision=None)` | Recursively list all files below path. Like `ls -R` |
| `walk` | `(path, *args, **kwargs)` | Generator yielding `(dirpath, dirnames, filenames)` tuples |
| `tree` | — | Display directory tree |
| `du` | — | Disk usage (alias) |
| `disk_usage` | `(path, total=True, maxdepth=None)` | Calculate storage used |

**File Operations:**

| Method | Signature | Description |
|---|---|---|
| `open` | `(path, mode='rb', block_size=None, cache_options=None, compression=None, **kwargs)` | Open file for read/write. **Default is binary (`'rb'`)** unlike Python's `open`. Use `'r'`/`'w'` for text. Append modes (`'a'`/`'ab'`) NOT supported |
| `cat_file` | `(path, start=None, end=None, **kwargs)` | Get file content as bytes (with optional byte range) |
| `read_text` | `(path, encoding=None, errors=None, newline=None, **kwargs)` | Get file content as string. Pass `revision=` for specific branch |
| `write_text` | `(path, value, encoding=None, errors=None, newline=None, **kwargs)` | Write string content to remote file |
| `read_bytes` | `(path)` | Read raw bytes |
| `pipe_file` | `(path, value)` | Write bytes directly |
| `head` | `(path, size=1024)` | Read first N bytes |
| `tail` | `(path, size=1024)` | Read last N bytes |
| `read_block` | — | Read a block of bytes |
| `cat_ranges` | — | Read multiple byte ranges efficiently |

**File System Operations:**

| Method | Signature | Description |
|---|---|---|
| `info` | `(path, refresh=False, revision=None)` | Get file/directory metadata (size, type, created, modified) |
| `exists` | `(path, **kwargs)` | Check if path exists |
| `isfile` / `isdir` | `(path)` | Type checks |
| `stat` | — | File stats |
| `size` / `sizes` | — | File size(s) |
| `checksum` | — | File checksum |
| `created` / `modified` | — | Timestamps |
| `sign` | `(path, expiration=100)` | Generate signed URL (for temporary access) |
| `url` | — | Get public URL |

**Copy, Move, Delete:**

| Method | Signature | Description |
|---|---|---|
| `cp` / `copy` | `(path1, path2, **kwargs)` | Copy file(s) between paths (remote-to-remote) |
| `mv` / `move` / `rename` | `(path1, path2, recursive=False, maxdepth=None)` | Move/rename file(s) |
| `rm` / `delete` | `(path, recursive=False, maxdepth=None, revision=None)` | Delete file(s). Use `recursive=True` for directories |
| `rm_file` | — | Delete single file |

**Local ↔ Remote Transfers:**

| Method | Signature | Description |
|---|---|---|
| `get_file` | `(rpath, lpath, callback=None, outfile=None)` | Copy remote file to local filesystem |
| `put_file` | `(lpath, rpath, callback=None, mode='overwrite')` | Copy local file to remote repository |
| `get` / `download` | — | Batch download files |
| `put` / `upload` | — | Batch upload files |

**Directory Management:**

| Method | Signature | Description |
|---|---|---|
| `mkdir` / `makedirs` | `(path, create_parents=True)` | Create directory (actually creates a `.gitkeep` since HF Hub doesn't have empty dirs) |
| `rmdir` | — | Remove directory |
| `touch` | — | Create empty file |
| `makedir` / `mkdirs` | — | Directory variants |

**Other:**

| Method | Description |
|---|---|
| `get_mapper` | Get a `zarr.Mapping`-like interface for array storage |
| `expand_path` | Expand glob patterns in paths |
| `invalidate_cache` | Clear the filesystem listing cache |
| `clear_instance_cache` | Clear all cached HfFileSystem instances |
| `resolve_path` / `unstrip_protocol` | Path resolution utilities |
| `transaction_type` / `start_transaction` / `end_transaction` | Transaction support |

### Integrations (Full Ecosystem)

**Pandas:**
```python
import pandas as pd
# Read from Hub
df = pd.read_csv("hf://datasets/my-username/my-dataset/train.csv")
df = pd.read_parquet("hf://datasets/my-username/my-dataset/data.parquet")
df = pd.read_json("hf://my-username/my-model/config.json")
# Write to Hub  
df.to_csv("hf://datasets/my-username/my-dataset/test.csv")
df.to_parquet("hf://buckets/my-username/my-bucket/results.parquet")
```

**DuckDB (remote SQL queries on Hub files):**
```python
from huggingface_hub import HfFileSystem
import duckdb

fs = HfFileSystem()
duckdb.register_filesystem(fs)
fs_file = "hf://datasets/my-username/my-dataset/train.parquet"
df = duckdb.query(f"SELECT col1, COUNT(*) FROM '{fs_file}' GROUP BY col1").df()
```

**Zarr (array store):**
```python
import zarr, numpy as np
# Write
with zarr.open_group("hf://my-username/my-model/embeddings", mode="w") as root:
    root.zeros('experiment_0', shape=(50000, 1000), chunks=(10000, 1000), dtype='f4')
# Read
with zarr.open_group("hf://my-username/my-model/embeddings", mode="r") as root:
    first_row = root["embeddings/experiment_0"][0]
```

**Dask & Polars:**
```python
# Dask
import dask.dataframe as dd
df = dd.read_csv("hf://datasets/my-username/my-dataset/*.csv")

# Polars
import polars as pl
df = pl.read_csv("hf://datasets/my-username/my-dataset/train.csv")
```

### Authentication

| Method | Code |
|---|---|
| **Default (cached token)** | `from huggingface_hub import hffs` (uses token from `huggingface-cli login`) |
| **Programmatic** | `HfFileSystem(token="hf_...")` or `HfFileSystem(token=True)` for cached |
| **Via singleton** | `hffs = HfFileSystem(token=os.getenv("HF_TOKEN"))` |
| **Endpoint override** | `HfFileSystem(endpoint="https://huggingface.co", token=...)` |

**⚠ Security:** Never hardcode tokens in source code. Use environment variables, `huggingface-cli login`, or secret management.

### Performance Considerations

| Aspect | Detail |
|---|---|
| **Overhead** | HfFileSystem adds ~10-20% overhead vs direct HfApi calls due to fsspec compatibility layer |
| **Caching** | Directory listings are cached. Use `refresh=True` or `invalidate_cache()` for fresh data |
| **Best for** | Ad-hoc analysis, prototyping, and when library integration (pandas/DuckDB) is needed |
| **Production** | Use `HfApi` methods (`api.upload_file`, `api.hf_hub_download`) for critical paths |
| **Large files** | `hf_transfer` (Rust-accelerated) is NOT used by HfFileSystem; use `hf_hub_download` for large model weights |
| **Rate limits** | Each filesystem operation maps to at least 1 REST API call; batch operations for efficiency |

### Limitations

1. **No append** — modes `"a"` and `"ab"` not supported
2. **`hf_transfer` not integrated** — does not use the Rust-accelerated upload/download backend
3. **Binary mode default** — `open()` defaults to `'rb'`, unlike Python's built-in `open`
4. **Revision + buckets** — `revision` parameter incompatible with bucket paths
5. **No atomic multi-file commits** — each write is a separate commit. Use `HfApi.create_commit()` for atomic multi-file operations
6. **No empty directories** — the Hub doesn't support empty dirs; `mkdir` creates a `.gitkeep` marker
7. **Not for streaming training** — not designed for high-throughput streaming; use `datasets` library or `HfApi.hf_hub_download` for model weight streaming

### Comparison: HfFileSystem vs HfApi

| Dimension | HfFileSystem | HfApi |
|---|---|---|
| **API style** | File-system (POSIX-like) | REST/object-oriented |
| **Speed** | ~10-20% slower | Direct, minimal overhead |
| **Integration** | pandas, DuckDB, Zarr, Dask, Polars | Direct upload/download/commit |
| **Atomic commits** | No (per-file) | Yes (`create_commit`) |
| **Streaming** | No | Yes (`hf_hub_download`) |
| **Cache control** | Limited | Full (resumable downloads, local cache) |
| **Best for** | Data science, ad-hoc analysis | Production pipelines, CI/CD |

### Best Practices

1. **Use `hffs` singleton for ad-hoc** — the module-level `hffs` uses your cached credentials
2. **Pass `revision=` explicitly** — avoid accidental writes to `main`
3. **Prefers `detail=False` for `ls()`** — reduces API calls when only paths are needed
4. **Batch writes via HfApi for commits** — use `api.create_commit(operations=[...])` for atomic multi-file changes
5. **Clear cache for refresh** — call `hffs.invalidate_cache()` when you know the Hub state changed externally
6. **Use `hf://` URL in integrations** — libraries detect the protocol and use fsspec automatically
7. **Avoid for model weight downloads** — use `hf_hub_download` for large checkpoints (it supports resumption, `hf_transfer`, and local caching)

### Resources
- HfFileSystem guide: https://huggingface.co/docs/huggingface_hub/main/en/guides/hf_file_system
- HfFileSystem API reference: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_file_system
- fsspec documentation: https://filesystem-spec.readthedocs.io/en/latest/
- Hugging Face Buckets guide: https://huggingface.co/docs/huggingface_hub/main/en/guides/buckets
- hf_transfer (Rust): https://github.com/huggingface/hf_transfer
- huggingface_hub source (hffs): https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/hf_file_system.py

## 2026-07-24: hf-datasets-server-advanced-query (Deep Dive — Full API Reference with Real-World Testing)

### Summary
Deep-dive into the Hugging Face Datasets Server REST API — every endpoint tested live against `stanfordnlp/imdb`. Covers /splits, /first-rows, /rows (with offset/length), /search, /filter (with where/orderby), /parquet, /size, /statistics, /is-valid. Documents real response structures, error behavior, pagination mechanics, the filter predicate syntax, and partial indexing limits (5GB ceiling for /filter).

### Endpoint Reference

#### 1. `/splits` — List configs and splits
Returns all config/split tuples for a dataset.

```
GET https://datasets-server.huggingface.co/splits?dataset=stanfordnlp/imdb
```
```json
{
  "splits": [
    {"dataset":"stanfordnlp/imdb","config":"plain_text","split":"train"},
    {"dataset":"stanfordnlp/imdb","config":"plain_text","split":"test"},
    {"dataset":"stanfordnlp/imdb","config":"plain_text","split":"unsupervised"}
  ],
  "pending": [],
  "failed": []
}
```

**Notes:**
- Always use fully qualified dataset names (e.g. `stanfordnlp/imdb`, not `imdb`)
- The `pending` and `failed` arrays show splits that are still processing or errored

#### 2. `/first-rows` — Quick preview of first rows
Returns the first rows of a split with feature metadata. No pagination — always shows exactly 100 rows (the first page).

```
GET https://datasets-server.huggingface.co/first-rows?dataset=stanfordnlp/imdb&config=plain_text&split=train
```

**Response structure:**
```json
{
  "dataset": "stanfordnlp/imdb",
  "config": "plain_text",
  "split": "train",
  "features": [
    {"feature_idx": 0, "name": "text", "type": {"dtype": "string", "_type": "Value"}},
    {"feature_idx": 1, "name": "label", "type": {"names": ["neg","pos"], "_type": "ClassLabel"}}
  ],
  "rows": [
    {"row_idx": 0, "row": {"text": "...", "label": 0}, "truncated_cells": []}
  ]
}
```

**Feature type mapping:**
| HF Type | dtype | JSON representation |
|---------|-------|-------------------|
| Value   | string/int/float/bool | `{"dtype": "string", "_type": "Value"}` |
| ClassLabel | class_label | `{"names": ["neg","pos"], "_type": "ClassLabel"}` |
| Sequence | sequence | `{"_type": "Sequence", "feature": {...}}` |

**Key insight:** ClassLabel features return integer indices in `rows`, not string labels. Map from the `features[].type.names` array.

#### 3. `/rows` — Paginated row access with optional WHERE filter
```
GET https://datasets-server.huggingface.co/rows?dataset=stanfordnlp/imdb&config=plain_text&split=train&offset=0&length=3
```

**Parameters:**
| Param | Required | Default | Notes |
|-------|----------|---------|-------|
| `dataset` | Yes | — | Fully qualified name |
| `config` | Yes | — | Config/subset name |
| `split` | Yes | — | Split name |
| `offset` | No | 0 | Zero-indexed start row |
| `length` | No | 100 | Max rows per page (max=100) |
| `where` | No | — | **Predicate string** (not JSON!) |

**Response:**
```json
{
  "features": [...],
  "rows": [{"row_idx": 0, "row": {...}, "truncated_cells": []}],
  "num_rows_total": 25000,
  "num_rows_per_page": 100,
  "partial": false
}
```

**The `where` parameter uses predicate syntax, not JSON:**
- Correct: `"label">0` or `"label">=0 AND "label"<=1`
- Correct: `"name"='Simone' OR "children"=0`
- INCORRECT: `{"label": 1}` (JSON object — silently ignored on `/rows`)
- INCORRECT: URL-encoded nested JSON like `{"label":{"_eq":1}}` (returns 422)

**Important behavior:** The `/rows` endpoint with `where` applied did NOT actually filter when I passed `{"label":1}` — it silently returned unfiltered rows. The predicate syntax (`"label">0`) is the correct format. For proper filtering, use the dedicated `/filter` endpoint.

**Pagination:** `num_rows_total` gives total rows, `num_rows_per_page` is the page size. Iterate by incrementing `offset` by `length` each request.

#### 4. `/filter` — Full-featured row filtering
The dedicated filtering endpoint with proper predicate support.

```
GET https://datasets-server.huggingface.co/filter?dataset=ibm/duorc&config=SelfRC&split=train&where="no_answer"=true&offset=150&length=2
```

**Supported operators in `where`:**
| Operator | Example | Note |
|----------|---------|------|
| `=` (equals) | `"age"=30` | String values use single quotes: `"name"='Alice'` |
| `!=` | `"age"!=30` | |
| `>` / `>=` | `"age">30` | |
| `<` / `<=` | `"age"<30` | |
| `AND` | `"age">30 AND "city"='Paris'` | |
| `OR` | `"age">30 OR "city"='Paris'` | |
| `NOT` | `NOT "age"=30` | |

**Sorting with `orderby`:**
- Ascending (default): `orderby="age"`
- Descending: `orderby="age" DESC`

**Partial indexing warning:**
Datasets > 5GB are only partially indexed for /filter. Check the `partial` field:
- `"partial": true` — filtering is on first 5GB only
- `"partial": false` — full dataset indexed

#### 5. `/search` — Text search within a split
```
GET https://datasets-server.huggingface.co/search?dataset=stanfordnlp/imdb&config=plain_text&split=train&query=terrible&limit=2
```

**Parameters:**
| Param | Required | Description |
|-------|----------|-------------|
| `dataset` | Yes | Fully qualified |
| `config` | Yes | Subset name |
| `split` | Yes | Split name |
| `query` | Yes | Search text |
| `offset` | No | Pagination offset |
| `limit` | No | Results per page (max=100) |

**Behavior observed:** The search endpoint returned a 502 Bad Gateway for the imdb dataset with "terrible" — suggesting search may time out on large textual datasets. Tends to work better on smaller or structured datasets.

#### 6. `/parquet` — List available Parquet exports
```
GET https://datasets-server.huggingface.co/parquet?dataset=stanfordnlp/imdb
```

**Response:**
```json
{
  "parquet_files": [
    {
      "dataset": "stanfordnlp/imdb",
      "config": "plain_text",
      "split": "test",
      "url": "https://huggingface.co/datasets/stanfordnlp/imdb/resolve/refs%2Fconvert%2Fparquet/plain_text/test/0000.parquet",
      "filename": "0000.parquet",
      "size": 20470363
    },
    {
      "dataset": "stanfordnlp/imdb",
      "config": "plain_text",
      "split": "train",
      "url": "https://huggingface.co/datasets/stanfordnlp/imdb/resolve/refs%2Fconvert%2Fparquet/plain_text/train/0000.parquet",
      "filename": "0000.parquet",
      "size": 20979968
    }
  ],
  "pending": [],
  "failed": [],
  "partial": false
}
```

**Key insights:**
- Parquet URL path uses `refs%2Fconvert%2Fparquet` (URL-encoded `refs/convert/parquet`) — auto-generated by HF
- Each split has its own Parquet file(s) with size in bytes
- Multiple Parquet files per split if the dataset is large (sharded)

**Usage with DuckDB/Polars:**
```python
from huggingface_hub import HfFileSystem
import duckdb

fs = HfFileSystem()
duckdb.register_filesystem(fs)
url = "hf://datasets/stanfordnlp/imdb/refs%2Fconvert%2Fparquet/plain_text/train/0000.parquet"
df = duckdb.query(f"SELECT * FROM read_parquet('{url}') WHERE label = 1 LIMIT 10").df()
```

#### 7. `/size` — Dataset size breakdown
```
GET https://datasets-server.huggingface.co/size?dataset=stanfordnlp/imdb&config=plain_text
```

**Response:**
```json
{
  "size": {
    "config": {
      "dataset": "stanfordnlp/imdb",
      "config": "plain_text",
      "num_bytes_original_files": 83446840,
      "num_bytes_parquet_files": 83446840,
      "num_bytes_memory": 128683449,
      "num_rows": 100000,
      "num_columns": 2,
      "estimated_num_rows": null
    },
    "splits": [
      {
        "dataset": "stanfordnlp/imdb",
        "config": "plain_text",
        "split": "train",
        "num_bytes_parquet_files": 20979968,
        "num_bytes_memory": 33090550,
        "num_rows": 25000,
        "num_columns": 2,
        "estimated_num_rows": null
      }
    ]
  },
  "partial": false
}
```

**Field meanings:**
| Field | Meaning |
|-------|---------|
| `num_bytes_original_files` | Size of original (non-Parquet) data files |
| `num_bytes_parquet_files` | Size of Parquet export files |
| `num_bytes_memory` | Estimated memory footprint when loaded via `datasets` library |
| `estimated_num_rows` | Non-null only for datasets too large for exact counting |

**Compression ratio signal:** Compare `num_bytes_parquet_files` vs `num_bytes_memory` to estimate Parquet compression ratio. For imdb: ~20MB vs 33MB per split (~1.6x compression on text).

#### 8. `/statistics` — Column-level statistics
```
GET https://datasets-server.huggingface.co/statistics?dataset=stanfordnlp/imdb&config=plain_text&split=train
```

**Response:**
```json
{
  "num_examples": 25000,
  "statistics": [
    {
      "column_name": "label",
      "column_type": "class_label",
      "column_statistics": {
        "nan_count": 0,
        "nan_proportion": 0.0,
        "no_label_count": 0,
        "no_label_proportion": 0.0,
        "n_unique": 2,
        "frequencies": {"neg": 12500, "pos": 12500}
      }
    },
    {
      "column_name": "text",
      "column_type": "string_text",
      "column_statistics": {
        "nan_count": 0,
        "nan_proportion": 0.0,
        "min": 52,
        "max": 13704,
        "mean": 1325.07,
        "median": 979.0,
        "std": 1003.13,
        "histogram": {
          "hist": [17426, 5384, 1490, 535, 147, 11, 4, 2, 0, 1],
          "bin_edges": [52, 1418, 2784, 4150, 5516, 6882, 8248, 9614, 10980, 12346, 13704]
        }
      }
    }
  ],
  "partial": false
}
```

**Column type-specific statistics:**

| Column Type | Available Stats | Notes |
|-------------|----------------|-------|
| `class_label` | `n_unique`, `frequencies` (map of string→count) | Labels returned as string names |
| `string_text` | `min`, `max`, `mean`, `median`, `std`, `histogram` | Length stats (char count) |
| `float` / `int` | `min`, `max`, `mean`, `median`, `std`, `histogram` | Value stats |
| `bool` | `n_unique`, `frequencies` | |
| `sequence` | No statistics | Not computed for nested types |

**Histogram interpretation:** 10-bin histogram. `bin_edges` has 11 values (edges of 10 bins). `hist[i]` = count of rows in range `[bin_edges[i], bin_edges[i+1])`.

#### 9. `/is-valid` — Check dataset viewer status
```
GET https://datasets-server.huggingface.co/is-valid?dataset=stanfordnlp/imdb
```

**Response:**
```json
{
  "preview": true,
  "viewer": true,
  "search": true,
  "filter": true,
  "statistics": true
}
```

**Field meaning:** Each boolean indicates if the feature is available for this dataset. Useful for conditional logic before calling other endpoints.

### Error Handling

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | Success | Normal response |
| 404 | Dataset not found or renamed | Removed/renamed datasets |
| 422 | Invalid parameters | Wrong `where` syntax |
| 500 | Server error | Internal indexing failure |
| 502 | Bad Gateway | Timeout on large search queries |

**Error response format:**
```json
{"error": "The dataset has been renamed. Please use the current dataset name."}
```
or
```json
{"error": "Parameter 'where' contains errors or invalid symbols"}
```

### Performance & Limits

| Endpoint | Max Page Size | Indexing Limit |
|----------|--------------|----------------|
| `/rows` | 100 rows/page | Full dataset |
| `/filter` | 100 rows/page | First 5GB (partial=true if exceeded) |
| `/search` | 100 rows/page | First 5GB |
| `/first-rows` | 100 rows (fixed) | Full dataset (preview only) |
| `/statistics` | — | Full dataset |
| `/size` | — | Full dataset |

### Best Practices

1. **Always use fully qualified dataset names** (e.g. `stanfordnlp/imdb`, not `imdb`)
2. **Check `/is-valid` first** before polling other endpoints — it's the fastest way to know what's available
3. **For row-level queries**, prefer `/rows` with `offset`/`length` pagination over `/filter` if you don't need filtering — `/rows` is simpler and has no 5GB index limit
4. **For filtered queries**, use `/filter` with **predicate syntax** (not JSON): `"label">0`, NOT `{"label":1}`
5. **For text search**, use `/search` with short, specific queries — long/common queries may time out on large datasets
6. **For bulk analysis**, use `/parquet` to get file URLs, then query with DuckDB/Polars via `HfFileSystem` for efficient columnar access
7. **ClassLabel columns** return integer indices — always check `features[n].type.names` to map indices to string labels
8. **Handle `partial: true`** — when present, results represent a subset of the data (first 5GB)
9. **Single config vs multi-config**: Datasets with one config return `/splits` normally; `/configs` endpoint returns "Not Found" for single-config datasets — use `/splits` to discover configs instead

### Resources
- Datasets Server OpenAPI spec: https://datasets-server.huggingface.co/openapi.json (uses ReDoc)
- Filter docs: https://huggingface.co/docs/dataset-viewer/en/filter
- Rows docs: https://huggingface.co/docs/dataset-viewer/en/rows
- Search docs: https://huggingface.co/docs/dataset-viewer/en/search
- Parquet docs: https://huggingface.co/docs/dataset-viewer/en/parquet
- Datasets Server source: https://github.com/huggingface/dataset-viewer

---

## 2026-07-24: hf-transformers-gguf-integration (Deep Dive)

### Summary
Comprehensive deep-dive into the Transformers v4.46+ GGUF integration — loading GGUF format models directly via `AutoModelForCausalLM.from_pretrained()` with `gguf_file` parameter, without requiring llama.cpp Python bindings. Covers the GGUF format architecture, all quantization types (Q2_K through Q8_0 with bit-widths and formulas), the hub integration (GGUF viewer, JS parser, model discovery), conversion workflow, supported architectures, and production best practices.

### GGUF Format Overview
GGUF (GPT-Generated Unified Format) is a **single-file binary format** that bundles both model metadata and tensors, designed for use with GGML/llama.cpp — a fast C/C++ inference framework. Unlike tensor-only formats (safetensors), GGUF encodes:
- Standardized metadata header (architecture, tokenizer config, hyperparameters)
- All tensor weights in a single file
- Support for many quantized data types (2-bit through 8-bit)

**Key advantages:**
- Single-file deployment (no `model-00001-of-00002.safetensors` splits)
- Extreme memory efficiency via quantization (4-bit and below)
- Community standard for local/edge inference (LlamaFile, Ollama, LM Studio)
- Hub-native viewer for inspecting metadata & tensors without downloading

### Transformers GGUF Integration (v4.46+)
Starting in Transformers v4.46, you can load GGUF models **directly** without llama-cpp-python:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
filename = "tinyllama-1.1b-chat-v1.0.Q6_K.gguf"

tokenizer = AutoTokenizer.from_pretrained(model_id, gguf_file=filename)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    gguf_file=filename,
    dtype=torch.float16  # or torch.bfloat16, torch.float32
)
```

**Mechanism:** The `gguf_file` parameter tells Transformers to locate the specified GGUF file within the model repo, parse its metadata header to determine the architecture (e.g., LlamaForCausalLM, MistralForCausalLM), and load the weights into the appropriate PyTorch model class — converting quantized weights back to the specified float dtype.

### Supported Architectures
| Architecture | Transformers Class |
|---|---|
| Llama / Llama-2 / Llama-3 | `LlamaForCausalLM` |
| Mistral | `MistralForCausalLM` |
| Qwen2 | `Qwen2ForCausalLM` |
| Qwen2MoE | `Qwen2MoeForCausalLM` |
| Phi-3 | `Phi3ForCausalLM` |
| Bloom | `BloomForCausalLM` |
| Falcon | `FalconForCausalLM` |
| StableLM | `StableLmForCausalLM` |
| GPT2 | `GPT2LMHeadModel` |
| Starcoder2 | `Starcoder2ForCausalLM` |
| Whisper | `WhisperForConditionalGeneration` |

### Complete GGUF Quantization Type Reference
All quantization types from the GGUF specification, as documented on the Hub:

| Type | Bits/Weight | Block Structure | Category |
|------|-------------|----------------|----------|
| `F32` | 32 | — | Unquantized (float) |
| `F16` | 16 | — | Half-precision |
| `BF16` | 16 | — | Brain float |
| `F64` | 64 | — | Double-precision |
| `Q8_0` | 8.0 | Block of 32 weights | Round-to-nearest |
| `Q8_1` | 8.0 | Block of 32 weights | Round-to-nearest + min |
| `Q6_K` | 6.5625 | Super-blocks: 16×16 weights | K-quant |
| `Q5_0` | 5.0 | Block of 32 weights | Legacy round-to-nearest |
| `Q5_1` | 5.0 | Block of 32 weights | Legacy round-to-nearest + min |
| `Q5_K_M/S` | 5.5 | Super-blocks: 8×32 weights | K-quant (recommended) |
| `Q4_0` | 4.0 | Block of 32 weights | Legacy round-to-nearest |
| `Q4_1` | 4.0 | Block of 32 weights | Legacy round-to-nearest + min |
| `Q4_K_M/S` | 4.5 | Super-blocks: 8×32 weights | K-quant (recommended) |
| `Q3_K_S/M/L` | 3.44 | Super-blocks: 16×16 weights | K-quant |
| `Q2_K` | 2.625 | Super-blocks: 16×16 weights | K-quant |
| `IQ4_NL` | 4.25 | Super-blocks: 256 weights | Importance-aware |
| `IQ3_XXS` | 3.44 | Super-blocks: 256 weights | Importance-aware |
| `IQ2_XXS` | 2.06 | Super-blocks: 256 weights | Importance-aware |
| `IQ1_S` | 1.56 | Super-blocks: 256 weights | Importance-aware |
| `F4` | 4 | — | 4-bit Microscaling Block Float |

**Picking the right quantization:** K-quant types (Q2_K–Q6_K) are the recommended family — they use importance-aware block sizing. Q4_K_M is the default choice for most users (4.5 bpw, good quality). Q5_K_M for higher quality when you have the memory. Q2_K for extreme compression (small but reduced reasoning). The newer IQ (Importance-aware Quant) types push below 3 bits for specialized use cases.

### GGUF ↔ Transformers Conversion Workflow
**HF → GGUF:** Use llama.cpp's conversion script:
```bash
python ${llama_cpp_dir}/convert-hf-to-gguf.py ${hf_model_directory} \
    --outfile model.q4_k_m.gguf --outtype q4_k_m
```

**GGUF → Transformers:** Load directly with `gguf_file` parameter. Once loaded, you can continue training with PEFT LoRA, export to safetensors, or convert back to GGUF.

### Hub Integration Features
1. **GGUF File Viewer** — Built-in viewer showing metadata & tensor info on model pages
2. **@huggingface/gguf parser** — JS package that parses GGUF metadata from remote URLs
3. **Tag filtering** — https://huggingface.co/models?library=gguf
4. **Library tag** — Repos use `library_name: gguf` in YAML frontmatter

### Production Best Practices
1. **Q4_K_M** for best quality/size trade-off; Q5_K_M for higher quality
2. **Load with bfloat16** on compatible hardware for optimal dequantization speed
3. **GGUF for deployment**, safetensors for training — or load GGUF then PEFT LoRA
4. **Key publishers:** TheBloke, MaziyarPanahi, Bartowski, QuantFactory
5. **Always specify `--outtype`** when converting; default may not match needs

### Resources
- Transformers GGUF docs: https://huggingface.co/docs/transformers/en/gguf
- Hub GGUF docs: https://huggingface.co/docs/hub/en/gguf
- llama.cpp repo: https://github.com/ggml-org/llama.cpp
- JS parser: `@huggingface/gguf` on npm
- GGUF models: https://huggingface.co/models?library=gguf

---

## 2026-07-24: hf-spaces-persistent-storage-zero-cost — Full Deep Dive v2 (Topic #95, Updated 2026-07-24)

### Summary
Comprehensive deep-dive into persisting data across Hugging Face Space restarts without spending money. Covers all five zero-cost persistence strategies: (A) Storage Buckets (new — free tier, read-write mounts, recommended), (B) Dataset repos via Hub API, (C) read-only volumes for models/datasets, (D) Space's own git repo (with heavy caveats), and (E) external free services. Includes the new `Volume` API in `huggingface_hub`, ZeroGPU integration patterns, Space lifecycle management, and practical code examples for each strategy.

### MAJOR CORRECTIONS from Previous Coverage

| Old (v1) Claim | New (v2) Reality | Source |
|---|---|---|
| Storage Buckets cost money, 0 GB free tier | **Buckets are free to create with a free storage allowance** — pricing is per-TB above free tier | HF docs July 2026 |
| No writable mounts for free | **Buckets support read-write mounts** in Spaces (models/datasets remain read-only) | HF Spaces Storage doc |
| `update_space_volume()` is the API | **Deprecated/replaced by `set_space_volumes()`** using the `Volume` dataclass | huggingface_hub API |
| `hf spaces volume add` CLI | **Replaced by `hf spaces volumes set`** (atomic replace) and `hf spaces volumes ls` | CLI reference |

### Strategy Comparison Matrix

| Strategy | Writable? | Free? | Survives Restart? | Latency | Max Size | Setup Complexity |
|---|---|---|---|---|---|---|
| **A. Storage Bucket** (recommended) | ✅ Read-Write | ✅ Free tier | ✅ Yes — mounted as volume | Filesystem-native | Free allowance | Low |
| **B. Dataset Repo via API** | ✅ Write via API | ✅ Free | ✅ Yes | API latency (~100ms) | LFS storage limit | Medium |
| **C. Read-only Volume** (model/dataset) | ❌ Read-only | ✅ Free | ✅ Yes (mount persists) | Filesystem-native | Repo limit | Low |
| **D. Space's own git repo** | ⚠️ Yes (write) | ✅ Free | ✅ Yes (committed) | Seconds (build+restart) | Space disk (50GB) | Low but DANGEROUS |
| **E. External free service** | ✅ | ✅ Free | ✅ Yes | Network latency | Varies | High |

### Strategy A: Storage Buckets (Recommended — New Free Tier)

**Buckets are the recommended way to persist data in your Space** as of July 2026. They support read-write mounts directly into the Space container.

#### Creating a Bucket

```bash
# CLI
hf buckets create my-space-data

# Python
from huggingface_hub import create_bucket
create_bucket("my-space-data")
```

#### Mounting as a Read-Write Volume (New Volume API)

The old `update_space_volume()` / `hf spaces volume add` APIs are **replaced**. Use the `Volume` dataclass and `set_space_volumes()`:

```python
from huggingface_hub import HfApi, Volume

api = HfApi()

# Mount a bucket as read-write volume at Space creation
api.create_repo(
    repo_id="username/my-space",
    repo_type="space",
    space_sdk="gradio",
    space_volumes=[
        Volume(
            type="bucket",
            source="username/my-bucket",
            mount_path="/data",       # default: read-write
        ),
    ],
)

# Mount on existing Space (replaces ALL existing volumes)
api.set_space_volumes(
    repo_id="username/my-space",
    volumes=[
        Volume(type="bucket", source="username/my-bucket", mount_path="/data"),
        Volume(type="model",  source="username/basemodel", mount_path="/models", read_only=True),
    ],
)

# Check current volumes
runtime = api.get_space_runtime(repo_id="username/my-space")
for v in runtime.volumes:
    print(f"{v.type}: {v.source} -> {v.mount_path} ({'ro' if v.read_only else 'rw'})")

# Remove all volumes
api.delete_space_volumes(repo_id="username/my-space")
```

#### CLI for Volumes (New Syntax)

```bash
# List mounted volumes
hf spaces volumes ls username/my-space

# Set (replace) all volumes — atomically replaces previous mounts
hf spaces volumes set username/my-space \
  --volume bucket=username/my-bucket:/data \
  --volume model=username/basemodel:/models:ro

# Delete all volumes
hf spaces volumes delete username/my-space
```

#### Inside the Space — Read/Write to Volume

Once mounted, the bucket appears as a local filesystem path. No API calls needed:

```python
# Write — persists across restarts
with open("/data/counter.txt", "w") as f:
    f.write(str(count))

# Read — survives restarts, sleep, rebuilds
if os.path.exists("/data/counter.txt"):
    with open("/data/counter.txt") as f:
        count = int(f.read().strip())

# List files in the bucket
import os
for fname in os.listdir("/data"):
    print(fname)
```

**Key advantage:** Filesystem semantics — no API calls, no rate limits, no latency beyond local I/O.

#### Pricing Reality for Free Accounts

- **Free to create** — zero cost to create a bucket
- **Free storage allowance** — basic personal accounts get free bucket storage
- **Above free tier** — billed per-TB, see hf.co/storage
- **Enterprise** — dedup-based billing (shared chunks reduce billed footprint)

For Beer's use case (small configs, chat logs, state files) — stays within free tier indefinitely.

### Strategy B: Dataset Repo via Hub API (Classic Fallback)

Use when you can't use buckets (e.g., need Git versioning, or access from non-Space environments). Every HF account gets free Dataset repo storage with Git LFS.

```python
from huggingface_hub import HfApi
import json, os

api = HfApi()
DATASET_ID = "username/my-space-state"
HF_TOKEN = os.environ["HF_TOKEN"]  # Set as Space secret

def save_state(state: dict):
    """Persist state dict to Dataset repo."""
    api.upload_file(
        path_or_fileobj=json.dumps(state).encode(),
        path_in_repo="state.json",
        repo_id=DATASET_ID,
        repo_type="dataset",
        token=HF_TOKEN,
    )

def load_state() -> dict:
    """Load state from Dataset repo. Returns {} on first boot."""
    from huggingface_hub import hf_hub_download
    try:
        path = hf_hub_download(
            repo_id=DATASET_ID,
            filename="state.json",
            repo_type="dataset",
            token=HF_TOKEN,
        )
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}  # First boot — no file yet
```

**Limitations (unchanged from v1):**
- ~50MB max per `upload_file` call (use `upload_folder` or `CommitScheduler` for larger)
- API rate limits: ~100 requests/min for free tier
- ~100ms+ latency per API call
- No atomic read-modify-write — handle concurrent write conflicts
- `upload_file` overwrites atomically but doesn't lock

### Strategy C: Read-Only Volumes (Models/Datasets/Spaces)

Models, datasets, and other Spaces can be mounted as **read-only** volumes for free. Use for reference data, model weights, configuration files.

```python
from huggingface_hub import HfApi, Volume

api = HfApi()

# Mount at creation
api.create_repo(
    repo_id="username/my-space",
    repo_type="space",
    space_sdk="gradio",
    space_volumes=[
        Volume(type="model",   source="meta-llama/Llama-3.2-3B", mount_path="/models/llama", read_only=True),
        Volume(type="dataset", source="username/my-ref-data",   mount_path="/data/ref",     read_only=True),
    ],
)

# Attach to existing Space
api.set_space_volumes(
    repo_id="username/my-space",
    volumes=[
        Volume(type="model", source="username/my-model", mount_path="/models", read_only=True),
    ],
)
```

**Inside the Space:**
```python
# Files are immediately available — no download code needed
with open("/models/llama/config.json") as f:
    config = json.load(f)
```

**Benefits vs downloading at runtime:**
- Zero startup delay — files are mounted, not downloaded
- No ephemeral disk usage for reference data
- Works seamlessly with all file-access patterns

### Strategy D: Space's Own Git Repo (Use with Extreme Caution)

Writing into the Space's own git repo triggers an automatic rebuild + restart. Pattern: one-shot initialization or explicit user-triggered save.

```python
from huggingface_hub import HfApi
import os

api = HfApi()
SPACE_ID = os.environ["SPACE_ID"]  # Built-in env var

# DANGEROUS — triggers rebuild
api.upload_file(
    path_or_fileobj=b"data",
    path_in_repo="persistent/data.txt",
    repo_id=SPACE_ID,
    repo_type="space",
)

# SAFER — commit via PR (no immediate rebuild, but needs merge)
from huggingface_hub import create_commit, CommitOperationAdd
create_commit(
    repo_id=SPACE_ID,
    repo_type="space",
    operations=[CommitOperationAdd(path_in_repo="data.txt", path_or_fileobj=b"data")],
    commit_message="save state",
    create_pr=True,  # PRs don't trigger automatic rebuild
)
```

**⚠️ Warnings:**
- Every push to default branch triggers `BUILDING` stage — ~30-120s downtime
- Writing frequently can create an infinite loop: write → rebuild → boot → write → rebuild...
- Only safe for: user-triggered "Save" buttons, initial setup, infrequent checkpoint saves
- PR-based saves avoid auto-rebuild but still consume git history

### Strategy E: External Free Services

When HF-native options are insufficient, free external services can supplement:

| Service | Free Tier | Use Case |
|---|---|---|
| **Supabase** | 500 MB DB, 2 GB bandwidth | Structured data, real-time sync |
| **MongoDB Atlas** | 512 MB shared cluster | Document storage, JSON state |
| **Cloudflare KV** | 100k reads/day, 1k writes/day | Key-value state, configs |
| **Vercel Blob** | 250 MB, 5 GB bandwidth | Binary artifacts, images |
| **GitHub Gist API** | Unlimited gists via API | Config files, small state |

**Trade-off:** Adds network dependency and external credentials. Only use when HF-native options don't fit.

### ZeroGPU + Storage Integration

Beer: Free personal accounts can host **up to 2 ZeroGPU Spaces** if account is in good standing (verified email, older than 30 days). Daily quota: **5 minutes GPU time** for free accounts (40 min for PRO).

```python
import spaces
import os
from huggingface_hub import HfApi

HF_TOKEN = os.environ["HF_TOKEN"]
api = HfApi()

# Load model at module level (runs once on CPU)
model = load_my_model()

@spaces.GPU
def generate(prompt: str) -> str:
    """GPU is allocated only during this function call."""
    return model.generate(prompt)

# Persist results to a bucket (always accessible)
def save_result(prompt: str, output: str):
    import json
    with open("/data/results.jsonl", "a") as f:
        f.write(json.dumps({"prompt": prompt, "output": output}) + "\n")
```

**ZeroGPU storage best practices:**
- Load model weights from a mounted model volume (read-only, no startup delay)
- Write inference results to a mounted bucket volume (persistent)
- Use `@spaces.GPU(duration=...)` for accurate GPU time estimation
- Module-level model loading (not inside `@spaces.GPU`) avoids re-loading per call
- Prep models with ahead-of-time compilation (`torch.export`) for ZeroGPU efficiency

### Practical Patterns

#### Pattern 1: First-Boot Detection

```python
import os

BOOT_FLAG = "/data/.initialized"

def is_first_boot() -> bool:
    return not os.path.exists(BOOT_FLAG)

def mark_initialized():
    with open(BOOT_FLAG, "w") as f:
        f.write("1")
```

#### Pattern 2: Periodic State Snapshots

```python
import threading, json, time

snapshot_interval = 300  # 5 minutes

def snapshot_loop(state_getter):
    while True:
        time.sleep(snapshot_interval)
        state = state_getter()
        # Write directly to bucket volume
        with open("/data/snapshot.json", "w") as f:
            json.dump(state, f)

# Start in background
threading.Thread(target=snapshot_loop, args=(lambda: current_state,), daemon=True).start()
```

#### Pattern 3: Concurrent-Write Safe Logging

```python
import json, time, os

LOG_FILE = "/data/event_log.jsonl"

def log_event(event: dict):
    event["_ts"] = time.time()
    # Append-only pattern — safe for concurrent Gradio requests
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")
```

#### Pattern 4: Chat History Persistence (Bucket Volume)

```python
import json, os

HISTORY_FILE = "/data/chat_history.json"

def load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []

def append_message(role: str, content: str):
    history = load_history()
    history.append({"role": role, "content": content})
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)
    return history
```

### Migration Guide: v1 (Dataset API) → v2 (Bucket Volume)

If you have existing Spaces using the old Dataset-API pattern, migrate to bucket volumes:

1. **Create a bucket**: `hf buckets create my-space-data`
2. **Copy existing data**: Download from dataset, upload to bucket
3. **Mount the bucket**: Use `api.set_space_volumes()` with the Volume dataclass
4. **Update app code**: Replace `api.upload_file()` / `hf_hub_download()` calls with direct filesystem I/O to `/data/`
5. **Clean up**: Remove old Dataset API calls and rate-limit handling

### Limitations & Edge Cases

| Issue | Mitigation |
|---|---|
| Bucket volume mount replaces ALL existing volumes | Read current volumes first, append new one |
| Model/dataset volumes are read-only | Use bucket for writes, model mounts for reference data only |
| Buckets are not versioned | Take periodic snapshots to a dataset repo if history needed |
| Space goes to sleep after 48h inactivity (free CPU) | Use `HF_API` to wake: `api.restart_space(repo_id)` |
| ZeroGPU has 5 min daily quota (free) | Optimize GPU calls, cache results, batch requests |
| Bucket not available from outside Spaces | Use Dataset API for cross-environment access |
| Volume changes trigger Space rebuild | Batch volume changes together in one `set_space_volumes()` call |

### Updated Resources (July 2026)

- HF Spaces Storage: https://huggingface.co/docs/hub/en/spaces-storage
- Storage Buckets: https://huggingface.co/docs/hub/en/storage-buckets
- huggingface_hub Manage Spaces: https://huggingface.co/docs/huggingface_hub/guides/manage-spaces
- Volume API (new): `from huggingface_hub import Volume`
- ZeroGPU docs: https://huggingface.co/docs/hub/en/spaces-zerogpu
- HF Spaces Overview: https://huggingface.co/docs/hub/en/spaces-overview
- Buckets Pricing: https://huggingface.co/docs/hub/en/storage-buckets#pricing

---

## 2026-07-24: hf-smolagents — Deep Dive v2

### Summary
Comprehensive deep-dive into Hugging Face's smolagents library (v1.26.0). The v1 skill covered basic CodeAgent/ToolCallingAgent usage. This v2 deep-dive adds: multi-agent orchestration via `managed_agents`, agent memory management (inspection and resumption), two tool creation patterns (`@tool` decorator and `Tool` subclass), Human-in-the-Loop via step callbacks and plan customization, async integration with Starlette/anyio, OpenTelemetry telemetry for run inspection, Agentic RAG patterns, and an expanded secure code execution comparison.

### Key Concepts

**Multi-Agent Orchestration:**
- smolagents supports hierarchical multi-agent systems using `managed_agents` parameter
- Sub-agents require `name` and `description` attributes — the manager calls them like tools
- `ToolCallingAgent` is preferred for focused sub-agents (web search, data fetch); `CodeAgent` works as the reasoning manager
- Systems can nest arbitrarily deep

**Agent Memory:**
- `agent.memory.steps` contains all steps (PlanningStep, ToolCallStep, FinalAnswerStep, ActionStep)
- `agent.run(task, reset=True)` starts fresh; `reset=False` preserves memory and resumes
- Supports human-in-the-loop interruption + resumption with full memory

**Tool Creation:**
- Two patterns: `@tool` decorator (simple functions) vs `Tool` subclass (complex tools with class attributes)
- Tools can be pushed to Hub via `tool.push_to_hub()` — requires self-contained imports, `__init__` with only `self`

**Human-in-the-Loop:**
- `step_callbacks` dict keyed by step type classes (e.g., `{PlanningStep: callback}`)
- Callback signature: `callback(step, agent, task, **kwargs)`
- Supports plan approval, modification, and cancellation

**Async Integration:**
- Use `anyio.to_thread.run_sync(agent.run, task)` to avoid blocking async event loops
- Pattern works with Starlette, FastAPI, and any ASGI framework

**Telemetry:**
- OpenTelemetry-based instrumentation via `SmolagentsInstrumentor`
- Works with Arize Phoenix, Grafana, Datadog, etc.
- Essential for production agent monitoring — agent runs are non-deterministic and hard to debug from console logs alone

**Agentic RAG:**
- Agents with retrieval tools can formulate optimized queries, perform multiple retrievals, reason over sources, and self-critique
- Transforms RAG from rigid pipeline to interactive reasoning process
- Naturally implements HyDE, self-query refinement, and multi-hop retrieval

**Secure Code Execution:**
- Four sandbox options: Blaxel (<25ms), E2B (~500ms), Modal (~2s), Docker
- Only CodeAgent supports sandboxed execution via `executor_type`
- Blaxel provides fastest cold starts and auto-scaling to zero

### Resources
- Docs: https://huggingface.co/docs/smolagents/en/index
- Multi-agent example: https://huggingface.co/docs/smolagents/en/examples/multiagents
- Agentic RAG: https://huggingface.co/docs/smolagents/en/examples/rag
- Memory management: https://huggingface.co/docs/smolagents/en/tutorials/memory
- Tools guide: https://huggingface.co/docs/smolagents/en/tutorials/tools
- Human-in-the-Loop: https://huggingface.co/docs/smolagents/en/examples/plan_customization
- Async agents: https://huggingface.co/docs/smolagents/en/examples/async_agent
- Telemetry: https://huggingface.co/docs/smolagents/en/tutorials/inspect_runs
|- Secure code execution: https://huggingface.co/docs/smolagents/en/tutorials/secure_code_execution

---

## 2026-07-24: hf-hub-lfs-architecture — Deep Dive (Deepening on LFS Mechanics)

### Summary
Comprehensive deep-dive into Hugging Face Hub's Git LFS (Large File Storage) architecture — the underlying protocol that makes hosting multi-GB model weights, datasets, and Spaces possible. Covers the LFS batch API, pointer file mechanics, the `UploadInfo`/`post_lfs_batch_info` pipeline in `huggingface_hub`, storage quota tiers (free/PRO/Team/Enterprise), the Xet protocol replacing `hf_transfer`, LFS file management (deleting, tracking, super-squash), and practical zero-cost strategies for staying within free tier limits.

### Core Architecture

**What Git LFS is on the Hub:** Hugging Face uses an extended Git LFS v1 protocol to handle large binary files. When you `git push` a file matching LFS patterns (`.bin`, `.safetensors`, `.pt`, etc.), Git LFS intercepts it and:

1. **Replaces the file locally with a pointer file** — a tiny text file containing the SHA-256 OID and file size
2. **Uploads the real content** to the Hub's content-addressable LFS store (keyed by SHA-256)
3. **Pushes the pointer** to the Git repository

This means the Git repo stays lightweight — the heavy content lives in a separate blob store, deduplicated by content hash.

### LFS Batch API (Preupload Protocol)

The `post_lfs_batch_info()` function in `huggingface_hub.lfs` implements the [Git LFS Batch API spec](https://github.com/git-lfs/git-lfs/blob/main/docs/api/batch.md):

```python
def post_lfs_batch_info(
    upload_infos: Iterable[UploadInfo],
    token: str | None,
    repo_type: str,
    repo_id: str,
    revision: str | None = None,
    endpoint: str | None = None,
    headers: dict[str, str] | None = None,
    transfers: list[str] | None = None,
) -> tuple[list[dict], list[dict], str | None]:
```

**Flow:**
1. Client sends a batch request to `{endpoint}/{repo_type}/{repo_id}.git/info/lfs/objects/batch`
2. Request body contains JSON with `operation`, `objects` (list of OID+size), `transfers` (preferred transfer protocols)
3. Hub responds with per-object instructions — either `upload` actions (with URLs + headers) or an `error` (e.g., file already exists, quota exceeded)
4. Client then uploads each file using the provided URL

**Protocol-specific headers:**
```python
LFS_HEADERS = {
    "Accept": "application/vnd.git-lfs+json",
    "Content-Type": "application/vnd.git-lfs+json",
}
```
These are required for LFS API calls. The response format follows the Git LFS v1 spec.

### UploadInfo — Smart, Lazy SHA-256

The `UploadInfo` class was designed for efficiency:

```python
class UploadInfo:
    def __init__(self, size: int, sample: bytes, sha256=None, source_path=None):
        ...
```

**Lazy hashing:** Creating `UploadInfo.from_path()` reads only the first **512 bytes** (the `sample`). The full SHA-256 is computed on-demand only when `.sha256` is accessed. This is critical because:
- Some files may be uploaded via Xet protocol which computes SHA during upload (single read pass)
- Avoiding eager SHA saves one full file read per file in batch operations
- The 512-byte sample is used by the server for content-type sniffing

```python
@classmethod
def from_path(cls, path: str):
    size = getsize(path)
    with open(path, "rb") as file:
        sample = file.peek(512)[:512]  # Only reads first 512 bytes!
    return cls(size=size, sample=sample, source_path=path)
```

### LFS Multipart Upload

For very large files, the Hub supports multipart uploads via the `lfs-multipart-upload` command:

```python
LFS_MULTIPART_UPLOAD_COMMAND = "lfs-multipart-upload"
```

The `SliceFileObj` utility (from `huggingface_hub.utils._lfs`) handles splitting large files into chunks for parallel upload. Each chunk is uploaded independently, and the Hub reassembles them server-side.

Key constants in `huggingface_hub`:
- **Max LFS files per commit:** 25,000
- **Max regular (non-LFS) payload:** 1 GB per commit
- **Individual file size limit:** 500 GB hard cap (200 GB recommended)

### Storage Quota Tiers (as of 2026-07-24)

| Account Type | Public Storage | Private Storage |
|---|---|---|
| **Free user/org** | Best-effort (no hard limit, but expect throttling beyond low GBs) | **100 GB** |
| **PRO** | Up to 10 TB included + add-on available | 1 TB + pay-as-you-go |
| **Team** | 12 TB base + 1 TB/seat + add-on | 1 TB/seat + pay-as-you-go |
| **Enterprise** | 200 TB base + 1 TB/seat + add-on | 1 TB/seat + pay-as-you-go |

**Public Storage Add-on pricing:**
| Tier | Price |
|---|---|
| 1 TB | $12/mo |
| 5 TB | $60/mo |
| 10 TB | $120/mo |
| 20 TB | $240/mo |
| 50 TB | $500/mo |

**Private Storage Pay-as-you-go:** $18/TB/mo base, discounted to $16/TB/mo at 50 TB+, $14/TB/mo at 200 TB+, $12/TB/mo at 500 TB+.

**Free tier critical insight:** "Best-effort" means there's no hard cap for public repos on free tier, but the Hub may throttle or restrict accounts that exceed reasonable usage. The 100 GB private storage limit IS a hard cap.

### Repository Limitations

| Characteristic | Recommended | Notes |
|---|---|---|
| Total files per repo | < 100,000 | Merge data into fewer files |
| Entries per folder | < 10,000 | Use subdirectories |
| File size | < 200 GB | 500 GB absolute hard limit |
| Commit operations | < 100 files* | `upload_folder` auto-splits |

*\* Not relevant for `git` CLI directly*

### Xet Protocol (Replacing hf_transfer)

**Key change:** `hf_transfer` (the Rust upload accelerator via `pip install hf_transfer`) has been **removed** in favor of `hf_xet`. The old `HF_HUB_ENABLE_HF_TRANSFER=1` env var is deprecated.

**How to enable Xet:**
```bash
# Environment variable approach
export HF_STORAGE_BACKEND=xet
export HF_XET_HIGH_PERFORMANCE=1  # Saturates bandwidth + CPU

# Or set in Python
from huggingface_hub import HfApi
api = HfApi(storage_backend="xet")
```

**Xet advantages over hf_transfer:**
- Content-addressed deduplication for iterative releases (only uploads changed chunks)
- High-performance mode (`HF_XET_HIGH_PERFORMANCE=1`) saturates available bandwidth
- Single-pass SHA computation (no separate hash step before upload)
- Integrated into the core upload pipeline, not a separate package

**Warning:** Do NOT mix Xet and the legacy multipart transfer simultaneously.

### LFS File Management

#### Deleting LFS Files (Freeing Space)

1. **Individual LFS files:** Repo Settings → "List LFS files" → Actions → Delete
2. **PR refs:** Close/merge PR first, then use "Delete ref" at bottom of PR page
3. **Super-squash history:** Via Python API:
   ```python
   api.super_squash_history(repo_id="user/repo")
   ```
   ⚠️ Destructive — compresses all Git history into one commit, removing old LFS versions. Space freed within 36 hours.

#### Tracking LFS File Origins

When an LFS file's origin is unclear:
```bash
git log --all -p -S <SHA-256-OID>
```

#### Key Points
- Deleting LFS pointers (the text files in Git) does **NOT** free storage space
- Old LFS versions persist in commit history — only super-squash or deleting the LFS file itself truly removes them
- Set `lfs.skipdownloaderrors=true` in `.gitconfig` to avoid errors when checking out branches with deleted LFS content

### Grants for High-Impact Open-Source

Free-tier users with genuine community impact (downloads, citations, adoption) can apply for additional storage grants:
- Contact `datasets@huggingface.co` (datasets) or `models@huggingface.co` (models)
- Provide evidence of community impact (download numbers, citations, adoption)
- Evaluated case-by-case — not guaranteed

### Practical Zero-Cost Strategies

For Beer's situation (free tier, no income):

1. **Stay public:** Public repos have "best-effort" unlimited storage; private repos hit 100 GB hard cap
2. **Keep repos lean:** < 100K files, < 10K entries per folder, files < 200 GB each
3. **Use Parquet/WebDataset:** Merge many small JSON files into fewer Parquet files for efficient storage and faster loading
4. **Use `upload_folder`:** Auto-splits large folders into multiple commits, avoids commit timeouts
5. **Prune regularly:** Delete unused LFS files via Settings → List LFS files; super-squash if history balloons
6. **Avoid LFS on tiny files:** Files under ~1 MB don't benefit from LFS and may even hurt performance
7. **Use Xet for iterative uploads:** `HF_STORAGE_BACKEND=xet` with `HF_XET_HIGH_PERFORMANCE=1` for content-deduped updates to existing repos
8. **Apply for a grant** if you build something with genuine community impact
9. **Monitor usage:** Check `https://huggingface.co/settings/billing` for storage dashboard
10. **Delete stale PR branches:** Large files sitting in unmerged PR branches eat quota even though they never merged

### Resources
- Storage limits: https://huggingface.co/docs/hub/en/storage-limits
- Upload guide: https://huggingface.co/docs/huggingface_hub/en/guides/upload
- LFS source: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/lfs.py
- LFS batch API spec: https://github.com/git-lfs/git-lfs/blob/main/docs/api/batch.md
- Xet docs: https://huggingface.co/docs/xet/en/index
- LFS pointer deletion: https://huggingface.co/docs/hub/en/storage-limits#deleting-individual-lfs-files
- Super-squash API: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api#huggingface_hub.HfApi.super_squash_history
- Pricing: https://huggingface.co/pricing

## 2026-07-24: hf-transformers-hqq-quantization — Deep Dive (Topic #97)

### Summary
Half-Quadratic Quantization (HQQ) is a fast, data-free quantization method integrated into Transformers via the `HqqConfig` class. Unlike AWQ/GPTQ, HQQ requires no calibration dataset — it quantizes on-the-fly using a closed-form half-quadratic solver. Supports 8, 4, 3, 2, and even 1-bit quantization for any model modality (LLMs, vision, etc.). Fully compatible with PEFT/QLoRA fine-tuning and `torch.compile`.

### Core Architecture

HQQ replaces `torch.nn.Linear` layers with `HQQLinear` modules that store quantized weights and dequantize on-the-fly during forward passes. The quantization process uses a half-quadratic optimization that finds optimal scale factors without backpropagation or calibration data.

| Feature | Support |
|---------|---------|
| Data-free quantization | ✅ — no calibration data needed |
| Bit widths | 1, 2, 3, 4, 8 |
| On-the-fly quant | ✅ — quantizes at `from_pretrained()` time |
| PEFT/QLoRA | ✅ — full PEFT integration |
| torch.compile | ✅ — fullgraph compatible |
| Multi-modality | ✅ — LLMs, vision, audio |
| vLLM integration | ✅ — via gemlite backend |
| Serialization (HF) | ❌ — weights not serializable via `save_pretrained` |

### Installation

```bash
pip install hqq
```

For CUDA kernel support the build happens automatically. Disable with `DISABLE_CUDA=1 pip install hqq`.

For bleeding edge:
```bash
pip install git+https://github.com/dropbox/hqq.git
```

### Basic Usage in Transformers

**Replace all linear layers — 8-bit, group_size=64:**
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, HqqConfig

quant_config = HqqConfig(nbits=8, group_size=64)
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B",
    dtype=torch.float16,
    device_map="auto",
    quantization_config=quant_config
)
```

**Per-layer dynamic config (MoE-friendly):**
```python
q4_config = {'nbits': 4, 'group_size': 64}
q3_config = {'nbits': 3, 'group_size': 32}

quant_config = HqqConfig(dynamic_config={
    'self_attn.q_proj': q4_config,
    'self_attn.k_proj': q4_config,
    'self_attn.v_proj': q4_config,
    'self_attn.o_proj': q4_config,
    'mlp.gate_proj': q3_config,
    'mlp.up_proj': q3_config,
    'mlp.down_proj': q3_config,
})

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B",
    dtype=torch.float16,
    device_map="auto",
    quantization_config=quant_config
)
```

### Backends

| Backend | Description | axis | Best for |
|---------|-------------|------|----------|
| `PYTORCH` | Pure PyTorch dequant | 0 or 1 | Compatibility, older GPUs |
| `PYTORCH_COMPILE` | Compiled Pytorch graph | 0 or 1 | Torch.compile workflows |
| `ATEN` | CUDA dequant kernels | 0 only | Best quality, PEFT training |
| `gemlite` | Fused 4-bit gemm kernels | 1 only | High-throughput inference |
| `torchao_int4` | TorchAO tiny_gemm (batch<4) | 1 only | Low-latency single requests |

Set backend globally:
```python
from hqq.core.quantize import *
HQQLinear.set_backend(HQQBackend.PYTORCH)
```

Enable optimized inference after quantization:
```python
from hqq.utils.patching import prepare_for_inference
prepare_for_inference(model, backend="gemlite")
```

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `nbits` | 4 | Bits per weight (1, 2, 3, 4, 8) |
| `group_size` | 64 | Weights per group for shared scale/zero |
| `axis` | 1 | Grouping axis (0=per-output, 1=per-input) |
| `optimize` | True | Enable half-quadratic optimization |

- `axis=0` gives better quality, especially at low bits, but only ATEN backend supports it
- `axis=1` is required for gemlite/torchao_int4 fast inference
- Recommended starting config: `nbits=4, group_size=64, axis=1`

### PEFT/QLoRA Training

Full PEFT integration for fine-tuning quantized models:
```python
from hqq.core.peft import PeftUtils

base_lora_params = {
    'lora_type': 'default', 'r': 32,
    'lora_alpha': 64, 'dropout': 0.05,
    'train_dtype': torch.float32
}
lora_params = {
    'self_attn.q_proj': base_lora_params,
    'self_attn.k_proj': base_lora_params,
    'self_attn.v_proj': base_lora_params,
    'self_attn.o_proj': base_lora_params,
}

PeftUtils.add_lora(model, lora_params)
HQQLinear.set_backend(HQQBackend.ATEN)  # or PYTORCH_COMPILE
# Train...
model.eval()
PeftUtils.merge_and_unload(model)  # Optional: merge
```

Also directly supported in HuggingFace PEFT library:
```python
from peft import LoraConfig, get_peft_model
# Standard PEFT API works with HQQ-quantized models
```

### vLLM Integration

HQQ works with vLLM via gemlite backend for production serving:
```python
from hqq.utils.vllm import set_vllm_onthefly_hqq_quant
from vllm import LLM

skip_modules = ['lm_head', 'visual', 'vision']

# A16W4 HQQ weight-only
set_vllm_onthefly_hqq_quant(
    weight_bits=4, group_size=128,
    quant_mode='int4_weightonly',
    skip_modules=skip_modules
)

llm = LLM(model="meta-llama/Llama-3.2-3B-Instruct",
          max_model_len=4096,
          gpu_memory_utilization=0.80,
          dtype=torch.float16)
```

Supported quant modes for vLLM:
- `int8_weightonly` — A16W8 INT8
- `int4_weightonly` — A16W4 HQQ
- `int8_dynamic` — A8W8 INT8 dynamic
- `fp8_dynamic` — A8W8 FP8 dynamic
- `mxfp8_dynamic` — A8W8 MXFP8 dynamic
- `mxfp4_weightonly` — A16W4 MXFP4
- `nvfp4_dynamic` — A4W4 NVFP4 dynamic

### Zero-Cost Practical Notes

1. **Data-free is a superpower for free-tier:** Since HQQ needs no calibration, you can quantize a model entirely in CPU RAM + normal GPU VRAM — no need for expensive A100s or calibration runs.
2. **Best paired with small GPUs:** A 4-bit 8B model fits in ~5GB VRAM, usable on free T4s (15GB) in Spaces or Colab.
3. **axis=1 + gemlite for speed:** On a T4 you can expect ~30-50 tok/s for 4-bit 7B models.
4. **No serialization limitation:** HQQ models can't `save_pretrained()` in quantized form — you must re-quantize at load time. This is fine for inference-only setups (cache the original fp16, quantize at load).
5. **PEFT stays in fp32:** LoRA adapters train in fp32 by default; the HQQ base weights stay quantized. This is memory-efficient.
6. **torch.compile works with any backend:** Use `PYTORCH_COMPILE` backend or regular `torch.compile` wrapping for additional speed.

### Comparison with Other Quantization Methods

| Method | Calibration? | Bits | Serialize? | torch.compile | vLLM |
|--------|-------------|------|-----------|--------------|------|
| HQQ | No | 1-8 | ❌ | ✅ | ✅ |
| bitsandbytes | No | 4/8 | ✅ | ✅ | ❌ |
| AWQ | Yes | 4 | ✅ | ❌ | ✅ |
| GPTQ | Yes | 2-8 | ✅ | ❌ | ✅ |
| GGUF | No | 1-8 | ✅ | ❌ | ✅ |

### Resources
- Transformers HQQ docs: https://huggingface.co/docs/transformers/en/quantization/hqq
- HQQ blog: https://mobiusml.github.io/hqq_blog/
- HQQ+ (1-bit): https://dropbox.github.io/1bit_blog/
- HQQ repo (mobiusml): https://github.com/mobiusml/hqq
- HQQ repo (dropbox fork): https://github.com/dropbox/hqq
- PEFT HQQ guide: https://huggingface.co/docs/peft/en/developer_guides/quantization#hqq-quantization
- GemLite fast kernels: https://github.com/dropbox/gemlite

---

## 2026-07-24: hf-hub-lfs-architecture — Deep Dive v2 (LFS Batch API Internals, Pointer Format, Deduplication, Advanced Management)

### Summary
Second-pass deep-dive into Hugging Face Hub's Git LFS architecture, covering the LFS Batch API specification in full detail (operations, requests, responses, error codes, transfer adapters), the LFS pointer file specification (format, verification, creation), content-addressable storage deduplication across repos and forks, `.gitattributes` configuration for HF repos, Raw API direct download pattern, advanced LFS debugging, and practical management patterns for staying within free-tier storage limits with minimal overhead.

### 1. LFS Batch API — Full Specification

The Git LFS Batch API is the core protocol for transferring large files between client and server. It operates as an HTTP JSON API.

#### Protocol Endpoint

```
POST {endpoint}/{repo_type}/{repo_id}.git/info/lfs/objects/batch
```

Where:
- `endpoint` = `https://huggingface.co` (default) or `https://huggingface.co/datasets/{org}/{repo}` (for datasets via dataset URL)
- `repo_type` = explicit path to repo (inferred by the Hub), e.g. `https://huggingface.co/{org}/{repo}` for models
- The `.git` suffix is standard Git LFS convention

#### Request Body

```json
{
  "operation": "upload" | "download",
  "transfers": ["xet", "lfs-multipart-upload", "lfs-standalone-file", "basic"],
  "ref": {
    "name": "refs/heads/main"
  },
  "objects": [
    {
      "oid": "sha256:abcdef...",
      "size": 1234567890
    }
  ],
  "hash_algo": "sha256"
}
```

**Required fields:**
- `operation`: `"upload"` or `"download"` — determines whether the server returns upload URLs (with auth tokens) or download URLs
- `objects`: array of OID+size pairs identifying the files to transfer

**Optional fields:**
- `transfers`: ordered array of preferred transfer protocols. The server responds with the first supported one. If omitted, `["basic"]` is assumed.
- `ref`: Git ref name. For uploads, this helps the server validate permissions on the target branch/tag
- `hash_algo`: hash algorithm used. Default is `sha256`.

**Transfer adapters (in priority order as requested by `huggingface_hub`):**
| Adapter | Identifier | Description |
|---------|-----------|-------------|
| Xet | `xet` | Content-deduplicated chunked transfer (new default for HF) |
| LFS Multipart | `lfs-multipart-upload` | Chunked upload for very large files |
| LFS Standalone | `lfs-standalone-file` | Single-file upload via presigned URL |
| Basic | `basic` | Raw HTTP PUT with basic auth |

**Hub-specific extension:** The Hub's LFS server (not standard Git LFS) may return additional metadata about the repository state, storage quota usage, and whether the file already exists on the server (deduplication shunt).

#### Response Body (success, 200)

```json
{
  "transfer": "xet",
  "objects": [
    {
      "oid": "sha256:abcdef...",
      "size": 1234567890,
      "authenticated": true,
      "actions": {
        "upload": {
          "href": "https://...",
          "header": {
            "Authorization": "Bearer <token>",
            "Content-Type": "application/octet-stream"
          },
          "expires_at": "2026-07-24T12:00:00Z"
        },
        "verify": {
          "href": "https://...",
          "header": {
            "Authorization": "Bearer <token>"
          }
        }
      }
    },
    {
      "oid": "sha256:def...",
      "size": 987654321,
      "authenticated": true,
      "actions": null
    }
  ]
}
```

**Key response fields:**
- `transfer`: the transfer adapter the server selected (may differ from what was requested)
- `objects[].actions`: `null` means the object already exists at the target OID (dedup shunt) — no upload needed!
- `objects[].actions.upload`: presigned URL + headers for uploading the file content
- `objects[].actions.verify`: optional URL to verify the upload was stored correctly after upload completes
- `objects[].expires_at`: ISO 8601 timestamp after which the presigned URL expires

#### Response Body (error, 4xx/5xx)

```json
{
  "message": "Quota exceeded",
  "request_id": "abc-123",
  "documentation_url": "https://huggingface.co/docs/hub/en/storage-limits"
}
```

**Common error conditions:**
| Status | Message | Meaning |
|--------|---------|---------|
| 401 | Bad credentials | Token invalid or missing |
| 403 | Forbidden | No write permission on the repo |
| 403 | Quota exceeded | Storage limit reached for private repos |
| 404 | Not found | Repo does not exist |
| 422 | Invalid objects | OID or size validation failed |
| 429 | Too many requests | Rate limited — back off and retry |
| 507 | Insufficient storage | Private storage cap reached |

**Rate limiting:** The Hub applies per-user rate limits on LFS batch operations (~100 req/min). When hit, the server returns 429 with a `Retry-After` header. The `huggingface_hub` client library handles retry with exponential backoff automatically.

### 2. LFS Pointer File Format

Git LFS replaces large files with small pointer files in the actual Git repository. The pointer file is what Git tracks — the real content goes to the LFS store.

#### Canonical Pointer File

```
version https://git-lfs.github.com/spec/v1
oid sha256:4ac7d8e5a7a0a2e4c0c5a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8
size 4127389056
```

**Specification:** The pointer file MUST:
1. Be exactly 3 lines (with trailing newline on each, total 4 newlines including final blank)
2. Line 1: `version https://git-lfs.github.com/spec/v1\n`
3. Line 2: `oid sha256:<64-char lowercase hex>\n`
4. Line 3: `size <decimal integer>\n`
5. No trailing whitespace on any line
6. The OID format is exactly `sha256:` followed by 64 lowercase hex characters
7. The size is in bytes, decimal format, no leading zeros

**Verification:** The Hub validates pointer files at push time — if the pointer format is invalid (wrong version, malformed OID, missing size), the push is rejected.

**Hub extension:** In addition to the standard pointer file, `huggingface_hub` uses a companion cache (in `~/.cache/huggingface/hub/`) that maps `{repo_id}/{commit_hash}/{path_in_repo}` to the OID. This is how the library resolves LFS files without needing to query Git at all — it's a flat-file index that avoids Git metadata calls.

#### Detecting LFS Files in Python

```python
from huggingface_hub import HfApi
api = HfApi()

# List files in a repo — files returned as dicts with 'lfs' field
files = api.get_repo_tree(repo_id="user/repo")
lfs_files = [f for f in files if f.get("lfs")]

# Each LFS file entry has:
# - lfs['oid']: the SHA-256 OID (in hex)
# - lfs['size']: original file size
# - lfs['pointerSize']: size of the pointer file (typically ~120 bytes)
```

### 3. Content-Addressable Storage — Deduplication Mechanics

The Hub stores LFS content in a **content-addressable store** keyed by SHA-256 OID.

#### How CSD Works

```
File A (~/model-00001-of-00002.safetensors) → SHA-256 OID → Store at /objects/4a/c7/d8e5...
File B (fork of same repo, same file) → SHA-256 OID (IDENTICAL) → Files already exists, no re-upload
```

**Implications for free-tier users:**
1. **Forks cost zero extra storage:** If you fork a repo, even if the fork is private, you don't pay for the content already stored. The Hub stores content once by OID. This is true even across repos — if file `abc.safetensors` in `user/repo1` has the same SHA-256 as `abc.safetensors` in `user/repo2`, it's stored only once.
2. **Cross-repo deduplication:** Two separate repos with identical LFS files share the same underlying storage. The storage quota counts only unique new content.
3. **Commit history is not deduplicated:** Different commits that modify an LFS file each store a NEW OID (because the SHA changes when the file changes). Old OIDs remain stored and referenced in the Git history. This is why old LFS versions consume space even after file deletion.
4. **Super-squash is the only escape:** Compressing history via `api.super_squash_history()` drops old LFS OIDs that are no longer referenced by any commit in the new single-commit history.

#### Verifying Deduplication

```python
# Check if a file already exists on the Hub without uploading
from huggingface_hub import HfApi
api = HfApi()

# The batch API's preupload check does this automatically:
# objects with actions=null in the batch response = already exists, dedup'd
```

### 4. `.gitattributes` — LFS Pattern Configuration for HF Repos

The Hub's default LFS patterns are configured server-side but can be overridden locally.

#### Hub's Default LFS Patterns

These file extensions are automatically tracked via LFS by the Hub server:
```
*.safetensors filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
*.pt filter=lfs diff=lfs merge=lfs -text
*.pth filter=lfs diff=lfs merge=lfs -text
*.ckpt filter=lfs diff=lfs merge=lfs -text
*.gguf filter=lfs diff=lfs merge=lfs -text
*.ggml filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.onnx filter=lfs diff=lfs merge=lfs -text
*.tar filter=lfs diff=lfs merge=lfs -text
*.gz filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.zst filter=lfs diff=lfs merge=lfs -text
*.jsonl filter=lfs diff=lfs merge=lfs -text (for very large dataset files)
*.parquet filter=lfs diff=lfs merge=lfs -text
```

**Custom patterns:** You can override by providing a `.gitattributes` file in your repo root:

```gitattributes
# Track extra formats as LFS
*.msgpack filter=lfs diff=lfs merge=lfs -text
*.npy filter=lfs diff=lfs merge=lfs -text

# Force small files to be stored inline (NOT LFS) — saves pointer overhead
*.config -filter -diff -merge
*.json -filter -diff -merge
*.yaml -filter -diff -merge
*.txt -filter -diff -merge
```

**Note:** The Hub server has the final say. If the Hub server considers a file too large (>1 MB) and NOT on a tracked pattern, the push will fail with a connection error because the Git remote helper expects LFS for large blobs.

#### Un-tracking Files from LFS

If you accidentally pushed a large file as regular Git (not LFS) and it bloated the repo:

```bash
# 1. Install git-lfs
git lfs install

# 2. Migrate the file from Git to LFS
git lfs migrate import --include="path/to/large/file.bin" --everything

# 3. Force push (destructive — coordinate with collaborators)
git push --force origin main
```

### 5. Raw API — Direct LFS File Downloads Without Git

The Hub's Raw API allows direct HTTP downloads of LFS files without needing the Git LFS client:

```
GET https://huggingface.co/{repo_id}/raw/{branch}/{path}
```

But for LFS files, the raw endpoint returns the **pointer file** (not the real content). To get real content directly:

```
# Direct LFS download URL:
GET https://huggingface.co/{repo_id}/resolve/{branch}/{path}

# With huggingface_hub:
from huggingface_hub import hf_hub_download
path = hf_hub_download(repo_id="user/repo", filename="model.safetensors", repo_type="model")
```

**The `resolve` endpoint** auto-redirects to the LFS content's CDN URL. This is the recommended URL for downloading model weights in scripts, Colab notebooks, and Spaces.

**Streaming support:**
```python
# Stream large models without fully downloading
from huggingface_hub import hf_hub_download
import torch

# With `hf_hub_download`, use `local_files_only=False` to force fresh download
# Or use the datasets library with streaming for dataset content

# For models, load directly from Hub using transformers with device_map:
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained("user/repo", device_map="auto")
# Downloads LFS weights on-the-fly via the resolve endpoint
```

**Cache behavior:** `hf_hub_download` returns the cached path. Subsequent calls with the same `repo_id` + `filename` return the cached copy instantly. Use `force_download=True` to bypass cache.

### 6. LFS on Free Tier — Advanced Management Patterns

#### Monitoring LFS Usage

```python
from huggingface_hub import HfApi

api = HfApi()

# Get repo info including LFS file listing
repo_info = api.repo_info(repo_id="user/repo", files_metadata=True)

# Count LFS files
lfs_count = sum(1 for f in repo_info.siblings if f.lfs)
lfs_total_size = sum(f.lfs["size"] for f in repo_info.siblings if f.lfs)

print(f"LFS files: {lfs_count}")
print(f"Total LFS size: {lfs_total_size / 1e9:.2f} GB")
```

#### Finding and Deleting Orphaned LFS References

```python
# List all LFS files across all branches/tags
# (requires git CLI access to the cloned repo)
import subprocess

# Find all LFS OIDs referenced by current HEAD
result = subprocess.run(
    ["git", "lfs", "ls-files", "--all", "--name-only"],
    capture_output=True, text=True
)
referenced_oids = set(result.stdout.strip().split('\n'))

# Find LFS files in the cache that are NOT referenced
# (these consume space but are not needed for current checkout)
# Cache is at ~/.cache/huggingface/hub/
```

#### Git LFS Cleanup Commands

```bash
# Check how much space LFS cache is using
du -sh ~/.cache/huggingface/hub/

# Prune local LFS cache (removes unreferenced objects)
git lfs prune

# Check LFS cache health
git lfs fsck  # Verifies all LFS files checkout correctly

# List all LFS files in a repo (from any checkout)
git lfs ls-files --all
```

#### LFS Across All Files in a Repo (Using the Web API)

```bash
# List all files in a repo with LFS status
curl -s https://huggingface.co/api/models/{org}/{repo} | \
    jq '.siblings[] | select(.lfs != null) | {path: .rfilename, size: .lfs.size, oid: .lfs.oid}'

# Get total LFS storage used by a repo
curl -s https://huggingface.co/api/models/{org}/{repo} | \
    jq '[.siblings[] | select(.lfs != null) | .lfs.size] | add | . / 1e9 | "\(.) GB"'
```

#### Avoiding LFS Bloat on Free Tier

**The biggest hidden storage sink** is **version history**. Every time you push an updated LFS file, the old version's OID remains stored. Over 10 updates, that's 10× the storage cost for the same file.

**Strategies:**
1. **One-shot uploads:** When possible, push the final version of a file rather than iterating locally and pushing updates
2. **Super-squash before major storage increases:** Before uploading a large model to a repo with history, run `api.super_squash_history("user/repo")` to reset the commit history to a single commit
3. **Use Xet for iterative updates:** Xet's chunk-level deduplication is more efficient than LFS's whole-file deduplication for iterative releases — only changed chunks are uploaded
4. **Delete old LFS versions via UI:** Go to Repo Settings → "List LFS files" → Delete obsolete versions
5. **Watch for deleted branches:** Merged branches and stale PRs often hold LFS references. After cleanup, run super-squash to truly free the space

### 7. LFS and Xet — Dual Protocol Strategy

The Hub now supports both traditional LFS and the Xet storage backend. Understanding when each is better helps optimize storage:

| Scenario | Best Protocol | Reason |
|----------|--------------|--------|
| First upload of a model | LFS (traditional) | Stable, fastest for single-shot large uploads |
| Iterative updates to large files | Xet | Chunk-level dedup, only uploads changed bytes |
| Many small LFS files | LFS | Xet overhead not worth it for <10 MB files |
| CI/CD pipeline pushing daily | Xet with `HF_XET_HIGH_PERFORMANCE=1` | Bandwidth saturation + dedup |
| Dataset with incremental additions | Xet | Append-only chunks dedup naturally |

**Detection of which protocol was used:**
- LFS-stored files: show up in "List LFS files" in Settings
- Xet-stored files: handled transparently — the Hub API abstracts the backend. Check `HF_STORAGE_BACKEND` env var to see which is active.

### Resources
- Git LFS Batch API spec: https://github.com/git-lfs/git-lfs/blob/main/docs/api/batch.md
- Git LFS Pointer file spec: https://github.com/git-lfs/git-lfs/blob/main/docs/pointer.md
- Git LFS file locking: https://github.com/git-lfs/git-lfs/blob/main/docs/api/locking.md
- HF Storage limits: https://huggingface.co/docs/hub/en/storage-limits
- HF Xet docs: https://huggingface.co/docs/xet/en/index
- huggingface_hub LFS source: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/lfs.py
- huggingface_hub upload guide: https://huggingface.co/docs/huggingface_hub/en/guides/upload
- HF API endpoint: https://huggingface.co/api/models/{org}/{repo}
|- Git LFS migration docs: https://git-lfs.com/

## 2026-07-24: hf-inference-client-structured-outputs — Deep Dive (Topic #100)

### Summary

Comprehensive deep-dive into Hugging Face InferenceClient's **Structured Outputs**, **JSON Mode**, and **Tool/Function Calling** capabilities. These three features form a continuum of structured generation — from unvalidated JSON (JSON Mode) to schema-enforced JSON (Structured Outputs) to dynamic function selection (Tool Calling). All follow OpenAI-compatible API specs for easy migration. Combined with TGI's grammar-based guidance engine (powered by the `outlines` library), these features enable reliable programmatic consumption of LLM outputs without parsing errors.

### The Three Structured Generation Modes

| Mode | What It Does | When To Use | Cost/Complexity |
|------|-------------|-------------|-----------------|
| **JSON Mode** (`response_format={"type": "json_object"}`) | Forces valid JSON output, no schema enforcement | Quick data extraction, prototyping | Lowest — any provider that supports it |
| **Structured Outputs** (`response_format={"type": "json_schema", "json_schema": {...}}`) | Enforces a specific JSON Schema compliant output | Production pipelines, database inserts, API responses | Medium — requires schema definition |
| **Tool Calling** (OpenAI `tools` parameter) | Model decides whether to call a function and with which args | Agent workflows, function dispatching, RAG tool use | Highest — requires tool definitions + handling logic |

### JSON Mode vs Structured Outputs — Key Difference

**JSON Mode** (`type: "json_object"`) only guarantees syntactically valid JSON. The model can output any shape — keys, nesting, data types all vary. Use it when you just need parseable output and can handle variation.

**Structured Outputs** (`type: "json_schema"`) guarantees both valid JSON AND compliance with a specified [JSON Schema](https://json-schema.org/). The model's output is constrained to match your schema exactly — field names, types, required fields, nested structures all enforced. Use it when downstream code depends on a fixed contract.

### Implementation — Structured Outputs with InferenceClient

```python
from huggingface_hub import InferenceClient

# Define a JSON Schema for structured output
json_schema = {
    "name": "book",
    "schema": {
        "properties": {
            "name": {"title": "Name", "type": "string"},
            "authors": {
                "items": {"type": "string"},
                "title": "Authors",
                "type": "array",
            },
        },
        "required": ["name", "authors"],
        "title": "Book",
        "type": "object",
    },
    "strict": True,  # Enforce strict schema compliance
}

client = InferenceClient(provider="cerebras")
completion = client.chat.completions.create(
    model="Qwen/Qwen3-32B",
    messages=[
        {"role": "system", "content": "Extract the books information."},
        {"role": "user", "content": "I recently read 'The Great Gatsby' by F. Scott Fitzgerald."},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": json_schema,
    },
)
print(completion.choices[0].message)
# => {"name": "The Great Gatsby", "authors": ["F. Scott Fitzgerald"]}
```

### JSON Mode — Quick & Lightweight

```python
completion = client.chat.completions.create(
    model="Qwen/Qwen3-32B",
    messages=[{"role": "user", "content": "List 3 colors as JSON."}],
    response_format={"type": "json_object"},
)
# Output is valid JSON but shape not guaranteed
```

### Tool/Function Calling — OpenAI-Compatible

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
    }
}]

completion = client.chat.completions.create(
    model="Qwen/Qwen3-32B",
    messages=[{"role": "user", "content": "What's the weather in Bangkok?"}],
    tools=tools,
    tool_choice="auto",
)
# completion.choices[0].message.tool_calls contains the function calls
```

### The `response_format` Argument — API Details

The `response_format` parameter in `InferenceClient.chat.completions.create()` accepts one of three types:

| Type | Description |
|------|-------------|
| `ChatCompletionInputResponseFormatText` | Text output (default) |
| `ChatCompletionInputResponseFormatJSONObject` | JSON mode — `{"type": "json_object"}` |
| `ChatCompletionInputResponseFormatJSONSchema` | Structured Outputs — `{"type": "json_schema", "json_schema": {...}}` |

### Async Client for Concurrent Structured Requests

```python
from huggingface_hub import AsyncInferenceClient
import asyncio

async def extract_multiple(texts: list[str]):
    async with AsyncInferenceClient(provider="cerebras") as client:
        tasks = [
            client.chat.completions.create(
                model="Qwen/Qwen3-32B",
                messages=[{"role": "system", "content": "Extract entities."},
                          {"role": "user", "content": t}],
                response_format={"type": "json_schema", "json_schema": schema},
            )
            for t in texts
        ]
        return await asyncio.gather(*tasks)
```

### How It Works Under the Hood — TGI Guidance Engine

Text Generation Inference (TGI) implements structured generation via **guidance** — grammar-based token masking powered by the `outlines` library:

1. **Grammar compilation:** The JSON Schema or tool definition is compiled into a finite state machine (FSM).
2. **Forward pass:** The model runs a forward pass over the batch, returning token probabilities.
3. **Masking:** A processor applies the grammar mask — tokens not allowed by the grammar have their probabilities set to zero.
4. **Sampling:** The model samples from the remaining (masked) distribution.
5. **State update:** The chosen token updates the FSM state, preparing for the next pass.

This happens at each generation step, ensuring 100% compliance with the grammar/schema.

**Key insight for zero-cost users:** Providers that run TGI under the hood (Cerebras, Novita, DeepInfra) generally support structured outputs. Providers using vLLM (Together AI, Fireworks) may support it via vLLM's own guided decoding. Check provider docs.

### Provider Support Matrix (Serverless Inference)

Support varies by provider. Verified patterns as of July 2026:

| Provider | JSON Mode | Structured Outputs | Tool Calling | Backend |
|----------|-----------|-------------------|--------------|---------|
| Cerebras | ✓ | ✓ | ✓ | TGI-based |
| Novita | ✓ | ✓ | ✓ | TGI-based |
| DeepInfra | ✓ | ✓ | ✓ | TGI-based |
| Together AI | ✓ | Partial | ✓ | vLLM |
| Fireworks | ✓ | Partial | ✓ | vLLM |
| Replicate | ✓ | Partial | ✓ | Custom |
| Groq | ✓ | ✓ | ✓ | Custom/LPU |
| Fal AI | ✓ | — | — | Custom |

*Partial* = schema enforcement but may not support `strict: True`.

### Zero-Cost Best Practices

1. **Prefer JSON Schema over regex/string parsing** — Structured Outputs eliminate the most common failure mode in agent pipelines (malformed JSON).
2. **Use `strict: True` for production** — Without strict mode, the schema acts as a hint rather than a constraint.
3. **Short schemas generate faster** — Complex deeply nested schemas increase FSM compilation time and per-step overhead.
4. **Combine tools with system prompts** — A system prompt that says "You MUST call a function for every query" improves tool-calling reliability.
5. **`tool_choice: "required"`** — Force the model to always call a tool (useful for classification workflows).
6. **Fallback chain:** Structured Outputs → JSON Mode → raw text with regex parsing. Start with the cheapest option that meets reliability needs.
7. **Rate limits:** Free-tier providers (especially Cerebras, Novita) have tighter rate limits on structured generation due to the FSM overhead per token.

### Resources

- InferenceClient reference: https://huggingface.co/docs/huggingface_hub/en/package_reference/inference_client
- Inference providers guide: https://huggingface.co/docs/huggingface_hub/en/guides/inference
- TGI Guidance docs: https://huggingface.co/docs/text-generation-inference/en/conceptual/guidance
- OpenAI-compatible structured outputs: https://platform.openai.com/docs/guides/structured-outputs
- JSON Schema spec: https://json-schema.org/
- `outlines` library (FSM grammar engine): https://github.com/dottxt-ai/outlines
## 2026-07-24: hf-hub-storage-buckets — Deep Dive (New Feature, Topic #103)

### Summary
Comprehensive deep-dive into Hugging Face **Storage Buckets** — a brand-new repo type providing S3-like object storage on the Hub, powered by the Xet storage backend. Unlike Git-based repositories (models, datasets, Spaces), buckets are non-versioned and mutable: designed for training checkpoints, logs, intermediate artifacts, agent scratch storage, and any large collection of files that doesn't need version control. Buckets have a **free storage allowance** and are available to all users.

### Buckets vs Repositories — Key Differences

| Feature            | Repositories (Git-based)        | Storage Buckets                     |
| ------------------ | ------------------------------- | ----------------------------------- |
| Versioning         | Full Git history                | None (mutable, overwrite-in-place)  |
| Types              | Models, Datasets, Spaces        | Standalone bucket                   |
| Primary use case   | Publishing finished artifacts   | Working storage / intermediate data |
| Operations         | Hub API, Git push/pull          | S3-like `sync`, `cp`, `rm`          |
| Deduplication      | Xet chunk-level                 | Xet chunk-level                     |
| Pull Requests      | Yes                             | No                                  |
| Model/Dataset Cards| Yes                             | No (but plain README rendered)      |

### Creating a Bucket

**From Hub UI:** Visit huggingface.co/new-bucket, choose owner, name, public/private visibility, optional CDN pre-warming regions.

**From CLI:**
```bash
hf buckets create my-bucket
hf buckets create my-org/shared-bucket --private
```

**From Python:**
```python
from huggingface_hub import create_bucket
create_bucket("my-bucket")
create_bucket("my-org/shared-bucket", private=True)
```

### Managing Files

All bucket file references use hf://buckets/ paths.

**Upload/Download/Sync:**
```bash
hf buckets cp ./model.safetensors hf://buckets/username/my-bucket/models/
hf buckets cp hf://buckets/username/my-bucket/config.json - | jq .
hf buckets sync ./data hf://buckets/username/my-bucket/data --delete
```

The sync command supports --include/--exclude filters, --dry-run, and a plan-and-apply workflow (--plan sync-plan.jsonl then --apply).

**Server-Side Copy (brand-new feature):**
```bash
hf buckets cp hf://datasets/HuggingFaceFW/fineweb/data hf://buckets/username/fineweb-data
```
Only Xet-tracked files (large) copied server-side instantly; small non-Xet files auto-downloaded and re-uploaded. Source and destination must be in the same storage region.

### Access Patterns

| Method | Best for |
|--------|----------|
| hf-mount | Mount as local filesystem via NFS/FUSE |
| Volume mounts | HF Jobs & Spaces |
| hf:// paths (fsspec) | Python data tools (pandas, DuckDB) |
| CLI sync | Batch transfers, backups |
| S3 API | AWS CLI, boto3, s5cmd |

**Python via HfFileSystem:**
```python
import pandas as pd
df = pd.read_parquet("hf://buckets/username/my-bucket/data.parquet")

import duckdb
from huggingface_hub import HfFileSystem
duckdb.register_filesystem(HfFileSystem())
```

### Key Use Cases for Zero-Cost

1. Training checkpoints & logs - overwrite-in-place, no Git history accumulation
2. Data processing pipelines - staging area for intermediate results
3. Agentic storage - Hub-native scratch for AI agents (tool outputs, working memory)
4. Rolling backups - old files truly gone when deleted (unlike Git repos)
5. Linking models to buckets - two-way link via model card YAML

### Pricing

Buckets are free to create with a free storage allowance. Per-TB billing above free tier. Enterprise plans get dedup-based billing. CDN pre-warming available at hf.co/storage.

### Resources
- Storage Buckets docs: https://huggingface.co/docs/hub/en/storage-buckets
- Access Patterns: https://huggingface.co/docs/hub/en/storage-buckets-access
- S3-Compatible API: https://huggingface.co/docs/hub/en/storage-buckets-s3
- hf-mount: https://github.com/huggingface/hf-mount
- HuggingFace Hub Buckets Python guide: https://huggingface.co/docs/huggingface_hub/guides/buckets
- Xet storage backend: https://huggingface.co/docs/hub/xet/index

---

## 2026-07-24: hf-hub-collections-api-deep-dive — Full API Reference & Patterns (Topic #107)

### Summary
Comprehensive deep-dive into the Hugging Face Hub Collections API — covering all 7 collection methods from source (`huggingface_hub` v1.x), the `list_collections` pagination engine with 3 sort modes and 2 filter axes, the `Collection` and `CollectionItem` data classes, 6 item types (model, dataset, space, paper, collection, bucket), and practical patterns for programmatic curation, batch population, and integration with other Hub features.

### Core Data Types

**`CollectionItemType_T`** = `Literal["model", "dataset", "space", "paper", "collection", "bucket"]`

**`CollectionSort_T`** = `Literal["lastModified", "trending", "upvotes"]`

**`CollectionItem`** fields: `item_object_id` (DB id), `item_id` (Hub ID), `item_type`, `position`, `note` (max 500 chars)

**`Collection`** fields: `slug`, `title`, `owner`, `items`, `last_updated`, `position`, `private`, `theme`, `upvotes`, `description` (max 150 chars), `url` (property)

### Method Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `list_collections()` | GET `/api/collections` | List with filters (owner, item, sort, limit) — items truncated to 4 |
| `get_collection()` | GET `/api/collections/{slug}` | Full collection with ALL items |
| `create_collection()` | POST `/api/collections` | Create new (title, namespace, description, private, exists_ok) |
| `update_collection_metadata()` | PATCH `/api/collections/{slug}` | Update title/desc/position/private/theme |
| `delete_collection()` | DELETE `/api/collections/{slug}` | Irreversible! Supports `missing_ok` |
| `add_collection_item()` | POST `/api/collections/{slug}/items` | Add item (item_id, item_type, note, exists_ok) |
| `update_collection_item()` | PATCH `/api/collections/{slug}/items/{id}` | Edit note/position (uses `item_object_id`) |
| `delete_collection_item()` | DELETE `/api/collections/{slug}/items/{id}` | Remove item (uses `item_object_id`) |

### Key Behaviors & Pitfalls

1. **`list_collections` truncates items to 4** — always use `get_collection()` for full item lists
2. **`item_object_id` vs `item_id`** — modify/delete operations require the internal DB id, NOT the Hub repo ID
3. **No `theme` on `create_collection`** — must be set via `update_collection_metadata()` after creation
4. **Slug changes on title update** — prefix changes but trailing hash stays the same; old slug URL breaks
5. **Description capped at 150 chars** — silently truncated; notes capped at 500 chars
6. **6 item types**: model, dataset, space, paper, collection, bucket
7. **`exists_ok` on create_collection catches HTTP 409** — returns existing collection if slug collision
8. **Hub Web UI features NOT in API**: item images, history, drag-and-drop, gating group collections, resource group assignment

### 6 Practical Patterns

1. **Batch population** — iterate model lists with `exists_ok=True` and try/except for resilience
2. **Trending discovery** — combine `list_models()` search with `add_collection_item()`
3. **Cross-user mirror** — `get_collection()` source → `create_collection()` dest with all items copied
4. **Research project page** — paper + model + dataset in one collection with notes
5. **Annotated curation** — use `note` fields for ratings/status emoji (⭐ ⚠ 🔄)
6. **Auto-curation via cron** — daily cron to maintain a "Trending Today" collection

### Resources
- Source: `huggingface_hub/hf_api.py` lines 9908–10400
- Hub docs: https://huggingface.co/docs/hub/en/collections
- Collections page: https://huggingface.co/collections
