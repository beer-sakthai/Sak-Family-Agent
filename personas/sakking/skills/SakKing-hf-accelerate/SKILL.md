---
name: SakKing-hf-accelerate
description: "Hugging Face Accelerate: distributed/mixed-precision training, device mapping, and the accelerate launch CLI — unify CPU/GPU/TPU/FSDP/DeepSpeed workflows with a single PyTorch-compatible API."
tags: [huggingface, accelerate, distributed, training, deepspeed, fsdp, mixed-precision, mlops]
version: 1.0.0
author: SakThai
license: MIT
platforms: [linux, macos, windows]
---

# Hugging Face Accelerate

**One-line goal**: let you write standard PyTorch training code once, then run it on CPU, single-GPU, multi-GPU, TPU, orNPU without rewriting the training loop.

## What Problem Accelerate Solves

- **Distributed training boilerplate**: `DistributedDataParallel`, `DataParallel`, `DeepSpeed`, and `FSDP` each require different setup code. Accelerate detects the environment and picks the right wrapper automatically.
- **Mixed precision complexity**: `amp`, `bf16`, `fp8`, and `fp16` each need slightly different autocast / GradScaler logic. Accelerate handles it via `Accelerator(mixed_precision="fp8")`.
- **Cross-device device mapping**: You shouldn't have to manually move every model/tensor to the correct device in custom loops. `accelerator.prepare()` does it for you.
- **TPU special-casing**: PyTorch/XLA requires `xm.mark_step()` and different optimizer stepping. Accelerate abstracts these differences.

## Quickstart

```python
from accelerate import Accelerator

accelerator = Accelerator()

model = ...      # any PyTorch model
optimizer = ...  # torch.optim
train_dl = ...   # torch.utils.data.DataLoader

# Wrap everything in one call
model, optimizer, train_dl = accelerator.prepare(model, optimizer, train_dl)

for batch in train_dl:
    optimizer.zero_grad()
    outputs = model(**batch)
    loss = outputs.loss
    accelerator.backward(loss)   # replaces loss.backward()
    optimizer.step()
```

Run the same script with:

```bash
# CPU / single GPU
python train.py

# Multi-GPU / DeepSpeed / FSDP / TPU
accelerate launch train.py --config_file config.yaml
```

## Core API

### `Accelerator`

| Argument | Common Values | What it Controls |
|----------|---------------|------------------|
| `device_placement` | `True` (default) | Auto-move inputs/model to the right device. |
| `mixed_precision` | `"no"`, `"fp16"`, `"bf16"`, `"fp8"` | Automatic mixed precision. |
| `gradient_accumulation_steps` | `int` | Accumulates gradients across steps without extra code. |
| `deepseed_plugin` | `DeepSpeedPlugin` | Enables DeepSpeed ZeRO stages, offload, etc. |
| `fsdp_plugin` | `FullyShardedDataParallelPlugin` | Enables FSDP wrapping. |
| `log_with` | `"tensorboard"`, `"wandb"`, `"mlflow"` | Logging integrations via `accelerate init`. |

**Common methods:**

| Method | Purpose |
|--------|---------|
| `prepare(*objects)` | Wrap models, optimizers, dataloaders, schedulers for distributed / device-aware execution. |
| `backward(loss)` | Scales loss, runs backward, and synchronizes gradients across processes. |
| `wait_for_everyone()` | Barrier; blocks until all processes reach this point. |
| `gather(tensor)` | Gather tensors from all processes (returns stacked tensor on main process). |
| `reduce(tensor, ...)` | Reduce (sum/mean) across processes. |
| `unwrap_model(model)` | Access the original underlying model from a DDP/FSDP wrapper. |
| `get_state_dict(model)` | Fetch a checkpoint-safe state dict without DDP-specific prefixes. |
| `save_state(output_dir)` | Save accelerator state (model, optimizer, RNG) in a distributed-safe way. |
| `load_state(input_dir)` | Load and restore distributed-aware state. |

### Device Placement (without `prepare`)

```python
device = accelerator.device   # e.g., cuda:0, xla:0, cpu
model = model.to(device)
batch = {k: v.to(device) for k, v in batch.items()}
```

`Accelerator` automatically respects:
- CUDA (`cuda:0`, `cuda:1`, …)
- MPS (`mps:0`) on Apple Silicon
- TPU (`xla:0`, …)
- CPU
- NPU (Ascend via `torch_npu`, if available)

## Mixed Precision

```python
accelerator = Accelerator(mixed_precision="bf16")
# or "fp16", "fp8", or "no"
```

- `accelerator.backward(loss)` automatically scales with `GradScaler` when `fp16` / `fp8` is active.
- For `bf16`, no scaling is required on Ampere+ GPUs.
- `fp8` support requires Hopper GPUs (compute capability >= 8.9) and PyTorch ≥ 2.1.

## Gradient Accumulation

```python
accelerator = Accelerator(gradient_accumulation_steps=4)

for i, batch in enumerate(train_dl):
    with accelerator.accumulate(model):   # handles no-sync when needed
        outputs = model(**batch)
        loss = outputs.loss
        accelerator.backward(loss)
        optimizer.step()
        optimizer.zero_grad()
```

No DDP `no_sync()` context managers needed.

## DeepSpeed Integration

```python
from accelerate import Accelerator, DeepSpeedPlugin

plugin = DeepSpeedPlugin(
    zero_stage=2,
    offload_optimizer_device="cpu",
    offload_param_device="cpu",
)
accelerator = Accelerator(deepspeed_plugin=plugin)

model, optimizer, train_dl = accelerator.prepare(model, optimizer, train_dl)
```

**ZeRO stages:**
- **0**: disabled (standard DDP)
- **1**: optimizer state partitioning
- **2**: optimizer + gradient partitioning
- **3**: optimizer + gradient + parameter partitioning

Offload to CPU or NVMe to fit larger models in less GPU VRAM.

## FSDP Integration

```python
from accelerate import FullyShardedDataParallelPlugin

fsdp_plugin = FullyShardedDataParallelPlugin(
    min_num_params=1e6,
    sharding_strategy="FULL_SHARD",
)
accelerator = Accelerator(fsdp_plugin=fsdp_plugin)
model, optimizer, train_dl = accelerator.prepare(model, optimizer, train_dl)
```

FSDP is activated when `fsdp_plugin` is supplied. It shards model parameters, gradients, and optimizer states across GPUs.

## Accelerate CLI

The `accelerate` command-line tool manages configs and launches jobs.

```bash
accelerate config          # interactive setup (saves to ~/.cache/huggingface/accelerate/default_config.yaml)
accelerate launch train.py --config_file config.yaml
accelerate launch train.py --num_processes 8 --mixed_precision fp16
accelerate env             # shows capabilities (GPU count, XLA, etc.)
accelerate test            # quick sanity check
accelerate estimate-memory # print VRAM requirement for a model
```

### `estimate-memory`

```bash
accelerate estimate-memory \
  --model_name EleutherAI/gpt-neo-125M \
  --dtypes float32
```

Returns peak VRAM, activation VRAM, and parameter count. Useful before launching on a shared cluster.

## Integration with Transformers

- `transformers.Trainer` uses Accelerate internally since v4.26.
- Custom training loops: use the `accelerator.prepare()` pattern.
- For loading/saving checkpoints in a distributed run:
  ```python
  # Save
  accelerator.wait_for_everyone()
  unwrapped_model = accelerator.unwrap_model(model)
  unwrapped_model.save_pretrained(output_dir)

  # Load
  model = AutoModelForCausalLM.from_pretrained(input_dir)
  model = accelerator.prepare(model)
  ```

## Integration with Other Libraries

| Library | How it integrates |
|---------|-------------------|
| **PEFT** | `get_peft_model()` + `accelerator.prepare(model)` for distributed LoRA/QLoRA. |
| **Diffusers** | Same pattern as Transformers; `accelerator.prepare(unet, optimizer, dl)`. |
| **TRL** | `SFTTrainer` / `PPOTrainer` use Accelerate under the hood. |
| **BitsAndBytes** | `load_in_4bit` / `load_in_8bit` models work directly with `prepare`. |
| **W&B / TensorBoard** | Pass `log_with` in `Accelerator` and use `accelerator.init_trackers(...)`. |

## Common Pitfalls

1. **Forgetting `accelerator.backward()`**: using raw `loss.backward()` breaks gradient synchronization. Always use the Accelerator method.
2. **Loading DDP-only checkpoints**: `accelerator.load_state()` expects Accelerate-formatted checkpoints. Use `accelerator.unwrap_model().save_pretrained()` for Hub-style saves.
3. **FP16 without CUDA / MPS**: `fp16` on CPU is slow and can be unstable; use `bf16` (if supported) or `no`.
4. **Too-large micro-batch size on TPU**: `xm.step()` semantics differ; let Accelerate handle it.
5. **Saving inside `accelerator.prepare`**: save only the unwrapped model, or use `accelerator.save_state()`, otherwise you'll get DDP wrappers in your saved weights.
6. **Variable sequence lengths with FSDP**: FSDP expects static graph shapes; wrap dynamic padding in `torch.utils.checkpoint` or pad to a fixed length.
7. **DeepSpeed config conflicts**: if `zero_stage=3`, set `offload_optimizer_device` / `offload_param_device` carefully; CPU offload dramatically slows training.

## When to Use Accelerate

| Scenario | Recommendation |
|----------|----------------|
| Single GPU experiment | `Accelerator()` with `mixed_precision="bf16"`. |
| Consumer GPU fine-tuning | QLoRA + Accelerate + Transformers Trainer. |
| Multi-GPU node (research cluster) | `accelerate launch` + DeepSpeed ZeRO-2/3 or FSDP. |
| TPU training | `accelerate launch --tpu` or `xla_spawn`. |
| Custom reinforcement learning loop | `accelerator.backward()` + `wait_for_everyone()` + `gather()`. |
| Reproducible launch scripts | Put hyperparameters in a config file; use `accelerate launch --config_file config.yaml`. |

## References

- **Docs**: https://huggingface.co/docs/accelerate
- **GitHub**: https://github.com/huggingface/accelerate
- **Quicktour**: https://huggingface.co/docs/accelerate/en/quicktour
- **DeepSpeed guide**: https://huggingface.co/docs/accelerate/en/usage_guides/deepspeed
- **FSDP guide**: https://huggingface.co/docs/accelerate/en/usage_guides/fsdp
- **Launch config**: https://huggingface.co/docs/accelerate/en/package_reference/cli#accelerate-launch
