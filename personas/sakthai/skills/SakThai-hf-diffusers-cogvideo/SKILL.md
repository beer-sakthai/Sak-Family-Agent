---
name: SakThai-hf-diffusers-cogvideo
description: "Expertise in CogVideoX \u2014 large diffusion transformer for text-to-video, image-to-video,\
  \ and video-to-video generation, integrated as a first-class Diffusers pipeline."
---

## Description

Expertise in CogVideoX — a large diffusion transformer model for text-to-video, image-to-video, and video-to-video generation, integrated as a first-class Diffusers pipeline. Covers the 3D causal VAE architecture, expert transformer with adaptive LayerNorm, T5 text encoder, DDIM/DPM schedulers, memory optimization (CPU offloading, tiling, quantization), LoRA support, and the CogVideoXFunControl pipeline for controlled generation with spatial conditioning.

Skills in this subtree:
- **CogVideoXPipeline** — text-to-video generation (2B and 5B parameter variants)
- **CogVideoXImageToVideoPipeline** — image-to-video generation with reference frame conditioning
- **CogVideoXVideoToVideoPipeline** — video-to-video translation with configurable strength
- **CogVideoXFunControlPipeline** — controlled video generation with spatial control signals
- Memory optimization: model CPU offload, sequential CPU offload, tiling, torchao int8 quantization, FP8 layerwise casting, group offloading

## Key Components

| Component | Description |
|-----------|-------------|
| `CogVideoXPipeline` | T2V pipeline, uses T5 text encoder + 3D VAE + DiT |
| `AutoencoderKLCogVideoX` | 3D causal VAE compressing spatial+temporal dimensions |
| `CogVideoXTransformer3DModel` | Expert DiT with adaptive LayerNorm for text-video fusion |
| `CogVideoXDDIMScheduler` / `CogVideoXDPMScheduler` | Custom schedulers for CogVideoX denoising |
| `CogVideoXFunControlPipeline` | Controlled T2V with spatial control_video input |

## Checkpoints

| Model | Parameters | Best For |
|-------|-----------|----------|
| `THUDM/CogVideoX-2b` | 2B | Lighter inference, ~12GB VRAM |
| `THUDM/CogVideoX-5b` | 5B | Higher quality, ~16GB VRAM (quantized) |
| `zai-org/CogVideoX-5b-I2V` | 5B | Image-to-video generation |

## Resources

- Diffusers docs: https://huggingface.co/docs/diffusers/main/en/api/pipelines/cogvideox
- Paper: https://arxiv.org/abs/2408.06072
- HF Collection: https://huggingface.co/collections/.../cogvideox
- Learnings: references/hf-learnings.md
