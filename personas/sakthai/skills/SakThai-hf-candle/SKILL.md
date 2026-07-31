---
name: SakThai-hf-candle
version: 1.0.0
author: SakThai
license: MIT
description: Complete reference for Candle — Hugging Face's minimalist ML framework for Rust, focused on serverless inference, CPU/GPU inference, and lightweight deployments
category: mlops
---

# HF Candle — Rust ML Framework

## Summary
Candle is Hugging Face's minimalist ML framework for Rust, focused on **serverless inference** without the overhead of full Python frameworks like PyTorch. It lets you deploy lightweight Rust binaries for inference on CPU and GPU (CUDA, Metal), supports safetensors/npz/ggml/PyTorch weight formats, and has built-in quantization. Current version: **0.11.0**.

| Aspect | Detail |
|--------|--------|
| **Author** | Hugging Face (Laurent Mazare primary) |
| **Language** | Rust (with WASM support) |
| **License** | MIT / Apache 2.0 dual |
| **Latest** | 0.11.0 |
| **Stars** | ~17k+ on GitHub |

## Why Candle Exists

Candle was created to solve three problems:

1. **Serverless inference startup time** — Full PyTorch environments are ~2GB+ and slow to spin up. Candle produces single-digit MB binaries that start in milliseconds.
2. **Remove Python from production** — Python's GIL and overhead hurt serving performance. Rust gives predictable latency.
3. **Rust-native HF ecosystem** — safetensors and tokenizers are already Rust crates; Candle completes the picture.

## Architecture

### Core Crates

| Crate | Purpose |
|-------|---------|
| `candle-core` | Tensor ops, devices (CPU/CUDA/Metal), DType definitions, storage backend |
| `candle-nn` | Neural network building blocks (Linear, Conv2d, LayerNorm, etc.) |
| `candle-transformers` | Transformer utils (models, configs, generation) |
| `candle-examples` | Pre-built model examples (Llama, Whisper, Stable Diffusion, etc.) |
| `candle-kernels` | Custom CUDA kernels (fused ops) |
| `candle-datasets` | Dataset loading and data loaders |
| `candle-flash-attn` | Flash Attention v2 layer |
| `candle-onnx` | ONNX model evaluation |

### Backends

| Backend | Feature Flag | Description |
|---------|-------------|-------------|
| CPU (native) | (default) | Pure Rust, no dependencies |
| CPU (MKL) | `mkl` | Intel MKL-accelerated linear algebra |
| CPU (Accelerate) | `accelerate` | Apple Accelerate framework for macOS |
| CUDA | `cuda` | NVIDIA GPU support |
| cuDNN | `cudnn` | NVIDIA cuDNN-accelerated ops |
| Metal | `metal` | Apple Metal GPU support |
| WASM | (target) | Browser-based inference |

### Device Management

```rust
use candle_core::{Device, Tensor};

// CPU
let device = Device::Cpu;

// CUDA GPU
let device = Device::new_cuda(0)?;

// Metal GPU (macOS)
let device = Device::new_metal(0)?;
```

Backends are **compile-time selected** via Cargo features — no runtime switching.

## Key Features

### 1. PyTorch-like API
```rust
// Create tensors, operations feel like PyTorch
let a = Tensor::randn(0f32, 1., (2, 3), &device)?;
let b = Tensor::randn(0f32, 1., (3, 4), &device)?;
let c = a.matmul(&b)?;
let d = c.reshape((2, 2, 3))?;
```

### 2. Weight Format Support
| Format | crate | Notes |
|--------|-------|-------|
| safetensors | `candle-core` (built-in) | Recommended, zero-copy mmap |
| npz | `candle-core` (built-in) | NumPy format |
| ggml / GGUF | `candle-core` (via `quantized` module) | llama.cpp quantized formats |
| PyTorch (.bin/.pt) | `candle-core` (via pickle) | Generic PyTorch checkpoint |
| ONNX | `candle-onnx` | ONNX model evaluation |

### 3. Quantization
Candle supports llama.cpp quantized types for reduced memory usage:

| Type | Bits | Description |
|------|------|-------------|
| Q4_0 | 4-bit | Standard 4-bit, good balance |
| Q4_1 | 4-bit | Higher accuracy 4-bit |
| Q5_0 | 5-bit | Better quality, moderate size |
| Q5_1 | 5-bit | Higher accuracy 5-bit |
| Q8_0 | 8-bit | Almost no quality loss |
| Q6_K | 6-bit | K-quant method |
| Q2_K-Q6_K | 2-6 bit | Variable K-quants |

### 4. Model Support

**Language Models:**
- LLaMA v1/v2/v3 (including SOLAR-10.7B)
- Falcon, Mistral 7B, Mixtral 8x7B
- Gemma v1/v2 (2b, 7b, 9b)
- Phi 1/1.5/2/3
- Qwen1.5, Qwen3 MoE (including GGUF quantized)
- Mamba, RWKV v5/v6
- Yi-6B/34B, StableLM, Replit-Code
- StarCoder, StarCoder2

**Vision Models:**
- Stable Diffusion (1.5, 2.1, XL 1.0, Turbo)
- Wuerstchen v2
- DINOv2, ViT, ResNet, ConvNeXT
- YOLO-v3/v8 (object detection + pose)
- Segment Anything (SAM)
- MobileNetv4, EfficientVit, Hiera

**Audio Models:**
- Whisper (multi-lingual speech-to-text)
- EnCodec (audio compression)
- MetaVoice-1B (text-to-speech)
- Parler-TTS (text-to-speech)

**Multimodal:**
- BLIP (image captioning)
- CLIP (vision-language)
- TrOCR (OCR)
- Moondream (visual QA)

### 5. Text Generation Pipeline

```rust
// Llama example (from candle-examples)
use candle_core::Device;
use candle_transformers::models::llama as model;

let device = Device::Cpu;
// Load weights from safetensors
let model = model::Llama::load(weights, config)?;
// Generate tokens
for _ in 0..100 {
    let logits = model.forward(&input_ids)?;
    let next_token = sample(logits)?;
    // ... loop
}
```

## Installation

### Cargo dependencies

```toml
[dependencies]
candle-core = "0.11.0"
candle-nn = "0.11.0"
candle-transformers = "0.11.0"
```

### CUDA support

```bash
# Ensure CUDA toolkit is installed, then:
cargo add candle-core --features cuda
```

### Feature flags

```toml
candle-core = { version = "0.11.0", features = ["cuda"] }
# or for Metal:
candle-core = { version = "0.11.0", features = ["metal"] }
# or for MKL:
candle-core = { version = "0.11.0", features = ["mkl"] }
```

## Zero-Cost Patterns

Since Beer has no income, all HF Candle usage must be free:

| Goal | Free Method |
|------|-------------|
| **Try Candle** | `cargo new test-candle && cd test-candle && cargo add candle-core && cargo run` (runs on CPU) |
| **Run a model** | Use `cargo run --example quantized --release` from candle repo clone |
| **Browser demo** | Use HF Spaces: https://huggingface.co/spaces/lmz/candle-llama2 |
| **WASM in browser** | Build with `trunk` for client-side inference |
| **HF Inference** | No Candle needed — use HF Inference API directly |
| **GPU** | Candle CUDA requires NVIDIA hardware (not available on free infra) |

## Comparison: Candle vs Other Rust ML Frameworks

| | Candle | burn | tch-rs | dfdx |
|---|---|---|---|---|
| **Backend** | CPU/CUDA/Metal/WASM | Multiple | PyTorch | Rust-native |
| **Python-free** | ✅ | ✅ | ❌ (needs libtorch) | ✅ |
| **HF integration** | Native | Partial | Via Python | None |
| **WASM** | ✅ Built-in | Partial | ❌ | ❌ |
| **Model zoo** | 30+ models | Limited | All PyTorch | Few |
| **Training** | Basic | ✅ Full | Full | Full |
| **Binary size** | ~5-10 MB | ~10 MB | ~1 GB+ (w/ libtorch) | ~5 MB |

## Key Architectural Details

### Tensor Storage
- Tensors use **contiguous row-major** layout by default
- `safetensors` format loads via **memory-mapped (mmap)** I/O — zero-copy for inference
- DTypes: F32, F16, BF16, F8 (E4M3, E5M2), I64, I32, I16, I8, U8, BOOL

### Module System (candle-nn)
Like PyTorch's `nn.Module`, but in Rust:
```rust
use candle_nn::{Linear, Module};
let linear = Linear::new(weights, bias, config)?;
let output = linear.forward(&input)?;
```

### Auto-diff
- Limited compared to PyTorch
- `Var` wrapper type tracks gradient tape
- Primarily designed for **inference** — training support exists but is less mature

### Hub Integration
- Models can be loaded directly from HF Hub URLs
- Uses `huggingface-hub` Rust crate for downloading
- Candle reads safetensors files directly from cache

## Resources
- [GitHub Repo](https://github.com/huggingface/candle)
- [Candle Book (docs)](https://huggingface.github.io/candle/)
- [crates.io: candle-core](https://crates.io/crates/candle-core)
- [HF Spaces demos](https://huggingface.co/spaces/lmz/candle-llama2)
- [candle-lora](https://github.com/EricLBuehler/candle-lora) — LoRA for Candle
- [candle-vllm](https://github.com/EricLBuehler/candle-vllm) — vLLM-like serving for Candle
