---
name: SakThai-hf-text-generation-inference
description: "Hugging Face Text Generation Inference (TGI) \u2014 deploy and serve LLMs with continuous\
  \ batching, Flash Attention, quantization, and OpenAI-compatible API."
---

# HF Text Generation Inference (TGI)

## ⚠️ Maintenance Mode Notice

As of 2025, **TGI is in maintenance mode**. Hugging Face recommends adopting these downstream engines for new projects:
- **[vLLM](https://github.com/vllm-project/vllm)** — highest throughput, PagedAttention, general-purpose
- **[SGLang](https://github.com/sgl-project/sglang)** — structured generation, efficient prefix caching
- **[llama.cpp](https://github.com/ggerganov/llama.cpp)** — CPU/edge inference, local deployment
- **[MLX](https://github.com/ml-explore/mlx)** — Apple Silicon optimization

TGI still receives minor bugfix and documentation PRs.

## When to use

Use when you are already in the Hugging Face ecosystem (Inference API, Inference Endpoints) and want the simplest out-of-the-box serving. For new greenfield projects, prefer vLLM.

## Quick Start

### Docker (recommended)

Latest image: `ghcr.io/huggingface/text-generation-inference:3.3.5`

```bash
model=HuggingFaceH4/zephyr-7b-beta
volume=$PWD/data

docker run --gpus all --shm-size 1g -p 8080:80 -v $volume:/data \
    ghcr.io/huggingface/text-generation-inference:3.3.5 --model-id $model
```

### Basic inference request

```bash
curl 127.0.0.1:8080/generate \
    -X POST \
    -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":20}}' \
    -H 'Content-Type: application/json'
```

### Streaming inference (SSE)

```bash
curl 127.0.0.1:8080/generate_stream \
    -X POST \
    -d '{"inputs":"Explain quantum computing","parameters":{"max_new_tokens":100}}' \
    -H 'Content-Type: application/json'
```

### OpenAI-compatible Messages API

```bash
curl localhost:8080/v1/chat/completions \
    -X POST \
    -d '{
  "model": "tgi",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is deep learning?"}
  ],
  "stream": true,
  "max_tokens": 20
}' \
    -H 'Content-Type: application/json'
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Continuous Batching** | Mix prefill and decode requests for maximum throughput |
| **Flash Attention v2** | Optimized attention kernel for speed and memory |
| **Paged Attention** | Block-based KV cache management (vLLM-style) |
| **Tensor Parallelism** | Shard model across multiple GPUs |
| **Token Streaming** | Server-Sent Events for real-time output |
| **OpenAI-compatible API** | `/v1/chat/completions` endpoint |
| **Quantization** | bitsandbytes, GPT-Q, AWQ, EETQ, Marlin, FP8 |
| **Guidance/JSON** | Structured output via outlines library |
| **Speculation** | Medusa heads and ngram speculation (~2x speedup) |
| **Monitoring** | Prometheus metrics, OpenTelemetry tracing |

## Common Workflows

### Workflow 1: Serve a gated model (e.g., Llama 3)

```bash
token=<your HF READ token>

docker run --gpus all --shm-size 1g \
    -e HF_TOKEN=$token \
    -p 8080:80 \
    -v $PWD/data:/data \
    ghcr.io/huggingface/text-generation-inference:3.3.5 \
    --model-id meta-llama/Meta-Llama-3.1-8B-Instruct
```

### Workflow 2: Quantized serving (AWQ)

```bash
docker run --gpus all --shm-size 1g \
    -p 8080:80 \
    -v $PWD/data:/data \
    ghcr.io/huggingface/text-generation-inference:3.3.5 \
    --model-id TheBloke/Llama-2-7B-AWQ \
    --quantize awq
```

### Workflow 3: Tensor parallelism (multi-GPU)

```bash
docker run --gpus all --shm-size 1g \
    -p 8080:80 \
    -v $PWD/data:/data \
    ghcr.io/huggingface/text-generation-inference:3.3.5 \
    --model-id meta-llama/Llama-2-70b-hf \
    --num-shard 4
```

### Workflow 4: Enable speculative decoding

```bash
docker run --gpus all --shm-size 1g \
    -p 8080:80 \
    -v $PWD/data:/data \
    ghcr.io/huggingface/text-generation-inference:3.3.5 \
    --model-id meta-llama/Llama-3.1-8B-Instruct \
    --speculate 5 \
    --draft-model-id google/gemma-2-2b-it
```

## CLI Flags Reference

| Flag | Purpose |
|------|---------|
| `--model-id` | Model name on Hugging Face Hub |
| `--num-shard` | Number of GPU shards for tensor parallelism |
| `--quantize` | Quantization method (bitsandbytes, gptq, awq, eetq, marlin, fp8) |
| `--max-total-tokens` | Max sequence length (prompt + generation) |
| `--max-batch-prefill-tokens` | Max tokens in prefill batch |
| `--max-input-length` | Max input prompt length |
| `--speculate` | Number of tokens to speculate |
| `--draft-model-id` | Draft model for speculation |
| `--otlp-endpoint` | OpenTelemetry collector endpoint |
| `--otlp-service-name` | Service name for distributed tracing |
| `--host` | Bind address (default: 0.0.0.0) |
| `--port` | HTTP port (default: 80) |

## Hardware Support

- **NVIDIA** (primary, CUDA 12.2+)
- **AMD** (MI210/MI250 via ROCm images)
- **Intel Gaudi** (via tgi-gaudi fork)
- **Google TPU** (via optimum-tpu)
- **AWS Inferentia** (via optimum-neuron)

## Monitoring

TGI exposes Prometheus metrics and OpenTelemetry tracing:

```bash
# Prometheus metrics
curl http://localhost:8080/metrics

# Enable OpenTelemetry
docker run ... ghcr.io/huggingface/text-generation-inference:3.3.5 \
    --model-id $model \
    --otlp-endpoint http://otel-collector:4318
```

## Common Pitfalls

1. **Shared Memory**: Always set `--shm-size 1g` for NCCL tensor parallelism
2. **CUDA version**: Use NVIDIA drivers with CUDA 12.2+ for best performance
3. **CPU-only**: Remove `--gpus all` and add `--disable-custom-kernels` (performance will be poor)
4. **Gated models**: Always set `HF_TOKEN` environment variable
5. **OOM**: Reduce `--max-total-tokens` or enable quantization

## When to use vs alternatives

| Tool | Best for |
|------|----------|
| **TGI** | Hugging Face ecosystem, quick start, Inference Endpoints |
| **vLLM** | Highest throughput, production APIs, new projects |
| **SGLang** | Structured generation, prefix caching |
| **llama.cpp** | CPU inference, edge devices, local use |
| **MLX** | Apple Silicon Macs |

## Resources

- Docs: https://huggingface.co/docs/text-generation-inference
- GitHub: https://github.com/huggingface/text-generation-inference
- Swagger API: https://huggingface.github.io/text-generation-inference
- Supported models: https://huggingface.co/docs/text-generation-inference/supported_models
