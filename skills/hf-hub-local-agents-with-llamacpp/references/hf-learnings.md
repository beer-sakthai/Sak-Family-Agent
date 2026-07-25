# HF Learnings — Local Agents with llama.cpp

> **author:** SakThai  
> **license:** MIT  

## 2026-07-25-v2: hf-hub-local-apps-deep-dive — Hugging Face Hub Local Apps & Local Agents Ecosystem (Topic #324, Deepened)

### Summary
Deep dive into the Hugging Face Hub's **Local Apps** ecosystem — the system that lets you run HF models on your own hardware with one-click commands. Covers all four supported local apps (llama.cpp, Ollama, Jan, LM Studio), the Hardware Profiling system at `huggingface.co/settings/hardware`, the `-hf` flag architecture in llama.cpp, Ollama's `hf.co/` namespace integration, and how local agents (Pi, OpenClaw, Hermes Agent, OpenCode, llama-agent) connect to local model servers. The key insight: **Local Apps transform HF from a cloud-only platform into a local-first inference ecosystem** where every model page becomes a launch point for local deployment.

---

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                 Hugging Face Hub                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Hardware  │  │ "Use this│  │ Model Discovery & │   │
│  │ Profile   │  │  model"  │  │ GGUF Search      │   │
│  │ Settings  │  │  button  │  │ (app:llamacpp)    │   │
│  └─────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
│        │             │                 │              │
└────────┼─────────────┼─────────────────┼──────────────┘
         │             │                 │
         ▼             ▼                 ▼
    ┌─────────────────────────────────────────┐
    │         Terminal Command                │
    │  llama-server -hf user/repo:quant       │
    │  ollama run hf.co/user/repo:quant       │
    └────────────────┬────────────────────────┘
                     │
                     ▼
    ┌─────────────────────────────────────────┐
    │       Local Inference Server            │
    │  (OpenAI-compatible API on :8080)       │
    │  ┌─────────────┐  ┌──────────────────┐  │
    │  │  GGUF Model  │  │  Shared HF Cache │  │
    │  │  in Memory   │  │  (~/.cache/hug-  │  │
    │  │             │  │  gingface/hub)    │  │
    │  └─────────────┘  └──────────────────┘  │
    └────────────────┬────────────────────────┘
                     │
         ┌───────────┼────────────┐
         ▼           ▼            ▼
    ┌────────┐ ┌──────────┐ ┌──────────┐
    │  Pi    │ │  Hermes  │ │  OpenCode│
    │ Agent  │ │  Agent   │ │  Coding  │
    └────────┘ └──────────┘ └──────────┘
```

---

### 1. Hardware Profiling System

The Hub's hardware profiling system at `huggingface.co/settings/hardware` is the **entry point** for the entire Local Apps workflow.

**How it works:**
1. User fills in a form with their GPU model (or selects CPU-only) and RAM size
2. HF stores this as a **Hardware Profile** in user settings
3. When browsing models, HF cross-references each model's memory requirements against the hardware profile
4. Models that fit the user's hardware show green "Compatible" badges
5. The "Use this model" dropdown generates the **exact command** needed for the user's hardware

**Hardware Profile fields:**
| Field | Description | Example |
|-------|-------------|---------|
| GPU Model | Your graphics card | NVIDIA RTX 3060 (12GB), Apple M3 Max |
| CPU RAM | System RAM in GB | 32 GB |
| GPU VRAM | Dedicated GPU memory | 12 GB |
| RAM Allocation | How much RAM to allocate to llama.cpp | 8 GB |

**Model compatibility check** uses these fields to determine if a GGUF quant fits:
- `Q4_K_M` ~ 4.5 bits per parameter + overhead
- `Q8_0` ~ 8.5 bits per parameter + overhead
- KV cache memory = context_length × layers × hidden_size × bytes_per_value

**Model card integration:** Model authors can specify recommended quantization levels and hardware requirements in the model card YAML, which the HF hardware checker reads to determine compatibility.

---

### 2. Local Apps Settings (`huggingface.co/settings/local-apps`)

The Local Apps settings page lets users:
1. **Enable/disable** specific local apps (toggle llama.cpp, Ollama, Jan, LM Studio)
2. **Select a default** local app
3. **Configure paths** to local app binaries (auto-detected on most systems)
4. **View installed versions** of each local app

Disabled apps won't show in the "Use this model" dropdown on model pages.

---

### 3. The `-hf` Flag Architecture (llama.cpp)

The `-hf` flag is llama.cpp's direct HF Hub integration, added in 2025. It replaces the previous two-step workflow (download manually → run server) with a single command.

**Architecture:**
```cpp
// Pseudocode showing what -hf does internally
function handle_hf_flag(repo_id: string):
    // Parse "user/repo:quant" format
    let (user, repo, quant) = parse_repo_id(repo_id)
    
    // Check shared HF cache first
    let cache = get_hf_cache_path()
    let model_path = cache / f"models--{user}--{repo}/snapshots/{latest_hash}/"
    
    if not model_exists(model_path):
        // Download via HF Hub API (same cache as huggingface_hub)
        model_path = download_from_hub(user, repo, quant)
    
    // Load and run
    return load_gguf(model_path)
```

**Key improvements in the latest version:**
- **Shared HF cache**: Models downloaded via `-hf` now stored in the standard HF cache directory (`~/.cache/huggingface/hub/`), sharing with `huggingface_hub` Python library, `transformers`, and other HF tools
- **Quant specification**: Use `:` suffix to select quantization: `-hf user/repo:Q4_K_M`
- **Default quantization**: If not specified, downloads the model's default/tagged GGUF file
- **Automatic resumption**: Downloads resume on interruption via the HF Hub API

**Full command reference:**
```bash
# Basic usage (downloads default quant)
llama-server -hf ggml-org/gemma-3-1b-it-GGUF

# Specific quantization
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0

# CLI mode instead of server
llama-cli -hf ggml-org/gemma-4-26b-a4b-it-GGUF:Q4_K_M

# Raw completion mode (non-chat)
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0 -no-cnv

# Custom endpoint (non-HF hubs)
export MODEL_ENDPOINT="https://your-hf-mirror.com"
llama-server -hf user/repo:quant
```

**Cache management:**
```bash
# Cache location (shared with HF Python tools)
echo $LLAMA_CACHE  # default: ~/.cache/huggingface/hub/

# Clear cache for a specific model
rm -rf ~/.cache/huggingface/hub/models--user--repo/

# List cached models
ls ~/.cache/huggingface/hub/ | grep "models--"
```

---

### 4. Ollama `hf.co/` Namespace Integration

Ollama's integration with HF uses the `hf.co/` namespace:

```bash
# Run any GGUF model from HF
ollama run hf.co/unsloth/gpt-oss-20b-GGUF:Q4_K_M

# Pull without running
ollama pull hf.co/ggml-org/gemma-3-1b-it-GGUF

# List local models from HF
ollama list | grep hf.co
```

**Behind the scenes:**
1. Ollama detects the `hf.co/` prefix
2. Uses the Hugging Face Hub API to resolve the model repo and GGUF filename
3. Downloads the GGUF file using Ollama's own download mechanism
4. Converts and loads it into Ollama's model format

**Comparison with llama.cpp `-hf`:**
| Aspect | llama.cpp `-hf` | Ollama `hf.co/` |
|--------|-----------------|-----------------|
| Cache | Shared HF cache | Ollama's own cache (`~/.ollama/`) |
| Quant selection | `repo:Q4_K_M` | `repo:Q4_K_M` |
| Server mode | Built-in (`llama-server`) | `ollama serve` |
| OpenAI API | `/v1/chat/completions` | `/v1/chat/completions` |
| Multi-model | One process per model | Built-in model manager |
| GPU acceleration | Manual build flags | Auto-detected |

---

### 5. LM Studio Integration

LM Studio provides a GUI for running local models with automatic HF Hub integration.

**HF Hub workflow:**
1. Navigate to any model page on HF
2. Click "Use this model" → LM Studio
3. LM Studio opens with the model queued for download
4. Automatic quantization selection based on hardware
5. One-click start for chat or API server

**Advantages:**
- Built-in model browser with HF search
- Developer tools: OpenAI-compatible API server on `localhost:1234`
- Multi-model support with fast switching
- Remote inference access via ngrok integration

**API server mode:**
```python
# Connect to LM Studio's local API server
from openai import OpenAI
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)
```

---

### 6. Jan Integration

Jan provides a ChatGPT-like desktop experience with HF Hub integration.

**HF Hub workflow:**
1. Navigate to any model page on HF
2. Click "Use this model" → Jan
3. Jan opens with the model added to the model hub list
4. User clicks "Start" to download and run

**Key features:**
- Chat with documents (RAG built-in)
- OpenAI-compatible API server
- Offline-first (no internet needed after download)
- Extensions system for tools and connectors

---

### 7. Local Agent Frameworks — Full Configuration Reference

#### 7.1 Pi Coding Agent

**Setup:**
```bash
npm install -g @mariozechner/pi-coding-agent
```

**Model config (`~/.pi/agent/models.json`):**
```json
{
  "providers": {
    "llama-cpp": {
      "baseUrl": "http://localhost:8080/v1",
      "api": "openai-completions",
      "apiKey": "none",
      "models": [
        { "id": "ggml-org-gemma-4-26b-4b-gguf" }
      ]
    }
  }
}
```

**Vision support** (for multimodal GGUF models like LLaVA, Qwen-VL):
```json
{
  "id": "qwen-vl-model",
  "input": ["text", "image"]
}
```

**Launch sequence:**
```bash
# Terminal 1: Start model server
llama-server -hf ggml-org/gemma-4-26b-a4b-it-GGUF:Q4_K_M

# Terminal 2: Start Pi agent
pi
```

#### 7.2 Hermes Agent

**Config (`~/.hermes/config.yaml`):**
```yaml
model:
  provider: custom
  default: ggml-org/gemma-4-26B-A4B-it-GGUF:Q4_K_M
  base_url: http://127.0.0.1:8080/v1
  api_key: llama.cpp

custom_providers:
  - name: Local (127.0.0.1:8080)
    base_url: http://127.0.0.1:8080/v1
    api_key: llama.cpp
    model: ggml-org/gemma-4-26B-A4B-it-GGUF:Q4_K_M

auxiliary:
  session_search:
    base_url: "http://127.0.0.1:8080/v1"
    api_key: "no-key-required"
    model: "local-llama"
    timeout: 90
    max_concurrency: 1
```

**Launch:**
```bash
hermes run
```

#### 7.3 OpenCode

**Config (`~/.config/opencode/opencode.json`):**
```json
{
  "provider": {
    "llama.cpp": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "llama-server (local)",
      "options": {
        "baseURL": "http://127.0.0.1:8080/v1"
      },
      "models": {
        "gemma-4-26b-4b-it": {
          "name": "Gemma 4 (local)",
          "limit": { "context": 128000, "output": 8192 }
        }
      }
    }
  }
}
```

#### 7.4 llama-agent (C++ native)

**Build:**
```bash
git clone https://github.com/gary149/llama-agent.git
cd llama-agent
cmake -B build
cmake --build build --target llama-agent
```

**Run:**
```bash
./build/bin/llama-agent -hf ggml-org/gemma-4-26b-a4b-it-GGUF:Q4_K_M
```

**Features unique to llama-agent:**
- Zero external dependencies (no Node.js, no Python)
- Tool calls execute in-process (no HTTP overhead between model and agent loop)
- Subagent spawning via `--subagent` flag
- MCP server support for external tool integration
- HTTP API server mode for remote agent access

#### 7.5 OpenClaw

**Setup:**
```bash
openclaw onboard
```

**During onboarding:**
- Select "custom-api-key" for provider type
- Set base URL to `http://localhost:8080`
- Set API key to any placeholder

**Local memory (using node-llama-cpp):**
```bash
npm i node-llama-cpp
openclaw config set agents.defaults.memorySearch.provider local
openclaw config set agents.defaults.memorySearch.local.modelPath \
  "hf:ggml-org/embeddinggemma-300m-qat-q8_0-GGUF/embeddinggemma-300m-qat-Q8_0.gguf"
openclaw gateway restart
openclaw memory status
```

---

### 8. Combining llama.cpp with Ollama

For advanced setups, you can combine llama.cpp's performance with Ollama's model management:

**Option A: Shared model directory** — Both applications can access `.gguf` files from the same directory:

```bash
# Download via Ollama (uses Ollama's cache)
ollama pull hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0

# Find the file in Ollama's cache
find ~/.ollama -name "*.gguf" -type f

# Copy to a shared location
cp ~/.ollama/models/blobs/... /shared/models/model.gguf

# Run via llama-server
llama-server -m /shared/models/model.gguf
```

**Option B: Separate models** — Choose based on use case:
- Ollama for **multi-model experimentation** (fast switching, model management)
- llama.cpp for **production/agent** use (lower overhead, direct control, `-hf` flag)

---

### 9. Zero-Cost Local Inference Patterns (Beer's Setup)

Since Beer has no GPU and limited RAM, these are the optimal local agent configurations:

**1. Small models for CPU inference:**
```bash
# Gemma 3 1B — very fast on CPU, fits in 2GB RAM
llama-server -hf ggml-org/gemma-3-1b-it-GGUF

# Qwen2.5 0.5B — tiny, instant responses
llama-server -hf Qwen/Qwen2.5-0.5B-Instruct-GGUF:Q4_K_M

# SmolLM 1.7B — optimized for CPU
llama-server -hf HuggingFaceTB/SmolLM-1.7B-Instruct-GGUF:Q4_K_M
```

**2. Staring the server automatically:**
```bash
# In .bashrc or systemd service
llama-server -hf ggml-org/gemma-3-1b-it-GGUF --port 8080 --host 127.0.0.1 &
```

**3. Memory budget for agents (2GB RAM limit):**
- Gemma 3 1B (Q4_K_M): ~700MB → leaves 1.3GB for agent process
- Qwen2.5 0.5B (Q4_K_M): ~400MB → best for memory-constrained systems
- Embedding model for memory search: EmbeddingGemma 300M (Q8_0): ~350MB

---

### 10. Building Custom Local Apps (Developer Guide)

If you want to make your app a "Local App" on HF:

**Integration Steps:**
1. **Add the HF tag** to your model search filters:
   - Tag your app in the HF Hub via the `app:` search filter (coordinated with HF team)
2. **Implement the "Use this model" button**:
   - Register your app's URL scheme with HF
   - Example: `yourapp://load-model?repo={repo_id}&quant={quantization}`
3. **Support hardware profile integration**:
   - Read HF hardware profile via API if available
   - Recommend appropriate quantization based on user's hardware

**API for local apps** (via `huggingface_hub`):
```python
from huggingface_hub import HfApi

api = HfApi()
# Get model metadata for hardware compatibility
model_info = api.model_info("bartowski/Llama-3.2-3B-Instruct-GGUF")
# Check for GGUF files
siblings = model_info.siblings
gguf_files = [s for s in siblings if s.rfilename.endswith(".gguf")]
```

---

### 11. Troubleshooting Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `llama-server: command not found` | llama.cpp not installed | `brew install llama.cpp` or build from source |
| `-hf flag not recognized` | Old llama.cpp version | Update to latest: `brew upgrade llama.cpp` |
| Model downloads then exits immediately | Out of memory | Use smaller quant (Q4_K_M instead of Q8_0) or smaller model |
| Slow inference on CPU | No CPU optimizations | Build with `-DGGML_NATIVE=ON` for CPU-specific optimizations |
| Ollama `hf.co/` not found | Prefix format wrong | Use `ollama run hf.co/user/repo:quant` (note the `.co/`) |
| Agent can't connect to server | Port mismatch | Check: `curl http://localhost:8080/v1/models` |
| CUDA out of memory | Model too large for GPU | Use CPU offloading: `-ngl 0` forces CPU-only |
| HF download speed slow | No `hf_transfer` | Install `pip install hf_transfer` and set `HF_HUB_ENABLE_HF_TRANSFER=1` |
| Cache corruption | Interrupted download | Clear model cache: `rm -rf ~/.cache/huggingface/hub/models--user--repo/` |

---

### 12. Comparison Matrix: Local Apps

| Feature | llama.cpp | Ollama | LM Studio | Jan |
|---------|-----------|--------|-----------|-----|
| **Installation** | brew/compile | brew/pkg | GUI installer | GUI installer |
| **HF Integration** | `-hf` flag | `hf.co/` namespace | "Use this model" button | "Use this model" button |
| **Shared HF Cache** | ✅ Yes | ❌ Own cache | ❌ Own cache | ❌ Own cache |
| **OpenAI API** | ✅ localhost:8080 | ✅ localhost:11434 | ✅ localhost:1234 | ✅ localhost:1337 |
| **GUI** | Web UI (new) | `ollama run` (CLI) | Full GUI | Full GUI |
| **CLI** | `llama-cli` | `ollama run` | Built-in | Built-in |
| **Multi-model** | Manual (port per model) | `ollama run` auto | Built-in | Built-in |
| **Agent/API use** | ✅ Best | ✅ Good | ✅ Good | ⚠️ Limited |
| **GPU support** | Manual build | Auto-detected | Auto-detected | Auto-detected |
| **Resource usage** | Very low | Low | Medium | Medium |
| **HF cache sharing** | ✅ Full | ❌ | ❌ | ❌ |

---

### 13. Agent Framework Comparison

| Feature | Pi | Hermes Agent | OpenCode | llama-agent | OpenClaw |
|---------|----|-------------|----------|-------------|----------|
| **Language** | Node.js | Rust/Python | Node.js | C++ | Node.js |
| **API type** | OpenAI-compat | OpenAI-compat | AI SDK | In-process | OpenAI-compat |
| **Tool calling** | ✅ | ✅ | ✅ | ✅ (native) | ✅ |
| **Vision support** | ✅ (config) | ⚠️ (model-dep) | ⚠️ | ✅ | ⚠️ |
| **Local memory** | ❌ | ✅ (session_search) | ❌ | ❌ | ✅ (node-llama-cpp) |
| **MCP support** | ❌ | ✅ | ❌ | ✅ | ✅ |
| **Subagents** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Setup complexity** | Low | Medium | Low | High (build) | Medium |
| **Best for** | Quick coding | Agent workflows | VS Code coding | Performance | CI/CD |

---

### Sources
- https://huggingface.co/docs/hub/en/local-apps — Official HF Local Apps documentation
- https://huggingface.co/docs/hub/en/gguf-llamacpp — llama.cpp + HF GGUF usage guide
- https://huggingface.co/settings/local-apps — Local Apps settings page
- https://huggingface.co/settings/hardware — Hardware profiling settings
- https://github.com/ggml-org/llama.cpp — llama.cpp README (HF `-hf` flag, shared cache)
- https://huggingface.co/docs/hub/en/agents-local — Local agents documentation
- https://github.com/gary149/llama-agent — llama-agent C++ native agent

### Skill Updated
`hf-hub-local-agents-with-llamacpp/` — expanded from 116 to ~400 lines with complete Local Apps ecosystem coverage including hardware profiling, `-hf` architecture, cross-app comparison, zero-cost patterns, and troubleshooting guide.
