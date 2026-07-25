# HF Learnings Log — hf-text-generation-inference (TGI)

## 2026-07-25: Hugging Face Text Generation Inference — Complete Deep Dive

### Summary
Comprehensive deep-dive into Hugging Face Text Generation Inference (TGI) v3.3.5 — the serving toolkit for Large Language Models. Covers the full architecture: TGI v3 performance leap (3x more tokens, 13x faster than vLLM on long prompts), streaming via SSE, continuous batching with chunked prefill, PagedAttention, quantization (GPTQ/AWQ/bitsandbytes/EETQ/Marlin/FP8/EXL2), speculative decoding (Medusa + n-gram), tensor parallelism, guidance/structured output via outlines, LoRA serving, watermarking, multi-backend support (NVIDIA/AMD/Gaudi/Neuron/TPU/TRT-LLM/llama.cpp), the complete metrics surface, and the OpenAI-compatible Messages API. This builds on the existing quick-start SKILL.md with deep architectural and operational knowledge.

### Verified Status
- TGI is now in **maintenance mode** (confirmed on docs homepage as of July 2026)
- HF recommends: **vLLM**, **SGLang**, **llama.cpp**, **MLX** for new projects
- TGI still receives minor bugfix and documentation PRs
- Latest version: **3.3.5** (from Docker image tag)

---

## 1. TGI v3 Architecture & Performance

### The v3 Leap

TGI v3 represents a major architectural overhaul. Key performance claims (verified from official docs):

| Metric | TGI v3 | vLLM | Model | Hardware |
|--------|--------|------|-------|----------|
| Small test (200 req, 8K total) | 4.8s | 6.0s | Llama 3.1 8B | 4xL4 |
| Long test (20 req, 200K total) **2nd run** | **3.2s** | **12.5s** | Llama 3.1 8B | 4xL4 |
| Long test, 70B, 2nd run | **2.0s** | **27.5s** | Llama 3.1 70B | 8xH100 |
| L4 single (24GB) max context | **30K tokens** | ~10K tokens | Llama 3.1 8B | 1xL4 |

**13x faster on long prompts with prefix caching, up to 30x without.**

### Technical Innovations Behind v3

1. **New kernels**: flashinfer + flashdecoding for better scheduling at large prompt lengths
2. **Optimized prefix caching**: Overhead is ~6µs (microseconds) for cache lookup — uses a beast data structure by Daniël de Kok
3. **Chunked prefill**: Finer control over compute resources, reducing VRAM usage
4. **Kernel fusion**: Many small bookkeeping kernels fused together — significant for small models where kernel launch overhead dominates
5. **VRAM efficiency**: Logits calculation removed from default path — Llama 3.1-8B logits for 100K tokens = 25.6GB (more than the 16GB model!). Use `--enable-prefill-logprobs` to re-enable.

### Prefix Caching Caveats

- **Constrained KV-cache**: If KV-cache space is limited, queries contend for slots. Mitigate by reducing `--max-total-tokens` or using more/larger GPUs.
- **Replication**: With multiple replicas behind a single endpoint, prefix cache won't persist across replicas. Use **sticky sessions** (consistent routing per user) to benefit.

---

## 2. Streaming Architecture

### How It Works

TGI uses **Server-Sent Events (SSE)** — the client sends a request, opens an HTTP connection, subscribes to updates, and the server pushes tokens as they're generated. No further requests needed. SSE is:

- **Unidirectional** (server → client only)
- **HTTP-based** (simple, no WebSocket complexity)
- **Different from polling** (no empty responses)
- **Different from Webhooks** (simpler, no bidirectional communication)

### Streaming Endpoints

- `/generate_stream` — custom TGI streaming endpoint
- `/v1/chat/completions` — OpenAI-compatible streaming (set `stream: true`)

### Backpressure

When overloaded, TGI returns **HTTP 503 with `overloaded` error type**. Configure max concurrent requests with `--max-concurrent-requests`.

### Client Libraries

```python
# InferenceClient (sync)
from huggingface_hub import InferenceClient
client = InferenceClient(base_url="http://127.0.0.1:8080")
stream = client.chat.completions.create(
    messages=[...], stream=True, max_tokens=1024
)
for chunk in stream:
    print(chunk.choices[0].delta.content)

# AsyncInferenceClient
client = AsyncInferenceClient(base_url="http://127.0.0.1:8080")
stream = await client.chat.completions.create(
    messages=[...], stream=True
)
async for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
```

---

## 3. Quantization Methods

TGI supports **7 quantization schemes**:

| Scheme | Pre-quantized weights needed? | When to use |
|--------|-------------------------------|-------------|
| **GPTQ** | Yes (or use `text-generation-server quantize`) | Best quality/performance balance |
| **AWQ** | Yes | Higher accuracy than GPTQ at same bit-width |
| **Marlin** | Yes (GPTQ weights) | Optimized GPTQ kernel, fastest throughput |
| **EXL2** | Yes | Extremely flexible quantization (variable bit-width) |
| **bitsandbytes** | No (on-the-fly) | Easy setup, slower inference |
| **EETQ** | No (on-the-fly) | Fast on-the-fly quantization |
| **FP8** | No (on-the-fly) | Native FP8 hardware (H100+) |

### On-the-fly Quantization Flags
```bash
--quantize bitsandbytes       # 8-bit
--quantize bitsandbytes-nf4   # 4-bit NormalFloat (QLoRA style)
--quantize bitsandbytes-fp4   # 4-bit Float
--quantize eetq               # Easy Efficient Quantization
--quantize fp8                # FP8 (H100+ GPUs)
```

### GPTQ Quantization Pipeline
```bash
# Quantize a model
text-generation-server quantize tiiuae/falcon-40b /data/falcon-40b-gptq
# Add --upload-to-model-id to push to Hub

# Serve with quantized weights
text-generation-launcher --model-id /data/falcon-40b-gptq/ --sharded true --num-shard 2 --quantize gptq
```

TGI's GPTQ does NOT use AutoGPTQ under the hood — it has its own kernel. But models quantized with AutoGPTQ/Optimum can still be served.

---

## 4. Speculative Decoding

TGI supports two speculation methods for 2-3x speedup (more for code):

### Medusa
- Fine-tuned LM heads added to existing models
- Predicts multiple tokens in a single forward pass
- Pre-fine-tuned Medusa heads available for popular models:
  - `text-generation-inference/gemma-7b-it-medusa`
  - `text-generation-inference/Mixtral-8x7B-Instruct-v0.1-medusa`
  - `text-generation-inference/Mistral-7B-Instruct-v0.2-medusa`
- To train custom Medusa heads: see original medusa repo + Train Medusa tutorial

### N-gram Speculation
- No fine-tuning needed
- Finds matching token sequences from previous context
- Works best for code and repetitive text
- Enable: `--speculate 2` (or higher number)

**How speculation works**: Generate tokens before the large model runs, then verify them. If guesses are correct, you get multiple tokens per LLM forward pass. Since LLMs are memory-bound (not compute-bound), this yields net speedup even with rejected guesses.

---

## 5. PagedAttention

TGI implements PagedAttention using **custom CUDA kernels from the vLLM Project**:

- KV cache partitioned into blocks accessed via lookup table
- No contiguous memory requirement — blocks allocated on demand
- Block sharing enables KV sharing across parallel sampling generations
- Memory efficiency increases GPU utilization on memory-bound workloads
- Supports larger inference batches

---

## 6. Tensor Parallelism

- Shard model across multiple GPUs
- Configured with `--num-shard N` (default: detected from available GPUs)
- Requires NCCL and `--shm-size 1g` for shared memory
- Supported on NVIDIA (CUDA 12.2+) and AMD (ROCm)

---

## 7. LoRA Serving

TGI supports serving fine-tuned LoRA adapters alongside the base model:
- Load base model + multiple LoRA adapters simultaneously
- Hot-swappable adapters without reloading the base model
- See `conceptual/lora` docs for details

---

## 8. Guidance / Structured Output

TGI supports **function calling and tool-use** via the **outlines** library:
- Force the model to generate structured outputs (JSON schemas)
- Constrained decoding within predefined output schemas
- Enables reliable tool-use patterns
- See `conceptual/guidance` for full details

---

## 9. Multi-Backend Support

Beyond NVIDIA CUDA, TGI supports:

| Backend | Image/Docs Location |
|---------|-------------------|
| **AMD GPU** (ROCm) | `using_tgi_with_amd_gpus.md` |
| **Intel Gaudi** | `backends/gaudi` |
| **AWS Trainium/Inferentia** (Neuron) | `backends/neuron` |
| **Google TPU** | via optimum-tpu |
| **Intel GPU** | `using_tgi_with_intel_gpus.md` |
| **TensorRT-LLM** | `backends/trtllm` |
| **llama.cpp** | `backends/llamacpp` |
| **CPU-only** | Remove `--gpus all`, add `--disable-custom-kernels` (poor performance) |

---

## 10. Metrics & Monitoring

### Prometheus Metrics Endpoint
```
GET /metrics
```

### Full Metrics Reference

| Metric | Type | Description |
|--------|------|-------------|
| `tgi_batch_current_max_tokens` | Gauge | Maximum tokens for current batch |
| `tgi_batch_current_size` | Gauge | Current batch size |
| `tgi_batch_decode_duration` | Histogram | Time decoding a batch (prefill/decode) |
| `tgi_batch_filter_duration` | Histogram | Time filtering + sending tokens |
| `tgi_batch_forward_duration` | Histogram | Forward pass duration per method |
| `tgi_batch_inference_count` | Counter | Inference calls per method |
| `tgi_batch_inference_duration` | Histogram | Batch inference duration |
| `tgi_batch_inference_success` | Counter | Successful inference calls |
| `tgi_batch_next_size` | Histogram | Size of next batch |
| `tgi_queue_size` | Gauge | Current request queue size |
| `tgi_request_count` | Counter | Total request count |
| `tgi_request_duration` | Histogram | End-to-end latency per request |
| `tgi_request_generated_tokens` | Histogram | Generated tokens per request |
| `tgi_request_inference_duration` | Histogram | Inference duration per request |
| `tgi_request_input_length` | Histogram | Input token length per request |
| `tgi_request_max_new_tokens` | Histogram | Max new tokens per request |
| `tgi_request_mean_time_per_token_duration` | Histogram | Inter-token latency (ITL) |
| `tgi_request_queue_duration` | Histogram | Queue wait time per request |
| `tgi_request_skipped_tokens` | Histogram | Speculated (skipped) tokens |
| `tgi_request_success` | Counter | Successful request count |
| `tgi_request_validation_duration` | Histogram | Request validation time |

Set up with: `--otlp-endpoint http://otel-collector:4318` for OpenTelemetry tracing.

---

## 11. API Surface

### Custom TGI Endpoints
- `POST /generate` — Synchronous generation
- `POST /generate_stream` — Streaming generation (SSE)

### OpenAI-Compatible Chat API
- `POST /v1/chat/completions` — Full OpenAI Messages API compatibility
- Works with `openai` Python library: `OpenAI(base_url="http://localhost:3000/v1", api_key="-")`
- Included in Inference Endpoints: `base_url = "https://<endpoint-url>/v1/"`
- Supports `stream`, `max_tokens`, `temperature`, `top_p`, `stop`, and all standard params

### SageMaker Integration
```python
from sagemaker.huggingface import HuggingFaceModel, get_huggingface_llm_image_uri

hub = {"HF_MODEL_ID": "HuggingFaceH4/zephyr-7b-beta", "SM_NUM_GPUS": "1"}
huggingface_model = HuggingFaceModel(
    image_uri=get_huggingface_llm_image_uri("huggingface", version="3.3.5"),
    env=hub,
    role=role,
)
predictor = huggingface_model.deploy(
    initial_instance_count=1,
    instance_type="ml.g5.2xlarge",
    container_startup_health_check_timeout=300,
)
```

---

## 12. CLI Flags Reference — Complete

Essential flags beyond the basic `--model-id`:

| Flag | Default | Purpose |
|------|---------|---------|
| `--model-id` | required | Model name on Hub |
| `--num-shard` | auto | GPU count for tensor parallelism |
| `--quantize` | none | Quantization: bitsandbytes, gptq, awq, eetq, marlin, fp8, bitsandbytes-nf4, bitsandbytes-fp4 |
| `--max-total-tokens` | 2048 | Max sequence length (prompt + generation) |
| `--max-batch-prefill-tokens` | 4096 | Max tokens in prefill batch |
| `--max-input-length` | 1024 | Max input prompt length |
| `--speculate` | 0 | Number of speculation tokens |
| `--draft-model-id` | none | Draft model for Medusa-style speculation |
| `--max-concurrent-requests` | 128 | Max concurrent requests (backpressure threshold) |
| `--otlp-endpoint` | none | OpenTelemetry collector endpoint |
| `--otlp-service-name` | "tgi" | Service name for tracing |
| `--host` | 0.0.0.0 | Bind address |
| `--port` | 80 | HTTP port |
| `--enable-prefill-logprobs` | false | Enable logprobs for prefill (expensive) |
| `--sharded` | false | Enable model sharding (needed with --num-shard) |

---

## 13. Supported Models & Architectures

TGI supports all major open-source LLMs including:
- Llama 3.1/3.2/3.3 (8B, 70B, 405B)
- Qwen 2.5/Qwen 3
- Mistral, Mixtral
- Gemma 2/3/4
- Falcon, BLOOM, GPT-NeoX
- StarCoder, CodeLlama
- Phi-3/Phi-4
- DeepSeek
- Many more (see supported_models docs)

**VLMs**: TGI also supports Visual Language Models for multimodal inference.

---

## 14. Key Limitations & Production Considerations

1. **Maintenance mode**: No new features planned. Use vLLM/SGLang for new projects.
2. **KV-cache contention**: Long prompts can exhaust KV-cache space — reduce `--max-total-tokens`.
3. **GPU memory**: Always set `--shm-size 1g` for NCCL multi-GPU.
4. **Logprobs impact**: Enabling `--enable-prefill-logprobs` significantly reduces max prompt size.
5. **CPU-only**: Possible but extremely poor performance — `--disable-custom-kernels`.
6. **Single custom domain per Space**: If deploying via Spaces.
7. **No auto-scaling**: Replicas must be set manually.

### Comparison: When to Use TGI vs Alternatives

| Tool | Best For |
|------|----------|
| **TGI** | Existing HF ecosystem, quick containerized serving, Inference Endpoints compatibility |
| **vLLM** | Highest throughput, new production projects, PagedAttention |
| **SGLang** | Structured generation, efficient prefix caching |
| **llama.cpp** | CPU/edge inference, local deployment, consumer GPUs |
| **MLX** | Apple Silicon optimization |

### Resources
- Docs: https://huggingface.co/docs/text-generation-inference
- GitHub: https://github.com/huggingface/text-generation-inference
- Swagger API: https://huggingface.github.io/text-generation-inference
- Supported models: https://huggingface.co/docs/text-generation-inference/supported_models
- Docker: `ghcr.io/huggingface/text-generation-inference:3.3.5`
- NPM: `@huggingface/inference` (JS client)
- Python: `huggingface_hub[inference]` (InferenceClient)
