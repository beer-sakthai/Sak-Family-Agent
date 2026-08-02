# GLM-5.2 Architecture Reference

Discovered during HF trending deep dive (2026-07-23 tick). Zhipu AI's flagship 744B-A40B MoE model.

## Quick Specs

| Property | Value |
|----------|-------|
| Total params | 744B |
| Active per token | ~40B |
| Layers | 78 |
| Hidden size | 6144 |
| Intermediate (dense) | 12288 |
| Attention heads | 64 (full, no GQA reduction — 64 KV heads) |
| Head dim | 192 |
| QK dimension | 256 (192 nope + 64 rope) |
| V dimension | 256 |
| Q LoRA rank | 2048 |
| KV LoRA rank | 512 |
| Routed experts | 256 |
| Shared experts | 1 |
| Experts per token | 8 |
| MoE intermediate | 2048 |
| Router | `noaux_tc` (auxiliary-loss-free), sigmoid scoring, routed_scaling_factor=2.5 |
| Context | 1,048,576 (1M tokens) |
| Precision | BF16 |
| License | MIT |
| MTP layers | 1 (Multi-Token Prediction for speculative decoding) |

## Key Innovations

### IndexShare (arXiv:2603.12201)
Reuses the same sparse-attention indexer across every 4 layers (`index_topk_freq=4`), reducing per-token FLOPs by 2.9× at 1M context.
- 32 index heads, each with `index_head_dim=128`
- `index_topk=2048` — selects top-k KV positions per query
- `index_skip_topk_offset=3` — skip first N KV positions from top-k selection
- `index_share_for_mtp_iteration=True` — also shared with the MTP head
- The `indexer_types` array (78 entries) maps each layer to its indexer type (shared group)

### DSA (DeepSeek Sparse Attention)
Uses grouped sparse attention where each group of 4 layers shares one indexer, drastically reducing the cost of the attention mechanism at long contexts.

### Architecture Config Mapping (from config.json)

When reverse-engineering MoE configs from HF `config.json`, look for these DSA-specific fields:

| Config Key | Meaning |
|-----------|---------|
| `index_topk` | Number of KV positions each query attends to (2048) |
| `index_topk_freq` | How often the indexer is recomputed (4 = every 4th layer) |
| `index_head_dim` | Dimension of indexer attention heads (128) |
| `index_n_heads` | Number of indexer heads (32) |
| `kv_lora_rank` | KV compression rank (512) |
| `q_lora_rank` | Q compression rank (2048) |
| `ep_size` | Expert parallelism group size (1) |
| `moe_layer_freq` | Every layer is MoE (1) |
| `first_k_dense_replace` | First 3 layers are dense (3) |
| `n_group` / `topk_group` | Expert grouping (1 group, 1 selected) |
| `scoring_func` | Router scoring function (`sigmoid`) |
| `norm_topk_prob` | Normalize top-k probabilities (True) |

## Benchmark Highlights

| Benchmark | Score |
|-----------|-------|
| HLE (text-only) | 40.5 |
| HLE (w/ tools) | 54.7 |
| AIME 2026 | 99.2 |
| GPQA-Diamond | 91.2 |
| SWE-bench Pro | 62.1 |
| Terminal-Bench 2.1 | 81.0 |
| FrontierSWE Dominance | 74.4 |
| DeepSWE | 46.2 |
| MCP-Atlas (Public) | 76.8 |
| CritPt | 20.9 |
| Tool-Decathlon | 48.2 |

## Deployment Frameworks
- SGLang v0.5.13.post1+
- vLLM v0.23.0+
- Transformers v5.12+
- KTransformers v0.5.12+
- Unsloth v0.1.47-beta+
- Ascend NPU: vLLM-Ascend, xLLM, SGLang
