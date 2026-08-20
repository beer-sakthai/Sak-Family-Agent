# Skeleton Inference Probe — StopIteration & Weightless Repo Diagnostic

## Session Context

2026-07-30, cron eval of `Nanthasit/sakthai-plus-1.5b-coder`. The model had zero weight files despite claiming `endpoints_compatible` in YAML metadata and `base_model: Qwen/Qwen2.5-Coder-1.5B-Instruct`.

## Root Cause: Skeleton Repo

A **skeleton repo** on HF Hub has:
- README.md (often elaborate, with badges claiming "Inference API Compatible")
- .gitattributes (LFS config)
- `.eval_results/` YAML files from prior health checks
- **No model weight files** (no `.safetensors`, `.gguf`, `.bin`, `.pt`, `.pth`)
- **No `config.json`** (no model architecture metadata)
- Zero downloads, zero likes

The model was created (`create_repo`) but the actual fine-tuned weights were never uploaded.

## Diagnostic Signals

### 1. `InferenceClient.text_generation()` → `StopIteration`

```python
from huggingface_hub import InferenceClient
client = InferenceClient(token=TOKEN, model=MODEL)
output = client.text_generation("Hello")  # ❌ StopIteration
```

**Why:** The `get_provider_helper()` function iterates `provider_mapping`, which is empty — no provider has this model deployed. The `StopIteration` is a library-level unhandled edge case when `next()` is called on an empty iterator.

**What it means:** The model is not deployed on any HF Inference Provider. The most common cause is a skeleton repo (no weights uploaded).

### 2. Router endpoint → `400` / `404`

```
curl -X POST https://router.huggingface.co/hf-inference/models/Nanthasit/sakthai-plus-1.5b-coder
→ HTTP 400: {"error":"Model not supported by provider hf-inference"}
→ HTTP 404: Not Found (router returns 404 when model has no config.json)
```

### 3. `model_info()` → 0 downloads, 0 weight files

```python
from huggingface_hub import HfApi
info = api.model_info("OWNER/MODEL")
# info.downloads == 0, info.likes == 0
# No .safetensors in siblings
```

## Probe Methodology (Systematic)

When a model fails inference, determine the root cause by checking in this order:

### Step 1: Quick weight check (fastest signal)
```python
api = HfApi(token=HF_TOKEN)
info = api.model_info(MODEL)
has_weights = any(
    s.rfilename.endswith(ext)
    for s in info.siblings
    for ext in [".safetensors", ".gguf", ".bin", ".pt", ".pth"]
)
if not has_weights:
    # Skeleton repo — stop here, report clearly
    conclusion = "SKELETON: No model weights in repository"
```

### Step 2: If weights exist, check if config.json exists
```python
has_config = any(s.rfilename == "config.json" for s in info.siblings)
# Without config.json, HF can't determine architecture for inference
```

### Step 3: Probe inference router
```python
import requests
r = requests.post(
    f"https://router.huggingface.co/hf-inference/models/{MODEL}",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={"inputs": "test", "parameters": {"max_new_tokens": 5}},
    timeout=15,
)
# HTTP 200 = works, 400 = not supported, 404/503 = loading/unavailable
```

### Step 4: Check third-party providers via InferenceClient
```python
client = InferenceClient(token=TOKEN, model=MODEL)
for prov in ["together", "deepinfra", "novita", "fireworks-ai"]:
    try:
        client.provider = prov
        output = client.text_generation("test", max_new_tokens=5)
        print(f"{prov}: works")
    except Exception as e:
        print(f"{prov}: {type(e).__name__}: {str(e)[:100]}")
```

### Step 5: Record & upload
Write YAML to `.eval_results/inference-readiness-{timestamp}.yaml` and upload to model repo.

## Example YAML Structure
```yaml
meta:
  model: Nanthasit/sakthai-plus-1.5b-coder
  timestamp: 20260730T234609Z
  check_type: inference-readiness
model_info:
  pipeline_tag: text-generation
  private: false
  downloads: 0
  total_siblings: 10
  has_weight_files: false
  weight_files: []
  safetensors_available: false
inference_endpoints:
  - provider: hf-inference (router)
    reachable: true
    status: 404
    ms: 148
    reason: Not Found
inference_ready: false
summary: "FAIL: No model weights found in repository. The repo contains only metadata files (README.md, .gitattributes) and eval result YAMLs. No .safetensors, .gguf, .bin, .pt, or .pth files present. Model cannot be served by HF Inference API without weight files."
```

## Pitfalls to Avoid

1. **Don't trust README badges** — A model can claim "Inference API Compatible" with zero weights. Verify by checking siblings programmatically.
2. **Don't conflate "Model not supported" with "Model broken"** — A 400 from the router may mean the model simply isn't deployed yet, not that the weights are corrupt.
3. **`InferenceClient(text_generation)` is not a reliable diagnostics tool** — It raises `StopIteration` without a clear error message for skeleton repos. Use the REST API or `model_info()` for root cause analysis.
4. **DNS is not the API** — `api-inference.huggingface.co` may not resolve in sandbox/cron environments. Always use `router.huggingface.co` for modern inference checks.
5. **Upload weight files before expecting inference to work** — A model with only metadata files will never serve inference, regardless of tags, badges, or model card quality.
