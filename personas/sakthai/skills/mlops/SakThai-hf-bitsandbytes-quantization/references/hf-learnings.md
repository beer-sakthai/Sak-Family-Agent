# HF Learnings — Bitsandbytes Quantization (v0.50.0 Deep Dive)

> *Entry 19 in cumulative HF learnings: deep-dive refresh*
> *Topic: `hf-bitsandbytes-quantization`*
> *Date: 2026-07-25*
> *Sources: bitsandbytes v0.50.0 release notes, Transformers 5 docs, GitHub changelogs (0.43→0.50)*

---

## 1. What bitsandbytes Is & Why It Matters

bitsandbytes is a **PyTorch quantization library** providing k-bit optimizers, 8-bit matrix multiplication (LLM.int8()), 4-bit NF4/FP4 quantization, and fused CUDA/ROCm kernels for memory-efficient LLM inference and training. It's the backbone of **QLoRA** — making large model fine-tuning possible on consumer GPUs.

**Key fact:** bitsandbytes is maintained by the **bitsandbytes-foundation** (not Tim Dettmers directly anymore) and is **MIT licensed**. Latest version: **0.50.0** (released 2026-07-25).

### What it provides

| Feature | What it does | Use Case |
|---------|-------------|----------|
| **LLM.int8()** | 8-bit inference via mixed-precision decomposition | Run 70B models on single GPU |
| **NF4/FP4 quantization** | 4-bit weight quantization from QLoRA paper | Train 65B models on 48GB GPUs |
| **8-bit optimizers** | AdamW, AdEMAMix, LION, LAMB etc at 8-bit | Memory-efficient training |
| **Fused 4-bit GEMM** | New in v0.50.0: dequantize+GEMM fused | Up to 4× faster inference |
| **CPU offload + optim** | 8-bit AdamW on CPU for hybrid training | Offload optimizer states |

### Version History (Recent)

| Version | Date | Key Change |
|---------|------|------------|
| 0.43.0 | 2024-05 | QLoRA+FSDP official support |
| 0.43.2 | 2024-07 | QLoRA memory bug fix (saves 39GB/seq on 405B) |
| 0.44.0 | 2024-10 | AdEMAMix optimizer, 8-bit blocksize 2048→256 |
| 0.45.0 | 2024-12 | LLM.int8() on Hopper (H100), wheel size -43.5% |
| 0.46.x–0.48.x | 2025 | AMD ROCm preview, Intel XPU support, Windows ARM |
| 0.49.0 | 2025-12 | CPU perf improvements (AVX512BF16), ROCm stable |
| **0.50.0** | **2026-07-25** | **Fused 4-bit GEMM inference, MPS support, ROCm stable** |

---

## 2. Architecture: How Quantization Works Under the Hood

### LLM.int8() — Mixed-Precision Decomposition

LLM.int8() works by decomposing matrix multiplication into two parts:

```
X·W = X·(W_fp16 + W_int8)
     = X·W_fp16 (outlier columns) + X·W_int8·S (normal columns)
```

1. **Outlier detection:** Columns with values > `llm_int8_threshold` (default 6.0) are identified
2. **High-precision path:** Outlier columns are computed in fp16 (typically 0.1–1% of columns)
3. **Quantized path:** Remaining 99% of columns use int8 matmul with row-wise quantization
4. **Combine:** Results are merged

This preserves full-precision accuracy for outlier-sensitive computation while getting 2× memory savings on the bulk of the weights.

### NF4 — Normal Float 4 (from QLoRA)

NF4 is a **non-uniform quantization** data type designed for normally distributed weights. Key properties:

- 4-bit values represent the quantile boundaries of a normal distribution N(0, 1)
- 16 representable values (vs 16 for FP4) but distributed optimally for weight distributions
- **Blocksize:** Default 64 (was 128 pre-0.49.2 on ROCm)
- **Double quantization:** Saves ~0.4 bits/param by quantizing the scaling factors too

```
NF4 Values: [-1.0, -0.696, -0.525, -0.393, -0.277, -0.169, -0.064, 0.039,
              0.143, 0.247, 0.352, 0.460, 0.572, 0.694, 0.830, 1.0]
```

### New in v0.50.0: Fused 4-bit GEMM Inference

Introduced in [#1949](https://github.com/bitsandbytes-foundation/bitsandbytes/pull/1949):
- **Fused kernels** combine dequantization + GEMM (General Matrix Multiply) into a single CUDA call
- **Up to 4× faster** at batch sizes 2–64 across Turing through Blackwell
- **Nested quantization fused** — double quantization sees additional benefit
- **Automatic kernel selection** based on shape, GPU architecture, and SM count at runtime
- ROCm SIMT version ported in [#1979](https://github.com/bitsandbytes-foundation/bitsandbytes/pull/1979)

---

## 3. Hardware Support Matrix (v0.50.0)

| Platform | 4-bit | 8-bit (LLM.int8) | 8-bit Optimizers | CPU Optimizers | Paged Optimizers |
|----------|:-----:|:-----------------:|:-----------------:|:--------------:|:----------------:|
| **NVIDIA CUDA** (sm_52+) | ✅ | ✅ (sm_75+ Turing) | ✅ | ❌ | ✅ |
| **AMD ROCm** (gfx908+) | ✅ stable | ✅ stable | ✅ | ❌ | ❌ |
| **Intel XPU** | ✅ | ❌ | ✅ | ❌ | ✅ (v0.49+) |
| **Intel Gaudi (HPU)** | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Apple Silicon (MPS)** | ✅ v0.50.0 | ✅ v0.50.0 | ❌ (future) | ❌ | ❌ |
| **CPU x86-64** | ✅ (AVX512/AVX2) | ✅ (v0.49+) | ❌ | ✅ v0.49+ | ❌ |
| **CPU ARM64** | ✅ (NEON) | ✅ | ❌ | ✅ v0.49+ | ❌ |
| **Windows x86-64** | ✅ CUDA+ROCm | ✅ CUDA | ✅ CUDA | ✅ | ✅ |
| **Windows ARM64** | ✅ CPU | ✅ | ❌ | ✅ v0.50.0 | ❌ |

**Minimum GPU requirements:**
- **8-bit optimizers:** Pascal (GTX 1080, P100) or newer — sm_52+
- **LLM.int8():** Turing (RTX 2060, T4) or newer — sm_75+
- **NF4/FP4 quantization:** Pascal or newer — sm_52+

**Minimum PyTorch:** 2.4 (v0.50.0 raised this from 2.3)

---

## 4. Transformers 5 Integration (BitsAndBytesConfig)

### Parameter Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `load_in_8bit` | bool | False | Enable LLM.int8() 8-bit quantization |
| `load_in_4bit` | bool | False | Enable 4-bit NF4/FP4 quantization |
| `llm_int8_threshold` | float | 6.0 | Outlier threshold (higher = more int8, less fp16) |
| `llm_int8_skip_modules` | list | None | Module names to keep in full precision |
| `llm_int8_enable_fp32_cpu_offload` | bool | False | Offload fp32 outlier computation to CPU |
| `bnb_4bit_compute_dtype` | torch.dtype | torch.float32 | Compute dtype for 4-bit matmul (use bf16 for speed) |
| `bnb_4bit_quant_type` | str | "fp4" | "nf4" (training, QLoRA paper) or "fp4" (inference) |
| `bnb_4bit_use_double_quant` | bool | False | Nested quantization of scaling factors (-0.4 bits/param) |
| `bnb_4bit_blocksize` | int | 64 | Blocksize for 4-bit quantization (default 64, ROCm parity) |

### Best Practice Configuration

**QLoRA training (recommended):**
```python
from transformers import BitsAndBytesConfig
import torch

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",        # NF4 from QLoRA paper
    bnb_4bit_compute_dtype=torch.bfloat16,  # Speed
    bnb_4bit_use_double_quant=True,   # Extra memory savings
    bnb_4bit_blocksize=64,            # Default blocksize
)
```

**8-bit inference (LLM.int8):**
```python
bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0,           # Default outlier threshold
)
```

### Important: Loading for Training vs Inference

| Aspect | Inference | Training (QLoRA) |
|--------|-----------|-----------------|
| `device_map` | `"auto"` (distributes efficiently) | **Do NOT set** (model auto-loads on GPU) |
| `bnb_4bit_quant_type` | `"fp4"` (faster) or `"nf4"` | `"nf4"` (required for QLoRA) |
| `torch_dtype` | `"auto"` or explicit | `torch.bfloat16` or `torch.float16` |

**For training**, do NOT pass `device_map="auto"` — PEFT handles device placement automatically. Setting both causes errors.

---

## 5. Memory Benchmarks

### QLoRA Memory Savings (from v0.43.2 fix)

Activation memory fix in v0.43.2 saved significant memory for frozen quantized parameters:

| Model | SeqLen | Memory Saved per Batch (before→after) |
|-------|--------|---------------------------------------|
| Llama 405B | 1024 | 39 GB |
| Llama 405B | 128K | 4888 GB |
| Llama 70B | 1024 | 10.1 GB |
| Llama 70B | 128K | 1258 GB |

### Model Memory Comparison (HF Inference API vs bnb Quantized)

| Model | Full FP16 | 8-bit (LLM.int8) | 4-bit NF4 | 4-bit + Double Quant |
|-------|:---------:|:-----------------:|:---------:|:--------------------:|
| Llama-2-7B | ~14 GB | ~7 GB | ~4 GB | ~3.5 GB |
| Llama-2-13B | ~26 GB | ~13 GB | ~7 GB | ~6.5 GB |
| Llama-2-70B | ~140 GB | ~70 GB | ~35 GB | ~32 GB |
| Llama-3-405B | ~810 GB | ~405 GB | ~200 GB | ~185 GB |

Note: These are model weights only. Additional memory needed for KV cache, activations, and optimizer states during training.

### Inference Speed (v0.50.0 fused 4-bit GEMM)

New fused kernels provide **up to 4×** improvement over previous GEMV/dequantize+linear approach:

| GPU Family | BS=1 | BS=8 | BS=32 | BS=64 |
|------------|:----:|:----:|:-----:|:-----:|
| Turing (T4) | 1.2× | 2.1× | 3.2× | 3.8× |
| Ampere (A100) | 1.1× | 1.8× | 2.8× | 3.5× |
| Hopper (H100) | 1.0× | 1.5× | 2.5× | 3.2× |
| Blackwell (B100) | 1.0× | 1.4× | 2.4× | 3.1× |

---

## 6. Complete Training Pipeline

### QLoRA + SFTTrainer (Recommended)

```python
import torch
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

# 1. Quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

# 2. Load base model — NO device_map for training
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B",
    quantization_config=bnb_config,
    torch_dtype=torch.bfloat16,
)
model = prepare_model_for_kbit_training(model)

# 3. LoRA config
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)

# 4. Training
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    args=TrainingArguments(
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        bf16=True,
        logging_steps=10,
        save_strategy="epoch",
        output_dir="./qlora-output",
    ),
)
trainer.train()
```

### QLoRA + FSDP (Large Models on Multi-GPU)

Available since bitsandbytes v0.43.0, enables training 70B-scale models on 8× consumer GPUs:

```python
# Launch with torchrun for FSDP
# torchrun --nproc_per_node=8 train_qlora_fsdp.py

# Requires:
# - bitsandbytes >= 0.43.0
# - transformers >= 4.38.0 (PR #32276 for quant_storage)
# - accelerate >= 0.28.0
# - peft >= 0.14.0 (for 8-bit adapter merging)

# FSDP config (accelerate config or YAML):
# fsdp: "full_shard auto_wrap"
# fsdp_config:
#   fsdp_offload_params: true  # offload optimizer states to CPU
#   fsdp_state_dict_type: SHARDED_STATE_DICT
```

### FSDP+QLoRA Memory: Llama 3.1 405B on 8×H100

Using bitsandbytes 0.43.3+ with NF4 quant_storage in bf16:
- **Hardware:** Single 8×H100 or 8×A100 node
- **System RAM:** As low as 256 GB
- **Technique:** FSDP full sharding with optimizer offload + QLoRA 4-bit base

---

## 7. Available Optimizers (v0.50.0)

bitsandbytes provides memory-efficient optimizers as drop-in replacements for PyTorch's:

### 32-bit Optimizers
| Optimizer | 8-bit variant | Paged variant | CPU support | Description |
|-----------|:-------------:|:-------------:|:-----------:|-------------|
| Adam | ✅ Adam8bit | ✅ PagedAdam | ✅ v0.49+ | Standard Adam |
| AdamW | ✅ AdamW8bit | ✅ PagedAdamW | ✅ v0.49+ | Adam with decoupled weight decay |
| SGD | ✅ SGD8bit | — | ✅ | Standard SGD |
| LION | ✅ LION8bit | — | ✅ v0.49+ | Evolution-based optimizer |
| LAMB | ✅ LAMB8bit | — | ✅ XPU | Layer-wise adaptive moments |
| LARS | ✅ LARS8bit | — | ✅ XPU | Layer-wise adaptive rate scaling |
| **AdEMAMix** | ✅ AdEMAMix8bit | ✅ PagedAdEMAMix | — | New: dual-EMA variant of AdamW |

**AdEMAMix** (added in v0.44.0) is notable: it tracks **two EMAs** (short + long-term) to better leverage past gradients, achieving faster convergence with less data. Reference: [AdEMAMix paper](https://hf.co/papers/2409.03137).

### Usage Pattern
```python
from bitsandbytes.optim import AdamW8bit

optimizer = AdamW8bit(model.parameters(), lr=2e-5)
# Uses 8-bit optimizer states — ~3× memory savings vs 32-bit
```

### 8-bit Blocksize Change (v0.44.0)
- Old: blocksize 2048 (from original 2021 paper)
- **New: blocksize 256** — improves accuracy with no performance cost
- Configurable via `block_wise=True` (default, blockwise quantization is now **required** — non-blockwise deprecated and removed in v0.50.0)

---

## 8. Integration with Other HF Libraries

### With PEFT (LoRA/QLoRA)
```python
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

model = prepare_model_for_kbit_training(model)  # Freeze base, prepare inputs
model = get_peft_model(model, LoraConfig(...))  # Add LoRA adapters
```

### With TRL (RLHF/DPO)
```python
from trl import DPOTrainer

# QLoRA + DPO works directly — TRL handles k-bit models
trainer = DPOTrainer(
    model=model,  # Already quantized with BitsAndBytesConfig
    ref_model=None,  # Automatically creates a reference
    ...
)
```

### With Transformers Pipeline
```python
from transformers import pipeline

# Quantized model works in pipeline
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
pipe("Hello, I am", max_new_tokens=50)
```

---

## 9. v0.50.0 Breaking Changes & Migration Guide

### Breaking Changes
| Change | Impact | Migration |
|--------|--------|-----------|
| **Min PyTorch 2.4** | Need torch >= 2.4 | `pip install --upgrade torch` |
| **Removed `research` module** | `bnb.research.*` broken | Use stable APIs |
| **Removed non-blockwise optimizers** | `block_wise=False` fails | Default is blockwise, just remove param |
| **Removed sparse ops** | `spmm_coo*` gone | Use dense matmul |
| **Deprecated: `igemm`, `batched_igemm`** | Warnings emitted | Use `matmul_4bit` / `matmul_8bit` |
| **PEFT adapter merging** | Need peft >= 0.14.0 | `pip install --upgrade peft` |

### Windows Users
- **ROCm on Windows:** Now supported! ROCm 7.2.1+ wheels for Windows
- **Windows ARM64 CPU:** NEON-optimized wheels available

### Apple Silicon Users
- **macOS 26+:** Install `kernels` package for optimized Metal kernels
- **torch >= 2.9 required** for MPS path
- **All 4-bit and LLM.int8() configs work** on MPS
- **8-bit optimizers** coming in future release

---

## 10. Zero-Cost Patterns & Limitations

### Zero-Cost Patterns
1. **bitsandbytes is free (MIT license)** — no licensing cost
2. **QLoRA on consumer GPUs:** Train 7B models on 8GB VRAM (RTX 3070)
3. **Hugging Face Inference API with 4-bit:** Not directly available (serverless runs fp16), but bnb-quantized models can be uploaded to HF Hub and downloaded by anyone
4. **CPU inference:** v0.49+ CPU perf improvements make 4-bit inference viable on CPU for small models
5. **Google Colab (free tier):** 15GB T4 GPU can run Llama-13B with 4-bit + double quant

### Limitations
| Limitation | Impact | Workaround |
|------------|--------|------------|
| No device_map during training | Must manage GPU placement manually | accelerate/FSDP handles this |
| No serverless 4-bit on HF Inference API | Can't run bnb-quantized via serverless | Use TGI with custom Docker or self-host |
| QLoRA training speed overhead | ~20-30% slower than full fine-tune | Use higher rank (r=32, r=64) to compensate |
| NF4 quality ceiling | Some loss vs fp16 at very high ranks | Use 8-bit for critical production deployments |

---

## 11. Security & Reproducibility

### Model Hash Verification
```python
from huggingface_hub import snapshot_download
import hashlib

# Download a pre-quantized model
path = snapshot_download("hugging-quants/Meta-Llama-3.1-405B-BNB-NF4-BF16")

# Verify checksums
with open(f"{path}/model.safetensors.index.json") as f:
    import json
    manifest = json.load(f)
    for filename, metadata in manifest.get("weight_map", {}).items():
        # Verify each shard
        pass
```

### Deterministic Quantization
bitsandbytes quantization is deterministic for the same hardware/config:
```python
torch.use_deterministic_algorithms(True)
model = AutoModelForCausalLM.from_pretrained(..., quantization_config=bnb_config)
```

---

## 12. Comparison with Other Quantization Methods

| Feature | bitsandbytes (4-bit) | bitsandbytes (8-bit) | AWQ | GPTQ | GGUF (llama.cpp) | Quanto |
|---------|:-------------------:|:--------------------:|:---:|:----:|:----------------:|:------:|
| **Training support** | ✅ QLoRA | ❌ inference only | ❌ | ❌ | ❌ | ✅ |
| **Inference speed** | Fast (v0.50.0 GEMM) | Moderate | Very fast | Fast | Very fast | Moderate |
| **Quality retention** | Good (NF4) | Excellent | Excellent | Excellent | Good-Fair | Moderate |
| **Hardware** | CUDA, ROCm, MPS, CPU | CUDA, ROCm, MPS, CPU | CUDA | CUDA | CPU, GPU, Apple | CPU, CUDA |
| **Dynamic quant** | ✅ | ✅ | ❌ (static) | ❌ (static) | ❌ (static) | ❌ (static) |
| **Prequantized models** | ✅ growing library | ✅ (common) | ✅ (common) | ✅ (common) | ✅ (common) | ❌ |
| **License** | MIT | MIT | MIT | MIT | MIT | Apache 2.0 |
| **Best for** | QLoRA training | Quick inference | Production inference | Batch inference | Edge/mobile deployment | Research/experimentation |

---

## 13. Common Pitfalls & Solutions

| Problem | Cause | Solution |
|---------|-------|----------|
| `"The model is not loaded in 8-bit"` | Forgot `load_in_8bit=True` | Add to BitsAndBytesConfig |
| CUDA out of memory with device_map="auto" during training | device_map conflicts with PEFT | Remove device_map for training |
| Slow first inference call | Model loading + quantization overhead | Preload with `preload_from_hub` in Spaces |
| `"Unsupported linear type"` | Model uses custom Linear (not nn.Linear) | Add to `llm_int8_skip_modules` |
| QLoRA loss higher than expected | Wrong quant_type (fp4 instead of nf4) | Set `bnb_4bit_quant_type="nf4"` |
| `bitsandbytes` import error | CUDA version mismatch | Check `import bitsandbytes; bitsandbytes.cuda_version` |
| MPS backend not working | torch < 2.9 | Upgrade torch to >= 2.9 |
| `AttributeError: 'Linear4bit'` | Loading model with wrong `torch_dtype` | Set `torch_dtype="auto"` or match quant_storage |

---

## 14. Key Source Files in bitsandbytes

| File | Purpose |
|------|---------|
| `bitsandbytes/nn/modules.py` | `Linear4bit`, `Linear8bitLt`, `Params4bit` |
| `bitsandbytes/optim/` | All optimizer implementations (Adam8bit, AdEMAMix8bit, etc.) |
| `bitsandbytes/functional.py` | Low-level quantize/dequantize/matmul ops |
| `bitsandbytes/cuda_setup/main.py` | CUDA version detection and library loading |
| `csrc/ops/gemm_4bit.cu` | Fused 4-bit GEMM kernels (new in v0.50.0) |
| `csrc/python_interface.cu` | Python-to-CUDA bridge |

---

## 15. Sources

- bitsandbytes GitHub: https://github.com/bitsandbytes-foundation/bitsandbytes
- PyPI: https://pypi.org/project/bitsandbytes/
- HF Docs (bitsandbytes): https://huggingface.co/docs/bitsandbytes/main
- HF Docs (Transformers integration): https://huggingface.co/docs/transformers/en/quantization/bitsandbytes
- QLoRA paper: https://hf.co/papers/2305.14314
- LLM.int8() paper: https://hf.co/papers/2208.07339
- Blog (4-bit): https://huggingface.co/blog/4bit-transformers-bitsandbytes
- Blog (8-bit): https://huggingface.co/blog/hf-bitsandbytes-integration
- AdEMAMix paper: https://hf.co/papers/2409.03137
