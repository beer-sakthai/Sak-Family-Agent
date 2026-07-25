---
name: hf-transformers-cache-api-deep-dive
author: SakThai
license: MIT
description: "A skill for Hf Transformers Cache Api Deep Dive."
version: 0.1.0
---

# Transformers Cache API: DynamicCache, StaticCache, QuantizedCache & More

**author:** SakThai
**license:** MIT

## Summary

Complete reference for the Hugging Face Transformers cache system (v4.47+). Covers all cache classes — `DynamicCache`, `StaticCache`, `QuantizedCache`, `EncoderDecoderCache` — the layer-level architecture, and how to configure caching via `model.generate()` using `cache_implementation` and `cache_config`.

The cache system was completely revamped in Transformers v4.47. Instead of the old `past_key_values` tuple-of-tuples, the library now uses proper class-based caches with unified interfaces, support for `torch.compile`, sliding window, CPU offloading, and KV cache quantization.

## Core Concepts

### What is a KV Cache?

During autoregressive generation, each new token's attention attends to all previous tokens. Without caching, this means recomputing all previous key (K) and value (V) tensors for every new token — O(n²) compute. The KV cache stores these tensors from previous forward passes, reducing per-step cost to O(n).

The cache stores per-layer key/value tensors of shape `[batch_size, num_heads, seq_len, head_dim]`.

### Cache Architecture

```
model.past_key_values (one of the Cache classes below)
 ├── layers: list[CacheLayer]  ← one per transformer layer
 │    ├── keys: Tensor [batch, num_heads, seq_len, head_dim]
 │    └── values: Tensor [batch, num_heads, seq_len, head_dim]
 └── methods: update(), get_seq_length(), get_max_length(), reset(), reorder_cache()
```

Each `CacheLayer` can be:
- **`DynamicLayer`** — grows as tokens are added (default)
- **`StaticLayer`** — fixed pre-allocated buffer (for `torch.compile`)
- **`DynamicSlidingWindowLayer`** / **`StaticSlidingWindowLayer`** — sliding window attention
- **`QuantizedLayer`** — quantized K/V storage (KIVI-style)
- **`LinearAttentionLayer`** — recurrent/convolutional state (Mamba, etc.)
- **Hybrid layers** — combinations of linear + attention (e.g. `LinearAttentionAndFullAttentionLayer`)

## Cache Classes

### DynamicCache (default)

**Purpose:** Grows dynamically as tokens are generated. This is the default cache for all generative models.

**Key features:**
- Appends new K/V tensors via `torch.cat` on the seq_len dimension
- Supports sliding window — if `config.sliding_window` is set, only the last `sliding_window` tokens are kept
- Supports optional CPU offloading with `offloading=True`
- Supports hybrid cache structures automatically from model config

**Usage:**
```python
from transformers import DynamicCache

# Default -- no explicit config needed
past_key_values = DynamicCache()

# With sliding window from model config
past_key_values = DynamicCache(config=model.config)

# With CPU offloading for memory-constrained GPUs
past_key_values = DynamicCache(offloading=True)
past_key_values = DynamicCache(config=model.config, offloading=True, offload_only_non_sliding=True)
```

**When to use:** Always the safe default. Ideal for most use cases where you don't need `torch.compile`.

### StaticCache

**Purpose:** Pre-allocated, fixed-size cache for use with `torch.compile()` and `torch.export()`. The cache buffer is allocated once and mutated in-place, which is required for graph compilation.

**Key features:**
- Pre-allocates tensors of shape `[batch_size, num_heads, max_cache_len, head_dim]`
- Mutates tensors in-place instead of concatenating
- Supports sliding window and hybrid layers
- Supports CPU offloading
- Compatible with `torch.compile` and `torch.export()`

**Usage:**
```python
from transformers import StaticCache

# Allocate cache for 2048 total tokens
past_key_values = StaticCache(
    config=model.config,
    max_cache_len=2048
)

# With CPU offloading
past_key_values = StaticCache(
    config=model.config,
    max_cache_len=2048,
    offloading=True,
    offload_only_non_sliding=True
)
```

**When to use:** When using `torch.compile(model)` for accelerated inference. Must know the maximum generation length ahead of time.

### QuantizedCache

**Purpose:** Reduces memory usage of the KV cache by quantizing keys and values, based on the [KIVI paper](https://huggingface.co/papers/2402.02750). Uses a hybrid storage: a small residual buffer in original precision + a larger quantized buffer.

**Key features:**
- Two storage tiers: original precision (residual) + quantized
- Per-channel quantization with configurable group size
- Two backends: Quanto (`"quanto"`) and HQQ (`"hqq"`)
- When the residual buffer exceeds `residual_length`, it is quantized and moved

**Parameters:**
| Param | Default | Description |
|-------|---------|-------------|
| `backend` | *required* | `"quanto"` or `"hqq"` |
| `nbits` | 4 | Bits per element (2 or 4) |
| `axis_key` | 0 | Quantization axis for keys |
| `axis_value` | 0 | Quantization axis for values |
| `q_group_size` | 64 | Group size for per-channel quantization |
| `residual_length` | 128 | Max length before quantizing |

**Usage:**
```python
from transformers import QuantizedCache

# 4-bit KV cache with Quanto backend
past_key_values = QuantizedCache(
    backend="quanto",
    nbits=4,
    q_group_size=64,
    residual_length=128
)
```

**When to use:** When generating very long sequences (e.g. 32K+ tokens) on memory-constrained hardware. Note: requires `quanto` or `hqq` library installed.

### EncoderDecoderCache

**Purpose:** Holds both self-attention and cross-attention caches for encoder-decoder models (e.g. Whisper, T5, BART).

**Usage:**
```python
from transformers import DynamicCache, EncoderDecoderCache

self_attention_cache = DynamicCache(config=model.config)
cross_attention_cache = DynamicCache(config=model.config)
past_key_values = EncoderDecoderCache(self_attention_cache, cross_attention_cache)
```

### MtpCache

**Purpose:** Multi-Token Prediction cache, used by models with MTP heads like DeepSeek V3/V4. Holds draft token key/value states for speculative decoding-style MTP.

## User-Facing API: `cache_implementation`

The simplest way to configure caching is through `GenerationConfig` or directly in `model.generate()` using the `cache_implementation` string.

### Valid Values

| Value | Cache Class | Description |
|-------|------------|-------------|
| `"dynamic"` | `DynamicCache()` | Default. Grows dynamically |
| `"static"` | `StaticCache(...)` | Pre-allocated, for `torch.compile` |
| `"offloaded"` | `DynamicCache(offloading=True)` | Dynamic with CPU offloading |
| `"offloaded_static"` | `StaticCache(offloading=True)` | Static with CPU offloading |
| `"quantized"` | `QuantizedCache(...)` | Quantized KV cache (KIVI) |

### Via `model.generate()`

```python
# Default (dynamic)
outputs = model.generate(input_ids, max_new_tokens=100)

# Static cache for compiled model
outputs = model.generate(
    input_ids,
    max_new_tokens=100,
    cache_implementation="static",
    max_cache_len=512,
)

# With quantized cache
outputs = model.generate(
    input_ids,
    max_new_tokens=100,
    cache_implementation="quantized",
    cache_config={"backend": "quanto", "nbits": 4},
)

# CPU offloading
outputs = model.generate(
    input_ids,
    max_new_tokens=100,
    cache_implementation="offloaded",
)
```

### Via `GenerationConfig`

```python
from transformers import GenerationConfig

gen_config = GenerationConfig(
    max_new_tokens=100,
    cache_implementation="static",
    max_cache_len=512,
)
outputs = model.generate(input_ids, generation_config=gen_config)
```

### Direct Cache Instantiation

For manual generation loops (e.g. streaming, custom stopping criteria):

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, DynamicCache

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2-0.5B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2-0.5B-Instruct")

inputs = tokenizer("Hello, my name is", return_tensors="pt")

# Prepare cache
past_key_values = DynamicCache(config=model.config)

# Manual generation loop
for _ in range(50):
    outputs = model(**inputs, past_key_values=past_key_values, use_cache=True)
    next_token = outputs.logits[:, -1, :].argmax(dim=-1, keepdim=True)
    inputs = {"input_ids": next_token, "attention_mask": torch.ones_like(next_token)}
    past_key_values = outputs.past_key_values
    
    if next_token.item() == tokenizer.eos_token_id:
        break
```

## Layer-Level Architecture (Advanced)

### CacheLayer Types

The library dynamically selects the correct `CacheLayer` type per model layer based on `config.layer_type`:

| `layer_type` | CacheLayer class | Behavior |
|-------------|-----------------|----------|
| `"full_attention"` | `DynamicLayer` | Full attention, dynamic growth |
| `"sliding_attention"` | `DynamicSlidingWindowLayer` | Sliding window, keeps last N tokens |
| `"chunked_attention"` | `DynamicSlidingWindowLayer` | Same as sliding (chunked mask differs) |
| `"linear_attention"` | `LinearAttentionLayer` | Recurrent/SSM state (no KV dim) |
| `"conv"` | `LinearAttentionLayer` | Conv state buffer |
| `"moe"` | `LinearAttentionLayer` | MoE routing state |
| `"hybrid"` | `LinearAttentionAndFullAttentionLayer` | Both linear + attention |
| `"hybrid_sliding"` | `LinearAttentionAndSlidingWindowAttentionLayer` | Linear + sliding attention |

For static caches, analogous classes exist: `StaticLayer`, `StaticSlidingWindowLayer`, `StaticIndexedLayer`, etc.

### Key Methods on CacheLayer

| Method | Description |
|--------|-------------|
| `update(key_states, value_states)` | Add new tokens to cache, return updated K,V in-place |
| `get_seq_length()` | Current sequence length |
| `get_max_length()` | Maximum capacity (-1 = unlimited for dynamic) |
| `reset()` | Zero all cached values |
| `reorder_cache(beam_idx)` | Reorder for beam search by index |
| `crop(max_length)` | Truncate to max_length |
| `is_compileable` | Whether layer supports `torch.compile` |

## Performance Considerations

| Cache Type | Memory | Speed | Use Case |
|-----------|--------|-------|----------|
| `DynamicCache` | Higher (unbounded growth) | Fast (cat operation) | General use, short sequences |
| `DynamicCache + offloading` | Lower (CPU offload) | Slower (PCIe transfer) | GPU memory constrained |
| `StaticCache` | Fixed (pre-allocated) | Fastest (in-place, compile) | `torch.compile`, production |
| `QuantizedCache` | Lowest (4-bit K,V) | Medium (quantize/dequantize) | Very long sequences |
| `SlidingWindow` | Bounded | Fast | Streaming, fixed window |

### Memory Formula

For `DynamicCache` with sequence length `L`:
```
Memory per layer = 2 × batch_size × num_heads × L × head_dim × dtype_bytes
Total memory = layers × Memory_per_layer
```

For `StaticCache` with `max_cache_len = M`:
```
Memory per layer = 2 × batch_size × num_heads × M × head_dim × dtype_bytes
```
(Pre-allocated, does not grow)

For `QuantizedCache` with `nbits = B`:
```
Memory per layer ≈ 2 × batch_size × num_heads × L × head_dim × (B/8 + residual_factor)
```

## Practical Recipes

### Recipe 1: Max throughput with torch.compile
```python
model = AutoModelForCausalLM.from_pretrained("model-name", torch_dtype=torch.bfloat16)
model = torch.compile(model, mode="reduce-overhead")
outputs = model.generate(..., cache_implementation="static", max_cache_len=2048)
```

### Recipe 2: Long context with quantized cache
```python
outputs = model.generate(
    input_ids,
    max_new_tokens=32768,
    cache_implementation="quantized",
    cache_config={"backend": "quanto", "nbits": 4, "residual_length": 64},
)
```

### Recipe 3: Memory-constrained GPU
```python
outputs = model.generate(
    input_ids,
    max_new_tokens=2048,
    cache_implementation="offloaded",
)
```

### Recipe 4: Streaming with custom cache
```python
past_key_values = DynamicCache(offloading=True)
for token_id in stream_tokens():
    outputs = model(input_ids=token_id, past_key_values=past_key_values, use_cache=True)
    yield decode(outputs.logits)
    past_key_values = outputs.past_key_values
```

## Key Takeaways

1. **Default is `DynamicCache`** — no need to configure anything for normal use
2. **Use `"static"`** when you want `torch.compile` speedups
3. **Use `"quantized"`** for very long contexts (requires `quanto` or `hqq`)
4. **Use `"offloaded"`** when GPU memory is tight
5. **Pass `cache_config` dict** for advanced parameters (backend, bits, etc.)
6. **Pre-`generate()` caching** only works if the cache type is compatible — static caches require `max_cache_len`
7. **All cache classes** support `reset()` to reuse without reallocation
8. **Sliding window** is configured in the model config, not the cache — the cache adapts automatically
