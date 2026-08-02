# HF Learnings — PEFT LoRA Deep Dive

## 2026-07-24: hf-peft-lora-deep-dive — All LoRA Variants, Initialization Methods, Advanced Training Patterns (PEFT v0.20.0)

### Summary
Comprehensive deep dive into Hugging Face PEFT v0.20.0 covering all LoRA initialization strategies (PiSSA, OLoRA, EVA, LoRA-GA, MiCA, CorDA, LoftQ), advanced training features (rsLoRA, DoRA, layer replication, KappaTune, trainable token indices, weight tying), MoE expert parameter targeting, multi-adapter management, merging patterns, and the full LoraConfig API. This is a go-deeper companion to the existing hf-peft-lora skill.

### Source
- PEFT v0.20.0 docs: https://huggingface.co/docs/peft/en/index
- LoRA reference: https://huggingface.co/docs/peft/en/package_reference/lora
- Quicktour: https://huggingface.co/docs/peft/en/quicktour
- Method overview: https://huggingface.co/docs/peft/en/methods/overview

---

## 1. PEFT Architecture (v0.20.0)

PEFT v0.20.0 ships with **32+ adapter methods** organized into three categories:

| Category | Methods | Description |
|---|---|---|
| **Prompt-based** | Prompt Tuning, P-Tuning, Prefix Tuning, Llama-Adapter, Multitask Prompt Tuning | Learnable soft tokens prepended to input |
| **Layer Tuning** | LayerNorm Tuning, Trainable Tokens, BEFT | Targets specific layer types |
| **Adapter** | LoRA (+ variants), AdaLoRA, LoHa, LoKr, OFT, BOFT, IA3, VeRA, VB-LoRA, X-LoRA, Poly, MiSS, HRA, HiRA, C3A, DEFT, DeLoRA, FourierFT, GraLoRA, Lily, OSF, PEANuT, PSOFT, PVeRA, RandLora, RoAd, SHiRA, TinyLoRA, UniLoRA, WaveFT, MiCA, CorDA | Small trainable matrices injected into frozen base model |

## 2. LoraConfig — Complete Parameter Reference

```python
from peft import LoraConfig

config = LoraConfig(
    # Core LoRA parameters
    r=8,                           # Rank of update matrices
    lora_alpha=32,                 # Scaling factor (alpha/r applied during forward)
    target_modules=["q_proj", "v_proj"],  # Module names to attach LoRA to
    lora_dropout=0.1,              # Dropout for LoRA layers

    # Bias handling
    bias="none",                   # "none" | "all" | "lora_only"

    # Initialization
    init_lora_weights="gaussian",  # "gaussian" | "olora" | "pissa" | "pissa_niter_4" |
                                   # "loftq" | "corda" | "eva" | "mica" | "false"

    # Variants
    use_dora=False,                # Set True for DoRA (Weight-Decomposed Low-Rank Adaptation)
    use_rslora=False,              # Set True for rank-stabilized LoRA (scaling = alpha/sqrt(r))

    # Fine-grained control
    rank_pattern={},               # Per-layer rank overrides (dict of module_name_pattern: rank)
    alpha_pattern={},              # Per-layer alpha overrides

    # Modules to fully train (not just LoRA adapt them)
    modules_to_save=[],            # e.g., ["classifier", "embed_tokens"]

    # Advanced
    layers_to_transform=None,      # Specific layer indices to apply LoRA to
    layers_pattern=None,           # Layer name pattern (e.g., "h.{id}")

    # Layer replication (SOLAR-style expansion)
    layer_replication=None,        # e.g., [[0,4], [2,5]] to expand layer count

    # Trainable token indices (efficient embedding tuning)
    trainable_token_indices=None,  # List of indices or dict {"embed_layer": [indices]}

    # MoE expert parameter targeting
    target_parameters=None,        # e.g., ["mlp.experts.gate_up_proj"]

    # Memory-efficient initialization
    loqtq_kwargs=None,             # LoftQ init kwargs
    corda_config=None,             # CorDA init config

    # Weight tying
    ensure_weight_tying=True,      # Maintain tied weights for embed_tokens/lm_head

    # EVA config
    eva_config=None,               # EvaConfig instance

    # Task type (helps auto-save relevant layers)
    task_type=TaskType.CAUSAL_LM,  # From peft.TaskType enum
)
```

## 3. LoRA Initialization Methods

PEFT v0.20.0 supports **12 initialization strategies** for LoRA weights, controlled via `init_lora_weights`:

### 3.1 Default / Gaussian — `"gaussian"` or `"kaiming"`

- **Default**: Weight A initialized with Kaiming-uniform, weight B with zeros (identity transform at init)
- **Gaussian**: Weight A initialized with Gaussian distribution, weight B with zeros (Diffusers-style)
- **`False`**: Debug/test — no identity transform initialization

```python
config = LoraConfig(init_lora_weights="gaussian", r=8, ...)
```

### 3.2 PiSSA — `"pissa"` or `"pissa_niter_[N]"`

**Paper**: https://huggingface.co/papers/2404.02948

Uses **principal singular values and singular vectors** (SVD) to initialize LoRA adapters. The base weight is mutated by subtracting the rank-r SVD approximation, preserving the original output.

- `"pissa"` — full SVD, may take several minutes on large models
- `"pissa_niter_4"` — fast randomized SVD with 4 iterations (seconds vs minutes)

```python
config = LoraConfig(init_lora_weights="pissa", r=16, ...)
# Fast version:
config = LoraConfig(init_lora_weights="pissa_niter_4", r=16, ...)
```

**Benefits**: Faster convergence, better final performance, reduces quantization error in QLoRA.

### 3.3 OLoRA — `"olora"`

**Paper**: https://huggingface.co/papers/2406.01775

Uses **QR decomposition** to translate base weights before training. Mutates the base model weights by a factor of their QR decompositions.

```python
config = LoraConfig(init_lora_weights="olora", r=16, ...)
```

**Benefits**: Improved stability, accelerated convergence, superior final performance.

### 3.4 EVA — `"eva"`

**Paper**: https://huggingface.co/papers/2410.07170

**E**xplained **V**ariance **A**daptation — data-driven initialization:
1. Performs SVD on input activations of each layer
2. Uses right-singular vectors to initialize LoRA weights
3. **Adaptively allocates ranks across layers** based on explained variance ratio

Requires an additional initialization step with a dataloader:

```python
from peft import LoraConfig, EvaConfig, get_peft_model
from peft.tuners.lora import initialize_lora_eva_weights

config = LoraConfig(
    init_lora_weights="eva",
    eva_config=EvaConfig(rho=2.0),  # rho ≥ 1.0 controls redistribution
    r=16,
    target_modules=["q_proj", "v_proj"],
)
peft_model = get_peft_model(model, config, low_cpu_mem_usage=True)
initialize_lora_eva_weights(peft_model, dataloader)  # Run on GPU for speed
```

**Note**: `rho=1.0` disables redistribution (exactly r ranks per layer). `rho=2.0` allows up to 2r ranks.

### 3.5 MiCA — `"mica"`

**Paper**: https://arxiv.org/abs/2604.01694

**Mi**nor **C**omponent **A**daptation — complements PiSSA by using the **minor** (smallest) singular components instead of principal ones:

```
W = U Σ V^T
B = U[:, -r:]  # left singular vectors associated with smallest singular values
A = 0           # only A is trained; B is frozen
```

```python
config = LoraConfig(
    init_lora_weights="mica",
    r=16,
    target_modules=["q_proj", "v_proj"],
)
```

**Benefits**: Half the trainable parameters of LoRA (only A trained), preserves base output exactly at step 0 (no residual subtraction needed). Best for **continued pretraining / domain-adaptive pretraining** — use base model, not instruction-tuned checkpoint.

**Constraints**: `r <= min(in_features, out_features)` for Linear, `r <= min(num_embeddings, embedding_dim)` for Embedding.

### 3.6 CorDA — `"corda"`

**Paper**: https://huggingface.co/papers/2406.05223

Context-oriented Decomposition Adaptation — task-aware initialization:

- **IPM** (Instruction-Previewed Mode): Focus on downstream task — faster convergence, better fine-tuning
- **KPM** (Knowledge-Preserved Mode): Maintain world knowledge — mitigates catastrophic forgetting

```python
from peft import LoraConfig, CordaConfig
import torch

config = LoraConfig(
    init_lora_weights="corda",
    corda_config=CordaConfig(corda_method="kpm"),  # or "ipm"
)
preprocess_corda(model, config, run_model=run_model)
peft_model = get_peft_model(model, config)
```

Requires a `run_model` callback to collect covariance matrices from data.

### 3.7 LoftQ — (via `loftq_kwargs`)

**Paper**: https://huggingface.co/papers/2310.08659

LoRA-Fine-Tuning-aware Quantization — minimizes quantization error when using QLoRA. LoRA weights are initialized to compensate for quantization loss.

```python
config = LoraConfig(
    r=16,
    loftq_kwargs={"loftq_config": LoftQConfig(loftq_bits=4, ...)},
)
```

Follow: https://github.com/huggingface/peft/tree/main/examples/loftq_finetuning

### 3.8 LoRA-GA — `"loraga"` (via preprocess function)

**Paper**: https://huggingface.co/papers/2407.05000

**Lo**RA with **G**radient **A**pproximation — initializes adapter weights by SVD on estimated gradients, aligning closer to full fine-tuning.

```python
from peft.tuners.lora import preprocess_loraga

def train_step():
    for _ in range(64):  # 64-128 batches for gradient estimation
        batch = next(dataloader_iter)
        outputs = model(**batch)
        outputs.loss.backward()

preprocess_loraga(model, lora_config, train_step)
```

**Direction strategies** (via `LoraConfig(lora_ga_direction="ArB2r")`):
- `"ArBr"`, `"A2rBr"`, `"ArB2r"` (default), `"random"`

**Scaling strategies** (via `LoraConfig(lora_ga_scale="stable")`):
- `"stable"` (default), `"weight_svd"`, `"gd_scale"`, `"unit"`

**Note**: Requires full precision, no quantization. Modifies base weights (use `save_mutated_as_lora` pattern).

### 3.9 rsLoRA — `use_rslora=True`

**Paper**: https://huggingface.co/papers/2312.03732

**R**ank-**S**tabilized LoRA — changes scaling from `alpha/r` to `alpha/sqrt(r)`, stabilizing higher ranks.

```python
config = LoraConfig(use_rslora=True, r=64, lora_alpha=32)
```

**Benefit**: Enables effective use of much higher ranks (up to 256+) without training collapse.

### 3.10 KappaTune — Automatic Target Module Selection

**Paper**: https://arxiv.org/abs/2506.16289

Condition-number-based target selection. Computes matrix condition number κ = σ_max / σ_min for each `nn.Linear` module and selects the most isotropic layers (lowest κ) — these absorb new information more readily.

```python
from peft.helpers import find_kappa_target_modules

targets = find_kappa_target_modules(model, top_p=0.2)
config = LoraConfig(
    target_modules=targets["target_modules"],
    r=64,
    lora_alpha=32,
)
```

Also supports MoE expert parameters (3D `nn.Parameter` tensors like Llama-4, Qwen3-MoE).

## 4. Advanced Training Features

### 4.1 DoRA — `use_dora=True`

**Paper**: https://huggingface.co/papers/2402.09353

**D**irection **o**riented **R**ank **A**daptation — decomposes weight updates into **magnitude** and **direction** components. Learns a separate magnitude vector alongside the LoRA low-rank update.

```python
config = LoraConfig(use_dora=True, r=16, ...)
```

**Benefits**: Better alignment with full fine-tuning direction, often outperforms standard LoRA at same rank.

### 4.2 Layer Replication (SOLAR-style Expansion)

Duplicates model layers to build larger models from pretrained ones (e.g., 7B → 10B as in SOLAR paper). Replicated layers share underlying weights but get distinct LoRA adapters.

```python
# Original model layers: [0, 1, 2, 3, 4]
# Replicated model layers: [0, 1, 2, 3, 2, 3, 4]
config = LoraConfig(layer_replication=[[0, 4], [2, 5]], ...)
```

Each range is [start, end) — Python slice convention. Used by models like `abacusai/Fewshot-Metamath-OrcaVicuna-Mistral-10B`.

### 4.3 Fine-grained Rank/Alpha Control

Override rank and alpha per layer using `rank_pattern` and `alpha_pattern` with regex keys:

```python
config = LoraConfig(
    r=16,
    rank_pattern={
        "q_proj": 8,                # Lower rank for query
        "v_proj": 4,                # Lower rank for value
        "^model.layers.0\\.*": 32,  # Higher rank for first layer
    },
    alpha_pattern={"v_proj": 16},  # Different scaling for value
    ...
)
```

Regex rules: `^` matches start of module name, PEFT auto-adds `$` at end.

### 4.4 Trainable Token Indices

Efficiently train only specific token embeddings alongside LoRA, saving VRAM vs full embedding fine-tuning:

```python
special_tokens = ['<|start_think|>', '<|stop_think|>']
tokenizer.add_special_tokens({'additional_special_tokens': special_tokens})
model.resize_token_embeddings(len(tokenizer))

config = LoraConfig(
    target_modules="all-linear",
    trainable_token_indices={
        'embed_tokens': tokenizer.convert_tokens_to_ids(special_tokens)
    },
)
```

**VRAM savings** (Mistral-7B, 6 tokens): 15,562 MB (trainable tokens) vs ~16,500 MB (full embedding) vs 15,581 MB (LoRA on embedding).

### 4.5 QLoRA-style — `target_modules="all-linear"`

Instead of specifying individual modules, target all linear layers:

```python
config = LoraConfig(target_modules="all-linear", r=16, ...)
```

This is the standard QLoRA configuration — matches the original QLoRA paper which applies LoRA to every linear projection.

### 4.6 Weight Tying — `ensure_weight_tying=True`

Many causal LMs share weights between `embed_tokens` and `lm_head`. This flag ensures adapter-side updates remain tied for these layers.

```python
config = LoraConfig(
    modules_to_save=["embed_tokens"],
    ensure_weight_tying=True,  # Default
)
```

When True and weights are tied, PEFT wraps both layers in a single `ModulesToSaveWrapper`. When False, they're treated as separate trainable parameters.

## 5. Multi-Adapter Management

```python
# Start with default adapter
peft_model = get_peft_model(model, config)

# Add more adapters
peft_model.add_adapter("math-lora")
peft_model.add_adapter("code-lora")

# Switch active adapter
peft_model.set_adapter("code-lora")

# Disable adapter (use base model only)
peft_model.disable_adapter_layers()

# Re-enable
peft_model.enable_adapter_layers()

# Delete adapter
peft_model.delete_adapter("math-lora")

# List adapters
peft_model.active_adapter
peft_model.peft_config  # dict of adapter_name -> config
```

### Mixed Adapter Inference
PEFT supports combining multiple adapters during inference via linear interpolation:

```python
peft_model.set_adapter("adapter1")
weights = [0.7, 0.3]
# Note: This requires additional API or can be done by merging
```

## 6. Adapter Merging Patterns

```python
# Merge adapter weights into base model (keeps adapter architecture)
peft_model.merge_adapter()

# Merge and unload (removes PEFT wrapper entirely)
merged_model = peft_model.merge_and_unload()

# For specific adapters only
peft_model.merge_adapter(["adapter1", "adapter2"])

# In-place weight combination without merging
# (useful for multi-adapter serving with task arithmetic)
for name, weight in [("code-lora", 0.8), ("math-lora", 0.2)]:
    # Use model.add_weighted_adapter for TIES/DARE merging
    pass
```

**Recommendation for MoE inference**: Always `merge_and_unload()` to avoid PEFT overhead per expert activation.

## 7. MoE Expert Parameter Targeting

For models with MoE expert weights stored as 3D `nn.Parameter` tensors (Llama-4, Qwen3-MoE, Mixtral):

```python
num_experts = getattr(model.config, "num_local_experts", None) or model.config.num_experts
effective_r = max(1, r // num_experts)  # Keep total param budget similar

config = LoraConfig(
    r=r,
    target_modules=["q_proj", "v_proj"],
    target_parameters=[
        "mlp.experts.gate_up_proj",
        "mlp.experts.down_proj",
        # Llama-4: "feed_forward.experts.gate_up_proj"
    ],
    rank_pattern={
        "experts.gate_up_proj": effective_r,
        "experts.down_proj": effective_r,
    },
)
```

**Performance note**: PEFT materializes LoRA contribution for EVERY expert at each forward pass, even if only a few are activated. During inference with KV cache, this causes substantial slowdown. Always merge_and_unload() for production MoE inference.

## 8. Saving & Loading

```python
# Save adapter only (default - small, portable)
peft_model.save_pretrained("my-adapter")
# Creates: adapter_config.json, adapter_model.safetensors (few MB)

# Push to Hub
peft_model.push_to_hub("my-user/my-adapter")

# Load for inference
from peft import AutoPeftModelForCausalLM
model = AutoPeftModelForCausalLM.from_pretrained("ybelkada/opt-350m-lora")

# Load on top of base model
from peft import PeftModel
base = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-1B")
peft_model = PeftModel.from_pretrained(base, "my-user/my-adapter")

# Save mutated weights (for LoRA-GA, OLoRA, PiSSA that modify base weights)
peft_model.save_pretrained("output_dir", save_embedding_layers=True)
```

## 9. Key PEFT v0.20.0 Changes & New Methods

| Method | Status | Description |
|---|---|---|
| **MiCA** | New | Minor Component Adaptation — PiSSA complement using smallest singular vectors |
| **CorDA** | New | Context-oriented Decomposition Adaptation — task-aware init |
| **KappaTune** | New | Automatic target module selection via condition numbers |
| **Trainable Tokens** | New | Efficient token embedding training alongside LoRA |
| **Weight Tying** | New | `ensure_weight_tying` for tied embed/lm_head |
| **MoE Parameter Targeting** | New | `target_parameters` for 3D expert weights |
| **Layer Replication** | New | SOLAR-style expansion with LoRA |
| **DoRA + LoRA-GA** | Enhanced | Combining direction decomposition with gradient-aware init |

## 10. Best Practices

1. **Start simple**: Default init + `r=8` or `r=16`. Increase rank only if underfitting.
2. **High rank + rsLoRA**: For r≥64, always use `use_rslora=True` to prevent training collapse.
3. **QLoRA**: Use `target_modules="all-linear"` + 4-bit NF4 quantization for consumer GPU training.
4. **Fast convergence**: PiSSA (especially `pissa_niter_4`) gives faster convergence than default init.
5. **Domain adaptation**: MiCA for continued pre-training, EVA for adaptive rank allocation.
6. **Knowledge preservation**: CorDA KPM for mitigating catastrophic forgetting.
7. **Multi-adapter serving**: Merge and unload for production. Use `set_adapter` for multi-tenant demos.
8. **MoE models**: Always `merge_and_unload()` for inference. Set `effective_r = max(1, r // num_experts)` to keep param budget.
9. **Memory**: Use `trainable_token_indices` instead of `modules_to_save=["embed_tokens"]` to save VRAM.
10. **Reproducibility**: Set `init_lora_weights` explicitly rather than relying on defaults (may change across versions).
