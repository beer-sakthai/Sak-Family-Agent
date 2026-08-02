# Baidu Unlimited-OCR Architecture Reference

Discovered during HF trending deep dive (2026-07-23 tick). Baidu's one-shot long-horizon OCR model using Reference Sliding Window Attention (R-SWA). Complements the GLM-5.2 reference as a contrasting pattern: a compact MoE decoder with constant-memory attention instead of sparse attention.

## Quick Specs

| Property | Value |
|----------|-------|
| Pipeline | image-text-to-text |
| License | MIT |
| Stars / Downloads | 2,834 ⭐ / 2.41M ⬇ |
| Vision encoder | CLIP-L-14-224 (1024×24L) + SAM ViT-B (768×12L) — dual encoder |
| Projector | Linear MLP (2048 → 1280) |
| Language decoder | DeepSeekV2-based MoE |
| Decoder layers | 12 |
| Hidden size | 1280 |
| Intermediate (dense) | 6848 |
| MoE intermediate | 896 |
| Attention heads / KV heads | 10 / 10 (full GQA — no reduction) |
| Routed experts | 64 |
| Shared experts | 2 |
| Experts per token | 6 (top-6 via greedy routing) |
| Context length | 32,768 |
| Sliding window | 128 tokens (R-SWA replaces full attention entirely) |
| Precision | BF16 |
| Vocab size | 129,280 |
| Tile tag | `2D` (spatial tiling for high-res input) |
| Candidate resolution | 1024×1024 |
| First K dense layers | 1 |
| Use MLA | false (no Multi-head Latent Attention) |

## Key Innovation: Reference Sliding Window Attention (R-SWA)

R-SWA is the core contribution. It replaces every attention layer in the decoder with a constant-memory sliding window:

- **Constant KV cache** — Unlike standard attention (KV cache grows linearly with output length) or sparse attention (KV cache grows but has sparse access), R-SWA maintains exactly 128 tokens of KV cache throughout decoding. This eliminates the memory wall that makes LLM-based OCR prohibitively expensive for multi-page documents.
- **Why it matters for OCR** — OCR produces long structured output sequences from dense visual input. Standard transformers accumulate GBs of KV cache per page; R-SWA stays flat regardless of page count.
- **General-purpose** — The paper (arXiv 2606.23050) positions R-SWA as a *general-purpose parsing attention mechanism*, applicable to ASR, translation, or any task requiring long-horizon structured output, not just OCR.

### Inference Modes

| Mode | Image Size | Cropping | Use Case |
|------|-----------|----------|----------|
| `gundam` | 640px | Yes (`crop_mode=True`) | Single-image dense OCR |
| `base` | 1024px | No (`crop_mode=False`) | Multi-page / PDF |

## Multimodal Config Nesting Pattern

This model's `config.json` demonstrates the **nested multimodal config pattern** common to image-text-to-text models:

```json
{
  "model_type": "unlimited-ocr",
  "architectures": ["UnlimitedOCRForCausalLM"],
  "vision_config": {
    "model_name": "deeplip_b_l",
    "image_size": 1024,
    "width": {
      "clip-l-14-224": { "heads": 16, "layers": 24, "width": 1024 },
      "sam_vit_b": { "heads": 12, "layers": 12, "width": 768 }
    }
  },
  "projector_config": {
    "input_dim": 2048,
    "n_embed": 1280,
    "projector_type": "linear"
  },
  "language_config": {
    "architectures": ["DeepseekOCRForCausalLM"],
    "num_hidden_layers": 12,
    "hidden_size": 1280,
    "intermediate_size": 6848,
    "moe_intermediate_size": 896,
    "n_routed_experts": 64,
    "n_shared_experts": 2,
    "num_experts_per_tok": 6,
    "num_attention_heads": 10,
    "num_key_value_heads": 10,
    "sliding_window": 128,
    "max_position_embeddings": 32768,
    "vocab_size": 129280,
    "torch_dtype": "bfloat16",
    "use_mla": false
  }
}
```

Key lesson: **The authoritative decoder parameters live under `language_config`, not at the root.** The root-level `config.json` mirrors some fields (like `hidden_size`, `num_hidden_layers`) for convenience, but the nested `language_config` is the source of truth for architectural analysis. For Qwen-VL family models the equivalent key is `text_config`; for LLaVA-style models it may be `text_config` or `llm_config`.

## Sibling Check: Eval Results & Weights

As of the discovery tick:
- **No eval result files** were published under `.eval_results/` in the HF repo
- **No safetensors shards** are stored on the Hub — the model uses a gated/redirect mechanism (downloads still count from usage via Transformers/sglang/vllm pipelines)
- **Custom code** — model uses `trust_remote_code=True` (custom modeling file `modeling_unlimitedocr.py`)

## Training & Lineage

Unlimited-OCR builds on the DeepSeek-OCR lineage, replacing standard attention with R-SWA:
- DeepSeek-OCR → DeepSeek-OCR-2 → Unlimited-OCR
- Baidu's curated multilingual OCR dataset for training
- End-to-end trained: dual vision encoder → linear projector → MoE decoder with R-SWA
- No RLHF or alignment reported; the architecture itself is the focus

## Deployment Frameworks

| Framework | Notes |
|-----------|-------|
| Transformers | `trust_remote_code=True`, requires `torch>=2.10`, CUDA 12.9 |
| vLLM | Dedicated Docker image: `vllm/vllm-openai:unlimited-ocr` |
| SGLang | Requires custom build wheel (v0.0.4.dev11416+), `kernels==0.11.7` |
| Baidu Cloud | REST API via Baidu Cloud OCR service |
| ModelScope | Chinese ecosystem mirror |
| HF Spaces | Community demo by AK at `baidu/Unlimited-OCR` |
| ms-swift | Training support via ms-swift framework |

## Comparison: R-SWA (this model) vs DSA (GLM-5.2)

| Aspect | R-SWA (Unlimited-OCR) | DSA+IndexShare (GLM-5.2) |
|--------|----------------------|--------------------------|
| KV cache growth | None (flat — 128 tokens) | Sub-linear (sparse top-k access) |
| Max context | 32K | 1M |
| Mechanism | Fixed sliding window | Learned top-k sparse retrieval |
| Network cost | O(1) per token | O(log n) per token |
| Model scope | 12-layer, ~3B active MoE | 78-layer, 744B/40B MoE |
| Target task | Document OCR | General reasoning + coding |
