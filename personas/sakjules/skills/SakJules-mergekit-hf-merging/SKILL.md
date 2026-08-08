---
name: SakJules-mergekit-hf-merging
description: "MergeKit — complete model merging toolkit for combining LLMs on the Hugging Face Hub. Expanded deep-dive: all 17+ merge methods, MoE conversion (mergekit-moe), evolutionary search (mergekit-evolve), multi-stage merging (mergekit-multi), raw PyTorch m"
---

# MergeKit — Complete Reference (v2.0 Deep-Dive)

Deep reference covering all MergeKit operations for combining LLMs and uploading to the Hugging Face Hub.

## 1. Installation

```bash
git clone https://github.com/arcee-ai/mergekit.git
cd mergekit
pip install -e .                     # basic install
pip install -e .[evolve,vllm]        # with evolutionary search
```

All operations are zero-cost (CPU-only) or GPU-accelerated with ≥8 GB VRAM.

## 2. Merge Methods — Complete Taxonomy (17+)

### Basic
| Method | Inputs | Base? | Core Idea |
|--------|--------|-------|-----------|
| **Linear** | ≥2 | - | Weighted average of parameters (model soups) |
| **Passthrough** | 1 | - | Direct tensor copy (frankenmerging/layer stacking) |

### Spherical Interpolation
| Method | Inputs | Base? | Core Idea |
|--------|--------|-------|-----------|
| **SLERP** | 2 | ✓ | Spherical linear interpolation on hypersphere (`t` param) |
| **NuSLERP** | 2 | \* | Enhanced SLERP with flexible weighting, row/column-wise modes |
| **Multi-SLERP** | ≥2 | \* | Barycentric SLERP for >2 models (tangent space projection) |
| **Karcher Mean** | ≥2 | - | Riemannian barycenter on manifolds (geometric averaging) |

### Task Vector Methods
| Method | Inputs | Base? | Core Idea |
|--------|--------|-------|-----------|
| **Task Arithmetic** | ≥2 | ✓ | Linear combination of task vectors (deltas from base) |
| **TIES** | ≥2 | ✓ | Task arithmetic + sparsification + sign consensus |
| **DARE** | ≥2 | ✓ | Task arithmetic + random pruning + rescaling |
| **DELLA** | ≥2 | ✓ | Adaptive magnitude-based pruning (density ± epsilon per row) |
| **Model Breadcrumbs** | ≥2 | ✓ | Outlier removal (both small & large diffs), gamma+density params |
| **SCE** | ≥2 | ✓ | Adaptive matrix-level weighting by parameter variance + sign consensus |
| **RAM** | ≥2 | ✓ | Per-parameter classification: inactive/unique/shared (RL agents) |

### Specialized
| Method | Inputs | Base? | Core Idea |
|--------|--------|-------|-----------|
| **Model Stock** | ≥3 | ✓ | Geometric weight calculation for linear interpolation |
| **Nearswap** | 2 | ✓ | Interpolate only where parameters are similar |
| **Arcee Fusion** | 2 | ✓ | Dynamic thresholding for fusing important changes |

## 3. YAML Configuration

### Slices Mode — piecewise layer assembly:
```yaml
merge_method: slerp
slices:
  - model: model1
  - model: model2
    parameters:
      weight: 0.5
parameters:
  t: 0.5
```

### Models Mode — entire models as inputs:
```yaml
merge_method: ties
base_model: mistralai/Mistral-7B-v0.1
models:
  - model: model1
    parameters:
      weight: 1.0
      density: 0.5
  - model: model2
    parameters:
      weight: 0.5
      density: 0.3
dtype: bfloat16
tokenizer:
  source: union
```

### Fine-Grained Parameter Control with Tensor Name Filters

Parameters can be set at **four precedence levels** (highest first):

1. `slices.*.sources.parameters` — specific input slice
2. `slices.*.parameters` — specific output slice
3. `models.*.parameters` — tensors from specific input models
4. `parameters` — catchall (lowest precedence)

**Tensor name filters** allow different parameters for attention vs. MLP layers:

```yaml
parameters:
  normalize: true
  tensors:
    - filter: self_attn
      weight: 0.3   # applies only to attention projections
    - filter: mlp
      weight: 0.7   # applies only to feed-forward layers
```

**Gradient interpolation** for per-layer-varying weights:
```yaml
parameters:
  weight: [1.0, 0.8, 0.6, 0.4, 0.2, 0.0]
```
A gradient with N values automatically interpolates across N equally-sized groups of layers.

### Tokenizer Configuration

**Modern `tokenizer` field** (recommended — mutually exclusive with `tokenizer_source`):

```yaml
tokenizer:
  source: "union"            # union|base|<path/to/model>
  tokens:                    # optional: override specific token embeddings
    <|im_start|>:
      source: "path/to/chatml/model"
    <|special|>:
      source: "path/to/model"
      force: true
  pad_to_multiple_of: null   # optional: pad vocab size
```

**Embedding fallback rules**: When a model lacks a token from the merged vocabulary:
1. Use base model's embedding if it has the token
2. If only one model has it, use that model's
3. Otherwise, average all available embeddings

**Legacy `tokenizer_source`** (deprecated but maintained):
```yaml
tokenizer_source: "union"  # union|base|<path>
```

## 4. Execution

```bash
# Basic merge (CPU, zero-cost)
mergekit-yaml ./config.yml ./merged-model --lazy-unpickle --allow-crimes

# GPU-accelerated
mergekit-yaml ./config.yml ./merged-model --cuda

# With sharding for Hub upload
mergekit-yaml ./config.yml ./merged-model --cuda --out-shard-size 9.9B

# Upload to Hugging Face Hub
huggingface-cli login
huggingface-cli upload your_ns/merged-model ./merged-model .
```

Key flags: `--lazy-unpickle` (low memory), `--allow-crimes` (relax strict checks), `--trust-remote-code` (custom architectures), `--load-in-8bit`/`--load-in-4bit` (quantized loading).

## 5. Advanced: mergekit-moe — Dense-to-MoE Conversion

Converts dense models into Mixtral/DeepSeek/Qwen MoE architectures.

### YAML Configuration
```yaml
base_model: path/to/self_attn_donor
gate_mode: hidden          # hidden|cheap_embed|random
dtype: bfloat16
experts:
  - source_model: expert_model_1
    positive_prompts:
      - "This prompt demonstrates what expert_model_1 excels at"
    # negative_prompts:
    #   - "What expert_model_1 should NOT be used for"
  - source_model: expert_model_2
    # ...
# Optional shared expert (Qwen MoE)
shared_experts:
  - source_model: model_name
    positive_prompts:
      - "shared task description"
    residual_scale: 0.1     # prevent overcooking
```

### Gate Modes
- **`hidden`** (default, best): Uses hidden state representations of prompts for gate params. Use `--load-in-8bit`/`--load-in-4bit` for constrained VRAM.
- **`cheap_embed`**: Uses raw token embeddings only — same gate params for every layer. Lower quality but runs on minimal hardware.
- **`random`**: Random initialization — for sparse upcycling or further training.

### Execution
```bash
mergekit-moe ./config.yml ./my-moe-model
```

Architecture auto-inferred from input models, or explicitly set with `architecture: qwen|mixtral|deepseek`.

### Sparse Upcycling Example (8x same model):
```yaml
base_model: BEE-spoke-data/smol_llama-220M-GQA
gate_mode: random
dtype: bfloat16
experts:
  - source_model: BEE-spoke-data/smol_llama-220M-GQA  # repeat 8x
  # ... (7 more)
```

## 6. Advanced: mergekit-evolve — Evolutionary Merge Optimization

Uses CMA-ES (Covariance Matrix Adaptation Evolution Strategy) to optimize merge parameters against evaluation benchmarks.

### Installation
```bash
pip install -e .[evolve,vllm]
```

### YAML Configuration
```yaml
genome:
    models:
      - model_1
      - model_2
    merge_method: dare_ties
    base_model: base_model_if_needed
    tokenizer_source: null
    layer_granularity: 8       # params per N-layer slice
    normalize: false
    allow_negative_weights: false
    smooth: false               # interpolate params across layers
    filters:
      - self_attn               # separate params for attn vs mlp
      - mlp
tasks:
  - name: hellaswag
    weight: 1.0
    metric: "acc,none"
  - name: truthfulqa_mc
    weight: 0.5
```

### Running
```bash
mergekit-evolve --strategy pool --storage-path /path/to/storage ./config.yml
```

**Scheduling Strategies:**
- `pool` (default): One actor per GPU, safe for all configs
- `buffered`: Concurrent merge+evaluate on same GPU (single-node + fast FS)
- `serial`: Ray placement groups

**Key Options:**
- `--vllm`: Use vLLM backend instead of Hugging Face
- `--in-memory`: Keep model resident (faster, more RAM)
- `--max-fevals 100`: Max merges to evaluate
- `--wandb`: Log to Weights & Biases
- `--task-search-path`: Custom LM Eval Harness tasks

**Output:** `best_config.yaml` written to storage path with optimal merge parameters.

## 7. Advanced: mergekit-multi — Multi-Stage Merging

Chains multiple merge operations where later stages consume earlier outputs.

### Configuration (YAML with `---` separators)
```yaml
name: first-merge
merge_method: linear
models:
  - model: model_A
  - model: model_B
parameters:
  weight: 0.5
---
name: second-merge
merge_method: slerp
base_model: first-merge          # reference by name
models:
  - model: model_C
parameters:
  t: 0.5
---
# Final merge (no name — becomes output)
merge_method: dare_ties
base_model: mistralai/Mistral-7B-v0.1
models:
  - model: second-merge          # chain reference
    parameters:
      density: 0.6
      weight: 0.5
```

### Execution
```bash
mergekit-multi ./multimerge.yaml \
  --intermediate-dir ./intermediates \
  --out-path ./final-merge
```

Key options: `--lazy`/`--no-lazy` (skip cached intermediates), `--cuda`, `--out-shard-size`.

## 8. Advanced: mergekit-pytorch — Raw PyTorch Merging

For merging **non-Transformers** PyTorch models (arbitrary `.pt`/`.safetensors` checkpoints). Same algorithms but no layer slicing or tokenizer support.

### Example Config
```yaml
merge_method: slerp
models:
  - model: /path/to/model1.pt
  - model: /path/to/model2.pt
dtype: float32
parameters:
  t: 0.5
```

### Usage
```bash
mergekit-pytorch ./raw_config.yml ./output_dir [options]
```

## 9. Advanced: mergekit-extract-lora — LoRA Extraction

Extracts PEFT-compatible low-rank approximations from fine-tuned models via SVD decomposition of the delta (fine-tuned − base).

### Usage
```bash
mergekit-extract-lora \
  --model ./fine-tuned-model \
  --base-model ./base-model \
  --out-path ./lora-adapter \
  --max-rank 128 \
  --distribute-scale
```

**Options:**
- `--max-rank 128`: Maximum rank for LoRA decomposition
- `--distribute-scale/--no-distribute-scale`: Scale distribution between A and B
- `--embed-lora/--no-embed-lora`: LoRA for embeddings vs. modules_to_save
- `--save-module`: Keep specific modules at full rank
- `--exclude-regex` / `--include-regex`: Module filtering
- `--sv-epsilon 0`: Threshold for discarding singular values

## 10. Advanced: mergekit-tokensurgeon — Tokenizer Transplantation

Aligns vocabulary between models for speculative decoding or cross-tokenizer distillation.

### Usage
```bash
mergekit-tokensurgeon --base-model ./model_A --target-model ./model_B --output ./model_B_with_A_vocab
```

Use cases:
- Produce draft models for **speculative decoding** (same tokenizer as target)
- **Cross-tokenizer knowledge distillation**
- Migrate fine-tuned weights to a different tokenizer

## 11. Zero-Cost Operation

- **Entirely CPU-runnable**: `--lazy-unpickle` loads tensors lazily; no GPU needed
- **No inference credits consumed**: merging is local computation, no HF Inference calls
- **Free Hub uploads**: the HF Hub hosts merged models at zero cost
- **Recommended for Beer's hardware**: works with 0.5B (380 MB) and 1.5B (934 MB) GGUF models; use `--allow-crimes` for CPU-only on small models

## 12. Hub Upload & Model Card

MergeKit auto-generates a `README.md` with merge metadata. Edit before uploading:
```bash
huggingface-cli login
huggingface-cli upload your_ns/merged-model ./merged-model .
```

*See [docs/merge_methods.md](https://github.com/arcee-ai/mergekit/blob/main/docs/merge_methods.md) for complete method specifications.*

## References
- MergeKit GitHub: https://github.com/arcee-ai/mergekit
- MergeKit README: https://github.com/arcee-ai/mergekit/blob/main/README.md
- Merge Methods Guide: https://github.com/arcee-ai/mergekit/blob/main/docs/merge_methods.md
- MoE Merging: https://github.com/arcee-ai/mergekit/blob/main/docs/moe.md
- Multi-Stage Merging: https://github.com/arcee-ai/mergekit/blob/main/docs/multimerge.md
- Evolutionary Merge: https://github.com/arcee-ai/mergekit/blob/main/docs/evolve.md
- EMNLP Paper: https://aclanthology.org/2024.emnlp-industry.36/
- FrankenSteinAI (hosted UI): https://frankenstein-ai.com/
