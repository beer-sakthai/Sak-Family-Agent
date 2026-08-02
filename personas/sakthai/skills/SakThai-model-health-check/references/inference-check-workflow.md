# Inference Check Workflow — Cron Eval Pattern

## When to Use
Verify whether a specific HF model works on serverless inference from a cron job or autonomous agent with no user present.

## Standard Probe Procedure (3-Level Fallback Chain)

### Level 1: Router Chat Completions (preferred for chat/text models)
```bash
curl -s -w "\n__HTTP_CODE__:%{http_code}\n__TIME_TOTAL__:%{time_total}\n" \
  -X POST "https://router.huggingface.co/v1/chat/completions" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "OWNER/MODEL_NAME",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

### Level 2: Router Text Generation (for text-generation-only models)
```bash
curl -s -w "\n__HTTP_CODE__:%{http_code}\n__TIME_TOTAL__:%{time_total}\n" \
  -X POST "https://router.huggingface.co/hf-inference/models/OWNER/MODEL_NAME" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "Hello world", "parameters": {"max_new_tokens": 50}}'
```

### Level 3: Classic Inference API (often DNS-blocked in sandboxes)
```bash
curl -s -w "\n__HTTP_CODE__:%{http_code}\n__TIME_TOTAL__:%{time_total}\n" \
  -X POST "https://api-inference.huggingface.co/models/OWNER/MODEL_NAME" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "Hello world"}'
```
**Known limitation:** `api-inference.huggingface.co` is frequently blocked by DNS in sandbox/cloud environments (exit code 6). This is not a model issue — fall back to Levels 1/2.

### Level 4: huggingface_hub Python client (fallback via library DNS)
```python
from huggingface_hub import InferenceClient
client = InferenceClient(token=HF_TOKEN)
result = client.chat_completion(model="OWNER/MODEL_NAME", ...)
```

## Known Error Codes for GGUF / Unsupported Models

| Error | Meaning | What to do |
|-------|---------|-----------|
| `model_not_supported` / "not a chat model" | Model is GGUF vision/embedding/tts architecture unsupported by serverless inference | Run locally with llama.cpp or deploy via Inference Endpoints with custom container |
| `model_not_supported` / "Model not supported by provider hf-inference" | **PEFT/LoRA adapter** — LoRA adapters cannot be loaded on serverless inference at all | Merge LoRA into base model and push as standalone, or use Inference Endpoints with TGI `--adapter-id` |
| `StopIteration` from `huggingface_hub.InferenceClient` | Provider mapping is empty (no deployment exists for this model) | Fall back to Level 2 router endpoint or switch to local inference |
| `000` curl exit code 6 | DNS resolution failure (sandbox blocks `api-inference.huggingface.co`) | Use router endpoint instead |
| `429` | Rate limited | Exponential backoff, retry after delay |
| `503` | Model loading | Retry after 10-30s (cold start) |

## YAML Report Format

Upload results to the model repo under `.eval_results/inference-check-{timestamp}.yaml`:

```yaml
# Variant A: Chat/model not supported (GGUF vision, embedding, TTS, etc.)
inference_check:
  timestamp: "2026-07-30T12:00:00Z"
  model: "OWNER/MODEL_NAME"
  test: "serverless_inference"
  attempts:
    - method: "router_chat_completions"
      endpoint: "https://router.huggingface.co/v1/chat/completions"
      http_status: 400
      error: "model_not_supported"
      message: "The requested model is not a chat model."
      response_time_s: 0.121
      note: "GGUF vision models require local llama.cpp or Inference Endpoints"
  conclusion: "Brief assessment of why the model failed/passed"
  recommendation: "Actionable next step"

# Variant B: PEFT/LoRA adapter (no provider support at all)
inference_check:
  model: "OWNER/MODEL_NAME-lora"
  type: "peft_lora_adapter"
  base_model: "BASEMODEL_NAME"
  timestamp: "2026-07-30T23:49:50Z"
  endpoint: "router.huggingface.co/hf-inference/models"
  status: "unsupported"
  http_status: 400
  response_time_s: 0.17
  error: "Model not supported by provider hf-inference"
  detail: "LoRA/PEFT adapters cannot be loaded directly via HF serverless Inference API."
  suggestions:
    - "Merge LoRA weights into base model and push as standalone"
    - "Use Inference Endpoints with TGI --adapter-id"
    - "Use local llama.cpp with merged GGUF"
```

Upload via Python:
```python
from huggingface_hub import HfApi, get_token
import yaml, os
from datetime import datetime, timezone

api = HfApi(token=get_token())
ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
filename = f'inference-check-{ts}.yaml'
filepath = f'/tmp/{filename}'

with open(filepath, 'w') as f:
    yaml.dump(results, f, default_flow_style=False, sort_keys=False)

api.upload_file(
    path_or_fileobj=filepath,
    path_in_repo=f'.eval_results/{filename}',
    repo_id='OWNER/MODEL_NAME',
    repo_type='model'
)
```
