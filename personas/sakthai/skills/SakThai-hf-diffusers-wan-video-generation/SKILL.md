---
name: SakThai-hf-diffusers-wan-video-generation
author: SakThai
license: MIT
description: Comprehensive knowledge of the Wan2.1/Wan2.2 video generation model family and its integration into Hugging Face Diffusers — covering all pipelines, architecture, scheduler options, memory optimization, LoRA support, and usage patterns.
version: 1.0.0
category: mlops
tags: [huggingface, diffusers, video-generation, wan, diffusion]
---

# hf-diffusers-wan-video-generation

**Author:** SakThai  
**License:** MIT

## Description

Comprehensive knowledge of the **Wan2.1 / Wan2.2** video generation model family and its integration into Hugging Face Diffusers. Covers all pipelines (T2V, I2V, FLF2V, VACE, Animate, Video2Video), model architecture (WanTransformer3D, AutoencoderKLWan), scheduler options (FlowMatchEuler, UniPCMultistep), memory optimization, LoRA support, and usage patterns.

## Key Commands

```python
# Text-to-Video (1.3B — consumer GPU friendly)
from diffusers import AutoModel, WanPipeline
pipe = WanPipeline.from_pretrained("Wan-AI/Wan2.1-T2V-1.3B-Diffusers", torch_dtype=torch.bfloat16)
pipe.to("cuda")
output = pipe(prompt="A cat baking a cake", num_frames=81, guidance_scale=5.0).frames[0]

# Image-to-Video
from diffusers import WanImageToVideoPipeline
pipe = WanImageToVideoPipeline.from_pretrained("Wan-AI/Wan2.1-I2V-14B-480P-Diffusers", ...)
output = pipe(image=image, prompt=prompt, height=480, width=832).frames[0]

# LoRA loading
pipe.load_lora_weights("benjamin-paine/steamboat-willie-1.3b", adapter_name="steamboat-willie")
pipe.set_adapters("steamboat-willie")

# Single-file loading (ComfyUI repackaged)
transformer = WanTransformer3DModel.from_single_file("https://...wan2.1_t2v_1.3B_bf16.safetensors")
vae = AutoencoderKLWan.from_single_file("https://...wan_2.1_vae.safetensors")
pipe = WanPipeline.from_pretrained("Wan-AI/Wan2.1-T2V-1.3B-Diffusers", transformer=transformer, vae=vae)
```

## Related Skills
- `hf-diffusers-cogvideo` — CogVideoX pipeline (alternative video generation)
- `hf-diffusers-video-generation-pipeline` — generic video pipeline patterns
- `hf-diffusers-flux` — Flux image pipeline (same codebase family)
