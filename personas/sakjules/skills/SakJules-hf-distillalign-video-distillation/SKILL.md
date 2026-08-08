---
name: SakJules-SakThai-hf-distillalign-video-distillation
description: "Class-level reference on autoregressive video distillation — DMD mode-seeking vs Consistency-Distillation mode-covering, distributional precision/coverage evaluation in V-JEPA2 latent space, and the DistillAlign release (Wan2.1-1.3B students, 25K cle"
---

# Autoregressive Video Distillation — DistillAlign (mode-covering × mode-seeking)

Reference for the **DistillAlign** method (arXiv 2607.26811, Riemann Dynamics + NTU, 2026-07-31 scan; HF repos `LiJiaxing/DistillAlign`, datasets `LiJiaxing/DistillAlign_1p3b_25K` / `DistillAlign_14B_25K`). First video-distillation-methodology entry in the HF trending scanner's history.

## The problem

Autoregressive video distillation (Wan2.1 family) uses a multi-stage pipeline:
1. **Initializer** stage — train a student toward the teacher.
2. **DMD stage** — Distribution Matching Distillation.

Prior work judged the intermediate student with **visual scores (VBench)**. DistillAlign shows this is misleading because of the objective mismatch:

- **DMD is mode-seeking** (reverse-KL): it collapses toward high-probability teacher regions.
- Therefore a good initializer should match the **mode COVERAGE** of the target DMD teacher, not merely high visual quality.
- VBench hides precision/coverage failures: some initializers hit high precision but low coverage → suboptimal DMD refinement.

## Key contributions

1. **Distributional evaluation protocol** — measure **precision + coverage** between student and teacher distributions in a **shared latent space**: V-JEPA2 ViT-H features (`facebook/vjepa2-vith-fpc64-256`), 2560-D, token mean/std concat pooling, L2-normalized, 8 uniform frames from first 81 frames.
2. **Joint distillation** — combine DMD's mode-seeking objective with a **Consistency Distillation (CD)-based mode-covering constraint** (addresses late-training coverage collapse even when targets are aligned).
3. **Headline result** — with only a **1.3B DMD teacher**, DistillAlign students **surpass baselines refined with a 14B DMD teacher**. Alignment matters more than teacher scale.

## Distributional eval protocol (reusable pattern)

- Grid: 16 prompts × 16 seeds (`11,22,33,42,44,55,66,77,88,123,456,789,2024,3407,7777,9999`) = 256 samples per teacher.
- Teacher generation: 25-step UniPC, timestep shift 8.0, classifier-free guidance 5.0, official negative prompt.
- Caches: `.npz` 256×2560 features + `.meta.json` with extractor fingerprint and prompt/seed hash — the metric CLI **rejects incompatible caches** so numbers stay comparable.
- Pass the `.npz` to `--teacher-features`; only the student side needs generating (`evaluate_distribution.py run --teacher-model Wan2.1-T2V-14B --teacher-features ...`).

## Released artifacts

### Model repo `LiJiaxing/DistillAlign` (Apache-2.0, text-to-video, 34 dl / 1 like at scan, ~23.4 GB, 523 files)

All generators are **Wan2.1-1.3B students**; the name size = the **teacher** used during training. Four checkpoints, each `{"generator": state_dict}`, ~5.68 GB each (verified via tree endpoint):

| Checkpoint | Role |
|---|---|
| `distillalign_init_1p3b_teacher.pt` | Pre-DMD initializer → Wan2.1-T2V-1.3B teacher |
| `distillalign_init_14b_teacher.pt` | Pre-DMD initializer → Wan2.1-T2V-14B teacher |
| `distillalign_distill_1p3b_teacher.pt` | Final joint-distilled generator (1.3B DMD teacher) |
| `distillalign_distill_14b_teacher.pt` | Final joint-distilled generator (14B DMD teacher) |

Code: `github.com/LiJiaxing0213/DistillAlign-release`.

### Datasets — 25K clean VAE latents per teacher

- `LiJiaxing/DistillAlign_1p3b_25K` — **open**, Apache-2.0, ~209.6 GB, 25,002 files.
- `LiJiaxing/DistillAlign_14B_25K` — **gated: manual** (first gated:manual dataset seen in scanner history; metadata public, data needs request).

Format: 25,000 samples, prompts from **VidProM** (English), Wan2.1 VAE (8× spatial, ~4× temporal), latent shape **`[21, 16, 60, 104]`** = 21 temporal latent frames (~81 video frames) × 16 latent channels × 60 latent height (→480 px) × 104 latent width (→832 px), `float32`, one `.pt` per sample in `part0/` = dict `{prompt_str: latent_tensor}`. Use as regression/distribution-matching targets for video-diffusion distillation or latent-space research.

### Teacher caches (`teacher_caches/`)

- `wan2.1_t2v_{1.3b,14b}_reference_vjepa2.npz` — 256×2560 features.
- `videos/wan2.1_t2v_{1.3b,14b}_reference/` — 256 reference videos each (verified: 371.2 MB / 348.9 MB).

## Scan notes / pitfalls

- **Repo is a method + weights + data release, not a serving-ready model** — checkpoints are plain state_dicts for the project's own inference/eval code; no `config.json`, no transformers loader. Report as such.
- **Checkpoint sizes identical across all 4 files (~5.68 GB)** — the teacher size is in the NAME, not the file size; all are 1.3B-student checkpoints.
- **Sibling datasets differ in gated state** — always check `gated` per dataset; don't assume family-wide access. `gated: manual` = request-required, `false` = open.
- **Tree-endpoint sizes** are the reliable byte source; `siblings[].size` returns null for these `.pt`/`.npz` files.
- **Diversity heuristic applied:** daily-papers fallback picked this because #1 (TurboVLA, 122 upvotes) was already scanned; video-generation was covered by Spaces (wan555, wan2-2-i2v-v3, LTX-2.3) but the *distillation-methodology* class was unrepresented.

## Related

- Wan2.1 model family: `Wan-AI/Wan2.1-T2V-*` (upstream weights keep their own licenses; release is Apache-2.0).
- Distributional eval feature extractor: `facebook/vjepa2-vith-fpc64-256`.
- Prior video-gen scans in this tracker: `kulkas2pintu/wan555`, `cinderholm/wan2-2-i2v-v3`, `Fighterdan/LTX-2.3-10Eros_I2V`.
