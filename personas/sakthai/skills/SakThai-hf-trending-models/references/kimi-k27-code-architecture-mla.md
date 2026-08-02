# Kimi K2.7 Code — MLA + MoE Under Diverging `model_type`s

_Model: `moonshotai/Kimi-K2.7-Code` — Moonshot AI's 1T MoE coding agent_

## Config Nesting Pattern

Root `config.json`:
```json
{
  "model_type": "kimi_k25",
  "text_config": {
    "model_type": "kimi_k2",
    "architectures": ["DeepseekV3ForCausalLM"],
    ...
  },
  "vision_config": {...}
}
```

**Key insight:** The root `model_type` (`kimi_k25`) is the **multimodal wrapper identifier** — not the actual decoder architecture. The authoritative decoder lives in `text_config` where `model_type: kimi_k2` maps to `DeepseekV3ForCausalMachines` (the HF Transformers loader class). This is a third nesting pattern to add to the known list alongside `language_config` (DeepSeek OCR) and plain `text_config` (Qwen-VL family).

## Architecture Specs

| Field | Value |
|-------|-------|
| **Total params** | 1,058,589,420,528 (~1T) |
| **Activated per token** | ~32B |
| **Architecture** | DeepseekV3-style MoE |
| **Layers** | 61 (1 dense, 60 MoE) |
| **Hidden dim** | 7,168 |
| **MoE intermediate per expert** | 2,048 |
| **Routed experts** | 384 |
| **Shared experts** | 1 |
| **Experts per token** | 8 |
| **Scoring function** | Sigmoid (`scoring_func: sigmoid`) |
| **Topk method** | `noaux_tc` (no auxiliary loss for top-k) |
| **Norm topk prob** | True |
| **Routed scaling factor** | 2.827 |
| **Grouped MoE** | `n_group: 1`, `topk_group: 1` (no group-level gating) |

## Attention — Multi-head Latent Attention (MLA)

Kimi K2.7 Code uses **MLA** (Multi-head Latent Attention), the same compressed-KV mechanism from DeepSeek-V2/V3:

| MLA Field | Value |
|-----------|-------|
| `q_lora_rank` | 1,536 |
| `kv_lora_rank` | 512 |
| `qk_nope_head_dim` | 128 |
| `qk_rope_head_dim` | 64 |
| `v_head_dim` | 128 |
| `num_attention_heads` | 64 |
| `num_key_value_heads` | 64 |

MLA compresses the full KV cache into a low-rank latent space via `kv_lora_rank=512`, dramatically reducing per-token KV cache memory compared to standard MHA or even GQA. The `qk_rope_head_dim=64` provides positional-aware queries/keys while `qk_nope_head_dim=128` handles content-based attention without RoPE.

## Vision Encoder — MoonViT

MoonViT is Moonshot's custom vision encoder:
- **Patch size:** 14×14
- **Hidden dim:** via `vt_hidden_size` (nested under `vision_config`)
- **Layers:** via `vt_num_hidden_layers`
- **Attention heads:** via `vt_num_attention_heads`
- **Position embedding:** 3D (height, width, time) — supports video
- **Merge type:** specific to MoonViT architecture
- **Parameters:** ~400M
- **Video support:** `video_attn_type` with temporal position embedding

## Context & Vocabulary

- **Context window:** 262,144 tokens (256K)
- **Vocabulary:** 163,840 tokens
- **RoPE theta:** 50,000 (standard, no long-context extension needed for 256K)
- **Dtype:** bfloat16
- **Tie embeddings:** False (separate input embed and LM head)

## INT4 Quantization (Native)

The Hugging Face release ships with **native INT4 quantization** — not GGUF, but the HF `compressed-tensors` format:

```json
"safetensors": {
  "parameters": {
    "BF16": 43902267888,
    "F32": 23040,
    "I32": 1014687129600,
    "total": 1058589420528
  }
}
```

The 1T I32 byte count reflects packed 4-bit weights stored as int32 containers. Real disk footprint at INT4 is ~quarter of full BF16.

## License

**Modified MIT** — permissive but custom terms. The model is gated (requires agreeing to terms on the Hub before download).

## When to Use This Pattern

Use this reference when researching models where:
- Root `model_type` differs from nested `text_config.model_type` — indicates a multimodal wrapper over a known decoder
- The `text_config` carries both `model_type` AND `architectures` — the latter is the actual Transformers loader
- `n_routed_experts`, `n_shared_experts`, `scoring_func`, `topk_method` are present — MLA + MoE with custom gating
- `q_lora_rank` and `kv_lora_rank` exist — compressed latent attention
- Large I32 in safetensors + `compressed-tensors` tag = native INT4 quantized weights on the Hub
