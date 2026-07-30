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

---

## 2026-07-25 (v2): hf-transformers-cache-api-deep-dive — Transformers v5.14.0 Cache Updates (Topic #392, Deeper)

### Summary
Deeper research into the Transformers cache system using the official v5.14.0 documentation, which now has dedicated pages for cache strategies (`kv_cache.md`) and caching explanation (`cache_explanation.md`). This update adds iterative generation patterns, prefix caching, CPU tensor bookkeeping for compiled inference, OOM-resilient generation, manual generation loops with proper attention mask handling, and updated quantized cache backend recommendations.

### Key New Findings

| Area | Finding |
|------|---------|
| **Iterative generation** | Cache can persist across chatbot turns. Initialize `DynamicCache(config=model.config)` once, reuse in `generate()` for each user message. Warning: special reasoning tokens (`<think>`) may be lost during re-encoding. |
| **Prefix caching** | Prefill a `StaticCache` with a common prefix prompt, then `deepcopy` + reuse for multiple queries. Useful for "system prompt + user query" patterns. Requires running a no-grad forward pass to populate the cache. |
| **CPU tensor bookkeeping** | On Neuron/TPU backends, leaving inputs on CPU avoids compiler retracing. `generate()` moves only forward-required tensors to model device, output follows input device. |
| **OOM resilience** | Pattern: catch `torch.OutOfMemoryError`, `empty_cache()`, retry with `cache_implementation="offloaded"`. |
| **HQQ quantization** | HQQ backend now supports int2, int4, AND int8. Recommended `axis-key` / `axis-value` = 1 for HQQ, 0 for Quanto. |
| **Manual generation loop** | Official example showing proper attention mask concatenation when using DynamicCache in a custom loop without `generate()`. |
| **StaticCache trade-off** | Fixed-size cache wastes tokens in attention computation for short sequences, but enables torch.compile. Best for consistent-length batched generation. |
| **Cache storage implementation** | Caches store per-layer key/value tensors of shape `[batch_size, num_heads, seq_len, head_dim]`. Layer types (`DynamicLayer`, `StaticLayer`, `StaticSlidingWindowLayer`) change only how seq_len is handled. |
| **Comparison table** | Official doc now has clear table: DynamicCache (sliding✅, offload✅, compile❌, medium memory), StaticCache (✅✅✅, high), QuantizedCache (❌❌❌, low). |

### New Recipes Added to SKILL.md
1. Iterative generation with cache — chatbot loop
2. Prefix caching — prefill + reuse StaticCache
3. CPU tensor bookkeeping — Neuron/TPU optimization
4. OOM-resilient generation — automatic offload fallback
5. Manual generation loop — proper attention mask handling
6. Quantized cache backend recommendations — HQQ vs Quanto axis settings

### Updated SKILL.md
- Added YAML frontmatter with `author: SakThai` and `license: MIT`
- Version bumped to 2.0.0
- Added tags for discoverability
- New sections: Iterative Generation, Prefix Caching, CPU Bookkeeping, OOM Resilience, Manual Loop, Quantized Backend Recommendations, Updated Comparison Table
- Added Recipe 5 (prefix caching) and Recipe 6 (OOM resilience)
- Added v5.14.0 source references

### Sources
- https://huggingface.co/docs/transformers/en/kv_cache — Cache strategies (v5.14.0)
- https://huggingface.co/docs/transformers/en/cache_explanation — Caching explanation (v5.14.0)
- https://huggingface.co/docs/transformers/en/generation_strategies — Custom generation methods

### Tags
`kv-cache` `inference` `optimization` `transformers` `torch-compile` `quantization` `memory` `prefix-caching` `iterative-generation`
