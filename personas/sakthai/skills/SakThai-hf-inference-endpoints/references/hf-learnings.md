# HF Learnings Log

## 2026-07-25: hf-inference-endpoints-deep-dive-v2 — Inference Endpoints Complete Architecture Deep-Dive (Topic #259)

### Summary
Comprehensive deep-dive on Hugging Face Inference Endpoints — the managed production-grade deployment service. Covers the full architecture (container lifecycle, inference engines, orchestration), vLLM parallelism strategies (TP×DP=total GPUs), dual autoscaling strategies with scale-to-zero (`X-Scale-Up-Timeout` header), observability (HTTP metrics, latency distributions p50/p95/p99, OpenMetrics for Prometheus/Grafana), analytics dashboard (pending requests, hardware utilization, running replicas), configuration options (hardware selection across AWS/Azure/GCP, authentication modes, AWS PrivateLink, secrets, tags), logs interface (real-time filtering, per-replica, pagination), custom containers with FastAPI + ModelManager pattern, quota management, audit logs, the model catalog system, and enterprise features (SSO, resource groups, contract billing). Includes the REST API (OpenAPI v2 on `api.endpoints.huggingface.cloud`) and Python SDK (`huggingface_hub` `HfApi` methods) references.

### Source
- Inference Endpoints Documentation: https://huggingface.co/docs/inference-endpoints/en/index
- Quick Start: https://huggingface.co/docs/inference-endpoints/en/quick_start
- How It Works: https://huggingface.co/docs/inference-endpoints/en/about
- Configuration: https://huggingface.co/docs/inference-endpoints/en/guides/configuration
- Autoscaling: https://huggingface.co/docs/inference-endpoints/en/guides/autoscaling
- Analytics & Metrics: https://huggingface.co/docs/inference-endpoints/en/guides/analytics
- Foundations: https://huggingface.co/docs/inference-endpoints/en/guides/foundations
- Logs: https://huggingface.co/docs/inference-endpoints/en/guides/logs
- vLLM Engine: https://huggingface.co/docs/inference-endpoints/en/engines/vllm
- Custom Containers: https://huggingface.co/docs/inference-endpoints/en/engines/custom_container
- API Reference (Swagger): https://huggingface.co/docs/inference-endpoints/en/api_reference
- huggingface_hub Python SDK: https://huggingface.co/docs/huggingface_hub/guides/inference_endpoints
- Pricing: https://huggingface.co/pricing
- Endpoints Dashboard: https://endpoints.huggingface.co
- OpenAPI Specification: https://api.endpoints.huggingface.cloud

### Skill
mlops/hf-inference-endpoints — Hugging Face Inference Endpoints comprehensive reference: full architecture, 7 supported inference engines, vLLM TP/DP parallelism strategy, dual autoscaling strategies (hardware utilization + pending requests), scale-to-zero with X-Scale-Up-Timeout, observability (HTTP/latency/hardware metrics, OpenMetrics Prometheus integration), configuration (hardware across AWS/Azure/GCP, authentication, PrivateLink, secrets, tags), custom containers with FastAPI+ModelManager pattern, quota management, audit logs, and enterprise features

---

### 1. Architecture — How Inference Endpoints Works

Inference Endpoints is a managed container orchestration service specifically designed for AI model deployment. Three components come together:

1. **Model Weights & Artifacts** — Stored and versioned on the Hugging Face Hub
2. **Inference Engine** — The software that loads and runs the model (vLLM, TGI, SGLang, llama.cpp, TEI, Inference Toolkit, or custom container)
3. **Production Infrastructure** — Fully managed by Inference Endpoints: provisioning, scaling, monitoring, security

Under the hood, each endpoint is a **prebuilt Docker container** that includes:
- The selected inference engine software
- Model weights downloaded from `/repository` (the Hub mount point)
- Configuration and environment variables
- Health check routes for lifecycle management

The platform handles the full container lifecycle: starting, stopping, scaling (including autoscaling and scale-to-zero), and health/performance monitoring. This orchestration is fully managed — no Kubernetes, CUDA version management, or VPN configuration needed.

### 2. Supported Inference Engines

| Engine | Use Case | Framework Value |
|--------|----------|----------------|
| **vLLM** | High-throughput LLM serving (PagedAttention, continuous batching, speculative decoding) | `"vllm"` or custom image |
| **TGI** (Text Generation Inference) | Optimized text generation with Tensor Parallelism, Multi-LoRA | `"text-generation-inference"` |
| **SGLang** | Structured generation with constrained decoding, RadixAttention | Custom image |
| **TEI** (Text Embeddings Inference) | Embedding models (BERT, sentence-transformers) | Custom image |
| **llama.cpp** | GGUF models, CPU-friendly inference | Custom image |
| **Inference Toolkit** | General-purpose PyTorch/ONNX inference | `"pytorch"`, `"onnx"` |
| **Custom Container** | Bring your own Docker image with custom logic | `"custom"` + `custom_image` dict |

### 3. vLLM — Tensor Parallelism vs Data Parallelism Deep-Dive

vLLM supports two parallelism strategies for distributed inference, and understanding the interplay is critical for cost-effective deployment.

**Fundamental formula:** `tensor_parallel_size × data_parallel_size = total GPUs on instance`

#### Tensor Parallelism (TP)
Splits model weights across multiple GPUs **within each layer**. Each GPU holds a slice and computes its portion, then synchronizes. Use TP when the model is too large for a single GPU.

- Llama 3 8B (FP16, ~16GB) → `tensor_parallel_size=1` (fits on 1 GPU)
- Llama 3 70B (FP16, ~140GB) → `tensor_parallel_size=2` (needs 2×80GB GPUs)
- Llama 3.1 405B (FP16, ~810GB) → `tensor_parallel_size=8` (needs 8×80GB GPUs)

#### Data Parallelism (DP)
Runs **independent copies** of the model on different GPUs. Each copy handles different requests. Use DP when the model fits on fewer GPUs than the instance provides — maximizes throughput.

#### Combined TP + DP Strategy

Example: Serving Llama 3 8B on 4×A100 80GB

| Configuration | TP | DP | Copies | Behavior |
|--------------|----|----|--------|----------|
| Default | 4 | 1 | 1 | Model sharded across all 4 GPUs (wasteful) |
| Balanced | 2 | 2 | 2 | 2 copies, each on 2 GPUs |
| Max Throughput | 1 | 4 | 4 | 4 independent copies |

**Trade-off:** Higher DP → higher throughput but less KV cache memory per copy (shorter context). Higher TP → more memory per copy for KV cache (longer context) but lower throughput.

**Recommended configuration workflow:**
1. Calculate minimum TP: how many GPUs to fit the model in memory
2. Set TP to that minimum
3. Set DP = total instance GPUs ÷ TP

**Common mistakes:**
- TP=1, DP=1 for 7B on 4×A10G → 3 GPUs idle. Fix: `data_parallel_size=4`
- TP=2, DP=4 on 4×A10G → fails (2×4=8 ≠ 4). Fix: TP=2, DP=2 or TP=1, DP=4
- TP=3, DP=1 on 4×A10G → 1 GPU idle. Fix: TP=4 or TP=2 with DP=2

#### vLLM Configuration Parameters

- **Max Number of Sequences** (`max_num_seqs`): Maximum requests processed together in a batch. Controls batch size by sequence count.
- **Max Number of Batched Tokens** (`max_num_batched_tokens`): Maximum total tokens summed across all sequences in a batch.
- **Tensor Parallel Size**: Number of GPUs the model is sharded across.
- **KV Cache DType**: `"auto"`, `"fp8"`, `"fp8_e5m2"`, `"fp8_e4m3"`. Lower precision reduces memory at slight quality cost.
- Advanced: any vLLM EngineArg can be passed as container argument (e.g., `--enable-lora true`).

### 4. Autoscaling — Two Strategies

#### Strategy A: Hardware Utilization-Based
- **CPU**: Scale up when average CPU utilization exceeds threshold (default 80%)
- **GPU**: Scale up when average GPU utilization over 1-minute window exceeds threshold (default 80%)
- Scale-up check: every **1 minute**
- Scale-down check: every **2 minutes** with **300-second stabilization** period

#### Strategy B: Pending Requests-Based
- **Pending requests** = requests that haven't received an HTTP status (in-flight + processing)
- Default threshold: >1.5 pending requests per replica over past 20 seconds triggers scale-up
- This is a **leading indicator** — responds faster than hardware metrics

#### Scale-to-Zero
- Default: endpoint scales to zero after **1 hour** of inactivity
- **`X-Scale-Up-Timeout` header**: prevents 503 responses during cold start. Set to max wait in seconds (e.g., `X-Scale-Up-Timeout: 600`). The proxy holds the request until a replica is ready or the timeout expires.
- Cold start takes **20-60 seconds** (depends on model size)
- Tip: If your app needs responsiveness, don't rely on scale-to-zero. Keep `min_replica >= 1`.

#### Replica Configuration
- `min_replica=0` required for scale-to-zero
- `max_replica` sets the cost ceiling
- Default: scale-to-zero timeout = 60 minutes

### 5. Observability & Analytics

#### Available Metrics (per endpoint dashboard)

| Metric | Description |
|--------|-------------|
| **HTTP Requests** | Count by response class (2xx/4xx/5xx), toggleable per individual status code |
| **Pending Requests** | Requests queued or in-flight. Rising trend = need more replicas |
| **Latency Distribution** | p50, p90, p95, p99. Narrow gap between median and p99 = uniform latency |
| **Running Replicas** | Count over time with max-replica ceiling line |
| **CPU Usage** | Average or per-replica view |
| **Memory Usage** | RAM utilization |
| **GPU Usage** | GPU compute utilization |
| **GPU Memory (VRAM)** | GPU memory utilization |

#### OpenMetrics API (Beta — Team/Enterprise only)

Endpoint: `GET https://api.endpoints.huggingface.cloud/v2/endpoint/{namespace}/{name}/open-metrics`

Returns Prometheus-compatible format:
```bash
# HELP latency_distribution Latency distribution
# TYPE latency_distribution summary
latency_distribution{quantile="0.5"} 0.006339203
latency_distribution{quantile="0.9"} 0.007574241
latency_distribution{quantile="0.95"} 0.007994495
latency_distribution{quantile="0.99"} 0.020140918
latency_distribution_count 4
latency_distribution_sum 0.042048857
# HELP http_requests HTTP requests by code and replicas
# TYPE http_requests counter
http_requests{replica_id="fqwg7eri-hskoj",status_code="200"} 1152
# HELP cpu_usage_percent CPU percent
# TYPE cpu_usage_percent gauge
# UNIT cpu_usage_percent percent
```

Integrates with **Datadog OpenMetrics**, **Grafana Prometheus datasource**, and standard observability stacks.

#### Logs Interface
- Real-time streaming per replica
- Filters: Timestamp, Log Level, Content, Replica ID
- Default: 50 lines with "Load More" pagination
- UTC timestamps by default
- Deployment identifier (e.g., `6pajyw3k`) + replica ID (e.g., `z7ghx`) → combined `6pajyw3k-z7ghx`

### 6. Configuration Options

#### Hardware Selection
Three cloud providers: **AWS**, **Azure**, **Google Cloud Platform**
Three accelerator types: **CPU**, **GPU**, **INF2 (AWS Inferentia)**
Region selection per provider

**Available GPU types:**
- Nvidia T4, A10G, A100, H100 (vary by provider/region)
- Each tile shows: GPU type+count, memory (GB), vCPUs, RAM, hourly pricing

#### Authentication Modes
| Mode | Access |
|------|--------|
| **Private** (default) | You + org members only, using personal HF access token |
| **Public** | Anyone can call the endpoint without authentication |
| **Authenticated** | Anyone with a Hugging Face account, using their HF access token |

**AWS PrivateLink** (for AWS deployments): Intra-region VPC-only access, no internet exposure.

#### Advanced Settings
- **Commit Revision**: Pin a specific commit hash for model artifacts
- **Task**: Model task (auto-detected from Hub metadata)
- **Container Arguments**: CLI-style args to container entrypoint
- **Container Command**: Override the entrypoint entirely
- **Download Pattern**: Regex filter for which model files to download (e.g., `*.safetensors`)
- **Endpoint Tags**: Plain-text labels for filtering/sorting in dashboard
- **Default Env**: Key-value env vars
- **Secret Env**: Securely stored, injected at runtime, write-only

### 7. Custom Container Deployment Pattern

When no built-in engine fits your needs, deploy a custom Docker container.

**Critical rules:**
1. Always load model from **`/repository`** — the Hub mounts the model there
2. Expose a **`/health`** route for container health checks
3. Use FastAPI's **`lifespan`** for clean model lifecycle (load on startup, unload on shutdown)

**ModelManager pattern** (recommended):
```python
class ModelManager:
    def __init__(self, model_id, device, dtype): ...
    async def load(self): ...     # Load model + tokenizer
    async def unload(self): ...    # Free memory, clear CUDA cache
    def get(self): ...             # Return (model, tokenizer) or raise
```

The custom container image is specified via `custom_image` dict in the API:
```python
custom_image={
    "url": "ghcr.io/my-org/my-engine:latest",
    "health_route": "/health",
    "env": {"MY_VAR": "value"},
}
```

### 8. Quota Management

- The **Quotas** section shows usage vs limits per provider/hardware type
- **Paused** endpoints don't count against "used" quota
- **Scaled-to-zero** endpoints DO count as "used" — pause them to free quota
- "Request More" button to increase limits

### 9. Audit Logs

Team/Enterprise feature providing a chronological record of all actions:
- **Action Type**: resumed, updated, paused, deleted, etc.
- **User**: Avatar + name of who performed the action
- **Timestamp**
- **Action Details**: Instance changes, configuration updates, state changes
- **Request Metadata**: IP address, X-Request-Id for tracking

### 10. Enterprise Features

- Higher GPU quotas for most performant hardware
- **Single Sign-On (SSO)**
- **Audit Logs**
- **Resource Groups** for team/project access control
- **Private repositories** storage
- **Contract-based invoicing** with prepaid credits
- **Dedicated support**

### 11. Endpoint States Lifecycle

```
pending → initializing → running
                            ↓
                        paused ←→ resumed
                            ↓
                      scaledToZero (idle, auto-resumes on request)
                            ↓
                        failed
                            ↓
                        deleted (irreversible)
```

- `initializing` → `running`: ~3-5 minutes typical
- `running` → `paused`: manual, stops billing
- `running` → `scaledToZero`: after 1h idle (configurable)
- `scaledToZero` → `running`: auto on next request (20-60s cold start)
- `paused` → `running`: manual resume

### 12. REST API (OpenAPI v2)

Base URL: `https://api.endpoints.huggingface.cloud/v2`
Full interactive spec: https://api.endpoints.huggingface.cloud

Key endpoints:
- `GET /endpoint/{namespace}` — list endpoints
- `POST /endpoint/{namespace}` — create endpoint
- `GET /endpoint/{namespace}/{name}` — get endpoint details
- `PATCH /endpoint/{namespace}/{name}` — update endpoint
- `DELETE /endpoint/{namespace}/{name}` — delete endpoint
- `POST /endpoint/{namespace}/{name}/pause` — pause
- `POST /endpoint/{namespace}/{name}/resume` — resume
- `POST /endpoint/{namespace}/{name}/scale-to-zero` — scale to zero
- `GET /endpoint/{namespace}/{name}/open-metrics` — Prometheus metrics (Team/Enterprise)

### 13. Python SDK (huggingface_hub)

Key methods on `HfApi`:
- `create_inference_endpoint(name, repository, ...)` → `InferenceEndpoint`
- `create_inference_endpoint_from_catalog(repo_id, ...)` → simplified creation
- `get_inference_endpoint(name, namespace=...)` → `InferenceEndpoint`
- `list_inference_endpoints(namespace=...)` → `List[InferenceEndpoint]`
- `update_inference_endpoint(name, ...)` → `InferenceEndpoint`
- `delete_inference_endpoint(name, ...)`

On `InferenceEndpoint` object:
- `.client` → synchronous `InferenceClient` pointing at endpoint URL
- `.async_client` → async variant
- `.wait(timeout=...)` → blocks until running
- `.fetch()` → refresh status
- `.pause()` / `.resume()` / `.scale_to_zero()` / `.update(...)` / `.delete()`

### 14. Zero-Cost Notice

Inference Endpoints is a **paid service** requiring an active subscription and payment method. The free alternatives are:
- **ZeroGPU Spaces** — free GPU-powered Spaces with queue-based access
- **Inference Providers** — serverless inference with 17+ providers, free tier available
- **Gradio Lite** — fully client-side browser inference (no server costs)
- **Static Spaces** — serverless Gradio apps via WebAssembly

### 15. Key Takeaways

1. **vLLM parallelism**: Always maximize DP for throughput, minimize TP to what fits the model. Use `TP × DP = total GPUs`.
2. **Scale-to-zero** is cost-effective but expect 20-60s cold start. Use `X-Scale-Up-Timeout` header to avoid 503s.
3. **Pending requests** autoscaling reacts faster than hardware utilization — prefer it for latency-sensitive apps.
4. **Custom containers** must load models from `/repository` and expose `/health`.
5. **Audit logs + OpenMetrics** require Team/Enterprise subscription.
6. **Paused ≠ scaled-to-zero**: paused endpoints don't count against quota; scaled-to-zero endpoints do.
7. **Use catalog models** when possible — they have pre-tuned configurations for one-click deployment.
