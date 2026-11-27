# Nanotron 3D Training, Nanosets & Optimization

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
