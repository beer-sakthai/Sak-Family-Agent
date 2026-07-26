# Wan Video Generation — Diffusers Integration Deep-Dive

## 2026-07-25: hf-diffusers-wan-video-generation

### Summary
Deep dive into the **Wan2.1/Wan2.2** open video foundation model family by the Wan Team (Alibaba), and its complete integration into Hugging Face Diffusers. Wan is a suite of diffusion transformer (DiT) models for video generation that consistently outperforms both open-source and commercial alternatives across benchmarks, while offering a consumer-grade 1.3B variant that runs on nearly any GPU (8.19 GB VRAM).

### Model Family Overview

| Variant | Parameters | Task | Resolution | VRAM |
|---------|-----------|------|-----------|------|
| Wan2.1 T2V 1.3B | 1.3B | Text-to-Video | 480P | ~8.19 GB |
| Wan2.1 T2V 14B | 14B | Text-to-Video | 480P/720P | ~61 GB |
| Wan2.1 I2V 14B 480P | 14B | Image-to-Video | 480P | ~61 GB |
| Wan2.1 I2V 14B 720P | 14B | Image-to-Video | 720P | ~78 GB |
| Wan2.1 FLF2V 14B 720P | 14B | First+Last-Frame-to-Video | 720P | ~78 GB |
| Wan2.1 VACE 1.3B | 1.3B | Any-to-Video (control) | 480P | ~9 GB |
| Wan2.1 VACE 14B | 14B | Any-to-Video (control) | 480P/720P | ~62 GB |
| Wan2.2 T2V 14B | 14B | Text-to-Video (v2) | 720P | ~62 GB |
| Wan2.2 I2V 14B | 14B | Image-to-Video (v2) | 720P | ~62 GB |
| Wan2.2 TI2V 5B | 5B | Text+Image-to-Video | 480P | ~21 GB |
| Wan2.2 Animate 14B | 14B | Character Animation/Replacement | 480P/720P | ~62 GB |

### Supported Diffusers Pipelines

Five pipeline classes live under `diffusers/pipelines/wan/`:

1. **`WanPipeline`** — Text-to-Video. Core pipeline, uses UMT5 text encoder + WanTransformer3D + AutoencoderKLWan
2. **`WanImageToVideoPipeline`** — Image-to-Video. Adds CLIPVisionModel image encoder for conditioning
3. **`WanAnimatePipeline`** — Character animation and replacement. Takes character image + pose/face video inputs. Two modes: `animate` (animate a character) and `replace` (replace character in background video)
4. **`WanVACEPipeline`** — Versatile Any-to-Video Controllable generation. Supports: Control to Video (depth, pose, sketch, flow, scribble, layout, bbox), Image/Video to Video, Inpainting/Outpainting, Subject to Video, Composition to Video
5. **`WanVideoToVideoPipeline`** — Video-to-Video translation

### Architecture

**WanTransformer3DModel** — 3D Diffusion Transformer with:
- Causal attention with rotary position embeddings (RoPE)
- Fused QKV projections (single linear for self-attention, separate Q/fused KV for cross-attention)
- Dual-stage denoising support: `transformer` (high-noise) + `transformer_2` (low-noise), split at `boundary_ratio`
- Patch embedding for video tokens (spatial×temporal)
- Configurable attention backend via `dispatch_attention_fn`
- NormQ + NormK for improved training stability
- Added KV projections for image conditioning (I2V tasks)
- Supports FP32 layer norm for precision

**AutoencoderKLWan** — Custom 3D VAE:
- `AvgDown3D` / `AvgUp3D` — average pooling-based down/upsampling in both spatial and temporal dimensions
- Temporal downsampling factor: 4 (via `CACHE_T = 2` and factor_t stacking)
- Spatial downsampling factor: 8
- Total compression: 32× in each spatial dim, 4× in temporal dim
- Configurable via `vae_scale_factor_spatial` and `vae_scale_factor_temporal`
- Available in fp32 (recommended for decoding) or bf16
- Single-file loading support via `from_single_file()`

**Text Encoder**: UMT5EncoderModel (google/umt5-xxl) — multilingual T5 variant supporting English and Chinese. Context length 512 tokens.

**Image Encoder** (I2V only): CLIPVisionModel for encoding the conditioning image.

### Scheduler

- Default: `FlowMatchEulerDiscreteScheduler` (flow-matching based)
- Alternative: `UniPCMultistepScheduler` with `flow_shift` parameter
- `flow_shift`: 5.0 for 720P, 3.0 for 480P (controls noise schedule sharpness)
- Can swap schedulers after pipeline creation with `pipe.scheduler = ...`

### Key Parameters (WanPipeline.__call__)

- `prompt` / `negative_prompt` — Text conditioning
- `height` / `width` — Output resolution (default: 480×832 for T2V 1.3B)
- `num_frames` — Number of frames (default: 81, formula: 4k+1)
- `num_inference_steps` — Denoising steps (default: 50)
- `guidance_scale` — CFG scale (default: 5.0)
- `guidance_scale_2` — Second-stage CFG scale (for dual-transformer setups)
- `max_sequence_length` — Text token truncation (default: 512)
- `generator` — Deterministic generation seed
- `latents` — Pre-initialized noise tensor
- `output_type` — `"np"` (numpy array) or `"pil"` (PIL images)
- `attention_kwargs` — Custom attention processor kwargs

### Memory Optimization

- **1.3B model runs on any GPU with ≥8GB VRAM** — key differentiator from 14B variants
- Group offloading support (`apply_group_offloading`) — offload transformer blocks to CPU
- Pipeline quantization config (`PipelineQuantizationConfig`)
- fp32 VAE recommended for better decoding quality (trade VRAM for quality)
- `vae_scale_factor_spatial` + `patch_size` used for dimension alignment
- LightX2V LoRAs available for inference speedup (Wan 2.2)

### LoRA Support

- `WanLoraLoaderMixin` integrated into all pipelines
- `load_lora_weights(adapter_name=...)` from Hub
- `set_adapters(...)` to activate
- Standard LoRA pattern: prompt trigger + adapter
- Wan 2.2 two-stage: LoRAs load into first denoiser by default; set `load_into_transformer_2=True` for second denoiser

### Visual Text Generation

Unique capability: **first video model to generate both Chinese and English text** in generated videos. Robust text rendering enhances practical applications (advertising, subtitles, signage).

### Wan VACE (Any-to-Video Control)

Most versatile pipeline supporting:
- **Depth/Pose/Sketch/Flow/Grayscale/Scribble/Layout/BBox** → Video (control signals)
- **First frame + last frame** → Video (interpolation)
- **Inpainting/Outpainting** (mask-based)
- **Subject to Video** (face/object/character reference)
- **Composition to Video** (animate/swap/expand/move anything)

Input convention: black mask = preserve conditioning content, white mask = generate new content.

### Wan Animate

Unified character animation with two modes:
- **`animate`** (default) — Animate a character image using pose+face reference video
- **`replace`** — Replace a character in background video while preserving scene
- Requires preprocessed inputs (pose video + face video from reference)
- Optional Relighting LoRA for environmental lighting integration
- CFG disabled by default (`guidance_scale=1.0`) but can be enabled
- `segment_frame_length=77`, `prev_segment_conditioning_frames=1` or `5` (5=better consistency, more VRAM)

### Key Resources
- Model repos: https://huggingface.co/Wan-AI
- Diffusers docs: https://huggingface.co/docs/diffusers/main/en/api/pipelines/wan
- GitHub: https://github.com/Wan-Video/Wan2.1
- License: Apache 2.0
- Supported HW: NVIDIA CUDA, consumer to enterprise GPUs

### Skill Created
`hf-diffusers-wan-video-generation/` — complete reference with SKILL.md + this learning document.
