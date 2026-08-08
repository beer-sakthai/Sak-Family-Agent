---
name: SakThai-hf-transformers-deepseek-v4-deep-dive
description: "Complete reference on DeepSeek V4 architecture in Transformers 5.14+ — three novel attention mechanisms, Lightning Indexer, Manifold-Constrained Hyper-Connections, Hash-MoE, and full source code layout."
---

# DeepSeek V4 Architecture in Transformers 5.14 — Complete Reference  

## Overview

DeepSeek V4 (`deepseek_v4` model type in Transformers 5.14+) is a Mixture-of-Experts (MoE) decoder-only transformer introducing three novel attention mechanisms, a Lightning Indexer for sparse attention routing, Manifold-Constrained Hyper-Connections (mHC), and Hash-MoE bootstrapping. Two model variants are defined: **V4-Flash** (43 layers, 64 heads, 256 experts) and **V4-Pro** (larger). The implementation ships in `models/deepseek_v4/modular_deepseek_v4.py` (1207 lines) and `configuration_deepseek_v4.py` (324 lines).

## Source Code Layout

```
modular_deepseek_v4.py (1207 lines)
├── apply_rotary_pos_emb()          — Interleaved RoPE on trailing rope slice
├── DeepseekV4RMSNorm               — Inherits DeepseekV3RMSNorm
├── DeepseekV4UnweightedRMSNorm     — RMSNorm without learned weight
├── DeepseekV4RotaryEmbedding       — Multi-type rotary (Laguna pattern)
├── DeepseekV4HCACache              — HCA sliding-window + compressor buffer
├── DeepseekV4CSACache(HCACache)    — CSA: adds indexer & overlap state
├── DeepseekV4GroupedLinear         — Block-diagonal grouped linear
├── DeepseekV4HCACompressor         — HCA: compress_rate=128
├── DeepseekV4IndexerScorer         — Lightning Indexer scoring head
├── DeepseekV4Indexer               — Top-k sparse routing
├── DeepseekV4CSACompressor         — CSA: compress_rate=4, two-series overlap
├── DeepseekV4Attention             — Q: LoRA-proj, KV: shared-MQA, compressor
├── DeepseekV4HyperConnection       — Manifold-Constrained Hyper-Connections
├── DeepseekV4HyperHead             — Block-start HC head
├── DeepseekV4MLP(LlamaMLP)         — Shared expert MLP
├── DeepseekV4Experts               — Grouped-GEMM MoE experts
├── DeepseekV4TopKRouter            — Standard top-k routed MoE
├── DeepseekV4HashRouter            — Frozen tid2eid[input_ids] routing
├── DeepseekV4SparseMoeBlock        — Routes through hash or topk per layer
├── DeepseekV4DecoderLayer          — Block: attn + MoE with mHC at both sites
├── DeepseekV4PreTrainedModel       — Weight init, eager-only enforcement
├── DeepseekV4Model(LlamaModel)     — Embed + layers + norm
└── DeepseekV4ForCausalLM           — LM head for text generation
```

## Three Attention Types

| Type | Compress Ratio | Indexer | Description |
|------|---------------|---------|-------------|
| Sliding Attention | — | No | Local window (128 tokens), plain RoPE (θ=10000), no compressor |
| Compressed Sparse Attention (CSA) | 4 | Yes | Lightning Indexer + compressed KV (2-series overlap window) |
| Heavily Compressed Attention (HCA) | 128 | No | Long-range compressor only, non-overlapping windows |

### Per-Layer Schedule (V4-Flash default)
- First 2 layers: HCA (bootstrap)
- Remaining 41 layers: CSA/HCA interleaved

## Key Innovations — Implementation Details

### 1. Q / KV Projection Pipeline (DeepseekV4Attention, L663–767)

**Q path** (LoRA-style for parameter efficiency):
```
hidden (4096) → q_a_proj → 1024 → RMSNorm → q_b_proj → 32768 → reshape [B,64,S,512] → UnweightedRMSNorm → RoPE
```

**KV path** (Shared-KV MQA: single head broadcast to all 64 Q heads):
```
hidden (4096) → kv_proj → 512 → RMSNorm → reshape [B,1,S,512] → RoPE (same tensor = key AND value)
```

**Output path**:
```
attn_output (32768) → conjugate RoPE (-sin) → reshape [B,S,8,4096] → o_a_proj (grouped: 8×4096→1024) → flatten → o_b_proj (8192→4096)
```

Key insight: **Shared-KV MQA** (`num_key_value_heads=1`) means a single KV head is broadcast to all 64 query heads via `repeat_kv`. The cache tracks `self.keys == self.values` always.

### 2. Compressed KV Pipeline

#### HCA Compressor (DeepseekV4HCACompressor, L298–379)
- Compress rate m'=128. Each window → one compressed entry:
  `C^{Comp}_i = Σ_j softmax(Z_j + B)_j ⊙ C_j`
- Learned `position_bias` added to gate before softmax
- RoPE applied at **deterministic** absolute position `i * compress_rate + first_window_position`
- Returns ALL compressed entries for full long-range history
- **block_bias**: `-inf` for entries where `entry_index >= (position_id + 1) // compress_rate`

#### CSA Compressor (DeepseekV4CSACompressor, L525–646)
- Compress rate m=4. `kv_proj` outputs 2× features: `[Ca | Cb]` (two independent series)
- Two-series overlap: pooled_entry = softmax-gated(Ca_prev + Cb_curr + position_bias)
- Effective width = 2m = 8, stride = m = 4
- Also produces indexer compressed KV at `index_head_dim=128`

### 3. Lightning Indexer (DeepseekV4IndexerScorer + DeepseekV4Indexer, L382–523)

**Scorer** (L382–395):
- Projects hidden states to `index_n_heads` (64) weights
- Score = `Σ_h w_{t,h} · ReLU(q_{t,h} · K^IComp_s) * (index_head_dim)^-0.5`

**Indexer** (L398–523):
- Own compressor at `index_head_dim=128` (separate `kv_proj_index`, `gate_proj_index`)
- Produces `compressed_kv_index` with same window structure as main compressor
- Keeps top-`index_topk` (512) entries per query after Sinkhorn normalization
- Returns gated sparse compressed KV — only top-k entries survive

### 4. Cache Architecture

#### DeepseekV4HCACache (L134–216) — HCA
- Inherits `DynamicSlidingWindowLayer` for 128-token sliding K=V buffer
- Per-`name` dicts: `buffer_kv`, `buffer_gate`, `compressed_kv`, `entry_count`
- `store_compression_weights`: appends to buffer, returns window-aligned prefix + leftover
- `update_compressor_states`: appends new compressed entries, bumps count

#### DeepseekV4CSACache (L218–263) — CSA
- Extends HCACache adding `"indexer"` entries to all state dicts
- `overlap_kv[name]` / `overlap_gate[name]` for two-series window scheme
- `update_overlap_state`: reads Ca (first head_dim) from prior call, persists current Ca for next call

### 5. Manifold-Constrained Hyper-Connection (DeepseekV4HyperConnection, L769–845)

Replaces standard residual with manifold projection:

```
hidden_streams [B,S,hc_mult,D] → flatten → RMSNorm → F.linear(fn) → split[pre, post, comb]

pre = σ(scale * pre_w + base[:H]) + eps        → collapse weights (streams → single)
post = 2·σ(scale * post_w + base[H:2H])         → block-output placement [0,2]
comb = softmax(comb, -1) → Sinkhorn(20 iters)   → doubly-stochastic residual mixer

collapsed = (pre · hidden_streams).sum(dim=2)   → weighted sum into sublayer
```

Applied at both attention and FFN sites:
```python
# Attention site
post, comb, collapsed = attn_hc(hidden_states)
attn_output = self_attn(layernorm(collapsed))
hidden_states = post * attn_output + comb.T @ hidden_streams

# FFN site
post, comb, collapsed = ffn_hc(hidden_states)
mlp_output = mlp(layernorm(collapsed))
hidden_states = post * mlp_output + comb.T @ hidden_streams
```

Key: `comb` consumed **transposed** — Sinkhorn produces non-symmetric matrices so direction matters.

### 6. Grouped Output Projection (DeepseekV4GroupedLinear, L266–296)

- Splits `num_heads * head_dim` (=32768 Flash, =65536 Pro) into g groups
- Per-group: `num_heads*head_dim/g` → `o_lora_rank` (1024)
- Mixer: `groups * o_lora_rank` → `hidden_size`
- Flash: 8 groups of 4096 → 1024, then 8192 → 4096
- Pro: 16 groups of 4096 → 1024, then 16384 → 7168
- Implemented as block-diagonal weight matrix (not independent per-group linears)

### 7. Hash-MoE Bootstrapping

- First 3 MLP layers use `hash_moe`: routes via frozen `tid2eid[input_ids]` lookup — no learned router
- Remaining layers use standard top-k routed MoE (6 experts per token, 256 total)
- Router scoring: `sqrtsoftplus` (default), `softmax`, or `sigmoid`

### 8. Interleaved Partial RoPE (apply_rotary_pos_emb, L46–63)

- `qk_rope_head_dim=64` (Flash) out of 512 head_dim — only 12.5% of channels get RoPE
- Interleaved: one θ per pair (`rope_head_dim // 2` entries), cos/sin expanded via `repeat_interleave(2)`
- Two rope types:
  - `main`: θ=10000, no scaling — for sliding attention
  - `compress`: θ=160000, **optional** YaRN scaling (factor=16) with `attention_factor=1.0` (no mscale)
- Per-head layout: `[nope | rope]` — nope untouched, rope rotated
- Rope-type labels (`main`/`compress`) decoupled from `layer_types` — live in `config.rope_parameters`

### 9. Expert Parallelism Plan

V4 ships EP only (no TP):
- `gate`: `ep_router` — each rank routes independently
- `experts.gate_up_proj`: `grouped_gemm` — sharded along expert axis
- `experts.down_proj`: `grouped_gemm` — sharded along expert axis
- `experts`: `moe_tp_experts` — all-reduce output across ranks
- Attention: stays replicated (single KV head MQA makes TP non-trivial)
- Shared MLP: stays replicated (too small to shard)
- Lightning Indexer: `q_b_proj` + `scorer.weights_proj` colwise, scorer output all-reduced

### 10. Implementation Limitations

| Limitation | Root Cause |
|---|---|
| **Eager-only** | head_dim=512 exceeds FlashAttention 2/3 cap of 256 |
| **No TP** | MQA + single KV head make TP attention sharding non-trivial |
| **Sinkhorn in fp32** | mHC projection always runs in float32 |
| **No eviction** | Compressed KV grows unbounded with sequence length |
| **Single KV head** | Extreme memory savings but limits representational capacity |

## Configuration Highlights

| Parameter | V4-Flash | V4-Pro |
|-----------|----------|--------|
| hidden_size | 4096 | 7168 |
| num_attention_heads | 64 | 128 |
| num_key_value_heads | 1 (MQA) | 1 (MQA) |
| head_dim | 512 | 512 |
| q_lora_rank | 1024 | 1024 |
| n_routed_experts | 256 | 256 |
| num_experts_per_tok | 6 | 6 |
| n_shared_experts | 1 | 1 |
| sliding_window | 128 | 128 |
| max_position_embeddings | 1,048,576 | 1,048,576 |
| vocab_size | 129,280 | 129,280 |
| o_groups | 8 | 16 |
| hc_mult | 4 | 4 |
| index_n_heads | 64 | 64 |
| index_topk | 512 | 512 |

## Sources
- Transformers 5.14.1 source: `models/deepseek_v4/modular_deepseek_v4.py` (1207 lines)
- Configuration: `models/deepseek_v4/configuration_deepseek_v4.py` (324 lines)
- Inherits from: DeepseekV3RMSNorm, MixtralTopKRouter/MixtralExperts, LlamaMLP, LagunaRotaryEmbedding, LlamaModel, MixtralForCausalLM
- License: Apache 2.0 (HuggingFace Inc.)
