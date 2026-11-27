# Diffusion ControlNet, Video Generation & Training Guide

(Precise Structural Control)

```python
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
from diffusers.utils import load_image
import torch

# Multiple ControlNet types
controlnet = ControlNetModel.from_pretrained("lllyasviel/sd-controlnet-canny")
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    controlnet=controlnet,
    torch_dtype=torch.float16,
).to("cuda")

# Control image (edges)
control_image = load_image("input_sketch.jpg")
image = pipe(
    "futuristic city with neon lights",
    image=control_image,
    controlnet_conditioning_scale=0.8,  # 0.0=ignore control, 1.0=strict
).images[0]

# Other ControlNet types: depth, openpose, scribble, normal, mlsd, etc.
```

## Video Generation

```python
# AnimateDiff
from diffusers import AnimateDiffPipeline, MotionAdapter, DDIMScheduler

adapter = MotionAdapter.from_pretrained("guoyww/animatediff-motion-adapter-v1-5-2")
pipe = AnimateDiffPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    motion_adapter=adapter,
)
pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
output = pipe(prompt="astronaut walking on mars", num_frames=16)
frames = output.frames[0]  # list of PIL Images

# CogVideoX (text-to-video)
from diffusers import CogVideoXPipeline
pipe = CogVideoXPipeline.from_pretrained("THUDM/CogVideoX-5b").to("cuda")
video = pipe(prompt="a cat dancing").frames[0]
```

## Training

### LoRA Fine-Tuning (Complete Pipeline)

This is the most common and memory-efficient way to fine-tune diffusion models.

#### Using the training script (recommended for production)
```bash
# Install dependencies
pip install diffusers[training] accelerate peft

# Train LoRA on custom dataset
accelerate launch examples/text_to_image/train_text_to_image_lora.py \
  --pretrained_model_name_or_path="stable-diffusion-v1-5/stable-diffusion-v1-5" \
  --dataset_name="lambdalabs/pokemon-blip-captions" \
  --caption_column="text" \
  --resolution=512 \
  --random_flip \
  --train_batch_size=4 \
  --num_train_epochs=100 \
  --checkpointing_steps=5000 \
  --learning_rate=1e-04 \
  --lr_scheduler="constant" \
  --lr_warmup_steps=0 \
  --seed=42 \
  --output_dir="sd-pokemon-lora" \
  --validation_prompt="a blue pokemon with red eyes" \
  --report_to="tensorboard"
```

#### Manual LoRA Training (Python API)
```python
import torch
from diffusers import DiffusionPipeline, UNet2DConditionModel, DDPMScheduler
from datasets import load_dataset
from torchvision import transforms
from peft import LoraConfig, get_peft_model
from accelerate import Accelerator
from tqdm.auto import tqdm

# Setup
accelerator = Accelerator()
unet = UNet2DConditionModel.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    subfolder="unet",
    torch_dtype=torch.float16,
)

# Configure LoRA — target attention projection matrices
lora_config = LoraConfig(
    r=16,                      # Rank — higher = more adaptivity, more memory
    lora_alpha=16,             # Scaling factor (higher = stronger adaptation)
    target_modules=["to_q", "to_k", "to_v", "to_out.0"],
    lora_dropout=0.1,          # Prevent overfitting on small datasets
    bias="none",
)
unet = get_peft_model(unet, lora_config)
unet.train()

# Load dataset
dataset = load_dataset("lambdalabs/pokemon-blip-captions", split="train")
train_transforms = transforms.Compose([
    transforms.Resize(512, interpolation=transforms.InterpolationMode.BILINEAR),
    transforms.CenterCrop(512),
    transforms.ToTensor(),
    transforms.Normalize([0.5], [0.5]),
])

# VAE for encoding images to latents
vae = AutoencoderKL.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    subfolder="vae",
    torch_dtype=torch.float16,
)

# Training loop
optimizer = torch.optim.AdamW(unet.parameters(), lr=1e-4)
noise_scheduler = DDPMScheduler.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    subfolder="scheduler",
)

unet, optimizer, train_dataloader = accelerator.prepare(
    unet, optimizer, DataLoader(dataset, batch_size=4, shuffle=True)
)

for epoch in range(10):
    for batch in tqdm(train_dataloader):
        with torch.no_grad():
            latents = vae.encode(batch["pixel_values"].to(torch.float16)).latent_dist.sample()
            latents = latents * vae.config.scaling_factor
        
        noise = torch.randn_like(latents)
        timesteps = torch.randint(0, noise_scheduler.config.num_train_timesteps, (latents.shape[0],))
        noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)
        
        noise_pred = unet(noisy_latents, timesteps, batch["input_ids"]).sample
        loss = torch.nn.functional.mse_loss(noise_pred, noise)
        
        accelerator.backward(loss)
        optimizer.step()
        optimizer.zero_grad()

# Save LoRA weights
unet.save_pretrained("./my-lora-adapter")

# Inference with trained LoRA
from peft import PeftModel
base_unet = UNet2DConditionModel.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5", subfolder="unet"
)
unet_lora = PeftModel.from_pretrained(base_unet, "./my-lora-adapter")
pipe = DiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    unet=unet_lora,
    torch_dtype=torch.float16,
).to("cuda")
image = pipe("a blue pokemon with red eyes").images[0]
```

#### Dataset Preparation for LoRA
```
my-dataset/
├── images/
│   ├── img_001.png
│   ├── img_002.png
│   └── ...
└── metadata.jsonl  # {"file_name": "img_001.png", "text": "caption for image"}
```

### DreamBooth (Subject Personalization)
```bash
accelerate launch examples/dreambooth/train_dreambooth.py \
  --pretrained_model_name_or_path="stable-diffusion-v1-5/stable-diffusion-v1-5" \
  --instance_data_dir="./my-subject" \
  --instance_prompt="a photo of sks subject" \
  --class_prompt="a photo of a person" \
  --with_prior_preservation \
  --prior_loss_weight=1.0 \
  --num_class_images=200 \
  --output_dir="./dreambooth-output"
```

### Textual Inversion (Learn New Tokens)
```bash
accelerate launch examples/textual_inversion/textual_inversion.py \
  --pretrained_model_name_or_path="stable-diffusion-v1-5/stable-diffusion-v1-5" \
  --train_data_dir="./my-subject" \
  --placeholder_token="<my-token>" \
  --initializer_token="object"
```

### Full Training (DDPM from scratch)
```bash
pip install diffusers[training]
accelerate launch examples/unconditional_image_generation/train_unconditional.py \
  --dataset_name="huggan/flowers-102-categories" \
  --output_dir="./ddpm-flowers" \
  --resolution=64 \
  --train_batch_size=16
```

## Optimization & Memory Saving

Memory-constrained (no GPU or <8GB VRAM):
```python
# CPU offloading
pipe.enable_model_cpu_offload()

# Sequential offload (extremely memory-efficient)
pipe.enable_sequential_cpu_offload()

# Attention slicing (reduces peak memory)
pipe.enable_attention_slicing()

# VAE tiling (for high-res images)
pipe.enable_vae_tiling()
```

Performance (GPU):
```python
# torch.compile (30-50% speedup)
pipe.unet = torch.compile(pipe.unet, mode="reduce-overhead", fullgraph=True)

# xformers (memory-efficient attention)
pipe.enable_xformers_memory_efficient_attention()

# Use fp16
pipe.to(torch.float16)
```

### Memory Optimization Ladder (5 Tiers)

| Tier | VRAM Required | Configuration |
|------|--------------|---------------|
| 1 (Max quality) | 24GB+ | Full fp16, no offloading, SDXL/FLUX |
| 2 (High) | 16GB | fp16, sliced attention, SDXL |
| 3 (Medium) | 12GB | fp16, CPU offload, SD 1.5 |
| 4 (Low) | 8GB | fp16, sequential offload, SD 1.5 |
| 5 (Minimal) | 4-6GB | fp16, sequential + vae tiling + attention slicing |

## The HF Diffusion Models Course

Free course at https://huggingface.co/learn/diffusion-course by Jonathan Whitaker and Lewis Tunstall.

### Unit 1: Introduction to Diffusion Models
- Theory: forward/reverse diffusion process, Markov chains
- Implementing DDPM from scratch
- Training a simple diffusion model on MNIST
- Hands-on with diffusers: `DDPMPipeline`, `UNet2DModel`

### Unit 2: Fine-tuning & Guidance
- Loading pretrained models
- Classifier-free guidance (CFG scale)
- Fine-tuning on custom datasets
- Sampling speed vs quality tradeoffs

### Unit 3: Stable Diffusion
- Latent diffusion architecture (VAE + UNet + text encoder)
- Text conditioning (CLIP text encoder)
- CFG with textual prompts
- Image-to-image and inpainting
- Advanced: cross-attention control, prompt weighting

### Unit 4: Advanced Techniques
- DDIM inversion for real image editing
- Custom pipeline creation
- Diffusion for audio generation
- Model deployment on Spaces
- Contributions to the diffusers library

## Key New Features in v0.39+

| Feature | Description |
|---------|-------------|
| **Flow Matching** | Rectified flow models (SD3, FLUX) via `FlowMatchEulerDiscreteScheduler` |
| **CogVideoX** | 3D full-attention transformer for text-to-video |
| **Mochi-1** | Open-source text-to-video from Genmo |
| **PixArt-α / PixArt-Σ** | Efficient transformer-based T2I |
| **Playground v2.5** | High-aesthetic-quality text-to-image |
| **HunyuanDiT** | Multi-resolution Chinese/English DiT |
| **Stable Audio / AudioLDM 2** | Text-to-audio generation |
| **Kandinsky 3** | Simplified two-stage architecture |

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| `CUDA out of memory` | Model too large for VRAM | Enable model CPU offload, reduce batch size, use SD 1.5 instead of SDXL |
| `Nan in loss` | Learning rate too high | Reduce LR to 1e-5, add gradient clipping |
| `Garbage images` | Wrong scheduler or dtype | Use appropriate scheduler; ensure fp16 is loaded correctly |
| `Loading gated model fails` | Not authenticated | `huggingface-cli login` and accept terms on model page |
| `Pipeline too slow` | No optimization | Enable xformers, torch.compile, use DPM++ scheduler (fewer steps) |
| `Inpainting artifacts` | Mask boundary issues | Dilate mask, use higher strength |

## Pitfalls

- **Memory:** Large models (FLUX, SD3) need 12-24GB VRAM. Use `enable_model_cpu_offload()` on consumer GPUs.
- **Scheduler selection:** Different schedulers mean different quality/speed tradeoffs — try DPM++ or FlowMatchEuler for best quality.
- **Licenses:** Check model cards! Stable Diffusion is CreativeML Open RAIL, FLUX.1-dev is Apache 2.0, SD3 has a custom research license.
- **LoRA training:** Needs well-captioned images — bad captions = bad results.
- **Loading gated models:** Requires `huggingface-cli login` and accepting terms on the model page.
- **DDIM inversion** is lossy; expect minor quality degradation on reconstruction.
- **Video generation** is computationally expensive — use sequential offload and gradient checkpointing.
- **Outdated model IDs:** `runwayml/stable-diffusion-v1-5` is deprecated. Use `stable-diffusion-v1-5/stable-diffusion-v1-5`.
- **Batched generation** can OOM — reduce batch size or enable attention slicing.
- **LoRA rank choice:** r=4 for strong style adaptation, r=16-64 for new concepts, r=128+ for complex subjects (needs more data).

## References

- [Diffusers Documentation](https://huggingface.co/docs/diffusers)
- [Diffusion Course](https://huggingface.co/learn/diffusion-course)
- [Diffusers GitHub](https://github.com/huggingface/diffusers)
- [Models on Hub with diffusers](https://huggingface.co/models?library=diffusers)
- [Architecture Philosophy](https://huggingface.co/docs/diffusers/conceptual/philosophy)
- [Contribution Guide with AI Agents](https://huggingface.co/docs/diffusers/main/en/conceptual/contribution#coding-with-ai-agents)

## Linked Files

- `references/pipeline-reference.md` — condensed lookup table: 15+ pipeline → model-ID mappings, 8 scheduler comparisons, memory optimization ladder (5 tiers), course unit syllabus
