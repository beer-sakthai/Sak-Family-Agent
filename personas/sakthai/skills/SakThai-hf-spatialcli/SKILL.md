---
name: SakThai-hf-spatialcli
description: "SpatialCLI \u2014 the tool-use \u2192 capability-internalization paradigm for spatial\
  \ VLMs (arXiv:2607.27703): 3-stage Call\u2192Learn\u2192Internalize training, Qwen3-VL-8B\
  \ fine-tune config, SpatialCLI-Bench + CII validation + RL parquet layout, MindCube/BOPASK/DA-2K/MMSI-Bench\
  \ eval bundles."
---

# SpatialCLI — Reasoning With Spatial Tools, Then Without Them

Class-level reference for the SpatialCLI paradigm and release (`ZYT-MFM/SpatialCLI-8B` + `ZYT-MFM/SpatialCLI-Data`, arXiv:2607.27703, 2026-07-30, cs.AI, 19 upvotes at scan). Scanned 2026-07-31 as a daily-papers fallback pick (all 30 `/api/trending` items were covered).

## The paradigm (why it matters)

Embodied agents face a capability mismatch: general VLMs reason about the task but miss visual details; specialist vision models capture details but can't make task-level decisions. SpatialCLI bridges this with **tool amortization**:

1. **Call** — specialist vision models (localization, segmentation, depth, pose) are exposed as *spatial tools* augmenting the VLM's perception.
2. **Learn** — Cold-Start SFT + agentic RL trains the VLM to *use* the tools well.
3. **Internalize** — successful tool-use trajectories are verbalized and trained back into the model, so it can reason **without** the tools at inference time.

Distinct from tool-calling-only agents (XYZ-Aquila-SFT, tool-trace datasets): the end state is a model that has *absorbed* the perceptual capability, not one that keeps calling APIs.

**Headline results (paper, self-reported):** MindCube — Qwen3-VL-8B-Instruct 29.3% → 84.6% with tools (beats GPT-5.6 Sol with tools at 72.1%); retains 73.8% *without* tools after internalization.

## Model: ZYT-MFM/SpatialCLI-8B

- MIT, bf16, single `model.safetensors` = 17,534,340,584 B ≈ 8.77B params (full checkpoint, not a stub)
- `Qwen3VLForConditionalGeneration` (`qwen3_vl`), fine-tune of **Qwen3-VL-8B-Instruct** (transformers 5.5.4)
- **Text:** 36 layers, hidden 4096, 32 heads / 8 KV GQA, head_dim 128, intermediate 12288, vocab 151,936, 262,144 ctx, rope_theta 5M, mrope [24,20,20]
- **Vision:** 27 layers, hidden 1152, 16 heads, intermediate 4304, patch 16, spatial_merge 2, temporal_patch 2, **DeepStack visual indexes [8,16,24]**, out_hidden 4096
- Card is minimal (title + paper link only) — config.json + dataset + arXiv are the sources of truth
- `ZYT-MFM` is a fresh account (2 repos, no profile) — identify the lab via the arXiv author list (Peiliang Li, Xiaozhi Chen = AD/embodied pedigree), not HF profile APIs (both `/api/orgs/` and `/api/users/` return null)

## Dataset: ZYT-MFM/SpatialCLI-Data

MIT, image+text. Layout (three dirs):
- `data/assets/` — ONE shared image pool for train and eval: BOPASK core (handal/hope/ycbv images + depth maps + goal/target/rearrange masks), bopask linemod train_pbr rgb, mindcube images. Manifest totals: 10,228 shared files ≈3.51 GB + 7,556 new ≈2.11 GB
- `data/eval/` — benchmarks + CII validation + manifest
- `data/train/RL/` — RL parquet + manifest

### SpatialCLI-Bench (own benchmark)
- 516 test rows in `data/eval/SpatialCLI-Bench/full.jsonl`
- Row schema: `id`, `prompt` [{type: image|text, value}], `answer` (letter), `candidates` (6), `source`, `category`, `required_capabilities`, `difficulty_bucket`, `source_metadata` (source_type/source_ids/scene_id/image_hashes sha256), per-option fields A–F
- Category mix (verified): GDP 187 / GD 114 / GP 113 / DP 102 · difficulty easy 98 / medium 335 / hard 83 · sources mindcube 195 / bopask 162 / refspatial 159
- Prompt style: MCQ with "verify every clause" instruction, JSON `{"answer": "C"}` output contract

### CII validation (data/eval/cii/)
- 5 direct **spatial-tool-output imitation** tasks: locate / segment / depth / pose-object / pose-camera — 200 rows each (1,000 total), 1,313 visual refs (1,181 unique), `verl_sft` parquet (VerL RL-framework SFT schema) — "separate from the public benchmark suite"

### RL data (data/train/RL/)
- `SpatialCLI-Train_train.6350.parquet` — 6,350 rows, 9,831 image refs (7,807 unique)
- `SpatialCLI-Bench_eval.516.parquet` — 516 rows (789 refs, 690 unique)

### Bundled external eval sets
- **MindCube** — 1,200 rows (verified), 2-view ego-motion "which direction did I move" MCQ
- **BOPASK** subsets — Object-Rearrangement.jsonl + Trajectory.jsonl (6D pose)
- **DA-2K** full.jsonl (depth) · **MMSI-Bench** subsets — Motion-Cam.jsonl + Pos-Cam-Cam.jsonl (moving-camera pose)

## Pitfalls / operational notes

- **Composite license:** repo is MIT but wraps third-party benchmark content — eval README explicitly says to confirm upstream licenses (SpatialCLI-Bench, DA-2K, MindCube, MMSI-Bench, BOPASK) before redistribution. Always note this when recommending the dataset.
- **Huge sibling lists:** the dataset has ≈840K chars of sibling entries — use the manifests (`data/eval/cii/manifest.json`, `data/train/RL/manifest.json`) for row/asset counts, never the sibling array.
- **`curl -sL` mandatory** for `/resolve/` fetches (redirect body trap).
- All asset paths inside JSONL/parquet records are **relative to repo root** — run consumers from repo root.
- Eval JSONL uses `answer` (letter) while MindCube JSONL uses `ground_truth` — schema differs per bundle; check the top-level keys before parsing.
