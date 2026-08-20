---
name: SakThai-hf-inference-client-image-generation
description: Using Hugging Face InferenceClient for image generation via serverless inference API.
  Covers text-to-image, image-to-image, inpainting, and controlnet through hf_hubs
  InferenceClient.
...
---

# InferenceClient Image Generation Patterns

## Overview
Hugging Face's `InferenceClient` provides a serverless API for image generation models without needing local GPUs. This skill covers all image generation endpoints, parameter tuning, and error handling patterns.

## API Methods

| Method | Description |
|--------|-------------|
| `text_to_image()` | Text-to-image generation (SD, Flux, SDXL) |
| `image_to_image()` | Image-to-image with prompt guidance |
| `inpaint()` | Inpainting with mask |
| `controlnet()` | ControlNet-conditioned generation |

See `references/hf-learnings.md` for the full deep dive.
