---
name: hf-trl
description: "Hugging Face TRL (Transformer Reinforcement Learning): post-training library for LLMs — trainer taxonomy (SFT, GRPO, DPO, PPO, KTO, ORPO, etc.), vLLM/PEFT/DeepSpeed integrations, Harbor/OpenEnv agent training, and installation/usage patterns."
version: 1.0.0
author: SakThai
license: MIT
tags: [huggingface, trl, rlhf, dpo, grpo, sft, peft, vllm, post-training, alignment]
platforms: [linux, macos, windows]
---

# Hugging Face TRL — Post-Training Library

TRL is the Hugging Face library for post-training transformer language models. It provides a unified set of trainers for Supervised Fine-Tuning (SFT), preference alignment, reinforcement learning (RLHF/GRPO/RLOO), reward modeling, and knowledge distillation.

## Quick Install

```bash
# Stable release via PyPI (e.g. v1.6.0)
pip install trl

# Main branch (requires source install)
git clone https://github.com/huggingface/trl.git
cd trl
pip install -e .
# or development install
pip install -e ".[dev]"
```

Requires Python >= 3.10 and PyTorch >= 2.4.

## Trainer Taxonomy

### Online methods (RL / RLHF)
- `GRPOTrainer` ⚡️ — Group Relative Policy Optimization; supports `vLLM` and `Harbor` sandboxed environments via `environment_factory`.
- `RLOOTrainer` ⚡️ — Reward-based Leave-One-Out.
- `OnlineDPOTrainer` 🧪 ⚡️ — Online Direct Preference Optimization.
- `NashMDTrainer` 🧪 ⚡️ — Nash-Mean Dynamics.
- `PPOTrainer` 🧪 — Proximal Policy Optimization (classic RLHF).
- `XPOTrainer` 🧪 ⚡️ — Expert-based Policy Optimization.

### Reward modeling
- `RewardTrainer` — train a scalar reward model from pairwise preference data.
- `PRMTrainer` 🧪 — Process Reward Modeling.

### Offline methods
- `SFTTrainer` — Supervised Fine-Tuning; the standard supervised baseline.
- `DPOTrainer` — Direct Preference Optimization (no reward model needed).
- `BCOTrainer` 🧪 — Behavioral Cloning from Observation.
- `CPOTrainer` 🧪 — Conservative Preference Optimization.
- `KTOTrainer` 🧪 — Kahneman-Tversky Optimization.
- `ORPOTrainer` 🧪 — Odds Ratio Preference Optimization.

### Knowledge distillation
- `GKDTrainer` 🧪 — Generalized Knowledge Distillation.
- `MiniLLMTrainer` 🧪 — Distillation into smaller models.

⚡️ = vLLM acceleration supported  
🧪 = experimental / API may change

## Integrations

TRL is tightly integrated with the HF ecosystem:
- **transformers** — models and tokenizers are passed directly.
- **PEFT** — LoRA / QLoRA / adapters via `peft` configs.
- **Accelerate** — distributed training (`accelerate launch`).
- **DeepSpeed** — ZeRO stages, CPU/disk offloading.
- **vLLM** — high-throughput inference in online trainers (colocate vLLM with training for efficiency).
- **Unsloth** — memory-efficient fine-tuning.
- **Liger Kernel** — Triton kernels for faster attention.
- **Trackio / W&B** — experiment tracking via callbacks.

## Streaming / vLLM Colocation Patterns

A common optimization is **vLLM colocation**: run a vLLM engine in the same worker process as the trainer to avoid inter-process communication overhead. A June 2025 blog post demonstrated significant throughput gains with `GRPOTrainer`.

```python
from trl import GRPOTrainer, GRPOConfig

trainer = GRPOTrainer(
    model=model,
    reward_funcs=[reward],
    train_dataset=dataset,
    args=GRPOConfig(),
)
```

> **Note:** vLLM colocation requires compatible CUDA/cuDNN versions and PyTorch 2.8.0+ for ahead-of-time compilation in some configurations.

## Agent Training via Harbor / OpenEnv

`GRPOTrainer` supports an `environment_factory` that lets you train agents against sandboxed task suites:
- Instruction + sandbox image + in-sandbox verifier.
- Built on the **OpenEnv** ecosystem (announced Oct 2025).
- Reward is computed inside the sandbox; the policy is updated with standard GRPO.

This makes TRL usable for tool-use, code-generation, and embodied-agent post-training, not just pure language modeling.

## Practical Tips

1. **Start with SFT** — `SFTTrainer` is the most stable and well-documented baseline.
2. **Prefer DPO over PPO for simple preferences** — DPO avoids explicit reward model training and is much simpler to debug.
3. **Use vLLM with GRPO/RLOO** — online methods benefit the most from batched inference.
4. **PEFT is practically required for 7B+ models on consumer GPUs** — combine `SFTTrainer`/`DPOTrainer` with LoRA.
5. **Track runs** — integrations with `Trackio` and `W&B` help reproduce experiments.

## Versioning Context

- **TRL v1** (released March 27, 2026) marked a major API stabilization and feature shift.
- The latest stable pip release at time of research is **v1.6.0**.
- The `main` branch on GitHub is ahead of PyPI and requires source installation.

## References

- Docs: https://huggingface.co/docs/trl/main/en/index
- GitHub: https://github.com/huggingface/trl
- Blog (TRL v1): https://huggingface.co/blog/trl-v1
- OpenEnv: https://huggingface.co/blog/openenv

## Session Research Notes

See `references/research-notes.md` for the raw TRL trainer taxonomy extracted from the official docs index page, installation commands, and the research fallback pattern used when managed web tools hit billing/timeouts.
