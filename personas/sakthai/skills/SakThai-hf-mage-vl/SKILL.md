---
name: SakThai-hf-mage-vl
description: "Complete reference on Microsoft Mage-VL — a 4B codec-native streaming VLM (Mage-ViT from-scratch encoder + Qwen3-4B decoder + Mamba-1 StreamMind cognition gate). Architecture, codec tokenization, gate, training curriculum, benchmarks, deployment."
---

# Mage-VL — Codec-Native Streaming Multimodal Foundation Model

Reference for `microsoft/Mage-VL` (arXiv:2607.24904, Apache-2.0, public,
~9.48 GB BF16) and its demo Space `microsoft/mage-vl-demo` (ZeroGPU, Gradio
6.20.0). Scanned 2026-07-31 — first codec-native VLM + Mamba/SSM entry in
tracker history. Findings: `~/profiles/sakthai/cron/findings/hf-findings-2026-07-31-mage-vl.md`.

## Core idea

Instead of decoding video into uniformly-sampled frames and pushing a dense
patch grid through a frozen web-pretrained ViT, Mage-VL follows video-codec
structure: keep **every anchor (I) frame patch** and only the **predicted (P)
frame patches where the codec spends bits** (motion + new detail), then pack
survivors into **canvases**. Result: visual tokens cut by **>75%** (~1/8 of
dense sampling), **up to 3.5× wall-clock inference speedup** at matched
accuracy. Codec-agnostic: traditional H.264/HEVC (motion vectors + residual
energy) OR neural DCVC-RT (learned rate map) — same interface, no retraining.

## Architecture (config.json ground truth)

| Component | Details |
|---|---|
| **Mage-ViT** (from scratch) | `mage_vl_vision`: hidden 1024, 24 layers, 16 heads, intermediate 4096, patch 16, image_size 448, out_hidden 2560, spatial_merge_size 2, temporal_patch 1, frame_windows_size 4, rope_theta 10000, LayerNorm (not RMS), use_head false, max_pos 8192 |
| **Qwen3-4B-Instruct-2507** decoder (only pretrained part) | qwen3: 36 full-attn layers, hidden 2560, 32 heads / 8 KV GQA, head_dim 128, intermediate 9728, vocab 151,936, max_pos 262,144, rope_theta 5e6 |
| **Projector** | two-layer MLP 2560 → 2560 |
| **Special tokens** | vision_start 151652, vision_end 151653, image_token_id 151655, video_token_id 151656 |
| **Checkpoint** | 2 shards ~9.48 GB BF16 (696 keys) + `streammind_gate.safetensors` ~1.07 GB |
| **Companion** | `microsoft/Mage-ViT` — standalone encoder, ViT-pretrain only (no VLM joint training) |

## StreamMind gate — System 1 / System 2

- **PreNet**: Linear(2560→2560) + leaky ReLU.
- **VideoMamba**: `create_block(d_model=2560, d_intermediate=0, layer_idx=0)` —
  **Mamba-1** mixer, upstream defaults: d_state=16, d_conv=4, expand=2,
  dt_rank=ceil(2560/16)=160, LayerNorm, mlp=Identity, fused_add_norm=False.
- **perception_tokens()**: `[B,T,P,D]` patches → mean over P → one **EPFE
  token per time step** → pre_net → Mamba-1 → post_net.
- **ClsNet**: 4-layer Qwen3 (`Qwen3Config(vocab_size=2, hidden 2560, 32/8
  heads, intermediate 12288, head_dim 128, max_pos 8192)`), trained with
  class-weighted CE (weight=[0.15, 0.85]) for silent/speak.
- Gate predicts `p_speak = g(h_t)` per rolling codec window; full VLM (frozen)
  generates only when `p_speak ≥ τ`; text query injectable anytime. **One
  checkpoint = understanding + gate, no separate streaming model.**

## Training — 5-stage supervised curriculum (no RL)

1. Multimodal alignment: ~350M image captions + 4.2M short-video captions.
2. Instruction tuning + short temporal grounding: ~54M image-instruction +
   3.4M 30–180 s video captions.
3. Temporal-horizon expansion: LLaVA-Video, TimeLens, VideoChat-Flash, Molmo2.
4. Codec-native long-context adaptation: 350K long videos as rolling windows
   (up to 384/768 frames).
5. Proactive streaming alignment: gate on ~3.3M streaming samples (encoder +
   LLM frozen).

AI4AI pipeline: agentic caption loop (GPT-5 rubric scorer + Copilot co-design).

## Key benchmarks

- **Image/doc:** DocVQA-val 95.14, InfoVQA 80.33, ChartQA 84.88, OCRBench
  81.80, MMStar 67.32, CV-Bench 87.79, EmbSpatial 82.67, **CrossPoint 80.00 vs
  Qwen3-VL-4B 26.90**. Trails TextVQA (77.28) + CC-OCR Doc (32.25).
- **Video/temporal:** VideoMME 64.0, NextQA 83.1, MLVU-dev 68.7,
  **VideoEval-Pro 45.2 (vs 20.7)**, Timelens-QVHighlight 57.4 (+22.5),
  VSI-Bench 64.3 (+11.0), Ref-DAVIS17 25.83 (vs 7.48). Trails MV-Bench (65.1).
- **Streaming:** SoccerNet TimVal 55.54 / F1 16.35 / ROC-AUC 83.14 / PR-AUC
  9.30 (best on precision-sensitive metrics; JoyAI-9B wins TriggerAcc only).
  **OVO-Bench Overall 64.00 = SOTA among streaming architectures.**

## Deployment

- **Offline:** `AutoProcessor/AutoModelForCausalLM.from_pretrained(..., trust_remote_code=True)`
  (image + frame-sampled video need nothing extra). `attn_implementation="sdpa"`
  if no flash-attn. Codec video needs `codec-video-prep` + ffmpeg/ffprobe.
- **Online:** SGLang branch `feat/mage-vl` (github.com/kcz358/sglang), needs
  protobuf-compiler + Rust 1.90.0.
- **Demo Space:** `video_backend="codec"` + `codec_config={engine: "hevc",
  target_canvas: N, patch: 16}` + `max_pixels=150000`; frames path via
  `MageVLVideoProcessor(min_pixels 3136, max_pixels 589824)`; 150 s ffmpeg
  trim; disk-cached codec processing (one cache entry shared between gallery +
  processor).

## Pitfalls / notes

- **Space vendors a pure-PyTorch `mamba_ssm` stand-in** (`mamba_ssm/models/mixer_seq_simple.py`)
  because real mamba-ssm CUDA extensions have no wheel for the Space runtime.
  Parameter names/shapes match upstream so `streammind_gate.safetensors` loads
  with `strict=True` — proof the gate is Mamba-1 (d_state 16, d_conv 4,
  expand 2, dt_rank ceil(d/16)).
- The DCVC-RT neural-codec engine ships in the model repo
  (`neural_codec/`, py_rans CUDA extensions, ~265 MB tars) but is **not** wired
  into the demo Space — traditional HEVC path only there.
- `codec-video-prep` pip package = lightweight way to reproduce codec readiness
  (`cv-preinfer`).
- ZeroGPU duration budgeting (measured): image `16 + tokens*0.013` s; video
  `30 + tokens*0.020` s; streaming `14 + segs*(2.5 + tokens*0.021)` s.
- Model is public (`gated: false`) — unlike the sibling `microsoft/Mage-Flow`
  family whose models are all private/gated.
