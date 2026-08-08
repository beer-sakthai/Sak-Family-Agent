---
name: SakJules-SakThai-hf-turbovla
description: "TurboVLA — LLM-free real-time Vision-Language-Action (VLA) architecture. Direct V+L→A mapping with DINOv3 + frozen BERT + BiAttentionBlock bidirectional fusion + ACT-style chunk decoder. 0.2B params, 97.7% LIBERO, 32 Hz / 0.9 GB VRAM on RTX 4090. Dai"
---

# TurboVLA — LLM-free Real-Time VLA (arXiv 2607.27205)

**One-liner:** reformulates the conventional LLM-centric `V → L → A` VLA pathway as a direct `V + L → A` mapping — no LLM as the central interface between perception and action.

**Why it matters:** 0.2B params, 97.7% avg LIBERO success, 31.2 ms inference (~32 Hz), 0.9 GB inference VRAM on a consumer RTX 4090 — matches/exceeds much larger LLM-centric policies at a fraction of the cost. First robotics/`pipeline_tag: robotics` entry in the HF trending tracker history (scan 2026-07-31).

## Repos

| Asset | ID / URL |
|---|---|
| HF model | `H-EmbodVis/TurboVLA` (created 2026-07-31, 0 dl / 1 like at scan) |
| GitHub | https://github.com/H-EmbodVis/TurboVLA (Apache-2.0, 117★) |
| arXiv | https://arxiv.org/abs/2607.27205 (2026-07-29) |
| Project | https://h-embodvis.github.io/TurboVLA/ |
| Train data | `StarVLA/RoboTwin-Clean` (RoboTwin 2.0, 50 tasks) |

## Architecture

```
multi-view RGB ──► DINOv3 (ViT-B/16 LIBERO | ViT-L/16 RoboTwin, full unfreeze)
                         │  + learned per-view embedding
                         ▼
              VisionProjector (MLP + skip + LN)
                         │
   instruction ──► BERT-base-uncased (FROZEN, text cache) ──► text tokens
                         │
                         ▼
   GroundingDINOFeatureEnhancer (6 layers)
     = text self-attn TransformerEncoderLayer (4 heads)
       + BiAttentionBlock bidirectional v↔l cross-attention (4 heads, inner 1024)
                         │
   robot state ──► StateProjector (MLP → 2 learned-pos tokens)
                         │
                         ▼
   ACTActionDecoder — nn.TransformerDecoder (3 layers, 8 heads, ff 3072)
     learned action_queries (chunk_size), tanh MLP head ──► action chunk
```

**Key components** (from `turbovla/models/turbovla.py`, `components/fusion.py`):
- **DINOv3 visual encoder** — flash_attention_2, BF16 autocast, `dinov3-vitb16`/`vitl16-pretrain-lvd1689m` (facebook/dinov3 ViT-B/L, 1689M-image LVD pretraining), vision_dropout 0.1. DINOv3 weights NOT redistributed.
- **Frozen BERT text encoder** — `google-bert/bert-base-uncased`, max_text_len 256, cached instruction features (runs once per instruction, not per step — big inference win).
- **BiAttentionBlock** — GroundingDINO lineage: cross-modal attention both directions (v→l and l→v) with FeatureResizer, scaled-dot-product alignment, l1/l2/softmax norm options. This IS the "lightweight bidirectional vision-language interaction".
- **StateProjector** — proprioceptive state → 2 tokens (LN → MLP 256 → 2×hidden + learned pos).
- **ACTActionDecoder** — TransformerDecoder with learned action queries (chunk_size), norm_first, tanh output. L1 loss.
- **VisionProjector** — LN → MLP(in→1536→out) + skip → LN.

**Config landmarks** (RoboTwin `config.yaml`): hidden_size 1024, action_horizon 50 (LIBERO chunk 12), action_dim 14 (LIBERO 7), state_dim 14, 3 views × 224, act_num_layers 3, act_nheads 8, diffusion_model_cfg cross_attention_dim 256 (diffusion variant exists but released action_model_type is `act`), lr 5e-5 all modules, EMA 0.999, DeepSpeed ZeRO-2, pyav video, lerobot dataloader.

## Training recipe

- **LIBERO:** mixed-suite (all 4 suites, no-noop trajectories), full DINOv3 ViT-B unfreeze, global batch 256 on 4 GPUs, 80k steps, 10k warmup, lr 5e-5, seed 42, FP32 policy + BF16 autocast for DINOv3. Reference env: torch 2.3.1, torchvision 0.18.1, transformers 4.56, TF 2.20, tfds 4.9.3.
- **RoboTwin 2.0:** RoboTwin-Clean 50 tasks, abs action mode, per-device batch 48, max 100k steps, save every 5k, EMA eval.

## Checkpoints (HF repo, 14 files ≈ 2.6 GB)

- `checkpoints/libero/{object,goal,spatial,long}.pth` — 426.5 MB each, PyTorch state-dict-only (no optimizer), suite-specific eval checkpoints
- `checkpoints/robotwin/steps_55000_ema_model.safetensors` — 868 MB, EMA
- `config.json` — `model_type: turbovla`, arch `GroundingDINOVLA`/`Grounding_DINO_DiT`, benchmarks LIBERO + RoboTwin 2.0
- `config.yaml`, `dataset_statistics.json`, `libero_all4_stats.json`, `CHECKSUMS.sha256`, `DINOv3_LICENSE.md`

## Pitfalls

- **License split:** code Apache-2.0; **checkpoints carry DINOv3 terms** (`license: other` / `license_name: dinov3-license` — a separate LICENSE file in-repo, not the standard `license:` value). Always flag this for robotics weights — encoder-derived parameters propagate third-party terms.
- **Not `transformers.AutoModel`-loadable** — custom PyTorch VLA; use official GitHub loader (`pip install -e ".[libero]"`, evaluate.py).
- **DINOv3 + GroundingDINO weights not bundled** — need `--allow_hf_download` and network at first run.
- **Demo data not redistributed** — LIBERO no-noop trajectories regenerated via `scripts/libero/regenerate_libero_no_noops.py` from official LIBERO.
- **0.2B params is the LIBERO config** (ViT-B). RoboTwin uses ViT-L — larger but still far below LLM-centric VLAs.

## How to use this skill

- Loading a TurboVLA checkpoint or replicating LIBERO/RoboTwin evals → follow repo layout + training recipe above.
- Comparing VLA architectures → use the `V+L→A` vs `V→L→A` framing; cite 0.2B/97.7%/31.2 ms/0.9 GB as the edge baseline.
- Scanning HF robotics repos → check `pipeline_tag: robotics`, `dinov3` tag, `libero`/`robotwin` tags, `dataset:StarVLA/RoboTwin-Clean`.

## Verification provenance

- HF model API + tree endpoint verified 2026-07-31 (14 siblings, sizes as above).
- GitHub API verified 2026-07-31 (117★, 11 forks, pushed 2026-07-31).
- Source code read: `turbovla/models/turbovla.py` (438 lines), `components/fusion.py` (BiAttentionBlock), `config.yaml`, README.
- arXiv abstract via export API (200 OK) + daily_papers API (122 upvotes).
- Full write-up: `~/profiles/sakthai/cron/findings/hf-findings-2026-07-31-turbovla.md`
