# HF Learnings Log

## 2026-07-25: hf-transformers-deepseek-v4-deep-dive — DeepSeek V4 Architecture Complete Reference (Topic #358)

### Summary
Deep dive into the **DeepSeek V4** architecture as implemented in Transformers 5.14.1 (`models/deepseek_v4/`). DeepSeek V4 is a Mixture-of-Experts (MoE) decoder-only transformer introducing three novel attention mechanisms (Sliding, Compressed Sparse CSA, Heavily Compressed HCA), a Lightning Indexer for sparse attention routing, Manifold-Constrained Hyper-Connections (mHC), Grouped Output Projection, and Hash-MoE bootstrapping. Models V4-Flash (43L, 64H, 256E) and V4-Pro are defined.

### Key Findings
- **Three attention types**: Sliding (local window 128), CSA (compress_rate=4 with Lightning Indexer), HCA (compress_rate=128 without indexer). Per-layer schedule: 2× HCA bootstrap + CSA/HCA interleave.
- **Lightning Indexer**: Scaled-down compressor at index_head_dim=128, scores queries with `Σ_h w_{t,h} · ReLU(q_{t,h} · K^IComp_s)`, keeps top-512 entries. Reduces compressed attention cost from `seq_len/4` to 512.
- **CSA's two-series overlap**: Ca (previous window) + Cb (current window) = 2m effective width, softmax-gated with position bias. Adjacent windows share state via overlap_kv cache.
- **Grouped Output Projection**: Split heads into g=8 (Flash) or 16 (Pro) groups, each projected to o_lora_rank=1024, mixed to hidden_size. V4-Flash saves from 32768→4096 through 8×4096→1024 intermediates.
- **Hash-MoE bootstrap**: First 3 layers route via frozen `tid2eid[input_ids]` (no learned router), rest use standard top-6-of-256 routed MoE with sqrtsoftplus scoring.
- **Interleaved Partial RoPE**: qk_rope_head_dim=64 (Flash) out of 512 head_dim. Two rope types: "main" (θ=10000, no scaling) for sliding; "compress" (θ=160000, YaRN optional) for CSA/HCA.
- **mHC with Sinkhorn-Knopp**: 20 iterations t_max for doubly-stochastic projection of residual mapping.
- **Shared-KV MQA**: Single KV head (num_key_value_heads=1) broadcast to all query heads.
- **Expert Parallelism only**: No TP — MoE parallelism on gate/router, grouped-GEMM on experts, attention replicated. Lightning Indexer's scorer all-reduced.

### Architecture Sources
- Transformers 5.14.1 source: `models/deepseek_v4/configuration_deepseek_v4.py` (324 lines), `models/deepseek_v4/modular_deepseek_v4.py` (1207 lines)
- Inherits: DeepseekV3RMSNorm, MixtralTopKRouter/MixtralExperts, LlamaMLP (shared expert), LagunaRotaryEmbedding
- License: Apache 2.0 (HuggingFace Inc.)

### Skill Created
`hf-transformers-deepseek-v4-deep-dive/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md.
