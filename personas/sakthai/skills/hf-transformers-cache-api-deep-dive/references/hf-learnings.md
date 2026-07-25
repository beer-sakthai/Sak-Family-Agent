# HF Learnings Log

## 2026-07-25: hf-transformers-cache-api-deep-dive — Transformers Modern Cache API: DynamicCache, StaticCache, QuantizedCache & friends (Topic #392)

### Summary
Comprehensive deep dive into the revamped Hugging Face Transformers cache system (v4.47+). The old `past_key_values` tuple-of-tuples has been replaced with proper class-based caches — `DynamicCache`, `StaticCache`, `QuantizedCache`, `EncoderDecoderCache`, and `MtpCache` — each with a unified interface. The user-facing API exposes these through `cache_implementation` string values in `model.generate()` / `GenerationConfig`.

### Key Findings

#### Cache Classes
- **DynamicCache** — default, grows dynamically via `torch.cat`. Supports sliding window, hybrid layers, CPU offloading
- **StaticCache** — pre-allocated fixed buffer for `torch.compile()` / `torch.export()`. Requires `max_cache_len` upfront
- **QuantizedCache** — KIVI-style 2/4-bit KV cache quantization. Two backends: `"quanto"` and `"hqq"`
- **EncoderDecoderCache** — holds self + cross attention caches for encoder-decoder models
- **MtpCache** — multi-token prediction cache (DeepSeek V3/V4)

#### User-Facing API
Set `cache_implementation` to one of: `"dynamic"`, `"static"`, `"offloaded"` (DynamicCache CPU offload), `"offloaded_static"` (StaticCache CPU offload), `"quantized"`
Additional params: `cache_config` (dict for advanced options), `max_cache_len` (for static caches only)

#### Layer-Level Architecture
Each Cache contains a list of `CacheLayer` objects, one per model layer. Layer types map automatically from `config.layer_type`:
- `"full_attention"` → `DynamicLayer`
- `"sliding_attention"` → `DynamicSlidingWindowLayer`
- `"linear_attention"` → `LinearAttentionLayer` (recurrent/SSM, no KV dim)
- `"hybrid"` → `LinearAttentionAndFullAttentionLayer`
- Static equivalents exist for torch.compile compatibility

#### Layer Type Mapping (from source)
```
DYNAMIC_LAYER_TYPE_MAPPING = {
    "full_attention": DynamicLayer,
    "sliding_attention": DynamicSlidingWindowLayer,
    "chunked_attention": DynamicSlidingWindowLayer,
    "conv": LinearAttentionLayer,
    "moe": LinearAttentionLayer,
    "linear_attention": LinearAttentionLayer,
    "hybrid": LinearAttentionAndFullAttentionLayer,
    "hybrid_sliding": LinearAttentionAndSlidingWindowAttentionLayer,
}
```

#### GenerationConfig Constants
```python
STATIC_CACHE_IMPLEMENTATIONS = ("static", "offloaded_static")
DYNAMIC_CACHE_IMPLEMENTATIONS = ("dynamic", "offloaded", "quantized")
DEPRECATED_STATIC_CACHE_IMPLEMENTATIONS = ("sliding_window", "hybrid", "hybrid_chunked", "offloaded_hybrid", "offloaded_hybrid_chunked")
```

### Source Code Analyzed
- `src/transformers/cache_utils.py` — full cache class hierarchy (2056 lines)
- `src/transformers/generation/configuration_utils.py` — `cache_implementation` parameter, constants, validation

### Practical Impact
Understanding the cache API is essential for optimizing LLM inference:
- **Long contexts** → `QuantizedCache` (4-bit KV reduces memory 4-8x)
- **Compiled inference** → `StaticCache` (enables torch.compile for 2-3x speedup)
- **Memory limited** → `DynamicCache(offloading=True)` (moves K/V to CPU)
- **Streaming** → direct `DynamicCache` manipulation in manual loops
- **Sliding window models** (Mistral, Gemma 2) → cache auto-detects from config

### Skill Created
`hf-transformers-cache-api-deep-dive/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md covering the complete cache class hierarchy, user-facing API, layer-level architecture, performance considerations, and practical recipes.
