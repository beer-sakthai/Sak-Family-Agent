# HF Learnings: Transformers Memory Estimation & Batch Size Optimization

## What I Learned

### Core Memory Formulas

- Model weight memory (inference): `num_params * bytes_per_param / (1024^3)` GB
- Training total (AdamW): ~16-20× parameter count in bytes (weights + gradients + optimizer + activations)
- Activation memory is the biggest variable cost — grows with batch_size × seq_len × hidden_size × num_layers
- KV cache for inference: `2 * batch * seq_len * num_layers * num_kv_heads * head_dim * bytes_per_param`

### Official HF Documentation Key Findings

The HF Transformers docs at perf_train_gpu_one and perf_infer_gpu_one are the canonical references. They cover:

**Training optimizations** (from perf_train_gpu_one.md):
- Batch size: Use powers of 2, match NVIDIA tensor core requirements (multiples of 8 for fp16, 64 for A100)
- Gradient accumulation: Prefer `batch=4, accum=16` over `batch=1, accum=64` for better GPU utilization
- Gradient checkpointing: ~20% speed penalty for ~3-5x activation memory reduction
- Mixed precision: bf16 > fp16 for dynamic range; tf32 for Ampere+ (16x throughput with fp16/bf16)
- Optimizer choice: `adamw_bnb_8bit` reduces optimizer memory; `adamw_apex_fused` fastest; Adafactor lowest memory
- Data preloading: `dataloader_pin_memory=True` + `dataloader_num_workers=4`

**Inference optimizations** (from perf_infer_gpu_one.md):
- bitsandbytes 8-bit/4-bit quantization via BitsAndBytesConfig
- Optimum + ONNX Runtime for CUDA/ROCm/TensorRT
- SDPA enabled by default in PyTorch 2.1.1+
- FlashAttention standalone: significant for long sequences, but slower with padding tokens
- `attn_implementation` parameter and `set_attention_implementation()` for runtime switching

### New Techniques in v5.14+

- Liger Kernel: fused Triton kernels for RMSNorm, RoPE, SwiGLU, CrossEntropy — 20-40% memory reduction
- NEFTune: noise added to embeddings during training (neftune_noise_alpha)
- torch.compile: inductor backend default for 20-30% training speedup
- `torch_empty_cache_steps`: periodic cache clearing to avoid OOM

### Practical Decision Framework

The key insight is a tiered optimization hierarchy:
1. Free wins: SDPA, bf16, device_map
2. Small cost: gradient checkpointing (~20% slower)
3. Medium: quantization (bitsandbytes, GPTQ, AWQ)
4. Big impact: PEFT/LoRA (train 0.1-1% of parameters)
5. Last resort: gradient accumulation, smaller batches

### Memory Estimation Heuristic

For a quick train/no-train decision:
- Inference: multiply parameter count by 2 (fp16) → needs < available memory
- Training: multiply parameter count by 16-20 → needs < available memory
- If training doesn't fit: use LoRA (requires ~weight_memory * 1.2 for adapters + activations)
- If still doesn't fit: use QLoRA (4-bit base model + LoRA adapters)

## Sources

- https://huggingface.co/docs/transformers/main/en/perf_train_gpu_one — Official training GPU perf guide
- https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one — Official inference GPU perf guide
- https://huggingface.co/docs/transformers/main/en/perf_train_gpu_many — Multi-GPU training guide
- https://huggingface.co/docs/bitsandbytes/index — Quantization library docs
- https://huggingface.co/docs/accelerate/concept_guides/big_model_inference — Big model inference
