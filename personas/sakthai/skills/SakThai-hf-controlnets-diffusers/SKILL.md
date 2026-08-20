---
name: SakThai-hf-controlnets-diffusers
description: >-
  Complete reference on ControlNets in Hugging Face Diffusers — architecture,
  model classes, inference pipelines (text-to-image, image-to-image, inpainting,
  multi-control, guess mode), training, Control-LoRA, and all backbone variants
  (SD1.5, SDXL, FLUX, SD3, Hunyuan-DiT, Sana).
category: mlops
tags: [diffusers, controlnet, image-generation, adapters, conditional-control]
author: SakThai
created: 2026-07-26
version: 1.0.0
---

# ControlNets in Hugging Face Diffusers — Complete Reference

## Overview

ControlNet (Zhang et al., 2023) is a neural network architecture that adds
**spatial conditioning controls** to pretrained text-to-image diffusion models.
It works by:

1. **Freezing** the original model parameters (no retraining).
2. Adding a smaller network of **zero convolution** layers that progressively
   grow parameters from zero, ensuring no harmful noise affects fine-tuning.
3. Conditioning on extra visual information — **structural controls** such as
   canny edges, depth maps, human pose, segmentation maps, and more.

The ControlNet output is injected into the frozen UNet's down- and mid-block
activations (or the DiT backbone for transformer-based models), steering the
generation without modifying the base model's weights.

---

## Model Classes (Diffusers v0.39.0)

| Class | Backbone | Notes |
|-------|----------|-------|
| `ControlNetModel` | SD1.5, SD2, SDXL | The original; supports `from_single_file()` and `from_unet()` |
| `FluxControlNetModel` | FLUX.1-dev, FLUX.1-schnell | Rectified flow transformer backbone |
| `SD3ControlNetModel` | Stable Diffusion 3 (MMDiT) | Multimodal DiT backbone |
| `HunyuanDiT2DControlNetModel` | Hunyuan-DiT | Chinese-native DiT |
| `SanaControlNetModel` | Sana (efficient) | Lightweight, fast |
| `SparseControlNetModel` | Various | Memory-efficient sparse variant |
| `ControlNetUnionModel` | Multi-control | Unified multi-condition in one model |

### ControlNetModel

```python
from diffusers import ControlNetModel

# Standard loading from Hub
controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/control_v11p_sd15_canny",
    torch_dtype=torch.float16
)

# Loading from original .pth format
controlnet = ControlNetModel.from_single_file(
    "https://huggingface.co/lllyasviel/ControlNet-v1-1/blob/main/control_v11p_sd15_canny.pth"
)

# Initialise from a UNet (for training new controls)
from diffusers import UNet2DConditionModel
unet = UNet2DConditionModel.from_pretrained("runwayml/stable-diffusion-v1-5", subfolder="unet")
controlnet = ControlNetModel.from_unet(unet)
```

### FluxControlNetModel

```python
from diffusers import FluxControlNetModel

controlnet = FluxControlNetModel.from_pretrained(
    "InstantX/FLUX.1-dev-Controlnet-Canny",
    torch_dtype=torch.bfloat16
)
```

---

## ControlNet Inference

### Preprocessing the Conditioning Image

Different structural controls require different preprocessing. The most common
is Canny edge detection with OpenCV:

```python
import cv2
import numpy as np
from PIL import Image
from diffusers.utils import load_image

original_image = load_image("https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/non-enhanced-prompt.png")
image = np.array(original_image)

low_threshold = 100
high_threshold = 200
image = cv2.Canny(image, low_threshold, high_threshold)
image = image[:, :, None]
image = np.concatenate([image, image, image], axis=2)
canny_image = Image.fromarray(image)
```

Other common preprocessors (from `controlnet_aux` package):
- **Depth**: `MidasDetector` or `ZoeDetector`
- **Pose**: `OpenposeDetector`
- **MLSD** (straight lines): `MLSDdetector`
- **Segmentation**: `SuperAnnotate` or `OneFormerDetector`
- **HED** (soft edge): `HEDdetector`
- **Normal BAE**: `NormalBaeDetector`
- **Lineart**: `LineartDetector`
- **Content Shuffle**: `ContentShuffleDetector`
- **Soft Edge**: `SoftEdgeDetector`

### Text-to-Image (SDXL)

```python
import torch
from diffusers import StableDiffusionXLControlNetPipeline, ControlNetModel, AutoencoderKL

controlnet = ControlNetModel.from_pretrained(
    "diffusers/controlnet-canny-sdxl-1.0", torch_dtype=torch.float16
)
vae = AutoencoderKL.from_pretrained("madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16)
pipeline = StableDiffusionXLControlNetPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    controlnet=controlnet, vae=vae, torch_dtype=torch.float16
).to("cuda")

prompt = "aerial view, a majestic castle on a cliff, sunset, highly detailed"
image = pipeline(
    prompt,
    image=canny_image,
    controlnet_conditioning_scale=0.8,
    num_inference_steps=50,
).images[0]
```

### Text-to-Image (FLUX)

```python
from diffusers import FluxControlNetPipeline, FluxControlNetModel

controlnet = FluxControlNetModel.from_pretrained(
    "InstantX/FLUX.1-dev-Controlnet-Canny", torch_dtype=torch.bfloat16
)
pipeline = FluxControlNetPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev", controlnet=controlnet, torch_dtype=torch.bfloat16
).to("cuda")

image = pipeline(
    "A cat reclining in a flamingo pool floatie holding a margarita",
    control_image=canny_image,
    controlnet_conditioning_scale=0.5,
    num_inference_steps=50,
    guidance_scale=3.5,
).images[0]
```

### Image-to-Image

Use `StableDiffusionControlNetImg2ImgPipeline` for image-to-image with
ControlNet. It accepts both the conditioning image and an initial image.

```python
from diffusers import StableDiffusionControlNetImg2ImgPipeline

pipeline = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5", controlnet=controlnet, torch_dtype=torch.float16
).to("cuda")

image = pipeline(
    prompt,
    image=init_image,       # initial image for img2img
    control_image=canny_image,
    strength=0.7,           # denoising strength
).images[0]
```

### Inpainting

Use `StableDiffusionControlNetInpaintPipeline` for inpainting with ControlNet
control. Requires the input image, mask, and conditioning image.

```python
from diffusers import StableDiffusionControlNetInpaintPipeline

pipeline = StableDiffusionControlNetInpaintPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5", controlnet=controlnet, torch_dtype=torch.float16
).to("cuda")

image = pipeline(
    prompt,
    image=input_image,
    mask_image=mask_image,
    control_image=conditioning_image,
).images[0]
```

### Multi-ControlNet

Compose multiple conditionings (e.g., canny + depth) by passing a **list of
ControlNet models** and a **list of conditioning images**:

```python
controlnets = [
    ControlNetModel.from_pretrained("diffusers/controlnet-depth-sdxl-1.0-small", torch_dtype=torch.float16),
    ControlNetModel.from_pretrained("diffusers/controlnet-canny-sdxl-1.0", torch_dtype=torch.float16),
]

pipeline = StableDiffusionXLControlNetPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    controlnet=controlnets, vae=vae, torch_dtype=torch.float16
).to("cuda")

images = [canny_image.resize((1024, 1024)), depth_image.resize((1024, 1024))]

image = pipeline(
    prompt,
    image=images,
    controlnet_conditioning_scale=[0.5, 0.5],  # per-controlnet scale
    num_inference_steps=100,
).images[0]
```

For best results:
- **Mask** conditionings so they don't overlap spatially.
- **Experiment** with different `controlnet_conditioning_scale` values per net.

### Guess Mode

Guess mode generates from **only the control input** without a text prompt
(pass `""` as prompt). The ControlNet tries to "guess" the content from the
structural input alone. A `guidance_scale` of 3.0–5.0 is recommended.

```python
image = pipeline(
    "",
    image=canny_image,
    guess_mode=True,
    guidance_scale=4.0,
).images[0]
```

Internally, guess mode adjusts the scale of ControlNet's output residuals by a
fixed ratio depending on block depth: earlier DownBlocks get scaled by 0.1,
the MidBlock by 1.0.

### Key Inference Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `control_image` / `image` | `list[PIL.Image]` or `PIL.Image` | — | The conditioning image(s). For multi-control, pass a list. |
| `controlnet_conditioning_scale` | `float` or `list[float]` | `1.0` | Weight of the control signal. Lower = weaker control. For multi-control, pass a list of per-net scales. |
| `guess_mode` | `bool` | `False` | Generate from control input only (no prompt). |
| `strength` | `float` | — | Denoising strength for img2img/inpainting (0.0–1.0). Lower = closer to init image. |
| `num_inference_steps` | `int` | `50` | Denoising steps. |

---

## ControlNet Training

### Scripts

The official training scripts live in the Diffusers repo:

```
examples/controlnet/train_controlnet.py        # SD1.5/SD2
examples/controlnet/train_controlnet_sdxl.py   # SDXL
```

### Setup

```bash
git clone https://github.com/huggingface/diffusers
cd diffusers
pip install .
cd examples/controlnet
pip install -r requirements.txt

# Configure Accelerate
accelerate config default
```

### Key Training Parameters

| Parameter | Description |
|-----------|-------------|
| `--pretrained_model_name_or_path` | Base model ID or path |
| `--controlnet_model_name_or_path` | Existing ControlNet to continue training (optional) |
| `--dataset_name` | HF dataset for training (e.g., `fusing/fill50k`) |
| `--resolution` | Input resolution (e.g., `512`) |
| `--learning_rate` | Learning rate (e.g., `1e-5`) |
| `--train_batch_size` | Per-GPU batch size |
| `--gradient_accumulation_steps` | Accumulation steps |
| `--mixed_precision` | `"fp16"` or `"bf16"` |
| `--use_8bit_adam` | Enable 8-bit Adam (bitsandbytes) for ~38GB → 16GB |
| `--gradient_checkpointing` | Enable gradient checkpointing |
| `--snr_gamma` | Min-SNR weighting (recommended: `5.0`) |
| `--validation_image` | Path(s) to validation conditioning images |
| `--validation_prompt` | Prompt(s) for validation |
| `--push_to_hub` | Upload trained model to HF Hub |

### Training Command Example (16GB GPU)

```bash
export MODEL_DIR="stable-diffusion-v1-5/stable-diffusion-v1-5"
export OUTPUT_DIR="path/to/save/model"

accelerate launch train_controlnet.py \
  --pretrained_model_name_or_path=$MODEL_DIR \
  --output_dir=$OUTPUT_DIR \
  --dataset_name=fusing/fill50k \
  --resolution=512 \
  --learning_rate=1e-5 \
  --validation_image "./cond_img_1.png" "./cond_img_2.png" \
  --validation_prompt "red circle with blue background" "cyan circle with brown floral background" \
  --train_batch_size=1 \
  --gradient_accumulation_steps=4 \
  --gradient_checkpointing \
  --use_8bit_adam \
  --mixed_precision="fp16" \
  --snr_gamma=5.0 \
  --push_to_hub
```

### VRAM Requirements

| GPU | Optimisations Needed |
|-----|---------------------|
| 8GB | gradient_checkpointing + use_8bit_adam + mixed_precision + train_batch_size=1 |
| 12GB | gradient_checkpointing + use_8bit_adam |
| 16GB | gradient_checkpointing + use_8bit_adam (default script needs ~38GB without) |
| 24GB+ | Default settings |
| Multi-GPU | Add `--multi_gpu` to accelerate launch |

### Training — SDXL

For SDXL, use `train_controlnet_sdxl.py`:
```bash
accelerate launch train_controlnet_sdxl.py \
  --pretrained_model_name_or_path="stabilityai/stable-diffusion-xl-base-1.0" \
  --output_dir="./controlnet-sdxl" \
  --dataset_name=fusing/fill50k \
  --resolution=1024 \
  --learning_rate=1e-5 \
  --train_batch_size=1 \
  --gradient_accumulation_steps=4 \
  --gradient_checkpointing \
  --mixed_precision="fp16"
```

### Training Script Internals

The script core flow:

1. **Dataset preprocessing** (`make_train_dataset`):
   - Conditioning image transforms: `Resize → CenterCrop → ToTensor`
   - Standard image transforms + caption tokenization

2. **Model initialisation**:
   ```python
   if args.controlnet_model_name_or_path:
       controlnet = ControlNetModel.from_pretrained(args.controlnet_model_name_or_path)
   else:
       controlnet = ControlNetModel.from_unet(unet)
   ```

3. **Parameter freezing**: Only ControlNet parameters are optimised:
   ```python
   params_to_optimize = controlnet.parameters()
   optimizer = optimizer_class(params_to_optimize, lr=args.learning_rate, ...)
   ```

4. **Training loop**: The conditioning image and text embeddings are passed to
   the ControlNet's down- and mid-blocks:
   ```python
   encoder_hidden_states = text_encoder(batch["input_ids"])[0]
   controlnet_image = batch["conditioning_pixel_values"].to(dtype=weight_dtype)

   down_block_res_samples, mid_block_res_sample = controlnet(
       noisy_latents,
       timesteps,
       encoder_hidden_states=encoder_hidden_states,
       controlnet_cond=controlnet_image,
       return_dict=False,
   )
   ```

### Min-SNR Weighting

The Min-SNR weighting strategy rebalances the loss for faster convergence.
Compatible with both epsilon prediction and v-prediction. Enable with:

```bash
--snr_gamma=5.0
```

PyTorch only.

---

## Control-LoRA

Control-LoRA (Stability AI) combines ControlNet with **low-rank parameter
efficient fine-tuning**, producing much smaller file sizes suitable for
consumer GPUs.

```python
from diffusers import ControlNetModel, UNet2DConditionModel

# Load ControlNet from UNet, then attach LoRA adapter
unet = UNet2DConditionModel.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    subfolder="unet",
    torch_dtype=torch.bfloat16
).to("cuda")

controlnet = ControlNetModel.from_unet(unet).to(device="cuda", dtype=torch.bfloat16)
controlnet.load_lora_adapter(
    "stabilityai/control-lora",
    weight_name="control-LoRAs-rank128/control-lora-canny-rank128.safetensors",
    prefix=None,
    controlnet_config=controlnet.config,
)
```

Then use the ControlNet as normal in a pipeline.

---

## Popular ControlNet Models on the Hub

| Model ID | Backbone | Control Type |
|----------|----------|-------------|
| `lllyasviel/control_v11p_sd15_canny` | SD1.5 | Canny edge |
| `lllyasviel/control_v11p_sd15_depth` | SD1.5 | Depth map |
| `lllyasviel/control_v11p_sd15_openpose` | SD1.5 | Human pose |
| `lllyasviel/control_v11p_sd15_mlsd` | SD1.5 | Straight lines |
| `lllyasviel/control_v11p_sd15_seg` | SD1.5 | Segmentation |
| `lllyasviel/control_v11p_sd15_scribble` | SD1.5 | Scribbles |
| `lllyasviel/control_v11p_sd15_normalbae` | SD1.5 | Normal map |
| `lllyasviel/control_v11p_sd15_lineart` | SD1.5 | Line art |
| `lllyasviel/control_v11p_sd15_softedge` | SD1.5 | Soft edge |
| `lllyasviel/control_v11p_sd15_shuffle` | SD1.5 | Content shuffle |
| `lllyasviel/control_v11p_sd15_ip2p` | SD1.5 | Instruction-to-pixel |
| `diffusers/controlnet-depth-sdxl-1.0-small` | SDXL | Depth (lightweight) |
| `diffusers/controlnet-canny-sdxl-1.0` | SDXL | Canny edge |
| `InstantX/FLUX.1-dev-Controlnet-Canny` | FLUX.1 | Canny edge |
| `InstantX/FLUX.1-dev-Controlnet-Depth` | FLUX.1 | Depth |
| `stabilityai/control-lora` | SDXL | Canny (LoRA, rank-128) |

---

## Advanced Topics

### Attention Slicing

For memory-constrained inference:

```python
pipeline.enable_attention_slicing()       # "auto" — halves attention heads
pipeline.enable_attention_slicing("max")  # maximum savings
```

Or on the ControlNet model directly:

```python
controlnet.set_attention_slice("auto")
```

### Model CPU Offloading

```python
pipeline.enable_model_cpu_offload()  # moves models to CPU when not in use
pipeline.enable_sequential_cpu_offload()
```

### Controlling Channel Order

If your conditioning image is in BGR format (e.g., from OpenCV):

```python
# ControlNet will convert BGR → RGB internally
controlnet = ControlNetModel.from_pretrained(
    "diffusers/controlnet-canny-sdxl-1.0",
    controlnet_conditioning_channel_order="bgr"
)
```

---

## Common Pitfalls

1. **Resolution mismatch**: The conditioning image should match the pipeline's
   expected input resolution (e.g., 512×512 for SD1.5, 1024×1024 for SDXL).
   Use `.resize()` with `PIL.Image.Resampling.LANCZOS`.

2. **Dtype consistency**: Ensure `torch_dtype` matches between ControlNet and
   pipeline. SDXL/LDM pipelines typically use `float16`; FLUX uses `bfloat16`.

3. **ControlNet-UNet compatibility**: A ControlNet trained for SD1.5 cannot
   be used with SDXL or FLUX. Always match the backbone architecture.

4. **Multi-ControlNet image dimensions**: When using multiple controls, the
   `controlnet_conditioning_scale` list must have the same length as the
   number of controlnets. Each conditioning image must share the same
   spatial dimensions.

5. **Guess mode + prompt**: In guess mode, the prompt is ignored. Pass an
   empty string `""` to make this explicit.

6. **CPU-only inference**: ControlNet models are large. Loading on CPU without
   `torch_dtype` reduction will exceed most system RAM. Always use
   `torch.float16` or `torch.bfloat16`.

---

## Reference

- Paper: [Adding Conditional Control to Text-to-Image Diffusion Models](https://arxiv.org/abs/2302.05543)
- Diffusers docs: https://huggingface.co/docs/diffusers/en/using-diffusers/controlnet
- API reference: https://huggingface.co/docs/diffusers/v0.39.0/en/api/models/controlnet
- Training guide: https://huggingface.co/docs/diffusers/en/training/controlnet
- Control-LoRA: https://huggingface.co/stabilityai/control-lora
