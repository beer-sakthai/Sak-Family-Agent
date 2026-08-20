---
name: SakThai-hf-transformers-memory-estimation
description: '>-   Comprehensive deep dive into GPU memory estimation for Transformers models,   covering
  memory formulas, batch size optimization, quantization impact,   gradient checkpointing
  trade-offs, mixed precision, and practical recipes   for fitting model'
---

# Transformers Memory Estimation & Batch Size Optimization

## Overview

GPU memory is the most constrained resource when working with large language models. Estimating and optimizing memory usage — for both training and inference — is critical for choosing the right hardware, batch size, sequence length, and precision. This guide covers the formulas, tools, and techniques available in the Hugging Face ecosystem.

## Key Formula: Model Memory

The memory required to **load** a model (inference-only, no activations) is:

```
memory_gb = num_params * bytes_per_param / (1024^3)
```

| Precision | Bytes per param | 7B model | 13B model | 70B model |
|-----------|----------------|----------|-----------|-----------|
| fp32      | 4              | 28 GB    | 52 GB     | 280 GB    |
| fp16/bf16 | 2              | 14 GB    | 26 GB     | 140 GB    |
| int8      | 1              | 7 GB     | 13 GB     | 70 GB     |
| int4      | 0.5            | 3.5 GB   | 6.5 GB    | 35 GB     |

> `safetensors_total` in the HF Hub API gives the exact total size of all safetensors weight files for a model.

## Training Memory Breakdown

Training requires significantly more memory than inference because it must store:

1. **Model weights** — same as inference (fp32 typically for master weights, or fp16/bf16)
2. **Optimizer states** — AdamW stores 2 states per parameter (momentum + variance), each in fp32: `8 bytes * num_params`
3. **Gradients** — typically fp32: `4 bytes * num_params`
4. **Activations** — the largest variable component; scales with `batch_size * sequence_length * hidden_size * num_layers`

### Full Training Memory (AdamW, fp32 master weights):

```
weights:     4 * num_params
gradients:   4 * num_params
optimizer:   8 * num_params (2 states × fp32)
total:      16 * num_params ≈ 112 GB for a 7B model
```

With mixed precision (fp16/bf16 forward/backward, fp32 master weights):

```
weights (fp32 master):    4 * num_params
weights (fp16 copies):    2 * num_params
gradients (fp16):         2 * num_params
optimizer (fp32, 2 states): 8 * num_params
total:                   16 * num_params — same! (master weights + optim states dominate)
```

The **real savings** of mixed precision come from activations stored in fp16 (half the memory), not from weights/gradients.

## Activation Memory (the dominant variable)

For each transformer layer during training, activations stored for backward pass:

```
activations_per_layer = batch_size * sequence_length * hidden_size * (34 + 5 * num_attention_heads * sequence_length / hidden_size)
```

**Simplified rule of thumb:** Activations ≈ `batch_size * sequence_length * hidden_size * num_layers * 2 bytes * ~2` (in fp16)

### Strategies to Reduce Activation Memory

| Technique | Memory Reduction | Speed Impact | How |
|-----------|-----------------|--------------|-----|
| Gradient Checkpointing | ~3-5x fewer activations | ~20% slower | Recompute activations during backward instead of storing all |
| Gradient Accumulation | No peak reduction (same batch per step) | No effect | Simulates larger batch without more memory |
| Smaller batch size | Linear with batch | Slower overall | Fewer samples per step |
| Sequence packing | Fragments depend | Depends | Eliminates padding waste |
| FlashAttention | ~2-4x less attention memory | ~2x faster | IO-aware attention, no N² attention matrix materialization |

## Inference Memory

Inference typically only needs weights + KV cache:

```
total_inference = model_weights + KV_cache + activations

KV_cache = 2 * batch_size * sequence_length * num_layers * num_kv_heads * head_dim * bytes_per_param
```

For Llama-3.1-8B (num_layers=32, num_kv_heads=8, head_dim=128):
- fp16 KV cache per token: `2 * 1 * 1 * 32 * 8 * 128 * 2` = 131,072 bytes ≈ **128 KB per token per sequence**
- For batch=1, seq=4096: ~512 MB for KV cache
- For batch=32, seq=4096: ~16 GB for KV cache

## Practical Optimization Hierarchy (cheapest first)

1. **Use SDPA / FlashAttention** — Often free speed + memory win
2. **Load in bf16/fp16 instead of fp32** — Halves weight memory
3. **Use device_map="auto"** — Let Accelerate distribute across GPUs
4. **Enable gradient checkpointing** — 20% speed cost for ~3-5x activation reduction
5. **Use 8-bit or 4-bit quantization** — Via bitsandbytes or GPTQ/AWQ
6. **Use PEFT (LoRA/QLoRA)** — Only train adapters, not full model
7. **Gradient accumulation** — Effective batch size without peak memory increase
8. **`torch.compile`** — Reduces overhead, enables kernel fusion
9. **Use `max_memory` to distribute across devices** — Explicit GPU memory budgets
10. **Use optimizer 8-bit (adamw_bnb_8bit)** — Reduces optimizer state memory

## HF Tools for Memory Estimation

### 1. Hub Model API (`safetensors_total`)

```
GET /api/models/{model_id}?expand[]=safetensors_total
```
Returns the exact total size of all safetensors weight files, which gives the minimum disk/loading memory.

### 2. Accelerate `estimate_memory` (compute_environment.py)

Accelerate provides utilities to estimate memory usage per device before launching:
```python
from accelerate.utils import compute_module_memory
```

### 3. Practical heuristic for quick estimation

```python
def estimate_inference_memory(num_params_b, dtype="fp16"):
    bytes_map = {"fp32": 4, "fp16": 2, "fp8": 1, "int8": 1, "int4": 0.5}
    b = bytes_map[dtype]
    gb = num_params_b * b * 1e9 / (1024**3)
    return round(gb * 1.2, 2)  # 20% overhead buffer
```

## TrainingArguments Key Parameters

```python
from transformers import TrainingArguments

args = TrainingArguments(
    # Core batch size
    per_device_train_batch_size=4,       # Start small, increase until OOM
    per_device_eval_batch_size=4,
    
    # Memory reduction
    gradient_accumulation_steps=16,      # Effective batch = 4*16 = 64
    gradient_checkpointing=True,         # ~20% slower, ~3-5x less activation memory
    
    # Precision
    bf16=True,                           # or fp16=True
    tf32=True,                           # Ampere+ only
    
    # Optimizer memory
    optim="adamw_bnb_8bit",              # 8-bit AdamW from bitsandbytes
    
    # Speed
    dataloader_pin_memory=True,
    dataloader_num_workers=4,
    torch_empty_cache_steps=4,           # Clear cache periodically (~10% slower)
    
    # Compilation
    torch_compile=True,                  # Uses inductor backend
    torch_compile_backend="inductor",
    
    # Liger Kernel for fused ops
    use_liger_kernel=True,
)
```

## Quantization Comparison for Memory

| Method | Precision | Memory (7B) | Perf Impact | Library |
|--------|-----------|-------------|-------------|---------|
| None   | fp32      | 28 GB       | Baseline    | — |
| None   | fp16/bf16 | 14 GB       | ~1.5x faster | — |
| bitsandbytes | int8 | 7 GB | ~5-10% slower | `bitsandbytes` |
| bitsandbytes | int4 (NF4) | 3.5 GB | ~10-20% slower | `bitsandbytes` |
| GPTQ   | int4      | ~4 GB       | ~0-5% slower | `auto-gptq`, `optimum` |
| AWQ    | int4      | ~4 GB       | ~0-5% slower | `autoawq`, `optimum` |
| HQQ    | int2/3/4  | 1.75-3.5 GB | Variable | `hqq` |
| GGUF   | Q4_K_M    | ~4.5 GB     | ~5-10% slower | `llama.cpp`, `transformers` |

## Model Fit Decision Flowchart

```
1. How much GPU memory? ______ GB
2. Model size? ______ B parameters
3. fp16 weight memory: param_count * 2 GB
   ↓
   If weight_memory > available_GPU → use quantization
   If weight_memory < available_GPU - 2GB → can try training
   If weight_memory << available_GPU → increase batch size
   ↓
4. For training, multiply weight estimate by 4-6x for total
   (weights + grads + optimizer + activations)
   ↓
5. Reduce with: gradient_checkpointing, bf16, adamw_8bit, LoRA
```

## References

- https://huggingface.co/docs/transformers/main/en/perf_train_gpu_one — Training GPU optimization guide
- https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one — Inference GPU optimization guide
- https://huggingface.co/docs/bitsandbytes/index — bitsandbytes quantization docs
- https://huggingface.co/docs/accelerate/concept_guides/big_model_inference — Big model inference
- NVIDIA Performance Guide: https://docs.nvidia.com/deeplearning/performance
