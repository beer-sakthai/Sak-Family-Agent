---
name: SakThai-hf-transformers-quantization-eetq-deep-dive
description: "Complete reference for EETQ (Easy & Efficient Quantization for Transformers) — int8 weight-only per-channel quantization for NVIDIA GPUs, integrated via the Hugging Face Hub Kernels system."
---

# EETQ Quantization in Hugging Face Transformers

## Overview

**EETQ (Easy & Efficient Quantization for Transformers)** is an int8 weight-only per-channel quantization method for NVIDIA GPUs developed by NetEase FuXi AI. It quantizes linear layer weights from fp16/bf16 to int8 per output channel, leaving activations in fp16. No calibration dataset is required — quantization happens on-the-fly when loading the model.

### Key Properties

| Property | Value |
|----------|-------|
| Quantization type | int8 weight-only, per-channel |
| Activation dtype | fp16 (unchanged) |
| Requires calibration | No (on-the-fly) |
| GPU required | Yes (NVIDIA, CUDA ≥ 11.4) |
| CPU support | No |
| Memory reduction | ~2x for weights (fp16 → int8) |
| PEFT fine-tuning | Supported |
| Serializable | Yes (`save_pretrained` / `from_pretrained`) |
| Speed gain | 10–30% via GEMV kernels |
| Attention optimization | FlashAttention-2 |

### When to Use EETQ

- You have an NVIDIA GPU and need **immediate, no-calibration int8 quantization**
- You want to **cut VRAM usage for weights by ~50%** with minimal accuracy loss
- You need **compatibility with PEFT fine-tuning** (LoRA, etc.)
- You're deploying with **TGI** or **LoRAX** and want int8 quantized inference
- You want a **serializable** quantized model that loads fast on subsequent runs

### When NOT to Use EETQ

- No NVIDIA GPU (CPU, AMD, Apple Silicon) — EETQ requires CUDA
- You need sub-8-bit quantization (int4, int2) — use AWQ, GPTQ, or bitsandbytes instead
- You need to run on CPU or mixed CPU/GPU device maps — EETQ doesn't support disk/CPU offloading

## Architecture

### Quantization Scheme

EETQ applies **per-channel int8 quantization** to the weight matrices of `torch.nn.Linear` modules:

For each output channel c:
- scale_c = max(|W[c]|) / 127
- W_int8[c] = round(W_fp16[c] / scale_c)
- Store scale_c in fp16

During forward pass, the computation is **w8a16** (int8 weights × fp16 activations):
```
output = gemm(activation_fp16, W_int8) * scales
```

### Module Structure

EETQ replaces `torch.nn.Linear` with `EetqLinear`, which stores:
- `weight`: int8 tensor (in_features × out_features)
- `weight_scales`: fp16 tensor (out_features,) — per-channel scales
- `bias`: fp16 tensor (out_features,) — optional

### Kernel Architecture

Two custom CUDA kernels drive EETQ:

1. **GEMM Kernel** (from FasterTransformer / TensorRT-LLM): Matrix multiply with int8 weights and fp16 activations, applying per-channel scales inline.
2. **GEMV Kernel** (newer addition): Optimized for batch-size-1 inference, providing 10–30% speedup over naive GEMM for single-query generation.

Both kernels are distributed via **Hugging Face Hub Kernels** (`kernels-community/quantization-eetq`), not installed via PyPI. The `kernels` library downloads and caches them automatically.

## Installation

### Install the `kernels` Library

EETQ in Transformers uses the Hub Kernels system:

```bash
pip install kernels
```

### Install EETQ Directly (Optional — for standalone API)

```bash
# From release wheel
pip install --no-cache-dir https://github.com/NetEase-FuXi/EETQ/releases/download/v1.0.0/EETQ-1.0.0+cu121+torch2.1.2-cp310-cp310-linux_x86_64.whl

# Or from source
git clone https://github.com/NetEase-FuXi/EETQ.git
cd EETQ/
git submodule update --init --recursive
MAX_JOBS=4 pip install .
```

> **Note:** When using EETQ through Transformers, the `kernels` library is sufficient.

### Prerequisites

- CUDA ≥ 11.4
- PyTorch ≥ 1.14.0
- Transformers ≥ 4.45+ (EETQ integration)
- `accelerate` (for device_map)
- NVIDIA GPU

## Usage

### Basic Quantization (On-the-Fly)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, EetqConfig
import torch

model_id = "meta-llama/Llama-3.1-8B"

quantization_config = EetqConfig("int8")  # only "int8" supported

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,        # recommended for efficiency
    device_map="auto",
    quantization_config=quantization_config,
)

tokenizer = AutoTokenizer.from_pretrained(model_id)
inputs = tokenizer("Hello, how are you?", return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens=50)
print(tokenizer.decode(outputs[0]))
```

### Save and Reuse

```python
# Save quantized model
quant_path = "./llama-8b-eetq-int8"
model.save_pretrained(quant_path)
tokenizer.save_pretrained(quant_path)

# Later: load without re-quantizing
model = AutoModelForCausalLM.from_pretrained(
    quant_path,
    device_map="auto",
    torch_dtype=torch.float16,
)
```

### Excluding Specific Modules

Some modules (e.g., `lm_head`) are better left in full precision for numerical stability:

```python
quantization_config = EetqConfig(
    "int8",
    modules_to_not_convert=["lm_head"],
)
```

### With PEFT Fine-Tuning

EETQ quantized models support PEFT methods:

```python
from peft import LoraConfig, get_peft_model

quantization_config = EetqConfig("int8")
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B",
    quantization_config=quantization_config,
    device_map="auto",
    torch_dtype=torch.float16,
)

lora_config = LoraConfig(
    r=8,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
)
model = get_peft_model(model, lora_config)
```

### With TGI

```bash
text-generation-launcher \
    --model-id meta-llama/Llama-3.1-8B \
    --quantize eetq
```

### With LoRAX

```bash
lorax-launcher \
    --model-id meta-llama/Llama-3.1-8B \
    --quantize eetq
```

## Internal Architecture (Transformers Integration)

### Integration Flow

1. **Configuration**: `EetqConfig(weights="int8")` stores quant_method=`QuantizationMethod.EETQ`
2. **Validation**: `EetqHfQuantizer.validate_environment()` checks for CUDA GPU, `kernels`, `accelerate`
3. **Module Replacement**: `_process_model_before_weight_loading()` calls `replace_with_eetq_linear()` which replaces `nn.Linear` with `EetqLinear` (except those in `modules_to_not_convert`). Modules created on `meta` device initially.
4. **Weight Quantization**: As weights load via accelerate hooks, `EetqQuantize.convert()` calls `eetq_kernels_hub.quant_weights(weight, torch.int8, False)` to produce int8 weight + fp16 scales.
5. **Forward**: `EetqLinearMMFunction` calls `eetq_kernels_hub.w8_a16_gemm(x, weight, scales)`.

### Hub Kernels System

Kernels fetched from `kernels-community/quantization-eetq` (version 1). The `kernels` library:
- Downloads compiled kernel for detected CUDA architecture
- Caches locally (like HF Hub model caching)
- Provides `get_kernel()` used by `replace_with_eetq_linear()`

Environment variable `USE_HUB_KERNELS=YES` (default) enables this. Set `USE_HUB_KERNELS=NO` to disable.

## Performance

### Memory Reduction

For fp16 model (2 bytes/param), EETQ reduces weights to int8 (1 byte/param) — ~**2x reduction for weights**.

**Example: Llama-3.1-8B**
- fp16 weights: ~16 GB (8B params × 2 bytes)
- EETQ int8 weights: ~8 GB
- Total VRAM: ~12–14 GB vs ~22–24 GB fp16

### Speed

- GEMV optimization: **10–30% faster** for single-sequence generation
- Batch throughput comparable to fp16
- FlashAttention-2 for attention optimization

### Accuracy

Per-channel int8 quantization typically causes **< 1% accuracy degradation** on standard benchmarks, as each output channel gets its own scale factor.

## Comparison with Other Methods

| Aspect | EETQ | bitsandbytes (int8) | AWQ | GPTQ |
|--------|------|---------------------|-----|------|
| Weight bits | 8 | 8 (or 4) | 4 | 2/3/4/8 |
| Calibration | None | None | Small dataset | Small dataset |
| Fine-tuning | ✅ PEFT | ✅ PEFT | ✅ PEFT | ✅ PEFT |
| Serialization | ✅ | ✅ | ✅ | ✅ |
| GPU | NVIDIA CUDA | NVIDIA CUDA | NVIDIA/AMD | NVIDIA/AMD |
| Setup | Low | Low | Medium | Medium |

## Pitfalls

1. **CUDA-only**: Hard-fails with `RuntimeError: No GPU found` on CPU/Apple Silicon
2. **No CPU/disk offloading**: Mixed device maps with CPU/disk raise `ValueError`
3. **int8 only**: `EetqConfig("int4")` raises `ValueError`
4. **No pre-quantized hub models**: Unlike AWQ/GPTQ, EETQ quantizes on-the-fly (save your own)
5. **Always exclude `lm_head`** from quantization for generation quality

## Environment Variables

| Variable | Default | Effect |
|----------|---------|--------|
| `USE_HUB_KERNELS` | `YES` | Enables Hub Kernels system for EETQ |

## References

- [EETQ GitHub](https://github.com/NetEase-FuXi/EETQ)
- [Transformers EETQ Docs](https://huggingface.co/docs/transformers/en/quantization/eetq)
- [Hub Kernel on HF](https://huggingface.co/kernels-community/quantization-eetq)
- [TGI EETQ PR](https://github.com/huggingface/text-generation-inference/pull/1502)
- [Quantization Overview](https://huggingface.co/docs/transformers/en/quantization/overview)
