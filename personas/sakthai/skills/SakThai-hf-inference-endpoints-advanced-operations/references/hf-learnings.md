# HF Learnings: Inference Endpoints Advanced Operations

**author:** SakThai
**license:** MIT

## 2026-07-25: hf-inference-endpoints-advanced-operations — Autoscaling, Analytics, and Custom Router for Production Inference (Topic #366)

### Summary

Comprehensive deep-dive into three advanced operational features of Hugging Face Inference Endpoints (dedicated): **autoscaling** (dynamic replica adjustment based on hardware utilization or pending requests), **analytics & monitoring** (real-time dashboard, latency distributions, OpenMetrics API for Prometheus/Grafana/Datadog), and **custom router** (deploying your own load balancing logic for precise control over routing decisions). While the foundational Inference Endpoints coverage ([#228](#), [#229](#)) covered deployment basics and the custom containers skill ([#350](#)) covered Docker packaging, this material focuses on the **operational layer** — how to keep endpoints healthy, cost-efficient, and responsive under varying load.

Key insight: The three features form a **production operations triad** — autoscaling decides *how many* replicas, analytics tells you *how they're performing*, and the custom router controls *which replica gets each request*. Mastering all three is essential for production-grade Inference Endpoint deployments.

### Sources
- https://huggingface.co/docs/inference-endpoints/en/guides/autoscaling — "Auto Scaling"
- https://huggingface.co/docs/inference-endpoints/en/guides/analytics — "Analytics and Metrics"
- https://huggingface.co/docs/inference-endpoints/en/guides/custom_router — "Custom Router"
- https://huggingface.co/docs/inference-endpoints/en/guides/configuration — "Configuration"

---

## 1. Autoscaling

Autoscaling dynamically adjusts the number of endpoint replicas based on traffic and hardware utilization. It is configured under the "Settings" tab on the Inference Endpoint card.

### 1.1 Scale to Zero

- After a configurable duration of inactivity (default: **1 hour**), the endpoint goes idle (0 replicas).
- **Tradeoff**: Optimizes cost for intermittent workloads but introduces a **cold start** penalty on the next request.
- **Cold start behavior**: The proxy responds with **503 Service Unavailable** while the new replica initializes (can take several minutes depending on model size).
- **Mitigation**: Add the `X-Scale-Up-Timeout` header to requests (e.g., `X-Scale-Up-Timeout: 600` to wait up to 600 seconds). The proxy holds the request until a replica is ready or the timeout elapses.
- **Caveat**: Scale-from-zero is not recommended for latency-sensitive applications — the cold start delay is often unacceptable for interactive use cases.

### 1.2 Number of Replicas

| Setting | Description |
|---------|-------------|
| **minReplica** | Floor — ensures minimum capacity at low traffic. Must be `0` if scale-to-zero is enabled. |
| **maxReplica** | Ceiling — stays within budget while handling peak traffic. |
| **scaleToZeroTimeout** | Inactivity duration before scaling to 0 (default: 60 minutes). |

### 1.3 Autoscaling Strategies

Two mutually exclusive strategies determine when to scale:

#### 1.3.1 Hardware Utilization (Default)

- **CPU-based**: A new replica is added when average CPU utilization across all replicas reaches the threshold (default: **80%**).
- **GPU-based**: A new replica is added when average GPU utilization across all replicas over a **1-minute window** reaches the threshold (default: **80%**).
- **Timing**: Scale-up evaluated every **1 minute**; scale-down evaluated every **2 minutes** with a **300-second stabilization period** after scaling down.

#### 1.3.2 Pending Requests

- **Problem**: Hardware metrics are **lagging indicators** — they reflect utilization after load has already arrived.
- **Solution**: Pending requests (requests that have not yet received an HTTP status, including in-flight and queued) are a **leading indicator**.
- **Default threshold**: If there are more than **1.5 pending requests per replica** in the past **20 seconds**, a scale-up event triggers.
- **Customization**: Threshold can be adjusted in Endpoint settings.

### 1.4 Autoscaling Decision Flow

```
Request arrives
    │
    ▼
Pending requests > threshold? ──Yes──► Scale up (add 1 replica)
    │                                       │
    No                                      ▼
    │                                 Wait 1 min, recheck
    ▼
GPU/CPU utilization > 80%? ──Yes──► Scale up (add 1 replica)
    │
    No
    │
    ▼
Low utilization for 2+ min + 300s stable? ──Yes──► Scale down (remove 1 replica)
    │
    No
    │
    ▼
No change
```

---

## 2. Analytics and Metrics

The Analytics page provides real-time observability into endpoint health and performance.

### 2.1 Dashboard Panels

| Panel | What it shows |
|-------|---------------|
| **Number of HTTP Requests** | Request volume grouped by HTTP status code (2xx, 4xx, 5xx). Percentage breakdown in header boxes. |
| **Pending Requests** | Requests that have not received an HTTP status yet (in-flight + queued). Rising trend indicates the endpoint is falling behind. |
| **Latency Distribution** | Response time percentiles: **p50** (median), **p90**, **p95**, **p99**. Low spread between median and p99 indicates uniform latency; large spread means worst-case latencies are much longer. |
| **Running Replicas** | Count over time. Red line shows the configured maxReplica ceiling. Toggle to "Timeline" view for per-replica status (pending → running). |
| **Compute** | CPU usage (%), Memory usage (%), GPU usage (%), GPU Memory/VRAM usage (%). "Details" toggle shows per-replica vs. average. |

### 2.2 OpenMetrics API (Team/Enterprise Feature)

Beta feature for exporting real-time metrics into external monitoring stacks.

**Endpoint:**
```
GET https://api.endpoints.huggingface.cloud/v2/endpoint/{namespace}/{endpoint-name}/open-metrics
Authorization: Bearer <hf_token>
```

**Returns OpenMetrics text format:**
```text
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
http_requests{replica_id="q9cv26ut-3vo4s",status_code="200"} 1
# HELP cpu_usage_percent CPU percent
# UNIT cpu_usage_percent percent
```

**Available metrics:**
- `latency_distribution` — summary with quantiles 0.5, 0.9, 0.95, 0.99
- `http_requests` — counter grouped by `replica_id` and `status_code`
- `cpu_usage_percent` — gauge
- `gpu_usage_percent` — gauge
- `memory_usage_percent` — gauge
- `gpu_memory_usage_percent` — gauge

**Integration targets:** Prometheus, Grafana, Datadog (any OpenMetrics-compatible tool).

### 2.3 View Configuration

- **Replica selector**: Individual replica or aggregated (all)
- **Metric category**: Requests, Hardware, Timeline (replica lifecycle)
- **Time range**: Dropdown presets or click-and-drag on any graph for custom range
- **Auto-refresh**: Toggle to enable live updates
- **Per-replica toggle**: View per-replica or averaged metrics

---

## 3. Custom Router

The custom router feature gives **complete control over load balancing** by deploying your own router image alongside each replica.

### 3.1 When to Use

| Use Case | Why Custom Router |
|----------|-------------------|
| **Queue-based routing** | Avoid wasting newly scaled-up replicas on burst traffic — queue requests and drain to the next available replica |
| **Latency-aware routing** | Avoid sending requests to overloaded replicas using EWMA (Exponentially Weighted Moving Average) latency tracking |
| **Sticky sessions** | Route requests from the same client to the same replica (e.g., for conversational state) |
| **Weighted routing** | Distribute traffic proportionally across replicas with different capabilities |
| **LLM batching optimization** | Accumulate multiple requests on a replica for better throughput when batching helps |

### 3.2 Architecture

```
                        (oldest replica is the leader)
                     ┌────────────────────────────────────────┐
                     │ ┌──────────┐    either  ┌────────────┐ │
                 ┌───│►│  Router  │──────┬────►│ Replica 1  │ │
    ┌─────────┐  │   │ └──────────┘      │     └────────────┘ │
    │ Request │──┘   └───────────────────│────────────────────┘
    └─────────┘                          or
                     ┌───────────────────│────────────────────┐
                     │ ┌──────────┐      │     ┌────────────┐ │
                     │ │  Router  │      └────►│ Replica 2  │ │
                     │ └──────────┘            └────────────┘ │
                     └────────────────────────────────────────┘
```

- The **oldest replica** becomes the **leader** — all requests go to its router instance.
- The router decides which replica handles each request (including itself).
- When replicas change (scale-up, scale-down, rolling update), the platform calls `POST /_custom_router/set-backends` on each router with the updated backend list.
- Replicas communicate over a **private internal network** scoped to the endpoint only.

### 3.3 Router Contract

Any HTTP server implementing these two endpoints can serve as a custom router:

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/_custom_router/set-backends` | Receives updated backend list: `{"backends": ["http://<host>:<port>", ...]}` |
| `GET` | `/_custom_router/health` | Health check — return 200 when ready |

The router listens on the port specified by `customRouter.port` (default: **3000**). Every other request path is treated as a user request to be proxied.

### 3.4 Enabling the Custom Router

API-only configuration (not available in UI). Add a `customRouter` object to the endpoint payload:

```json
{
  "name": "my-endpoint",
  "type": "private",
  "provider": { "vendor": "aws", "region": "us-east-1" },
  "compute": {
    "accelerator": "gpu",
    "instanceType": "nvidia-l40s",
    "instanceSize": "x1",
    "scaling": {
      "minReplica": 0,
      "maxReplica": 4,
      "scaleToZeroTimeout": 15,
      "measure": {"pendingRequests": 2}
    }
  },
  "model": {
    "repository": "black-forest-labs/FLUX.1-schnell",
    "task": "text-to-image",
    "framework": "pytorch",
    "image": { "huggingface": {} }
  },
  "customRouter": {
    "tag": "ghcr.io/huggingface/endpoints-custom-routers/queued-least-latency:1.0.0",
    "env": {
      "MY_VAR": "value"
    }
  }
}
```

**Fields:**
| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `tag` | ✅ | — | Docker image reference (e.g., `your-org/your-router:1.0.0`) |
| `env` | ❌ | `{}` | Environment variables passed to the router container |
| `port` | ❌ | `3000` | Port the router listens on |

**To remove** the custom router on update: send `"customRouter": {}` (null or absent tag).

### 3.5 Reference Implementation: `queued-least-latency`

HF provides a ready-to-use router at `ghcr.io/huggingface/endpoints-custom-routers/queued-least-latency:1.0.0`.

#### 3.5.1 Routing Strategy

1. **FIFO queue**: Incoming requests pushed onto an in-memory queue
2. **EWMA latency tracking**: Each replica tracked with exponentially weighted moving average of response latencies
3. **Least-loaded dispatch**: Dispatcher picks replica with lowest EWMA latency that is still under a configurable threshold
4. **New replica preference**: Replicas never seen have latency 0 and are picked first — new capacity is used immediately on scale-up
5. **Backpressure**: If all replicas above threshold, requests held in queue until a replica becomes available or timeout elapses
6. **Feedback loop**: After each response, measured end-to-end latency feeds back into the EWMA

#### 3.5.2 Configuration

All settings are environment variables:

**Routing:**
| Variable | Default | Description |
|----------|---------|-------------|
| `CUSTOM_ROUTER_LATENCY_THRESHOLD` | `3.0` | Replica treated as "loaded" once EWMA exceeds this (seconds). New requests stop going to it. |
| `CUSTOM_ROUTER_EWMA_ALPHA` | `0.3` | How quickly EWMA reacts (0=stable, 1=reactive). Rarely needs changing. |

**Queue:**
| Variable | Default | Description |
|----------|---------|-------------|
| `CUSTOM_ROUTER_QUEUE_MAX_SIZE` | `1000` | Max queued requests. Oldest dropped with 503 when full. |
| `CUSTOM_ROUTER_QUEUE_TIMEOUT` | `1200` | Max seconds a request can wait in queue before being dropped with 503. |

**Operational:**
| Variable | Default | Description |
|----------|---------|-------------|
| `CUSTOM_ROUTER_PORT` | `3000` | Router listen port. Must match `customRouter.port` in API config. |
| `CUSTOM_ROUTER_STATE_LOG_INTERVAL` | `30` | Seconds between per-replica state log lines. |

#### 3.5.3 Tuning by Model Type

| Scenario | Approach |
|----------|----------|
| **Burst traffic + autoscaling** | Use queued-least-latency: queued requests drain to new replicas on scale-up |
| **Heterogeneous replica performance** | EWMA routing naturally avoids slow replicas |
| **Diffusion / image gen (no batching benefit)** | Keep threshold at default (3.0s) — one request at a time per replica |
| **LLM (batching increases throughput)** | Raise threshold (e.g., 65.0s) to allow concurrent requests on a replica |

Example for LLM tuning:
```json
"customRouter": {
  "tag": "ghcr.io/huggingface/endpoints-custom-routers/queued-least-latency:1.0.0",
  "env": {
    "CUSTOM_ROUTER_LATENCY_THRESHOLD": "65.0",
    "CUSTOM_ROUTER_QUEUE_MAX_SIZE": "2000"
  }
}
```

#### 3.5.4 Prometheus Metrics

The reference implementation exposes metrics at `GET /_custom_router/metrics`:

| Metric | Type | Description |
|--------|------|-------------|
| `custom_router_queue_depth` | Gauge | Requests currently waiting in the queue |
| `custom_router_backend_ewma_latency_seconds` | Gauge | EWMA latency per replica (addr label) |
| `custom_router_backend_inflight_requests` | Gauge | In-flight requests per replica |
| `custom_router_requests_dispatched_total` | Counter | Requests successfully forwarded |
| `custom_router_requests_evicted_total` | Counter | Requests dropped due to full queue |
| `custom_router_requests_timeout_total` | Counter | Requests dropped due to queue timeout |

`GET /_custom_router/health` also returns a JSON snapshot of current queue depth and per-replica EWMA stats for debugging.

### 3.6 Building Your Own Router

`queued-least-latency` is a starting point. Build your own for KV-cache-aware routing, proactive scale-up signals, or sticky sessions.

**Minimal Go skeleton:**
```go
// POST /_custom_router/set-backends
func handleSetBackends(w http.ResponseWriter, r *http.Request) {
    var payload struct {
        Backends []string `json:"backends"`
    }
    json.NewDecoder(r.Body).Decode(&payload)
    updateMyBackendList(payload.Backends)
    json.NewEncoder(w).Encode(map[string]bool{"ok": true})
}

// GET /_custom_router/health
func handleHealth(w http.ResponseWriter, r *http.Request) {
    json.NewEncoder(w).Encode(map[string]bool{"ok": true})
}

// Everything else is a user request to proxy
func handleProxy(w http.ResponseWriter, r *http.Request) {
    backend := pickBackend() // your routing logic
    forwardTo(w, r, backend)
}
```

The full `queued-least-latency` source in the [endpoints-custom-routers](https://github.com/huggingface/endpoints-custom-routers) repository is a good template to fork.

---

## 4. Production Operations Triad — Putting It Together

```
                    ┌───────────────────┐
                    │   Autoscaling     │
                    │ (how many?)       │
                    └────────┬──────────┘
                             │ feeds
                             ▼
                    ┌───────────────────┐
                    │   Custom Router   │
                    │ (which replica?)  │
                    └────────┬──────────┘
                             │ monitored by
                             ▼
                    ┌───────────────────┐
                    │   Analytics       │
                    │ (how performing?) │
                    └────────┬──────────┘
                             │ informs
                             ▼
                    ┌───────────────────┐
                    │ Tuning decisions  │
                    │ threshold, limits │
                    └───────────────────┘
```

### 4.1 Typical Production Workflow

1. **Start** with hardware-utilization autoscaling (default 80% GPU/CPU)
2. **Monitor** analytics dashboard — watch pending requests as a leading indicator
3. **If** pending requests grow faster than replicas scale up → switch to pending-requests-based autoscaling
4. **If** requests are queuing on busy replicas while new replicas sit idle → enable custom router with queued-least-latency
5. **Tune** router threshold based on whether your model benefits from batching
6. **Export** OpenMetrics to Prometheus/Grafana for long-term trend analysis and alerting

### 4.2 Cost Optimization Strategies

| Strategy | How |
|----------|-----|
| **Scale-to-zero for dev/staging** | Enable scale-to-zero with X-Scale-Up-Timeout for acceptable cold starts |
| **Pending requests for production** | More responsive than hardware metrics — reduces over-provisioning |
| **Custom router for bursty workloads** | Queues smooth traffic to new replicas, preventing premature scale-down |
| **Analytics for rightsizing** | Monitor p99 latency vs. replica count to find the sweet spot |

---

## 5. Configuration Quick Reference

### API Payload

```json
{
  "compute": {
    "scaling": {
      "minReplica": 0,
      "maxReplica": 4,
      "scaleToZeroTimeout": 60,
      "measure": {
        "type": "gpu" | "cpu" | "pendingRequests",
        "value": 80 | 80 | 1.5,
        "window": 60 | 60 | 20
      }
    }
  },
  "customRouter": {
    "tag": "ghcr.io/huggingface/endpoints-custom-routers/queued-least-latency:1.0.0",
    "env": {
      "CUSTOM_ROUTER_LATENCY_THRESHOLD": "3.0",
      "CUSTOM_ROUTER_QUEUE_MAX_SIZE": "1000",
      "CUSTOM_ROUTER_QUEUE_TIMEOUT": "1200"
    }
  }
}
```

### Autoscaling Parameters

| Parameter | Allowed Values | Default |
|-----------|---------------|---------|
| `measure.type` | `"gpu"`, `"cpu"`, `"pendingRequests"` | `"gpu"` (if GPU) else `"cpu"` |
| `measure.value` | Integer threshold | `80` (%, for hardware), `1.5` (per replica, for pending) |
| `measure.window` | Seconds | `60` (hardware), `20` (pending) |
| `scaleToZeroTimeout` | Minutes (minimum 15) | `60` |
| `minReplica` | 0+ (must be 0 if scale-to-zero) | `0` |
| `maxReplica` | 1+ | Depends on plan |

---

## 6. Limitations and Considerations

- **Custom router is API-only** — cannot be configured through the UI
- **OpenMetrics API requires Team or Enterprise plan** — not available on free/Pro tiers
- **Scale-to-zero cold starts** — can take several minutes depending on model size; not suitable for latency-sensitive apps
- **Custom router port must match** — the `customRouter.port` in API config and the `CUSTOM_ROUTER_PORT` env var must agree
- **Load balancer field ignored** — when `customRouter` is set, the `loadBalancer` field in `experimentalFeatures` is ignored
- **Per-replica OpenMetrics** — only available when the endpoint is subscribed to Team or Enterprise
