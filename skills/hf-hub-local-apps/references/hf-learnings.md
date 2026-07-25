# HF Learnings Log — hf-hub-local-apps

## 2026-07-25: Hugging Face Hub — Use AI Models Locally with Local Apps

### Summary
Deep-dive into the HF Hub's Local Apps integration — the setting, UI flow, and four supported local inference apps (llama.cpp, Ollama, Jan, LM Studio). Also covers the Hardware profile setting (TFLOPS badge, model compatibility panel) that pairs with Local Apps for zero-cost local inference. This is a 2026-era feature that makes running GGUF/MLX models from the Hub a one-click (or one-command) experience.

### Key Findings

#### 1. Enabling Local Apps

**Location**: https://huggingface.co/settings/local-apps

The Local Apps settings page lists all supported applications. Toggle each one you have installed. When enabled, model pages with supported file types (GGUF, MLX) show a **"Use this model"** dropdown with options for each enabled app.

**Flow**:
1. Go to Settings → Local Apps
2. Toggle on the apps you have installed (llama.cpp, Ollama, Jan, LM Studio)
3. Browse to any model page with GGUF/MLX files
4. Click "Use this model" dropdown → select your app
5. Copy the provided command snippet and paste into terminal (or click "Open in app")

**Per-app behavior**:
- **llama.cpp**: Shows a terminal command (`llama-server -hf <repo>:<quant>`)
- **Ollama**: Shows an `ollama run` command
- **Jan**: Opens the app directly (GUI)
- **LM Studio**: Opens the app directly, or shows download prompt if not installed

---

#### 2. Supported Apps Deep Dive

##### Llama.cpp

**Installation**:
- macOS/Linux: `brew install llama.cpp`
- Windows: `winget install llama.cpp`
- Build from source: clone `ggerganov/llama.cpp`, run CMake build

**Command format** (from "Use this model"):
```sh
# Chat server (OpenAI-compatible endpoint)
llama-server -hf unsloth/gpt-oss-20b-GGUF:Q4_K_M

# CLI mode
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

**Key points**:
- The `-hf` flag downloads + caches the model automatically (cache location: `$LLAMA_CACHE`)
- Server mode gives a `/v1/chat/completions` OpenAI-compatible endpoint on `localhost:8080`
- Quantization selection via `:` after the model path (e.g., `Q4_K_M`, `Q8_0`, `Q6_K`)
- Hardware acceleration: CUDA (`-DGGML_CUDA=ON`), Metal (auto on macOS), ROCm, SYCL
- Multiple interface options: CLI, server, Python bindings, various UIs
- Already covered in depth in `hf-gguf-llama-cpp` skill — this page focuses on the HF Hub integration

**Key advantages**:
- Extremely fast CPU inference (AVX2, NEON optimizations)
- Low resource usage — runs on 4GB RAM systems with quantized models
- Multiple hardware backends

##### Ollama

**Installation**: Download from https://ollama.ai — single binary, cross-platform

**Command format**:
```sh
ollama run hf.co/unsloth/gpt-oss-20b-GGUF:Q4_K_M
```

**Key points**:
- The `hf.co/` prefix tells Ollama to fetch directly from Hugging Face Hub
- Ollama manages model downloads, caching, and serving automatically
- Integrates with Ollama's own Modelfile system for custom configurations
- OpenAI-compatible API server built in (`ollama serve`)
- Supports GGUF models from HF without manual conversion

**Advanced Ollama + HF Integration** (new findings):
- **Custom quantization**: Override with `:tag` syntax, e.g. `ollama run hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF:IQ3_M`. Case-insensitive. Full filename also works as tag.
- **Custom chat templates**: Create a `template` file in the HF repo — must be **Go template format** (NOT Jinja), using `.System`, `.Prompt`, `.Response` variables
- **Custom system prompt**: Create a `system` file in the HF repo with default system text
- **Custom sampling params**: Create a `params` JSON file in the repo (temperature, top_p, top_k, etc.)
- **Private GGUFs**: Add `~/.ollama/id_ed25519.pub` SSH key to HF account settings → run private GGUFs with same `ollama run hf.co/{user}/{repo}` syntax
- **Domain aliases**: Both `hf.co` and `huggingface.co` work
- **Available**: 45K+ public GGUF checkpoints on the Hub as of July 2026

**Key advantages**:
- Easiest setup — single binary, minimal configuration
- Built-in model management (list, pull, rm, show)
- REST API for integration with other tools
- Active community with thousands of pre-configured models

##### Jan

**Website**: https://jan.ai
**Installation**: Download desktop app (cross-platform)

**Flow**:
1. Enable Jan in HF Local Apps settings
2. Go to a GGUF model page → "Use this model" → Jan
3. Jan opens automatically with the model loaded
4. Start chatting through Jan's GUI

**Key advantages**:
- Full offline operation — no data leaves your machine
- User-friendly GUI (chat interface, document upload)
- OpenAI-compatible API server built in
- Extensions system (document Q&A, web search, etc.)

##### LM Studio

**Website**: https://lmstudio.ai
**Installation**: Download desktop app (macOS Apple Silicon, Windows, Linux)

**Three ways to get models**:

1. **"Use this model" button** on HF model page → opens LM Studio with model loaded (or shows download prompt)
2. **In-app downloader**: Press ⌘+Shift+M (Mac) or Ctrl+Shift+M (Windows/Linux), search or paste HF URL
3. **CLI (`lms`)**: Terminal-based model management

```sh
# Search models
lms get qwen

# Filter by type
lms get qwen --mlx
lms get qwen --gguf

# Download specific model from HF URL
lms get https://huggingface.co/lmstudio-community/Ministral-3-8B-Reasoning-2512-GGUF

# Choose specific quantization
lms get https://huggingface.co/lmstudio-community/Ministral-3-8B-Reasoning-2512-GGUF@Q6_K
```

**Key advantages**:
- Intuitive GUI with model loader, chat interface, and developer tools
- Built-in model browsing with hardware compatibility indicators
- Automatically selects optimal load parameters for your hardware
- Multi-model support (GGUF and MLX)
- Free for personal and commercial use

---

#### 3. Hardware Profile Integration

The Hardware settings page (https://huggingface.co/settings/hardware) pairs directly with Local Apps:

**Setup**:
1. Add each piece of hardware you own (GPU, CPU, Apple Silicon)
2. Select provider/model (e.g., NVIDIA RTX 4090)
3. Set VRAM/RAM and quantity
4. Mark primary hardware
5. Toggle public visibility (on by default)

**Features**:
- **TFLOPS badge** on your profile — aggregated compute power estimate
- **Model compatibility panel** on GGUF/MLX model pages — estimates which quantization fits your saved hardware
- **Community hardware browsing** (https://huggingface.co/hardware) — see what others run, compare setups

**Zero-cost implications**:
- No subscription needed for hardware profile or local apps
- GGUF models from 0.5B to 70B can run on consumer hardware
- Quantization selection guided by the compatibility panel prevents downloading models too large for your system
- Hardware profile is optional — local apps work without it

---

#### 4. Key Takeaways for Zero-Cost Users

| Aspect | Assessment |
|--------|-----------|
| **Cost** | Completely free — no API calls, no inference credits, no GPU time |
| **Privacy** | Full local execution — no data leaves your machine |
| **Speed** | Limited only by your hardware, not by server capacity |
| **Setup effort** | Low for Ollama, medium for llama.cpp (build), low for Jan/LM Studio (GUI) |
| **Model selection** | Any GGUF or MLX model on HF Hub — thousands available |
| **Hardware needed** | Can run on CPU-only (llama.cpp optimized), 4GB RAM minimum for small models |
| **Integration** | "Use this model" dropdown makes discovery and launch seamless |

**Best for Beer's situation**:
- **llama.cpp** for headless/server use on the dev VM (no GPU = CPU inference)
- **Ollama** for quick experimentation with minimal setup
- **Hardware profile** to track what machines are available and find compatible models
- Small GGUF models (0.5B–3B) run on CPU with acceptable speed

### References
- https://huggingface.co/docs/hub/en/local-apps
- https://huggingface.co/docs/hub/en/ollama
- https://huggingface.co/docs/hub/en/lmstudio
- https://huggingface.co/docs/hub/en/gguf-llamacpp (llama.cpp + HF integration)
- https://huggingface.co/docs/hub/en/hardware (hardware profile page)
- https://huggingface.co/settings/local-apps
- https://huggingface.co/settings/hardware
