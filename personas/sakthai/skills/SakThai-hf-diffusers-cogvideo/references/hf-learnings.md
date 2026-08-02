# HF Learnings — CogVideoX in Diffusers

## 2026-07-24: hf-diffusers-cogvideo-deep-dive

### Summary
Researched the CogVideoX integration in Diffusers — a family of diffusion transformer models (2B and 5B parameters) by THUDM (Tsinghua University) for text-to-video, image-to-video, and video-to-video generation. CogVideoX uses a 3D causal VAE, an expert transformer with adaptive LayerNorm for text-video fusion, and supports multiple pipelines in Diffusers: `CogVideoXPipeline`, `CogVideoXImageToVideoPipeline`, `CogVideoXVideoToVideoPipeline`, and `CogVideoXFunControlPipeline`.

### Architecture

**3D Causal Variational Autoencoder (`AutoencoderKLCogVideoX`):**
- Compresses video along both spatial and temporal dimensions (unlike 2D VAEs that only compress spatially)
- 3D causal convolutions prevent flickering and improve temporal consistency
- Reduces sequence length significantly, lowering training compute requirements
- Temporal compression factor (`vae_scale_factor_temporal`) must be divisible into `num_frames`
- Spatial compression handled by `vae_scale_factor_spatial` (default sample_height * scale = 480p output)

**Expert Transformer with Adaptive LayerNorm (`CogVideoXTransformer3DModel`):**
- "Expert" transformer design: uses adaptive LayerNorm (adaLN) to modulate features based on text embeddings
- 3D full attention — attends across both spatial and temporal dimensions to capture motion accurately
- Text conditioning via cross-attention between T5 encoder outputs and transformer hidden states
- Available in 2B and 5B parameter configurations
- Supports fused QKV projections (`fuse_qkv_projections()`) for faster inference

**Text Encoder:**
- Frozen T5 encoder (`t5-v1_1-xxl` variant) via `T5EncoderModel`
- Tokenizer: `T5Tokenizer`
- Maximum sequence length: 226 tokens (configurable via `max_sequence_length`)
- Produces encoder hidden states that condition the diffusion transformer

**Scheduler Options:**
- `CogVideoXDDIMScheduler` — DDIM scheduler specialized for CogVideoX
- `CogVideoXDPMScheduler` — DPM solver based scheduler for higher quality

### Pipelines

**1. CogVideoXPipeline (Text-to-Video):**
- Main T2V pipeline, supports both 2B and 5B checkpoints
- Default height: 480px, width: 720px (T2V works best at 1360×768 pretrained resolution)
- Default `num_frames`: 48 (generates `num_seconds * fps + 1` frames, where num_seconds=6, fps=8 → 49 frames)
- Recommended: 81 or 161 frames, export at 16fps
- Supports `guidance_scale` (default 6.0), `use_dynamic_cfg` for adaptive guidance
- `num_inference_steps`: default 50
- Returns `CogVideoXPipelineOutput` with `.frames[0]` containing the video frames list

**2. CogVideoXImageToVideoPipeline (Image-to-Video):**
- Takes an input `image` + `prompt` to generate a video continuing from the reference frame
- Default `num_frames`: 49
- I2V works with multiple resolutions: width 768–1360, height must be 758 (divisible by 16)
- Same T5 text encoder and transformer architecture

**3. CogVideoXVideoToVideoPipeline (Video-to-Video):**
- Takes an input `video` (list of PIL frames) + `prompt`
- `strength` parameter (default 0.8) controls how much the output differs from input
- Uses DDIM inversion or similar technique to noisify input video before denoising

**4. CogVideoXFunControlPipeline (Controlled T2V):**
- Extension from CogVideoX-Fun project (Alibaba PAI)
- `control_video` parameter accepts a list of frames for spatial conditioning
- Uses `KarrasDiffusionSchedulers` (not CogVideoX-specific schedulers)
- `control_video_latents` for passing pre-encoded control signals

### Memory Optimization

| Technique | VRAM Usage (enabled) | VRAM Usage (disabled) | Notes |
|-----------|---------------------|----------------------|-------|
| `enable_model_cpu_offload()` | 19 GB | 33 GB | Standard offloading |
| `enable_sequential_cpu_offload()` | < 4 GB | ~33 GB | Very slow inference |
| `enable_tiling()` | 11 GB (with offload) | — | Only VAE decoding tiled |
| TorchAO Int8 weight-only | — | — | Quantizes transformer to int8 |
| FP8 layerwise casting | ~16 GB (5B) | ~33 GB | storage_dtype=float8_e4m3fn |
| `apply_group_offloading()` | — | — | Groups layers for efficient offload |

**Quantization Pipeline (requires ~16GB VRAM for 5B):**
```python
from diffusers.quantizers import PipelineQuantizationConfig
from diffusers import CogVideoXPipeline, AutoModel, TorchAoConfig
from torchao.quantization import Int8WeightOnlyConfig

pipeline_quant_config = PipelineQuantizationConfig(
    quant_mapping={"transformer": TorchAoConfig(Int8WeightOnlyConfig())}
)
transformer = AutoModel.from_pretrained(
    "THUDM/CogVideoX-5b", subfolder="transformer", torch_dtype=torch.bfloat16
)
transformer.enable_layerwise_casting(
    storage_dtype=torch.float8_e4m3fn, compute_dtype=torch.bfloat16
)
pipeline = CogVideoXPipeline.from_pretrained(
    "THUDM/CogVideoX-5b", transformer=transformer,
    quantization_config=pipeline_quant_config, torch_dtype=torch.bfloat16
)
```

### LoRA Support
- Supported via `load_lora_weights(adapter_name=...)` + `set_adapters(adapter_name, scale)`
- Example LoRA: `finetrainers/CogVideoX-1.5-crush-smol-v0`
- Negative prompts help reduce artifacts: "inconsistent motion, blurry motion, worse quality"

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `guidance_scale` | 6.0 | CFG scale; higher = more conditioned on prompt |
| `num_inference_steps` | 50 | Denoising steps |
| `num_frames` | 48 (T2V) / 49 (I2V) | Output frame count |
| `height` | 480 | Output height (must be divisible by VAE spatial factor) |
| `width` | 720 | Output width |
| `use_dynamic_cfg` | False | Adaptively adjust CFG during inference |
| `max_sequence_length` | 226 | T5 text encoding max length |
| `strength` (V2V) | 0.8 | How much to change from input video |
| `fps` (export) | 8 (T2V) / 16 (I2V) | Video export frame rate |

### Output Format
- Returns `CogVideoXPipelineOutput` (named tuple with `frames` attribute)
- `frames[0]` is a `list[PIL.Image]` of the generated video frames
- Export via `export_to_video(frames, "output.mp4", fps=8)`

### Model Variants Comparison

| Variant | Params | VRAM (no opt) | VRAM (offload) | VRAM (quant) | Best Use Case |
|---------|--------|---------------|----------------|--------------|--------------|
| CogVideoX-2b | 2B | ~20 GB | ~12 GB | — | Faster generation, lighter hardware |
| CogVideoX-5b | 5B | ~33 GB | ~19 GB | ~16 GB (int8+fp8) | Higher quality video |
| CogVideoX-5b-I2V | 5B | ~33 GB | ~19 GB | ~16 GB | Image-to-video tasks |

### Resources
- https://huggingface.co/docs/diffusers/main/en/api/pipelines/cogvideox
- https://arxiv.org/abs/2408.06072 (CogVideoX paper)
- https://huggingface.co/THUDM/CogVideoX-5b
- https://huggingface.co/zai-org/CogVideoX-5b-I2V
- https://huggingface.co/zai-org/CogVideoX-2b
- https://github.com/THUDM/CogVideo (original repo)
- https://huggingface.co/docs/diffusers/main/en/using-diffusers/cogvideo (usage guide)

## 2026-07-24: hf-diffusers-nunchaku-lite — Nunchaku Lite 4-bit W4A4 Diffusion Inference in Diffusers (Topic #76 Deepening)

### Summary
Deep-dive on **Nunchaku Lite** — the native integration of SVDQuant 4-bit W4A4 diffusion inference into Diffusers. See central `references/hf-learnings.md` for full content.

### Key Points for Diffusers Users
- Install `kernels` package for auto CUDA kernel download (no local compilation)
- Use `from_pretrained()` on any Nunchaku Lite checkpoint — works like any Diffusers model
- Two kernel families: `svdq_w4a4` (INT4/NVFP4 for compute-bound layers) and `awq_w4a16` (INT4 for precision-sensitive modulation layers)
- Combined with `torch.compile` → 1.8× speedup over BF16
- Peak VRAM reduction: ~50% (31.1 GB → 16.0 GB with NF4 text encoder)
- Quantize your own models with `diffuse-compressor` toolkit

### Hardware Support
| Scheme | Precision | GPUs |
|--------|-----------|------|
| `svdq_w4a4` | NVFP4 | Blackwell (RTX 50, B200) |
| `svdq_w4a4` | INT4 | Turing/Ampere/Ada (RTX 30/40, A100, L40S) |
| `awq_w4a16` | INT4 | Turing/Ampere/Ada |

### References
- Blog: https://huggingface.co/blog/nunchaku-diffusers
- Docs: https://huggingface.co/docs/diffusers/main/en/quantization/nunchaku
- PR: https://github.com/huggingface/diffusers/pull/14100
- Nunchaku: https://github.com/nunchaku-tech/nunchaku
- diffuse-compressor: https://github.com/rootonchair/diffuse-compressor
