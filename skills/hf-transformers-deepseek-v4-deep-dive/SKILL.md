# DeepSeek V4 Architecture in Transformers 5.14

> **author:** SakThai  
> **license:** MIT  
> **topic:** `hf-transformers-deepseek-v4-deep-dive`  
> **last-updated:** 2026-07-25  

## Overview

DeepSeek V4 (`deepseek_v4` model type in Transformers 5.14+) is a Mixture-of-Experts (MoE) decoder-only transformer introducing three novel attention mechanisms, a Lightning Indexer for sparse attention routing, Manifold-Constrained Hyper-Connections (mHC), and Hash-MoE bootstrapping. Two model variants are defined: **V4-Flash** (43 layers, 64 heads, 256 experts) and **V4-Pro** (larger). The architecture is implemented as a modular model in Transformers, inheriting from DeepSeek V3 (RMSNorm) and Mixtral (MoE experts, router).

## Three Attention Types

| Type | Compress Ratio | Indexer | Description |
|------|---------------|---------|-------------|
| Sliding Attention | — | No | Local window (128 tokens), plain RoPE (θ=10000), no compressor |
| Compressed Sparse Attention (CSA) | 4 | Yes | Lightning Indexer + compressed KV (2-series overlap window) |
| Heavily Compressed Attention (HCA) | 128 | No | Long-range compressor only, non-overlapping windows |

### Per-Layer Schedule (V4-Flash default)
- First 2 layers: HCA (bootstrap)
- Remaining 41 layers: CSA/HCA interleaved

## Key Innovations

### 1. Lightning Indexer (CSA only)
- Scaled-down compressor at `index_head_dim=128` over same windows as outer CSA
- Scores queries against compressed keys: `Σ_h w_{t,h} · ReLU(q_{t,h} · K^IComp_s)`
- Keeps top-`index_topk` (default 512) entries per query
- Reduces attention from `seq_len/compress_rate` to just `index_topk` entries
- Has its own rotary embedding (same `compress_rope_theta=160000` as outer compressor)

### 2. Compressed Sparse Attention (CSA)
- Compress rate m=4: every 4 tokens → 1 compressed KV entry
- Two-series overlap: Ca (previous window) + Cb (current window) = 2m effective width
- Softmax-gated convex combination with position bias
- Shared-KV: single key/value head broadcast to all query heads (MQA)

### 3. Heavily Compressed Attention (HCA)
- Compress rate m'=128: every 128 tokens → 1 compressed KV entry
- Non-overlapping windows, no indexer
- Simple softmax-gated combination with position bias
- Full compressed history available to attention (no sparse selection)

### 4. Manifold-Constrained Hyper-Connection (mHC)
- `hc_mult`: expansion factor n_hc (always active, Section 2.2)
- Sinkhorn-Knopp iterations t_max (default 20) for doubly-stochastic projection
- Applied to the residual mapping

### 5. Grouped Output Projection
- Splits attention heads into `o_groups` groups (Flash: 8, Pro: 16)
- Per-group: `num_heads*head_dim/g` → `o_lora_rank` (1024) via grouped linear
- Mixer: `groups * o_lora_rank` → `hidden_size`
- V4-Flash: 8 groups of 4096 → 1024, then 8192 → 4096
- V4-Pro: 16 groups of 4096 → 1024, then 16384 → 7168

### 6. Hash-MoE Bootstrapping
- First 3 MLP layers use `hash_moe`: routes via frozen `tid2eid[input_ids]` lookup (no learned router)
- Remaining layers use standard top-k routed MoE (6 experts per token, 256 total)
- Router scoring: `sqrtsoftplus` (default), `softmax`, or `sigmoid`

### 7. Interleaved Partial RoPE
- `qk_rope_head_dim=64` (Flash) or 128 (Pro) out of 512 head_dim
- Remaining `head_dim - rope_head_dim` channels are noPE
- RoPE interleaved: pairs of channels share one θ — no end-to-end duplication
- Two rope types: "main" (θ=10000 for sliding attention) and "compress" (θ=160000 for CSA/HCA, optionally YaRN scaled)

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

## Expert Parallelism Plan
- V4 ships EP only (no TP): MoE parallelism on the gate/router
- Grouped-GEMM on expert gate_up_proj/down_proj
- `moe_tp_experts` wrapper all-reduces expert outputs
- Attention stays replicated (single KV head → repeat_kv works trivially)
- Lightning Indexer: q_b_proj/scorer colwise-sharded, scorer output all-reduced

## Memory Hierarchy
- `DynamicCache` for sliding attention layers
- `DeepseekV4HCACache` for HCA: sliding window + compressed KV buffer + entry count
- `DeepseekV4CSACache` for CSA: same as HCA + indexer entry + overlap state (Ca persistence)

## Sources
- Transformers 5.14 source: `models/deepseek_v4/` (modular architecture)
- License: Apache 2.0 (HuggingFace Inc.)
