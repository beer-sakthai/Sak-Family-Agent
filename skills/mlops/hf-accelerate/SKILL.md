---
name: hf-accelerate
author: SakThai
license: MIT
title: HF Accelerate
category: mlops
tags: [accelerate, distributed-training, mixed-precision, fsdp, deepspeed]
related_skills:
  - huggingface-hub
  - hf-transformers-5
  - hf-peft-lora
description: Covers Hugging Face Accelerate library — distributed training engine with Accelerator, mixed precision, and composable parallelism.
version: 1.0.0
---

## Description
Covers Hugging Face Accelerate library (v1.14.0+) — the zero-boilerplate distributed training engine. Includes the Accelerator class, mixed precision (FP16/BF16/FP8), GradScaler, DeepSpeed/FSDP integration, and the new Composable Parallelism system (`ParallelismConfig`) for 2D/3D/4D parallel training with FSDP2 + Tensor/Context/Sequence Parallelism. Focused on patterns that work under zero-cost constraints.

## Key Resources
- [Accelerate docs](https://huggingface.co/docs/accelerate/en/index)
- [ParallelismConfig API](https://huggingface.co/docs/accelerate/en/package_reference/accelerator#accelerate.utils.ParallelismConfig)
- [FSDP2 docs](https://pytorch.org/docs/stable/distributed.fsdp.html)
- [torchtitan ParallelDims](https://github.com/pytorch/torchtitan/blob/main/torchtitan/distributed/parallel_dims.py)
- [Accelerate GitHub](https://github.com/huggingface/accelerate)

## Topics Covered
- `ParallelismConfig`: dp_replicate_size, dp_shard_size, tp_size, cp_size, sp_size
- Composable parallelism: 2D (FSDP+TP), 3D (HSDP+TP/CP), 4D (all dimensions)
- TorchTensorParallelConfig: async TP support
- TorchContextParallelConfig: allgather/alltoall comm strategies
- DeepSpeedSequenceParallelConfig: Ulysses/ALSD attention
- Device mesh construction: init_device_mesh with mesh_dim_names
- Environment variable configuration (PARALLELISM_CONFIG_*)
- FSDP2: native composable sharding without policy objects
