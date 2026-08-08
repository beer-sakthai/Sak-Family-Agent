# HF Learnings — mergekit-hf-merging (Deep-Dive v2)

## 2026-07-25: mergekit-hf-merging-deep-dive-v2 — MergeKit Advanced Features Deep-Dive (Topic #270)

### Summary
Deep-dive on the advanced MergeKit features beyond basic merge methods: dense-to-MoE conversion (mergekit-moe), evolutionary parameter optimization (mergekit-evolve), multi-stage chaining (mergekit-multi), raw PyTorch checkpoint merging (mergekit-pytorch), LoRA extraction via SVD (mergekit-extract-lora), tokenizer transplantation (mergekit-tokensurgeon), fine-grained parameter control with tensor name filters, gradient interpolation, and modern tokenizer configuration with per-token embedding override.

### Sources
- MergeKit GitHub: https://github.com/arcee-ai/mergekit
- Merge Methods Guide: https://github.com/arcee-ai/mergekit/blob/main/docs/merge_methods.md
- MoE Merging: https://github.com/arcee-ai/mergekit/blob/main/docs/moe.md
- Multi-Stage Merging: https://github.com/arcee-ai/mergekit/blob/main/docs/multimerge.md
- Evolutionary Merge: https://github.com/arcee-ai/mergekit/blob/main/docs/evolve.md

### New Learnings (beyond v1)

1. **mergekit-moe Gate Modes**: Three modes — `hidden` (hidden state from prompts, best quality, default), `cheap_embed` (raw token embeddings, low hardware), `random` (for sparse upcycling/further training). Shared expert support with `residual_scale` for Qwen MoE architecture.

2. **mergekit-evolve CMA-ES**: Uses Covariance Matrix Adaptation Evolution Strategy with LM Eval Harness tasks. Multiple scheduling strategies: `pool` (one actor/GPU), `buffered` (concurrent on same GPU), `serial` (Ray placement groups). Supports in-memory merging and vLLM backend.

3. **mergekit-multi Chaining**: YAML documents separated by `---`. Named intermediates referenced by name in later stages. `--lazy` flag skips cached intermediates. Undefined behavior if no named intermediate exists for a reference.

4. **mergekit-pytorch**: Applies merge algorithms to arbitrary `.pt`/`.safetensors` (non-Transformers models). No layer slicing or tokenizer support.

5. **mergekit-extract-lora**: SVD-based extraction of PEFT-compatible LoRA adapters. Options: `--max-rank`, `--embed-lora`, `--distribute-scale`, regex filtering, `--sv-epsilon` for singular value thresholding.

6. **mergekit-tokensurgeon**: Transplants tokenizers between models for speculative decoding draft models or cross-tokenizer distillation.

7. **Fine-Grained Parameters**: Four-level precedence + tensor name filters (`self_attn`, `mlp`, etc.) for different merge weights per module type. Gradient interpolation arrays for per-layer-varying weights.

8. **Tokenizer Configuration**: New `tokenizer` block with `tokens` map for per-token embedding override and `pad_to_multiple_of`. Legacy `tokenizer_source` maintained for backward compatibility but fields are mutually exclusive.

### Skill Updated
SakThai-mergekit-hf-merging v2.0.0 — Complete MergeKit reference with all advanced features, configuration patterns, and zero-cost operation guidelines.
