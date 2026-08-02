---
name: SakThai-bonsai-27b-1bit
description: |
  Bonsai 27B by Prism ML — a true 1-bit (Q1_0_g128) LLM derived from Qwen3.6-27B.
  3.9 GB footprint, ~90% FP16 intelligence, runs in-browser via WebGPU.
  Companion ternary variant at ~7.2 GB (~95% FP16).
references:
  - model: prism-ml/Bonsai-27B-gguf
  - mlx: prism-ml/Bonsai-27B-mlx-1bit
  - ternary: prism-ml/Ternary-Bonsai-27B-gguf
  - space: webml-community/bonsai-webgpu-kernels
  - whitepaper: https://github.com/PrismML-Eng/Bonsai-demo/blob/main/bonsai-27b-whitepaper.pdf
  - llama.cpp fork: https://github.com/PrismML-Eng/llama.cpp
---

# Bonsai 27B — True 1-bit LLM

## Overview

Bonsai 27B is a **true 1-bit** (1.125 bits/weight) LLM by [Prism ML](https://prismml.com), derived from
**Qwen3.6-27B** with hybrid attention (≈75% linear + ≈25% full attention). It is the most extreme
low-bit operating point in the Bonsai family: weights are binary {−1, +1} with FP16 group-wise
scaling every 128 weights.

| Metric | Value |
|--------|-------|
| Footprint | **3.9 GB** (vs 54 GB FP16 — 14.2× reduction) |
| Intelligence retention | **~90% of FP16** (76.11 avg across 15 thinking benchmarks) |
| Context length | **262K tokens** on-device |
| Throughput (M5 Pro) | 44 tok/s |
| Throughput (M5 Max) | 66 tok/s |
| Throughput (H100) | 105 tok/s |
| Decode energy (M5 Pro) | 0.275 mWh/token |
| License | Apache 2.0 |

## Architecture

- **Backend**: llama.cpp with custom Q1_0_g128 hybrid-attention kernels (CUDA, Metal)
- **Weight format**: GGUF Q1_0_g128 — sign bit + FP16 scale per 128-weight group
- **Low-bit coverage**: Embeddings, attention projections, MLP projections, LM head — *no* high-precision escapes
- **KV cache**: 4-bit quantization; 16/64 layers use full attention cache (~4.3 GB at 262K)
- **Optional DSpark drafter**: 1.79 GB Q4_1 for 1.37× speculative-decode speedup
- **Optional vision tower**: HQQ 4-bit mmproj (0.63 GB), loaded only for image input

## Benchmark Performance

Averages across 15 thinking-mode benchmarks (compared to FP16 baseline):

| Category | Score | % of FP16 |
|----------|-------|-----------|
| Overall (avg) | 76.11 | 89.5% |
| Math | 91.66 | — |
| Coding | 81.88 | — |

## Deployment

### WebGPU (Browser)
The Space at [webml-community/bonsai-webgpu-kernels](https://huggingface.co/spaces/webml-community/bonsai-webgpu-kernels)
runs the full 27B model in-browser via WebGPU — a static Space, no GPU backend required.

### Local via llama.cpp
```bash
# Prism ML fork with 1-bit kernels
git clone https://github.com/PrismML-Eng/llama.cpp
cd llama.cpp && cmake -B build -DGGML_CUDA=ON && cmake --build build -j
hf download prism-ml/Bonsai-27B-gguf Bonsai-27B-Q1_0.gguf --local-dir .
./build/bin/llama-cli -m Bonsai-27B-Q1_0.gguf -p "Your prompt" -n 256 -ngl 99
```

### MLX (Apple Silicon)
Available as [Bonsai-27B-mlx-1bit](https://huggingface.co/prism-ml/Bonsai-27B-mlx-1bit) including
iPhone via MLX Swift (~11 tok/s on iPhone 17 Pro Max).

## Variants

| Variant | Footprint | Quality | Use Case |
|---------|-----------|---------|----------|
| 1-bit (Q1_0_g128) | 3.9 GB | ~90% FP16 | Extreme compression, on-device |
| Ternary (TQ1_0) | ~7.2 GB | ~95% FP16 | Quality-oriented, still laptop-class |

## Why This Matters for Beer's Ecosystem

- **Zero-cost inference**: 3.9 GB fits Beer's available hardware without paid GPUs
- **WebGPU Space**: Free inference via HF Spaces (static, no GPU cost)
- **Apache 2.0**: No restrictions on use
- **1-bit frontier**: Represents the bleeding edge of model compression — useful for
  comparison with GGUF quants Beer already works with
