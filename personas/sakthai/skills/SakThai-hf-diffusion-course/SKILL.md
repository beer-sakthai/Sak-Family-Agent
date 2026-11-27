---
name: SakThai-hf-diffusion-course
version: 1.0.0
description: Comprehensive guide to Hugging Face Diffusers library (v0.39+) — pipelines,
  schedulers, models, training, optimization, and the Diffusion Models Course. Covers
  image, video, audio, and 3D generation.
category: mlops
tags:
- audiogeneration
- controlnet
- course
- diffusers
- diffusion
- flux
- hf
- huggingface
- imagegeneration
- lora
- sd3
- stablediffusion
- videogeneration
author: SakThai
license: MIT
---

# Hugging Face Diffusers & Diffusion Models Course

The [Diffusers library](https://huggingface.co/docs/diffusers) is the go-to toolkit for state-of-the-art diffusion models — images, video, audio, and 3D molecular structures. Design philosophy: **usability over performance**, **simple over easy**, **customizability over abstractions**.

Current version: **v0.39.0** (July 2025). GitHub: https://github.com/huggingface/diffusers

The Free [Hugging Face Diffusion Models Course](https://huggingface.co/learn/diffusion-course) (Apache 2.0) covers theory + practice: DDPM, fine-tuning, Stable Diffusion, guidance, and advanced techniques — 4 units, 6-8h/week each.

## When to Use

- Generate images from text (Stable Diffusion, FLUX, SD3, Kandinsky)
- Image-to-image, inpainting, ControlNet-guided generation
- Video generation (AnimateDiff, CogVideoX, Mochi-1)
- Audio/music generation
- Fine-tune diffusion models with LoRA/DreamBooth/Textual Inversion
- Build custom diffusion pipelines from components
- 3D molecular generation

## Installation

```bash
# Core (PyPI)
pip install --upgrade diffusers[torch]

# With Conda
conda install -c conda-forge diffusers

# With training support
pip install diffusers[training] accelerate tensorboard

# With video pipelines
pip install diffusers[torch] transformers accelerate

# Repository (bleeding edge)
pip install git+https://github.com/huggingface/diffusers.git
```

## Core Architecture

Diffusers has **three core components** that can be mixed and matched:

### 1. DiffusionPipeline
The high-level API. Load with `from_pretrained()` — auto-detects architecture.

```python
from diffusers import DiffusionPipeline
import torch

pipe = DiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16
)
pipe.to("cuda")
image = pipe("A cat in space").images[0]
```

### 2. Models (denoising backbones)
| Model | Description |
|-------|-------------|
| `UNet2DModel` | Unconditional image denoising (DDPM) |
| `UNet2DConditionModel` | Conditional denoising (text, class, image) |
| `AutoencoderKL` (VAE) | Encode/decode between pixel and latent space |
| `FluxTransformer2DModel` | DiT-based transformer for FLUX/SD3 flow matching |
| `CogVideoXTransformer3DModel` | 3D transformer for video diffusion |

### 3. Schedulers
Controls the denoising process. Swap between different schedulers.

## End-to-End Text-to-Image Pipeline

### Basic T2I with Stable Diffusion
```python
from diffusers import DiffusionPipeline
import torch

# Load pipeline
pipe = DiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16",
    use_safetensors=True,
)
pipe.to("cuda")

# Optional: swap scheduler for faster inference
from diffusers import DPMSolverMultistepScheduler
pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config, use_karras_sigmas=True
)

# Generate
prompt = "A majestic dragon flying over a cyberpunk city, digital art, 4K"
image = pipe(
    prompt=prompt,
    negative_prompt="blurry, low quality, distorted",
    num_inference_steps=25,
    guidance_scale=7.5,
    width=1024,
    height=1024,
).images[0]
image.save("dragon.png")
```

### T2I with FLUX (Flow Matching)
```python
from diffusers import FluxPipeline
import torch

# FLUX.1-dev requires ~24GB VRAM
pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev",
    torch_dtype=torch.bfloat16
)
pipe.to("cuda")
pipe.enable_model_cpu_offload()  # Reduces peak memory

image = pipe(
    "A serene Japanese garden in autumn, falling leaves, pond with koi fish",
    guidance_scale=3.5,
    num_inference_steps=50,
    width=1024,
    height=1024,
).images[0]
image.save("garden.png")
```

### T2I with SD3.5
```python
from diffusers import StableDiffusion3Pipeline
import torch

pipe = StableDiffusion3Pipeline.from_pretrained(
    "stabilityai/stable-diffusion-3.5-medium",
    torch_dtype=torch.float16,
)
pipe.to("cuda")
pipe.enable_model_cpu_offload()

image = pipe(
    "A cinematic shot of a astronaut riding a horse on Mars, dramatic lighting",
    negative_prompt="blurry, low quality",
    num_inference_steps=28,
    guidance_scale=7.0,
).images[0]
```

### Batched Generation
```python
prompts = [
    "A cat in a spacesuit",
    "A dog wearing sunglasses",
    "A bird reading a book",
    "A fish riding a bicycle",
]
images = pipe(prompts, num_images_per_prompt=1).images
for i, img in enumerate(images):
    img.save(f"output_{i}.png")
```

### Image-to-Image Pipeline
```python
from diffusers import StableDiffusionImg2ImgPipeline
from PIL import Image

pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
).to("cuda")

init_image = Image.open("photo.jpg").convert("RGB").resize((512, 512))
image = pipe(
    prompt="turn into van gogh painting style",
    image=init_image,
    strength=0.75,  # 0.0 = no change, 1.0 = completely new
    guidance_scale=7.5,
).images[0]
```

### Inpainting Pipeline
```python
from diffusers import StableDiffusionInpaintPipeline
from PIL import Image
import numpy as np

pipe = StableDiffusionInpaintPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-inpainting",
    torch_dtype=torch.float16,
).to("cuda")

init_image = Image.open("room.jpg").convert("RGB")
mask_image = Image.open("mask.png").convert("RGB")  # White = area to inpaint

image = pipe(
    prompt="a modern sofa with velvet upholstery",
    image=init_image,
    mask_image=mask_image,
    strength=0.8,
    guidance_scale=7.5,
).images[0]
```

## Schedulers Comparison

| Scheduler | Typical Steps | Quality | Speed | Best For |
|-----------|--------------|---------|-------|----------|
| `DDPMScheduler` | 1000 | Reference | Slow | Training DDPM from scratch |
| `DDIMScheduler` | 20-50 | Good | Fast | Deterministic generation, inversion |
| `PNDMScheduler` | 20-50 | Good | Fast | Legacy SD 1.x (pseudo numerical) |
| `DPMSolverMultistepScheduler` | 4-10 | Best | Fastest | General inference with Karras sigmas |
| `DPMSolverSinglestepScheduler` | 3-6 | Good | Very Fast | Ultra-fast generation |
| `EulerDiscreteScheduler` | 20-30 | Good | Fast | General-purpose, flow matching |
| `EulerAncestralDiscreteScheduler` | 20-30 | Good | Fast | More creative variation (ancestral noise) |
| `LMSDiscreteScheduler` | 20-50 | Good | Fast | Stable alternative to DDIM |
| `FlowMatchEulerDiscreteScheduler` | 20-50 | Best | Fast | Rectified flow models (SD3, FLUX) |
| `DEISMultistepScheduler` | 5-15 | Good | Fast | Exponential integrator method |
| `HeunDiscreteScheduler` | 20-50 | High | Moderate | Improved ODE solver accuracy |

### Scheduler Selection Guide

```python
# Fast (DPM++ with Karras) — best quality per step
from diffusers import DPMSolverMultistepScheduler
pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config, use_karras_sigmas=True, algorithm_type="sde-dpmsolver++"
)
# Use 8-12 steps for good quality, 20 for best

# Deterministic (DDIM) — for reproducibility and inversion
from diffusers import DDIMScheduler
pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
# Same seed + prompt = same image

# Flow Matching (SD3, FLUX)
from diffusers import FlowMatchEulerDiscreteScheduler
pipe.scheduler = FlowMatchEulerDiscreteScheduler.from_config(pipe.scheduler.config)
# Default for SD3/FLUX pipelines

# Ultra-fast (DPM++ Single)
from diffusers import DPMSolverSinglestepScheduler
pipe.scheduler = DPMSolverSinglestepScheduler.from_config(pipe.scheduler.config)
# 4-5 steps, good for quick iteration
```

---

## Deep Dive Reference

For exhaustive reference specifications, cookbook snippets, and extended documentation, see [Diffusion ControlNet, Video Generation & Training Guide](./references/diffusion-controlnet-video-and-training.md).
