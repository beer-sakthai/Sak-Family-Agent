# TGI Ecosystem Learning — Run 3/5 of hf-github-learn

## Date: 2026-07-29
## Repo: huggingface/text-generation-inference

### Maintained by: The HF Serving Team

## Strategic Signal: TGI in Maintenance Mode

TGI (v3.3.5) is **now in maintenance mode** (announced on README). Hugging Face is actively directing users toward:

| Engine | When to Use |
|--------|------------|
| **vLLM** | Production serving on NVIDIA GPUs, PagedAttention, continuous batching, tensor parallelism |
| **SGLang** | Structured generation, RadixAttention, efficient prefix sharing |
| **llama.cpp** | CPU/local/edge inference, GGUF quantization |
| **MLX** | Apple Silicon inference |

**Impact on Sak Ecosystem:** We already have `hf-jobs-serving-vllm` skill and use llama.cpp CLI locally. This confirms our direction is aligned with HF's recommended path. No action needed — we're already on the right track.

## TGI Architecture (v3 backend)

```
┌──────────────────────────────────────────────┐
│                   Client                      │
└────────────┬─────────────────────┬────────────┘
             │ HTTP (generate_stream) │ gRPC (Kubernetes)
             ▼                       ▼
┌──────────────────────────────────────────────┐
│              Router (Rust)                    │
│  - Request batching, continuous scheduling    │
│  - Token streaming (SSE), stop sequences      │
│  - OpenTelemetry, Prometheus metrics          │
│  - OpenAI-compatible Messages API             │
│  - Validation (max tokens, logits warper)     │
└─────────────────────┬────────────────────────┘
                      │ gRPC
                      ▼
┌──────────────────────────────────────────────┐
│           Backend (v3 Rust)                   │
│  - PagedAttention block allocator             │
│  - Radix tree prefix caching                  │
│  - Chunked prefill (progressive)              │
│  - Quantization: AWQ, GPTQ, bitsandbytes, fp8 │
│  - Speculative decoding (Medusa + N-gram)     │
└──────────────────────────────────────────────┘
```

## Speculative Decoding — Zero-Training Path

Two methods in TGI:

### 1. Medusa (Trained Heads)
- Fine-tune extra LM heads on top of base model
- Each head predicts token at position t+N
- Pre-trained heads on HF: `text-generation-inference/gemma-7b-it-medusa` etc.
- **Training guide:** `docs/source/basic_tutorials/train_medusa.md` in TGI repo

### 2. N-gram (Zero Training, ~2x speedup)
- `--speculate N` — no training, no additional model
- Drafts tokens by matching against previous context
- Best for code/repetitive text
- Works out-of-the-box on any model
- **llama.cpp equivalent:** `--draft N` (requires `LLAMA_SPECULATIVE=ON` at build time)

### Verdict for Sak Ecosystem
- Our local llama.cpp was built **without** `LLAMA_SPECULATIVE` flag
- Not a priority to rebuild — we use opencode-go (DeepSeek V4 Flash) for chat, not local serving
- **Documented for future:** If we ever serve a Sak model locally via llama-server, rebuild with `cmake -DLLAMA_SPECULATIVE=ON` and use `--draft N` for free speedup

## Chunked Prefill (v3 Backend)
- Long prompts split into chunks for progressive PagedAttention
- Interleaves prefilling with decoding to avoid OOM
- Relevant for 128K-context models like our `sakthai-context-7b-128k`
- **llama.cpp equivalent:** `--chunks N` or handled automatically with `--ctx-size`

## Multi-Backend Architecture
TGI supports 4 backends through a unified Router → gRPC → Backend interface:

1. **TGI CUDA (v3)** — Default, PagedAttention, NVIDIA-optimized
2. **TGI TRTLLM** — NVIDIA TensorRT, needs model compilation per GPU arch
3. **TGI Llamacpp** — GGUF support, CPU + GPU via llama.cpp
4. **TGI Neuron** — AWS Trainium/Inferentia

**Key takeaway:** The multi-backend Router pattern (Rust gRPC gateway + pluggable backends) is how HF productionizes inference at scale. Not directly applicable to our single-model setup but useful architectural reference.
