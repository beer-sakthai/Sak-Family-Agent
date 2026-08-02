---
name: SakThai-hf-optimum
author: SakThai
license: MIT
description: Deep-dive guide for Hugging Face Optimum — the hardware optimization library for accelerating inference and training on targeted hardware (Intel OpenVINO, ONNX Runtime, NVIDIA TensorRT-LLM, AWS Trainium/Inferentia, Google TPU, Intel Gaudi, AMD, FuriosaAI).
version: 1.0.0
category: mlops
tags: [huggingface, optimum, optimization, quantization, onnx, openvino, inference, training]
---

# 🤗 Optimum — Hardware Optimization Library

## What it is

Optimum is an extension of Transformers, Diffusers, TIMM, and Sentence-Transformers that provides performance optimization tools to train and run models on targeted hardware with maximum efficiency. It is distributed as a collection of packages — each accelerator gets its own sub-package.

## Installation

```bash
# Base package
pip install optimum

# Accelerator-specific installs
pip install optimum[onnx]           # ONNX export + optimization
pip install optimum[onnxruntime]    # ONNX Runtime CPU inference
pip install optimum[onnxruntime-gpu] # ONNX Runtime GPU inference
pip install optimum[openvino]       # Intel OpenVINO
pip install optimum[amd]            # AMD Instinct / Ryzen AI NPU
pip install optimum[neuronx]        # AWS Trainium / Inferentia
pip install optimum[habana]         # Intel Gaudi (HPU)
pip install optimum[furiosa]        # FuriosaAI WARBOY
pip install optimum-quanto          # PyTorch quantization backend
# NVIDIA TensorRT-LLM: docker-based
# docker run -it --gpus all --ipc host huggingface/optimum-nvidia
```

Use `--upgrade --upgrade-strategy eager` with pip to ensure all dependency packages are at latest versions.

## Hardware Partners

| Accelerator | Package | Use Case |
|---|---|---|
| **NVIDIA** (TensorRT-LLM) | `optimum-nvidia` (Docker) | LLM inference on H100+ |
| **AWS Trainium/Inferentia** | `optimum-neuron` | Trn1/Inf2 instances |
| **Google TPUs** | `optimum-tpu` | Cloud TPU training/inference |
| **Intel** (OpenVINO) | `optimum-intel` | CPU/NPU inference optimization |
| **Intel Gaudi** (HPU) | `optimum-habana` | Gaudi/Gaudi2/Gaudi3 training |
| **AMD** (ROCm/Ryzen AI) | `optimum[amd]` | Instinct GPUs, Ryzen AI NPU |
| **FuriosaAI** (WARBOY) | `optimum[furiosa]` | NPU inference |

## Open-Source Integrations

### ONNX Runtime (`optimum-onnx`)
- Export Transformers/Diffusers/TIMM models to ONNX format
- `optimum-cli export onnx --model <model> <output_dir>`
- Use `ORTModelForXXX` classes for inference (replaces `AutoModelForXXX`)
- Graph optimization + quantization on exported models
- Supports CPU and GPU (CUDA) execution providers

### Intel OpenVINO (`optimum-intel`)
- Optimize, quantize, and deploy on Intel hardware
- Post-training quantization via NNCF
- `OVModelForXXX` classes for inference
- Supports weight-only and weight+activation quantization

### ExecuTorch (`optimum-executorch`)
- PyTorch's native solution for on-device inference
- Export Transformers models to ExecuTorch format
- Deploy on mobile and edge devices

### Exporters (`optimum.exporters`)
- Export PyTorch models to ONNX and other formats
- `optimum-cli export onnx --model <model> <path>`
- Supports tasks: text-generation, text-classification, image-classification, etc.

### Torch FX (`optimum.torch_fx`)
- Create and compose custom graph transformations
- Optimize PyTorch Transformer models via FX graph manipulation

## Quantization with Optimum Quanto

Quanto is a PyTorch-native quantization backend integrated with Optimum (package: `optimum-quanto` via pip). Designed for versatility and simplicity, it works in eager mode (no tracing required), supports any device (CUDA, MPS, CPU), and automatically inserts quantized modules and operations.

> ⚠ **Maintenance mode**: As of 2025–2026, Optimum Quanto is in maintenance mode (only minor bug fixes/doc PRs accepted). For production quantization, prefer [bitsandbytes](https://github.com/bitsandbytes-foundation/bitsandbytes) or [torchAO](https://github.com/pytorch/ao).

### Supported dtypes

| Quantization Target | Types | Notes |
|---|---|---|
| **Weights** | int2, int4, int8, float8 | Per-channel along first dim (output features) by default |
| **Activations** | int8, float8 | Per-tensor with static scales (defaults to [-1, 1]) |
| **CUDA matmul** | int8×int8, fp16×int4, bf16×int8, bf16×int4 | Accelerated kernels when available |

### Complete workflow (5 steps)

```python
from optimum.quanto import quantize, freeze, Calibration, qint4, qint8, qfloat8

# Step 1: Quantize (dynamic)
# Converts float model to dynamically quantized — insertion of quant stubs
quantize(model, weights=qint8, activations=qint8)

# Step 2: Calibrate (required only if activations are quantized)
# Records activation ranges via momentum-based calibration
with Calibration(momentum=0.9):
    model(samples)

# Step 3: Tune / QAT (optional — recovers accuracy lost by quantization)
model.train()
for batch in dataloader:
    output = model(batch).dequantize()  # .dequantize() before loss
    loss = criterion(output, targets)
    loss.backward()
    optimizer.step()

# Step 4: Freeze integer weights
# Replaces float weights with quantized integer weights — inference only after this
freeze(model)

# Step 5: Serialize (safetensors recommended)
from safetensors.torch import save_file
save_file(model.state_dict(), 'model.safetensors')

# Also save the quantization map for reloading
import json
from optimum.quanto import quantization_map
with open('quantization_map.json', 'w') as f:
    json.dump(quantization_map(model), f)
```

### Hugging Face model helpers

Quanto provides ready-to-use classes that wrap the full quantization pipeline:

```python
from optimum.quanto import QuantizedModelForCausalLM, qint4

# Quantize (with weight dtype and optional exclusions)
model = AutoModelForCausalLM.from_pretrained('meta-llama/Llama-2-7b')
qmodel = QuantizedModelForCausalLM.quantize(model, weights=qint4, exclude='lm_head')

# Save / Reload via standard HF workflow
qmodel.save_pretrained('./Llama-2-7b-quantized')
qmodel = QuantizedModelForCausalLM.from_pretrained('./Llama-2-7b-quantized')
```

### Diffusers integration

Quantize individual pipeline submodels and reload them:

```python
from diffusers import PixArtTransformer2DModel
from optimum.quanto import QuantizedPixArtTransformer2DModel, qfloat8

# Quantize
model = PixArtTransformer2DModel.from_pretrained(
    "PixArt-alpha/PixArt-Sigma-XL-2-1024-MS", subfolder="transformer")
qmodel = QuantizedPixArtTransformer2DModel.quantize(model, weights=qfloat8)
qmodel.save_pretrained("./pixart-sigma-fp8")

# Later reload and use in a new pipeline
transformer = QuantizedPixArtTransformer2DModel.from_pretrained("./pixart-sigma-fp8")
transformer.to(device="cuda")
pipe = PixArtSigmaPipeline.from_pretrained(
    "PixArt-alpha/PixArt-Sigma-XL-2-1024-MS",
    transformer=None, torch_dtype=torch.float16,
).to("cuda")
pipe.transformer = transformer
```

### Low-level API (requantize from serialized)

Reload a quantized model from separate `state_dict` + `quantization_map`:

```python
from safetensors.torch import load_file
from optimum.quanto import requantize

state_dict = load_file('model.safetensors')
with open('quantization_map.json') as f:
    qmap = json.load(f)

with torch.device('meta'):
    new_model = ...  # instantiate empty model

requantize(new_model, state_dict, qmap, device=torch.device('cuda'))
```

### Quantized modules

| Module | Quantized Replacement | What's Quantized |
|---|---|---|
| `nn.Linear` | `QLinear` | Weights always; biases never; inputs/outputs optional |
| `nn.Conv2d` | `QConv2d` | Weights always; biases never; inputs/outputs optional |
| `nn.LayerNorm` | — | Weights/biases NOT quantized; outputs optional |

Biases are intentionally never quantized — they'd need ~int12 to avoid clipping with int8 inputs/weights, making it wasteful.

### Architecture & design

Quanto uses a `torch.Tensor` subclass that:
1. Projects source tensor into optimal range for the destination type
2. Maps projected values to destination type
  - Float destinations: native `Tensor.to()` cast
  - Integer destinations: `torch.round()`
3. Projection is symmetric per-tensor or per-channel (int8/float8), or group-wise affine (lower bitwidths)

### Pitfalls

1. **Activation quantization + outliers**: Per-tensor int8 activation quantization suffers badly when tensors contain large outliers (most values collapse to zero, only outliers survive). Mitigation: use float8 activations instead, or apply SmoothQuant-style activation smoothing.
2. **Freezing is irreversible**: After `freeze()`, weights are integer and cannot be trained. Run QAT before freezing.
3. **No dynamo/torch.compile support**: Quanto doesn't yet work with torch compiler. Eager mode only.
4. **Mixed weight types per-tensor**: Quanto does NOT support mixing different quantization types within one tensor. Each tensor uses one type.
5. **Maintenance mode**: For new projects, prefer bitsandbytes (mature CUDA kernels) or torchAO (active development by PyTorch team).

## Accelerated Training

Optimum provides wrappers around Transformers Trainer for hardware-accelerated training:

| Hardware | Package | Key Feature |
|---|---|---|
| Intel Gaudi (HPU) | `optimum[habana]` | Gaudi2/Gaudi3 training |
| AWS Trainium | `optimum[neuronx]` | Trn1 instances |
| ONNX Runtime (GPU) | `optimum[onnxruntime-gpu]` | GPU-optimized training |

## CLI Tool (`optimum-cli`)

```bash
# List available tasks
optimum-cli export onnx --help

# Export a model to ONNX
optimum-cli export onnx --model bert-base-uncased ./onnx_export

# Export with task specification
optimum-cli export onnx --model gpt2 --task text-generation ./onnx_export
```

## Pitfalls & Tips

1. **Quanto is in maintenance mode** — for production quantization, prefer bitsandbytes or torchAO
2. **ONNX was moved to separate repo** — `optimum-onnx`, not in core `optimum` package
3. **NVIDIA TensorRT-LLM requires Docker** — no pip install available for optimum-nvidia
4. **Use `--upgrade --upgrade-strategy eager`** when installing accelerator extras to avoid version conflicts
5. **Quanto vs bitsandbytes**: quanto is simpler but less optimized; bitsandbytes has better CUDA kernel support
6. **Hardware availability matters** — most optimum features require actual accelerator hardware to test
7. **For free-tier users**: ONNX Runtime or OpenVINO CPU optimizations are the most accessible — no paid hardware needed
