# Docker Space Multi-Model Analysis

## Recognizing multi-model orchestration Spaces

Some of the most architecturally interesting Spaces chain **two or more AI models** across independent providers. These are not single-model demos — they are miniature AI applications that orchestrate text generation + image/audio/video generation in a pipeline.

### Telltale signs

Check these in the Space's API metadata and source files:

| Signal | What to look for |
|--------|-----------------|
| **CPU hardware with heavy inference** | `runtime.hardware.current = "cpu-basic"` but the Space generates images/video — means it's API-backed, not running models locally |
| **Multiple provider SDKs in package.json** | `openai`, `@anthropic-ai/sdk`, `groq-sdk`, `replicate`, `@huggingface/inference` in the same file |
| **Configurable engine env vars** | `LLM_ENGINE`, `RENDERING_ENGINE`, `AUTH_*_API_KEY` in `.env` or README |
| **OAuth with inference-api scope** | `hf_oauth: true` + `hf_oauth_scopes: ["inference-api"]` in cardData — users bring their own HF tokens |
| **Docker SDK** | `sdk: "docker"` — custom backend, not limited to Gradio/Streamlit |

### Analysis workflow for Docker Spaces

```
1. Fetch API metadata → check sdk, hardware, oauth, models
2. Fetch siblings list → understand file structure
3. Fetch README.md → understand env vars, architecture
4. Fetch Dockerfile → base image, build pipeline
5. Fetch package.json → provider SDKs, UI framework
6. Fetch key source files → lib/ and app/api/ for Docker/Next.js
```

### Case study: jbilcke-hf/ai-comic-factory

**Architecture:** Two-stage pipeline — LLM writes script → SDXL renders panels

**Stage 1 — Script generation (LLM):**
- Default: Zephyr 7B (HuggingFaceH4/zephyr-7b-beta) via HF Inference Endpoint
- Alternatives: GPT-4 Turbo, Claude 3 Opus, Mixtral 8x7B (Groq)
- Configurable via `LLM_ENGINE` env var (INFERENCE_API, INFERENCE_ENDPOINT, OPENAI, GROQ, ANTHROPIC)

**Stage 2 — Panel rendering (Image):**
- Default: SDXL via HF Inference API (stabilityai/stable-diffusion-xl-base-1.0 + refiner)
- Alternatives: Replicate, custom VideoChain API, OpenAI DALL-E
- Configurable via `RENDERING_ENGINE` env var

**Key architectural patterns:**
- Each stage is fully decoupled — any LLM + any image provider, independently configured
- OAuth with `hf_oauth_scopes: ["inference-api"]` lets users pay for their own inference
- CPU-only hardware (`cpu-basic`) — all heavy work offloaded to inference APIs
- Next.js 14 app with Docker — 257 files, production-grade CI/CD
- `react-konva` (Konva.js) for interactive canvas editing of generated panels
- State management via Zustand, UI via Radix primitives

**What to extract for reports:**
1. Chain architecture (which models, in what order)
2. Decoupling pattern (are providers swappable?)
3. Auth/OAuth design (who pays for inference?)
4. Hardware profile (CPU with API-backing vs GPU running local models)
5. UI framework and canvas/interaction layer
