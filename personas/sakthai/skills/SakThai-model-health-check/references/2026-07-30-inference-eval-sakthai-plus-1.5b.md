# Inference Eval: sakthai-plus-1.5b (2026-07-30)

## Summary

Attempted serverless inference evaluation on `Nanthasit/sakthai-plus-1.5b` via HF Inference API. Model is not available on any serverless provider — returned `400 Model not supported by provider hf-inference`.

## Timeline

1. **Primary attempt** — `curl POST` to `router.huggingface.co/hf-inference/models/Nanthasit/sakthai-plus-1.5b`
   - Status: 400
   - Time: 0.13s
   - Error: `Model not supported by provider hf-inference`

2. **SDK fallback** — `huggingface_hub InferenceClient.chat_completion()`
   - Status: `BadRequestError` — "The requested model is not supported by any provider you have enabled"
   - Same root cause as the curl attempt

3. **Local inference (BF16)** — `transformers` full-precision load
   - Status: OOM (exit 137)
   - Environment: 7.8GB RAM total, only 1.4GB available at time of attempt
   - Model weights: 2.9GB (BF16 safetensors) — cannot fit

4. **Local inference (4-bit)** — `transformers` + `bitsandbytes` 4-bit quantization
   - Status: OOM (exit 137)
   - Failed to load CPU gemm kernel before OOM

## Root Cause

The model is a fine-tuned Qwen2.5-1.5B-Instruct (safetensors, BF16). It has:
- `transformers` library format (not GGUF)
- Full model weights (not LoRA adapter)
- No inference endpoint configured
- Not onboarded to any HF Inference provider

HF serverless inference only serves models that are explicitly onboarded/sponsored by providers (Together, Replicate, Sambanova, etc.). Fine-tunes of existing architectures are NOT automatically available — each model variant must be individually enabled.

## Inference Check YAML Format

File: `.eval_results/inference-check-{YYYYMMDDTHHMMSSZ}.yaml`

```yaml
check:
  timestamp: 20260730T231504Z
  model: Nanthasit/sakthai-plus-1.5b
  method: HF Inference API (router.huggingface.co)
  endpoint: https://router.huggingface.co/hf-inference/models/Nanthasit/sakthai-plus-1.5b
results:
  status: not_available
  http_code: 400
  response_time_seconds: 0.13
  error: "Model not supported by provider hf-inference"
alternative_attempts:
  - method: "huggingface_hub InferenceClient.chat_completion"
    status: "model_not_supported"
  - method: "Local transformers (BF16, full precision)"
    status: "OOM (exit 137)"
    detail: "7.8GB RAM total, 1.4GB available; weights 2.9GB"
  - method: "Local transformers (4-bit bitsandbytes)"
    status: "OOM (exit 137)"
recommendations:
  - "Convert model to GGUF format for llama.cpp inference (lower memory)"
  - "Onboard model to HF serverless inference providers"
```

## Key Observations

| Issue | Resolution |
|-------|-----------|
| `api-inference.huggingface.co` DNS failure | Use `router.huggingface.co/hf-inference/models/{id}` instead |
| "Model not supported by provider" | Not a transient error — record as "not_available" and stop. Do NOT retry with paid alternatives. |
| OOM on local inference | Environment has 7.8GB RAM, only 1.4GB free. 1.5B BF16 model needs ~3GB+. Constraints are real and not fixable from inside the session. |

## Related Skills

- `sakthai-model-health-check` — contains the Inference Benchmark Eval procedure this session exercised
- `SakThai-hf-inference-client-serverless-inference-patterns` — API syntax and provider selection policies

## Next Steps for This Model

- Convert to GGUF (via `llama.cpp/convert.py` or `hf-to-gguf`) — enables local inference with ~2GB RAM
- Upload GGUF to HF model repo for broader accessibility
- Re-run inference check after conversion
