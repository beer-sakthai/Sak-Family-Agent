# AuraSR-v2 — Case Study (2026-07-23)

**Space:** `gokaygokay/AuraSR-v2`
**Model:** `fal/AuraSR-v2`
**Likes:** 622 · **Runtime:** ZeroGPU (free GPU)
**SDK:** Gradio with `ImageSlider` component
**Category:** Image-to-image (super-resolution)

## What it is

GAN-based 4× image upscaler by fal.ai, reproducing Adobe's GigaGAN architecture. Takes any image and produces a 4× higher-resolution version in a single forward pass (~0.25s on GPU).

## Tech stack

- `aura-sr` Python package (PyTorch, 600M params, GAN generator)
- Gradio `ImageSlider` for before/after comparison
- `@spaces.GPU` decorator (ZeroGPU)
- `upscale_4x_overlapped` method eliminates seam artifacts via overlapping tile averaging

## Key difference from diffusion upscalers

GAN-based: single forward pass, ~0.25s for 4× upscale. Compare to diffusion-based models that take multiple denoising steps (10–50× slower). The tradeoff is different output characteristics — GANs produce sharper but potentially less natural textures.

## Training improvement from v1→v2

1. **Tile-stratified training:** v1 trained on full 256→64px image pairs but inferred on tiles of larger images. v2 trains on 256px tiles cropped from 1024px images, matching inference distribution.
2. **Degradation augmentation:** v2 added JPG compression simulation so it works on real photos, not just AI-generated art.
3. **Overlapping inference:** v2's `upscale_4x_overlapped` runs two passes and averages overlapping tiles to remove seams.

## Discovery method

Found via EXA_SEARCH with query `"huggingface spaces trending popular new July 2026"`. The result led to the Spaces trending page which listed AuraSR-v2 as a "Space of the week" (Apr 13, 2026). Follow-up EXA_SEARCH with `"AuraSR-v2 huggingface space super resolution ZeroGPU fal.ai trending"` gathered full details.

## Why notable for the skill

- Demonstrates that EXA web search is a reliable primary discovery method (not just fallback to HF API)
- Shows ZeroGPU + Gradio pattern for computationally heavy models
- Good example of GAN-based approach vs diffusion — relevant for architecture comparison reports
