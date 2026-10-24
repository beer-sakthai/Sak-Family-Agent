---
title: SakThai Training Space
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# SakThai Training Space

GPU-backed Docker Space for reinforcement-learning / post-training of Sak family agents.

Pre-installed stack:
- PyTorch 2.5.1 (CUDA 12.4)
- Transformers, Datasets, Accelerate, PEFT
- DeepSpeed 0.15.4
- TRL 0.15.x with `trl[deepspeed]`
- Optional: vLLM, Weights & Biases, TensorBoard

## How to use

1. Set secrets/variables in the Space settings:
   - `HF_TOKEN` (secret) — for pushing/pulling models and datasets
   - `WANDB_API_KEY` (secret) — optional experiment tracking
   - `SAKTHAI_TRAIN_SCRIPT` (variable) — e.g. `scripts/grpo.py`
   - `SAKTHAI_TRAIN_ARGS` (variable) — optional extra CLI args

2. Rebuild/restart the Space; training starts automatically if `SAKTHAI_TRAIN_SCRIPT` is set.

3. Alternatively, enable **Dev Mode** or use **HF Jobs** to run training manually inside the container.

## Directories

- `/workspace/scripts` — training scripts
- `/workspace/configs` — deepspeed / accelerate configs
- `/workspace/outputs` — local checkpoints (ephemeral; push to Hub)
- `/workspace/data` — datasets (ephemeral; stream from Hub when possible)
