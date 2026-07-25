# Diffusers Pipeline Reference

> Condensed lookup table for the Hugging Face Diffusers library (v0.39.0+).
> Source: hf.co/docs/diffusers, GitHub README, and the Diffusion Models Course.

## Current Version

Latest stable: **v0.39.0** (July 2025) — supports 30+ pipeline types.
Install: `pip install --upgrade diffusers[torch]`
Bleeding edge: `pip install git+https://github.com/huggingface/diffusers.git`

## Task → Pipeline → Hub Model ID

| Task | Pipeline Class | Recommended Hub ID | Params |
|------|---------------|-------------------|--------|
| Text-to-Image (SD 1.5) | `StableDiffusionPipeline` | `stable-diffusion-v1-5/stable-diffusion-v1-5` | ~860M UNet |
| Text-to-Image (SDXL) | `StableDiffusionXLPipeline` | `stabilityai/stable-diffusion-xl-base-1.0` | 2.6B UNet |
| Text-to-Image (SD3.5) | `StableDiffusion3Pipeline` | `stabilityai/stable-diffusion-3.5-medium` | 2.5B MMDiT |
| Text-to-Image (FLUX) | `FluxPipeline` | `black-forest-labs/FLUX.1-dev` | 12B DiT |
| Text-to-Image (Kandinsky) | `KandinskyPipeline` | `kandinsky-community/kandinsky-2-2-decoder` | 1.2B prior |
| Text-to-Image (DeepFloyd) | `IFPipeline` | `DeepFloyd/IF-I-XL-v1.0` | 4B T5-XXL |
| Image-to-Image | `StableDiffusionImg2ImgPipeline` | same SD model ID (pass `image` + `strength`) | — |
| Inpainting | `StableDiffusionInpaintPipeline` | `stable-diffusion-v1-5/stable-diffusion-inpainting` | special mask UNet |
| ControlNet | `StableDiffusionControlNetPipeline` | SD base + `lllyasviel/sd-controlnet-canny` | ~350M ControlNet |
| InstructPix2Pix | `StableDiffusionInstructPix2PixPipeline` | `timbrooks/instruct-pix2pix` | SD 1.5 fine-tune |
| Video (AnimateDiff) | `AnimateDiffPipeline` | SD base + `guoyww/animatediff-motion-adapter-v1-5-2` | motion module |
| Video (CogVideoX) | `CogVideoXPipeline` | `THUDM/CogVideoX-5b` | 5B 3D transformer |
| Video (Mochi-1) | `MochiPipeline` | `genmo/mochi-1-preview` | 10B DiT |
| Audio (Stable Audio) | `StableAudioPipeline` | `stabilityai/stable-audio-open-1.0` | latent diffusion |
| Upscale (SD x4) | `StableDiffusionUpscalePipeline` | `stabilityai/stable-diffusion-x4-upscaler` | |
| Upscale (Latent) | `StableDiffusionLatentUpscalePipeline` | `stabilityai/sd-x2-latent-upscaler` | |

## Scheduler Quick-Reference

| Scheduler | Steps | Quality | Speed | Use Case |
|-----------|-------|---------|-------|----------|
| `DDPMScheduler` | 1000 | high | slow | Training only |
| `DDIMScheduler` | 10-50 | good | fast | Inference, inversion |
| `PNDMScheduler` | 50 | fair | medium | Legacy SD 1.x |
| `DPMSolverMultistepScheduler` | 4-10 | high | fast | **Default for quality** |
| `EulerDiscreteScheduler` | 10-50 | good | fast | Flow matching, generic |
| `FlowMatchEulerDiscreteScheduler` | 4-28 | high | fast | SD3, FLUX, rectified flow |
| `LMSDiscreteScheduler` | 50-100 | fair | medium | Stable alternative |
| `DPMSolverSinglestepScheduler` | 3-10 | high | fastest | Single-step DPM |

Swap any scheduler: `pipe.scheduler = NewScheduler.from_config(pipe.scheduler.config)`

## Memory Optimization Ladder (GPU-poor environments)

Order from least to most aggressive:

1. `pipe.enable_attention_slicing()` — reduces peak memory ~30%
2. `pipe.to(torch.float16)` — halves memory
3. `pipe.enable_vae_tiling()` — for high-res images >1024px
4. `pipe.enable_model_cpu_offload()` — moves submodules to CPU between runs
5. `pipe.enable_sequential_cpu_offload()` — most aggressive, submodule-by-submodule

Performance (GPU-rich):
- `pipe.unet = torch.compile(pipe.unet, mode="reduce-overhead", fullgraph=True)` — 30-50% speedup
- `pipe.enable_xformers_memory_efficient_attention()` — requires xformers installed

## Diffusion Models Course Units

https://huggingface.co/learn/diffusion-course

| Unit | Topic | Key Notebooks | Theory Papers |
|------|-------|---------------|---------------|
| 0 | Orientation | — | — |
| 1 | Intro to Diffusion | DDPM from scratch, training on MNIST | DDPM (Ho et al. 2020) |
| 2 | Fine-tuning & Guidance | Load pretrained, CFG scale, custom data | Classifier-Free Guidance (Ho & Salimans 2021) |
| 3 | Stable Diffusion | Text-to-image, img2img, inpainting, cross-attention | LDM (Rombach et al. 2022) |
| 4 | Advanced Techniques | DDIM inversion, custom pipelines, audio, deployment | Various |

## Common Pitfalls (Quick Reference)

- **Model licenses vary.** SD 1.5 = CreativeML Open RAIL-M, FLUX.1-dev = Apache 2.0, SD3 = custom research. Read the model card.
- **`runwayml/stable-diffusion-v1-5` is deprecated.** Use `stable-diffusion-v1-5/stable-diffusion-v1-5`.
- **Gated models need login + terms acceptance.** Run `huggingface-cli login` and accept on the Hub page.
- **Different schedulers != different quality.** A bad scheduler choice can make a great model look terrible. Try DPM++ first.
- **Batched generation OOMs fast.** Start with batch=1, enable attention slicing, then increase.
