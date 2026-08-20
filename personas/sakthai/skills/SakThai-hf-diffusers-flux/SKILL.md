---
name: SakThai-hf-diffusers-flux
description: "Comprehensive reference for Hugging Face Diffusers integration with Black Forest Labs Flux models (FLUX.1-dev, FLUX.1-schnell). Covers FluxPipeline, FluxFillPipeline, FluxControlPipeline, IP-Adapter, LoRA stacking, optimization techniques (group offl"
---

# SakThai-hf-diffusers-flux

## Overview

Flux is a family of text-to-image generation models by Black Forest Labs, integrated into Hugging Face Diffusers (v0.39.0+). The Flux models use a rectified flow transformer architecture with dual text encoders (CLIP-L + T5-XXL) and produce high-quality 1024×1024 images.

## Available Pipelines

| Pipeline | Class | Description |
|----------|-------|-------------|
| FluxPipeline | `diffusers.FluxPipeline` | Text-to-image generation (dev + schnell variants) |
| FluxFillPipeline | `diffusers.FluxFillPipeline` | Inpainting / image-filling with mask |
| FluxControlPipeline | `diffusers.FluxControlPipeline` | ControlNet-based conditioning (depth, Canny, etc.) |
| FluxImg2ImgPipeline | `diffusers.FluxImg2ImgPipeline` | Image-to-image generation |

All four pipelines can also be loaded via `DiffusionPipeline` (auto-detection from model ID).

## Basic Usage

### Text-to-Image (FLUX.1-dev)

```python
import torch
from diffusers import FluxPipeline

pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev", dtype=torch.bfloat16
).to("cuda")

prompt = "A cat holding a sign that says hello world"
image = pipe(
    prompt=prompt,
    guidance_scale=3.5,
    height=1024,
    width=1024,
    num_inference_steps=50,
    max_sequence_length=512,
    generator=torch.Generator("cuda").manual_seed(0),
).images[0]
image.save("flux-dev.png")
```

### FLUX.1-schnell (4-step fast mode)

```python
pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-schnell", dtype=torch.bfloat16
).to("cuda")

image = pipe(
    prompt="A cat holding a sign that says hello world",
    guidance_scale=0.0,          # schnell uses 0 guidance
    height=1024,
    width=1024,
    num_inference_steps=4,       # 4-step distilled model
    max_sequence_length=256,
).images[0]
```

> **Note:** `guidance_scale` must be 0 for schnell. For dev, typical range is 3.0–10.0.

## Inpainting (FluxFillPipeline)

```python
import torch
from diffusers import FluxFillPipeline
from diffusers.utils import load_image

pipe = FluxFillPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev", dtype=torch.bfloat16
).to("cuda")

image = load_image("https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/inpaint-input.png")
mask = load_image("https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/inpaint-mask.png")

prompt = "A majestic tiger sitting on a park bench"
image = pipe(
    prompt=prompt,
    image=image,
    mask_image=mask,
    guidance_scale=30.0,
    height=1024,
    width=1024,
    num_inference_steps=50,
    max_sequence_length=512,
).images[0]
```

## ControlNet (FluxControlPipeline)

Depth conditioning with Flux + Control LoRA:

```python
import torch
from diffusers import FluxControlPipeline
from diffusers.utils import load_image
from diffusers.pipelines.flux.pipeline_flux_controlnet import DepthPreprocessor

pipe = FluxControlPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev", dtype=torch.bfloat16
).to("cuda")

# Load a Control LoRA (e.g., depth LoRA plus hyper-SD LoRA for speed)
pipe.load_lora_weights(
    "black-forest-labs/FLUX.1-dev-ControlNet-Depth-lora",
    adapter_name="depth"
)
pipe.load_lora_weights(
    hf_hub_download("ByteDance/Hyper-SD", "Hyper-FLUX.1-dev-8steps-lora.safetensors"),
    adapter_name="hyper-sd"
)
pipe.set_adapters(["depth", "hyper-sd"], adapter_weights=[0.85, 0.125])
pipe.enable_model_cpu_offload()

control_image = load_image("https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/robot.png")
processor = DepthPreprocessor.from_pretrained("LiheYoung/depth-anything-large-hf")
control_image = processor(control_image)[0].convert("RGB")

image = pipe(
    prompt="A robot made of exotic candies",
    control_image=control_image,
    num_inference_steps=8,
    guidance_scale=10.0,
    generator=torch.Generator().manual_seed(42),
).images[0]
```

> **Important:** To unload LoRA weights, call `pipe.unload_lora_weights(reset_to_overwritten_params=True)` to fully reset the transformer.

## IP-Adapter (Image Prompting)

Prompt Flux with an image reference via IP-Adapter:

```python
import torch
from diffusers import FluxPipeline
from diffusers.utils import load_image

pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev", dtype=torch.bfloat16
).to("cuda")

image = load_image("...").resize((1024, 1024))
pipe.load_ip_adapter(
    "XLabs-AI/flux-ip-adapter",
    weight_name="ip_adapter.safetensors",
    image_encoder_pretrained_model_name_or_path="openai/clip-vit-large-patch14"
)
pipe.set_ip_adapter_scale(1.0)

image = pipe(
    prompt="wearing sunglasses",
    true_cfg_scale=4.0,
    ip_adapter_image=image,
    generator=torch.Generator().manual_seed(4444),
).images[0]
```

## Memory Optimization

Flux requires ~50GB RAM/VRAM to load all components. Use these techniques to reduce memory:

### Group Offloading (Recommended)

```python
from diffusers.hooks import apply_group_offloading

apply_group_offloading(
    pipe.transformer,
    offload_type="leaf_level",
    offload_device=torch.device("cpu"),
    onload_device=torch.device("cuda"),
    use_stream=True,
)
apply_group_offloading(
    pipe.text_encoder, offload_type="leaf_level",
    offload_device=torch.device("cpu"),
    onload_device=torch.device("cuda"), use_stream=True,
)
apply_group_offloading(
    pipe.text_encoder_2, offload_type="leaf_level",
    offload_device=torch.device("cpu"),
    onload_device=torch.device("cuda"), use_stream=True,
)
apply_group_offloading(
    pipe.vae, offload_type="leaf_level",
    offload_device=torch.device("cpu"),
    onload_device=torch.device("cuda"), use_stream=True,
)
```

Group offloading is a middle ground between `enable_model_cpu_offload()` (module-level, higher memory) and `enable_sequential_cpu_offload()` (leaf-level, lower memory, slower). It offloads groups of internal layers.

### FP16 Inference

For Turing/Volta GPUs (FP16 accelerates these):

```python
pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-schnell", dtype=torch.bfloat16
)
pipe.enable_sequential_cpu_offload()
pipe.vae.enable_slicing()
pipe.vae.enable_tiling()
pipe.to(torch.float16)  # cast after constructor to avoid CPU memory spike
```

### Quantization with BitsAndBytes

```python
from diffusers import BitsAndBytesConfig as DiffusersBitsAndBytesConfig, FluxTransformer2DModel
from transformers import BitsAndBytesConfig, T5EncoderModel

quant_config = BitsAndBytesConfig(load_in_8bit=True)
text_encoder_2_8bit = T5EncoderModel.from_pretrained(
    "black-forest-labs/FLUX.1-dev", subfolder="text_encoder_2",
    quantization_config=quant_config, torch_dtype=torch.float16,
)

quant_config = DiffusersBitsAndBytesConfig(load_in_8bit=True)
transformer_8bit = FluxTransformer2DModel.from_pretrained(
    "black-forest-labs/FLUX.1-dev", subfolder="transformer",
    quantization_config=quant_config, dtype=torch.float16,
)

pipeline = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev",
    text_encoder_2=text_encoder_2_8bit,
    transformer=transformer_8bit,
    dtype=torch.float16, device_map="balanced",
)
```

### Single File Loading + FP8 (Sub-16GB VRAM)

Requires `pip install optimum-quanto`:

```python
from diffusers import FluxTransformer2DModel, FluxPipeline
from transformers import T5EncoderModel, CLIPTextModel
from optimum.quanto import freeze, qfloat8, quantize

dtype = torch.bfloat16

# Load FP8 quantized transformer from single file
transformer = FluxTransformer2DModel.from_single_file(
    "https://huggingface.co/Kijai/flux-fp8/blob/main/flux1-dev-fp8.safetensors",
    dtype=dtype,
)
quantize(transformer, weights=qfloat8)
freeze(transformer)

# Quantize text encoder as well
text_encoder_2 = T5EncoderModel.from_pretrained(
    "black-forest-labs/FLUX.1-dev", subfolder="text_encoder_2", torch_dtype=dtype,
)
quantize(text_encoder_2, weights=qfloat8)
freeze(text_encoder_2)

pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev", transformer=None, text_encoder_2=None, dtype=dtype,
)
pipe.transformer = transformer
pipe.text_encoder_2 = text_encoder_2
pipe.enable_model_cpu_offload()

image = pipe("A cat holding a sign", guidance_scale=3.5, num_inference_steps=50).images[0]
```

## Model Variants

| Variant | ID | Steps | Guidance | Notes |
|---------|-----|-------|----------|-------|
| FLUX.1-dev | `black-forest-labs/FLUX.1-dev` | 50 | 3.5 | Standard quality, full precision |
| FLUX.1-schnell | `black-forest-labs/FLUX.1-schnell` | 4 | 0.0 | Fast distilled model |
| FLUX.1-dev (FP8) | Community (e.g., `Kijai/flux-fp8`) | 50 | 3.5 | Sub-16GB VRAM inference |

## LoRA Stacking on Flux

Flux supports loading multiple LoRAs and combining them:
- Use `pipe.load_lora_weights()` with unique `adapter_name` per LoRA
- Use `pipe.set_adapters(names, weights)` to blend
- Unload with `pipe.unload_lora_weights(reset_to_overwritten_params=True)`

## Key Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `guidance_scale` | float | 3.5 (dev) / 0.0 (schnell) | Classifier-free guidance |
| `num_inference_steps` | int | 50 (dev) / 4 (schnell) | Denoising steps |
| `max_sequence_length` | int | 512 (dev) / 256 (schnell) | Max T5 tokens |
| `height` / `width` | int | 1024 | Image dimensions (multiples of 16) |
| `true_cfg_scale` | float | None | Alternate guidance for IP-Adapter |

## References

- [HF Diffusers Flux Documentation](https://huggingface.co/docs/diffusers/en/api/pipelines/flux)
- [Diffusers v0.39.0 Release](https://github.com/huggingface/diffusers/releases)
- [Black Forest Labs](https://blackforestlabs.ai/)
