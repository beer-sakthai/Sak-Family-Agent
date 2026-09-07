---
name: SakThai-hf-inference-endpoints
description: "Hugging Face Inference Endpoints — deploy, manage, scale, and monitor production-grade model endpoints via the Python SDK and REST API. Covers creation, lifecycle, auto-scaling, pause/resume, scale-to-zero, custom containers, and cost optimization."
---

# Hugging Face Inference Endpoints

Inference Endpoints is a managed service to deploy AI models to production on dedicated infrastructure. You select the hardware (CPU/GPU/Neuron), configure auto-scaling, and get a secure HTTPS endpoint with an OpenAI-compatible API.

> **Zero-cost notice**: Inference Endpoints are a **paid** service requiring an active HF subscription + credit card. This skill documents the API and lifecycle for when deployment budget exists. The free alternative is ZeroGPU Spaces or serverless Inference Providers (covered in `spaces-zerogpu` skill).

## API Endpoint

```
Base: https://api.endpoints.huggingface.cloud/v2
Auth: Bearer <HF_TOKEN>
```

## Python SDK — Quick Reference

All methods live on `HfApi` or the `InferenceEndpoint` object from `huggingface_hub`.

**Key constants:**
```python
INFERENCE_ENDPOINTS_ENDPOINT = "https://api.endpoints.huggingface.cloud/v2"  # REST API base
INFERENCE_ENDPOINT = "https://api-inference.huggingface.co"                  # serverless inference
```

### Import & Setup

```python
from huggingface_hub import HfApi

api = HfApi()
```

### Status Enum

| Status | Meaning |
|--------|---------|
| `pending` | Being created |
| `initializing` | Container starting |
| `updating` | Config/model update in progress |
| `updateFailed` | Update failed |
| `running` | Ready to serve |
| `paused` | Manually paused — no billing |
| `failed` | Deployment failed |
| `scaledToZero` | Auto-scaled down — no billing, resumes on request |

### Type Enum (access control)

- `"public"` — anyone can access (if they know the URL)
- `"authenticated"` — requires a valid HF token (recommended)
- `"private"` — requires specific token + IP allowlist

### Create an Endpoint

```python
endpoint = api.create_inference_endpoint(
    name="my-llm-endpoint",         # unique name within namespace
    repository="mistralai/Mistral-7B-Instruct-v0.3",
    framework="pytorch",             # "pytorch", "custom", etc.
    accelerator="gpu",               # "cpu", "gpu", "neuron"
    instance_size="small",           # "small", "medium", "large", "xlarge"
    instance_type="nvidia-a10g",     # or "intel-icl", "amd-milan", "aws-tn", etc.
    region="eu-west-1",              # e.g. "us-east-1", "eu-west-1"
    vendor="aws",                    # "aws", "azure", "gcp"
    min_replica=1,                   # minimum running instances
    max_replica=5,                   # max auto-scale instances
    scale_to_zero_timeout=15,        # minutes before scaling to zero on idle
    task="text-generation",
    revision="main",                 # model branch/commit
    type="authenticated",
    # Optional advanced:
    # secrets={"MY_API_KEY": "sk-..."},
    # env={"LOG_LEVEL": "debug"},
    # custom_image={"url": "...", "command": ["..."], "args": ["..."]},
)
print(f"Created {endpoint.name}, status: {endpoint.status}")
```

### Create from Catalog (simplified)

The [Inference Catalog](https://endpoints.huggingface.co/catalog) has pre-tested, optimized configs:

```python
endpoint = api.create_inference_endpoint_from_catalog(
    repo_id="mistralai/Mistral-7B-Instruct-v0.3",
    name="my-mistral",  # optional, auto-generated if omitted
    accelerator="gpu",
)
```

### List Endpoints

```python
# List all endpoints for current user
endpoints = api.list_inference_endpoints()

# List for a specific org
endpoints = api.list_inference_endpoints(namespace="my-org")

# List ALL endpoints across user + all orgs
endpoints = api.list_inference_endpoints(namespace="*")
```

### Get a Single Endpoint

```python
ep = api.get_inference_endpoint("my-llm-endpoint")
# or for an org:
ep = api.get_inference_endpoint("my-llm-endpoint", namespace="my-org")
```

### Run Inference

Once the endpoint status is `"running"`, get a client:

```python
# Synchronous client
client = ep.client
response = client.text_generation(
    "What is the capital of France?",
    max_new_tokens=100,
)
print(response)

# Async client
aclient = ep.async_client
```

The client is a standard `InferenceClient` pointing at your endpoint URL. Works with all HF inference methods (`text_generation`, `text_classification`, `image_generation`, etc.).

### Lifecycle Operations

```python
# Wait until endpoint is ready (blocks)
ep.wait(timeout=300)         # 5 minute timeout
ep.wait()                    # wait indefinitely (polling every 5s)

# Refresh status
ep.fetch()

# Pause — stop billing, requires manual resume
ep.pause()

# Resume
ep.resume()

# Scale to zero — no billing, auto-resumes on next request
ep.scale_to_zero()

# Update configuration
ep.update(
    accelerator="gpu",
    instance_size="medium",
    min_replica=2,
    max_replica=10,
    scale_to_zero_timeout=30,
    # Can also update model:
    # repository="new-model-id",
    # revision="v2.0",
)

# Delete permanently
ep.delete()
```

### Update Endpoint (detailed)

```python
api.update_inference_endpoint(
    name="my-endpoint",
    # Compute updates
    accelerator="gpu",
    instance_size="large",
    instance_type="nvidia-a100",
    min_replica=1,
    max_replica=3,
    scale_to_zero_timeout=15,
    # Scaling policy
    scaling_metric="pendingRequests",  # or "hardwareUsage"
    scaling_threshold=0.8,             # scale when 80% utilization
    # Model updates
    repository="new-model-id",
    framework="pytorch",
    revision="main",
    task="text-generation",
    # Route
    domain="my-custom-domain.com",
    path="/v1/chat/completions",
    # Other
    cache_http_responses=True,
    tags=["production", "llm"],
)
```

## REST API (direct)

If you prefer curl:

```bash
# List endpoints
curl -H "Authorization: Bearer $HF_TOKEN" \
  https://api.endpoints.huggingface.cloud/v2/endpoint/{namespace}

# Create
curl -X POST -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-endpoint",
    "model": {
      "repository": "mistralai/Mistral-7B-Instruct-v0.3",
      "framework": "pytorch",
      "revision": "main",
      "task": "text-generation",
      "image": {}
    },
    "compute": {
      "accelerator": "gpu",
      "instanceSize": "small",
      "instanceType": "nvidia-a10g",
      "scaling": {
        "minReplica": 1,
        "maxReplica": 5,
        "metric": "pendingRequests",
        "threshold": 0.8,
        "zeroScaleTimeout": 15
      }
    },
    "region": "eu-west-1",
    "vendor": "aws",
    "type": "authenticated"
  }' \
  https://api.endpoints.huggingface.cloud/v2/endpoint/{namespace}

# Pause
curl -X POST -H "Authorization: Bearer $HF_TOKEN" \
  https://api.endpoints.huggingface.cloud/v2/endpoint/{namespace}/{name}/pause

# Resume
curl -X POST -H "Authorization: Bearer $HF_TOKEN" \
  https://api.endpoints.huggingface.cloud/v2/endpoint/{namespace}/{name}/resume

# Scale to zero
curl -X POST -H "Authorization: Bearer $HF_TOKEN" \
  https://api.endpoints.huggingface.cloud/v2/endpoint/{namespace}/{name}/scale-to-zero

# Delete
curl -X DELETE -H "Authorization: Bearer $HF_TOKEN" \
  https://api.endpoints.huggingface.cloud/v2/endpoint/{namespace}/{name}
```

## Inference Engines

| Engine | Use Case | Framework Value |
|--------|----------|----------------|
| **vLLM** | High-throughput LLM serving (PagedAttention) | `"vllm"` or custom image |
| **TGI** (Text Generation Inference) | Optimized text generation | `"text-generation-inference"` |
| **SGLang** | Structured generation with constrained decoding | Custom image |
| **TEI** (Text Embeddings Inference) | Embedding models (BERT, sentence-transformers) | Custom image |
| **llama.cpp** | GGUF models, CPU-friendly | Custom image |
| **Inference Toolkit** | General-purpose inference | `"pytorch"`, `"onnx"` |
| **Custom Container** | Bring your own Docker image | `"custom"` + `custom_image` dict |

### Using a Custom Inference Engine (TGI example)

```python
endpoint = api.create_inference_endpoint(
    name="tgi-llama",
    repository="meta-llama/Llama-3.2-3B-Instruct",
    framework="custom",  # must be "custom" for custom image
    accelerator="gpu",
    instance_size="small",
    instance_type="nvidia-a10g",
    region="eu-west-1",
    vendor="aws",
    custom_image={
        "url": "ghcr.io/huggingface/text-generation-inference:3.2.0",
        "health_route": "/health",
        "env": {
            "MAX_INPUT_LENGTH": "4096",
            "MAX_TOTAL_TOKENS": "8192",
        },
    },
    task="text-generation",
    type="authenticated",
)
```

## Pricing

- **Hourly billing** per instance (replica), metered per minute
- **Paused / scaled-to-zero** = no billing
- **Instance types** vary by vendor/region and include:
  - CPU: `intel-icl` (small to xlarge, different vCPU/RAM)
  - GPU: `nvidia-t4`, `nvidia-a10g`, `nvidia-a100`, `nvidia-h100`
  - AWS Trainium: `aws-tn-1`, `aws-tn-2`
  - Google TPU: `gcp-tpu-v5e`
- See [pricing page](https://huggingface.co/pricing) for exact rates
- Billing starts when endpoint reaches `running` status, stops when `paused` or `scaledToZero`

## Auto-Scaling Configuration

```python
endpoint = api.create_inference_endpoint(
    ...,
    min_replica=1,      # minimum running instances
    max_replica=10,     # max scale-out
    scale_to_zero_timeout=15,   # minutes idle before → zero
    scaling_metric="pendingRequests",   # scale on queue depth
    scaling_threshold=0.8,       # scale when metric hits 80%
)
```

Two scaling metrics:
- `"pendingRequests"` — number of queued requests
- `"hardwareUsage"` — CPU/GPU utilization

## Security & Compliance

- **AWS PrivateLink** — expose endpoint inside a VPC (no internet)
- **Custom Router** — custom domain, path routing
- **Type** controls access at the API level
- **Secrets** — inject env vars (API keys, tokens) without exposing in config
- **Logs** — stream to your observability pipeline

## Known Pitfalls

- **Endpoints cost money** — even running idle you're billed per replica per hour. Always pause or scale-to-zero when not in use.
- **Cold start on scale-to-zero** — first request after scale-to-zero takes 20-60s to spin up.
- **Instance availability varies by region** — not all instance types exist in all regions.
- **Framework must match model** — custom frameworks may need custom images.
- **Secrets are write-only** — you can set them, but the API never returns their values.
- **Namespace required for org endpoints** — always pass `namespace="org-name"` when working with org-owned endpoints.
- **Delete is irreversible** — use `pause()` or `scale_to_zero()` instead of `delete()` unless you're certain.
- **`update()` triggers a rolling restart** — brief downtime.

## Verification

```python
from huggingface_hub import HfApi

api = HfApi()
# List endpoints (requires subscription)
try:
    eps = api.list_inference_endpoints(namespace="*")
    print(f"Found {len(eps)} endpoints across all namespaces")
except Exception as e:
    print(f"No active subscription or auth error: {e}")
```
