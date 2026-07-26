# Motif-3-Beta — GDLA, PolyNorm, MHC & MLA-Style KV Compression

_Model: `Motif-Technologies/Motif-3-Beta` — Motif Technologies' in-house 314B MoE with proprietary attention and activation_

## Architecture Overview

Motif-3 is a **fully in-house design** — not a fork or reparameterization of existing open architectures. It combines three proprietary components:

- **GDLA (Grouped Differential Latent Attention)** — custom attention mechanism
- **Grouped PolyNorm activation** — polynomial normalization per expert
- **Modified mHC (Multi-Head Convolution)** — convolutional processing

## Config — Flat Text-Only LLM (No Multimodal Nesting)

Unlike multimodal models that nest decoder config under `text_config`/`language_config`, Motif-3 is a **pure text-generation LLM** (`pipeline_tag: text-generation`) with all architecture params **at the root** of `config.json`:

### Scale & MoE

| Field | Value | Notes |
|-------|-------|-------|
| `total params` | ~314B | BF16 safetensors, no I32 quant — FP16-native |
| `active per token` | ~13B | 384 experts × top-8 + 1 shared |
| `num_hidden_layers` | 53 | Transformer depth |
| `hidden_size` | 4,096 | Embedding dim |
| `intermediate_size` | 12,288 | Dense FFN dimension |
| `moe_intermediate_size` | 1,280 | Per-expert FFN dim |
| `num_experts` | 384 | Routed experts |
| `num_shared_experts` | 1 | Shared expert (always active) |
| `experts_top_k` | 8 | Activated per token |
| `interleave_moe_layer_step` | 1 | Every layer is MoE (no alternating dense/MoE) |
| `n_dense_first_layers` | 2 | First 2 layers are dense FFN before MoE starts |

### MoE Routing

| Field | Value | Notes |
|-------|-------|-------|
| `score_func` | `sigmoid` | Routing score activation (vs softmax in many MoEs) |
| `route_norm` | `true` | Normalize routing scores |
| `route_scale` | 2.0 | Post-normalization scaling factor |
| `score_before_experts` | `false` | Apply score after (not before) expert compute |
| `load_balance_coeff` | 0.0001 | Very weak load-balance auxiliary loss |
| `router_aux_loss_coef` | 0.0 | No auxiliary loss — routing relies on sigmoid + norm |
| `output_router_logits` | `false` | Don't output logits during forward pass |
| `diff_v2` | `true` | Differential routing v2 enabled |

### Attention — GDLA

| Field | Value | Notes |
|-------|-------|-------|
| `attention_cls` | `gdla` | **Grouped Differential Latent Attention** — not softmax |
| `elementwise_attn_output_gate` | `true` | Gating on attention output (element-wise) |
| `headwise_attn_output_gate` | `false` | Not head-wise gated |
| `num_attention_heads` | 80 | Query heads |
| `num_key_value_heads` | 16 | KV heads (5:1 GQA ratio) |
| `head_dim` | 192 | Total per-head dimension |
| `qk_rope_head_dim` | 64 | Dim alloc for rotary position (RoPE) |
| `v_head_dim` | 128 | Dim alloc for value (non-RoPE) |
| `k_ratio` | 1 | KV compression ratio |
| `q_lora_rank` | 1,024 | Query low-rank projection (MLA-style) |
| `kv_lora_rank` | 512 | KV low-rank projection (MLA-style) |

**Key insight:** GDLA is not standard softmax attention. The presence of `q_lora_rank`+`kv_lora_rank` suggests MLA-style latent KV compression (like DeepSeek V2/V3), but with `attention_cls: gdla` indicating a differential/linear attention variant rather than the standard MLA dot-product. The `elementwise_attn_output_gate: true` adds an output gating mechanism per element — likely stabilizing the differential attention mechanism.

### Sliding Window

| Field | Value | Notes |
|-------|-------|-------|
| `use_sliding_window` | `true` | Active |
| `sliding_window` | 128 | Local window size |
| `sliding_window_pattern` | `interleave` | Interleaved every N layers |
| `sliding_window_period` | 4 | Every 4th layer uses SWA |
| `max_window_layers` | 9 | Max layers with sliding window |
| `swa_rope_theta` | 10,000 | RoPE theta for SWA layers |

### Long Context

| Field | Value | Notes |
|-------|-------|-------|
| `max_position_embeddings` | 262,144 | 256K native context |
| `original_seq_len` | 4,096 | Base pre-training length |
| `rope_scaling.rope_type` | `yarn` | YaRN scaling |
| `rope_scaling.factor` | 64.0 | 64× extrapolation |
| `rope_scaling.mscale` | 1.0 | No monotonic scaling applied |
| `rope_scaling.beta_fast` | 32.0 | YaRN beta fast |
| `rope_scaling.beta_slow` | 1.0 | YaRN beta slow |
| `rope_theta` | 10,000 | Base RoPE frequency |

### Multi-Head Convolution (mHC)

| Field | Value | Notes |
|-------|-------|-------|
| `mhc_enabled` | `true` | Active |
| `mhc_expansion_rate` | 4 | Channel expansion factor |
| `mhc_identity_init` | `false` | Not identity-initialized |
| `mhc_sinkhorn_iters` | 20 | Sinkhorn normalization iterations |

The mHC module uses Sinkhorn normalization over 20 iterations — suggesting a role in balancing/exchanging information across tokens or experts, potentially replacing or augmenting the MoE router's auxiliary loss.

### Activation & Normalization

| Field | Value | Notes |
|-------|-------|-------|
| `hidden_act` | `poly_norm` | **PolyNorm** — polynomial normalization activation |
| `polynorm_output_scale` | 0.5 | Output scaling factor |
| `polynorm_output_scale_per_layer` | `{}` | Empty = uniform across layers |
| `polynorm_bias_clamp` | 0.5 | Bias clipping range |
| `hidden_clamp` | 1,000,000 | Max hidden value clamp |
| `rms_norm_eps` | 1e-05 | Pre-norm epsilon |
| `initializer_range` | 0.02 | Weight init range |

### Multi-Token Prediction (MTP)

| Field | Value | Notes |
|-------|-------|-------|
| `num_nextn_predict_layers` | 1 | One MTP head |

The MTP head enables training on multiple future tokens per position — a technique also used in DeepSeek-V3 and others.

### Vocabulary & Misc

| Field | Value | Notes |
|-------|-------|-------|
| `vocab_size` | 220,160 | Large multilingual vocab (EN + KO) |
| `tie_word_embeddings` | `false` | Separate input embed + LM head |
| `dtype` | `bfloat16` | Native precision |
| `use_cache` | `true` | KV cache enabled |
| `eos_token_id` | 0 | Single EOS (generation_config lists [0, 3, 6]) |

## Benchmark

| Metric | Score |
|--------|-------|
| **AAII** (Artificial Analysis Intelligence Index) | **44** |

Source: [Artificial Analysis](https://artificialanalysis.ai/). No further per-task benchmarks published in the beta model card.

## Serving

- **vLLM** (recommended): Custom Docker image `ghcr.io/motiftechnologies/vllm:v0.20.2-motif3.rc2`
- **Expert parallelism** required: `--enable-expert-parallel`, `--data-parallel-size 8`, `--data-parallel-size-local 8`
- **Quantization**: `modelopt_blockfp8` supported
- **Tested on**: B200, H200 GPUs only
- **HF `.generate`**: Works with `trust_remote_code=True`, but vLLM recommended for production

## License & Access

- **License:** Non-commercial research only (custom terms — commercial use requires written permission)
- **Access:** Open weights, no gate — anyone can download
- **Status:** ⚠️ Beta/preview checkpoint — final release pending

## When to Use This Pattern

Use this reference when researching models where:
- `attention_cls` is NOT one of the standard values (`eager`, `flash_attention_2`, `sdpa`) — indicates a custom attention mechanism
- `q_lora_rank` + `kv_lora_rank` are present at root level (not nested) — MLA-style compression in a text-only LLM
- `hidden_act` is a non-standard value like `poly_norm` — custom activation function
- `mhc_enabled` is present — Multi-Head Convolution module
- `score_func: sigmoid` with `route_norm: true` and `route_scale` — alternative MoE gating without auxiliary loss
- Config is **flat** (all fields at root) despite being a custom architecture — pure text-generation LLM, not multimodal
- `diff_v2: true` + `score_before_experts: false` — differential routing variant
- No `num_experts_per_tok` field but has `experts_top_k` — alternative naming convention for MoE top-k
