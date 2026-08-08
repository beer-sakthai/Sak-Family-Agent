---
name: SakThai-hf-sglang-integration
description: "Complete reference on SGLang serving frameworks Hugging Face integration — loading HF models, OpenAI-compatible APIs, offline inference, quantization, LoRA, tool calling, and multi-GPU deployment."
---

# SGLang + Hugging Face Integration

> SGLang is a high-performance serving framework for large language and multimodal models, built by LMSYS. It natively integrates with Hugging Face Hub for model loading, tokenizer use, and chat templates.

## Overview

SGLang (github.com/sgl-project/sglang) is a production-grade inference engine powering 400k+ GPUs worldwide. It loads any Hugging Face model via repo ID or local path, serves it through an OpenAI-compatible API, and provides advanced features like RadixAttention prefix caching, tensor parallelism, FP8 quantization, and speculative decoding.

**Key HF integration points:**
- `--model-path` accepts any HF repo ID (`meta-llama/Llama-3.1-8B-Instruct`) or local path
- Auto-detects safetensors, GGUF, Mistral native, and object-storage URIs
- Uses HF tokenizer & chat template automatically (overrideable with `--chat-template`)
- Supports Hugging Face token for gated repos via `HF_TOKEN` env var
- Downloads and caches models in the standard HF cache dir (`~/.cache/huggingface`)

## Installation

```bash
# Prerequisites: Python 3.10+, NVIDIA GPU (sm80+) with CUDA
pip install --upgrade pip
pip install uv
uv pip install --prerelease=allow sglang
```

For Docker:
```bash
docker run --gpus all --shm-size 32g -p 30000:30000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --env "HF_TOKEN=<your-token>" \
  lmsysorg/sglang:latest \
  python3 -m sglang.launch_server --model-path meta-llama/Llama-3.1-8B-Instruct --host 0.0.0.0 --port 30000
```

## Loading HF Models

### Basic syntax
```bash
python3 -m sglang.launch_server \
  --model-path qwen/qwen2.5-0.5b-instruct \
  --host 0.0.0.0 --port 30000
```

### Load formats (`--load-format`)

| Format | Description |
|--------|-------------|
| `auto` (default) | Load safetensors if available, fall back to PyTorch .bin |
| `safetensors` | Load weights in safetensors format |
| `pt` | Load weights in PyTorch .bin format |
| `npcache` | Load PyTorch format, store numpy cache for faster subsequent loads |
| `dummy` | Random weights (for profiling) |
| `sharded_state` | Each TP worker reads only its pre-sharded shard |
| `fastsafetensors` | Load using fastsafetensors iterator |
| `layered` | Load layer by layer (reduces peak memory for quantization) |
| `gguf` | Load GGUF format (auto-detected from .gguf path) |
| `bitsandbytes` | Load with bitsandbytes quantization |
| `mistral` | Load Mistral native format (auto-detected) |
| `runai_streamer` | Stream from SSDs/filesystems/object storage |
| `remote` | Load from remote KV/filesystem connector |
| `remote_instance` | Pull weights from another running SGLang instance |

### Weight loading performance flags

| Flag | Description | Default |
|------|-------------|---------|
| `--download-dir` | Custom download cache directory for HF models | HF default |
| `--weight-loader-disable-mmap` | Disable mmap for safetensors (slow filesystems) | off |
| `--weight-loader-prefetch-checkpoints` | Prefetch checkpoint files into OS page cache | off |
| `--weight-loader-prefetch-num-threads` | Threads per rank for prefetching | 4 |
| `--weight-loader-drop-cache-after-load` | Call posix_fadvise(DONTNEED) after loading | off |
| `--custom-weight-loader` | Import path of custom weight loading function | — |

### Model loader extra config

Pass JSON to the loader via `--model-loader-extra-config`:

```bash
python3 -m sglang.launch_server \
  --model-path Qwen/Qwen3.6-35B-A3B \
  --model-loader-extra-config '{"enable_multithread_load": true, "num_threads": 16}'
```

## Server Configuration

### Model & Tokenizer arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--model-path` / `--model` | HF repo ID or local path | (required) |
| `--tokenizer-path` | Separate tokenizer path (defaults to model path) | None |
| `--tokenizer-mode` | `auto` (fast if available) or `slow` | auto |
| `--tokenizer-backend` | `huggingface` or `fastokens` | huggingface |
| `--skip-tokenizer-init` | Skip tokenizer init (for debugging) | off |
| `--hf-chat-template-name` | Select named template (e.g., `tool_use`) | None |

### Parallelism

| Argument | Alias | Description |
|----------|-------|-------------|
| `--tensor-parallel-size` | `--tp` | Number of GPUs for tensor parallelism |
| `--data-parallel-size` | `--dp` | Number of GPUs for data parallelism |
| `--nnodes` | | Number of nodes for multi-node TP |
| `--node-rank` | | Node rank for multi-node (0-indexed) |

### Memory & Performance

| Argument | Description | Default |
|----------|-------------|---------|
| `--mem-fraction-static` | Fraction of GPU memory for KV cache pool | 0.9 |
| `--max-total-tokens` | Max total tokens (input + output) | based on model |
| `--chunked-prefill-size` | Token budget per prefill chunk | 8192 |
| `--kv-cache-dtype` | KV cache data type (e.g., `fp8_e4m3`) | auto |
| `--enable-torch-compile` | Enable torch.compile acceleration | off |
| `--enable-deterministic-inference` | Deterministic mode | off |
| `--quantization` | Quantize weights on load | None |

### Config file

```bash
python3 -m sglang.launch_server --config config.yaml
```

```yaml
# config.yaml
model-path: meta-llama/Meta-Llama-3-8B-Instruct
host: 0.0.0.0
port: 30000
tensor-parallel-size: 2
enable-metrics: true
log-requests: true
```

## API Reference

### OpenAI-Compatible API

SGLang is fully OpenAI API compatible.

**Chat Completions:**
```bash
curl http://localhost:30000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen2.5-0.5b-instruct",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0,
    "max_tokens": 64
  }'
```

**Using OpenAI Python client:**
```python
import openai
client = openai.Client(base_url="http://127.0.0.1:30000/v1", api_key="None")
response = client.chat.completions.create(
    model="qwen/qwen2.5-0.5b-instruct",
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0, max_tokens=64,
)
print(response.choices[0].message.content)
```

**Streaming:**
```python
stream = client.chat.completions.create(
    model="...", messages=[...], stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

**Additional OpenAI endpoints:** `/v1/completions`, `/v1/embeddings`, `/v1/chat/completions` (with image_url for vision models)

**Other compatible endpoints:** `/v1/messages` (Anthropic API), Ollama streaming format

### Native API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/generate` | POST | Text generation |
| `/get_model_info` | GET | Model metadata (HF model path, type, architectures) |
| `/server_info` | GET | Server arguments, limits, memory pools |
| `/health` | GET | Health check |
| `/health_generate` | GET | Health check with test generation |
| `/flush_cache` | POST | Clear KV cache |
| `/update_weights` | POST | Hot-swap model weights |
| `/encode` | POST | Embedding encode |
| `/v1/rerank` | POST | Cross-encoder reranking |
| `/v1/score` | POST | Decoder-only scoring |
| `/classify` | POST | Reward/classification |
| `/tokenize` | POST | Tokenize text |
| `/detokenize` | POST | Detokenize IDs |

**Generate example:**
```python
import requests
response = requests.post(
    "http://localhost:30000/generate",
    json={
        "text": "The capital of France is",
        "sampling_params": {"temperature": 0, "max_new_tokens": 32},
    },
)
print(response.json())
```

### Offline Engine API (No Server)

```python
import sglang as sgl

llm = sgl.Engine(model_path="qwen/qwen2.5-0.5b-instruct")

outputs = llm.generate(
    ["Hello, my name is", "The capital of France is"],
    sampling_params={"temperature": 0.8, "top_p": 0.95},
)

for prompt, output in zip(["Hello...", "Capital..."], outputs):
    print(f"Generated: {output['text']}")

llm.shutdown()
```

## Advanced Features

### RadixAttention (Prefix Caching)

SGLang's core innovation — a tree-structured RadixTree that caches KV computations by their token prefix. Activated by default. Automatically shares cache across requests with common prefixes.

### Quantization

| `--quantization` | Description |
|-----------------|-------------|
| `fp8` | FP8 E4M3 weight quantization |
| `int8` | INT8 weight quantization |
| `int4` | INT4 weight quantization |
| `nvfp4` | NVFP4 (NVIDIA Blackwell format) |
| `--kv-cache-dtype fp8_e4m3` | FP8 KV cache |
| `--kv-cache-dtype fp8_e5m2` | FP8 KV cache wider exponent |

### LoRA Serving

```bash
python3 -m sglang.launch_server \
  --model-path meta-llama/Llama-3.1-8B-Instruct \
  --lora-paths /path/to/adapter1 /path/to/adapter2
```

Key args: `--enable-lora`, `--max-loras-per-batch` (default 8), `--max-lora-rank`, `--lora-target-modules`, `--lora-backend` (`triton` or `csgmv`).

### Speculative Decoding (EAGLE3)

```bash
python3 -m sglang.launch_server \
  --model-path meta-llama/Llama-3.1-8B-Instruct \
  --speculative-draft-model-path lmsys/SGLang-EAGLE3-Llama-3.1-8B-Instruct-SpecForge
```

Draft models available on HF: https://huggingface.co/lmsys

### Structured Outputs

```bash
python3 -m sglang.launch_server \
  --model-path meta-llama/Llama-3.1-8B-Instruct \
  --enable-structured-output
```

Supports JSON mode, grammar, regex constraints.

### Tool Calling

```bash
python3 -m sglang.launch_server \
  --model-path meta-llama/Llama-3.1-8B-Instruct \
  --tool-call-parser llama
```

Supported parsers: `llama`, `qwen`, `mistral`, `hermes`, `python`, etc.

### Multi-GPU Deployment

```bash
# Tensor parallelism (single node, 4 GPUs)
python3 -m sglang.launch_server \
  --model-path meta-llama/Llama-3.1-8B-Instruct \
  --tensor-parallel-size 4

# Multi-node
python3 -m sglang.launch_server \
  --model-path model-id --tp 4 --nnodes 2 --node-rank 0 \
  --dist-init-addr host:50000

# Data parallelism (better throughput)
python3 -m sglang.launch_server \
  --model-path model-id --dp 2 --tp 2
```

### Hot-Swapping Model Weights

```bash
curl http://localhost:30000/update_weights \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"model_path": "new-model-id", "load_format": "safetensors"}'
```

## Supported HF Model Families

- **LLMs**: Llama 3/4, Qwen 2.5/3/3.5/3.6, DeepSeek V2/V3/V4, Mistral, Gemma 4, Phi-4, GLM-4/5, Kimi-K, MiniMax-M, MiMo
- **VLMs**: Qwen2.5-VL, Qwen3-VL, InternVL3.5, LLaVA, MiniCPM-V, GLM-4V
- **Embedding**: EmbeddingGemma, BGE, E5
- **Reward/Rerank/Classify**: Standard head variants

Fallback to HuggingFace Transformers via `--transformers-fallback`.

## Docker with HF

```bash
docker run --gpus all --shm-size 32g -p 30000:30000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --env "HF_TOKEN=hf_xxxx" \
  lmsysorg/sglang:latest \
  python3 -m sglang.launch_server \
    --model-path meta-llama/Llama-4-Scout-17B-16E-Instruct \
    --host 0.0.0.0 --port 30000
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `HF_TOKEN` | HF auth token for gated repos |
| `HF_ENDPOINT` | Override HF Hub URL (e.g., mirror) |
| `HF_HOME` | Override HF cache directory root |
| `SGLANG_HF_MODEL_CACHE` | Custom HF model cache path |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| CUDA_HOME not set | `export CUDA_HOME=/usr/local/cuda-<ver>` |
| OOM during serving | `--mem-fraction-static 0.7` |
| OOM during long prefill | `--chunked-prefill-size 4096` |
| GPU peer access error | `--enable-p2p-check` |
| No chat template | `--chat-template my_template.jinja` |
| Named template selection | `--hf-chat-template-name tool_use` |

## See Also

- Official docs: https://docs.sglang.io/
- GitHub: https://github.com/sgl-project/sglang
- HF collection: https://huggingface.co/lmsys
- Server arguments: https://docs.sglang.io/docs/advanced_features/server_arguments
- Model loading: https://docs.sglang.io/docs/advanced_features/model_loading