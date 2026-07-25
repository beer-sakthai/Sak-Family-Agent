# HF Learnings Log — DeepSeek V4 Transformers Implementation

## 2026-07-25: hf-transformers-deepseek-v4-deep-dive — Architecture Complete Reference (Topic #358)

### Summary
Deep dive into the **DeepSeek V4** architecture as implemented in Transformers 5.14.1 (`models/deepseek_v4/`). DeepSeek V4 is a Mixture-of-Experts (MoE) decoder-only transformer introducing three novel attention mechanisms (Sliding, Compressed Sparse CSA, Heavily Compressed HCA), a Lightning Indexer for sparse attention routing, Manifold-Constrained Hyper-Connections (mHC), Grouped Output Projection, and Hash-MoE bootstrapping. Models V4-Flash (43L, 64H, 256E) and V4-Pro are defined.

### Key Findings
- **Three attention types**: Sliding (local window 128), CSA (compress_rate=4 with Lightning Indexer), HCA (compress_rate=128 without indexer). Per-layer schedule: 2× HCA bootstrap + CSA/HCA interleave.
- **Lightning Indexer**: Scaled-down compressor at index_head_dim=128, scores queries with `Σ_h w_{t,h} · ReLU(q_{t,h} · K^IComp_s)`, keeps top-512 entries. Reduces compressed attention cost from `seq_len/4` to 512.
- **CSA's two-series overlap**: Ca (previous window) + Cb (current window) = 2m effective width, softmax-gated with position bias. Adjacent windows share state via overlap_kv cache.
- **Grouped Output Projection**: Split heads into g=8 (Flash) or 16 (Pro) groups, each projected to o_lora_rank=1024, mixed to hidden_size.
- **Hash-MoE bootstrap**: First 3 layers route via frozen `tid2eid[input_ids]` (no learned router), rest use standard top-6-of-256 routed MoE with sqrtsoftplus scoring.
- **Interleaved Partial RoPE**: qk_rope_head_dim=64 (Flash) out of 512 head_dim. Two rope types: "main" (θ=10000) for sliding; "compress" (θ=160000, YaRN optional) for CSA/HCA.
- **mHC with Sinkhorn-Knopp**: 20 iterations t_max for doubly-stochastic projection of residual mapping.
- **Shared-KV MQA**: Single KV head (num_key_value_heads=1) broadcast to all query heads.
- **Expert Parallelism only**: No TP — MoE parallelism on gate/router, grouped-GEMM on experts, attention replicated.

## 2026-07-25: Deepening — Source Code Analysis of Transformers 5.14.1 `modular_deepseek_v4.py`

### Summary
Second-pass deepening through direct analysis of the implementation source (1207 lines in `modular_deepseek_v4.py`, 324 lines in `configuration_deepseek_v4.py`). Covers the runtime architecture, cache layer internals, compressor pipeline, HyperConnection mechanics, and key limitations not apparent from the config surface alone.

### Source File Layout
```
modular_deepseek_v4.py (1207 lines)
├── apply_rotary_pos_emb()           — Interleaved RoPE on trailing rope slice
├── DeepseekV4RMSNorm                — Passthrough (aliases DeepseekV3RMSNorm)
├── DeepseekV4UnweightedRMSNorm      — RMSNorm without learned weight
├── DeepseekV4RotaryEmbedding        — Multi-layer-type rotary (Laguna pattern)
│   └── Uses rope_parameters keys ("main"/"compress") not layer_types
├── DeepseekV4HCACache               — HCA sliding-window + compressor buffer
├── DeepseekV4CSACache(HCACache)     — CSA adds indexer entries + overlap state
├── DeepseekV4GroupedLinear          — Block-diagonal grouped linear
├── DeepseekV4HCACompressor          — HCA: compress_rate=128, non-overlapping
├── DeepseekV4IndexerScorer          — Lightning Indexer scoring head
├── DeepseekV4Indexer                — CSA indexer: top-k sparse routing
├── DeepseekV4CSACompressor          — CSA: compress_rate=4, two-series overlap
├── DeepseekV4Attention              — Main attention module
│   ├── Q: LoRA-proj (q_a → RMSNorm → q_b → norm → RoPE)
│   ├── KV: single kv_proj (MQA) → norm → RoPE
│   ├── Shared-KV: K == V throughout
│   ├── Compressor (CSA/HCA) attaches extra KV entries after sliding cache
│   ├── Output: conjugate RoPE (-sin) then grouped projection
│   └── Per-head learnable attention sink (sinks parameter)
├── DeepseekV4HyperConnection        — mHC mapping (Manifold-Constrained)
├── DeepseekV4HyperHead              — Block-start HC head for parallel streams
├── DeepseekV4MLP(LlamaMLP)          — Shared expert MLP
├── DeepseekV4Experts                — Grouped-GEMM MoE experts
├── DeepseekV4TopKRouter             — Standard top-k routed MoE
├── DeepseekV4HashRouter             — Frozen tid2eid[input_ids] lookup routing
├── DeepseekV4SparseMoeBlock         — Routes through hash or topk per layer
├── DeepseekV4DecoderLayer           — Block: attn + MoE with mHC at both sites
├── DeepseekV4PreTrainedModel        — Weight init, eager-only enforcement
├── DeepseekV4Model(LlamaModel)      — Embed + layers + norm
└── DeepseekV4ForCausalLM            — LM head for text generation
```

### 1. Attention Pipeline (DeepseekV4Attention, L648–767)

The attention module has a **LoRA-style Q projection** for parameter efficiency:

1. **Q path**: `hidden → q_a_proj (4096→1024) → RMSNorm → q_b_proj (1024→32768) → reshape [B,H,S,D] → UnweightedRMSNorm → apply_rotary_pos_emb(cos, sin)`
2. **KV path**: `hidden → kv_proj (4096→512) → RMSNorm → reshape [B,1,S,512] → apply_rotary_pos_emb(cos, sin)`
3. **Cache**: Shared K=V sliding window (128 tokens) via `past_key_values.update(kv, kv, layer_idx)`
4. **Compressed KV**: If compressor exists (CSA/HCA), attach compressed entries after sliding cache
5. **Attention mask**: Extended with `block_bias` from compressor (causality over compressed slots)
6. **Attention call**: Uses `ALL_ATTENTION_FUNCTIONS` interface with `s_aux=sinks` for attention sinks
7. **Output**: `attn_output → apply_rotary_pos_emb(cos, -sin)` (conjugate rotation to undo KV RoPE) → reshape groups → `o_a_proj` (grouped) → `o_b_proj` → hidden

Key insight: **Shared-KV MQA** means `kv_proj` outputs a SINGLE head (head_dim=512) which is broadcast to all 64 query heads via `repeat_kv`. The same tensor serves as both key and value — the cache tracks `keys == values`.

### 2. Cache Architecture

#### DeepseekV4HCACache (L134–216) — HCA cache
- Inherits `DynamicSlidingWindowLayer` for the 128-token sliding K=V buffer
- Adds per-`name` dicts for state keyed by `"compressor"`:
  - `buffer_kv[name]` / `buffer_gate[name]`: Source tokens between windows
  - `compressed_kv[name]`: Running list of emitted compressed entries
  - `entry_count[name]`: Number of compressed entries emitted (for position tracking)
- `store_compression_weights(name, kv, gate)`: Appends to buffer, returns window-aligned prefix + leftover
- `update_compressor_states(name, compressed)`: Appends new entries, bumps count

#### DeepseekV4CSACache (L218–263) — CSA cache
- Extends HCACache with `"indexer"` entries in all state dicts
- Adds `overlap_kv[name]` / `overlap_gate[name]` for two-series overlap
- `update_overlap_state(name, chunk_kv, chunk_gate, head_dim)`:
  - Ca (slice `[:, head_dim]`) from previous call is read as prior overlap
  - Current call's Ca is persisted for next call
  - Only Ca is consumed — Cb is already folded into emitted compressed entry

#### Cache State Machine
```
prefill (no past_key_values)
  → stateless mode: compress every complete window, discard remainder
  → returns compressed entries for prefill attention

decode (past_key_values present)
  → store_compression_weights: accumulate buffer until full window
  → when full: emit one compressed entry, append to compressed_kv
  → returning compressed entries for decode attention
```

### 3. Compressor Pipeline

#### HCA Compressor (DeepseekV4HCACompressor, L298–379)
- Compress rate m'=128 (configurable via `compress_rates["heavily_compressed_attention"]`)
- Each closed window produces one entry via:
  `C^{Comp}_i = Σ_j softmax(Z_j + B)_j ⊙ C_j`  (eqs. 20–23)
- Position bias `position_bias` (learned, [128, 512]) added to gate before softmax
- RoPE applied at **deterministic** absolute position `i * compress_rate + first_window_position`
- Returns running list of ALL compressed entries since start
- `block_bias` masks entries not yet visible causally: `entry_index >= (position_id + 1) // compress_rate`

#### CSA Compressor (DeepseekV4CSACompressor, L525–646)
- Compress rate m=4 (configurable, default 4)
- `kv_proj` outputs 2× features: `[Ca | Cb]` (two independent series in one tensor)
- Two-series overlap: pooled_entry = softmax-gated(Ca_prev + Cb_curr + position_bias)
- Effective width = 2m = 8, stride = m = 4
- Also produces indexer compressed KV at `index_head_dim=128` for the Lightning Indexer

### 4. Lightning Indexer (DeepseekV4IndexerScorer + DeepseekV4Indexer, L382–523)

**DeepseekV4IndexerScorer** (L382–395):
- Projects hidden states to `index_n_heads` (64) weights
- Score formula: `Σ_h w_{t,h} · ReLU(q_{t,h} · K^IComp_s) * (index_head_dim)^-0.5`
- Returns per-position scores over compressed entries

**DeepseekV4Indexer** (L398–523):
- Own compressor at `index_head_dim=128` (separate `kv_proj_index`, `gate_proj_index`, `position_bias_index`)
- Produces `compressed_kv_index` with same window structure as main compressor
- Indexer scorer computes scores, keeps top-`index_topk` (512) entries
- Indexer scores and gating weights undergo Sinkhorn normalization
- Returns **gated sparse compressed KV** — only top-k entries survive

### 5. Manifold-Constrained Hyper-Connection (DeepseekV4HyperConnection, L769–845)

The mHC replaces the standard residual connection with a manifold projection:

**Architecture**:
- Input: `hc_mult` parallel residual streams `[B, S, hc_mult, D]`
- `input_norm`: UnweightedRMSNorm on flattened `[B, S, hc_mult*D]`
- `fn`: Linear mapping `(hc_mult*D) → (2 + hc_mult) * hc_mult` — produces pre, post, comb logits
- `base` + `scale`: Learned bias and scale for each output

**Forward (L817–845)**:
1. Normalize and project: `F.linear(norm(hidden_streams.flatten()), fn)` → split into pre, post, comb
2. `pre = σ(pre_w * pre_scale + pre_b) + eps` — collapse weights for input to sublayer
3. `post = 2 · σ(post_w * post_scale + post_b)` — block-output placement [0, 2]
4. `comb = softmax(comb_logits, dim=-1) + eps` → Sinkhorn-Knopp iteration (20× row/col normalize)
5. `collapsed = (pre · hidden_streams).sum(dim=2)` — weighted sum of hc_mult streams
6. Returns `(post, comb, collapsed)`

**Decoder Layer usage (L1001–1025)**:
```
hidden_states → attn_hc → post, comb, collapsed
attn_output = self_attn(layernorm(collapsed))
hidden_states = post * attn_output + comb.T @ hidden_streams

hidden_states → ffn_hc → post, comb, collapsed
mlp_output = mlp(layernorm(collapsed))
hidden_states = post * mlp_output + comb.T @ hidden_streams
```

Key: `comb` is consumed **transposed** — indexed as `comb.T @ residual` (sum over first hc axis), because Sinkhorn produces a non-symmetric doubly-stochastic matrix.

### 6. Config-Source Mapping (configuration_deepseek_v4.py, 324 lines)

| Config Field | Type | Default (Flash) | Purpose |
|---|---|---|---|
| `layer_types` | `list[str]` | 2×HCA + interleave | Per-layer attention schedule |
| `compress_rates` | `dict` | CSA=4, HCA=128 | Compress ratio per type |
| `mlp_layer_types` | `list[str]` | 3×hash_moe + rest moe | Per-layer MoE schedule |
| `hc_mult` | `int` | 4 | mHC expansion factor |
| `hc_sinkhorn_iters` | `int` | 20 | Sinkhorn-Knopp iterations |
| `o_groups` | `int` | 8 (Flash) / 16 (Pro) | Grouped output projection groups |
| `o_lora_rank` | `int` | 1024 | Per-group intermediate dim |
| `index_n_heads` | `int` | 64 | Indexer query heads |
| `index_head_dim` | `int` | 128 | Indexer head dim |
| `index_topk` | `int` | 512 | Kept compressed entries per query |
| `qk_rope_head_dim` | `int` | 64 (computed) | RoPE channels per head |
| `sliding_window` | `int` | 128 | Local window size |
| `scoring_func` | `str` | `sqrtsoftplus` | Router activation |
| `norm_topk_prob` | `bool` | True | Normalize top-k probs |
| `routed_scaling_factor` | `float` | 1.5 | MoE scaling factor |
| `rope_parameters` | `dict` | `{main: {default}, compress: {yarn}}` | Per-type rope config |

**Legacy config compatibility** (via `__post_init__`):
- `compress_ratios` (V3-style per-layer ints) → converted to `layer_types`
- `compress_rate_csa` / `compress_rate_hca` → folded into `compress_rates`
- `num_hash_layers` → converted to `mlp_layer_types`
- `qk_rope_head_dim` → `partial_rotary_factor = qk_rope_head_dim / head_dim`

### 7. Implementation Limitations

| Limitation | Reason |
|---|---|
| **Eager-only** | head_dim=512 exceeds FlashAttention 2/3 cap of 256 |
| **No Tensor Parallelism** | V4 ships EP-only; MQA + single KV head make TP attention sharding non-trivial |
| **Sinkhorn in fp32** | mHC projection runs in float32 regardless of input dtype |
| **In-memory compressed KV** | Compressed KV grows unbounded with sequence length (no eviction) |
| **Single KV head** | Shared-KV MQA means KV cache is 1/64 of Q cache — extreme memory saving for attention but limits representational capacity |

### Architecture Sources
- Transformers 5.14.1 source: `models/deepseek_v4/modular_deepseek_v4.py` (1207 lines)
- Configuration: `models/deepseek_v4/configuration_deepseek_v4.py` (324 lines)
- Inherits from: `DeepseekV3RMSNorm`, `MixtralTopKRouter`/`MixtralExperts`, `LlamaMLP`, `LagunaRotaryEmbedding`, `LlamaModel`, `MixtralForCausalLM`

