---
name: SakThai-hf-accelerate
description: "Comprehensive deep-dive on Hugging Face Accelerate (v1.14.0) \u2014 the Accelerator\
  \ class, distributed training, mixed precision, big model inference, FSDP, DeepSpeed,\
  \ FP8 training, CLI, and production patterns."
---

# HF Accelerate Deep Dive

Complete reference for Hugging Face Accelerate v1.14.0 — the unified API for distributed training and inference.

## Core Concepts

- **Accelerator class** — main entry point; manages device placement, mixed precision, gradient accumulation, distributed state
- **`accelerate launch`** — CLI launcher for multi-process/multi-GPU/multi-node scripts
- **`accelerate config`** — interactive or default configuration generation
- **Big Model Inference** — `init_empty_weights`, `load_checkpoint_and_dispatch`, device maps, CPU/disk offload
- **FSDP Integration** — fully sharded data parallelism via PyTorch FSDP
- **DeepSpeed Integration** — ZeRO stages, optimizer/parameter offload, NVMe
- **Mixed Precision** — fp16, bf16, fp8 (TransformersEngine, MS-AMP legacy, torchao)
- **Experiment Tracking** — TensorBoard, WandB, MLflow, Comet, Aim, DVCLive, SwanLab
- **Gradient Accumulation** — `accumulate()` context manager
- **Memory Estimation** — `accelerate estimate-memory` CLI

## References

- `~/profiles/sakthai/skills/mlops/hf-accelerate/references/hf-learnings.md` — complete deep-dive reference
- Official docs: https://huggingface.co/docs/accelerate
- Source: https://github.com/huggingface/accelerate
