---
name: SakThai-hf-transformers-inkling
description: ">-   Comprehensive deep-dive into Inkling (Thinking Machines Lab) — a 975B   sparse MoE multimodal model (41B active) supporting text, image, audio,   and video inputs with a 1M-token context window. Added in Transformers   5.14.0. Covers architectur"
---

# Inkling (Transformers 5.14.0+) — Comprehensive Deep-Dive

## Overview

**Inkling** is a general-purpose multimodal autoregressive transformer from
[Thinking Machines Lab](https://huggingface.co/thinkingmachines) that accepts
**text, image, audio, and video** inputs and generates text. It is a **975B
total / 41B active** sparse Mixture-of-Experts (MoE) model with a **1M-token
context window**, trained on **45 trillion tokens** of text, images, audio, and
video.

Added in **Transformers 5.14.0** (2026-07-15), PR #47347 by @molbap, @Cyrilvallez,
@eustlb, and @zucchini-nlp.

### Key Numbers

| Property | Value |
|----------|-------|
| Total parameters | 975B |
| Active parameters | 41B (per token) |
| Context length | 1,048,576 tokens (1M) |
| Layers | 66 (55 hybrid + 11 dense global) |
| Hidden size | 6,144 |
| Attention heads | 64 |
| KV heads | 8 (grouped query attention) |
| Head dim | 128 |
| Routed experts | 256 (6 active per token) |
| Shared experts | 2 (always active) |
| Vocab size | 201,024 |
| Training data | 45T tokens (text, images, audio, video) |
| License | Apache 2.0 |
| Numerics | BF16, NVFP4 |

---

## Architecture Deep-Dive

### 1. Relative Position Encoding (No RoPE)

Unlike most modern LLMs that use Rotary Position Embeddings (RoPE), Inkling uses
**learned relative attention** to encode position. Each attention layer has a
fourth projection (beyond Q, K, V) that produces a per-token, per-head **relative
feature R**. The attention logits between query at position `i` and key at
position `j` are modulated by `f(R_i - R_j, d_rel)` where `d_rel=16` and
`rel_extent=1024`.

```
logits[i][j] = (q_i · k_j) + relative_bias(R_i - R_j, i - j)
```

- `d_rel=16`: dimension of the relative position feature
- `rel_extent=1024`: maximum distance the relative bias attends to
- `log_scaling_n_floor=128000`: log-scaling floor
- `log_scaling_alpha=0.1`: log-scaling coefficient

### 2. Hybrid Attention (Global + Sliding Window)

The 66 decoder layers alternate between **global attention** (full context) and
**sliding window attention** (local context). The pattern is **5:1 sliding
window to global** — every 6th layer is global attention. This hybrid scheme
provides:

- **Efficiency**: sliding window layers scale O(n·w) vs O(n²) for global
- **Global context**: final layer and every 6th layer maintain full-context awareness

Sliding window size: **512 tokens** (`sliding_window_size=512`)
Hybrid config: 55 local (sliding window) + 11 dense (global) layers

Local layer IDs: 0,1,2,3,4,6,7,8,9,10,12,13,14,15,16,18,19,20,21,22,24,
25,26,27,28,30,31,32,33,34,36,37,38,39,40,42,43,44,45,46,48,49,50,51,52,
54,55,56,57,58,60,61,62,63,64 (55 layers)

Sliding Window Attention (SWA) has its own head config:
- `swa_head_dim=128`
- `swa_num_attention_heads=64`
- `swa_num_key_value_heads=16`

### 3. Short 1D Convolution (SConv)

Inkling uses a distinctive **short 1D convolution (SConv)** over hidden states
before each attention layer. SConv reads the current token and the previous
`W-1` hidden states, where `W` is the sliding window size (512). This helps
with local feature extraction, freeing the attention and MoE modules from
low-level local representations.

- `use_sconv=true`
- `sconv_kernel_size=4`

### 4. Mixture of Experts with Shared Expert Sink

The MoE architecture routes each token to **6 of 256 routed experts**, plus
**2 shared experts** that are always active. The shared expert "sink" means
common knowledge is handled by the always-active shared experts, while routed
experits specialize in distinct domains.

- `n_routed_experts=256`: total expert count
- `num_experts_per_tok=6`: active routed experts per token
- `n_shared_experts=2`: always-active shared experts
- `shared_expert_sink=true`: shared experts handle common knowledge
- `route_scale=8.0`: scaling factor for routing scores
- `use_gate_bias=true`: per-expert bias in router
- `gate_activation="sigmoid"`: sigmoid activation for router
- `norm_after_topk=true`: normalize routing weights after top-k selection
- `use_global_scale=true`: global scaling factor
- `dense_intermediate_size=24576`: hidden dim for dense (global) layers
- `intermediate_size=3072`: hidden dim for routed expert FFN
- `dense_mlp_idx=2`: layer index for dense MLP

### 5. Vision Encoder

The vision encoder uses a **hierarchical MLP patchifier (hMLP)** rather than a
separate ViT/SigLIP encoder. It consists of several linear layers that
progressively merge pixels until the final layer produces one embedding per
patch. An additional **temporal dimension** supports video processing.

- `vision_encoder_type="hmlp"`
- `patch_size=40`
- `temporal_patch_size=2` (video capable)
- `n_layers=4`
- `n_channels=3`
- `decoder_dmodel=6144` (projects to model hidden dim)
- `use_vision_norm=true`

### 6. Audio Encoder

Audio uses a **discretized mel spectrogram** approach. Each 100ms audio chunk
is converted to the mel scale (80 bins) and classified into one of 16 discrete
mel bins. The mel bin values are embedded and summed to produce the audio input.

- `audio_mode="dmel"` (delta-mel spectrogram)
- `n_mel_bins=80`
- `mel_vocab_size=16` (16 discrete bins)
- `dmel_min=-7.0`
- `dmel_max=2.0`
- `decoder_dmodel=6144`
- `bias=false`
- `use_audio_norm=true`

### 7. Multi-Token Prediction (MTP) for Speculative Decoding

Inkling includes **deep MTP** — 8 additional transformer blocks that predict
future tokens and serve as **drafters for speculative decoding**. This enables
faster inference without quality loss.

- `num_nextn_predict_layers=8` (8 future tokens)
- `chain_hidden_post_norm=false`
- Local layer IDs for MTP: 0,2,4,5,6,7 (6 of 8 are hybrid/sliding window)

---

## Chat Template

Inkling uses a sophisticated Jinja chat template with:

- **Role tokens**: `<|message_user|>`, `<|message_model|>`, `<|message_system|>`,
  `<|message_tool|>`
- **Content markers**: `<|content_text|>`, `<|content_xml|>`
- **Reasoning effort**: `reasoning_effort` parameter with values:
  `"none"` (0.0), `"minimal"` (0.1), `"low"` (0.2), `"medium"` (0.7),
  `"high"` (0.9), `"xhigh"`, `"max"` (0.99)
- **Tool support**: `tool_declare` system message with XML-encoded tool specs
- **Response format**: Structured output with `<|message_model|>`,
  `<|content_text|>`, and optional tool call markers

---

## Inference

### Hardware Requirements

| Checkpoint | Precision | VRAM Required | GPU |
|-----------|-----------|--------------|-----|
| `thinkingmachines/Inkling` | BF16 | ~2 TB | 8×H100 (or multi-node) |
| `thinkingmachines/Inkling-NVFP4` | NVFP4 | ~600 GB | Blackwell GPUs |
| `unsloth/inkling-GGUF` | 1-bit GGUF | ~30-100 GB | Consumer GPUs |

### Transformers Pipeline (Recommended for Testing)

```python
from transformers import pipeline

# Requires transformers >=5.14.0
pipe = pipeline("image-text-to-text", model="thinkingmachines/Inkling-NVFP4")

messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "https://example.com/image.jpg"},
            {"type": "text", "text": "Describe this image."},
        ],
    },
]
output = pipe(
    messages,
    max_new_tokens=2000,
    return_full_text=False,
    reasoning_effort="medium",
)
```

### Auto Classes

```python
from transformers import AutoModelForMultimodalLM, AutoProcessor

model_id = "thinkingmachines/Inkling-NVFP4"
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForMultimodalLM.from_pretrained(
    model_id,
    device_map="auto",
)

messages = [
    {"role": "user", "content": "What is 17 × 23?"},
]
inputs = processor.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
    reasoning_effort="high",
).to(model.device)

output = model.generate(**inputs, max_new_tokens=2000)
response = processor.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=False)
processor.parse_response(response)
```

### Audio Inference

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "Transcribe this audio."},
            {"type": "audio", "audio": "speech.mp3"},
        ],
    },
]
inputs = processor.apply_chat_template(
    messages, tokenize=True, return_tensors="pt",
    add_generation_prompt=True,
).to(model.device)
outputs = model.generate(**inputs, max_new_tokens=512)
```

### MTP Speculative Decoding

```python
generated = model.generate(
    **inputs,
    max_new_tokens=1000,
    do_sample=False,
    use_mtp=True,  # Enable MTP speculative decoding
)
```

### Serving with transformers serve

```bash
transformers serve thinkingmachines/Inkling-NVFP4
```

Then consume via OpenAI-compatible API:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="any")
completion = client.chat.completions.create(
    model="thinkingmachines/Inkling-NVFP4",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### SGLang

```bash
python3 -m sglang.launch_server \
    --model-path thinkingmachines/Inkling \
    --tp-size 8 \
    --host 0.0.0.0 --port 30000
```

### vLLM

```bash
vllm serve thinkingmachines/Inkling-NVFP4 \
    --trust-remote-code \
    --tokenizer-mode inkling \
    --tensor-parallel-size 8 \
    --enable-auto-tool-choice \
    --tool-call-parser inkling \
    --reasoning-parser inkling
```

### llama.cpp (Local — Zero-Cost for GGUF)

```bash
llama serve -hf unsloth/inkling-GGUF:UD-IQ1_S
```

### HF Inference Providers (Zero-Cost for Limited Usage)

```python
from openai import OpenAI
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
)
completion = client.chat.completions.create(
    model="thinkingmachines/Inkling:auto",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

Suffix `:auto` routes to your preferred provider, `:cheapest` or `:fastest` also
available.

---

## Evaluation Results

Reported at reasoning effort=0.99 (2026-07-14). Compared against open-weights
and closed-weights models.

### Reasoning

| Benchmark | Inkling | Nemotron 3 Ultra | DeepSeek V4 Pro | Gemini 3.1 Pro |
|-----------|---------|------------------|-----------------|-----------------|
| HLE (text) | 29.7% | 26.6% | 35.9% | 44.7% |
| HLE (w/ tools) | 46.0% | 37.4% | 48.2% | 51.4% |
| AIME 2026 | **97.1%** | 94.2% | 96.7% | 98.3% |
| GPQA Diamond | 87.2% | 86.7% | 88.8% | 94.1% |

### Agentic (Coding)

| Benchmark | Inkling | Nemotron 3 Ultra | DeepSeek V4 Pro |
|-----------|---------|------------------|-----------------|
| SWEBench Verified | **77.6%** | 70.7% | 80.6% |
| SWEBench Pro | 54.3% | 46.4% | 55.4% |
| Terminal Bench 2.1 | **63.8** | 56.4 | 64.0 |

### Vision

| Benchmark | Inkling |
|-----------|---------|
| MMMU Pro (Standard 10) | 73.3% |
| Charxiv RQ | 78.1% |
| Charxiv RQ (w/ python) | 82.0% |

### Audio

| Benchmark | Inkling |
|-----------|---------|
| Audio MC | 56.6% |
| MMAU | 77.2% |
| VoiceBench | 91.4% |

---

## Zero-Cost Strategies

| Strategy | Cost | Notes |
|----------|------|-------|
| Inference Providers (serverless) | Free with HF token | Rate-limited, but free |
| llama.cpp GGUF (local) | Free | Needs ~30-100GB VRAM/quant |
| `transformers serve` | Free (local) | Needs multi-GPU for full model |
| HF `any-to-any` pipeline | Free (local) | Same hardware requirements |
| **Full BF16 model** | 💰 Requires 2TB+ VRAM | Multi-node H100 cluster |

---

## Sources

- https://huggingface.co/thinkingmachines/Inkling — Official model
- https://huggingface.co/docs/transformers/main/en/model_doc/inkling — Transformers docs
- https://huggingface.co/blog/thinkingmachines-inkling — Official HF blog post
- https://github.com/huggingface/transformers/pull/47347 — PR #47347
- https://huggingface.co/thinkingmachines/Inkling-NVFP4 — NVFP4 quantized variant

## See Also

- `hf-transformers-moe-deep-dive` — General MoE architecture reference
- `hf-transformers-speculative-decoding-deep-dive` — Speculative decoding patterns
- `hf-transformers-deepseek-v4-deep-dive` — Comparable MoE model architecture
- `hf-inference-providers-comprehensive-architecture` — Serverless inference routing
- `hf-inference-providers-responses-api-deep-dive` — Inference API patterns
