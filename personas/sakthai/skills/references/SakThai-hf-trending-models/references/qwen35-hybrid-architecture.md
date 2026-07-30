# Qwen3.5 / Qwen3.6 Hybrid Architecture — Linear Attention + Full Attention Interleaving

_Reference extracted from `empero-ai/Qwythos-9B-Claude-Mythos-5-1M` (base: Qwen/Qwen3.5-9B). Qwen3.6 variants share the same hybrid structure._

## Architecture Overview

Qwen3.5 departs from pure transformer by **interleaving linear-attention (SSM-style) layers with full-attention layers** at a fixed ratio. The result is a hybrid that keeps the sub-quadratic scaling of state-space models while retaining a regular full-attention layer every N steps for retrieval-heavy tasks.

## Config Structure (Multimodal)

```json
{
  "model_type": "qwen3_5",
  "architectures": ["Qwen3_5ForConditionalGeneration"],
  "text_config": { /* LLM decoder — THIS is the authoritative source */ },
  "vision_config": { /* Vision encoder — ViT */ },
  "image_token_id": 248056,
  "video_token_id": 248057,
  "vision_start_token_id": 248053,
  "vision_end_token_id": 248054
}
```

**Rule:** As with other Qwen-VL models, the authoritative LLM decoder params live under `text_config`, not the root. Root `model_type` is `qwen3_5` (multimodal wrapper); `text_config.model_type` is `qwen3_5_text`. Vision params are under `vision_config`.

If the model is **text-only** (pipeline_tag `text-generation`), the config may be flat with `model_type: qwen3_5_text` directly at root — no nesting needed.

## Key Architecture Fields

### Layer Type Interleaving

The most distinctive field is `layer_types` — an explicit array of length `num_hidden_layers` specifying each layer's attention class:

```json
"layer_types": ["linear_attention", "linear_attention", "linear_attention", "full_attention", ...]
```

**Pattern:** 3× linear_attention followed by 1× full_attention, repeated 8 times = 32 layers total.  
**`full_attention_interval`:** Alternative shorthand that also encodes the 4 (every 4th layer is full attention).  
**`mlp_only_layers`:** Empty array `[]` — no pure-MLP layers in this config.

### Linear Attention (SSM-style) Parameters

```json
"linear_conv_kernel_dim": 4,        // Depthwise conv kernel width in linear-attention layers
"linear_key_head_dim": 128,          // Per-head dimension for linear-attention key
"linear_num_key_heads": 16,          // Number of heads in the linear-attention key space
"linear_num_value_heads": 32,        // Number of heads in the linear-attention value space
"linear_value_head_dim": 128,        // Per-head dimension for linear-attention value
"mamba_ssm_dtype": "float32"         // SSM recurrence precision (float32 for numerical stability)
```

Compared to full-attention layer config:

```json
"num_attention_heads": 16,           // Full-attention query heads
"num_key_value_heads": 4,            // GQA: only 4 KV heads for 16 query heads
"head_dim": 256                      // Per-head dimension for full attention
```

Note the **asymmetry**: full attention uses GQA with a 4:1 KV ratio and larger head_dim (256), while linear attention has more key heads (16) at smaller per-head dim (128) and more value heads (32) at 128.

### Multi-Token Prediction (MTP)

```json
"mtp_num_hidden_layers": 1,          // One MTP head (drafts 1 future token)
"mtp_use_dedicated_embeddings": false // Shares embeddings with main model
```

MTP enables speculative decoding — the model predicts the next *N* tokens as a draft head, which the main model verifies in parallel. `mtp_num_hidden_layers: 1` means a single MTP head drafting 1 future token. GGUF variants frequently ship separate files with `-MTP-` in the filename containing this head.

### Long Context via YaRN + MRoPE

```json
"max_position_embeddings": 1048576,  // 1M context window
"rope_parameters": {
    "rope_type": "yarn",
    "factor": 4.0,                    // 4× extension beyond native
    "original_max_position_embeddings": 262144,  // native rope limit
    "mrope_interleaved": true,        // Multimodal RoPE: spatial positions interleaved
    "mrope_section": [11, 11, 10],    // Token dimensions for temporal/height/width positions
    "rope_theta": 10000000
},
"partial_rotary_factor": 0.25         // Only 25% of head dim gets rotary embedding
```

`mrope_section: [11, 11, 10]` allocates 11 dims for temporal position, 11 for height, 10 for width — the standard Qwen-VL multimodal 3D-RoPE scheme. The 4× YaRN factor extends the 262k native rope to 1M.

### Other Specs

| Field | Value | Note |
|-------|-------|------|
| `hidden_size` | 4096 | Embedding dimension |
| `intermediate_size` | 12288 | 3× hidden (standard) |
| `num_hidden_layers` | 32 | Transformer depth |
| `hidden_act` | `silu` | SwiGLU activation |
| `vocab_size` | 248320 | Tokenizer size |
| `rms_norm_eps` | 1e-6 | Normalization epsilon |
| `tie_word_embeddings` | false | Embeddings + LM head not tied |
| `use_cache` | true | KV-cache enabled |
| `attention_dropout` | 0.0 | No dropout |
| `attention_bias` | false | No bias in QKV projections |
| `attn_output_gate` | true | Gated attention output |

## Vision Encoder Config

```json
"vision_config": {
    "model_type": "qwen3_5_vision",
    "depth": 27,                    // 27-layer ViT
    "hidden_size": 1152,            // Embedding dim
    "intermediate_size": 4304,
    "num_heads": 16,
    "patch_size": 16,
    "temporal_patch_size": 2,       // 2-frame temporal aggregation
    "spatial_merge_size": 2,        // 2×2 spatial merging
    "num_position_embeddings": 2304, // Max patches
    "out_hidden_size": 4096,        // Projector output = text hidden_size
    "in_channels": 3,
    "hidden_act": "gelu_pytorch_tanh",
    "initializer_range": 0.02
}
```

The vision tower outputs embeddings at `hidden_size=4096` matching the LLM's `hidden_size=4096` — no dimension bridge needed beyond the existing ViT-to-LLM projector.

## How to Identify Hybrid Architecture

1. Check `text_config.layer_types` exists and contains `"linear_attention"` entries
2. Check for `linear_*` fields under `text_config` — `linear_conv_kernel_dim`, `linear_key_head_dim`, etc.
3. Check for `mamba_ssm_dtype`
4. Check `full_attention_interval` as a shorthand for the interleaving pattern
5. Check `mtp_num_hidden_layers` for MTP draft heads
6. For context length, check `rope_parameters.rope_type == "yarn"` with the scaling factor

## GGUF-Specific Notes

- GGUF exports preserve the `layer_types` array and MTP head if `mtp_num_hidden_layers > 0`
- MTP-enabled GGUF files usually have `-MTP-` in the filename (e.g., `Qwythos-9B-1M-MTP-Q4_K_M.gguf`)
- The vision mmproj (`mmproj-*.gguf`) is interchangeable between any Qwen3.5-9B-based GGUF — these are the CLIP-style vision encoder exported via `llama.cpp`'s multimodal projection export
- The `llama.cpp` context size `-c` can be set up to `max_position_embeddings` (1M) but practical single-GPU limits are 256k–512k

## Qwen3.6-27B Specific Architecture

Drawn from the official model card at [Qwen/Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B). Unlike Qwen3.5-9B (32 layers, hidden_size=4096), the 27B variant scales up significantly:

| Field | Qwen3.5-9B | Qwen3.6-27B | Note |
|-------|-----------|-------------|------|
| `num_hidden_layers` | 32 | **64** | Double the depth |
| `hidden_size` | 4096 | **5120** | Wider embeddings |
| `intermediate_size` | 12288 | **15360** | 3× hidden (same ratio) |
| `vocab_size` | 248320 | 248320 | Same tokenizer |
| `max_position_embeddings` | 1,048,576 | 1,048,576 | Same 1M context |

### Layer Composition

The Qwen3.6-27B model card describes its layer layout explicitly:

```
16 × (3 × (Gated DeltaNet → FFN) → 1 × (Gated Attention → FFN))
```

Breaking this down:
- **64 layers total** — 48 Gated DeltaNet (linear-attention/SSM) layers + 16 Gated Attention (full-attention) layers
- **Gated DeltaNet** is the specific linear-attention variant used — a gated version of DeltaNet that uses a delta rule for state updates, distinct from Mamba or Mamba2. This is a more specific name than the generic `linear_attention` label used in Qwen3.5-9B's config, though both serve the same hybrid role.
- **Gated Attention** refers to the full-attention layers with `attn_output_gate: true` — a learned gating mechanism on the attention output projection (present in Qwen3.5-9B too).
- Each attention layer (whether DeltaNet or full-attention) is followed by a standard SwiGLU FFN.
- The pattern cycles: 3 DeltaNet layers, 1 full-attention, repeat 16 times.

### Dimensions

- `num_attention_heads`: 20 (full-attention GQA heads)
- `num_key_value_heads`: 5 (4:1 GQA ratio — same 4:1 as Qwen3.5-9B's 16:4)
- `head_dim`: 256 (per-head dimension for full attention)
- Linear-attention layer specific dims for the 27B variant have not been confirmed from published config; derive from Qwen3.5-9B ratios as baseline.

### Vision Encoder

- 27-layer ViT (same depth as Qwen3.5-9B)
- `hidden_size`: 1152
- `out_hidden_size`: **5120** (matches 27B hidden_size, not 4096 like the 9B)
- `num_heads`: 16
- `patch_size`: 16
- `temporal_patch_size`: 2
- `spatial_merge_size`: 2

### Implications for Deep-Dive Research

When evaluating a Qwen3.6-27B based fine-tune:
- The 64-layer depth means GGUF files are ~2× larger per-quant than 32-layer models at the same quantization — expect ~16 GB for Q4 vs ~8 GB for a 9B.
- The 5120 hidden dimension means the KV cache per token is larger: ~2.5 MB per token at full attention vs ~1.6 MB for 4096-dim models (at same bit-width).
- Fine-tunes that claim "Qwen3.6-27B base" should be compared against the baseline numbers above; the 0.647 ARC-C from the Qwen3.6 official eval is the reference.
- MTP (Multi-Token Prediction) is a separate optional head — not all GGUF variants include it. MTP files have `-MTP-` in the filename.

## Related Models Using This Architecture

- **Qwen/Qwen3.5-9B** ([Hub](https://huggingface.co/Qwen/Qwen3.5-9B)) — official base, 32-layer 9B
- **Qwen/Qwen3.5-14B** — larger variant, same hybrid pattern
- **Qwen/Qwen3.6-27B** ([Hub](https://huggingface.co/Qwen/Qwen3.6-27B)) — 64-layer 27B with Gated DeltaNet
- **Qwen/Qwen3.6-35B-A3B** — MoE variant of Qwen3.6 (35B total, 3B active)
- **empero-ai/Qwythos-9B-Claude-Mythos-5-1M** — Claude Mythos reasoning fine-tune of Qwen3.5-9B
- **bottlecapai/ThinkingCap-Qwen3.6-27B** — fine-tune of Qwen3.6-27B
- **DavidAU/Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF** — multi-stage abliterated fine-tune of Qwen3.6-27B; first open 27B model to exceed 700 ARC-C (0.711 in 8-bit, 0.701 in 4-bit). Multi-collaborator methodology: DavidAU (fine-tunes, multi-stage merges), Nightmedia (benchmarking), TeichAI (Polaris dataset), arman0e (Fable traces), trohrbaugh (Heretic abliteration). Ships 25+ GGUF quants including MTP-enabled variants.

### DavidAU Fine-Tune Pattern

DavidAU's models (Qwen3.5-9B-The-Defiant, Qwen3.6-27B-Fable-Fusion) follow a consistent methodology worth recognizing in trend analysis:

1. **Multi-stage pipeline**: multiple sequential fine-tunes on different datasets, not a single SFT run
2. **Multi-merge**: the final model is a weighted merge of fine-tune checkpoints
3. **Heretic abliteration**: refusal vectors removed pre-fine-tuning (applied to base model first)
4. **"No benchmaxing"**: explicit claim that benchmark-specific overfitting was avoided
5. **NEO IMATRIX quantization**: claims 2-4% accuracy improvement over standard GGUF quants via modified importance matrices
6. **MTP support**: optional Multi-Token Prediction heads in separate GGUF files, with MTP tensors stored at Q8_0
7. **Consumer hardware**: fine-tuned via Unsloth on consumer GPUs (documented methodology)
8. **Output tensor modification**: the final 10-20% of the output projection is stored at full FP16 precision in all quants

When researching these models, expect benchmark comparison tables embedded in the README body (not in separate `.eval_results/` files), often using text-block format with multiple model comparisons (arc/c, arc/e, boolq, hswag, obkqa, piqa, wino columns).
