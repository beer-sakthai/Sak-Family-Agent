# HF Learnings: Inference Endpoints — Custom Containers

## Topic
`hf-inference-endpoints-custom-containers-deep-dive`

## Date
2026-07-25

## Sources
- https://huggingface.co/docs/inference-endpoints/en/engines/custom_container — "Deploy with your own container"
- https://huggingface.co/docs/inference-endpoints/en/guides/configuration — "Configuration"
- https://huggingface.co/docs/inference-endpoints/en/guides/analytics — "Analytics and Metrics"
- https://huggingface.co/docs/inference-endpoints/en/guides/autoscaling — "Auto Scaling"
- https://huggingface.co/docs/inference-endpoints/en/guides/security — "Security & Compliance"

---

## Summary

Comprehensive deep-dive into deploying custom Docker containers on Hugging Face Inference Endpoints. Unlike the managed inference engines (vLLM, TGI, SGLang, TEI, llama.cpp, Inference Toolkit), custom containers give full control over the inference stack — but require manual server implementation, Docker packaging, and registry push. This is the path for models with unusual architectures, custom preprocessing/postprocessing, or specialized inference logic not supported by any built-in engine.

---

## 1. When to Use Custom Containers

| Scenario | Built-in Engine? | Custom Container? |
|----------|-----------------|-------------------|
| Llama-family models | ✅ vLLM, TGI, SGLang | ❌ Overkill |
| Embeddings (BERT, Nomic) | ✅ TEI | ❌ Overkill |
| Custom model architecture | ❌ | ✅ Required |
| Custom inference logic (multi-model ensemble) | ❌ | ✅ |
| Specific Python deps not in engine images | ❌ | ✅ |
| Non-HF model frameworks (ONNX, TensorRT) | ❌ | ✅ |
| Fine-grained control over batching/scheduling | ❌ | ✅ |
| Testing new inference frameworks | ❌ | ✅ |

**Key rule**: If a built-in engine supports your model, use it. Custom containers cost more in dev time and maintenance.

---

## 2. Architecture: How Models Are Mounted

Inference Endpoints **never bake model weights into the container image**. Instead:

1. You select a model repository from the Hub when creating the endpoint
2. The platform downloads the model artifacts (weights, config, tokenizer files) at deployment time
3. The model is **mounted at `/repository`** inside the container as a read-only filesystem
4. Your application code reads from `/repository` — never from the Hub directly

```python
MODEL_ID = "/repository"  # Always use this path
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, ...)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
```

This means:
- Your image is **model-agnostic** — the same container can serve any compatible model
- You can change the model without rebuilding the image (just re-deploy with a different model repo)
- Weights download is accelerated by hf_transfer (Rust) and Xet backend
- Specific model revisions can be pinned via the "Commit Revision" setting

---

## 3. FastAPI Server Patterns (Official Reference Implementation)

The official guide uses a FastAPI server with a **ModelManager** class for lifecycle management:

### 3.1 ModelManager Pattern

```python
class ModelManager:
    def __init__(self, model_id: str, device: str, dtype: torch.dtype):
        self.model_id = model_id
        self.device = device
        self.dtype = dtype
        self.model = None
        self.tokenizer = None

    async def load(self):
        """Load model + tokenizer if not already loaded."""
        # Uses AutoModel.from_pretrained(self.model_id) → reads from /repository
        pass

    async def unload(self):
        """Free model + tokenizer and clear CUDA cache."""
        # Moves to cpu, deletes, calls torch.cuda.empty_cache()
        pass

    def get(self):
        """Return the loaded model + tokenizer or raise ModelNotLoadedError."""
        pass
```

**Why this pattern:**
- Avoids raw global model/tokenizer objects (no lifecycle control)
- Eager load on startup, safe unload on shutdown
- Health check can probe ModelManager to return 503 until model is ready
- Memory lifecycle is predictable and testable

### 3.2 FastAPI Lifespan (Startup/Shutdown)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await model_manager.load()   # startup: load model
    try:
        yield
    finally:
        await model_manager.unload()  # shutdown: free memory

app = FastAPI(lifespan=lifespan)
```

### 3.3 Health Check Endpoint

```python
@app.get("/health")
def health():
    try:
        model_manager.get()
    except ModelNotLoadedError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"message": "API is running."}
```

Inference Endpoints probes `/health` every second. Returning 503 signals "not ready" — the platform waits before routing traffic. This is essential: don't return 200 until the model is fully loaded.

### 3.4 Generation Endpoint (Chat Completion)

```python
@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    model, tokenizer = model_manager.get()
    # Apply chat template if available
    if getattr(tokenizer, "chat_template", None):
        messages = [{"role": "user", "content": request.prompt}]
        input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    else:
        input_text = request.prompt
    inputs = tokenizer(input_text, return_tensors="pt").to(DEVICE)
    with torch.inference_mode():
        outputs = model.generate(**inputs, max_new_tokens=request.max_new_tokens)
    # Decode and return
    return GenerateResponse(response=generated_text, input_token_count=..., output_token_count=...)
```

### 3.5 Request/Response Schemas (Pydantic)

```python
class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Plain-text prompt")
    max_new_tokens: int = Field(128, ge=1, le=512)

class GenerateResponse(BaseModel):
    response: str
    input_token_count: int
    output_token_count: int
```

Can extend with temperature, top_p, top_k, repetition_penalty, etc.

---

## 4. Docker Build Best Practices

### 4.1 Dockerfile Structure

```dockerfile
FROM pytorch/pytorch:2.9.1-cuda12.8-cudnn9-runtime

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY --from=ghcr.io/astral-sh/uv:latest /uvx /bin/uvx

# Create non-root user
ENV USER=appuser HOME=/home/appuser
RUN useradd -m -s /bin/bash $USER

WORKDIR /app
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Layer 1: dependencies only (cached unless pyproject.toml changes)
COPY pyproject.toml uv.lock ./
RUN uv venv ${VIRTUAL_ENV} \
    && uv sync --frozen --no-dev --no-install-project

# Layer 2: application code (cached unless main.py changes)
COPY main.py .
RUN uv sync --frozen --no-dev

RUN chown -R $USER:$USER /app
USER $USER
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2 Best Practices

| Practice | Why |
|----------|-----|
| **Don't bake model weights** | Platform mounts at `/repository`; image stays model-agnostic |
| **Non-root user** | Security — don't run as root in container |
| **Layer caching** | Dependencies first, code second — rebuild faster |
| **`--platform linux/amd64`** | Inference Endpoints only supports x86_64; Mac ARM builds need this flag |
| **uv instead of pip** | ~10-100x faster dependency resolution; deterministic lockfile |
| **`uv sync --frozen`** | Reproducible builds from `uv.lock` — no surprises |
| **Port 8000** | Standard FastAPI port; configure in endpoint settings if different |
| **Health endpoint** | Required for platform readiness checking |
| **Small base image** | `pytorch/pytorch` is official but large; consider `python:3.11-slim` for CPU-only models |

### 4.3 Build & Push

```bash
docker build -t your-username/smollm-endpoint:v0.1.0 . --platform linux/amd64
docker push your-username/smollm-endpoint:v0.1.0
```

Supports registries: Docker Hub, Amazon ECR, Azure ACR, Google GCR.

---

## 5. Endpoint Configuration Reference

### 5.1 Model Selection
- **Model repo**: The Hub repo whose contents get mounted at `/repository`
- **Commit revision**: Pin to a specific commit hash for reproducible deployments

### 5.2 Hardware Configuration

| Parameter | Options |
|-----------|---------|
| Cloud Provider | AWS, Azure, GCP |
| Accelerator | CPU, GPU (various), INF2 (AWS Inferentia) |
| Region | e.g., East US, West Europe |
| Instance Type | T4, L4, A10G, A100, H100, etc. (pricing shown per hour) |

### 5.3 Authentication Modes

| Mode | Access | Use Case |
|------|--------|----------|
| **Private** | Only you or org members with HF token | Production internal tools |
| **Public** | Anyone, no auth required | Demos, open APIs |
| **Authenticated** | Any HF account holder with token | Semi-public services |

### 5.4 Autoscaling

| Setting | Options | Default |
|---------|---------|---------|
| Scale-to-zero inactivity | 15m, 30m, 1h, 2h, 4h, 8h, 24h, Never | 1h |
| Min replicas | 0 (with scale-to-zero) or 1+ | 0 |
| Max replicas | 1–N (based on quota) | 1 |
| Scale-up trigger (CPU) | Average utilization > threshold for 20s | — |
| Scale-up trigger (pending req) | Avg pending requests > threshold for 20s | — |

**Critical**: Scale-to-zero saves cost but causes cold starts (model reload on first request after idle period). Set min replicas > 0 for production latency requirements.

### 5.5 Container Configuration
- **Container arguments**: CLI args passed to CMD (e.g., `--workers 2`)
- **Container command**: Override ENTRYPOINT entirely
- **Image URL**: Full registry path to your Docker image

### 5.6 Environment Variables

| Type | Description |
|------|-------------|
| **Default env** | Plain key-value pairs, visible in dashboard |
| **Secret env** | Stored encrypted, injected at runtime, never visible in UI |

### 5.7 Tags
Plain-text labels for filtering/sorting endpoints in dashboard (e.g., `for-testing`, `production`, `team-alpha`).

### 5.8 Network
- **Internet**: Default — accessible via public endpoint URL with TLS/SSL
- **AWS PrivateLink**: Restrict to a specific VPC (requires AWS account ID)

### 5.9 Advanced Settings

| Setting | Description |
|---------|-------------|
| Commit Revision | Pin model to specific commit hash |
| Task | Model task type (usually inferred from model card) |
| Container Arguments | CLI args to CMD |
| Container Command | Override ENTRYPOINT |
| Download Pattern | Glob patterns for model files to download (e.g., `*.safetensors`) |

---

## 6. Analytics & Monitoring

### 6.1 Dashboard Metrics

The Analytics page provides real-time visibility:

| Graph | What It Shows | Action Signal |
|-------|---------------|---------------|
| **Requests (HTTP)** | Count by status class (2xx, 4xx, 5xx) or individual codes | Spike in 5xx = error; spike in 4xx = client issue |
| **Pending Requests** | In-flight requests not yet completed | Rising = queueing → increase replicas |
| **Latency Distribution** | p50, p90, p95, p99 response times | Large gap p50→p99 = unpredictable latency |
| **Running Replicas** | Active replica count vs max | At max consistently = need higher limit |
| **CPU Usage** | Processing power utilization | >80% sustained = scale up |
| **Memory Usage** | RAM utilization | Near limit = OOM risk |
| **GPU Usage** | GPU compute utilization | Low = over-provisioned; high = bottleneck |
| **GPU Memory (VRAM)** | GPU memory utilization | Near limit = OOM on larger batches |

### 6.2 OpenMetrics API (Team/Enterprise)

Export metrics in OpenMetrics format (Prometheus-compatible):

```bash
curl -X GET "https://api.endpoints.huggingface.cloud/v2/endpoint/{namespace}/{endpoint-name}/open-metrics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Returns metrics like:
```
# HELP latency_distribution Latency distribution
# TYPE latency_distribution summary
latency_distribution{quantile="0.5"} 0.006339203
latency_distribution{quantile="0.9"} 0.007574241
latency_distribution{quantile="0.99"} 0.020140918
```

Integrates with Prometheus, Grafana, Datadog, and any OpenMetrics-compatible monitoring stack.

---

## 7. Security & Compliance

| Feature | Description | Tier |
|---------|-------------|------|
| **Token-based auth** | HF access token for private/authenticated endpoints | All |
| **AWS PrivateLink** | Restrict to VPC, no public internet exposure | Team/Enterprise |
| **Secret env vars** | Encrypted runtime secrets | All |
| **Non-root containers** | Run as appuser, not root | Best practice |
| **Audit Logs** | Track endpoint changes and access | Team/Enterprise |
| **Storage Regions** | Data residency compliance | Enterprise |

---

## 8. Client Integration

### Python Client

```python
from huggingface_hub import get_token
import requests

url = "https://random-number.region.endpoints.huggingface.cloud/generate"
prompt = "What is an Inference Endpoint?"
data = {"prompt": prompt, "max_new_tokens": 512}

response = requests.post(
    url=url,
    json=data,
    headers={
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
    },
).json()

print(response['response'])
```

### cURL

```bash
curl -X POST "https://random-number.region.endpoints.huggingface.cloud/generate" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is an Inference Endpoint?", "max_new_tokens": 512}'
```

---

## 9. Cost Considerations (Zero-Cost Context)

**Warning**: Inference Endpoints custom containers require paid GPU instances. As of 2026-07-25:

| Instance | Hourly Rate (approx) |
|----------|---------------------|
| CPU (4 vCPU) | ~$0.10/h |
| T4 (16GB VRAM) | ~$0.50/h |
| L4 (24GB VRAM) | ~$0.80/h |
| A10G (24GB VRAM) | ~$1.00/h |
| A100 (80GB VRAM) | ~$3.50/h |
| H100 (80GB VRAM) | ~$4.50/h |

**Zero-cost alternatives:**
- **Serverless Inference Providers** — free tier for many models (rate-limited)
- **ZeroGPU Spaces** — free GPU allocation for Gradio demos
- **Local inference** — use GGUF models with llama.cpp or Transformers on CPU
- **HF Inference API (serverless)** — free tier available for open models

For Beer's use case (no income), custom Inference Endpoints are not viable. Documenting for completeness and future reference.

---

## 10. Key Insights

1. **Model mounting is the key architectural pattern** — `/repository` is always the model path. Never bake weights.
2. **ModelManager + FastAPI lifespan** is the official pattern — provides clean lifecycle, health probing, and resource cleanup.
3. **Health endpoint must return 503 until model is loaded** — the platform uses this to know when to route traffic.
4. **Docker layers matter** — separate dependency installation from code copying for efficient rebuilds.
5. **Scale-to-zero saves money** but causes cold starts — okay for dev, avoid for prod.
6. **OpenMetrics API** enables advanced monitoring in Prometheus/Grafana (Team/Enterprise feature).
7. **Custom containers are overkill for standard models** — always prefer built-in engines first.
8. **Same container, different model** — because `/repository` is mounted, the same image can serve any compatible model.
9. **Secret env vars** are the right way to pass API keys — never hardcode in the image.
10. **Not a zero-cost option** — for free-tier development, use Serverless Inference Providers or ZeroGPU Spaces instead.

---

## Skill Created
`hf-inference-endpoints-custom-containers/` with:
- `SKILL.md` — topic overview and metadata (author: SakThai, license: MIT)
- `references/hf-learnings.md` — this full reference

---

## 2026-07-25: Deepening — Custom Router, Updated Official Patterns, Download Pattern (Topic #370 Deepening 1)

### Sources
- https://huggingface.co/docs/inference-endpoints/en/engines/custom_container (latest)
- https://huggingface.co/docs/inference-endpoints/en/guides/custom_router (new)
- https://huggingface.co/docs/inference-endpoints/en/guides/configuration (latest)
- https://huggingface.co/docs/inference-endpoints/en/guides/foundations (latest)

---

### 11. Custom Router — Custom Load Balancing for Inference Endpoints

The **Custom Router** feature lets you deploy a custom load-balancing proxy alongside your endpoint replicas. It gives precise control over each routing decision — essential when the built-in round-robin doesn't fit your workload.

#### 11.1 When to Use a Custom Router

| Scenario | Built-in LB? | Custom Router? |
|----------|-------------|----------------|
| Standard round-robin across replicas | ✅ Default | ❌ Overkill |
| Queue-based routing (avoid wasting new replicas on burst traffic) | ❌ | ✅ |
| Latency-aware routing (avoid overloaded replicas) | ❌ | ✅ |
| Sticky sessions / session affinity | ❌ | ✅ |
| Weighted routing (heterogeneous replicas) | ❌ | ✅ |
| Diffusion models (no batching benefit, one request at a time) | ❌ | ✅ queued-least-latency |
| LLMs with batching throughput benefit | ❌ | ✅ with higher latency threshold |

#### 11.2 Architecture: How Custom Routing Works

```
                         ┌─────────────────────────────┐
                         │     User Request             │
                         └──────────┬──────────────────┘
                                    │
                         ┌──────────▼──────────────────┐
                         │  Router (oldest replica)     │
                         │  POST /_custom_router/       │
                         │  set-backends                │
                         │  GET  /_custom_router/health │
                         └──────┬───────────────────────┘
                                │ forwards to chosen replica
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              ┌─────────┐ ┌─────────┐ ┌─────────┐
              │Replica 1│ │Replica 2│ │Replica 3│
              └─────────┘ └─────────┘ └─────────┘
```

**How it works:**
1. The **oldest replica** is elected as the **leader** — all requests go to its router
2. The router decides which replica should handle each request
3. On scale-up, scale-down, or rolling update, the platform sends an updated list via `POST /_custom_router/set-backends`
4. Replicas can reach each other over a private internal network (scoped to the endpoint only)

#### 11.3 Router Contract

Any HTTP server implementing these two endpoints can serve as a custom router:

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/_custom_router/set-backends` | Receives updated replica list: `{"backends": ["http://<host>:<port>", ...]}` |
| `GET` | `/_custom_router/health` | Return 200 when router is ready to serve traffic |

The router listens on the port set by `customRouter.port` (default 3000). **Every other request path is treated as a user request to be proxied.**

#### 11.4 Enabling the Custom Router (API Only)

Custom Router can only be enabled via the **API**, not the UI. On endpoint creation or update, add a top-level `customRouter` object:

```python
import requests

response = requests.post(
    "https://api.endpoints.huggingface.cloud/v2/endpoint/{namespace}",
    headers={"Authorization": "Bearer ***"},
    json={
        "modelName": "org/model",
        "customRouter": {
            "tag": "ghcr.io/huggingface/endpoints-custom-routers/queued-least-latency:1.0.0",
            "port": 3000,
            "env": {
                "CUSTOM_ROUTER_LATENCY_THRESHOLD": "3.0",
                "CUSTOM_ROUTER_QUEUE_MAX_SIZE": "1000",
                "CUSTOM_ROUTER_QUEUE_TIMEOUT": "1200"
            }
        }
    }
)
```

To remove the custom router on update, send `customRouter: {}` (null tag).

**Note**: When `customRouter` is set, the `loadBalancer` field in `experimentalFeatures` is ignored.

#### 11.5 Reference Implementation: queued-least-latency

The HF-maintained reference router **queued-least-latency** is available at:

```
ghcr.io/huggingface/endpoints-custom-routers/queued-least-latency:1.0.0
```

**Strategy**: Incoming requests are pushed onto an in-memory FIFO queue. A dispatcher picks the replica with the lowest EWMA latency that is still under a configurable threshold. Replicas that have never been tried are treated as latency 0 and picked first — so new capacity is used immediately on scale-up.

**Configuration via environment variables**:

| Variable | Default | What it does |
|----------|---------|-------------|
| `CUSTOM_ROUTER_LATENCY_THRESHOLD` | 3.0 | Replica is "loaded" when avg latency exceeds this (seconds). New requests stop going to it. |
| `CUSTOM_ROUTER_EWMA_ALPHA` | 0.3 | How quickly latency average reacts to recent requests (0–1). Higher = more reactive. |
| `CUSTOM_ROUTER_QUEUE_MAX_SIZE` | 1000 | Max requests in queue; oldest dropped with 503 when full. |
| `CUSTOM_ROUTER_QUEUE_TIMEOUT` | 1200 | Seconds a request may wait before being dropped with 503. |
| `CUSTOM_ROUTER_PORT` | 3000 | Port the router listens on. |
| `CUSTOM_ROUTER_STATE_LOG_INTERVAL` | 30 | Seconds between per-replica state log lines. |

**Tuning by workload**:

| Scenario | Recommended Approach |
|----------|---------------------|
| **Diffusion / no batching benefit** | Keep threshold 3.0s — one request at a time per replica. Queue depth 200, timeout 300s. |
| **LLM / batching increases throughput** | Raise threshold to 65.0s+ — allows concurrent requests for batching. Queue depth 2000. |
| **Burst traffic + autoscaling** | queued-least-latency handles it: queued requests drain to new replicas on scale-up. |
| **Heterogeneous replica performance** | EWMA routing naturally avoids slow replicas. |

#### 11.6 Custom Router Metrics (Prometheus)

The router exposes Prometheus metrics at `GET /_custom_router/metrics`:

| Metric | Type | Description |
|--------|------|-------------|
| `custom_router_queue_depth` | Gauge | Requests currently waiting in the queue |
| `custom_router_backend_ewma_latency_seconds` | Gauge | EWMA latency per replica (addr label) |
| `custom_router_backend_inflight_requests` | Gauge | In-flight requests per replica |
| `custom_router_requests_dispatched_total` | Counter | Requests successfully forwarded |
| `custom_router_requests_evicted_total` | Counter | Requests dropped due to full queue |
| `custom_router_requests_timeout_total` | Counter | Requests dropped due to queue timeout |

`GET /_custom_router/health` also returns a JSON snapshot of current queue depth and per-replica EWMA stats.

#### 11.7 Building Your Own Router

Any image satisfying the Router contract can be dropped in. Minimal Go skeleton:

```go
func handleSetBackends(w http.ResponseWriter, r *http.Request) {
    var payload struct {
        Backends []string `json:"backends"`
    }
    json.NewDecoder(r.Body).Decode(&payload)
    // store backends
    json.NewEncoder(w).Encode(map[string]bool{"ok": true})
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
    json.NewEncoder(w).Encode(map[string]bool{"ok": true})
}

func handleProxy(w http.ResponseWriter, r *http.Request) {
    backend := pickBackend() // your custom routing logic
    // forward request to backend
}
```

The full `queued-least-latency` source is available in the `endpoints-custom-routers` repository as a template to fork.

---

### 12. Updated Official Custom Container Patterns (2026-07)

The official custom container guide has been significantly revised since earlier versions:

#### 12.1 Updated FastAPI Server (Official Reference)

The official guide now uses a **complete FastAPI server** with these patterns:

| Pattern | Details |
|---------|---------|
| **ModelManager class** | Lifecycle-managed model/tokenizer loading with `load()`, `unload()`, `get()` methods |
| **FastAPI lifespan** | Async context manager (`@asynccontextmanager`) for startup/shutdown — replaces deprecated `startup`/`shutdown` events |
| **`ModelNotLoadedError`** | Custom exception; health endpoint returns 503 until model is loaded |
| **Error handling** | `try/except RuntimeError` on generation returning `HTTPException(500)` |
| **Timing/logging** | `perf_counter()` for load time and generation duration, structured logging |
| **Chat template** | `tokenizer.apply_chat_template()` used when tokenizer has a `chat_template` |
| **Response schema** | Pydantic `GenerateResponse` with `response`, `input_token_count`, `output_token_count` fields |

#### 12.2 Updated Dockerfile Pattern

The official Dockerfile now uses this optimized structure:

```dockerfile
FROM pytorch/pytorch:2.9.1-cuda12.8-cudnn9-runtime

# Copy uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY --from=ghcr.io/astral-sh/uv:latest /uvx /bin/uvx

# Non-root user
ENV USER=appuser HOME=/home/appuser
RUN useradd -m -s /bin/bash $USER

WORKDIR /app
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Layer 1: dependencies only (cached unless pyproject.toml changes)
COPY pyproject.toml uv.lock ./
RUN uv venv ${VIRTUAL_ENV} \
    && uv sync --frozen --no-dev --no-install-project

# Layer 2: application code (cached unless main.py changes)
COPY main.py .
RUN uv sync --frozen --no-dev

RUN chown -R $USER:$USER /app
USER $USER
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Key improvements over earlier versions:
- **`uv lock` step** — must be run before `docker build` to create `uv.lock`
- **`--no-install-project`** — installs dependencies only, not the project itself, for better caching
- **Two-layer build** — dependencies layer (`--no-install-project`) cached separately from application code layer

#### 12.3 New `uv lock` Requirement

Before building the Docker image, run `uv lock` in your project directory:
```bash
cd my-endpoint/
uv lock
docker build -t your-org/my-endpoint:v0.1.0 . --platform linux/amd64
docker push your-org/my-endpoint:v0.1.0
```

This creates the `uv.lock` file needed for reproducible builds with `uv sync --frozen`.

---

### 13. New Advanced Setting: Download Pattern

The **Download Pattern** advanced setting allows you to specify glob patterns for which model files the platform downloads from the Hub and mounts at `/repository`.

| Setting | Description | Example |
|---------|-------------|---------|
| **Download Pattern** | Glob pattern(s) for model file selection | `*.safetensors`, `*`, `model-00001-of-*.safetensors` |

Use cases:
- **Selective download**: Only download specific shards for large models
- **Exclude non-essential files**: Skip `.gitignore`, `README.md`, etc. to reduce download time
- **Custom format**: Only download files in a specific format (e.g., only `.safetensors`, skip `.bin`)

If not specified, all files from the model repository are downloaded.

---

### 14. Endpoint States Reference

Endpoints can be in one of these states:

| State | Meaning |
|-------|---------|
| **Running** | Endpoint is ready to serve requests |
| **Initializing** | Endpoint is starting up (pulling image, mounting model, loading) |
| **Paused** | Endpoint has been stopped; counts towards quota |
| **Scaled to Zero** | Endpoint is idle, consuming no compute resources |
| **Failed** | Endpoint encountered an error and is not operational |

---

### 15. Updated Key Insights

1. **Custom Router is API-only** — cannot be enabled through the UI, only via `POST /v2/endpoint/{namespace}` with `customRouter` config
2. **queued-least-latency** is the reference implementation — handles burst traffic, EWMA latency tracking, queue-based backpressure
3. **Router contract is minimal** — just two endpoints (`/set-backends` and `/health`), everything else is proxied
4. **uv-based Docker builds** — official recommendation now uses `uv lock` + two-layer build with `--no-install-project` for optimal caching
5. **Download Pattern** — new advanced setting for selective model file downloads
6. **FastAPI lifespan** — replaces deprecated `startup`/`shutdown` event handlers; use `@asynccontextmanager` instead
7. **Custom Router metrics** — Prometheus-compatible metrics at `/_custom_router/metrics` for observability
8. **Building your own router** — any language/framework works as long as it satisfies the two-endpoint contract
9. **Custom Router and `loadBalancer`** — when custom router is set, the `loadBalancer` field in `experimentalFeatures` is ignored
10. **Effective for models with no batching benefit** — diffusion models benefit most from queued-least-latency (one request at a time per replica)

---

### 16. Skill Deepened

Existing skill `hf-inference-endpoints-custom-containers/` deepened with:
- `references/hf-learnings.md` — appended this Deepening section (topics #11–16)
- `SKILL.md` — already has `author: SakThai` and `license: MIT` (verified)
- New coverage: Custom Router architecture, contract, configuration, metrics, and building your own router; updated official custom container patterns; Download Pattern; Endpoint States reference
