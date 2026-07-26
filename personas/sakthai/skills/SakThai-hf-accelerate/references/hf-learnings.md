# HF Learnings: hf-accelerate-deep-dive

**Date:** 2026-07-25
**Topic:** Comprehensive deep-dive into Hugging Face Accelerate v1.14.0
**Skill:** `mlops/hf-accelerate/`

## Summary

Complete deep-dive on Hugging Face Accelerate (v1.14.0, installed currently). Covers the full Accelerator class API, all 50+ methods, the CLI toolkit (`accelerate config`, `launch`, `estimate-memory`, `env`, `test`), big model inference with device maps and CPU/disk offload, FSDP and DeepSpeed integration with comparison matrix, mixed-precision modes (fp16/bf16/fp8 via TE/MS-AMP/torchao), gradient accumulation patterns, experiment tracking, memory estimation for zero-cost planning, and production deployment checklist. Previous coverage (#17 in the tracker) was shallow; this is a proper deep-dive.

---

## 1. Architecture Overview

Accelerate enables the same PyTorch code to run across any distributed configuration by adding just four lines:

```python
from accelerate import Accelerator
accelerator = Accelerator()
model, optimizer, training_dataloader, scheduler = accelerator.prepare(
    model, optimizer, training_dataloader, scheduler
)
# in the training loop:
accelerator.backward(loss)
```

Then launch via:
```bash
accelerate launch {my_script.py}
```

Under the hood, Accelerate:
- Detects the hardware environment (GPUs, TPUs, CPU)
- Configures device placement, mixed precision, and distributed strategy
- Wraps model/optimizer/dataloader with distributed-aware versions
- Handles gradient synchronization across processes
- Manages RNG state synchronization

### Key Components Diagram

```
Accelerator
├── device (torch.device)
├── distributed_type (DistributedType)
├── mixed_precision (str: 'no'/'fp16'/'bf16'/'fp8')
├── num_processes (int)
├── process_index (int)
├── local_process_index (int)
├── state (AcceleratorState)
│   ├── AcceleratorState (global distributed state)
│   ├── PartialState (process-local state)
│   └── DistributedType (enum: NO, MULTI_GPU, MULTI_NPU, MULTI_XPU, DEEPSPEED, FSDP, TPU, MEGATRON_LM)
├── sync_gradients (bool)
└── optimizer_step_was_skipped (bool)
```

---

## 2. Accelerator Class — Complete Method Reference

### Construction Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `device_placement` | `bool` | `True` | Auto-place objects on device |
| `mixed_precision` | `str` | env var or `'no'` | `'no'`, `'fp16'`, `'bf16'`, `'fp8'` |
| `gradient_accumulation_steps` | `int` | `1` | Steps before gradient sync |
| `cpu` | `bool` | `False` | Force CPU execution |
| `dataloader_config` | `DataLoaderConfiguration` | — | Dataloader behavior config |
| `deepspeed_plugin` | `DeepSpeedPlugin` or dict | — | DeepSpeed configuration |
| `fsdp_plugin` | `FullyShardedDataParallelPlugin` | — | FSDP configuration |
| `megatron_lm_plugin` | `MegatronLMPlugin` | — | Megatron-LM configuration |
| `rng_types` | `list[str]` | `['generator']` | RNG sync at each iteration |
| `log_with` | `list[str]` | — | Logger names (`'tensorboard'`, `'wandb'`, etc.) |
| `project_config` | `ProjectConfiguration` | — | Checkpoint/logging config |
| `project_dir` | `str`, `PathLike` | — | Storage directory |
| `step_scheduler_with_optimizer` | `bool` | `True` | Step scheduler with optimizer |
| `kwargs_handlers` | `list[KwargsHandler]` | — | Custom handlers for distributed objects |
| `dynamo_backend` | `str` | `'no'` | TorchDynamo backend |
| `dynamo_plugin` | `TorchDynamoPlugin` | — | Fine-grained dynamo config |
| `gradient_accumulation_plugin` | `GradientAccumulationPlugin` | — | Advanced grad accum config |

### Core Methods (50+ total)

#### `accelerator.prepare(*objects)`
Wraps model, optimizer, dataloader, scheduler for distributed training. The single most important method.

```python
model, optimizer, dataloader, scheduler = accelerator.prepare(
    model, optimizer, dataloader, scheduler
)
```

- Moves model to correct device
- Wraps model in DDP/FSDP/DeepSpeed as configured
- Shards dataloader across processes
- Wraps optimizer for gradient scaling

#### `accelerator.backward(loss)`
Replaces `loss.backward()`. Scales gradients according to gradient accumulation plugin and calls correct backward based on configuration.

#### `accelerator.accumulate(*models)`
Context manager for gradient accumulation. Inside the block, gradients are accumulated across `gradient_accumulation_steps` without syncing.

```python
for batch in dataloader:
    with accelerator.accumulate(model):
        outputs = model(inputs)
        loss = loss_fn(outputs, labels)
        accelerator.backward(loss)
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()
```

#### `accelerator.gather(tensor)`
Gather tensors across all processes and concatenate on first dimension. For evaluation metrics.

#### `accelerator.gather_for_metrics(input_data, use_gather_object=False)`
Like gather but drops duplicates in the last batch on distributed systems. Always use this for metric computation.

#### `accelerator.unwrap_model(model)`
Returns the original unwrapped model (removes DDP/FSDP wrappers). Essential for saving.

#### `accelerator.save_state(output_dir)`
Saves model, optimizer, scheduler, RNG, and registered objects to directory.

#### `accelerator.load_state(input_dir)`
Loads a previously saved state.

#### `accelerator.save_model(model, save_directory, ...)`
Saves model in a format suitable for inference. Can shard checkpoints.

#### `accelerator.get_state_dict(model, unwrap=True)`
Returns state dict potentially without full precision.

#### `accelerator.clip_grad_norm_(parameters, max_norm)`
Gradient clipping — replaces `torch.nn.utils.clip_grad_norm_`.

#### `accelerator.clip_grad_value_(parameters, clip_value)`
Gradient value clipping — replaces `torch.nn.utils.clip_grad_value_`.

#### `accelerator.autocast()`
Context manager for automatic mixed precision (fp16/bf16).

```python
with accelerator.autocast():
    outputs = model(inputs)
```

#### `accelerator.join_uneven_inputs(joinables, even_batches=None)`
Context manager for handling uneven dataset sizes in distributed settings. Wraps `torch.distributed.algorithms.join`.

#### `accelerator.main_process_first()`
Context manager — main process (rank 0) enters first, others wait.

#### `accelerator.local_main_process_first()`
Like main_process_first but for local processes only.

#### `accelerator.on_main_process` / `accelerator.on_local_main_process`
Decorators for running functions only on main/local main process.

#### `accelerator.wait_for_everyone()`
Sync point — blocks until all processes reach this call.

#### `accelerator.free_memory()`
Releases all references and calls garbage collector. Use between trainings.

#### `accelerator.clear()`
Alias for `free_memory()`.

#### `accelerator.end_training()`
Stops trackers, destroys process group. Must call at end.

#### `accelerator.set_trigger()` / `accelerator.check_trigger()`
Inter-process signaling — set a flag on one process, check from another.

#### `accelerator.print(obj)`
Print only from main process (avoids spam).

#### `accelerator.log(values, step=None)`
Log metrics through all initialized trackers.

#### `accelerator.init_trackers(project_name, config=None)`
Initialize experiment tracking.

#### `accelerator.get_tracker(name)`
Get a specific tracker by name.

#### `accelerator.skip_first_batches(dataloader, num_batches)`
Skip N batches — useful for resuming from checkpoint mid-epoch.

#### `accelerator.split_between_processes(list_or_tensor)`
Split data evenly across processes.

#### `accelerator.reduce(tensor, reduction='sum')`
Reduce tensor across all processes.

#### `accelerator.pad_across_processes(tensor, dim=0, pad_index=0)`
Pad tensors to same size across processes for gather.

#### `accelerator.autocast_cache_enabled` property
Controls whether autocast caching is enabled.

---

## 3. CLI Toolkit

### `accelerate config`
Interactive configuration wizard. Creates `default_config.yaml`.

```bash
accelerate config                 # interactive
accelerate config default         # minimal config with only mixed_precision
accelerate config update          # update existing to latest defaults
```

Config file location: `~/.cache/huggingface/accelerate/default_config.yaml` (or `HF_HOME/accelerate/`)

### `accelerate launch`
Launches training script on distributed hardware.

```bash
accelerate launch [options] training_script.py --training_args

# Key options:
# --cpu                          Force CPU
# --multi_gpu                    Multi-GPU distributed
# --tpu                          TPU training
# --num_processes N              Total processes
# --num_machines N               Multi-node
# --mixed_precision {no,fp16,bf16,fp8}
# --use_deepspeed                Enable DeepSpeed
# --use_fsdp                     Enable FSDP
# --gpu_ids "0,1,2"              Specific GPUs
# -m                             Run as python module
# -q, --quiet                    Silence stack traces
```

### `accelerate env`
Prints environment info — always include when filing bugs.

### `accelerate estimate-memory {model_name}`
Estimates vRAM needed for model inference/training without loading it.

```bash
accelerate estimate-memory bigscience/bloom-176b --dtypes float16 int8
```

- Uses model metadata from Hub
- Reports memory for loading + training estimates
- Supports `--library_name` (timm, transformers)
- Supports `--trust_remote_code`

### `accelerate test`
Validates configuration by running test script.

### `accelerate tpu-config`
Manages TPU pod setup and command execution.

---

## 4. Mixed Precision Training

### FP16 (Automatic Mixed Precision — AMP)
- Enabled via `mixed_precision="fp16"` or `--mixed_precision fp16`
- Uses PyTorch native `torch.cuda.amp`
- Forward pass in fp16, master weights in fp32
- Loss scaling via `GradientScaler`
- Works on all NVIDIA GPUs with CUDA compute ≥ 7.0

### BF16 (Brain Floating Point)
- Enabled via `mixed_precision="bf16"`
- No loss scaling needed (same exponent range as fp32)
- Requires Ampere or newer NVIDIA GPU, or TPU
- Better training stability than fp16

### FP8 Training

Three backends:

#### TransformersEngine (TE) — Recommended
- Drop-in replacement for `nn.Linear` and `nn.LayerNorm`
- Selects FP8 for GEMM layers, BF16 for everything else
- Configured via `FP8RecipeKwargs`:

```python
from accelerate.utils import FP8RecipeKwargs

kwargs_handler = FP8RecipeKwargs(
    margin=0,                    # gradient scaling margin
    interval=1,                  # scaling factor recompute interval
    fp8_format="HYBRID",         # HYBRID (train) or E4M3 (eval)
    amax_history_len=16,         # history for scaling
    amax_compute_algo="max",     # max or most_recent
    override_linear_precision=(False, False, False)  # fprop, dgrad, wgrad
)
accelerator = Accelerator(mixed_precision="fp8", kwargs_handlers=[kwargs_handler])
```

- Performance gains only visible for models with billions+ parameters
- CLI flags: `--fp8_backend te`, `--fp8_format`, `--fp8_margin`, etc.

#### MS-AMP (Microsoft) — Deprecated
- Three optimization levels (O1, O2, O3)
- O1: fp8 comm + fp16 weights + fp32 optimizer
- O2: fp8 comm + fp16 weights + fp8/fp16 optimizer states
- O3: fp8 weights + fp16 master weights (DeepSpeed only)
- **Unmaintained since 2023** — do not use for new projects
- Incompatible with CUDA 12.x+, modern NCCL, PyTorch 2.2+

#### torchao (PyTorch Native)
- Native PyTorch FP8 via `torch.ao`
- Set `--fp8_backend torchao`
- Most modern, actively maintained

### Precision Comparison

| Backend | Computation | Weights | Optimizer | Comm | Memory Savings |
|---------|------------|---------|-----------|------|----------------|
| FP16 AMP | fp16 | fp32 | fp32+fp32 | fp32 | 2× vs fp32 |
| TE | fp8 | fp32 | fp32+fp32 | fp32 | ~1.5× vs fp16 |
| torchao | fp8 | varies | varies | varies | varies |
| MS-AMP O1 | fp8 | fp16 | fp32+fp32 | fp8 | ~2× vs fp16 |
| MS-AMP O2 | fp8 | fp16 | fp8+fp16 | fp8 | ~3× vs fp16 |

---

## 5. Big Model Inference

### Problem
Loading a 6B+ param model requires 2 copies in RAM (initialization + checkpoint), easily exceeding available memory.

### Solution: 3-Step Process

#### Step 1: `init_empty_weights()`
Initialize model on meta device — zero RAM usage.

```python
from accelerate import init_empty_weights
from transformers import AutoConfig, AutoModelForCausalLM

config = AutoConfig.from_pretrained("bigscience/bloom-176b")
with init_empty_weights():
    model = AutoModelForCausalLM.from_config(config)
```

Behind the scenes, uses PyTorch 1.9+'s `meta` device. Parameters are created but occupy no memory.

#### Step 2: `load_checkpoint_and_dispatch()`
Loads checkpoint (full or sharded) and dispatches across devices.

```python
from accelerate import load_checkpoint_and_dispatch

model = load_checkpoint_and_dispatch(
    model,
    checkpoint="path/to/checkpoint",
    device_map="auto",
    no_split_module_classes=["BloomBlock"],
    max_memory={0: "30GiB", 1: "46GiB", "cpu": "80GiB"}
)
```

#### Step 3: Run inference normally
Accelerate adds hooks to move data between devices transparently.

```python
outputs = model.generate(input_ids)
```

### Device Map Strategies

| Strategy | Behavior |
|----------|----------|
| `"auto"` | Evenly split across all GPUs + CPU offload. Same as `"balanced"`. |
| `"balanced"` | Even split across detected GPUs. |
| `"balanced_low_0"` | Even split on GPUs 1+, GPU 0 gets leftovers. Good for generate(). |
| `"sequential"` | Fill GPU 0, then GPU 1, etc. |
| Custom dict | Manually specify `{"layer_name": device_id}` for each module. |

### Device Map Memory Limits

```python
from accelerate import infer_auto_device_map

device_map = infer_auto_device_map(
    model,
    max_memory={0: "10GiB", 1: "10GiB", "cpu": "30GiB"}
)
```

**Important:** First CUDA allocation uses 1-2GB for kernels. Adjust max_memory accordingly.

### Offload Modes

| Mode | Function | Memory | Speed | Use Case |
|------|----------|--------|-------|----------|
| CPU Offload | `cpu_offload(model, device)` | High CPU RAM | Moderate | Model fits on 1 GPU with CPU spillover |
| CPU+Hook | `cpu_offload_with_hook(model, device)` | Lower | Faster loop | Pipeline-style inference in loop |
| Disk Offload | `disk_offload(model, dir, device)` | Disk space | Slow | Extreme cases, no CPU RAM |
| Full Dispatch | `load_checkpoint_and_dispatch()` | Mixed | Best | Multi-GPU with partial offload |

### Chained CPU Offload (Pipeline Pattern)

```python
model_1, hook_1 = cpu_offload_with_hook(model_1, device)
model_2, hook_2 = cpu_offload_with_hook(model_2, device, prev_module_hook=hook_1)
model_3, hook_3 = cpu_offload_with_hook(model_3, device, prev_module_hook=hook_2)

hid_1 = model_1(input)
for i in range(50):
    hid_2 = model_2(hid_1)
hid_3 = model_3(hid_3)
hook_3.offload()
```

### Sharded Checkpoints

Format:
```
checkpoint_dir/
├── index.json          # Maps param_name → shard_file
├── first_state_dict.bin
├── second_state_dict.bin
└── ...
```

`index.json` structure:
```json
{
  "linear1.weight": "first_state_dict.bin",
  "linear1.bias": "first_state_dict.bin",
  "linear2.weight": "second_state_dict.bin",
  "linear2.bias": "second_state_dict.bin"
}
```

### Known Limitations

1. Auto device map may over-allocate CPU RAM — move modules to disk if OOM
2. Naive model parallelism — only one GPU active at a time
3. No pre-fetching for CPU/disk offloaded weights
4. Disk offload very slow without NVMe
5. `load_checkpoint_and_dispatch()` performs no key validation

---

## 6. FSDP Integration (PyTorch Fully Sharded Data Parallel)

### What FSDP Does
- Shards model parameters, gradients, and optimizer states across GPUs
- All-gathers parameters on-demand for forward/backward
- Reduce-scatters gradients after backward
- Dramatically reduces per-GPU memory

### Configuration

Via CLI:
```bash
accelerate launch \
  --use_fsdp \
  --fsdp_sharding_strategy 1 \            # 1=FULL_SHARD, 2=SHARD_GRAD_OP, 3=NO_SHARD
  --fsdp_offload_params true \
  --fsdp_auto_wrap_policy TRANSFORMER_BASED_WRAP \
  --fsdp_transformer_layer_cls_to_wrap BloomBlock \
  --fsdp_state_dict_type SHARDED_STATE_DICT \
  --fsdp_forward_prefetch true \
  --fsdp_backward_prefetch BACKWARD_PRE \
  --fsdp_cpu_ram_efficient_loading true \
  --fsdp_sync_module_states true \
  --fsdp_use_orig_params true \
  --fsdp_activation_checkpointing true \
  training_script.py
```

Via Plugin:
```python
from accelerate import Accelerator
from accelerate.utils import FullyShardedDataParallelPlugin
from torch.distributed.fsdp import ShardingStrategy

fsdp_plugin = FullyShardedDataParallelPlugin(
    sharding_strategy=ShardingStrategy.FULL_SHARD,
    cpu_offload=True,
    auto_wrap_policy="TRANSFORMER_BASED_WRAP",
    transformer_layer_cls_to_wrap=["BloomBlock"],
)

accelerator = Accelerator(fsdp_plugin=fsdp_plugin)
```

### Sharding Strategies

| Strategy | Parameters | Gradients | Optimizer | Memory |
|----------|-----------|-----------|-----------|--------|
| `FULL_SHARD` (1) | Sharded | Sharded | Sharded | Lowest |
| `SHARD_GRAD_OP` (2) | Replicated | Sharded | Sharded | Medium |
| `NO_SHARD` (3) | Replicated | Replicated | Replicated | Highest |

### Key CLI Flags

| Flag | Description |
|------|-------------|
| `--fsdp_offload_params` | Offload params + gradients to CPU |
| `--fsdp_min_num_params` | Min params for auto wrap |
| `--fsdp_sharding_strategy` | 1 (FULL_SHARD), 2 (SHARD_GRAD_OP), 3 (NO_SHARD) |
| `--fsdp_auto_wrap_policy` | `TRANSFORMER_BASED_WRAP`, `SIZE_BASED_WRAP`, `NO_WRAP` |
| `--fsdp_transformer_layer_cls_to_wrap` | Class name for transformer wrapping |
| `--fsdp_backward_prefetch_policy` | `BACKWARD_PRE`, `BACKWARD_POST` |
| `--fsdp_state_dict_type` | `FULL_STATE_DICT`, `SHARDED_STATE_DICT`, `LOCAL_STATE_DICT` |
| `--fsdp_forward_prefetch` | Prefetch next params in forward |
| `--fsdp_use_orig_params` | Required for `torch.compile` |
| `--fsdp_cpu_ram_efficient_loading` | Load weights only on rank 0 |
| `--fsdp_sync_module_states` | Broadcast params from rank 0 |
| `--fsdp_activation_checkpointing` | Free intermediate activations |

### Checkpointing

- `FULL_STATE_DICT`: Consolidates to single rank (slow for large models)
- `SHARDED_STATE_DICT`: Per-rank shards (fast, needs consolidation for inference)
- Use `FULL_STATE_DICT` for easy downstream loading
- Use `SHARDED_STATE_DICT` for fast training checkpoints

---

## 7. DeepSpeed Integration

### ZeRO Stages

| Stage | Parameters | Gradients | Optimizer | Memory Saved |
|-------|-----------|-----------|-----------|-------------|
| ZeRO-1 | Replicated | Replicated | Partitioned | 4× (optimizer) |
| ZeRO-2 | Replicated | Partitioned | Partitioned | 8× (optimizer + gradients) |
| ZeRO-3 | Partitioned | Partitioned | Partitioned | Linear with GPUs |

### Configuration

Via config file:
```bash
accelerate launch \
  --use_deepspeed \
  --zero_stage 3 \
  --offload_optimizer_device cpu \
  --offload_param_device cpu \
  --gradient_accumulation_steps auto \
  --gradient_clipping auto \
  --zero3_init_flag true \
  --zero3_save_16bit_model true \
  --deepspeed_config_file ds_config.json \
  training_script.py
```

Via Plugin:
```python
from accelerate import Accelerator
from accelerate.utils import DeepSpeedPlugin

deepspeed_plugin = DeepSpeedPlugin(zero_stage=3, gradient_accumulation_steps="auto")
accelerator = Accelerator(deepspeed_plugin=deepspeed_plugin)
```

### Key CLI Flags

| Flag | Description |
|------|-------------|
| `--zero_stage` | 1, 2, or 3 |
| `--offload_optimizer_device` | `none`, `cpu`, `nvme` |
| `--offload_param_device` | `none`, `cpu`, `nvme` |
| `--gradient_accumulation_steps` | Use `auto` to inherit from Accelerator |
| `--gradient_clipping` | Use `auto` to inherit |
| `--zero3_init_flag` | Enable `deepspeed.zero.Init` for massive models |
| `--zero3_save_16bit_model` | Save consolidated 16-bit weights |
| `--deepspeed_config_file` | Custom DS config file (for advanced options) |
| `--deepspeed_moe_layer_cls_names` | MoE layer class names for ZeRO |

### DeepSpeed Config File (Advanced)

For settings not exposed via CLI, use `--deepspeed_config_file`:
```json
{
  "train_batch_size": 32,
  "gradient_accumulation_steps": 4,
  "zero_optimization": {
    "stage": 3,
    "contiguous_gradients": true,
    "overlap_comm": true,
    "reduce_scatter": true,
    "stage3_max_live_parameters": 1e9,
    "stage3_max_reuse_distance": 1e9,
    "stage3_prefetch_bucket_size": 5e7,
    "stage3_param_persistence_threshold": 1e5
  },
  "fp16": {
    "enabled": true,
    "loss_scale": 0,
    "loss_scale_window": 1000
  }
}
```

---

## 8. FSDP vs DeepSpeed — Comparison Matrix

| Feature | FSDP | DeepSpeed |
|---------|------|-----------|
| Sharding | `FULL_SHARD`=ZeRO-3, `SHARD_GRAD_OP`=ZeRO-2 | ZeRO stages 1-3 |
| Offload | All-or-nothing (params+grads+opt) | Flexible (params vs opt, CPU vs NVMe) |
| Prefetching | `forward_prefetch`, `backward_prefetch` | Auto based on hyperparams |
| Model Loading | Explicit `cpu_ram_efficient_loading` | Auto with ZeRO-3 |
| Auto Wrap | `TRANSFORMER_BASED_WRAP` / `SIZE_BASED_WRAP` | Transparent |
| torch.compile | Needs `--fsdp_use_orig_params true` | Transparent |
| Checkpointing | `SHARDED_STATE_DICT` or `FULL_STATE_DICT` | `zero_to_fp32.py` script |
| Precision (prep) | Flat params in `torch_dtype` | Flat params in fp32 (more memory) |
| Precision (optim) | Optimizer in `torch_dtype` (lower mem) | Optimizer always fp32 (upcasted) |
| MoE | Not native | Supported via `--deepspeed_moe_layer_cls_names` |
| Pipeline Parallel | No | Supported |
| Community | PyTorch native | Broader ecosystem |

### Data Precision Differences (Important!)

| Framework | Loading | Preparation | Training | Optimizer |
|-----------|---------|-------------|----------|-----------|
| FSDP (no MP) | bf16 | bf16 | bf16 | bf16 |
| FSDP (bf16 MP) | bf16 | fp32 | bf16 | fp32 |
| DeepSpeed (bf16) | bf16 | fp32 | bf16 | fp32 |

Key insight: DeepSpeed ALWAYS upcasts flat params to fp32 during preparation, consuming more memory with few GPUs. FSDP can optionally keep them in lower precision.

---

## 9. Gradient Accumulation

### Basic Pattern
```python
accelerator = Accelerator(gradient_accumulation_steps=4)
model, optimizer, dataloader = accelerator.prepare(model, optimizer, dataloader)

for batch in dataloader:
    with accelerator.accumulate(model):
        outputs = model(inputs)
        loss = loss_fn(outputs, labels)
        accelerator.backward(loss)
        optimizer.step()
        optimizer.zero_grad()
```

### How It Works
- Inside `accumulate()`: gradients are accumulated without syncing
- At the boundary: gradients are synced (all-reduced) across processes
- Optimizer step is taken only at sync points
- `sync_gradients` property indicates whether gradients are being synced

### Gradient Accumulation Plugin
For more control:
```python
from accelerate.utils import GradientAccumulationPlugin

plugin = GradientAccumulationPlugin(
    num_steps=4,
    adjust_scheduler=True,  # Auto-adjust LR scheduler
)
accelerator = Accelerator(gradient_accumulation_plugin=plugin)
```

---

## 10. Experiment Tracking

### Supported Trackers
- TensorBoard (`"tensorboard"`)
- WandB (`"wandb"`)
- MLflow (`"mlflow"`)
- Comet ML (`"comet_ml"`)
- Aim (`"aim"`)
- DVCLive (`"dvclive"`)
- TrackIO (`"trackio"`)
- SwanLab (`"swanlab"`)
- Custom (`GeneralTracker` subclass)
- `"all"` — auto-detect all available

### Initialization
```python
accelerator = Accelerator(log_with=["tensorboard", "wandb"])
accelerator.init_trackers(
    "my_project",
    config={"learning_rate": 1e-4, "batch_size": 32}
)
```

### Logging
```python
accelerator.log({"train/loss": loss.item(), "train/accuracy": acc}, step=step)
```

### Checkpoint Integration
```python
accelerator.save_state("checkpoint_dir")
accelerator.load_state("checkpoint_dir")
```

### At End of Training
```python
accelerator.end_training()
```

---

## 11. Dynamo Backend Integration

```python
accelerator = Accelerator(dynamo_backend="inductor")
# or
from accelerate.utils import TorchDynamoPlugin
plugin = TorchDynamoPlugin(backend="inductor", mode="max-autotune")
accelerator = Accelerator(dynamo_plugin=plugin)
```

Supported backends: `"eager"`, `"aot_eager"`, `"inductor"`, `"aot_ts_nvfuser"`, `"nvprims_nvfuser"`, `"cudagraphs"`, `"fx2trt"`, `"onnxrt"`, `"ipex"`

---

## 12. Memory Estimation (Zero-Cost Planning)

```bash
# Estimate memory for inference
accelerate estimate-memory meta-llama/Llama-2-7b-hf --dtypes float16

# Estimate for multiple dtypes
accelerate estimate-memory bigscience/bloom-176b --dtypes float32 float16 int8

# With custom library
accelerate estimate-memory timm/resnet50 --library_name timm --dtypes float16
```

**Uses:**
- Model metadata from Hugging Face Hub
- Parameter counts × bytes per parameter
- Training estimate ≈ 4× inference estimate (for Adam)
- Add ~20% to result for real allocation

---

## 13. Production Deployment Checklist

1. **Configure**: Run `accelerate config` or use config file
2. **Wrap**: Add Accelerator + 4 lines to training script
3. **Replace**: `loss.backward()` → `accelerator.backward(loss)`
4. **Accumulate**: Wrap training loop in `accelerator.accumulate(model)` for grad accum
5. **Clip**: Use `accelerator.clip_grad_norm_()` instead of torch's
6. **Save**: Use `accelerator.save_model()` or `accelerator.get_state_dict()` for checkpointing
7. **Gather**: Use `accelerator.gather_for_metrics()` for evaluation
8. **Log**: Use `accelerator.log()` for metrics
9. **Clean**: Call `accelerator.end_training()` at end
10. **Launch**: Use `accelerate launch` with appropriate config

### Inference-First Checklist (Zero-Cost)

1. Use `init_empty_weights()` to avoid OOM
2. Use `load_checkpoint_and_dispatch()` with `device_map="auto"`
3. Set `max_memory` to avoid CPU crashes
4. Mark residual-connected modules with `no_split_module_classes`
5. For single-GPU: use `cpu_offload()` if model > GPU memory
6. For multi-GPU: use `device_map="balanced_low_0"` for generation tasks
7. Always validate with `accelerate env` before filing bugs
8. Use `accelerate estimate-memory` before deployment

---

## 14. Key Insights

- **The 4-line magic**: `Accelerator()`, `prepare()`, `accelerate.backward()`, `accelerate launch` — this is all you need for 90% of distributed training.
- **Memory estimation is free**: Use `accelerate estimate-memory` before committing to any model — zero-cost planning.
- **Gradient accumulation is built in**: Don't implement it manually; use `accelerator.accumulate()`.
- **`gather_for_metrics` > `gather`**: Always use `gather_for_metrics()` for evaluation — it handles uneven batches correctly.
- **FSDP vs DeepSpeed**: Choose FSDP for PyTorch-native experience, DeepSpeed for MoE/NVMe offload/custom configs. FSDP uses less memory on optimizer states with few GPUs.
- **Big model inference**: Always start with `init_empty_weights()` + `load_checkpoint_and_dispatch(device_map="auto")`. Add `max_memory` cautiously.
- **Chained CPU offload**: For pipeline-style models, `cpu_offload_with_hook()` with `prev_module_hook` keeps models on GPU during loops.
- **FP8 is experimental**: Only beneficial for 1B+ param models. Use TE backend (not MS-AMP, which is deprecated).
- **Save model format**: `accelerator.save_model()` produces sharded checkpoints compatible with `from_pretrained()`.
- **Dynamo + FSDP**: Always set `--fsdp_use_orig_params true` when combining with torch.compile.

---

## Skill Created
`mlops/hf-accelerate/` — complete reference with SKILL.md + this learning reference.

## Repository Search Tags
- `accelerate.Accelerator` — main class API
- `accelerate launch` — CLI launcher
- `init_empty_weights` — meta device initialization
- `load_checkpoint_and_dispatch` — big model loading + device mapping
- `device_map` — model distribution strategy
- `FSDP vs DeepSpeed` — comparison matrix
- `gather_for_metrics` — correct metric gathering
- `FP8 training` — low-precision training backends
