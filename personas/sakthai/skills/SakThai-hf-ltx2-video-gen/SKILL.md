---
name: SakThai-hf-ltx2-video-gen
author: SakThai
license: MIT
description: "Complete reference on Lightricks LTX-2 / LTX-2.3 video generation — open 22B DiT family with native audio, ComfyUI workflow-in-Space pattern, MSR IC-LoRA likeness guidance, GGUF prompt enhancers, ZeroGPU recipes. Verified 2026-07-31 on Fighterdan/LTX-2.3-10Eros_I2V."
version: 1.0.0
category: mlops
tags: [huggingface, video-generation, ltx, lightricks, comfyui, native-audio, zerogpu, spaces]
platforms: [linux]
---

# LTX-2 / LTX-2.3 Video Generation (Lightricks)

Class-level reference for the open LTX-2/2.3 video-gen model family and the ComfyUI-workflow-in-Space pattern used to serve it on HF ZeroGPU. Ground-truth verified 2026-07-31 by deep-diving `Fighterdan/LTX-2.3-10Eros_I2V` (a 182 KB `app.py` full ComfyUI runner + 142-node workflow JSON).

## Family facts

- **LTX-2** (Lightricks): open 22B video DiT lineage, diffusers + ComfyUI support. Repos: `Lightricks/LTX-2`, `Comfy-Org/ltx-2` (ComfyUI text-encoder bundle), `ComfyUI-LTXVideo` (official ComfyUI nodes).
- **LTX-2.3**: successor adding **native audio** — a separate audio VAE + audio latents; video and audio generated jointly. Checkpoints ship as `ltx-2.3-22b-distilled-1.1_transformer_only_fp8_scaled.safetensors` (22B distilled, transformer-only, FP8-scaled) and `ltx-2.3-22b-distilled-lora-1.1_*` dynamic-rank LoRAs (FRO90/FRO99, avg-rank ~105–111).
- **Text encoder**: Gemma 3 12B (`gemma_3_12B_it_fp4_mixed.safetensors` / FP8-scaled, or `gemma-3-12b-it-Q2_K.gguf` via ComfyUI-GGUF `DualCLIPLoaderGGUF`) + `ltx-2.3_text_projection_bf16.safetensors` (type `ltxv`).
- **VAEs**: `LTX23_video_vae_bf16_KJ.safetensors` (video), `LTX23_audio_vae_bf16_KJ.safetensors` (audio), approx `taeltx2_3.safetensors`, `vae_tiny`. Audio nodes: `LTXVEmptyLatentAudio`, `LTXVConcatAVLatent`, `LTXVSeparateAVLatent`, `LTXVAudioVAELoader`, `LTXVAudioVAEDecode`.
- **Spatial upscaler**: `ltx-2.3-spatial-upscaler-x2-1.1.safetensors` + `LTXVLatentUpsampler` + `LTXVCropGuides`.
- **Samplers**: `euler_cfg_pp` / `euler_ancestral_cfg_pp`, SamplerCustomAdvanced + CFGGuider (low cfg ~1–3), `LTX2_NAG` node (widgets `[11, 0.25, 2.5, true]`).

## Native audio recipe (LTX-2.3)

1. Load both video and audio VAEs (`LTXVAudioVAELoader`, bf16, main_device).
2. Create empty audio latent (`LTXVEmptyLatentAudio`) alongside video latent (`EmptyLTXVLatentVideo`).
3. **Audio-reference conditioning**: `audio_ref_enabled` + `audio_ref_guidance_scale` (~3.0), stem separation (`audio_ref_stem_sep`), normalize — an input audio conditions the generated soundtrack. Optionally patch with **identity guidance** (`LTXVAudioVAELoader` patch, `identity_guidance_scale` ~3.0; lower if audio problems).
4. Concatenate AV latents (`LTXVConcatAVLatent`), sample, decode both (`LTXVAudioVAEDecode`), mux to h264-mp4 @ 24 FPS.

## MSR (Multi-Subject Reference) IC-LoRA likeness

- LoRA: `LTX2.3-Licon-MSR-test_version.safetensors` from `LiconStudio/LTX-2.3-Multiple-Subject-Reference`; custom node `ComfyUI-Licon-MSR` (`LiconMSR`).
- Recipe: 2 reference images + 1 background image → `LTXICLoRALoaderModelOnly` → likeness guide (strength ~0.9), likeness anchor (~0.15), latent anchor (~0.08), first-frame strength (~0.82); face mode anchor-only / auto-face / manual bbox. MSR injects a **pseudo-video latent** (`msr_pseudo`) + guide/crop nodes; pass-1 `LTXVImgToVideoInplaceKJ` rewired through the MSR guide.
- Extraction tip: `reference_downscale_factor` lives in the safetensors metadata — read it programmatically instead of hardcoding.

## ComfyUI-workflow-in-Space pattern (RunExx)

A Space that *is* a ComfyUI runner:
- Ship the workflow JSON (`runexx_*.json`, nodes/links/groups/subgraphs), convert at runtime, prune GGUF-parallel paths and preview nodes via **rewires keyed by node ID**; keep architectural nodes (LiconMSR, LTXVAudioVAE*, ConcatAVLatent) intact. Multi-pass via subgraphs ("Single vs 2 pass").
- Requirements give it away: `websocket-client`, `gguf`, `spandrel`, `rotary_embedding_torch`, `mediapipe`, `av` (PyAV), `kornia<0.8` — plus torch 2.8.0+cu128 via `--extra-index-url https://download.pytorch.org/whl/cu128`.
- ZeroGPU serving: gradio 5.44.1, hardware `zero-a10g`, 1 pinned replica. 22B FP8 + dynamic-rank LoRAs + chunked feed-forward (`LTXVChunkFeedForward [2, 4096]`) + attention tuner patches (`LTX2AttentionTunerPatch`) + sigma-gated KV-strength hooks (funpack-style `_sigma_gated_strength` ramps) keep it inside a10g memory.
- **GGUF prompt enhancer**: optional LLM rewrites prompts before encoding — e.g. `SulphurAI/Sulphur-2-base` → `prompt_enhancer_uncensored/prompt_enhancer_uncensored-q8_0.gguf` + `mmproj-*.gguf` (q8_0, multimodal). Load via llama.cpp-style GGUF + mmproj pair; `enhance` button before generation.

## Pitfalls

| Pitfall | Mitigation |
|---------|------------|
| Thinking a Space is a thin wrapper when app.py >100 KB | It's a full pipeline (ComfyUI runner). Grep `WORKFLOW_REPO|WORKFLOW_REVISION|RUNEXX_|_NODE_` to find the embedded workflow. |
| Space README is only the YAML header (~250 B) | All value in `app.py` + bundled `*_workflow.json` (per Space deep-dive rule 4a-4). |
| `not-for-all-audiences` tag on finetunes (e.g. TenStrip/LTX2.3-10Eros, 224K downloads / 524 likes) | Community/uncensored finetune — report facts, note dual-use, don't advertise. |
| `numParameters: None` on image-to-video models | Common for video checkpoints — get architecture from the checkpoint filenames (22B distilled, FP8-scaled) + workflow node config, not `numParameters`. |
| Audio missing from output | Check `audio_ref_enabled`/identity-guidance interaction; identity guidance ~3.0 "lower if audio problems" per the recipe. |

## Scan references
- Space: `Fighterdan/LTX-2.3-10Eros_I2V` (134 likes, ZeroGPU, gradio 5.44.1) — findings: `~/profiles/sakthai/cron/findings/hf-findings-2026-07-31-ltx-2-3-10eros-i2v.md`
- Model: `TenStrip/LTX2.3-10Eros` (base `Lightricks/LTX-2`), workflow repo `TenStrip/LTX2.3-10Eros_Workflows`.
