---
name: SakThai-hf-bitsandbytes-quantization
description: Guide to using bitsandbytes with Hugging Face Transformers for 4-bit and 8-bit quantization,
  enabling large model inference and QLoRA training on consumer GPUs.
...
---

# HF Bitsandbytes Quantization

## Overview

bitsandbytes enables accessible large language models via k-bit quantization for PyTorch. Three main features:

1. **8-bit optimizers** — block-wise quantization (32-bit perf at fraction of memory)
2. **LLM.int8()** — 8-bit inference, no quality degradation
3. **QLoRA (4-bit)** — quantize + LoRA training

## Installation

```bash
pip install bitsandbytes
# For NVIDIA CUDA, Intel XPU, Intel Gaudi HPU, or CPU
```

## 8-bit Inference (LLM.int8())

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig, AutoTokenizer
import torch

model_id = "meta-llama/Llama-2-7b-chat-hf"

quantization_config = BitsAndBytesConfig(load_in_8bit=True)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    quantization_config=quantization_config,
)
tokenizer = AutoTokenizer.from_pretrained(model_id)
```

### 8-bit Parameters

- `llm_int8_threshold=6.0` — outlier threshold (default 6.0)
- `llm_int8_skip_modules=["lm_head"]` — skip specific modules
- `llm_int8_enable_fp32_cpu_offload=True` — offload to CPU

## 4-bit Quantization (QLoRA)

### Basic 4-bit Load

```python
quantization_config = BitsAndBytesConfig(load_in_4bit=True)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    quantization_config=quantization_config,
)
```

### NF4 (Normal Float 4) — Best for training

```python
nf4_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",  # NF4 from QLoRA paper, best for training
)

model_nf4 = AutoModelForCausalLM.from_pretrained(
    model_id,
    dtype="auto",
    quantization_config=nf4_config,
)
```

### Compute Data Type (for speed)

```python
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,  # default float32, bf16 for speed
)
```

### Nested/Double Quantization (extra memory saving)

Saves additional 0.4 bits/parameter. Enables finetuning Llama-13b on 16GB T4 GPU.

```python
double_quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
)
model_double_quant = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-13b-chat-hf",
    dtype="auto",
    quantization_config=double_quant_config,
)
```

### Full QLoRA Training Pipeline (with PEFT)

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

# 1. 4-bit quantized base model
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
)

# 2. LoRA config (no device_map needed for training)
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, peft_config)

# 3. Train with SFTTrainer or Trainer
```

## Dequantization

```python
model.dequantize()  # Reverts to original precision (may lose quality)
```

## Important Notes

- For **training**, don't pass `device_map` — model auto-loads on GPU. `device_map="auto"` is for inference only.
- NF4 is quantized from a normal distribution — best for training weights.
- FP4 is standard 4-bit float — slightly faster inference.
- Nested quantization saves ~0.4 bits/param with no performance cost.
- bitsandbytes is MIT licensed.
- Supports: CUDA (NVIDIA), XPU (Intel), HPU (Intel Gaudi), CPU.

## Resources

- QLoRA Paper: https://hf.co/papers/2305.14314
- Blog: [Making LLMs even more accessible](https://huggingface.co/blog/4bit-transformers-bitsandbytes)
- Blog: [Gentle Intro to 8-bit Matrix Multiplication](https://huggingface.co/blog/hf-bitsandbytes-integration)
- Docs: https://huggingface.co/docs/transformers/en/quantization/bitsandbytes
- Reference: `skill_view(name='hf-bitsandbytes-quantization', file_path='references/hf-docs-api.md')` — extracted API params table, hardware support matrix, and Colab links
