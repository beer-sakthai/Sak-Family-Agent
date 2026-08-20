---
name: SakThai-hf-abot-world
author: SakThai
license: MIT
description: "Complete reference on ABot-World (AMap CVLab) — action-conditioned interactive world model built on Wan2.2-TI2V-5B. Causal student distillation + LongForcing, local attention, lightweight VAE decoder, low-bit DiT inference, and the ZeroGPU streaming Space recipe (per-visitor quota billing, steady-cadence pacing)."
version: 1.0.0
category: mlops
tags: [huggingface, world-model, video, interactive, zerogpu, space, abot-world]
platforms: [linux]
---

# ABot-World — Interactive World Rollout (AMap CVLab)

Paper: **ABot-World-0: Infinite Interactive World Rollout on a Single Desktop GPU** (arXiv:2607.19191, cs.CV/AI/LG).
Space: `acvlab/abot-world-interactive` · Model: `acvlab/ABot-World-0-5B-LF` · Code: github.com/amap-cvlab/ABot-World · Project: amap-cvlab.github.io/ABot-World.

**What it is:** upload ONE starting image, drive the world live with WASD (move/turn) + IJKL (look/pan). The model autoregressively rolls out an action-conditioned world, streaming decoded frames at 720P / up to 16 FPS on a single RTX 5090 (1.2 s action-to-first-frame latency, ~19 GiB peak VRAM). Not passive video playback — closed-loop interactive generation.

## Model facts (acvlab/ABot-World-0-5B-LF)

| Field | Value |
|---|---|
| base | Wan-AI/Wan2.2-TI2V-5B fine-tune |
| config | WanModel, dim 3072, ffn_dim 14336, heads 24, layers 30, in/out 48, freq_dim 256, text_len 512, `downscale_factor_control_adapter: 16` |
| params | 5.27B BF16 (diffusion_pytorch_model.safetensors 10.5 GB) |
| text enc | google/umt5-xxl encoder BF16 (11.4 GB pth) |
| VAE | Wan2.2_VAE.pth 2.8 GB + **taew2_2.pth 22.9 MB** lightweight decoder (taehv lineage) |
| license | Apache-2.0, en/zh; repo ~24.7 GB |

## Training pipeline

1. **Data**: AAA games + simulation engines + internet videos; `WorldExplorer` agent-driven collection; 14 deterministic quality checks + VLM assessment + synchronized action/text annotation. 500-hour dataset announced, not yet released.
2. **Distill**: bidirectional action-conditioned TEACHER → causal STUDENT via teacher forcing + ODE distillation (DMD; denoising_step_list [1000,750,500,250], warp_denoising_step, context_noise 0).
3. **LongForcing** (the "LF"): align long student self-rollouts with extended-horizon teacher → fights distribution shift / autoregressive drift.
4. **Control**: 8-key one-hot (W A S D I J K L); reference-character memory (`ref_num_slots 5`, `ref_resolution 512`) for 3rd-person identity consistency.
5. **Eval**: WorldRoamBench + extended rollouts.

## Inference stack (what makes it real-time)

- **Causal block-wise**: `CausalInferencePipeline` — set_prompts → set_first_frame_latent → per block: set_act(keys) → generate_next_block → decode_block_and_write. NUM_FPB=3 frames/block.
- **Local attention**: `local_attn_size 21`, `use_relative_rope true`, KV cache = local_attn_size × frame_seq_length; per-GPU cross-attn cache.
- **Helios Triton kernels** (PKU-YuanGroup): flash norms + flash RoPE (eager fallback).
- **Low-bit DiT**: FP8 block-wise GEMM (Triton + PyTorch fallback), fp8 per-block (128) / per-token-group quantizers, int8 SGL kernel; from Tencent AngelSlim lineage. `use_fp8_gemm: true` in default config; the HF Space forces it FALSE for ZeroGPU stability.
- Acknowledges: Causal Forcing (thu-ml), AngelSlim, LightX2V, taehv, Wan2.2, Helios.

## ZeroGPU Space recipe (reusable patterns)

- **gradio.Server + raw FastAPI WebSocket** (`/ws`) streaming binary JPEG frames; `/start_game` `/stop_game` API endpoints. No UI polling.
- Per-client `session_id` isolation (concurrent players never share state).
- **Per-visitor quota billing**: forward HF iframe's `x-api-token`/`x-ip-token` into the worker's gradio request context so `@spaces.GPU` consumes the VISITOR's quota, not the owner's.
- Rollout runs in forked subprocess → controls cross via multiprocessing Queue (picklable ControlCommand/StopCommand).
- **Steady-cadence pacing**: GPU bursts a whole block; parent thread paces frames evenly — EMA (α 0.25) of per-block generation time, `next_send = max(now, next_send + interval)` clock, coalesce stale frames (queue maxsize 4).
- Config: 704×1280 stream → latent 44×80 (upsample 16), noise [1,3,48,44,80] bf16; MAX_BLOCKS_PER_SESSION 512; SESSION_IDLE_TIMEOUT 600 s; GPU_DURATION 90 s.

## Gotchas

- Space raw files live under `/spaces/{id}/raw/main/...` — omitting the `spaces` prefix returns "Invalid username or password." (29-byte body).
- `hf download` works (`hf download acvlab/ABot-World-0-5B-LF --local-dir ./checkpoints/...`); ModelScope mirror: `amap_cvlab/ABot-World-0-5B-LF`.
- ZeroGPU Space: 1 replica zero-a10g, startup timeout 40 m (weights download at boot via snapshot_download).
- fp8 path is for the 5090 desktop deployment, NOT the ZeroGPU Space.
