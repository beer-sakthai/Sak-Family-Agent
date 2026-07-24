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

|---

## 2026-07-24: hf-transformers-5-architecture-registry-system-deep-dive (Topic #195)

### Summary
Source-verified deep-dive into the Transformers v5 Architecture Registry system — the complete pipeline by which config classes are mapped to model classes, remote code is resolved, and custom models register themselves with AutoModel/AutoConfig. Covers `_LazyAutoMapping`, `CONFIG_MAPPING_NAMES` (682 entries), `AutoConfig.register()`, `AutoModel.register()`, the `from_pretrained` resolution flow (local vs. remote code), `_get_model_class`, `register_for_auto_class`, `model_type_to_module_name`, and `get_class_from_dynamic_module`. All findings verified against `transformers==5.14.1` source.

### Key Concepts

**Two-Level Registration:** Transformers v5 uses a two-level registration system:

1. **`AutoConfig` — Config-level registry** (string → config class): `AutoConfig.register(model_type, config_class)` adds to `CONFIG_MAPPING` (a `_LazyAutoMapping` keyed by string model_type like `"llama"`, `"qwen2"`) — 682 entries.
2. **`AutoModel` — Model-level registry** (config class → model class): `AutoModel.register(config_class, model_class)` adds to `cls._model_mapping` (another `_LazyAutoMapping` keyed by config class).

**`_LazyAutoMapping` — The Core (source: `transformers.models.auto.auto_factory`):**
An `OrderedDict` subclass that lazy-loads model/config classes from `transformers.models.{module_name}` only when accessed. Contains:
- `_config_mapping`: `{model_type: config_class_name}` — maps model type strings to config class names (e.g., `"llama"` → `"LlamaConfig"`)
- `_model_mapping`: `{model_type: model_class_name}` — maps model type strings to model class names
- `_reverse_config_mapping`: `{config_class_name: model_type}` — reverse lookup
- `_extra_content`: `{config_class: model_class}` — for user-registered custom models (overrides native mappings)
- `_modules`: `{module_name: module}` — cache of imported model modules

**Key behaviours:**
- **Lazy loading**: Classes are imported only when accessed via `__getitem__` or `keys()`
- **Module resolution**: Uses `model_type_to_module_name(model_type)` which normalizes dashes to underscores (e.g., `"command-r"` → `"command_r"`)
- **Import path**: `from transformers.models.{module_name} import {class_name}`
- **`register(key, value, exist_ok=False)`**: Inserts into `_extra_content`. Skips registration if the config class module starts with `"transformers."` — this prevents native configs from being permanently remapped to custom models when `trust_remote_code=False` is later specified.

### AutoModel.from_pretrained() Resolution Flow

```
from_pretrained(model_name, ...)
  │
  ├── 1. Load config.json → config = AutoConfig.from_pretrained(...)
  │
  ├── 2. Check PEFT adapter config (find_adapter_config_file)
  │      If found, redirect base_model_name_or_path
  │
  ├── 3. Determine code source:
  │      has_remote_code = "auto_map" in config and cls.__name__ in config.auto_map
  │      has_local_code   = type(config) in cls._model_mapping
  │
  ├── 4. Resolve trust_remote_code via resolve_trust_remote_code()
  │
  ├── 5. Dispatch:
  │      ├── REMOTE CODE (has_remote_code && trust_remote_code && !explicit_local_code):
  │      │     class_ref = config.auto_map[cls.__name__]  # e.g., "modeling_lm.py--MyModel"
  │      │     model_class = get_class_from_dynamic_module(class_ref, ...)
  │      │     cls.register(config.__class__, model_class, exist_ok=True)
  │      │     model_class.register_for_auto_class(auto_class=cls)
  │      │     model_class = add_generation_mixin_to_remote_model(model_class)
  │      │     return model_class.from_pretrained(...)
  │      │
  │      └── LOCAL CODE (has_local_code):
  │            model_class = _get_model_class(config, cls._model_mapping)
  │            # If composite model, extract text_config and its quantization_config
  │            return model_class.from_pretrained(...)
  │
  └── 6. (Error if neither remote nor local code available)
```

**Remote Code Resolution (`config.auto_map`):**
The `auto_map` dict in `config.json` maps Auto class names to Python class references:
```json
{
  "auto_map": {
    "AutoConfig": "configuration_my_model.MyModelConfig",
    "AutoModel": "modeling_my_model.MyModel",
    "AutoModelForCausalLM": "modeling_my_model.MyModelForCausalLM"
  }
}
```
- Format: `"module_path.ClassName"` or `"repo_id--module_path.ClassName"` (cross-repo)
- `get_class_from_dynamic_module()` downloads the repo's code files to local cache and dynamically imports the class
- After loading, `cls.register()` adds to `_extra_content` for fast subsequent lookups
- `register_for_auto_class()` sets `cls._auto_class` on the model class for serialization

### `_get_model_class()` — Sub-Architecture Selection

```python
def _get_model_class(config, model_mapping):
    supported_models = model_mapping[type(config)]
    if not isinstance(supported_models, (list, tuple)):
        return supported_models

    name_to_model = {model.__name__: model for model in supported_models}
    architectures = getattr(config, "architectures", [])
    for arch in architectures:
        if arch in name_to_model:
            return name_to_model[arch]

    # Fallback to first element
    return supported_models[0]
```

This handles cases where one config maps to multiple model classes (e.g., `LlamaConfig` → `LlamaModel`, `LlamaForCausalLM`, `LlamaForSequenceClassification`). The `config.architectures` field (e.g., `["LlamaForCausalLM"]`) selects the correct one. If absent, the first registered model class is used.

### Custom Model Registration (User-Side)

```python
from transformers import AutoConfig, AutoModel

# 1. Register the config
AutoConfig.register("my_model", MyModelConfig)

# 2. Register the model (with error checking)
AutoModel.register(MyModelConfig, MyModel, exist_ok=False)

# 3. Mark the model class for auto-serialization
MyModel.register_for_auto_class("AutoModel")

# 4. Now use normally
model = AutoModel.from_pretrained("path/to/model")
```

The `exist_ok=False` default raises if the config class is already mapped. Set to `True` for hot-reloading or overrides.

### Important Guard: Native Config Protection

```python
# In _LazyAutoMapping.register():
if getattr(key, "__module__", "").startswith("transformers."):
    return  # Skip — native configs can't be permanently remapped
```

This ensures that if a remote-code model reuses a native Transformers config (e.g., `LlamaConfig`), the registration is silently skipped. Without this, every subsequent `from_pretrained` call would resolve to the custom model even with `trust_remote_code=False`, because the custom class would sit in `_extra_content` and take priority. Instead, the remote/native disambiguation happens only at `trust_remote_code` time via `resolve_trust_remote_code()`.

### `model_type_to_module_name()` Normalization

```python
model_type_to_module_name("command-r")  # → "command_r"
model_type_to_module_name("qwen2_moe")  # → "qwen2_moe"
model_type_to_module_name("phi4")        # → "phi4"
```

Simply replaces hyphens with underscores. Module names match the model type string (underscore-normalized).

### `register_for_auto_class()` — Serialization Support

```python
@classmethod
def register_for_auto_class(cls, auto_class="AutoModel"):
    import transformers.models.auto as auto_module
    if not hasattr(auto_module, auto_class):
        raise ValueError(f"{auto_class} is not a valid auto class.")
    cls._auto_class = auto_class
```

Sets `cls._auto_class` so that when `save_pretrained()` writes `config.json`, it includes the correct `auto_map` entry for the model's Auto class. Required for custom models that should be loadable with `AutoModel.from_pretrained()` after re-upload.

### `add_generation_mixin_to_remote_model()` — Backward Compat

For backward compatibility with pre-v4.45 models (when `PreTrainedModel` stopped inheriting `GenerationMixin`):
- Checks if model inherits `torch.nn.Module`
- Checks if it already directly inherits `GenerationMixin`
- Checks if it has custom `generate()` or `prepare_inputs_for_generation()`
- If needed, creates a new `type()` dynamically: `type(model_class.__name__, (model_class, GenerationMixin), {**model_class.__dict__})`

### All AutoModel* Classes in v5.14.1

53 Auto classes total. Key groups:
- **Core**: `AutoModel`, `AutoModelForPreTraining`, `AutoModelForCausalLM`, `AutoModelForSeq2SeqLM`, `AutoModelForMaskedLM`
- **Vision**: `AutoModelForImageClassification`, `AutoModelForObjectDetection`, `AutoModelForSemanticSegmentation`, `AutoModelForVideoClassification`, `AutoBackbone`
- **Audio**: `AutoModelForAudioClassification`, `AutoModelForCTC`, `AutoModelForSpeechSeq2Seq`, `AutoModelForTextToSpectrogram`
- **Multimodal**: `AutoModelForImageTextToText`, `AutoModelForMultimodalLM`, `AutoModelForImageToImage`, `AutoModelForVisualQuestionAnswering`, `AutoModelForDocumentQuestionAnswering`
- **Special**: `AutoModelForKeypointDetection`, `AutoModelForKeypointMatching`, `AutoModelForPointmapEstimation`, `AutoModelForNormalEstimation`
- **Other**: `AutoProcessor`, `AutoTokenizer`, `AutoFeatureExtractor`, `AutoImageProcessor`, `AutoVideoProcessor`

### Sources
- `transformers.models.auto.auto_factory` — `_LazyAutoMapping`, `_get_model_class`, `add_generation_mixin_to_remote_model`, `model_type_to_module_name`, `resolve_trust_remote_code`
- `transformers.models.auto.configuration_auto` — `CONFIG_MAPPING`, `CONFIG_MAPPING_NAMES` (682 entries)
- `transformers.models.auto.modeling_auto` — AutoModel source (register, from_pretrained)
- `transformers.models.auto.tokenization_auto` — AutoTokenizer
- `transformers.modeling_utils` — `register_for_auto_class`
- Docs: https://huggingface.co/docs/transformers/en/model_doc/auto
- Source: https://github.com/huggingface/transformers/tree/main/src/transformers/models/auto

## 2026-07-24: hf-transformers-inkling — Inkling by Thinking Machines Lab: 975B Multimodal MoE with Native Image/Audio/Text (Topic #198)

### Summary
Inkling (`thinkingmachines/Inkling`) is a **975B-parameter decoder-only multimodal Mixture-of-Experts transformer** released July 14, 2026 — the first large open model to natively accept **image, text, AND audio inputs** jointly. It uses 256 experts with top-6 routing + 2 shared experts (41B active), hybrid attention (5:1 sliding-window:global), relative attention instead of RoPE, short 1D convolution (SConv) for local processing, hierarchical MLP patchifier for vision, and discrete mel-spectrogram encoding for audio. Supports 1M context, Multi-Token Prediction (MTP) drafters for speculative decoding, and ships in BF16 (2TB VRAM) and NVFP4 (600GB VRAM). Day-0 support in transformers 5.14.0 (`AutoModelForMultimodalLM`), vLLM, SGLang, llama.cpp. Available via HF Inference Providers (Together, DeepInfra). Apache 2.0 license.

### Source
- Blog announcement: https://huggingface.co/blog/thinkingmachines-inkling
- Model: https://huggingface.co/thinkingmachines/Inkling
- NVFP4 quant: https://huggingface.co/thinkingmachines/Inkling-NVFP4
- Model card: https://huggingface.co/thinkingmachines/Inkling/raw/main/README.md
- Playground: https://tinker.thinkingmachines.ai/playground
- Cookbook: https://github.com/thinking-machines-lab/tinker-cookbook
- Transformers v5.14.0 release (same day): `pip install -U transformers`

### 1. Model Overview

| Property | Value |
|----------|-------|
| **Total params** | 975B (BF16), ~952B safetensors |
| **Active params** | 41B |
| **Architecture** | Decoder-only multimodal MoE transformer |
| **Layers** | 66 |
| **Experts** | 256, top-6 routed + 2 shared always active |
| **Context window** | 1M tokens |
| **Attention** | Hybrid: 5 sliding-window layers per 1 global attention layer |
| **Position encoding** | Relative attention (learned position logits, NOT RoPE) |
| **Vocab** | 200,064 tokens |
| **Precision** | BF16 (full) + NVFP4 (quantized) |
| **License** | Apache 2.0 |
| **Pipeline tag** | `image-text-to-text` (HF), also `audio-text-to-text` |
| **Libraries** | transformers 5.14.0+, vLLM, SGLang, llama.cpp, Unsloth |
| **Auto class** | `AutoModelForMultimodalLM` (NEW in transformers 5.14.0) |
| **Processor** | `AutoProcessor` |
| **Training data** | 45T tokens (text, images, audio, video) |

### 2. Key Architectural Innovations

#### Relative Attention (No RoPE)
Unlike most modern LLMs that use Rotary Position Embeddings (RoPE), Inkling uses **relative attention** — each attention layer learns position directly in the attention logits via a fourth projection producing per-token, per-head relative feature `R`. This tensor is modulated by distance between key and query vectors before propagating into the attention module. This avoids the fixed-frequency constraints of RoPE and allows the model to handle variable-length sequences more flexibly.

#### Hybrid Attention: 5:1 Sliding Window:Global
Decoder layers alternate between:
- **Sliding window attention** — attends to a fixed local context window (efficient, O(n·w) compute)
- **Global attention** — attends to the full 1M context (full O(n²) but infrequent)
- Pattern: 5 sliding-window layers followed by 1 global attention layer
- Final layer always uses global attention for rich feature representations

#### Short 1D Convolution (SConv)
A distinctive architectural element: a short 1D convolution (`nn.Conv1d`) over hidden states that reads the current token plus `k` previous tokens (where `k` is the sliding window size). SConv handles local pattern extraction, freeing the attention and MoE modules from learning local representations.

#### Vision: Hierarchical MLP Patchifier
No separate vision encoder (like CLIP/SigLIP). Instead:
- Simple hierarchical MLP consisting of several linear layers
- Each layer progressively merges pixels
- Final layer produces one embedding per patch
- Additional temporal dimension for video (video capability not evaluated out-of-box, intended for fine-tuning)
- The patch grid is folded — small local blocks of neighboring tokens stacked into the channel dimension, processed through hMLP

#### Audio: Discrete Mel-Spectrogram Encoding
- Audio waveform converted to mel scale
- Each 100ms chunk classified into discrete mel spectrogram bin
- Mel bin values embedded and summed to construct final audio input
- No separate audio encoder — lightweight embedding approach

### 3. Multi-Token Prediction (MTP) Drafters

Inkling includes built-in MTP drafters for speculative decoding. MTP (Multi-Token Prediction) is already covered in the transformers 5 cache system (`MtpCache`), but Inkling's implementation is notable because:

- Drafters predict multiple future tokens in parallel
- Used as the draught model in speculative decoding
- The main model (975B) verifies the draft tokens
- Significant speedup on long generations (2-3x throughput improvement)
- Enabled via `model.generate(use_mtp=True, num_assistant_tokens=N)`

### 4. transformers 5.14.0 Integration

Inkling's release coincided with transformers v5.14.0 which introduced `AutoModelForMultimodalLM` — a NEW auto class for multimodal models that accept >1 input modality.

```python
from transformers import pipeline

# High-level: pipeline
pipe = pipeline("image-text-to-text", model="thinkingmachines/Inkling")
result = pipe([
    {"type": "image", "url": "https://.../photo.jpg"},
    {"type": "text", "text": "Describe this image"}
])

# Low-level: Auto classes
from transformers import AutoProcessor, AutoModelForMultimodalLM

processor = AutoProcessor.from_pretrained("thinkingmachines/Inkling")
model = AutoModelForMultimodalLM.from_pretrained(
    "thinkingmachines/Inkling",
    device_map="auto",
    torch_dtype="auto",
)

# Multimodal chat template
messages = [
    {"role": "user", "content": [
        {"type": "image", "url": "https://.../photo.jpg"},
        {"type": "text", "text": "What's in this image?"}
    ]}
]

inputs = processor.apply_chat_template(
    messages,
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt",
).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=200)
response = processor.decode(outputs[0][inputs["input_ids"].shape[-1]:])
print(processor.parse_response(response))
```

#### Reasoning Effort Parameter
Inkling's chat template includes a unique `reasoning_effort` parameter (float 0.0–0.99) that controls inference-time compute:
- Passed through `apply_chat_template(reasoning_effort=0.9)`
- Added as system message: `Thinking effort level: 0.9`
- Higher values → more thorough reasoning chains (slower but more accurate)
- Can also use string aliases in generation config

#### Audio Inference
```python
messages = [
    {"role": "user", "content": [
        {"type": "audio", "url": "https://.../recording.wav"},
        {"type": "text", "text": "Transcribe this audio"}
    ]}
]
# Same apply_chat_template + generate pattern
```

### 5. NVFP4 Quantization

The NVFP4 variant (`thinkingmachines/Inkling-NVFP4`) is NVIDIA's 4-bit floating-point format (not integer quantization):
- Reduces VRAM from ~2TB (BF16) to ~600GB
- Well-calibrated — minimal accuracy regression vs BF16
- Requires Blackwell-generation NVIDIA GPUs (B200, B100)
- Uses the same architecture and can be loaded with the same transformers classes
- Available via HF Inference Providers on compatible hardware

### 6. Inference Providers & Serving

| Provider | Model ID | Live | Tool Calling | Structured Output | Tokens/s | Cost (per M output tokens) |
|----------|----------|------|--------------|-------------------|----------|---------------------------|
| **Together** | `thinkingmachines/Inkling` | ✅ | ✅ | ✅ | ~82.8 | $4.05 |
| **DeepInfra** | `thinkingmachines/Inkling` | ✅ | ❌ | ❌ | ~118.0 | $4.05 |

Both providers serve the BF16 variant. Together supports tool calling and structured output; DeepInfra offers higher throughput (118 tok/s) but no tool/structured output.

#### Local Deployment
```bash
# vLLM
pip install vllm
vllm serve "thinkingmachines/Inkling"

# SGLang
pip install sglang
python3 -m sglang.launch_server --model-path "thinkingmachines/Inkling" --host 0.0.0.0

# llama.cpp (with GGUF quants)
# See huggingface.co/thinkingmachines for GGUF variants

# Docker (via ghcr.io)
docker model run hf.co/thinkingmachines/Inkling
```

### 7. Agentic & Tool-Use Capabilities

Inkling supports:
- **Tool calling** via chat template (JSON-based tool declarations)
- **MCP** (Model Context Protocol) integration — scored 74.1% on MCP Atlas benchmark
- **Agentic coding** — SWE-bench Verified 77.6%, SWE-bench Pro 54.3%
- **Pi-powered agentic coding** (blog mentions native integration with Pi coding agent)

The chat template includes special tokens for tool use:
- `<|content_invoke_tool_json|>` — marks tool invocation beginning
- `<|content_tool|>` — tool response format
- Tools declared via system message with `tool_declare<|content_xml|>` tokens

### 8. Benchmark Results (effort=0.99)

| Category | Benchmark | Score | vs Frontier |
|----------|-----------|-------|-------------|
| **Reasoning** | AIME 2026 | 97.1% | #1 on leaderboard |
| **Reasoning** | GPQA Diamond | 87.2% | Competitive with GPT-5.6 Sol (94.1%) |
| **Reasoning** | HLE (text only) | 29.7% | Below frontier (53.3%) |
| **Reasoning** | HLE (with tools) | 46.0% | Improved with tool use |
| **Coding** | SWE-bench Verified | 77.6% | Better than Nemotron 3 Ultra (70.7%) |
| **Coding** | SWE-bench Pro | 54.3% | Mid-tier |
| **Agentic** | MCP Atlas | 74.1% | Strong, beats most open models |
| **Vision** | MMMU Pro | 73.5% | Strong for first multimodal release |
| **Vision** | Charxiv RQ | 78.1% | Competitive |
| **Audio** | MMAU | 77.2% | Strong (first model to report audio benchmarks) |
| **Audio** | VoiceBench | 91.4% | Very strong |
| **Safety** | StrongREJECT | 98.6% | Excellent refusal rate |
| **Factuality** | BrowseComp (w/ Ctx) | 77.1% | Competitive |

### 9. Key Takeaways for Practitioners

1. **Inkling is the first truly multimodal open model** — not just vision+text but also audio, all natively in one architecture without separate encoder modules for each modality.
2. **Requires heavy hardware** — 2TB VRAM for BF16, 600GB for NVFP4 (Blackwell GPUs needed). Realistically, use HF Inference Providers (Together/DeepInfra) or GGUF quants with llama.cpp.
3. **AutoModelForMultimodalLM** is the new transformers 5.14.0 auto class for any model accepting multiple input modalities. This will become the standard for future multimodal models.
4. **NVFP4 is the quantization format of choice** for Blackwell GPUs — 4-bit float, not integer, maintains calibration well.
5. **Relative attention (no RoPE)** is a notable design choice — the model learns position directly in attention logits via a fourth projection, breaking from the RoPE convention used by Llama, Qwen, DeepSeek, etc.
6. **Reasoning_effort parameter** provides fine-grained control over inference compute — useful for cost/performance trade-offs.
7. **MTP drafters are built-in** for speculative decoding speedup — no separate draught model needed.

### 10. Comparison with Previous Topics

This builds on prior learnings:
- **hf-transformers-5-architecture-deep-dive** (#100-101): Transformers v5 architecture registry, `register_for_auto_class`
- **hf-transformers-moe-deep-dive** (#68): MoE architectures in transformers — Inkling is the most advanced MoE model supported
- **hf-transformers-speculative-decoding-deep-dive-v3** (#167): MTP and speculative decoding — Inkling implements MTP drafters natively
- **hf-transformers-kv-cache-architecture** (#65, #126): Cache hierarchy — Inkling uses the 5.x cache system with MtpCache
- **hf-vllm-transformers-modeling-backend-native** (#179): vLLM native modeling — Inkling supported day-0
- **hf-inference-providers-multi-provider-routing** (#26): Multi-provider inference — Inkling available on Together + DeepInfra

### Sources
- HF Blog: https://huggingface.co/blog/thinkingmachines-inkling
- Model: https://huggingface.co/thinkingmachines/Inkling
- Model card (raw): https://huggingface.co/thinkingmachines/Inkling/raw/main/README.md
- NVFP4: https://huggingface.co/thinkingmachines/Inkling-NVFP4
- Tinker Cookbook: https://github.com/thinking-machines-lab/tinker-cookbook
- SGLang recipe: https://docs.sglang.io/cookbook/autoregressive/ThinkingMachines/Inkling
- vLLM recipe: https://recipes.vllm.ai/thinkingmachines/Inkling
- Unsloth recipe: https://unsloth.ai/docs/models/inkling
- Transformers 5.14.0 release: `pip install -U transformers`
|
|