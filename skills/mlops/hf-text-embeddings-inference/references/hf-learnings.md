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
