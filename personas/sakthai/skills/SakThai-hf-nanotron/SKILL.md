---
name: SakThai-hf-nanotron
description: "Complete reference on Hugging Face Nanotron — the minimalist 3D-parallelism distributed training framework for pre-training transformer models at scale, used by Cosmo-1B and SmolLM."
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

## Training

### Single Node (8×H100)

```bash
CUDA_DEVICE_MAX_CONNECTIONS=1 torchrun --nproc_per_node=8 run_train.py \
    --config-file examples/config_tiny_llama.yaml
```

A tiny Llama model trains in ~10 minutes on 8×H100s.

### Multi-Node (via Slurm)

Nanotron provides `slurm_launcher.py` for Slurm-managed clusters:

```bash
python slurm_launcher.py \
    --run_name production_run \
    --nodes 8 \
    --model_size base \
    --dp 4 --pp 2 --tp 2 \
    --train_steps 50000 \
    --learning_rate 2e-4 \
    --warmup_steps 2000 \
    --dataset my_dataset \
    --tokenizer my_tokenizer \
    --email researcher@example.com \
    --time_limit 72:00:00
```

Key parallelism parameters: `--dp`, `--pp`, `--tp`. Ensure `DP × PP × TP ≤ total GPUs`.

**Manual multi-node setup** uses `torchrun` with `--nnodes`, `--rdzv_backend c10d`, and `--rdzv_endpoint` across nodes.

### Generation from Checkpoint

```bash
torchrun --nproc_per_node=1 run_generate.py \
    --ckpt-path checkpoints/{checkpoint_number}/ \
    --tp 1 --pp 1
```

Increase `--tp` for faster generation on multiple GPUs.

## Trainer Internals

### Model Initialization

1. Create model instance
2. Initialize parameters randomly via context manager that overrides `nn.Module.register_parameter()` to init directly on target device/dtype
3. Mark tied parameters via `model.tie_parameters()`
4. Sync weights across DP ranks via all-reduce (ensures all replicas start identical)
5. Sync tied parameters within each replica via second all-reduce

**Why the custom init context manager?** Instead of `module.to(device)` which initializes on CPU then moves, Nanotron initializes directly on GPU at target precision — saving memory and startup time.

### The Kill Switch

A file-based graceful shutdown mechanism:
1. Trainer periodically checks for a kill switch file
2. If detected, saves a checkpoint then exits cleanly
3. Prevents corrupted checkpoints from Ctrl-C or job cancellation

### Checkpoint Format

Saves all of: model weights, optimizer state, LR scheduler state, RNG state, and shard-mapping metadata.

**Handling different parameter types:**
- **Regular params**: Save full tensor normally
- **Sharded params**: Only save the shard owned by the first model replica (no DP redundancy)
- **Tied params**: Only one rank in the tied group saves the weight

**Loading restores** sharded weights using slice-mapping metadata to reconstruct the full original tensor.

### Data Loading in 3D

The `MegatronPretrainingSampler` divides the dataset into equal chunks across DP ranks, then samples sequentially or randomly within each chunk. Sequential walks through the shard; random shuffles each epoch; cyclic loops back to the start after one pass.

## Features (Current + Roadmap)

### ✅ Implemented
- 3D parallelism (DP + TP + PP) with explicit APIs for easy debugging
- Expert parallelism for MoEs
- AFAB and 1F1B schedules for PP
- ZeRO-1 optimizer (sharded optimizer states)
- FP32 gradient accumulation
- Async Tensor Parallelism (REDUCE_SCATTER mode)
- Parameter tying/sharding
- Custom module checkpointing for large models
- Spectral µTransfer parametrization (μP) for scaling up networks
- Mamba architecture example
- CUDA event-based timing for accurate GPU performance measurement
- Checkpoint-and-resume with kill switch
- Custom dataloaders (user-supplied datasets)
- S3 checkpoint upload
- DoReMi (Data Models) for optimizing data mixing weights during training
- Nanoset weighted data blending
- UltraScale Playbook (benchmarking best practices)

### 🗺️ Roadmap
- FP8 training (partial support present in `src/nanotron/fp8/`)
- ZeRO-3 / FSDP
- `torch.compile` support
- Ring attention
- Interleaved 1F1B schedule

## Supported Model Architectures

| Model | File | Config |
|-------|------|--------|
| **LLaMA** | `src/nanotron/models/llama.py` | `LlamaConfig` |
| **Qwen** | `src/nanotron/models/qwen.py` | — |
| **StarCoder2** | `src/nanotron/models/starcoder2.py` | — |
| **Mamba** | `examples/mamba/` | Example only |
| **MoE** | `examples/moe/` | Example only |

## UltraScale Playbook

The [Ultrascale Playbook](https://huggingface.co/spaces/nanotron/ultrascale-playbook) is a comprehensive guide to scaling LLM training with Nanotron. It contains:

- **Benchmark data**: Extensive benchmarks across model sizes and configurations at `hf.co/datasets/nanotron/ultrascale-playbook-data`
- **Best configurations**: Optimal MFU (Model FLOPS Utilization) and memory usage for each model size and node count
- **Scaling guidance**:
  - <1B params: Focus on DP
  - 1-10B params: TP=2, PP=1 or PP=2
  - >10B params: Increase both TP and PP
  - Use async TP (`REDUCE_SCATTER` + `tp_linear_async_communication=True`) for communication-bound models

## Nanotron vs Alternatives

| Feature | Nanotron | Megatron-LM | DeepSpeed | FSDP (native PyTorch) |
|---------|----------|-------------|-----------|----------------------|
| **3D Parallelism** | ✅ Native | ✅ Native | ⚠️ Partial | ❌ TP not native |
| **Async TP** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **API complexity** | Low | High | Medium | Low |
| **HF Integration** | ✅ Native | ❌ Separate | ⚠️ Via HF | ✅ Native |
| **ZeRO stages** | Stage 1 only | Stage 1+2 | 1+2+3 | 1+2+3 (FSDP) |
| **FP8** | ⚠️ Partial (in-tree) | ✅ Yes | ❌ | ❌ |
| **MoE support** | ✅ Yes (expert parallelism) | ✅ Yes | ✅ Yes | ❌ |
| **Checkpoint format** | Custom (shard-aware) | Megatron format | DeepSpeed format | Standard torch |
| **Kill switch** | ✅ Yes | ❌ | ❌ | ❌ |
| **μP transfer** | ✅ Yes | ❌ | ❌ | ❌ |

## Pitfalls

- **Python 3.10–3.11 only**: PyPI lists `~=3.10`. May not work with 3.12+.
- **CUDA required**: Nanotron requires CUDA-enabled GPUs and CUDA toolkit. No CPU-only training.
- **uv recommended**: Install with `uv pip install nanotron` for faster dependency resolution. On HF cluster, set `UV_LINK_MODE=copy`.
- **Token size mismatch**: Ensure tokenized data doesn't exceed model's `vocab_size` — common source of cryptic errors.
- **Parallelism product check**: `DP × PP × TP` must not exceed total GPUs. Uneven splits waste resources.
- **Checkpoint path**: Set `checkpoints_path` to a writable location with sufficient storage — checkpoints for large models can be many GB.
- **Kill switch file**: Create a file at a known path to trigger graceful shutdown. Path is configurable.
- **dataset.index vs dataset_folder**: Always use `dataset_folder` (plural) in YAML config for Nanosets, not `dataset_path` or similar.
- **slurm_launcher.py expectation**: The launcher script is at the repo root (`slurm_launcher.py`), not under `src/`. Run it from the cloned repo or installed package's examples directory.
- **NCCL settings**: For multi-node, ensure `NCCL_DEBUG=WARN` or similar is set for debugging. `CUDA_DEVICE_MAX_CONNECTIONS=1` is essential for some distributed operations.
- **HF Hub login required**: Both `huggingface-cli login` and `wandb login` are needed before training for checkpoint pushing and logging.
- **No FSDP/ZeRO-3 yet**: Nanotron only supports ZeRO-1. For full-sharding, consider FSDP (PyTorch native) or DeepSpeed ZeRO-3.
- **SFT training**: Nanotron has basic SFT support in `src/nanotron/data/sft_processing.py` but the primary focus is pre-training, not fine-tuning.

## Key Repositories

| Component | URL |
|-----------|-----|
| Nanotron code | https://github.com/huggingface/nanotron |
| PyPI package | `pip install nanotron` (+ `[nanosets]` for data preprocessing support) |
| Ultrascale Playbook | https://huggingface.co/spaces/nanotron/ultrascale-playbook |
| Benchmark data | https://huggingface.co/datasets/nanotron/ultrascale-playbook-data |
| llm-swarm (generation) | https://github.com/huggingface/llm-swarm |
| datatrove (preprocessing) | https://github.com/huggingface/datatrove |

## Getting Started

```bash
# 1. Create environment
uv venv nanotron --python 3.11 && source nanotron/bin/activate
uv pip install torch --index-url https://download.pytorch.org/whl/cu124
uv pip install nanotron

# 2. Generate config and train
git clone https://github.com/huggingface/nanotron
cd nanotron
python examples/config_tiny_llama.py  # Generates YAML config
CUDA_DEVICE_MAX_CONNECTIONS=1 torchrun --nproc_per_node=8 run_train.py \
    --config-file examples/config_tiny_llama.yaml

# 3. Generate text from checkpoint
torchrun --nproc_per_node=1 run_generate.py \
    --ckpt-path checkpoints/10/ --tp 1 --pp 1
```
