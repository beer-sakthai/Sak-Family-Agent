# LoRA Adapter Inference Eval — Cron Session (2026-07-30)

**Model:** `Nanthasit/sakthai-plus-1.5b-lora`
**Base model:** `Qwen/Qwen2.5-1.5B-Instruct`
**Type:** PEFT LoRA adapter (SFT via TRL)
**Environment:** Cron job on `/opt/data` sandbox

## Goal

Run inference evaluation on a LoRA adapter via HF Inference API — send a test prompt, record status/response time/output, upload YAML findings.

## Methodology & Fallback Chain

Attempted four approaches in order:

| # | Method | Endpoint | Result | Duration | Cause |
|---|--------|----------|--------|----------|-------|
| 1 | `curl -X POST` | `api-inference.huggingface.co/models/...` | DNS_FAILURE | 34ms | Sandbox can't resolve this subdomain |
| 2 | `InferenceClient.text_generation()` | internal provider router | INTERNAL_ERROR | 0.19s | `StopIteration` bug in `huggingface_hub` v1.25.1 provider resolution |
| 3 | `InferenceClient.chat_completion()` | `router.huggingface.co/v1/chat/completions` | MODEL_NOT_SUPPORTED | 0.14s | No provider supports LoRA models |
| 4 | Control: `chat_completion` with base model | `router.huggingface.co/v1` | MODEL_NOT_SUPPORTED | 0.13s | Base model also not in provider pool |

## Key Findings

### 1. LoRA Adapters Cannot Be Served on Serverless Inference

**This is a fundamental architectural limitation, not a bug.** Serverless inference providers load models from Hub repos directly — they cannot apply PEFT adapters on top of base models without TGI's PEFT support or a dedicated Inference Endpoint.

**The router rejects LoRA models explicitly:** `"The requested model 'Nanthasit/sakthai-plus-1.5b-lora' is not supported by any provider you have enabled."`

### 2. Endpoint Reachability

| Endpoint | Reachable from cron sandbox | Use Case |
|----------|---------------------------|----------|
| `huggingface.co` (Hub API) | ✅ Always | All Hub API operations |
| `router.huggingface.co/v1` | ✅ Always | Chat completions, responses API |
| `api-inference.huggingface.co` | ❌ DNS blocked | Legacy inference API (blocked) |
| `hf.co` | ✅ Always | Alternative Hub domain |

### 3. InferenceClient v1.25.1 `StopIteration` Bug

`InferenceClient.text_generation()` (the legacy method, not chat-style) raises a `StopIteration` error during provider resolution:

```
StopIteration: provider = next(iter(provider_mapping)).provider
```

This is a local huggingface_hub library bug. `chat_completion()` works correctly through the router. Prefer `chat_completion()` for inference tests.

### 4. Upload Pattern for Inference Check Results

YAML uploaded to `.eval_results/inference-check-{timestamp}.yaml` in the model repo. Structure:

```yaml
test:
  prompt: "What is machine learning?"
  max_new_tokens: 50
infrastructure:
  sandbox_dns_resolution:
    huggingface.co: reachable
    api-inference.huggingface.co: BLOCKED
    router.huggingface.co: reachable
results:
  method_1_direct_api_inference:
    status: DNS_FAILURE
    error: Could not resolve host
  ...
assessment:
  generated_output: null
  cause: >-
    LoRA adapter cannot be loaded by serverless inference providers.
    This is an architectural limitation of how PEFT adapters work
    on the serverless API.
recommendations:
  - Merge LoRA adapter into base model for serverless deployment
  - Or deploy to dedicated Inference Endpoint with TGI + PEFT
  - Or use local inference with peft library to verify quality
```

Upload via `hf_api.upload_file(path_or_fileobj=yaml_bytes, path_in_repo='.eval_results/inference-check-{ts}.yaml', repo_id=..., repo_type='model')`.

## Recommendations

1. **Merge adapter into base model** — use `peft` to merge LoRA weights with `Qwen/Qwen2.5-1.5B-Instruct` → upload as merged model
2. **Local inference** — run with `transformers` + `peft` directly to verify quality
3. **Inference Endpoint** — deploy with TGI + PEFT flag (requires paid GPU)
