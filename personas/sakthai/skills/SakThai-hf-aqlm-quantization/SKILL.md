---
name: SakThai-hf-aqlm-quantization
description: "Complete reference for AQLM (Additive Quantization of Language Models) \u2014 theory,\
  \ configuration, inference, and practical deployment patterns"
---

# AQLM Quantization — Complete Reference
**tags:** quantization, aqlm, compression, transformers, inference, llm

## Overview

AQLM (Additive Quantization of Language Models) is an extreme compression method that quantizes groups of 8–16 weights together as a sum of multiple vector codes, capturing interdependencies between weights. Unlike element-wise quantization (GPTQ, AWQ), AQLM uses **multi-codebook additive quantization** — each weight group is reconstructed by summing a small number of vectors selected from learned codebooks.

**Key advantages:**
- Achieves **2-bit** and even **1-bit** effective precision per parameter
- Maintains high accuracy: Llama-2-7b at 2-bit retains 85–90% of FP16 performance
- Supports training via LoRA (PEFT) and torch.compile
- CUDA kernels provide up to **3× speedup** vs FP16 (2x8 scheme)
- Numba kernels provide up to **4× speedup** on CPU (Kx8 scheme)

**Limitations:**
- Quantization is **slow**: ~1 day for 7B on A100, ~14 days for 70B on single GPU
- Requires **calibration data** (2048+ samples recommended)
- Not all architectures supported (LLaMA, Mistral, Mixtral, Gemma, Qwen2, Phi-3)
- Requires `aqlm` library (`pip install aqlm[gpu,cpu]`)
- Python 3.10+ only

## Architecture

### Core Idea

AQLM represents a weight matrix `W` as a sum of `K` codebook products:

```
W ≈ Σ_{k=1}^{K} C_k · I(W, k)
```

Where:
- `C_k` is the **codebook** — a set of `2^B` vectors, each of dimension `G` (the group size)
- `I(W, k)` maps each weight group to an index into codebook `k`
- `K` = number of codebooks (typically 1 or 2)
- `B` = bits per codebook entry (typically 8 or 16)
- `G` = group size (typically 8 or 16)

### Notation

The scheme is denoted as **`K × B · gG`**:
- **1×16** (best accuracy): 1 codebook, 2^16 = 65,536 vectors, ~2.0 bits/weight (g8)
- **2×8** (balanced): 2 codebooks, 2^8 = 256 vectors each, ~2.0 bits/weight (g8)
- **1×16g16** (1-bit): 1 codebook, 2^16 vectors, group size 16, ~1.0 bit/weight
- **1×8g8** (1-bit, new): 1 codebook, 2^8 vectors, group size 8, ~1.0 bit/weight
- **K×8** (multi-codebook): K codebooks with 8-bit entries, flexible accuracy/speed tradeoff

### Inference Kernels

| Kernel | Codebooks | Bits | Scheme | Accuracy | Speedup | GPU | CPU |
|--------|-----------|------|--------|----------|---------|-----|-----|
| Triton | K | N | K×N | Varies | ~0.7× | ✅ | ❌ |
| CUDA | 1 | 16 | 1×16 | **Best** | ~1.3× | ✅ | ❌ |
| CUDA | 2 | 8 | 2×8 | OK | ~3.0× | ✅ | ❌ |
| Numba | K | 8 | K×8 | Good | ~4.0× | ❌ | ✅ |

### PV-Tuning (Post-Training Enhancement)

PV-Tuning (Malinovskii et al., NeurIPS 2024, oral) improves AQLM accuracy by jointly optimizing codebook vectors, code indices (via beam search), scale factors, and non-quantized parameters.

PV-tuned models are denoted with `-PV-` in the model name.

## Installation

```bash
pip install aqlm[gpu,cpu]    # GPU + CPU kernels
pip install aqlm>=1.1.6      # For g16 (1-bit) schemes
```

Requires Python 3.10+, PyTorch, and `accelerate`.

## Loading Models

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "ISTA-DASLab/Mixtral-8x7b-AQLM-2Bit-1x16-hf",
    torch_dtype="auto",
    device_map="auto"
)
```

Always set `torch_dtype="auto"` (GPU: float16, CPU: float32).

### Quantization Config

```python
from transformers import AqlmConfig

quant_config = AqlmConfig(
    in_group_size=8,           # Group size along input
    num_codebooks=1,           # Number of codebooks
    nbits_per_codebook=16,     # Bits per codebook entry
    linear_weights_not_to_quantize=["lm_head"]
)
```

## Transformers Integration (v5.14.0+)

- **AqlmConfig**: Configuration class extending `QuantizationConfigMixin`
- **AqlmHfQuantizer**: Quantization handler with `requires_calibration=True`
- **Layer replacement**: `replace_with_aqlm_linear()` replaces `nn.Linear` → `AqlmLinear`
- **Serializable**: `is_serializable()` → `True`
- **Trainable**: `is_trainable()` → `True` if `aqlm>=1.0.2`
- **Dependencies**: `accelerate` + `aqlm`

### Supported Architectures

LLaMA 2/3/3.1/3.2, Mistral, Mixtral, Gemma, Phi-3, Qwen2, Command-R

## Quantization (Calibration)

```bash
python main.py $MODEL_PATH $DATASET_PATH \
  --nsamples=1024 --val_size=128 \
  --num_codebooks=1 --nbits_per_codebook=16 --in_group_size=8 \
  --relative_mse_tolerance=0.01 \
  --finetune_max_epochs=10 --offload_activations \
  --save $SAVE_PATH
```

**Speed benchmarks:**
- 7B (1×16): ~1 day (1×A100), ~14.5h (2×A100)
- 70B (1×16): 10–14 days (1×A100), ~3.75 days (8×A100)

**Data:** RedPajama subset (1024+ samples, 4096 context). Pre-tokenized at `Vahe1994/AQLM`.

## PV-Tuning (Fine-tuning)

```bash
torchrun --nproc-per-node=$NUM_GPUS finetune.py \
  --base_model $MODEL_PATH --quantized_model $QUANTIZED_WEIGHTS \
  --update_codes --update_codebooks_and_scales \
  --update_non_quantized_parameters \
  --lr 3e-4 --code_lr 1e-2 --max_epochs 1 \
  --batch_size=128 --save $SAVE_PATH
```

### LoRA Fine-tuning (PEFT)

```python
from peft import get_peft_model, LoraConfig
model = AutoModelForCausalLM.from_pretrained("...", quantization_config=quant_config)
lora_config = LoraConfig(r=16, target_modules=["q_proj", "v_proj"])
model = get_peft_model(model, lora_config)
```

## Model Zoo

**Notable models (without PV):** Llama-3-8B 1×16 (4.1GB), Llama-3-70B 1×16 (21.9GB), Mixtral-8×7B 1×16 (12.6GB), Llama-2-7B 1×16 (2.4GB)

**With PV-Tuning:** Llama-2-7B 1×16 g8 (2.4GB, PPL 5.68), Llama-2-7B 1×8 g8 (1.34GB, PPL 7.85), Llama-3.2-1B 2×8 (0.8GB), Llama-3-8B 1×16 g8 (4.1GB, PPL 6.99)

## Comparison

| Method | Bits | Calibration | Training | Speedup | GPU Kernel |
|--------|------|-------------|----------|---------|------------|
| **AQLM** | 1–2 | ✅ Required | ✅ LoRA/PV | 1–4× | ✅ CUDA |
| GPTQ | 2–8 | ✅ Required | ❌ | 1–2× | ✅ CUDA |
| AWQ | 4 | ✅ Required | ❌ | 1–2× | ✅ CUDA |
| HQQ | 1–8 | ❌ Data-free | ❌ | ~1× | ✅ Triton |
| BitsAndBytes | 4/8 | ❌ Data-free | ✅ LoRA | ~1× | ✅ CUDA |

## References

- Paper: [2401.06118](https://arxiv.org/abs/2401.06118)
- PV-Tuning: [2405.14852](https://arxiv.org/abs/2405.14852)
- Repo: [github.com/Vahe1994/AQLM](https://github.com/Vahe1994/AQLM)
- HF Docs: [huggingface.co/docs/transformers/quantization/aqlm](https://huggingface.co/docs/transformers/quantization/aqlm)
- Browser Demo: [galqiwi.github.io/aqlm-rs](https://galqiwi.github.io/aqlm-rs/about.html)
