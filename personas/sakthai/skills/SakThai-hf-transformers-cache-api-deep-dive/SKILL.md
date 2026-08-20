---
name: SakThai-hf-transformers-cache-api-deep-dive
description: ">-   Complete deep-dive into the Transformers modern cache system — DynamicCache,   StaticCache, QuantizedCache, EncoderDecoderCache, prefix/prefill caching,   iterative generation, CPU offloading, and the cache_implementation API.   Covers v4.47+ wi"
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

## Iterative Generation with Cache (Chatbots)

For back-and-forth conversation, a cache eliminates recomputing the entire context at each turn. Initialize an empty cache once, then feed new prompts:

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, DynamicCache

model_id = "meta-llama/Llama-2-7b-chat-hf"
model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.bfloat16, device_map='auto')
tokenizer = AutoTokenizer.from_pretrained(model_id)

user_prompts = ["Hello, what's your name?", "Btw, yesterday I was on a rock concert."]
past_key_values = DynamicCache(config=model.config)

messages = []
for prompt in user_prompts:
    messages.append({"role": "user", "content": prompt})
    inputs = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt", return_dict=True
    ).to(model.device)
    input_length = inputs["input_ids"].shape[1]
    outputs = model.generate(**inputs, do_sample=False, max_new_tokens=256,
                             past_key_values=past_key_values)
    completion = tokenizer.decode(outputs[0, input_length:], skip_special_tokens=True)
    messages.append({"role": "assistant", "content": completion})
```

> [!WARNING]
> Some models use special `<think>...</think>` reasoning tokens that may be lost during re-encoding. You might need to manually adjust extra tokens from completions to keep things stable.

## Prefix Caching (Prefill a Cache)

Cache a common prefix prompt once and reuse it to generate multiple different continuations — ideal for "system prompt + user query" patterns:

```python
import copy
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, StaticCache

model_id = "meta-llama/Llama-2-7b-chat-hf"
model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.bfloat16, device_map={"": 0})
tokenizer = AutoTokenizer.from_pretrained(model_id)

# Pre-allocate StaticCache with large enough max_cache_len
prompt_cache = StaticCache(config=model.config, max_cache_len=1024)

INITIAL_PROMPT = "You are a helpful assistant. "
inputs = tokenizer(INITIAL_PROMPT, return_tensors="pt").to(model.device.type)
with torch.no_grad():
    prompt_cache = model(**inputs, past_key_values=prompt_cache).past_key_values

# Reuse cached prefix for different queries
prompts = ["Help me write a blogpost about travelling.", "What is the capital of France?"]
for prompt in prompts:
    new_inputs = tokenizer(INITIAL_PROMPT + prompt, return_tensors="pt").to(model.device.type)
    past_key_values = copy.deepcopy(prompt_cache)
    outputs = model.generate(**new_inputs, past_key_values=past_key_values, max_new_tokens=20)
    print(tokenizer.batch_decode(outputs)[0])
```

## CPU Tensor Bookkeeping for Compiled Inference

On Neuron/TPU-like backends, keeping generation bookkeeping tensors on CPU avoids compiler retracing:

```python
# Leave inputs on CPU — only forward inputs move to model device
inputs = tokenizer("The French Bread Law states", return_tensors="pt")  # NOT .to(model.device)
output = model.generate(**inputs, do_sample=False, max_new_tokens=20)
# output is on CPU (follows input device)
```

## OOM-Resilient Generation

Automatic fallback to offloaded cache on out-of-memory:

```python
def resilient_generate(model, *args, **kwargs):
    try:
        return model.generate(*args, **kwargs)
    except torch.OutOfMemoryError:
        print("OOM — retrying with cache_implementation='offloaded'")
        torch.cuda.empty_cache()
        kwargs["cache_implementation"] = "offloaded"
        return model.generate(*args, **kwargs)
```

## Manual Generation Loop with Cache

Using DynamicCache directly in a custom loop with proper attention mask handling:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, DynamicCache
from accelerate import Accelerator

device = Accelerator().device
model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.bfloat16, device_map=device)
tokenizer = AutoTokenizer.from_pretrained(model_id)

past_key_values = DynamicCache(config=model.config)
messages = [{"role": "user", "content": "Hello, what's your name."}]
inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True,
                                       return_tensors="pt", return_dict=True).to(model.device)

generated_ids = inputs.input_ids
for _ in range(10):
    outputs = model(**inputs, past_key_values=past_key_values, use_cache=True)
    next_token_ids = outputs.logits[:, -1:].argmax(-1)
    generated_ids = torch.cat([generated_ids, next_token_ids], dim=-1)
    # Extend attention mask for the new token
    attention_mask = torch.cat([inputs["attention_mask"],
                                inputs["attention_mask"].new_ones((1, 1))], dim=-1)
    inputs = {"input_ids": next_token_ids, "attention_mask": attention_mask}
```

## Quantized Cache Backend Recommendations (v5.14.0+)

| Backend | Supported Bitwidths | Recommended axis-key/axis-value |
|---------|-------------------|-------------------------------|
| **HQQ** | int2, int4, int8  | `1` |
| **Quanto** (default) | int2, int4 | `0` |

```python
# HQQ backend (int4)
out = model.generate(..., cache_implementation="quantized",
                     cache_config={"backend": "hqq"})

# Quanto backend (int4, explicit)
out = model.generate(..., cache_implementation="quantized",
                     cache_config={"backend": "quanto", "nbits": 4})
```

## Comparison Table (Updated v5.14.0)

| Cache Type | Sliding Layers | Offloading | torch.compile() | Memory |
|------------|:-------------:|:----------:|:---------------:|:------:|
| DynamicCache | ✅ | ✅ | ❌ | Medium |
| StaticCache | ✅ | ✅ | ✅ | High (fixed) |
| QuantizedCache | ❌ | ❌ | ❌ | Low |

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

### Recipe 5: Prefix caching for multi-query system prompt
```python
# See "Prefix Caching" section for full example
prompt_cache = StaticCache(config=model.config, max_cache_len=2048)
with torch.no_grad():
    prompt_cache = model(**prefix_inputs, past_key_values=prompt_cache).past_key_values
# Then deepcopy + reuse for each user query
```

### Recipe 6: OOM-resilient generation
```python
outputs = resilient_generate(model, **inputs, max_new_tokens=4096, num_beams=4)
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
