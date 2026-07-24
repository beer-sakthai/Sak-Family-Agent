# HF Learnings Log

## 2026-07-24: hf-transformers-cache-hierarchy-deep-dive

### Summary
Comprehensive deep-dive into the Transformers KV cache class hierarchy (`cache_utils.py`, ~2056 lines in main). The cache system underwent a major refactor from simple `past_key_values` tuples to a full class hierarchy with polymorphic layer types and pluggable backends. Covers the complete `Cache` container hierarchy (DynamicCache, StaticCache, QuantizedCache, EncoderDecoderCache, MtpCache), the `CacheLayerMixin` layer hierarchy (dynamic, static, sliding window, quantized, linear attention, hybrid), the `cache_implementation` parameter in `generate()` for selecting cache strategies at runtime, and the offloading infrastructure for GPU memory savings.

### Key Concepts

**Architecture overview:** The cache system has two levels:
1. **Cache layers** (`CacheLayerMixin`) — one per model layer, storing that layer's key/value states
2. **Cache containers** (`Cache`) — a list of `CacheLayerMixin` objects, providing the user-facing API

### Layer Class Hierarchy

```
CacheLayerMixin (ABC)
├── DynamicLayer                    — Grows dynamically via torch.cat (default)
│   ├── DynamicSlidingWindowLayer   — Caps at sliding_window size, then evicts oldest
│   ├── DynamicIndexedLayer         — Extra indexer cache for DeepSeek sparse attention
│   └── QuantizedLayer              — KIVI-style quantized KV cache
│       ├── QuantoQuantizedLayer    — Uses Optimum Quanto as backend
│       └── HQQQuantizedLayer       — Uses HQQ as backend
├── StaticLayer                     — Pre-allocated static tensor (for torch.compile/export)
│   ├── StaticSlidingWindowLayer    — Static version with sliding window
│   └── StaticIndexedLayer          — Static version with sparse attention indexer
└── LinearAttentionCacheLayerMixin (ABC)
    ├── LinearAttentionLayer        — Stores recurrent/conv states (Mamba, linear attention)
    ├── LinearAttentionAndFullAttentionLayer    — Hybrid: both linear + dynamic attention
    └── LinearAttentionAndSlidingWindowLayer    — Hybrid: linear + sliding window
```

**Layer type dispatch:** The `DYNAMIC_LAYER_TYPE_MAPPING` and `STATIC_LAYER_TYPE_MAPPING` dicts map config string identifiers to layer classes:

| Config Type | Dynamic Layer | Static Layer |
|---|---|---|
| `"full_attention"` | `DynamicLayer` | `StaticLayer` |
| `"sliding_attention"` | `DynamicSlidingWindowLayer` | `StaticSlidingWindowLayer` |
| `"chunked_attention"` | `DynamicSlidingWindowLayer` | `StaticSlidingWindowLayer` |
| `"conv"` / `"moe"` / `"linear_attention"` | `LinearAttentionLayer` | `LinearAttentionLayer` |
| `"hybrid"` | `LinearAttentionAndFullAttentionLayer` | `LinearAttentionAndStaticFullAttentionLayer` |
| `"hybrid_sliding"` | `LinearAttentionAndSlidingWindowAttentionLayer` | `LinearAttentionAndStaticSlidingWindowAttentionLayer` |
| `"deepseek_sparse_attention"` | `DynamicIndexedLayer` | `StaticIndexedLayer` |

Models declare per-layer types via `config.layer_types`. If absent, it's inferred from config fields like `sliding_window` or `attention_chunk_size`.

### Cache Container Classes

**`Cache`** (base, line 1218): Container holding a list of `CacheLayerMixin` objects. Provides:
- `update(key_states, value_states, layer_idx)` — updates a specific layer's cache
- `update_conv_state()` / `update_recurrent_state()` — for linear attention layers
- `offload(layer_idx)` / `prefetch(layer_idx)` — GPU↔CPU offloading
- `get_seq_length(layer_idx)` / `get_max_length(layer_idx)`
- `reset()` — zero out all cache values
- `reorder_cache(beam_idx)` — beam search reordering
- `crop(max_length)` / `batch_repeat_interleave()` / `batch_select_indices()` — advanced operations
- Offloading support via `torch.Stream()` with optional `only_non_sliding` flag

**`DynamicCache(Cache)`** (line 1681): Default cache for generative models.
- Accepts optional `config` to auto-detect sliding/hybrid structure (reduces memory from `[batch, heads, seq_len, head_dim]` to `[batch, heads, min(seq_len, sliding_window), head_dim]`)
- Accepts `ddp_cache_data` for distributed data-parallel compatibility
- Accepts `offloading=True` and `offload_only_non_sliding=True` for GPU memory management
- If no config or DDP data, lazily creates `DynamicLayer` instances on first call
- Iterating over it yields `(keys, values, sliding_window_tensor)` tuples

**`StaticCache(Cache)`** (line 1773): Pre-allocated static tensor cache.
- Required for `torch.compile(model)` and `torch.export()`
- Requires both `config` and `max_cache_len` at construction
- Pre-allocates contiguous tensors of shape `[batch, heads, max_cache_len, head_dim]` — eliminates reallocation overhead
- The `max_cache_len` is set once, and repeated `generate()` calls reuse the same allocation
- `offload_only_non_sliding` defaults to `True` (sliding layers are small, no need to offload)

**`QuantizedCache(Cache)`** (line 1828): KIVI-paper-style quantized KV cache.
- Two-tier storage: original precision (residual) + quantized cache
- When `residual_length` (default 128) is exceeded, older entries are quantized into the compressed cache
- Per-channel quantization with configurable `q_group_size` (default 64)
- Two backends: `"quanto"` (via Optimum Quanto) and `"hqq"` (via HQQ)
- `nbits` defaults to 4, `axis_key` and `axis_value` default to 0
- Only supports `full_attention` layers (validated at init)
- Enables much longer generation without OOM at modest quality cost

**`EncoderDecoderCache(Cache)`** (line 1891): For encoder-decoder models (Whisper, T5, etc.).
- Holds two inner `Cache` objects: `self_attention_cache` and `cross_attention_cache`
- Supports DDP init and manual init with two Cache objects
- `is_updated` tracks which cross-attention layers have been populated (useful for cross-attention masking)
- Deprecated alias: `SlidingWindowCache` was removed in favor of `StaticCache`

**`MtpCache(DynamicCache)`** (line 2047): For Multi-Token Prediction (MTP) models.
- Extends `DynamicCache` with query offset logic: queries for MTP depth `k` run `k+1` tokens ahead
- `get_query_offset(layer_idx)` adds the MTP offset to the superclass's calculation
- `get_mask_sizes()` adjusts mask offsets accordingly

### `cache_implementation` in `generate()`

The `generate()` method's `cache_implementation` parameter maps to concrete cache classes:

| Value | Class Instantiated | Best For |
|---|---|---|
| `"dynamic"` (default) | `DynamicCache()` | General use, unknown sequence length |
| `"static"` | `StaticCache(config, max_cache_len)` | torch.compile, torch.export, fixed-length generation |
| `"offloaded"` | `DynamicCache(offloading=True)` | GPU memory constrained, dynamic lengths |
| `"offloaded_static"` | `StaticCache(..., offloading=True)` | GPU memory constrained, fixed lengths |
| `"quantized"` | `QuantizedCache("quanto"/"hqq", config)` | Long generation, memory critical |

Additional parameters passed via `cache_config` dict (e.g., `{"nbits": 2, "residual_length": 64}` for QuantizedCache).

The `max_cache_len` parameter is used only with static caches to pre-size the allocation.

### Offloading Infrastructure

When `offloading=True`:
- After each layer's `update()`, the layer is moved to CPU via `offload(layer_idx)`
- Before the next layer's `update()`, a prefetch stream loads the following layer back to GPU (`prefetch(layer_idx + 1)`)
- Uses a separate `torch.Stream()` (or `torch.cuda.Stream()` pre-2.7) for non-blocking transfers
- `only_non_sliding=True` (default for StaticCache) keeps sliding layers resident on GPU since they're small
- The prefetch/search loops back to the beginning when the next offloaded layer is not found

### Hardware Assumptions

- CUDA-based GPU offloading (uses `torch.cuda` APIs for streams and default-stream management)
- `QuantizedCache` requires either `optimum-quanto` or `hqq` package installed
- `StaticCache` is designed for CUDA graphs and `torch.compile` compatibility
- `LinearAttentionCacheLayerMixin` layers are never offloaded (recurrent state is small)

### Resources
- Source: `transformers/src/transformers/cache_utils.py` (~2056 lines, main branch)
- Docs: https://huggingface.co/docs/transformers/main/en/main_classes/text_generation (cache_implementation parameter)
- Tutorial: https://huggingface.co/docs/transformers/main/en/llm_tutorial_optimization (KV cache walkthrough)
- KIVI paper: https://huggingface.co/papers/2402.02750 (quantized KV cache)
- Multi-Query Attention paper: https://huggingface.co/papers/1911.02150
- Grouped-Query Attention paper: https://huggingface.co/papers/2305.13245

---

