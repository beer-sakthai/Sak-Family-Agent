---
name: SakThai-hf-nanotron
version: 1.0.0
description: Complete reference on Hugging Face Nanotron — the minimalist 3D-parallelism
  distributed training framework for pre-training transformer models at scale, used
  by Cosmo-1B and SmolLM.
category: mlops
tags:
- hf
- huggingface
- nanotron
---

# HF Nanotron — Minimalistic 3D-Parallelism LLM Training

Trigger when: user asks about pre-training LLMs from scratch, distributed training at scale, 3D parallelism (DP+TP+PP), Hugging Face's training framework for large models, Nanotron, the Ultrascale Playbook, or how Cosmo-1B / SmolLM were trained.

## Overview

Nanotron is Hugging Face's **minimalistic, high-performance library for pre-training transformer models**. It implements 3D parallelism (Data Parallelism + Tensor Parallelism + Pipeline Parallelism) to train models across hundreds of GPUs efficiently.

| Attribute | Value |
|-----------|-------|
| **Repository** | https://github.com/huggingface/nanotron |
| **PyPI** | `pip install nanotron` |
| **Version** | 0.4 (latest, as of Jul 2026) |
| **License** | Apache-2.0 |
| **Python** | ~=3.10 |
| **Stars** | 2.8k |
| **Commits** | 1,269 |
| **Used By** | Cosmo-1B, SmolLM family (135M/360M/1.7B) |

**Core design principles:**
- **Simplicity**: Provides a simple, flexible API to pretrain models on custom datasets
- **Performance**: Uses the latest techniques (3D parallelism, async TP, 1F1B scheduling) for speed and scalability
- **Minimalism**: Clean codebase; ~20 core source files in `src/nanotron/`

## Architecture Overview

Nanotron's training pipeline:

```
Data Pipeline                        Training Loop
┌─────────────────────┐             ┌──────────────────────────┐
│ Datatrove Tokenizer │  ──────►   │ Nanoset (Dataset)        │
│ (tools/preprocess)  │             │  • Weighted mixing       │
└─────────────────────┘             │  • Epoch-based sampling  │
                                    │  • Shuffled indices      │
                                    └──────────┬───────────────┘
                                               │
                                    ┌──────────▼───────────────┐
                                    │ DataLoader + Sampler     │
                                    │  • Sequential/Random/Cyclic│
                                    │  • DP sharding           │
                                    └──────────┬───────────────┘
                                               │
                                    ┌──────────▼───────────────┐
                                    │ Trainer (run_train.py)   │
                                    │  • 3D parallelism engine │
                                    │  • FP32 grad accumulation│
                                    │  • Checkpoint & resume   │
                                    │  • Kill switch           │
                                    └──────────────────────────┘
```

## 3D Parallelism (DP + TP + PP)

The core of Nanotron: three complementary parallelism strategies that work together.

### 1. Data Parallelism (DP)

Replicates the entire model across GPUs, each processing different microbatches. Gradients are synchronized via all-reduce.

**Key points:**
- DP = total GPUs / (TP × PP)
- Each replica gets a shard of the dataset
- ZeRO-1 optimizer support (sharded optimizer states across DP ranks)
- Parameter tying/replicated parameters synced via all-reduce

### 2. Tensor Parallelism (TP)

Splits individual weight matrices across GPUs. Two modes:

| Mode | Description | Communication |
|------|-------------|---------------|
| **ALL_REDUCE** (regular) | Each rank computes its portion, then gathers partial outputs | More communication |
| **REDUCE_SCATTER** (async) | Each rank gathers ALL input shards and computes the full output locally | Less communication, more FLOPs |

**Asynchronous TP** is a key innovation: each rank kicks off an async all-gather of the input tensor at the start, computes its local portion while waiting, then completes the remaining computation when the gather finishes. This **trades more FLOPs for less communication** — ideal for communication-bound models.

**Tied linear layers** (e.g., embedding → LM head weight tying) are replicated across all ranks, not sharded. Only one rank saves tied weights to avoid checkpoint redundancy.

### 3. Pipeline Parallelism (PP)

Splits the model into sequential stages, each assigned to different GPUs.

**Core components:**
| Component | Role |
|-----------|------|
| **PipelineBlock** | Contains model computation split over devices |
| **PipelineEngine** | Orchestrates forward/backward passes across blocks |
| **PipelineBatchState** | Manages all P2P operations between stages |
| **TensorPointer** | Lazy tensor reference — a pointer to a tensor on another device |

**Scheduling strategies:**
- **1F1B** (One-Forward-One-Backward): Interleaves forward and backward passes for optimal memory usage (default)
- **AFAB** (All-Forward-All-Backward): All forwards first, then all backwards (simpler, more memory)

**Key innovation — TensorPointer:** Rather than immediately sending activations between pipeline stages, TensorPointers provide lazy communication. Tensors are only transferred when needed, and communications are batched across microbatches for efficiency.

### Putting It Together

```
Example: 8 GPUs, DP=2, PP=2, TP=2

GPU 0: DP=0, PP=0, TP=0   │   GPU 1: DP=0, PP=0, TP=1
GPU 2: DP=0, PP=1, TP=0   │   GPU 3: DP=0, PP=1, TP=1
GPU 4: DP=1, PP=0, TP=0   │   GPU 5: DP=1, PP=0, TP=1
GPU 6: DP=1, PP=1, TP=0   │   GPU 7: DP=1, PP=1, TP=1

DP=0: GPUs 0-3 (one model replica)
DP=1: GPUs 4-7 (second model replica)
PP=0: GPUs 0-1, 4-5 (first half of model)
PP=1: GPUs 2-3, 6-7 (second half of model)
TP: Within each PP stage, weights are split across 2 GPUs
```

## Configuration System

Training is configured via YAML files generated from Python scripts. The `nanotron.config` module provides typed dataclasses:

```python
from nanotron.config import (
    Config, GeneralArgs, CheckpointsArgs, ParallelismArgs,
    ModelArgs, TokenizerArgs, OptimizerArgs, LRSchedulerArgs,
    AdamWOptimizerArgs, DataArgs, DatasetStageArgs,
    LlamaConfig, RandomInit, TokensArgs, LoggingArgs,
)

config = Config(
    general=GeneralArgs(project="my-project", run="experiment-1", seed=42),
    checkpoints=CheckpointsArgs(checkpoints_path="./checkpoints", checkpoint_interval=1000),
    parallelism=ParallelismArgs(dp=2, pp=2, tp=2, pp_engine="1f1b",
                                tp_mode="REDUCE_SCATTER", tp_linear_async_communication=True),
    model=ModelArgs(init_method=RandomInit(std=0.025),
                    model_config=LlamaConfig(
                        hidden_size=16, intermediate_size=64,
                        num_hidden_layers=2, num_attention_heads=4,
                        num_key_value_heads=4, vocab_size=256,
                        max_position_embeddings=256, ...
                    )),
    tokenizer=TokenizerArgs("path/to/tokenizer"),
    optimizer=OptimizerArgs(
        zero_stage=0, weight_decay=0.01, clip_grad=1.0,
        accumulate_grad_in_fp32=True,
        learning_rate_scheduler=LRSchedulerArgs(
            learning_rate=3e-4, lr_warmup_steps=1000,
            lr_warmup_style="linear", lr_decay_style="cosine",
            min_decay_lr=1e-5
        ),
        optimizer_factory=AdamWOptimizerArgs(adam_eps=1e-8, ...),
    ),
    tokens=TokensArgs(sequence_length=2048, train_steps=10000,
                      micro_batch_size=2, batch_accumulation_per_replica=8),
    data_stages=[
        DatasetStageArgs(
            name="Stable Training",
            start_training_step=1,
            data=DataArgs(
                dataset=PretrainDatasetsArgs(
                    hf_dataset_or_datasets="stas/openwebtext-10k",
                    text_column_name="text"
                ), seed=42
            ),
        ),
    ],
    logging=LoggingArgs(log_level="info"),
)
config.save_as_yaml("config.yaml")
```

**Global batch size formula:**
```
global_batch_size = micro_batch_size × batch_accumulation_per_replica × dp
```

## Data Pipeline — Nanosets

Nanosets are Nanotron's custom dataset format for pre-tokenized training data, built on top of [datatrove](https://github.com/huggingface/datatrove).

### Preprocessing

Raw data is tokenized offline using `tools/preprocess_data.py`:

```bash
# Process a Hugging Face dataset
python3 tools/preprocess_data.py \
    --tokenizer-name-or-path meta-llama/Meta-Llama-3-8B \
    --output-folder datasets/emotion \
    --n-tasks 16 \
    hf --dataset dair-ai/emotion

# Process JSONL files
python3 tools/preprocess_data.py \
    --tokenizer-name-or-path gpt2 \
    --output-folder datasets/my_data \
    --n-tasks 16 \
    jsonl --dataset raw_datasets/my-json-files
```

Output files per worker:
- `*.ds` — tokenized documents
- `*.ds.index` — document boundaries
- `*.ds.metadata` — token counts and tokenizer info

### Dataset Configuration

Three ways to configure datasets in YAML:

**1. Single dataset:**
```yaml
data:
  dataset:
    dataset_folder: datasets/SlimPajama-6B
  num_loading_workers: 0
  seed: 1234
```

**2. Multiple datasets (random mixing):**
```yaml
data:
  dataset:
    dataset_folder:
      - datasets/SlimPajama-6B
      - datasets/testing_alpaca_small
  num_loading_workers: 0
  seed: 1234
```

**3. Weighted blending:**
```yaml
data:
  dataset:
    dataset_folder:
      datasets/SlimPajama-6B: 0.8
      datasets/testing_alpaca_small: 0.2
  num_loading_workers: 0
  seed: 1234
```

### Under the Hood

Nanosets build two internal indices:
- **dataset_index**: Maps each sample position to a source dataset (respecting weights)
- **dataset_sample_index**: Maps each sample position to a specific sample within that dataset

Both indices are shuffled together per epoch, ensuring each sample is consumed exactly once per epoch while following the specified mixture weights.

---

## Deep Dive Reference

For exhaustive reference specifications, cookbook snippets, and extended documentation, see [Nanotron 3D Training, Nanosets & Optimization](./references/nanotron-training-and-nanosets.md).
