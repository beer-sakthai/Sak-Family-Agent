# Example inference check output (2026-07-30 cron run)

```yaml
# Inference Check: 20260730-232720
---
model: Nanthasit/sakthai-vision-7b
timestamp: 20260730-232720
unix_ts: 1785454040
pipeline_tag: image-to-text
format: GGUF (LLaVA-1.5)

attempts:
  openai_chat_route:
    endpoint: https://router.huggingface.co/v1/chat/completions
    http_status: 400
    time_ms: 180
    error: "The requested model 'Nanthasit/sakthai-vision-7b' is not a chat model."
    code: model_not_supported
  tgi_inference_route:
    endpoint: https://router.huggingface.co/hf-inference/models/Nanthasit/sakthai-vision-7b
    http_status: 400
    time_ms: 223
    error: "Model not supported by provider hf-inference"
    code: model_not_supported
  legacy_api_inference:
    endpoint: https://api-inference.huggingface.co/models/Nanthasit/sakthai-vision-7b
    dns_status: NXDOMAIN - hostname has no A records
    note: api-inference.huggingface.co appears decommissioned

conclusion: "GGUF vision models cannot be served via HF serverless inference."

recommendations:
  - "Run locally: llama-cli --mmproj mmproj-model-f16.gguf -m llava-1.5-7b-hf-q4_k_m.gguf --image <path>"
  - "Or deploy to HF Inference Endpoint with custom llama.cpp Docker image"
  - "Or convert to safetensors Transformers format for serverless compatibility"
```
