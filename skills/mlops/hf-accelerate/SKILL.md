---
name: hf-accelerate
author: SakThai
license: MIT
title: Hugging Face Accelerate
description: Accelerate enables the same PyTorch code to run across any distributed configuration with minimal code changes. Covers the Accelerator class, device placement, mixed precision, gradient accumulation, DeepSpeed integration, FSDP, launching, saving/loading, and experiment tracking.
version: 1.0.0
tags:
  - huggingface
  - accelerate
  - distributed-training
  - pytorch
  - deepspeed
  - fsdp
  - mixed-precision
---

# Hugging Face Accelerate

The [Accelerate](https://huggingface.co/docs/accelerate/index) library lets you run the same PyTorch code on any distributed configuration by adding **just 4 lines of code**. It handles device placement, mixed precision, gradient accumulation, DeepSpeed/FSDP integration, and multi-GPU/TPU training transparently.

For a condensed API reference (all constructor parameters, CLI config options, properties table, and before/after migration table), see `references/api-docs.md` in this skill directory.

## Installation

```bash
pip install accelerate
# or with uv
uv pip install accelerate
```

For DeepSpeed support (optional):
```bash
pip install deepspeed
```

## Quick Start — Minimal Migration

### Before (standard PyTorch)

```python
device = "cuda"
model.to(device)

for batch in training_dataloader:
    optimizer.zero_grad()
    inputs, targets = batch
    inputs = inputs.to(device)
    targets = targets.to(device)
    outputs = model(inputs)
    loss = loss_function(outputs, targets)
    loss.backward()
    optimizer.step()
    scheduler.step()
```

### After (with Accelerate)

```python
from accelerate import Accelerator

accelerator = Accelerator()
device = accelerator.device

model, optimizer, training_dataloader, scheduler = accelerator.prepare(
    model, optimizer, training_dataloader, scheduler
)

for batch in training_dataloader:
    optimizer.zero_grad()
    inputs, targets = batch       # dataloader auto-places on device
    outputs = model(inputs)
    loss = loss_function(outputs, targets)
    accelerator.backward(loss)    # handles gradient scaling
    optimizer.step()
    scheduler.step()
```

### Launch

```bash
# Single GPU
accelerate launch train.py

# Multi-GPU (uses config)
accelerate config   # interactive setup, then:
accelerate launch train.py
```

## Core API

### Accelerator() Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `device_placement` | `bool` | `True` | Auto-place objects on correct device |
| `mixed_precision` | `str` | env var | `'no'`, `'fp16'`, `'bf16'`, or `'fp8'` |
| `gradient_accumulation_steps` | `int` | `1` | Steps before gradient update |
| `cpu` | `bool` | `False` | Force CPU execution |
| `deepspeed_plugin` | `DeepSpeedPlugin` | — | DeepSpeed configuration |
| `fsdp_plugin` | `FullyShardedDataParallelPlugin` | — | FSDP configuration |
| `log_with` | list[str] | — | Loggers: `'tensorboard'`, `'wandb'`, `'mlflow'`, etc. |
| `project_dir` | str/Path | — | Directory for logs/checkpoints |
| `dynamo_backend` | str | `'no'` | TorchDynamo backend for graph compilation |
| `rng_types` | list[str] | — | RNG types to sync: `'torch'`, `'cuda'`, `'generator'` |
| `step_scheduler_with_optimizer` | bool | `True` | Step scheduler with optimizer or manually |
| `kwargs_handlers` | list[KwargsHandler] | — | Custom handlers for distributed objects |

### Key Methods

**`accelerator.prepare(model, optimizer, dataloader, scheduler, ...)`**
Wraps each object for distributed training. Returns objects in same order. Only prepares objects that inherit from PyTorch base classes.

**`accelerator.backward(loss)`**
Replaces `loss.backward()`. Handles gradient scaling for mixed precision and gradient accumulation.

**`accelerator.accumulate(model)`** (context manager)
Wraps gradient accumulation logic. Use inside training loop with `gradient_accumulation_steps > 1`.

```python
for batch in dataloader:
    with accelerator.accumulate(model):
        outputs = model(batch)
        loss = loss_fn(outputs, labels)
        accelerator.backward(loss)
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()
```

**`accelerator.autocast()`** (context manager)
Context for automatic mixed precision. Only needed for computation outside model forward pass.

```python
with accelerator.autocast():
    loss = complex_loss_function(outputs, target)
```

**`accelerator.clip_grad_norm_(parameters, max_norm)`**
Replaces `torch.nn.utils.clip_grad_norm_`. Should be gated with `accelerator.sync_gradients` check.

**`accelerator.clip_grad_value_(parameters, clip_value)`**
Replaces `torch.nn.utils.clip_grad_value_`.

**`accelerator.gather(tensor)`**
Gathers tensors across all processes (useful for evaluation metrics). Works on all processes.

**`accelerator.unwrap_model(model)`**
Returns the original unwrapped model (for saving/checkpointing).

**`accelerator.save_state(output_dir)`**
Saves model, optimizer, scheduler, and RNG states for resuming training.

**`accelerator.load_state(input_dir)`**
Loads a previously saved state.

**`accelerator.get_state_dict(model)`**
Gets state dict with proper FSDP/DeepSpeed handling. Use when calling `save_pretrained`.

**`accelerator.free_memory(*objects)` / `accelerator.clear(*objects)`**
Releases references and calls GC. Use between different training runs.

**`accelerator.end_training()`**
Cleanup — stops trackers, destroys process group.

**`accelerator.set_trigger()` / `accelerator.check_trigger()`**
Cross-process signaling mechanism (e.g., for early stopping).

### Useful Properties

| Property | Type | Description |
|----------|------|-------------|
| `accelerator.device` | `torch.device` | Current device |
| `accelerator.process_index` | `int` | Global process index |
| `accelerator.local_process_index` | `int` | Local (per-machine) process index |
| `accelerator.num_processes` | `int` | Total process count |
| `accelerator.is_main_process` | `bool` | Is this process the main one? |
| `accelerator.is_local_main_process` | `bool` | Main on this machine? |
| `accelerator.distributed_type` | `DistributedType` | `NO`, `MULTI_GPU`, `DEEPSPEED`, `FSDP`, `TPU` |
| `accelerator.mixed_precision` | `str` | Current mixed precision mode |
| `accelerator.sync_gradients` | `bool` | Are gradients being synced now? |
| `accelerator.optimizer_step_was_skipped` | `bool` | Was optimizer step skipped? |
| `accelerator.use_distributed` | `bool` | Is this a distributed setup? |
| `accelerator.state` | `AcceleratorState` | Full distributed state |

## Mixed Precision

Three modes: `'fp16'`, `'bf16'`, `'fp8'` (fp8 needs transformers-engine).

```python
accelerator = Accelerator(mixed_precision="bf16")
```

For best performance, compute loss inside the model (like HF Transformers) — computations outside model use full precision.

## Gradient Accumulation

```python
accelerator = Accelerator(gradient_accumulation_steps=4)

for batch in dataloader:
    with accelerator.accumulate(model):
        outputs = model(batch)
        loss = loss_fn(outputs, labels)
        accelerator.backward(loss)
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()
```

The `accumulate` context manager automatically skips gradient syncing until the accumulation boundary is reached.

## DeepSpeed Integration

Two approaches:

### 1. Plugin (simpler, fewer options)

```bash
accelerate config  # Answer "no" to DeepSpeed config file
```

Supports via config:
- `zero_stage`: 0 (disabled), 1 (optimizer states), 2 (+gradients), 3 (+parameters)
- `offload_optimizer_device`: `'none'`, `'cpu'`, `'nvme'`
- `offload_param_device`: `'none'`, `'cpu'`, `'nvme'`
- `gradient_clipping`: enable with value
- `zero3_init_flag`: use `deepspeed.zero.Init` for large models
- `zero3_save_16bit_model`: save 16-bit weights

### 2. DeepSpeed Config File (full control)

```bash
accelerate config  # Answer "yes" then provide path to ds_config.json
```

Example config:
```json
{
  "fp16": {"enabled": true, "auto_cast": true, "loss_scale": 0, "initial_scale_power": 16},
  "gradient_accumulation_steps": 1,
  "gradient_clipping": 1.0,
  "zero_optimization": {
    "stage": 2,
    "allgather_partitions": true,
    "allgather_bucket_size": 2e8,
    "overlap_comm": true,
    "reduce_bucket_size": 2e8,
    "reduce_scatter": true
  }
}
```

```python
from accelerate import DeepSpeedPlugin

deepspeed_plugin = DeepSpeedPlugin(zero_stage=2, gradient_clipping=1.0)
accelerator = Accelerator(deepspeed_plugin=deepspeed_plugin)
```

### DeepSpeed ZeRO Stages

| Stage | Shards | Memory Savings | Use Case |
|-------|--------|----------------|----------|
| 1 | Optimizer states | ~4× | Large optimizers |
| 2 | + Gradients | ~8× | Most common for training |
| 3 | + Parameters | Memory = total / num_gpus | Very large models |
| 3 + Offload | + CPU/NVMe | Almost unlimited | Single GPU large models |

## FSDP (Fully Sharded Data Parallel)

### Plugin Approach (via `accelerate config`)

Config options:
- `fsdp_sharding_strategy`: `FULL_SHARD` (1), `SHARD_GRAD_OP` (2), `NO_SHARD` (3), `HYBRID_SHARD` (4), `HYBRID_SHARD_ZERO2` (5)
- `fsdp_offload_params`: Offload to CPU
- `fsdp_auto_wrap_policy`: `TRANSFORMER_BASED_WRAP`, `SIZE_BASED_WRAP`, `NO_WRAP`
- `fsdp_transformer_layer_cls_to_wrap`: Class names (e.g. `BertLayer,GPTJBlock`)
- `fsdp_backward_prefetch_policy`: `BACKWARD_PRE`, `BACKWARD_POST`, `NO_PREFETCH`
- `fsdp_state_dict_type`: `FULL_STATE_DICT`, `LOCAL_STATE_DICT`, `SHARDED_STATE_DICT` (recommended)
- `fsdp_use_orig_params`: `True` for PEFT/frozen params support
- `fsdp_cpu_ram_efficient_loading`: Only rank 0 loads pretrained weights
- `fsdp_sync_module_states`: Broadcast from rank 0

### Programmatic

```python
from accelerate import FullyShardedDataParallelPlugin

fsdp_plugin = FullyShardedDataParallelPlugin(
    state_dict_config=FullStateDictConfig(offload_to_cpu=False, rank0_only=False),
    optim_state_dict_config=FullOptimStateDictConfig(offload_to_cpu=False, rank0_only=False),
)
accelerator = Accelerator(fsdp_plugin=fsdp_plugin)
```

### Saving/Loading FSDP

```python
# Save (recommended: SHARDED_STATE_DICT)
accelerator.save_state("ckpt")
# Load
accelerator.load_state("ckpt")
# Save for hub/transformers
unwrapped_model.save_pretrained(
    output_dir,
    is_main_process=accelerator.is_main_process,
    save_function=accelerator.save,
    state_dict=accelerator.get_state_dict(model),
)
```

## Saving and Loading Models

```python
# Save complete state (for resuming training)
accelerator.save_state("checkpoint_dir")

# Save model only (for inference/hub)
unwrapped_model = accelerator.unwrap_model(model)
unwrapped_model.save_pretrained("output_dir")

# Load for resuming
accelerator.load_state("checkpoint_dir")
```

## Experiment Tracking

```python
accelerator = Accelerator(log_with="tensorboard")
accelerator.init_trackers("my_project")
accelerator.log({"loss": loss.item(), "accuracy": acc})
accelerator.end_training()
```

Supported: `tensorboard`, `wandb`, `mlflow`, `aim`, `comet_ml`, `dvclive`, `swanlab`, custom `GeneralTracker`.

Use `log_with="all"` to auto-discover all installed trackers.

## Notebooks (Jupyter/Colab)

```python
from accelerate import notebook_launcher

def training_function():
    accelerator = Accelerator()
    model, optimizer, dataloader = accelerator.prepare(...)
    # ... training loop

notebook_launcher(training_function, num_processes=2)
```

## Configuration

```bash
# Interactive config generation
accelerate config

# Check current config
accelerate env

# Estimate memory requirements
accelerate estimate-memory meta-llama/Llama-2-7b-hf --dtypes fp16
```

Config file (`~/.cache/huggingface/accelerate/default_config.yaml`):
```yaml
compute_environment: LOCAL_MACHINE
distributed_type: MULTI_GPU
mixed_precision: bf16
num_processes: 4
machine_rank: 0
main_process_ip: null
main_process_port: null
num_machines: 1
```

## Common Pitfalls

1. **Don't use `.to(device)` after `prepare`** — Accelerate's DataLoader auto-places tensors
2. **Always use `accelerator.backward()`** — handles gradient scaling for mixed precision
3. **`unwrap_model` before saving** — the prepared model is wrapped for distributed training
4. **FSDP saving**: Use `SHARDED_STATE_DICT` for checkpointing, `get_state_dict` for `save_pretrained`
5. **Gradient accumulation**: Always wrap in `with accelerator.accumulate(model):`
6. **Memory between runs**: Call `accelerator.free_memory()` or `accelerator.clear()`
7. **Don't mix DeepSpeed and FSDP** — pick one sharding strategy
8. **Notebooks**: Must use `notebook_launcher`, not `accelerate launch`
9. **`step_scheduler_with_optimizer`**: Default `True` steps scheduler every optimizer step; set `False` if stepping manually per epoch
10. **`fsdp_use_orig_params=True`** needed when optimizer is created before `prepare` (PEFT fine-tuning)
