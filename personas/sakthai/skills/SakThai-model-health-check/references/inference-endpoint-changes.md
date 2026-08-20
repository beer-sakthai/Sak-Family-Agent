# Inference Endpoint Changes — 2026-07-30

## api-inference.huggingface.co is DECOMMISSIONED

**Verified 2026-07-30** via Cloudflare DNS query (`cloudflare-dns.com/dns-query?name=api-inference.huggingface.co`):

- Returns **Authority-only** with zero A/AAAA records
- `curl: (6) Could not resolve host` — confirmed via Docker, Python `socket.getaddrinfo`, and `getent`
- The hostname has been fully decommissioned; all inference now routes through `router.huggingface.co`

### Current inference endpoints

| Purpose | Endpoint | Notes |
|---------|----------|-------|
| Chat completions (OpenAI-compatible) | `https://router.huggingface.co/v1/chat/completions` | Default for chat models |
| TGI-style text generation | `https://router.huggingface.co/hf-inference/models/{model_id}` | For `text-generation` pipeline |
| Vision/multimodal chat | `https://router.huggingface.co/hf-inference/models/{model_id}/v1/chat/completions` | For `image-to-text` pipeline |

### GGUF vision models on serverless inference

**LLaVA-style GGUF vision models are unsupported** on HF serverless inference. These models require both a `.gguf` weights file AND a `mmproj-*.gguf` multimodal projection file loaded together via `llama-cli --mmproj`.

Tested with `Nanthasit/sakthai-vision-7b` (LLaVA-1.5 7B, GGUF Q4_K_M):

| Endpoint | HTTP | Response |
|----------|:----:|----------|
| `router.huggingface.co/v1/chat/completions` | 400 | `"The requested model 'Nanthasit/sakthai-vision-7b' is not a chat model"` |
| `router.huggingface.co/hf-inference/models/...` | 400 | `"Model not supported by provider hf-inference"` |

**Workarounds:**
1. Local: `llama-cli --mmproj mmproj-model-f16.gguf -m llava-1.5-7b-hf-q4_k_m.gguf --image <path>`
2. HF Inference Endpoint with custom llama.cpp Docker container
3. Convert to safetensors Transformers format for serverless compatibility

### Why this matters for health checks

The "Inference Availability Probe" mode will correctly detect GGUF vision models as "reachable but unsupported" — the router responds promptly (180-223ms) but with a 400 error. This is **not a failure** — it's a format limitation. The probe should report:
- `status: unsupported_format` not `status: failing`
- `reason: GGUF vision model requires local inference with --mmproj`

The old fallback to `api-inference.huggingface.co` for unsupported models no longer works — that hostname is gone. Always use `router.huggingface.co` exclusively.
