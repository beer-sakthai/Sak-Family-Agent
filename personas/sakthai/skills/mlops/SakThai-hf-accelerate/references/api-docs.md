# Accelerate — API Reference Excerpts

Sourced from [Hugging Face Accelerate docs](https://huggingface.co/docs/accelerate/package_reference/accelerator) v1.14.0.

## Accelerator Constructor — Full API

```python
Accelerator(
    device_placement=True,
    mixed_precision=None,        # 'no'|'fp16'|'bf16'|'fp8'
    gradient_accumulation_steps=1,
    cpu=False,
    deepspeed_plugin=None,       # DeepSpeedPlugin or dict
    fsdp_plugin=None,            # FullyShardedDataParallelPlugin
    megatron_lm_plugin=None,
    rng_types=None,              # ['torch','cuda','xla','generator']
    log_with=None,               # 'tensorboard'|'wandb'|'all'|...
    project_dir=None,
    project_config=None,
    step_scheduler_with_optimizer=True,
    kwargs_handlers=None,
    dynamo_backend='no',
    dynamo_plugin=None,
    gradient_accumulation_plugin=None,
)
```

## Accelerate Launch CLI Config Options

### DeepSpeed Plugin (via `accelerate config`)

```
zero_stage:              0|1|2|3
gradient_accumulation_steps: int
gradient_clipping:       float
offload_optimizer_device: none|cpu|nvme
offload_param_device:    none|cpu|nvme
zero3_init_flag:         true|false
zero3_save_16bit_model:  true|false
mixed_precision:         no|fp16|bf16
deepspeed_moe_layer_cls_names: str (comma-sep)
deepspeed_hostfile:      str
deepspeed_exclusion_filter: str
deepspeed_inclusion_filter: str
deepspeed_multinode_launcher: pdsh|standard|openmpi|mvapich|mpich|slurm|nossh
```

### FSDP Plugin (via `accelerate config`)

```
fsdp_sharding_strategy:       1(FULL_SHARD)|2(SHARD_GRAD_OP)|3(NO_SHARD)|4(HYBRID_SHARD)|5(HYBRID_SHARD_ZERO2)
fsdp_offload_params:          true|false
fsdp_auto_wrap_policy:        TRANSFORMER_BASED_WRAP|SIZE_BASED_WRAP|NO_WRAP
fsdp_transformer_layer_cls_to_wrap: str (comma-sep class names)
fsdp_min_num_params:          int
fsdp_backward_prefetch_policy: BACKWARD_PRE|BACKWARD_POST|NO_PREFETCH
fsdp_forward_prefetch:        true|false
fsdp_state_dict_type:         FULL_STATE_DICT|LOCAL_STATE_DICT|SHARDED_STATE_DICT
fsdp_use_orig_params:         true|false
fsdp_cpu_ram_efficient_loading: true|false
fsdp_sync_module_states:      true|false
```

## Key Accelerator Properties

| Property | Returns |
|----------|---------|
| `accelerator.device` | `torch.device` |
| `accelerator.process_index` | `int` — global rank |
| `accelerator.local_process_index` | `int` — per-machine rank |
| `accelerator.num_processes` | `int` |
| `accelerator.is_main_process` | `bool` |
| `accelerator.is_local_main_process` | `bool` |
| `accelerator.distributed_type` | `DistributedType` enum |
| `accelerator.mixed_precision` | `str` |
| `accelerator.sync_gradients` | `bool` |
| `accelerator.optimizer_step_was_skipped` | `bool` |
| `accelerator.use_distributed` | `bool` |
| `accelerator.state` | `AcceleratorState` |

## Migration — Before/After By Feature

| Feature | Before (PyTorch) | After (Accelerate) |
|---------|-------------------|---------------------|
| Device setup | `device = "cuda"` / `model.to(device)` | `device = accelerator.device` / `accelerator.prepare()` handles placement |
| Backward pass | `loss.backward()` | `accelerator.backward(loss)` |
| Gradient clipping | `torch.nn.utils.clip_grad_norm_()` | `accelerator.clip_grad_norm_()` (gate with `accelerator.sync_gradients`) |
| Gradient accumulation | Manual tracking loop | `with accelerator.accumulate(model):` |
| Mixed precision | `torch.cuda.amp.autocast()` | `with accelerator.autocast():` |
| DataParallel/DDP | Wrapper class | `accelerator.prepare()` auto-detects |
| Model saving | `torch.save(model.state_dict())` | `accelerator.unwrap_model(model).save_pretrained()` |
| Checkpoint | Manual state tracking | `accelerator.save_state()` / `accelerator.load_state()` |
| Experiment logging | Manual logger setup | `accelerator.init_trackers()` / `accelerator.log()` |
