---
name: SakThai-hf-bitsandbytes
description: "Hugging Face bitsandbytes — 4-bit and 8-bit quantization for LLM inference and training, with integration guides for Transformers, PEFT, Accelerate, and PyTorch Lightning. Covers BitsAndBytesConfig, QLoRA, LLM.int8(), and custom quantized layers."
version: 1.0.0
author: SakThai
license: MIT
tags: [huggingface, bitsandbytes, quantization, 4bit, 8bit, qlora, llm.int8, peft, accelerate, inference, training]
platforms: [linux, macos, windows]
---

# Hugging Face BitsAndBytes — Quantization

`bitsandbytes` (Bnb) enables accessible large language models via k-bit quantization
for PyTorch. It is the standard Hugging Face-ecosystem library for running and
training LLMs on consumer GPUs by dramatically reducing memory consumption.

## What BNB Provides

| Feature | Use case | Memory savings |
|---------|----------|----------------|
| **LLM.int8()** | 8-bit inference at full 16-bit quality | ~50% |
| **4-bit (FP4/NF4)** | Inference + QLoRA training | ~75% |
| **8-bit optimizers** | Memory-efficient AdamW, Lion, etc. | ~75% for optimizer states |

> Current library version at time of writing: **v0.49.2** (stable). Python ≥ 3.10, PyTorch ≥ 2.4.

## Installation

### Recommended (PyPI wheel)

```bash
pip install bitsandbytes
```

Official wheels are built for NVIDIA (CUDA 11.8–13.0), Intel XPU, Intel Gaudi,
CPU (x86-64, aarch64, Windows ARM64, macOS arm64), and AMD ROCm (preview).

### Compute capability requirements (NVIDIA)

| Feature | CC required | Example hardware |
|---------|-------------|------------------|
| LLM.int8() | 7.5+ | Turing (RTX 20 series, T4) or newer |
| 8-bit optimizers | 6.0+ | Pascal (GTX 10X0, P100) or newer |
| NF4 / FP4 quantization | 6.0+ | Same as 8-bit optimizers |

### Source build (when wheels are unavailable)

```bash
git clone https://github.com/bitsandbytes-foundation/bitsandbytes.git
cd bitsandbytes/
cmake -DCOMPUTE_BACKEND=cuda -S .
make
pip install -e .
```

## Inference: 8-bit with Transformers

Use `BitsAndBytesConfig` to quantize any supported model on the fly.

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(load_in_8bit=True)
model_8bit = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    device_map="auto",
    quantization_config=quantization_config,
)
```

Key points:
- `load_in_8bit=True` enables 8-bit matrix multiplication for inference while
  keeping outliers in 16-bit; this preserves full 16-bit model quality.
- `device_map="auto"` shards the 8-bit model across available GPUs/CPU automatically.

## Inference: 4-bit QLoRA

4-bit gives the biggest memory win and is the standard starting point for
QLoRA training.

```python
import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,   # or torch.float16
    bnb_4bit_quant_type="nf4",               # "nf4" (recommended) or "fp4"
    bnb_4bit_use_double_quant=True,          # optional, nests a second quantization
)

model_4bit = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=bnb_config,
    device_map="auto",
)
```

### 4-bit data types

- **FP4** — standard 4-bit float.
- **NF4** — 4-bit *NormalFloat*, a quantized data type optimized for normally
  distributed weights (see the QLoRA paper). Usually the better choice for LLMs.
- **Double quantization** — applies a second quantization to the first
  quantization constants, squeezing out an extra ~0.37 bits/parameter of
  overhead.

## Training: QLoRA with PEFT

```python
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model

# 1. Load 4-bit model (as above)
model_4bit = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=bnb_config,
    device_map="auto",
)

# 2. Prepare for k-bit training
model_4bit = prepare_model_for_kbit_training(model_4bit)

# 3. Attach LoRA adapters
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules="all-linear",   # or explicit list like ["q_proj", "v_proj"]
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model_4bit, lora_config)
```

After this, the model is trainable: the base weights remain frozen in 4-bit while
only the LoRA adapters are updated in full precision.

## Training: 8-bit Optimizers

Replace standard optimizers with 8-bit/paged variants to reduce optimizer-state
memory by ~75%.

```python
from transformers import TrainingArguments, Trainer

training_args = TrainingArguments(
    output_dir="./results",
    optim="paged_adamw_32bit",   # or "adam8bit", "lion8bit", etc.
    # ...
)
trainer = Trainer(model, training_args, ...)
trainer.train()
```

Available 8-bit / paged optimizers (pass as string to `TrainingArguments(optim=...)`):

- `paged_adamw_32bit` — AdamW with paged states (recommended for QLoRA)
- `adam8bit`
- `adagrad8bit`
- `ademamix8bit`
- `lamb8bit`
- `lars8bit`
- `lion8bit`
- `rmsprop8bit`
- `sgd8bit`

## Accelerate Integration

For non-Transformers PyTorch models, use Accelerate’s `load_and_quantize_model`:

```python
from accelerate import init_empty_weights
from accelerate.utils import BnbQuantizationConfig, load_and_quantize_model

with init_empty_weights():
    model = MyGPT(config)

bnb_quantization_config = BnbQuantizationConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

quantized_model = load_and_quantize_model(
    model,
    weights_location=weights_location,
    bnb_quantization_config=bnb_quantization_config,
    device_map="auto",
)
```

## Custom Quantized Layers

Drop quantized linear modules directly into your architecture:

```python
import bitsandbytes as bnb

# 8-bit linear (int8)
linear_8bit = bnb.nn.Linear8bitLt(
    1024, 1024, has_fp16_weights=False
)

# 4-bit linear (NF4 / FP4)
linear_4bit = bnb.nn.Linear4bit(
    1024, 1024, compute_dtype=torch.bfloat16
)
```

## Compute dtype Recommendations

| dtype | Pros | Cons |
|-------|------|------|
| `torch.bfloat16` | Best speed + stability on Ampere+ | Requires Ampere+ GPU |
| `torch.float16` | Widely supported | Possible inf/nan instability |
| `torch.float32` | Maximum stability | Slower, more memory |

`bfloat16` is the preferred compute dtype for 4-bit when hardware supports it.

## Common Pitfalls

1. **Older GPUs cannot run 4-bit / 8-bit inference** — Check compute capability
   (≥ 6.0 for quantization, ≥ 7.5 for LLM.int8()).
2. **`device_map="auto"` on a single GPU** — Still useful; `accelerate` will
   place offloaded layers on CPU/disk automatically.
3. **FlashAttention + bitsandbytes** — FlashAttention v2 works well with 4-bit;
   FlashAttention v3 requires newer data types and is not yet universally
   compatible.
4. **PyTorch 2.4+ requirement** — BNB v0.49.x targets PyTorch 2.4+. Using an
   older PyTorch triggers installation failures.
5. **Windows aarch64** — Requires Python ≥ 3.12 due to official ARM64 Windows
   build constraints.
6. **NVIDIA Jetson (L4T)** — Standard Linux aarch64 wheels do not work because
   of CUDA ABI mismatch. Compile from source on-device with the correct
   `COMPUTE_CAPABILITY` (e.g., `87` for Orin).

## When to Choose Which Route

| Goal | Choose | Why |
|------|--------|-----|
| Fastest inference on a single GPU | 4-bit NF4 + `device_map="auto"` | ~75% memory reduction, minimal quality loss |
| Maximum inference quality | 8-bit LLM.int8() | Same quality as fp16, ~50% memory reduction |
| Fine-tune a 7B–70B model on consumer GPU | QLoRA (4-bit + PEFT/lora) | Industry standard for affordable post-training |
| Train with DeepSpeed / FSDP | 8-bit optimizers + QLoRA | Maximizes per-GPU batch size |
| Optimize only the optimizer state | `optim="paged_adamw_32bit"` | Keeps weights fp16/bf16, reduces optimizer memory |

## References

- **HF bitsandbytes docs**: https://huggingface.co/docs/bitsandbytes/main/en/index
- **Quickstart**: https://huggingface.co/docs/bitsandbytes/main/en/quickstart
- **Integrations**: https://huggingface.co/docs/bitsandbytes/main/en/integrations
- **4-bit quantizer API**: https://huggingface.co/docs/bitsandbytes/main/en/reference/nn/linear4bit
- **GitHub**: https://github.com/bitsandbytes-foundation/bitsandbytes
- **QLoRA paper**: https://arxiv.org/abs/2305.14314

> Session research notes (installation matrix, integration snippets, key facts):
> `references/bitsandbytes-research-notes.md`