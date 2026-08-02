---
name: SakThai-hf-videococo-code-cot
author: SakThai
license: MIT
description: "Complete reference on VideoCoCo (arXiv:2607.27380) — code-as-CoT physically-consistent video generation via an agentic dual-engine system (coding agent → Blender simulation draft → generative video editor). Covers the pipeline, agent skills, OmniWeaving/HunyuanVideo-1.5 base, FSDP2 patch, and toy dataset."
version: 1.0.0
category: mlops
tags: [huggingface, video-generation, chain-of-thought, blender, omniweaving, hunyuanvideo, agents]
platforms: [linux]
---

# VideoCoCo — Code-as-CoT Video Generation (Agentic Dual-Engine)

> Scan source: HF trending daily-papers fallback 2026-07-31 (arXiv:2607.27380, 45 upvotes, published 2026-07-29). Findings: `cron/findings/hf-findings-2026-07-31-videococo.md`.

## One-line summary

Text-to-video models fail at physical consistency because temporal evolution is inferred from a compressed prompt; VideoCoCo instead has a **coding agent write executable Blender code as a process-level chain of thought**, runs it to render a deterministic white/clay *proxy* draft, then restyles the draft into a photoreal video with a draft-conditioned **video editor** (Tencent HY-OmniWeaving / HunyuanVideo-1.5).

## Key repos

| Repo | Type | State (2026-07-31) |
|---|---|---|
| `micky-li-hd/VideoCoCo` (GitHub) | code | 37 stars, pushed 2026-07-29 — live artifact |
| `mickyhimself/VideoCoCo` (HF) | model | **stub** (`.gitattributes` only, 0 dl; weights "uploading") |
| VideoCoCo-3K | dataset | **not on Hub yet** (paper references it) |
| `tencent/HY-OmniWeaving` (HF) | base model | 704 dl / 272 likes, HunyuanVideo-1.5, image-to-video |

## Pipeline

1. **physical-state-planner** (skill): prompt → implementation-neutral physical plan: `physical_intent`, scene (initial/process/final objects), 4–6 semantic keyframes K0–K4 with `time_hint` percentages, transitions with `origin`/`direction`/`material_source`/`continuity`, causal `before/after` constraints, `must_show`/`must_avoid`, `uncertain_assumptions`. Dataset-agnostic JSON schema.
2. **physical-video-blender-implementer** (skill): plan → standalone Blender Python script. White/clay renders ONLY (grayscale materials, no semantic color — physics carried by shape/opacity/deformation/motion). Causal visibility: new states appear no earlier than their causing transition, originate from stated origin. Preview: 720p, 16:9, 5 s, 24 fps + keyframe-aligned audit sheet.
3. **blender-mcp-video** (skill): Blender MCP (port 9876, GUI instance) for preview/debug vs Blender CLI for final batch renders. Blender 5.x direct-MP4 gotcha: set `image_settings.media_type = "VIDEO"` BEFORE `file_format = "FFMPEG"` (dynamic enum order).
4. **seedance-edit-prompt / seedance-distill** (skills): NOT shipped in the repo (404s) — the restyle-stage skills are the missing half of the public recipe.
5. **Editor**: draft-conditioned v2v edit via OmniWeaving tuned transformer → photoreal video.

## Base architecture — HY-OmniWeaving / HunyuanVideo-1.5 transformer

Verified `transformer/config.json` (`tencent/HY-OmniWeaving`):

- patch_size [1,1,1], in_channels 32 / out_channels 32
- hidden_size 2048, heads_num 16, mlp_width_ratio 4, mlp_act gelu_tanh
- **54 double blocks + 0 single blocks** (MMDiT-style)
- rope_dim [16,56,56], qkv_bias true, qk_norm rms (rms_norm type)
- text_projection `single_refiner`, text_states_dim 3584, guidance_embed false
- Tags: HunyuanVideo-1.5, diffusers, arxiv:2603.24458 + arxiv:2511.18870, license:other

VideoCoCo is a **tuned transformer** (SFT or LoRA) swapped into this pipeline — it does NOT fork the model code; a small patch + bench scripts ride on the official OmniWeaving repo.

## FSDP2 patch highlights (verified in `videococo-omniweaving.patch`)

1. **flash3 → flash2 fallback** in `maybe_fallback_attn_mode` (was straight to torch).
2. **`LORA_ADAPTER_METADATA_KEY` import tolerance** for diffusers <0.33.
3. **LoRA-save deadlock fix under FSDP2** (`train.py`): old code saved LoRA adapters under `is_main_process` only → rank0 alone entered the all-gather → deadlock → platform SIGKILL at step 500 → poisoned resume. Fix: gather full unsharded state dict on EVERY rank (`StateDictOptions(full_state_dict=True, cpu_offload=True)`), only rank0 writes the LoRA subset (`safetensors.save_file`, filter keys containing `lora_` + adapter name), best-effort non-fatal.
4. **Incomplete-checkpoint guard**: dcp load now checks `transformer/.metadata` existence instead of dir existence.
5. **Real v2v data path**: `create_dummy_dataloader4` honors `V2V_LATENTS_DIR` (pre-encoded latents from `v2v_data/preencode_v2v.py`) instead of random dummies.

## Inference

```bash
git clone https://github.com/Tencent-Hunyuan/OmniWeaving.git && cd OmniWeaving
git apply /path/to/videococo/inference/patches/videococo-omniweaving.patch
cp -r /path/to/videococo/inference/bench_infer ./bench_infer
huggingface-cli download mickyhimself/VideoCoCo --local-dir ./VideoCoCo-weights
# assemble pipeline: base OmniWeaving pipeline + VideoCoCo-weights/transformer/
python bench_infer/batch_infer_edit.py \
  --model_path /path/to/assembled_pipeline \
  --manifest data/toy_cases/manifest.jsonl --dataset_dir data/toy_cases \
  --out_name out.mp4 --video_length 81 --num_inference_steps 50
```

- `batch_infer.py` = text→video baseline; `batch_infer_edit.py` = v2v (clay proxy + edit_prompt → photoreal).
- `run_node_infer.sh` / `run_node_infer_edit.sh` = 8-GPU manifest-sharded fan-out.
- `export_tuned_ckpt.py` / `export_tuned_lora_ckpt.py` = convert full-SFT / LoRA checkpoint to a pipeline transformer.

## Toy dataset format (verified manifest.jsonl, 8 cases)

One dir per case: `video.mp4` (white/clay proxy), `seedance.mp4` (photoreal target), `edit_prompt.txt` (~1 KB structured restyle instruction). Manifest line: `{case_id, source, target, instruction, category}`. Categories: buoyancy, stress, melting ×2, surface tension, sublimation, elasticity, boiling. Explicitly a format-inspection toy, not training-scale (training corpus = unreleased VideoCoCo-3K).

## Benchmarks (paper)

- PhyGenBench: OmniWeaving baseline 0.475 → **0.558**
- VBench-2.0: 52.18 → **77.88** — best average on both

## Pitfalls

- **HF model repo may be an empty stub** — verify siblings/`usedStorage` before deep-diving weights; the GitHub repo is often the live artifact while weights "are uploading".
- **README lists 5 agent skills but only 3 are committed** — `seedance-edit-prompt` and `seedance-distill` raw fetches return 404; don't report them as shipped.
- License chain: dataset research-use; tuned weights are a **Model Derivative under Tencent HY Community License Agreement** (not Apache/MIT).
- The `edit_prompt.txt` format (`--resolution 720p --duration 5 --ratio 16:9` trailing flags) is a useful template for draft-conditioned video-editing prompts.
