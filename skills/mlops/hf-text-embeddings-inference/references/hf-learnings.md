# HF Learnings — Text Embeddings Inference

## 2026-07-24: hf-text-embeddings-inference — Deep Dive (Topic #104)

### Summary
Comprehensive deep-dive into Hugging Face Text Embeddings Inference (TEI) — a high-performance Rust-based inference server for text embedding models. Covers architecture, deployment, API, supported models, and integration with `huggingface_hub.InferenceClient`.

### Core Architecture

TEI is written in Rust and uses:
- **Candle** — ML framework in Rust (no Python/PyTorch dependency at runtime)
- **Flash Attention** — optimized attention kernels (v1/v2 depending on GPU arch)
- **cuBLASLt** — CUDA linear algebra for NVIDIA GPUs
- **Safetensors** — fast, safe weight loading (no pickle vulnerability)
- **Token-based dynamic batching** — batches dynamically sized by total tokens, not request count

Key architectural advantages:
- No model graph compilation step (unlike TensorRT, ONNX Runtime)
- Small Docker images (~500MB–1.5GB vs 10GB+ for PyTorch-based solutions)
- Fast boot times (<5s from container start to ready)
- True serverless capability

### Supported Model Architectures

| Architecture | Examples | Position Encoding |
|---|---|---|
| BERT | `WhereIsAI/UAE-Large-V1` | Absolute |
| NomicBERT | `nomic-ai/nomic-embed-text-v1.5` | Absolute |
| JinaBERT | `jinaai/jina-embeddings-v2-base-en` | Alibi |
| XLM-RoBERTa | `intfloat/multilingual-e5-large-instruct` | Absolute |
| GTE (Alibaba) | `Alibaba-NLP/gte-Qwen2-7B-instruct` | Rope |
| Qwen2 | `Alibaba-NLP/gte-Qwen2-1.5B-instruct` | Rope |
| Qwen3 | `Qwen/Qwen3-Embedding-0.6B` | Rope |
| Mistral | `Salesforce/SFR-Embedding-2_R` | Rope |
| MPNet | `sentence-transformers/all-mpnet-base-v2` | Absolute |
| ModernBERT | `answerdotai/ModernBERT-large` | RoPE + no bias |
| Gemma3 | `google/embeddinggemma-300m` | RoPE + GeGLU |
| CamemBERT | Various French models | Absolute |

Re-ranking and sequence classification also supported on XLM-RoBERTa and GTE architectures.

### Docker Deployment

**GPU (CUDA):**
```bash
model=Qwen/Qwen3-Embedding-0.6B
volume=$PWD/data
docker run --gpus all -p 8080:80 -v $volume:/data --pull always \
  ghcr.io/huggingface/text-embeddings-inference:cuda-1.9 \
  --model-id $model
```

**CPU:**
```bash
docker run -p 8080:80 -v $volume:/data --pull always \
  ghcr.io/huggingface/text-embeddings-inference:cpu-1.9 \
  --model-id $model
```

**Apple Silicon (Metal):**
```bash
brew install text-embeddings-inference
text-embeddings-router --model-id $model --port 8080
```

**Docker Image Tags (architecture-specific):**

| Image Tag | Target |
|---|---|
| `cuda-1.9` | Ampere 8.0 (A100, A30) |
| `86-1.9` | Ampere 8.6 (A10, A40) |
| `turing-1.9` | Turing (T4, RTX 2000) — experimental |
| `hopper-1.9` | Hopper (H100) |
| `100-1.9` | Blackwell 10.0 (B200, GB200) — experimental |
| `89-1.9` | Ada Lovelace (RTX 4000) |
| `cpu-1.9` | x86 CPU |
| `cpu-arm64-1.9` | ARM64 CPU |

Add `-grpc` suffix for gRPC-enabled images.

### API Endpoints

| Endpoint | Method | Description | Returns |
|---|---|---|---|
| `/embed` | POST | Dense embeddings | `[[float]]` array |
| `/embed_sentence` | POST | Sentence-level embeddings | `[[float]]` array |
| `/embed_sparse` | POST | Sparse (SPLADE) embeddings | `[{index, value}]` |
| `/rerank` | POST | Re-rank query-document pairs | `[{index, score}]` |
| `/predict` | POST | Sequence classification | `[{label, score}]` |
| `/info` | GET | Model metadata | JSON |
| `/health` | GET | Health check | 200 OK |
| `/docs` | GET | Swagger UI | HTML |

**Embed request:**
```bash
curl 127.0.0.1:8080/embed \
  -X POST \
  -d '{"inputs":"What is Deep Learning?"}' \
  -H 'Content-Type: application/json'
```

**Batch embed:**
```bash
curl 127.0.0.1:8080/embed \
  -X POST \
  -d '{"inputs":["First text","Second text","Third text"]}' \
  -H 'Content-Type: application/json'
```

**Re-rank request:**
```bash
curl 127.0.0.1:8080/rerank \
  -X POST \
  -d '{"query":"What is deep learning?","texts":["Deep learning is ML","NLP is text processing"],"raw_scores":false}' \
  -H 'Content-Type: application/json'
```

### gRPC API

Protobuf: https://github.com/huggingface/text-embeddings-inference/blob/main/proto/tei.proto

```bash
# Start with gRPC image
docker run --gpus all -p 8080:80 ... ghcr.io/huggingface/text-embeddings-inference:cuda-1.9-grpc --model-id $model

# Query via grpcurl
grpcurl -d '{"inputs": "What is Deep Learning"}' -plaintext 0.0.0.0:8080 tei.v1.Embed/Embed
```

### Key CLI Arguments

| Flag | Default | Description |
|---|---|---|
| `--model-id` | required | HF model ID or local path |
| `--revision` | main | Model revision/branch |
| `--pooling` | auto | `cls`, `mean`, `last-token`, `splade` |
| `--dtype` | auto | `float16`, `float32` |
| `--max-batch-tokens` | 16384 | Max tokens per batch (critical perf tunable) |
| `--max-concurrent-requests` | 512 | Backpressure control |
| `--max-client-batch-size` | 32 | Max inputs per request |
| `--auto-truncate` | true | Truncate inputs exceeding model max length |
| `--default-prompt` | null | Prompt prepended to every input |
| `--default-prompt-name` | null | Sentence-Transformers prompt key |
| `--served-model-name` | model-id | OpenAI-compatible model name |
| `--hf-token` | env | Auth token for private/gated models |
| `--port` | 3000 | HTTP server port |
| `--json-output` | false | JSON structured logging |
| `--otlp-endpoint` | null | OpenTelemetry gRPC endpoint |
| `--prometheus-port` | 9000 | Metrics endpoint |

### Pooling Strategies

| Strategy | Method | Use Case |
|---|---|---|
| `cls` | Select CLS token embedding | Default for BERT-based models |
| `mean` | Average all token embeddings | Default for Sentence-BERT models |
| `last-token` | Select last token | Some modern architectures |
| `splade` | Sparse Lexical Expansion | Sparse retrieval (ForMaskedLM models only) |

SPLADE pooling requires a `ForMaskedLM` model and returns sparse vectors via `/embed_sparse`.

### Hugging Face InferenceClient Integration

The `InferenceClient.feature_extraction()` method directly integrates with TEI:

```python
from huggingface_hub import InferenceClient

client = InferenceClient()

# Single text embedding
embedding = client.feature_extraction(
    "What is Deep Learning?",
    model="Qwen/Qwen3-Embedding-0.6B"
)
# Returns: np.ndarray of shape (768,) for single text

# Batch embedding
embeddings = client.feature_extraction(
    ["Text one", "Text two", "Text three"],
    model="Qwen/Qwen3-Embedding-0.6B"
)
# Returns: np.ndarray of shape (3, 768)

# With normalization
embedding = client.feature_extraction(
    "What is Deep Learning?",
    model="Qwen/Qwen3-Embedding-0.6B",
    normalize=True
)

# With prompt_name (Sentence-Transformers style)
embedding = client.feature_extraction(
    "What is the capital of France?",
    model="intfloat/multilingual-e5-large-instruct",
    prompt_name="query"
)

# Sentence similarity
similarity = client.sentence_similarity(
    "The cat sits on the mat",
    other_texts=["A dog plays in the yard", "A feline rests on a rug"],
    model="sentence-transformers/all-MiniLM-L6-v2"
)
```

**Key parameters:**
- `normalize` (bool) — L2 normalize output embeddings (TEI-only)
- `prompt_name` (str) — Sentence-Transformers prompt key
- `truncate` (bool) — Enable truncation (TEI-only)
- `truncation_direction` ("left"|"right") — Which side to truncate
- `dimensions` (int) — Output dimension reduction (OpenAI-compatible endpoints)
- `encoding_format` ("float"|"base64") — Output format

### Private & Gated Models

```bash
export HF_TOKEN=<your-read-token>
docker run --gpus all -e HF_TOKEN=$HF_TOKEN -p 8080:80 ... --model-id $private_model
```

### Air Gapped Deployment

```bash
mkdir models && cd models
git lfs install
git clone https://huggingface.co/Qwen/Qwen3-Embedding-0.6B

docker run --gpus all -p 8080:80 -v $PWD:/data --pull always \
  ghcr.io/huggingface/text-embeddings-inference:cuda-1.9 \
  --model-id /data/Qwen/Qwen3-Embedding-0.6B
```

### Distributed Tracing & Monitoring

```bash
docker run ... \
  --otlp-endpoint http://localhost:4317 \
  --otlp-service-name tei-server \
  --json-output
```
- OpenTelemetry gRPC endpoint for traces
- Prometheus metrics on port 9000
- JSON structured logging for log aggregators

### Zero-Cost Strategies

1. **CPU-only Docker** — `cpu-1.9` tag runs on any x86 server with no GPU
2. **Serverless Inference API** — `InferenceClient.feature_extraction()` with default/community models
3. **Small models on CPU** — Models like `nomic-ai/nomic-embed-text-v1.5` (137M params) run reasonably fast on CPU
4. **Free Inference Endpoints** — ZeroGPU for Spaces that need embeddings
5. **Apple Silicon local** — Metal acceleration via Homebrew install, zero cloud cost

### Benchmark Reference

For `BAAI/bge-base-en-v1.5` on NVIDIA A10 (seq len 512):
- Batch size 1: ~4ms latency, ~250 seq/s throughput
- Batch size 32: ~15ms latency, ~2100 seq/s throughput
- Outperforms ONNX Runtime, PyTorch, and Sentence-Transformers in both latency and throughput

### Resources
- GitHub: https://github.com/huggingface/text-embeddings-inference
- Docs: https://huggingface.co/docs/text-embeddings-inference/en/index
- Swagger API: https://huggingface.github.io/text-embeddings-inference
- gRPC proto: https://github.com/huggingface/text-embeddings-inference/blob/main/proto/tei.proto
- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard
- RAG containers with TEI: https://github.com/plaggy/rag-containers
- Cookbook (Inference Endpoints + TEI): https://huggingface.co/learn/cookbook/automatic_embedding_tei_inference_endpoints

---

## 2026-07-24: hf-text-embeddings-inference-v2 — OpenAI-Compatible API, Router Architecture & Matryoshka (Topic #106)

### Summary
Second deep-dive into TEI covering the OpenAI-compatible `/v1/embeddings` endpoint, the internal router architecture (request pipeline, validation, tokenization, batching, inference), Matryoshka/linear dimension reduction, direct TEI endpoint connection patterns, and Kubernetes deployment patterns.

### OpenAI-Compatible `/v1/embeddings` Endpoint

TEI exposes an OpenAI-compatible embeddings endpoint at `/v1/embeddings` when started, enabling drop-in replacement for OpenAI clients:

```bash
docker run --gpus all -p 8080:80 ... \
  --model-id WhereIsAI/UAE-Large-V1 \
  --served-model-name text-embedding-3-large  # optional: rename for client compat
```

**Request format (OpenAI-compatible):**
```bash
curl http://localhost:8080/v1/embeddings \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "input": "The food was delicious and the service was great",
    "model": "text-embedding-3-large",
    "encoding_format": "float",
    "dimensions": 256
  }'
```

**Response format:**
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [0.0023, -0.0192, ...]
    }
  ],
  "model": "WhereIsAI/UAE-Large-V1",
  "usage": {
    "prompt_tokens": 9,
    "total_tokens": 9
  }
}
```

**Python client (OpenAI SDK):**
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-needed"  # TEI doesn't validate API keys locally
)

response = client.embeddings.create(
    input="Hello world",
    model="text-embedding-3-large",
    dimensions=256  # Matryoshka dimension reduction
)

embedding = response.data[0].embedding
```

**Key differences vs OpenAI API:**
- `api_key` is accepted but not validated (TEI is a local service)
- No rate limiting built-in (use `--max-concurrent-requests`)
- `dimensions` parameter only works with models that support Matryoshka

### Router Architecture & Request Pipeline

The TEI binary (`text-embeddings-router`) follows this internal pipeline:

```
HTTP/gRPC Request
    │
    ▼
┌─────────────┐
│ Router      │  ──  Request validation (JSON parse, type check, size check)
│ (Rust/Tokio)│  ──  Route dispatch (/embed vs /rerank vs /v1/embeddings)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Tokenizer   │  ──  Tokenize inputs (model-specific tokenizer)
│              │  ──  Apply truncation (if auto-truncate enabled)
│              │  ──  Apply default prompt (if --default-prompt set)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Batcher     │  ──  Token-aware dynamic batching
│              │  ──  Groups requests into batches up to --max-batch-tokens
│              │  ──  Maintains request-to-batch mapping for responses
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Backend     │  ──  Candle inference (Flash Attention kernels)
│ (Rust/Candle)│  ──  Pooling: CLS/mean/last-token/SPLADE
│              │  ──  Normalization (if requested)
│              │  ──  Dimension reduction (Matryoshka)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Response    │  ──  De-batch results back to individual responses
│ Builder     │  ──  Format: raw array, OpenAI-compatible JSON, or gRPC protobuf
└─────────────┘
```

**Token-aware batching algorithm:**
1. A new request arrives and is tokenized
2. The batcher checks if adding it to the current pending batch exceeds `--max-batch-tokens`
3. If not, it's added; if yes, the pending batch is dispatched and a new batch starts
4. Batches are dispatched to the backend every ~1ms or when the pending batch is full
5. Result: each GPU kernel invocation processes exactly the right number of tokens — no wasted compute

### Matryoshka Dimension Reduction

TEI supports Matryoshka (linear dimension reduction) for models fine-tuned with Matryoshka representation learning:

**Supported Matryoshka models:**
- `WhereIsAI/UAE-Large-V1` — supports dims 1024, 768, 512, 256
- `intfloat/multilingual-e5-large-instruct` — via dimension parameter
- `Alibaba-NLP/gte-Qwen2-1.5B-instruct` — supports dim reduction

**Via REST API:**
```bash
curl http://localhost:8080/v1/embeddings \
  -X POST \
  -d '{"input": "Hello world", "model": "default", "dimensions": 256}'
```

**Via InferenceClient:**
```python
embedding = client.feature_extraction(
    "Hello world",
    model="WhereIsAI/UAE-Large-V1",
    dimensions=256
)
```

**When to use dimension reduction:**
- **256–512 dims**: Semantic search with Pinecone/Weaviate (reduced storage cost, minimal quality loss)
- **128 dims**: High-throughput classification, clustering
- **768+ dims**: Fine-grained retrieval, re-ranking quality-critical

Matryoshka works by selecting the first N dimensions from the model's native output — the model is specifically trained so early dimensions carry the most information.

### Direct TEI Endpoint Connection Pattern

When running a self-hosted TEI instance, connect via `InferenceClient` with a `base_url`:

```python
from huggingface_hub import InferenceClient

# Connect directly to a TEI endpoint (not via HF serverless)
client = InferenceClient(base_url="http://localhost:8080")

embedding = client.feature_extraction(
    "Direct TEI endpoint connection",
    normalize=True
)
# Returns np.ndarray — no Hub model ID needed

# Re-rank via TEI
results = client.sentence_similarity(
    "Query text",
    other_texts=["Option A", "Option B", "Option C"],
    base_url="http://localhost:8080"
)
```

**Advantages over serverless:**
- Zero latency from Hub routing (direct TCP)
- No rate limits (controlled by `--max-concurrent-requests`)
- Can serve gated/private models without exposing tokens to Hub proxies
- Works air-gapped (no internet required)

**Health check pattern for production:**
```python
import requests

def tei_ready(url="http://localhost:8080/health") -> bool:
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except requests.ConnectionError:
        return False
```

### Kubernetes Deployment

**Minimal deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tei-embedding
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tei
  template:
    metadata:
      labels:
        app: tei
    spec:
      containers:
      - name: tei
        image: ghcr.io/huggingface/text-embeddings-inference:cpu-1.9
        args:
        - --model-id
        - WhereIsAI/UAE-Large-V1
        - --port
        - "80"
        - --max-batch-tokens
        - "8192"
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: tei-embedding
spec:
  selector:
    app: tei
  ports:
  - port: 8080
    targetPort: 80
```

**Key K8s considerations:**
- Use `terminationGracePeriodSeconds: 120` to allow in-flight requests to finish
- Set `--max-concurrent-requests` to match pod resource limits
- For GPU nodes, add `nvidia.com/gpu: 1` resource request
- `--auto-truncate` prevents OOM from long sequences
- Prometheus metrics on port 9000 for HPAs based on request latency

### TEI Logging & Debugging

**JSON structured logging:**
```bash
docker run ... --json-output
# Output: {"timestamp":"...","level":"INFO","message":"Embed request","batch_size":4,"total_tokens":512}
```

**Verbose startup logging:**
```bash
RUST_LOG=info text-embeddings-router --model-id $model
# Shows: tokenizer loading, device detection, pooling auto-select
```

**Common issues & fixes:**

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Model requires custom tokenizer` | Architecture not in built-in list | Use `--revision` with custom branch or open TEI issue |
| `CUDA out of memory` | `--max-batch-tokens` too high | Reduce from 16384 to 8192 or 4096 |
| `/embed_sparse` returns empty | Model not ForMaskedLM | Use `splade-cocondenser-selfdistil` or similar |
| Slow first request | Model loading + JIT compilation | Pre-warm with a dummy request at startup |
| `501 Not Implemented` for `/v1/embeddings` | Older TEI version | Update to TEI ≥1.5 |

### Best Practices Summary

1. **Tune `--max-batch-tokens`** — start at 16384, increase if GPU memory allows, decrease if OOM
2. **Use `--auto-truncate true`** — prevents silent failures on long documents
3. **Set `--pooling auto`** — let TEI pick the right pooling per architecture
4. **Pre-warm with a dummy request** — avoids cold-start latency in production
5. **Use CPU for batch <50 req/s** — GPU overhead isn't worth it at low throughput
6. **Matryoshka dims for cost savings** — 256 dims reduces vector DB storage by 75% vs 1024
7. **Always set resource limits** — embedding models can consume significant memory
