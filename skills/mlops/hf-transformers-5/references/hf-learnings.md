---

## 2026-07-24: hf-transformers-5-architecture-deep-dive v2 (Deep Dive — Full Migration & Architecture Analysis)

### Summary
Deep-dive into the Hugging Face Transformers v5.x architecture based on the official v5.0.0 release notes (1200+ commits, first major release in 5 years) and the complete MIGRATION_GUIDE_V5.md (791 lines) from the huggingface/transformers repository. Covers all breaking changes, new architectural components, and API migrations from v4 to v5, plus the weekly-release cadence (v5.0.0→v5.14.1 across 6 months). Verified at transformers v5.14.1 (latest, 2026-07-16).

### v5 Release Cadence
Starting with v5.0.0 (2026-01-26), Transformers adopted a **weekly minor release** cycle instead of every 5 weeks. This means models land in the library within days of release rather than weeks. As of 2026-07-24, the library has progressed through 14 minor releases (v5.0.0 through v5.14.1) in ~6 months.

### 1. Dynamic Weight Loading (Major Architectural Change)

**What changed:** The `from_pretrained` method was completely rewritten around a new `WeightConverter` class system.

**New concept — WeightConverter:**
```python
class WeightConverter(WeightTransform):
    operations: list[ConversionOps]
    source_keys: Union[str, list[str]]
    target_keys: Union[str, list[str]]
```

**Example — Fusing QKV projections:**
```python
conversion = WeightConverter(
    ["self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj"],
    "self_attn.qkv_proj",
    operations=[Concatenate(dim=0)],
)
```

**Benefits:**
- Much cleaner definition of weight transformations
- Reversible transformations (loading then saving produces the same checkpoint)
- Faster loading via scheduling of tensor materialization
- Enables complex combinations previously impossible (quantization + MoEs, tensor parallelism + MoEs)
- Removed years of technical debt in `from_pretrained`

**Impact:** Every model now defines its weight mapping declaratively, separating the checkpoint serialization format from the in-memory model structure.

### 2. Tokenization — Complete Backend Refactor

#### Removed: Slow/Fast Tokenizer Separation
v4 maintained two parallel implementations per model:
- `tokenization_<model>.py` — Python-based (slow)
- `tokenization_<model>_fast.py` — Rust-based (fast)

v5 consolidates to a **single file**: `tokenization_<model>.py` with backend selection.

#### New Backend Architecture (4 Backends)
| Backend | Use Case |
|---------|----------|
| **TokenizersBackend** | Preferred. Rust-based `tokenizers` library. Full feature set (training, additional tokens, parallelization, offsets, customization) |
| **SentencePieceBackend** | For models requiring `sentencepiece` library. Inherits from PythonBackend. |
| **PythonBackend** | Pure Python implementation (was `PreTrainedTokenizer` in v4) |
| **MistralCommonBackend** | Uses Mistral's `mistral-common` tokenization library |

`AutoTokenizer` automatically selects the right backend. Usage remains `AutoTokenizer.from_pretrained()`.

#### v5 Tokenizer API Changes
| v4 (deprecated/removed) | v5 replacement |
|---|---|
| `batch_decode()` | `decode()` (single unified method) |
| `encode_plus()` | `__call__()` |
| `tokenizer(text, ...)` + `with tokenizer.as_target_tokenizer():` | `tokenizer(text, text_target=...)` |
| `prepare_seq2seq_batch()` | `__call__()` with `text_target` |
| `apply_chat_template()` returning `input_ids` | Returns `BatchEncoding` dict |
| `special_tokens_map.json` + `added_tokens.json` | Consolidated into `tokenizer_config.json` + `tokenizer.json` |
| `additional_special_tokens` | `extra_special_tokens` |
| `sanitize_special_tokens()` | Removed |
| `BatchEncoding.words()` | `word_ids()` |
| `add_bos_token`/`add_eos_token` in config | Set in tokenizer class or `tokenizer.json` |

#### New: Empty/Untrained Tokenizer Initialization
```python
from transformers import LlamaTokenizer
tokenizer = LlamaTokenizer()  # Blank, trainable tokenizer following Llama definition
```

#### New: Init from Vocab and Merges
```python
tokenizer = LlamaTokenizer(
    vocab={"<unk>": 0, "<s>": 1, "</s>": 2, "hello": 3, "world": 4},
    merges=[("h", "e"), ("l", "l"), ("o", " ")]
)
```

#### Removed Methods from Base Class
- `create_token_type_ids_from_sequences()` — moved to subclasses that need it
- `prepare_for_model()`, `build_inputs_with_special_tokens()`, `truncate_sequences()` — moved to PythonBackend
- `_switch_to_input_mode()`, `_switch_to_target_mode()` — use `text_target` instead
- `parse_response()` — removed

### 3. TensorFlow and Jax Removed
v5 drops TF and JAX backends entirely to focus on PyTorch. The library is now **PyTorch-only**.

### 4. Quantization Changes

**Removed** `load_in_4bit` and `load_in_8bit` direct arguments. Must use `quantization_config`:
```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
quantization_config = BitsAndBytesConfig(load_in_4bit=True)
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-3B",
    device_map="auto", quantization_config=quantization_config)
```

### 5. Modeling Changes

#### Attention Features Removed
| Removed Feature | Reason |
|---|---|
| Head masking | Only worked with eager, barely used |
| Relative positional biases in BERT-like models | Added complexity, barely used, only worked with eager |
| Head pruning (`prune_heads`) | Legacy feature |

#### Removed Torch APIs
- `torchscript` support dropped (use `torch.compile`/`dynamo`/`export`)
- `torch.fx` support dropped

#### Auto-Class Changes
| v4 | v5 |
|---|---|
| `AutoModelWithLMHead` | `AutoModelForCausalLM` or `AutoModelForMaskedLM` or `AutoModelForSeq2SeqLM` |
| `AutoModelForVision2Seq` | `AutoModelForImageTextToText` |

#### Generate() Changes
- **Default cache**: Now model-defined instead of always `DynamicCache` (PR #41505)
- **Output classes**: Only 4 output classes (decoder-only vs encoder-decoder × beams vs no-beams)
- **Generation parameters**: No longer accessible via `model.config` — use `model.generation_config`
- Removed deprecated decoding-method classes moved to Hub

#### RoPE Parameters Unification
- `rope_theta`/`rope_type` moved to `config.rope_parameters` dict
- `config.rope_theta` → `config.rope_parameters["rope_theta"]`
- Nested rope_parameters for models with multiple RoPE configs (Gemma3, ModernBert)
- RotaryEmbeddings layers may return dict of tuples for multi-RoPE models

#### VLM Changes
- `model.language_model` shortcut removed — use `model.model.language_model` or `model.get_decoder()`
- Multi-modal models now have proper `base_model` prefix
- Qwen-VL config is nested; access via `config.text_config.vocab_size` (not `config.vocab_size`)

#### Feature Extraction Changes
`get_text_features()`, `get_image_features()`, `get_audio_features()`, `get_video_features()` now return `BaseModelOutputWithPooling` instead of raw tensor:
```python
# v5
outputs = model.get_text_features(**inputs, return_dict=True)
text_embeddings = outputs.pooler_output  # not the raw return value
```

#### Custom Pretrained Models
`_init_weights` is called automatically with a generalized initialization scheme (normal for Linear/Conv/Embedding, ones for norms). Override with `pass` if you want full control.

### 6. Image Processor Refactor

#### Old vs New
| v4 | v5 |
|---|---|
| `image_processing_<model>.py` (PIL/slow) | `image_processing_pil_<model>.py` (PIL backend) |
| `image_processing_<model>_fast.py` (torchvision) | `image_processing_<model>.py` (torchvision backend — default) |

**New parameter:** `use_fast` → `backend`
```python
# v5
processor = AutoImageProcessor.from_pretrained("...", backend="torchvision")
processor = AutoImageProcessor.from_pretrained("...", backend="pil")
```

**New registration API:**
```python
# v5
AutoImageProcessor.register(MyConfig, image_processor_classes={
    "pil": MyPilProcessor,
    "torchvision": MyTorchvisionProcessor
})
```

**Custom backends:** Any string key (e.g., `"mlx"`, `"onnx"`) via `register_backend()` class method.

### 7. Pipeline Removals

| Removed Pipeline | Replacement |
|---|---|
| `question-answering` | LLM chat via `text-generation` pipeline |
| `Text2TextGenerationPipeline` | `text-generation` with chat model |
| `SummarizationPipeline` | `text-generation` with summarization prompt |
| `TranslationPipeline` | `text-generation` with translation prompt |
| `image-to-text` | `image-text-to-text` pipeline |
| `visual-question-answering` | `image-text-to-text` pipeline |
| `image-to-image` | Diffusers library |

Image-text-to-text pipelines now require images embedded in chat content field (not separate argument).

### 8. Trainer Changes

#### Removed TrainingArguments (low usage)
`mp_parameters`, `_n_gpu`, `overwrite_output_dir`, `logging_dir`, `jit_mode_eval`, `tpu_num_cores`, `past_index`, `ray_scope`, `warmup_ratio`

#### Removed TrainingArguments (deprecated)
All replaced with new names:
- `fsdp_min_num_params`/`fsdp_transformer_layer_cls_to_wrap` → `fsdp_config`
- `push_to_hub_token` → `hub_token`
- `per_gpu_train_batch_size` → `per_device_train_batch_size`
- `no_cuda` → `use_cpu`
- `fp16_backend`/`half_precision_backend` → torch.amp only

#### Removed Trainer Init Arguments
- `tokenizer` → `processing_class`
- `model_path` in `train()` → `resume_from_checkpoint`

#### New Defaults
- `use_cache` in model config defaults to `False` (can override via `TrainingArguments.use_cache`)

### 9. CLI Changes

| v4 | v5 |
|---|---|
| `transformers-cli ...` | `transformers ...` (CLI now uses Typer) |
| `transformers chat` (monolithic) | Split into `transformers chat` (client) + `transformers serve` (server) |
| `transformers run` | Removed (undocumented artifact) |

New `transformers serve` command serves an OpenAI-compatible HTTP endpoint. `transformers chat` connects to any OpenAI-compatible endpoint.

### 10. Safetensors-Only & Shard Size
- `safe_serialization=False` **removed** — safetensors is now mandatory for `save_pretrained()` and `push_to_hub()`
- Default shard size increased from **5GB to 50GB** (enabled by Xet backend)

### 11. PushToHubMixin Changes
- `organization` and `repo_url` removed — use `repo_id`
- `use_temp_dir` removed — always uses temp dir
- `ignore_metadata_errors` removed
- `push_to_hub` no longer accepts `**kwargs`; all params explicitly documented
- Arguments are now keyword-only (except `repo_id`)

### 12. Environment & Requirements
- `TRANSFORMERS_CACHE`, `PYTORCH_TRANSFORMERS_CACHE`, `PYTORCH_PRETRAINED_BERT_CACHE` removed — use `HF_HOME`
- `use_auth_token` → `token` everywhere
- `huggingface_hub` ≥1.0.0 required (HTTP backend changed from `requests` to `httpx`)
- `hf_transfer`/`HF_HUB_ENABLE_HF_TRANSFER` dropped in favor of `hf_xet`
- `typer-slim` added as required dependency
- Python 3.10+, PyTorch 2.4+
- PEFT ≥0.18.0 required

### 13. Configuration Changes
- `from_xxx_config` methods deleted — configs init from `__init__` only
- Cannot load config from URL — local path or Hub repo only
- Non-generative models no longer have `generation_config`
- Config's `rope_theta` attribute access → `rope_parameters` dict

### 14. Processor Changes
- Processor attributes serialized under `processor_config.json` as nested dict
- `XXXFeatureExtractor` classes removed — use `XXXImageProcessor`
- `XXXFastImageProcessorKwargs` removed — use `XXXImageProcessorKwargs`
- `is_fast` property → `processor.backend == "torchvision"`

### Key Takeaways
1. **PyTorch-only**: TF/JAX dropped entirely — simplifies maintenance and accelerates new model support
2. **Weekly releases**: Models land within days, not weeks
3. **WeightConverter**: Declarative weight transforms enable reversible, composable weight operations
4. **Tokenization consolidation**: 4 backends behind a unified API, single file per tokenizer
5. **Safetensors mandatory**: No more pickle fallback; 50GB default shard size
6. **Pipeline simplification**: Text/vision pipelines streamlined to use chat models and VLMs
7. **Generate() API cleaner**: Model-default cache, 4 output classes, generation params separate from model config
8. **Image processor refactor**: Named backends (torchvision/PIL) replace slow/fast split
9. **httpx replaces requests**: Breaking change for code catching `requests.HTTPError`
10. **Xet replaces hf_transfer**: New storage backend for faster uploads/downloads

### Resources
- Official Migration Guide: https://github.com/huggingface/transformers/blob/main/MIGRATION_GUIDE_V5.md
- v5.0.0 Release: https://github.com/huggingface/transformers/releases/tag/v5.0.0
- Latest v5.14.1 Release: https://github.com/huggingface/transformers/releases/tag/v5.14.1
- v5 Announcement Blog: https://huggingface.co/blog/transformers-v5
|- Docs: https://huggingface.co/docs/transformers/en/index

---

## 2026-07-24: hf-transformers-speculative-decoding-deep-dive — v5.14.0 New Features: MTP Support & Static Ensemble Verification (Topic #79 Deepened)

### Summary
Deep dive into two major generation features added in Transformers v5.14.0 (2026-07-15):
1. **Multi-Token Prediction (MTP) decoding** — proper inference-time MTP support via `use_mtp=True`, auto-loading MTP head weights from the Hub repo and integrating with the assisted decoding framework. ~40% faster decoding on supported models.
2. **Static ensemble verification** — training-free increase of draft token acceptance rates by blending target/draft distributions via `assistant_ensemble_weight`. Pareto-optimal tradeoff between speed and distributional bias.

Source code: `transformers/generation/configuration_utils.py`, PRs #46229 and #45979 on GitHub. Docs: https://huggingface.co/docs/transformers/en/assisted_decoding.

---

### 1. Multi-Token Prediction (MTP) Decoding — `use_mtp=True`

**PR #46229** by @Cyrilvallez. Adds proper MTP inference support to Transformers' `generate()`.

#### How it works

MTP is a training-time technique (pioneered by DeepSeek V3/R1) where the model is trained with lightweight MTP "heads" that predict N future tokens simultaneously. During inference, these heads act as a built-in draft mechanism — no separate assistant model needed.

**Before v5.14.0:** MTP was only usable during training. Inference required external tools or manual handling of MTP heads.

**After v5.14.0:** A single `use_mtp=True` flag enables MTP decoding:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "zai-org/GLM-4.5-Air"

model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_id)

inputs = tokenizer("Hello, who are you and what can you do?", return_tensors="pt").to(model.device)

# Enable MTP — auto-loads MTP head weights from the repo
out = model.generate(**inputs, use_mtp=True, do_sample=False, max_new_tokens=100)
```

#### Key design decisions

| Aspect | Detail |
|--------|--------|
| **Weight loading** | `generate()` automatically scans the model repo for MTP layer weights and loads them |
| **Integration** | MTP uses the existing `_assisted_decoding` path — no new decoding method added |
| **Cache** | Uses `MtpCache` (extends `DynamicCache` with token-offset logic for MTP depth tracking) |
| **Depth** | `mtp_num_tokens` controls how many tokens to draft per step (default: 1) |
| **Fallback** | When all candidates are accepted, the bonus token comes from the main model |

#### Benchmark data

On GLM-4.5-Air (single test, official PR):

| Metric | Without MTP | With MTP | Improvement |
|--------|------------|----------|-------------|
| Decoding speed | baseline | +40% faster | 1.4× speedup |
| Token acceptance rate | — | 73.68% | — |

#### Supported models

| Model Family | MTP Support | Notes |
|-------------|-------------|-------|
| GLM-4.5-Air | ✅ Full | Reference implementation in PR |
| DeepSeek V3/R1 | ✅ Conceptual | Pre-v5.14 code had partial support via MtpCache |
| DeepSeek V4 | ⚠️ Partial | Different MTP layer naming (`e_proj`/`h_proj` split) + quantization — needs ConversionOps fix |
| Other MTP-trained models | ✅ Automatic | `generate()` scans repo for MTP weights |

**DeepSeek V4 limitation:** The MTP layer naming/conventions changed — `eh_proj` was split into `e_proj` and `h_proj` with quantization. A fix via `ConversionOps` or a model attribute `_mtp_conversions` is expected in a future release.

#### Cache infrastructure

MTP decoding uses `MtpCache`, which extends `DynamicCache`:

```python
class MtpCache(DynamicCache):
    # Extends DynamicCache with token-offset logic for MTP depth tracking
    # MTP depth k runs k+1 tokens ahead
    def get_query_offset(self) -> int:
        return self.layer_idx + 1
```

The `get_query_offset()` method adds `layer_idx + 1` offset — each MTP depth step runs one token ahead in the KV cache.

---

### 2. Static Ensemble Verification — `assistant_ensemble_weight`

**PR #45979** by @kasakh. Adds a training-free method to increase the acceptance rate of speculative decoding by relaxing the verification distribution.

#### The problem

Standard speculative decoding is **lossless** — it guarantees the output distribution matches the target model exactly. But this strictness rejects many plausible tokens, keeping acceptance rates low.

#### The solution

Static ensemble verification blends the target and draft distributions during verification:

```
v(x) = w * p_target(x) + (1 - w) * q_draft(x)
```

Where:
- `v(x)` = ensemble verifier distribution
- `p_target(x)` = target model distribution
- `q_draft(x)` = draft model distribution
- `w` = `assistant_ensemble_weight` (float in (0, 1))

This **provably** achieves the Pareto-optimal tradeoff between acceptance rate and distributional bias (Proposition 1 in the paper). The acceptance probability increases from `1 - TV(q,p)` to `1 - w * TV(q,p)`.

#### Usage

```python
# Sampling mode — recommended starting value: 0.7
outputs = model.generate(
    **inputs,
    assistant_model=assistant_model,
    do_sample=True,
    assistant_ensemble_weight=0.7,
)

# Greedy mode — compares draft tokens against argmax(v)
outputs = model.generate(
    **inputs,
    assistant_model=assistant_model,
    do_sample=False,
    assistant_ensemble_weight=0.7,
)
```

#### Parameter behavior

| `assistant_ensemble_weight` | Effect |
|-----------------------------|--------|
| `None` (default) | Standard lossless speculative decoding (backward compatible) |
| `1.0` | Equivalent to standard lossless (mathematically identical) |
| `0.7` (recommended) | Good balance: ~30% reduction in rejection, minor distribution shift |
| `0.5` | Equal blend: significantly higher acceptance, larger distributional shift |
| → `0.0` | Extreme: approaches draft-only (high speed, high distributional bias) |

**Constraint:** Must be in the open interval `(0.0, 1.0)`. Values outside raise `ValueError`.

#### Design decisions (from PR)

1. **Fallback distribution unchanged:** Since `[v-q]+ = w*[p-q]+` normalizes to the same distribution as `[p-q]+`, the standard fallback is used directly for numerical stability.

2. **Acceptance ratio form:** Uses `1 - w + w*(p_i/q_i)` — algebraically equivalent to `v_i/q_i` but avoids constructing the full ensemble distribution (more efficient).

3. **Bonus token:** When all candidates are accepted, the bonus token uses `p` (target) rather than `v`, since `q` at position N+1 is unavailable. This is conservative and documented.

4. **Greedy ensemble:** For `do_sample=False`, compares draft tokens against `argmax(v)` — "greedy under the ensemble verifier."

5. **Requires candidate logits:** Not supported with prompt lookup decoding or other candidate generators that don't return logits.

#### How it integrates

The acceptance ratio computation in `_speculative_sampling`:

```python
# Standard: accept if uniform_random < p_i / q_i
# Ensemble:  accept if uniform_random < 1 - w + w * (p_i / q_i)
```

When `w=1.0`, this reduces to the standard formula. When `w=0.7`, the acceptance threshold is lower, so more tokens are accepted.

#### Paper reference

**Static Ensemble Verification** — arxiv.org/abs/2604.07622. Proposes the ensemble verifier and proves it achieves the Pareto-optimal tradeoff between acceptance rate and distributional bias.

---

### Key Takeaways

1. **Two new generation params in v5.14.0:** `use_mtp` (bool) and `assistant_ensemble_weight` (float)
2. **MTP is now one flag away:** `model.generate(use_mtp=True)` — auto-loads MTP heads, ~1.4× speedup
3. **Ensemble verification is free performance:** `assistant_ensemble_weight=0.7` increases acceptance rates with zero training
4. **Both integrate with existing assisted decoding** — no new code paths, just new parameters
5. **DeepSeek V4 MTP not yet supported** — pending a fix for renamed/quantized MTP layers
6. **Ensemble requires candidate logits** — not compatible with prompt lookup decoding

### Resources
- Assisted decoding docs: https://huggingface.co/docs/transformers/en/assisted_decoding
- PR #46229 (MTP support): https://github.com/huggingface/transformers/pull/46229
- PR #45979 (Static ensemble verification): https://github.com/huggingface/transformers/pull/45979
- Static ensemble paper: https://arxiv.org/abs/2604.07622
- GenerationConfig source: https://github.com/huggingface/transformers/blob/main/src/transformers/generation/configuration_utils.py
- Assisted generation blog: https://huggingface.co/blog/assisted-generation

---

## 2026-07-24: hf-transformers-qwen3 (Qwen3 & Qwen3.5 Architecture Deep Dive)

### Summary
Deep-dive into the Qwen3 and Qwen3.5 model family architectures within Hugging Face Transformers v5.14.1. Covers the full ecosystem: Qwen3 (dense + MoE), Qwen3Next (512-expert MoE), Qwen3.5 (hybrid linear+full attention), Qwen3VL/VLMoe (vision-language), Qwen3OmniMoe (omni-modal + speech), and Qwen3ASR (speech recognition). Verified against Transformers v5.14.1 source and model configs. Qwen3 models have 16M+ downloads each, making them one of the most-used open-source model families.

### QwenModel Family Tree (Transformers v5)

```
Qwen3 (qwen3)            Dense decoder, full attention, QK-norm, head_dim=128
Qwen3 MoE (qwen3_moe)    128 experts, 8 active/tok, GQA 32→4
Qwen3Next (qwen3_next)   512 experts, 10 active/tok, hybrid linear/full attn, 48L
Qwen3VL (qwen3_vl)       Vision-language (dense encoder + Qwen3)
Qwen3VLMoe (qwen3_vl_moe) Vision-language + MoE
Qwen3.5 (qwen3_5)        Hybrid: 3 linear + 1 full attn, head_dim=256, vocab 248k
Qwen3.5 MoE (qwen3_5_moe) 256 experts, hybrid attn, 40 layers, GQA 16→2
Qwen3OmniMoe              Omni-modal: text+vision+audio, MoE
Qwen3ASR                  Automatic speech recognition (encoder-decoder)
```

### 1. Qwen3 Dense (`model_type: qwen3`)

**Architecture:** Standard Transformer decoder with causal attention.

**Key innovations vs. Llama-style:**
- **QK Normalization** — both query and key projections go through `Qwen3RMSNorm` on the head dimension BEFORE RoPE. This is unlike Llama (which doesn't norm Q/K) and OLMo (which norms both, but OLMo normalizes the full hidden dim before projection).
- **Configurable `head_dim`** — head dimension is an explicit config field (`head_dim: 128`), not derived from `hidden_size / num_attention_heads`. This allows non-standard head dimensions.
- **Layer-type routing** — each layer's attention type is specified in the `layer_types` array. Default is all `full_attention`, but can be `sliding_attention` per-layer. The attention module reads `self.sliding_window = config.sliding_window if self.layer_type == "sliding_attention" else None` and passes it to flash attention.
- **`rope_parameters` dict** — RoPE configuration is packed into a dict with `rope_theta`, `rope_type`, and optionally `partial_rotary_factor`. This is the v5 convention.
- **Vocabulary size:** 151,936 tokens (vs Qwen2's 152,064 — a slight reduction).

**Default configuration (8B class):**
```
hidden_size: 4096
intermediate_size: 22016
num_attention_heads: 32
num_key_value_heads: 32  (no GQA in the dense variant!)
head_dim: 128
num_hidden_layers: 32
max_position_embeddings: 32768
vocab_size: 151936
layer_types: ['full_attention'] × 32
sliding_window: None
max_window_layers: 28
```

### 2. Qwen3 MoE (`model_type: qwen3_moe`)

**Architecture:** Mixture of Experts with 128 experts and 8 active per token.

**Components:**
- `Qwen3MoeAttention` — same QK-norm attention as dense
- `Qwen3MoeTopKRouter` — simple linear router + softmax + top-k selection
  - `router_logits = F.linear(hidden_states, weight)` → softmax → top-k
  - Optional `norm_topk_prob` to renormalize routing weights
- `Qwen3MoeExperts` — sparse expert computation
- `Qwen3MoeSparseMoeBlock` — dispatcher that reshapes inputs → routes → experts → combines
- `Qwen3MoeMLP` — shared dense MLP used when no MoE

**Config highlights:**
```
num_experts: 128
num_experts_per_tok: 8
hidden_size: 2048
intermediate_size: 6144        (shared/dense intermediate)
moe_intermediate_size: 768     (per-expert intermediate)
num_attention_heads: 32
num_key_value_heads: 4         (GQA 8:1 ratio)
norm_topk_prob: False
router_aux_loss_coef: 0.001
output_router_logits: False
decoder_sparse_step: 1         (every layer uses MoE)
mlp_only_layers: []            (all layers use MoE)
vocab_size: 151936
```

### 3. Qwen3Next (`model_type: qwen3_next`)

**Architecture:** Next-generation MoE with 512 experts + hybrid attention. This is the largest Qwen architecture on the Hub.

**Landmark specs:**
```
num_experts: 512
num_experts_per_tok: 10
num_hidden_layers: 48
hidden_size: 2048
head_dim: 256
num_attention_heads: 16
num_key_value_heads: 2         (most extreme GQA yet — 8:1)
intermediate_size: 5632
moe_intermediate_size: 512
shared_expert_intermediate_size: 512
norm_topk_prob: True           (re-normalizes routing probs)
partial_rotary_factor: 0.25   (only 25% of dims get RoPE)
vocab_size: 151936
```

**Hybrid attention pattern (same as Qwen3.5) — 3 linear + 1 full, repeated:**
```
layer_types: ['linear_attention', 'linear_attention', 'linear_attention', 'full_attention',
              'linear_attention', 'linear_attention', 'linear_attention', 'full_attention', ...]
```
The linear attention blocks use `Qwen3_5GatedDeltaNet` (same class as Qwen3.5).

### 4. Qwen3.5 Dense (`model_type: qwen3_5`)

**Architecture:** Multimodal hybrid model combining linear attention (GatedDeltaNet) and full attention (standard scaled dot-product) at a 3:1 ratio, with a separate vision encoder for image/video understanding.

**Revolutionary features:**
- **Hybrid token mixing** — 24 linear attention layers + 8 full attention layers (interleaved 3:1)
- **GatedDeltaNet** — the linear attention mechanism (see below)
- **Native multimodal** — vision encoder (ViT-based, 27 layers) with spatial/temporal patch embedding
- **Extended vocabulary** — 248,320 tokens (64% larger than Qwen3's 151k)
- **Partial RoPE** — only 25% of attention dimensions get rotary embeddings

**Config highlights (multimodal wrapper):**
```
model_type: qwen3_5
vocab_size: 248320

text_config (qwen3_5_text):
  hidden_size: 4096
  head_dim: 256              (double Qwen3's 128)
  intermediate_size: 12288
  num_attention_heads: 16
  num_key_value_heads: 4     (GQA 4:1)
  partial_rotary_factor: 0.25
  max_position_embeddings: 32768

vision_config (qwen3_5_vision):
  depth: 27
  hidden_size: 1152
  num_heads: 16
  patch_size: 16
  spatial_merge_size: 2
  temporal_patch_size: 2
  out_hidden_size: 3584       (projects to text hidden size)
```

### 5. GatedDeltaNet — The Linear Attention Engine

**What it is:** A gated delta rule network with causal convolution, combining ideas from DeltaNet (Yang et al., 2024), Mamba (SSM discretization), and gating mechanisms.

**Architecture:**
```
Input → in_proj_qkv (Q+K+V) → Conv1d (kernel=4, groups=dim, causal)
     → in_proj_z (gating)   → in_proj_b (beta) → in_proj_a (alpha)
     → Delta rule recurrence (chunked or recurrent mode)
     → out_proj → output
```

**Key components:**
1. **Causal Conv1d** — depthwise conv with kernel_size=4 on combined QKV, captures local patterns before the recurrent step
2. **Discretization** — `dt_bias` (per-head learned bias) and `log_A` (per-head learned decay), similar to Mamba/SSM discretization
3. **Delta rule** — `A` decay matrix + `dt` (step size) control how quickly past context is forgotten, inspired by DeltaNet's gated delta attention
4. **Gating** — Separate `in_proj_z` for output gating, `in_proj_b` for beta modulation, `in_proj_a` for alpha modulation
5. **Two computation modes:**
   - **Chunked** (`chunk_gated_delta_rule`) — parallel within chunks, O(N) across chunks
   - **Recurrent** (`recurrent_gated_delta_rule`) — linear-time sequential, good for generation

**Performance:** The linear attention mechanism is O(N) in sequence length vs O(N²) for full attention, enabling longer context at lower cost. The 3:1 hybrid ratio provides a good trade-off: linear layers handle most tokens efficiently, while full-attention layers (every 4th) provide long-range recall.

**Dependencies for fast path:**
- `flash-linear-attention` (fla) — https://github.com/fla-org/flash-linear-attention
- `causal-conv1d` — https://github.com/Dao-AILab/causal-conv1d

### 6. Qwen3.5 MoE (`model_type: qwen3_5_moe`)

**Architecture:** 256-expert MoE with shared expert + hybrid 3:1 linear/full attention.

**Key diffs from Qwen3MoE:**
```
Qwen3MoE → Qwen3.5MoE
- 128 experts → 256 experts
- 32 layers → 40 layers
- GQA 32→4 → GQA 16→2
- All full attention → Hybrid 3:1 linear/full
- Vocab 151k → 248k
```

**Config highlights:**
```
num_experts: 256
num_experts_per_tok: 8
num_hidden_layers: 40
shared_expert_intermediate_size: 512
moe_intermediate_size: 512
hidden_size: 2048
head_dim: 256
num_attention_heads: 16
num_key_value_heads: 2         (16:2 = 8:1 GQA ratio)
vocab_size: 248320
```

### 7. Vision-Language Models (Qwen3VL, Qwen3VLMoe, Qwen3_5)

All Qwen VL models share a similar two-tower design:
- **Vision encoder** — ViT-style with patch embedding, spatial merge, and optional temporal patch for video
- **Text decoder** — The corresponding LLM (Qwen3, Qwen3MoE, or Qwen3.5MoE)
- **Vision projector** — A `PatchMerger` that maps vision encoder outputs to text embedding space

Qwen3.5VLMoe (`qwen3_5_moe_vl`) adds:
- A separate `vision_config` within the MoE text config
- Video support via temporal patch embedding (temporal_patch_size=2)
- Special tokens: `image_token_id=248056`, `video_token_id=248057`, `vision_start=248053`, `vision_end=248054`

### 8. Qwen3ASR (`model_type: qwen3_asr`)

**Architecture:** Encoder-decoder for speech recognition. Uses a dedicated audio encoder (`Qwen3ASREncoder`) with CTC-style token classification head.

**Components:**
- `Qwen3ASREncoder` — stacks of self-attention + conv layers for audio features
- `Qwen3ASRFeatureExtractor` — mel-spectrogram extraction
- `Qwen3ASRProcessor` — combines feature extractor + tokenizer
- `Qwen3ASRForConditionalGeneration` — seq2seq with decoder
- `Qwen3ASRForTokenClassification` — CTC head for alignment-free ASR

### 9. Usage Patterns

**Basic Qwen3 text generation:**
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-8B")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")

messages = [{"role": "user", "content": "What is MoE architecture?"}]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt", add_generation_prompt=True)
outputs = model.generate(inputs, max_new_tokens=256)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

**Qwen3.5 with hybrid attention (fast path):**
```python
# For optimal performance with GatedDeltaNet, install:
#   pip install flash-linear-attention causal-conv1d
#
# Without them, Transformers falls back to pure PyTorch implementation.
# The fallback is functional but ~2-3x slower for long sequences.

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3.5-9B")
# Model auto-selects attention implementation based on available kernels
```

**Checking MoE config at runtime:**
```python
from transformers import AutoConfig
config = AutoConfig.from_pretrained("Qwen/Qwen3-235B-A14B")
print(f"Experts: {config.num_experts}, Active/tok: {config.num_experts_per_tok}")
print(f"GQA: {config.num_attention_heads} heads → {config.num_key_value_heads} KV heads")
```

### 10. Key Takeaways

1. **Qwen3 introduced QK-norm + sliding window attention** — the foundation that made all subsequent variants possible
2. **Qwen3MoE pioneered massive MoE at scale** — 128 experts with 8 active, now used in production by Alibaba Cloud
3. **Qwen3.5's hybrid architecture is a breakthrough** — 3:1 linear-to-full attention ratio with GatedDeltaNet enables O(N) inference cost for most layers while maintaining full-attention quality every 4th layer
4. **Qwen3Next pushes MoE to 512 experts** — the largest open-source MoE architecture in Transformers
5. **Vocabulary doubled from Qwen3 (151k) to Qwen3.5 (248k)** — better tokenization efficiency for Chinese + multilingual + code
6. **Extreme GQA** — Qwen3.5MoE uses only 2 KV heads for 16 attention heads (8:1), reducing KV cache pressure by 8×
7. **Transformers v5 model-type convention** — all Qwen variants use distinct `model_type` values (`qwen3`, `qwen3_moe`, `qwen3_5`, `qwen3_5_moe`, etc.) enabling auto-class resolution via `AutoModel`

### Resources
- Qwen3 model card: https://huggingface.co/Qwen/Qwen3-8B
- Qwen3.5 model card: https://huggingface.co/Qwen/Qwen3.5-9B
- Transformers Qwen3 docs: https://huggingface.co/docs/transformers/main/en/model_doc/qwen3
- Gated Delta Net paper: Yang et al., "Parallelizing Linear Transformers with the Delta Rule" (2024)
- Flash Linear Attention: https://github.com/fla-org/flash-linear-attention
