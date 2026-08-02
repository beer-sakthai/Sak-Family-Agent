---
name: SakThai-hf-diffusers
description: "Hugging Face Diffusers: diffusion model library for image, video, and audio generation. Covers DiffusionPipeline, schedulers, memory optimizations, training examples, and component interoperability."
tags: [huggingface, diffusers, diffusion, stable-diffusion, schedulers, inference, training]
version: 1.0.0
---

# Hugging Face Diffusers — Diffusion Models Library

**🤗 Diffusers** is a library of state-of-the-art pretrained diffusion models for generating **videos, images, and audio**. It is built around the `DiffusionPipeline` API, designed for:

- Easy inference with only a few lines of code
- Flexibility to mix-and-match pipeline components (models, schedulers)
- Loading and using adapters like LoRA
- Memory-constrained inference via offloading, quantization, and torch.compile

Current stable docs version: **v0.38.0**.

## Core Architecture

| Component | Role |
|-----------|------|
| `DiffusionPipeline` | Bundles all models, schedulers, and processors into a single end-to-end class. |
| `SchedulerMixin` | Base class for all schedulers; handles denoising step logic and timestep formatting. |
| Models (UNet, DiT, VAE, etc.) | The actual learned networks used inside a pipeline. |
| Processors | Image/audio/video processors (e.g., `VaeImageProcessor`, `VideoProcessor`). |

### Loading a Pipeline

```python
from diffusers import StableDiffusionPipeline

pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    device_map="auto",        # automatic sharding across GPUs
    use_safetensors=True,
)
pipe.enable_attention_slicing()
image = pipe("A cat riding a bicycle").images[0]
```

Key `from_pretrained` options:
- `torch_dtype` — reduce memory with `float16` or `bfloat16`.
- `variant` — load specific weight variants (e.g., `"fp16"`).
- `use_safetensors` — prefer safe serialization format.
- `use_onnx` — load ONNX weights for CPU/accelerator inference.
- `trust_remote_code` — allow custom model code from the Hub (only for trusted repos).
- `local_files_only` — offline loading from cache.

### Reusing Components

`DiffusionPipeline.components` returns the underlying modules so they can be shared across pipeline types:

```python
text2img = StableDiffusionPipeline.from_pretrained("base-model")
img2img = StableDiffusionImg2ImgPipeline(**text2img.components)
inpaint = StableDiffusionInpaintPipeline(**text2img.components)
```

## Pipeline Ecosystem

Diffusers supports dozens of task-specific pipelines. Representative examples:

| Pipeline | Tasks |
|----------|-------|
| Stable Diffusion / SDXL / SD3 | text2image, img2img, inpainting |
| ControlNet | spatial conditioning (canny, depth, pose) over SD/SDXL/Flux |
| Flux | text2image (DiT-based) |
| CogVideoX | text2video |
| AudioLDM2 / LongCat-AudioDiT | text2audio |
| Shap-E | text2image, image-to-3D |
| Stable Audio | music / SFX generation |
| PixArt-α / PixArt-Σ | text2image |
| Marigold | depth, normals, intrinsic image estimation |

> Pipelines are **inference-only** (`torch.no_grad` is applied). For training individual components (UNet, DiT, VAE), use the underlying model classes directly.

## Schedulers

A scheduler defines how noise is added during training and how a sample is denoised during inference. Diffusers includes many schedulers, many ported from [k-diffusion](https://github.com/crowsonkb/k-diffusion) and compatible with Automatic1111 / ComfyUI mappings.

### Scheduler Families

| k-diffusion / A1111 | 🤗 Diffusers Class | Notes |
|---------------------|--------------------|-------|
| Euler | `EulerDiscreteScheduler` | |
| Euler a | `EulerAncestralDiscreteScheduler` | ancestral variant adds stochastic noise |
| DPM++ 2M | `DPMSolverMultistepScheduler` | fast multistep solver |
| DPM++ 2M Karras | `DPMSolverMultistepScheduler(use_karras_sigmas=True)` | Karras sigmas improve quality |
| DPM++ SDE | `DPMSolverSinglestepScheduler` | |
| LMS | `LMSDiscreteScheduler` | |
| DDIM | `DDIMScheduler` | deterministic, fast |
| UniPC | `UniPCMultistepScheduler` | unified predictor-corrector |

### Discrete vs Continuous Timesteps

- **Discrete** schedulers use integer `timestep` indices.
- **Continuous** schedulers use float `sigmas` (e.g., `KarrasStableDiffusionScheduler` with `use_karras_sigmas=True`).

Noise schedule options map as:

| A1111 schedule | Diffusers init |
|----------------|----------------|
| `simple` / `sgm_uniform` | `timestep_spacing="trailing"` |
| `exponential` | `use_exponential_sigmas=True`, `timestep_spacing="linspace"` |
| `beta` | `use_beta_sigmas=True`, `timestep_spacing="linspace"` |
| `Karras` | `use_karras_sigmas=True` |

## Memory & Inference Optimizations

Diffusers is designed to run on memory-constrained hardware through multiple optimization layers:

1. **Attention slicing** — `pipe.enable_attention_slicing()` reduces peak memory by chunking attention.
2. **xFormers** — `pipe.enable_xformers_memory_efficient_attention()` if `xformers` is installed.
3. **torch.compile** — wrap the UNet or full pipeline with `torch.compile` for speed.
4. **CPU / disk offloading** — `pipe.enable_model_cpu_offload()` / `pipe.enable_sequential_cpu_offload()` moves layers to CPU when inactive.
5. **Quantization** — 8-bit and 4-bit inference via `bitsandbytes` or `torchao`.
6. **ONNX runtime** — `use_onnx=True` loads `.onnx` weights for non-CUDA backends.

## Training Overview

Diffusers ships **beginner-friendly, single-purpose training scripts** in `diffusers/examples/`. Each script is self-contained with its own `requirements.txt`.

Active training examples (v0.38.0):

| Example | SDXL | LoRA |
|---------|------|------|
| unconditional image generation | — | — |
| text-to-image | ✅ | ✅ |
| textual inversion | — | — |
| DreamBooth | ✅ | ✅ |
| ControlNet | ✅ | — |
| InstructPix2Pix | ✅ | — |
| Custom Diffusion | — | — |
| T2I-Adapters | ✅ | — |
| Kandinsky 2.2 | — | ✅ |

Best practices for training:
- Use **PyTorch 2.0+** to automatically enable scaled dot-product attention.
- Install `xFormers` to enable memory-efficient attention during training.
- Prefer **fp16 / bf16** mixed precision to reduce VRAM.
- `accelerate` is recommended but not required; scripts can be adapted to custom loops.

## Adapters (LoRA / LoHa / etc.)

Diffusers integrates directly with PEFT-style adapters:

```python
pipe.load_lora_weights("path/to/lora")
# or from Hub:
pipe.load_lora_weights("user/model", weight_name="pytorch_lora_weights.safetensors")
pipe.unload_lora_weights()
```

Adapters can be merged into the base model weights or kept dynamically switchable.

## Key Design Principles

- **Modularity**: Pipelines are thin wrappers; every component (model, scheduler, processor) is independently loadable.
- **Hub-first**: All components are first-class citizens on the Hugging Face Hub; `from_pretrained` abstracts downloading/caching.
- **Safety**: Safetensors is the default format when available.
- **Inference-only contract**: Pipelines disable autograd (`torch.no_grad`) — they should not be used for training.

## Useful Docs & Resources

- **Main docs**: https://huggingface.co/docs/diffusers
- **GitHub**: https://github.com/huggingface/diffusers
- **Pipelines overview**: https://huggingface.co/docs/diffusers/v0.38.0/en/api/pipelines/overview
- **Schedulers**: https://huggingface.co/docs/diffusers/v0.38.0/en/api/schedulers/overview
- **Training overview**: https://huggingface.co/docs/diffusers/v0.38.0/en/training/overview
- **Optimization guide**: https://huggingface.co/docs/diffusers/main/en/optimization
- **Diffusion course**: https://huggingface.co/learn/diffusion-course/unit0/1
- **Scheduler mapping cheat sheet**: `references/scheduler-mapping.md` (A1111 / k-diffusion → Diffusers equivalences)
