# HF Learnings: Accelerate Composable Parallelism

## 2026-07-24: accelerate-composable-parallelism-deep-dive (Topic #120)

### Summary
Deep-dive into Hugging Face Accelerate v1.14.0's new composable parallelism system via `ParallelismConfig` — inspired by torchtitan's `ParallelDims`. This replaces the old `torch_tp_plugin` approach with a unified device-mesh-based framework supporting 2D (FSDP2 + TP), 3D (HSDP + TP/CP), and 4D (all dimensions: sharded DP + replicate DP + TP + CP/SP) parallelism configurations. All source-verified against the installed accelerate package.

### Core Architecture — ParallelismConfig

`ParallelismConfig` is a dataclass that describes the parallelism topology via dimension sizes:

```python
from accelerate import ParallelismConfig

config = ParallelismConfig(
    dp_replicate_size=1,   # DDP replicas (pure data parallel)
    dp_shard_size=8,       # FSDP sharded data parallel
    tp_size=4,             # tensor parallelism
    cp_size=1,             # context parallelism (future)
    cp_backend="torch",    # only "torch" currently supported
    sp_size=1,             # sequence parallelism (DeepSpeed Ulysses)
    sp_backend="deepspeed",# only "deepspeed" currently supported
)
```

Pass it to `Accelerator`:
```python
accelerator = Accelerator(parallelism_config=config)
```

### Dimension Name System

| Dim Name | Source | Meaning |
|----------|--------|---------|
| `dp_replicate` | `dp_replicate_size` | Pure DDP replication dimension |
| `dp_shard` | `dp_shard_size` | FSDP sharding dimension |
| `dp_shard_cp` | dp_shard + cp (flattened) | Joint FSDP+CP mesh (models are sharded across both) |
| `dp_cp` | dp_replicate + dp_shard + cp | Loss averaging across all data+context dims |
| `dp` | dp_replicate + dp_shard (flattened) | Aggregate data parallel dimension |
| `tp` | `tp_size` | Tensor parallelism |
| `cp` | `cp_size` | Context parallelism |
| `sp` | `sp_size` | Sequence parallelism |

### Parallelism Topologies (`dp_replicate_size` × `dp_shard_size`)

| Config | Pattern | Description |
|--------|---------|-------------|
| `dp_shard > 1, dp_replicate == 1` | Pure FSDP | Model fully sharded across dp_shard dimension |
| `dp_replicate > 1, dp_shard == 1` | ❌ Invalid with TP/CP | Pure DDP + TP not supported (must shard) |
| `dp_replicate > 1, dp_shard > 1` | HSDP (Hybrid Sharded DP) | Replicate DP on outer, FSDP shard on inner |
| `both == 1` | No DP | Single process or TP/CP only |

### Dimensionality Patterns

| Dimensions active | Name | Example Use Case |
|-------------------|------|------------------|
| dp_shard + tp | **2D (FSDP + TP)** | 32 GPUs: dp_shard=8, tp_size=4 |
| dp_shard + tp + cp | **3D (FSDP + TP + CP)** | 64 GPUs: dp_shard=8, tp=4, cp=2 |
| dp_shard + tp + sp | **3D (FSDP + TP + DeepSpeed SP)** | 64 GPUs: dp_shard=8, tp=4, sp=2 |
| dp_replicate + dp_shard + tp | **3D (HSDP + TP)** | 64 GPUs: dp_rep=2, dp_shard=8, tp=4 |
| all five | **4D (all)** | 128 GPUs: dp_rep=2, dp_shard=8, tp=4, cp/sp=2 |

### Validation Rules (from `__post_init__`)

1. **CP and SP are mutually exclusive** — cannot set both > 1 simultaneously
2. **TP or CP with pure DP (dp_replicate > 1, dp_shard == 1) is invalid** — must use FSDP (dp_shard > 1) as the foundation for composing with TP/CP
3. **Total size must match `num_processes`** — `dp_replicate * dp_shard * tp * cp * sp` must equal total GPUs (unless DeepSpeed SP handles groups globally)
4. **Minimum value per dimension is 1**
5. **Valid cp_backend values**: `"torch"` only (currently)
6. **Valid sp_backend values**: `"deepspeed"` only (currently)

### Handlers (Configuring Sub-Parallelism)

Each active parallelism dimension can be configured with a handler object:

#### TorchTensorParallelConfig

```python
from accelerate.utils import TorchTensorParallelConfig

tp_handler = TorchTensorParallelConfig(
    enable_async_tp=False  # reserved for future use
)
```

Requirements:
- PyTorch >= BETA_TP_AVAILABLE_PYTORCH_VERSION
- transformers >= BETA_TP_AVAILABLE_TRANSFORMERS_VERSION

Auto-created when `tp_size > 1` and no handler provided.

#### TorchContextParallelConfig

```python
from accelerate.utils import TorchContextParallelConfig

cp_handler = TorchContextParallelConfig(
    cp_comm_strategy="allgather"  # or "alltoall"
)
```

| Parameter | Options | Default | Description |
|-----------|---------|---------|-------------|
| `cp_comm_strategy` | `"allgather"`, `"alltoall"` | `"allgather"` | Communication strategy for context parallelism |

Auto-created when `cp_size > 1` and no handler provided.
Requirements: PyTorch >= BETA_CP_AVAILABLE_PYTORCH_VERSION (2.2+)

#### DeepSpeedSequenceParallelConfig

```python
from accelerate.utils import DeepSpeedSequenceParallelConfig

sp_handler = DeepSpeedSequenceParallelConfig(
    sp_seq_length=4096,         # Fixed sequence length
    sp_seq_length_is_variable=True,  # Variable-length batches
    sp_attn_implementation="flash_attention_2",  # or "sdpa", "flash_attention_3"
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sp_seq_length` | int or None | None | Fixed seq len (required if is_variable=False) |
| `sp_seq_length_is_variable` | bool | True | Handle variable-length batches |
| `sp_attn_implementation` | str or None | None | FA2, FA3, SDPA, or hub kernel (e.g. "kernels-community/flash-attn2") |

Default fallbacks from env vars:
- `PARALLELISM_CONFIG_SP_SEQ_LENGTH_IS_VARIABLE` (default "true")
- `PARALLELISM_CONFIG_SP_SEQ_LENGTH`
- `PARALLELISM_CONFIG_SP_ATTN_IMPLEMENTATION`

**Validation:**
- `"eager"` and `"flex_attention"` NOT supported for SP (raises ValueError)
- Hub-hosted kernels must contain "flash-attn" and have a "/" in the name

Auto-created when `sp_size > 1` and no handler provided.

### Custom Handler Assignment

```python
config = ParallelismConfig(
    dp_shard_size=8,
    tp_size=4,
    cp_size=2,
    tp_handler=TorchTensorParallelConfig(enable_async_tp=False),
    cp_handler=TorchContextParallelConfig(cp_comm_strategy="alltoall"),
)
```

If handler is set for a dimension with size=1, a warning is issued and the handler is ignored.

### Environment Variable Configuration

All `ParallelismConfig` fields can be set via environment variables, enabling SLURM/launcher integration without code changes:

| Env Var | Maps to | Default |
|---------|---------|---------|
| `PARALLELISM_CONFIG_DP_REPLICATE_SIZE` | `dp_replicate_size` | `"1"` |
| `PARALLELISM_CONFIG_DP_SHARD_SIZE` | `dp_shard_size` | `"1"` |
| `PARALLELISM_CONFIG_TP_SIZE` | `tp_size` | `"1"` |
| `PARALLELISM_CONFIG_CP_SIZE` | `cp_size` | `"1"` |
| `PARALLELISM_CONFIG_CP_BACKEND` | `cp_backend` | `"torch"` |
| `PARALLELISM_CONFIG_SP_SIZE` | `sp_size` | `"1"` |
| `PARALLELISM_CONFIG_SP_BACKEND` | `sp_backend` | `"deepspeed"` |
| `PARALLELISM_CONFIG_CP_COMM_STRATEGY` | cp_handler.cp_comm_strategy | `"allgather"` |
| `PARALLELISM_CONFIG_SP_SEQ_LENGTH` | sp_handler.sp_seq_length | None |
| `PARALLELISM_CONFIG_SP_SEQ_LENGTH_IS_VARIABLE` | sp_handler.sp_seq_length_is_variable | `"true"` |
| `PARALLELISM_CONFIG_SP_ATTN_IMPLEMENTATION` | sp_handler.sp_attn_implementation | None |

### Device Mesh Construction

When `Accelerator.__init__()` receives a `parallelism_config`, it calls:

```python
self.state.device_mesh = parallelism_config.get_device_mesh(self.device.type)
```

This builds a PyTorch `DeviceMesh` using `torch.distributed.init_device_mesh()` with canonical mesh dimension order:

```
dp_replicate → dp_shard → cp → sp → tp
```

**Flattened joint meshes** for FSDP:
- `["dp_replicate", "dp_shard"]` → flattened as `"dp"`
- `["dp_shard", "cp"]` → flattened as `"dp_shard_cp"`
- `["dp_replicate", "dp_shard", "cp"]` → flattened as `"dp_cp"`

**Sequence Parallel (DeepSpeed) exception:** When `sp_backend="deepspeed"` and `sp_size > 1`, device mesh creation is skipped entirely — DeepSpeed manages its own process groups globally via `initialize_sequence_parallel()`.

### Accessing Rank Information

```python
# After Accelerator init
acc = Accelerator(parallelism_config=config)

acc.tensor_parallel_rank       # → 0..tp_size-1 (or 0 if TP not enabled)
acc.data_parallel_rank         # → replicate dimension rank
acc.data_parallel_shard_rank   # → shard dimension rank

# Properties
acc.is_composable_parallelism_enabled  # True if FSDP2
acc.parallelism_config                # The config object
acc.torch_device_mesh                  # The PyTorch DeviceMesh
```

**Note:** `pipeline_parallel_rank` and `context_parallel_rank` both raise `NotImplementedError` — pipeline and context parallelism are reserved for future use in the rank API.

### FSDP2 Integration

The composable parallelism system requires **FSDP2** (FSDP version 2, native to PyTorch >= 2.2). Key differences from FSDP1:

| Feature | FSDP1 | FSDP2 (used by ParallelismConfig) |
|---------|-------|----------------------------------|
| Sharding strategy | Policy objects (`FULL_SHARD`, `SHARD_GRAD_OP`, `NO_SHARD`) | `dp_shard_size` dimension from device mesh |
| Composition | Manual wrapping or auto-wrap policy | Automatic via `dp_shard_cp` flattened mesh |
| TP integration | Not natively composable | Built-in via device mesh dimensions |
| Init | `FullyShardedDataParallel` wrapper | `fully_shard(model)` on the model |

`accelerator.is_fsdp2` property returns `True` when using FSDP2.

### Accelerator.prepare() with ParallelismConfig

When `prepare_model()` is called with a parallelism config:

1. **Deepspeed SP:** If `sp_backend="deepspeed"` and `sp_size > 1`, DeepSpeed process groups are set up
2. **TP (fsdp2):** If `tp_size > 1`, the model's `tp_size` attribute is validated against `parallelism_config.tp_size`. The model is expected to have TP applied before being passed to accelerator.
3. **Sequence parallelism** is configured via `sp_backend` and passes the handler's config to DeepSpeed

### Practical Patterns

#### Pattern 1: FSDP2 + TP (2D, 32 GPUs)

```python
from accelerate import Accelerator, ParallelismConfig

config = ParallelismConfig(
    dp_shard_size=8,
    tp_size=4,
)
acc = Accelerator(parallelism_config=config)

# Model should already have TP applied
# (e.g., via transformers' TensorParallelPreTrainedModel)
model = ...  # tp_size=4 applied
model = acc.prepare_model(model)
```

#### Pattern 2: HSDP + TP (3D, 64 GPUs)

```python
config = ParallelismConfig(
    dp_replicate_size=2,
    dp_shard_size=8,
    tp_size=4,
)
# Total: 2 × 8 × 4 = 64 GPUs
# Outer 2x DDP replicas, inner 8x FSDP shards, 4x TP per group
```

#### Pattern 3: FSDP + TP + DeepSpeed SP (3D, 64 GPUs)

```python
config = ParallelismConfig(
    dp_shard_size=8,
    tp_size=4,
    sp_size=2,
    sp_backend="deepspeed",
    sp_handler=DeepSpeedSequenceParallelConfig(
        sp_attn_implementation="flash_attention_2",
        sp_seq_length_is_variable=True,
    ),
)
```

#### Pattern 4: All Environment Variables (SLURM-friendly)

```bash
# In SLURM script or .env
export PARALLELISM_CONFIG_DP_SHARD_SIZE=8
export PARALLELISM_CONFIG_TP_SIZE=4
export PARALLELISM_CONFIG_SP_SIZE=2
export PARALLELISM_CONFIG_SP_BACKEND=deepspeed
export PARALLELISM_CONFIG_SP_ATTN_IMPLEMENTATION=flash_attention_2

# Then launch normally — no code changes needed
accelerate launch train.py
```

```python
# train.py — reads env vars automatically
from accelerate import Accelerator, ParallelismConfig
config = ParallelismConfig()  # all values from env
acc = Accelerator(parallelism_config=config)
```

#### Pattern 5: Checkpoint Save/Load with Device Mesh

```python
# Save (only one process per non-data-parallel group)
if acc.should_save_model:
    acc.save_model(model, "checkpoint.pt")

# Load
model = acc.prepare_model(model)
acc.load_state("checkpoint.pt")
```

The `should_save_model` property returns `True` for all ranks currently (due to pending optimization — see source comment about `save_safe_file` slowness).

### Key Insights

1. **ParallelismConfig replaces `torch_tp_plugin`** — The old `torch_tp_plugin` parameter is deprecated in favor of `parallelism_config`. If both are provided, `torch_tp_plugin` is ignored with a deprecation warning.

2. **FSDP2 + TP = the new standard** — The combo eliminates the need for manual `FullyShardedDataParallel` wrapping with policy objects. Device mesh dimensions handle everything.

3. **DeepSpeed SP bypasses device mesh** — DeepSpeed manages its own SP groups globally via `initialize_sequence_parallel()`. The device mesh is not built when DeepSpeed SP is active (avoids conflicts).

4. **CP and SP are mutually exclusive** — You cannot use both context parallelism and sequence parallelism simultaneously. Choose based on hardware: CP for dense GPU interconnects (NVLink), SP for large-scale multi-node where ring communication dominates.

5. **Handler auto-creation** simplifies setup — Just set `tp_size=4` and `TorchTensorParallelConfig()` is auto-created with defaults. Handlers only needed for non-default configuration.

6. **Validation catches topology errors early** — Common mistakes like combining TP with pure DDP (no FSDP sharding) are caught at Accelerator initialization time.

### Known Limitations (from source)

- `pipeline_parallel_rank` raises `NotImplementedError` — pipeline parallelism not yet supported
- `context_parallel_rank` raises `NotImplementedError` — CP rank API not exposed yet
- `enable_async_tp` in `TorchTensorParallelConfig` is accepted but warns "not supported"
- `should_save_model` currently returns `True` for all ranks (temporary workaround for slow `save_safe_file`)

### Resources
- Source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/accelerate/parallelism_config.py`
- Source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/accelerate/utils/dataclasses.py` (lines 2206–2313)
- Source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/accelerate/accelerator.py` (lines 454–476, 1887–1905)
- Accelerate docs: https://huggingface.co/docs/accelerate/en/index
- torchtitan ParallelDims: https://github.com/pytorch/torchtitan/blob/main/torchtitan/distributed/parallel_dims.py
- PyTorch DeviceMesh: https://pytorch.org/docs/stable/distributed.html#torch.distributed.device_mesh.DeviceMesh
- FSDP2 docs: https://pytorch.org/docs/stable/distributed.fsdp.html
