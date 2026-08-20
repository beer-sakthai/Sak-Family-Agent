---
name: SakThai-hf-peft-lora
description: "Deep dive into Hugging Face PEFT library — LoRA/QLoRA configuration, training, inference, multi-adapter management, merging, and Hub integration."
---

# HF PEFT — Parameter-Efficient Fine-Tuning with LoRA/QLoRA

PEFT (Parameter-Efficient Fine-Tuning) adapts large pretrained models by training a tiny fraction of parameters, making it possible to fine-tune LLMs and other large models on consumer hardware.

## When to Use

- User wants to "fine-tune a model without full fine-tuning"
- User asks about LoRA, QLoRA, DoRA, or adapter training
- User needs to attach a trained adapter to a base model for inference
- User wants to merge adapter weights back into the base model
- User wants to train multiple adapters on one base model and swap between them

## Prerequisites

```bash
pip install peft transformers accelerate datasets
# For QLoRA (4-bit quantization):
pip install bitsandbytes
```

## Core API Reference

### 1. Configuration

Every PEFT method starts with a config class. For LoRA:

```python
from peft import LoraConfig, TaskType

config = LoraConfig(
    r=8,                    # Rank of the update matrices (lower = fewer params)
    lora_alpha=32,          # Scaling factor (alpha / r = scaling)
    target_modules=["q_proj", "v_proj"],  # Which modules to attach LoRA to
    task_type=TaskType.CAUSAL_LM,  # Optional — helps auto-save relevant layers
    lora_dropout=0.1,       # Dropout for LoRA layers
    bias="none",            # "none" | "all" | "lora_only"
    use_dora=False,         # Set True for DoRA (Weight-Decomposed Low-Rank Adaptation)
    init_lora_weights="gaussian",  # "gaussian" | "olora" | "pissa" | "pissa_niter_4" | False
)
```

**Key config patterns by model architecture:**

| Architecture | Typical `target_modules` | TaskType |
|---|---|---|
| LLaMA / Mistral | `["q_proj", "k_proj", "v_proj", "o_proj"]` | `CAUSAL_LM` |
| GPT-2 / OPT | `["q_proj", "v_proj"]` | `CAUSAL_LM` |
| BERT | `["query", "value"]` | `SEQ_CLS` |
| Whisper | `["q_proj", "v_proj"]` | `SEQ_2_SEQ_LM` |
| ViT | `["query", "value"]` | `FEATURE_EXTRACTION` |

> **Tip:** If you're unsure which modules to target, load the model and inspect its named modules:
> `for name, _ in model.named_modules(): print(name)`

### 2. Create a PeftModel

```python
from peft import get_peft_model
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-1B")
peft_model = get_peft_model(model, config)
peft_model.print_trainable_parameters()
# output: trainable params: 524,288 || all params: 1,236,338,688 || trainable%: 0.0424
```

### 3. Training with Transformers Trainer

```python
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./my-lora-adapter",
    learning_rate=1e-3,
    per_device_train_batch_size=32,
    num_train_epochs=2,
    weight_decay=0.01,
    save_strategy="epoch",
)

trainer = Trainer(
    model=peft_model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
)
trainer.train()
```

### 4. Save / Upload Adapter

```python
# Save locally — only adapter weights (~6MB for 350M model)
peft_model.save_pretrained("./my-lora-adapter")

# Push to Hub
peft_model.push_to_hub("your-username/my-llama-adapter")
```

Both save only the PEFT adapter weights (`adapter_config.json` + `adapter_model.safetensors`), not the full base model.

### 5. Inference with Loaded Adapter

**Option A: AutoPeftModel (recommended — loads adapter + its base model from a PEFT-only repo)**

```python
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

peft_model = AutoPeftModelForCausalLM.from_pretrained("ybelkada/opt-350m-lora")
tokenizer = AutoTokenizer.from_pretrained("facebook/opt-350m")
inputs = tokenizer("Hello, how are you?", return_tensors="pt")
outputs = peft_model.generate(**inputs, max_new_tokens=50)
```

**Option B: PeftModel.from_pretrained (load adapter onto an existing base model)**

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-1B")
peft_model = PeftModel.from_pretrained(base_model, "your-username/my-llama-adapter")
```

### 6. Multi-Adapter Management

```python
# Add another adapter on the same base model
peft_model.add_adapter(adapter_name="math-expert", peft_config=math_config)

# Switch active adapter
peft_model.set_adapter("math-expert")

# Disable all adapters (revert to base model)
peft_model.disable_adapter_layers()

# Enable adapters again
peft_model.enable_adapter_layers()

# List all adapters
print(peft_model.peft_config.keys())  # dict_keys(['default', 'math-expert'])
```

### 7. Merging Adapter Weights

```python
# Merge LoRA weights into base model permanently
merged_model = peft_model.merge_and_unload()
merged_model.save_pretrained("./merged-model")
```

Useful for deployment — produces a single set of weights, no adapter needed at inference time.

### 8. QLoRA (4-bit Quantized LoRA)

Train with 4-bit base model to fit even larger models on consumer GPUs:

```python
from transformers import BitsAndBytesConfig, AutoModelForCausalLM
import torch

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-1B",
    quantization_config=bnb_config,
    device_map="auto",
)

peft_model = get_peft_model(model, lora_config)
# Now train — gradients only flow through LoRA params
```

### 9. Advanced Model Merging — TIES / DARE / Linear / SVD

PEFT v0.14+ supports **multi-adapter merging** using advanced methods that combine several fine-tuned adapters into one, giving the merged model the combined abilities of each individual adapter without additional training. This goes beyond simple `merge_and_unload()` (which only merges a single adapter into the base model).

**Supported `combination_type` values for `add_weighted_adapter()`:**

| Method | `combination_type` | Description |
|---|---|---|
| Linear | `"linear"` | Weighted average of adapter parameters |
| SVD | `"svd"` | Singular Value Decomposition-based merging |
| TIES | `"ties"` | Trim, Elect Sign, Merge — removes redundant params, resolves sign conflicts |
| DARE | `"dare_linear"` / `"dare_ties"` | Drop And REscale — randomly drops params, rescales remaining; pairs with Linear or TIES |
| Cat | `"cat"` | Concatenate adapters along the adapter dimension |

#### TIES-Merging (TrIm, Elect, and Merge)

[Paper: https://hf.co/papers/2306.01708](https://hf.co/papers/2306.01708)

A three-step method:
1. **Trim** — redundant parameters are trimmed (low-magnitude ones are dropped)
2. **Elect** — conflicting signs across adapters are resolved into an aggregated sign vector
3. **Merge** — parameters whose signs match the aggregate sign are averaged

This prevents redundant or sign-conflicting parameters from degrading the merged model.

#### DARE (Drop And REscale)

[Paper: https://hf.co/papers/2311.03099](https://hf.co/papers/2311.03099)

Works as a pre-processing step before Linear or TIES merging:
- **Drop** — randomly drops a fraction of parameters according to a `density` rate
- **REscale** — rescales remaining parameters to compensate

Use `combination_type="dare_linear"` or `combination_type="dare_ties"`. The `density` parameter controls the fraction of weights to keep (e.g., `0.2` = keep 20%).

#### Full Workflow: Merging 3 LoRA Adapters with TIES

```python
from peft import PeftConfig, PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 1. Load base model
config = PeftConfig.from_pretrained("smangrul/tinyllama_lora_norobots")
model = AutoModelForCausalLM.from_pretrained(
    config.base_model_name_or_path,
    load_in_4bit=True,
    device_map="auto"
).eval()
tokenizer = AutoTokenizer.from_pretrained("smangrul/tinyllama_lora_norobots")

# 2. Handle potential vocabulary size mismatches
model.config.vocab_size = 32005
model.resize_token_embeddings(32005)

# 3. Load the first adapter with PeftModel.from_pretrained
model = PeftModel.from_pretrained(
    model, "smangrul/tinyllama_lora_norobots", adapter_name="norobots"
)

# 4. Load additional adapters
_ = model.load_adapter("smangrul/tinyllama_lora_sql", adapter_name="sql")
_ = model.load_adapter("smangrul/tinyllama_lora_adcopy", adapter_name="adcopy")

# 5. Merge with TIES — set combination_type="ties" and specify density
adapters = ["norobots", "adcopy", "sql"]
weights = [2.0, 1.0, 1.0]        # weight > 1.0 typically works better
adapter_name = "merge"
density = 0.2                      # keep 20% of params per adapter
model.add_weighted_adapter(
    adapters, weights, adapter_name,
    combination_type="ties",
    density=density
)

# 6. Set the merged adapter as active
model.set_adapter("merge")

# 7. Inference with merged model
device = "cuda" if torch.cuda.is_available() else "cpu"
messages = [{"role": "user", "content": "Write an SQL query to find all users older than 30."}]
text = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
inputs = tokenizer(text, return_tensors="pt").to(device)
outputs = model.generate(**inputs, max_new_tokens=256, do_sample=True, top_p=0.95, temperature=0.2)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

#### Merging with DARE

```python
# DARE + Linear
model.add_weighted_adapter(
    adapters, weights, "dare_linear_merge",
    combination_type="dare_linear",
    density=0.5
)

# DARE + TIES
model.add_weighted_adapter(
    adapters, weights, "dare_ties_merge",
    combination_type="dare_ties",
    density=0.5
)
```

#### Merging (IA)³ Models (Linear Only)

For `IA3Model`, `add_weighted_adapter()` performs a linear weighted merge (no `combination_type` parameter). Weights should sum to 1.0 to preserve the model scale:

```python
adapters = ["adapter1", "adapter2", "adapter3"]
weights = [0.4, 0.3, 0.3]
model.add_weighted_adapter(adapters, weights, "merge")
model.set_adapter("merge")
```

#### Key Differences: `merge_and_unload()` vs `add_weighted_adapter()`

| Method | Purpose | Merges into base? | Multi-adapter? |
|---|---|---|---|
| `merge_and_unload()` | Merge single adapter permanently into base model weights | ✅ Yes | ❌ No (only active adapter) |
| `add_weighted_adapter()` | Combine multiple adapters into one new adapter (stays as PEFT layer) | ❌ No (stays as adapter) | ✅ Yes (TIES/DARE/Linear/SVD) |
| `merge_and_unload()` after `add_weighted_adapter()` | Merge the combined adapter permanently | ✅ Yes | ✅ Yes (two-step) |

> **Tip:** `add_weighted_adapter()` creates a *new adapter* on top of the base model. If you need a single set of weights for deployment, call `merge_and_unload()` after setting the merged adapter as active.

#### Pitfalls

- **Special tokens**: When merging fully trained models (not just LoRA adapters), each model may have added special tokens at the same embedding position. Use `model.resize_token_embeddings()` to resolve conflicts before merging.
- **Base model must match**: All adapters being merged must have been trained from the **same base model**. Mixing adapters from different base models will fail.
- **Weight values > 1.0** typically produce better results because they preserve the correct scale. Start with all weights at `1.0` as a default.
- **Density tradeoff**: Lower `density` = more aggressive trimming (faster, more memory-efficient) but may lose task-specific knowledge. Start with `density=0.5` and tune.
- **4-bit + merging**: TIES/DARE merging works on 4-bit models loaded with `bitsandbytes`, but the merged adapter must be saved separately (cannot `merge_and_unload()` a 4-bit model).
- **PEFT v0.14+ required**: TIES and DARE combination types were introduced in PEFT v0.14.0. Check your PEFT version with `import peft; print(peft.__version__)`.

### 10. DoRA — Weight-Decomposed Low-Rank Adaptation

DoRA (Weight-Decomposed Low-Rank Adaptation, [paper 2402.09353](https://huggingface.co/papers/2402.09353)) decomposes weight updates into **magnitude** and **direction** components. Direction uses standard LoRA, while magnitude gets a separate learnable parameter. This improves LoRA quality especially at low ranks.

#### API — Single flag

```python
from peft import LoraConfig

config = LoraConfig(use_dora=True, ...)  # That's it — everything else is same as LoRA
```

No other config changes needed. Dropout, target_modules, rank, alpha all work identically to LoRA.

#### Ephemeral GPU offload (speed boost for offloaded adapters)

When parts of the model or DoRA adapter are offloaded to CPU, enable ephemeral GPU offload to temporarily move activations back to GPU for forward/backward:

```python
from peft import LoraConfig, LoraRuntimeConfig

config = LoraConfig(
    use_dora=True,
    runtime_config=LoraRuntimeConfig(ephemeral_gpu_offload=True),
    ...
)
```

Also supported when loading a pretrained DoRA adapter:

```python
from peft import PeftModel
model = PeftModel.from_pretrained(base_model, peft_model_id, ephemeral_gpu_offload=True)
```

#### Inference optimization — `DoraCaching`

DoRA is automatically optimized for `eval()` mode or when `lora_dropout=0` (reuses base model results for speed). For further speed at the cost of memory, use the `DoraCaching` helper:

```python
from peft.helpers import DoraCaching

model.eval()
with DoraCaching():
    output = model(inputs)
```

**Benchmark (meta-llama/Llama-3.1-8B) vs standard LoRA:**

| Variant | Time overhead | Memory overhead |
|---------|:-------------:|:---------------:|
| DoRA (no cache) | +139% | +4% |
| DoRA (with caching) | +17% | +41% |

> **Recommendation:** For inference, call `model.merge_and_unload()` to merge DoRA weights back into the base — zero overhead.

#### DoRA vs LoRA — key differences

| Aspect | LoRA | DoRA |
|--------|------|------|
| Parameter count | Same as DoRA (one extra magnitude vector per target module) | ~0.01–0.1% more (single magnitude scalar per module) |
| Low-rank quality | Baseline | **Superior at low ranks** (rank 8 difference > rank 64 difference) |
| Convergence speed | Faster initially | May need slightly more steps (hyperparams tuned for LoRA may underfit DoRA) |
| Supported layers | Most layer types | **embedding, linear, Conv2d only** |
| Inference overhead | Negligible | High if not merged — always `merge_and_unload()` for deployment |
| Quantized QDoRA | Works via bitsandbytes | Supported but **reported issues with DeepSpeed Zero2** |

#### DoRA fine-tuning example

```python
import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer
from datasets import load_dataset

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-1B", device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B")
dataset = load_dataset("timdettmers/openassistant-guanaco", split="train")

lora_config = LoraConfig(use_dora=True, r=8, lora_alpha=32)
peft_model = get_peft_model(model, lora_config)

trainer = Trainer(
    model=peft_model,
    train_dataset=dataset,
    tokenizer=tokenizer,
)
trainer.train()
peft_model.save_pretrained("dora-llama-3-1b")
```

From CLI (using the PEFT examples script):
```bash
python examples/dora_finetuning/dora_finetuning.py \
    --base_model meta-llama/Meta-Llama-3-8B \
    --data_path timdettmers/openassistant-guanaco \
    --use_dora \
    --quantize \
    --batch_size 1 \
    --num_epochs 3
```

#### Caveats

- Limited to **embedding**, **linear**, and **Conv2d** layers — won't apply to attention output projections if they use other layer types.
- **Always merge for inference** — `peft_model.merge_and_unload()` removes the runtime overhead entirely.
- QDoRA (DoRA with 4-bit bitsandbytes) works but **avoid combining with DeepSpeed Zero2**.
- DoRA may require different hyperparameters than LoRA: start with the same `r`, `alpha`, and learning rate, but monitor convergence and increase steps if needed.

## PEFT Method Variants

| Config Class | Method | Description |
|---|---|---|
| `LoraConfig` | LoRA | Low-Rank Adaptation — most popular, broadly supported |
| `LoraConfig(use_dora=True)` | DoRA | Weight-Decomposed LoRA — typically better than vanilla LoRA |
| `PromptTuningConfig` | Prompt Tuning | Learn soft prompt tokens |
| `PrefixTuningConfig` | Prefix Tuning | Learn prefix activations for each transformer layer |
| `P tuningConfig` | P-Tuning | Learn continuous prompts with an LSTM/MLP encoder |
| `IA3Config` | (IA)³ | Learn rescaling vectors for attention/FF layers |
| `AdaLoraConfig` | AdaLoRA | Adaptive budget allocation — automatically prunes unimportant LoRA ranks |
| `LoHaConfig` | LoHa | Low-Rank Hadamard product — more expressive than LoRA |
| `BOFTConfig` | BOFT | Butterfly Orthogonal Fine-Tuning — orthogonal rotations |
| `LoraConfig(init_lora_weights="pissa")` | PiSSA | Principal Singular Values and Singular Vectors Adaptation — better initialization |

## Pitfalls

- **Module name mismatches**: Not all models use the same names (e.g., LLaMA uses `q_proj`, GPT-2 uses `q_proj`, BERT uses `query`). Always inspect the model first.
- **Multi-adapter and `merge_and_unload`**: You must merge the active adapter before calling `merge_and_unload`. Multi-adapter merging is not supported — you get the current active adapter's weights.
- **QLoRA requires `device_map="auto"`**: Without auto device mapping, 4-bit model loading may fail or produce unexpected behavior.
- **Adapter config must match training config**: When loading for inference, the adapter config specifies `r`, `alpha`, and `target_modules`. The base model must be compatible.
- **Inference-only loading with `AutoPeftModel`**: If the repo only has adapter weights (not the full base model), `AutoPeftModel` won't work; use `PeftModel.from_pretrained(base_model, adapter_path)` instead.
- **`push_to_hub` on PEFT model**: Pushes only the adapter. The base model must be loaded separately on the other end. This is by design (adapter is tiny).
- **PEFT v0.20+ changes**: In recent versions, `PeftModelForCausalLM` is deprecated in favor of `AutoPeftModelForCausalLM`. Use the Auto class for inference.
- **Gradient checkpointing**: When training large models with PEFT, enable `gradient_checkpointing=True` in `TrainingArguments` to reduce memory.

## Verification

```python
# Check trainable parameter count
peft_model.print_trainable_parameters()

# Verify adapter is loaded by checking active adapter name
print(f"Active adapter: {peft_model.active_adapter}")

# Test inference
inputs = tokenizer("A quick brown fox", return_tensors="pt")
outputs = peft_model.generate(**inputs, max_new_tokens=20)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## Related Skills

- `huggingface-hub` — for uploading/sharing adapters via CLI
- `model-publishing-pipeline` — end-to-end training → publish pipeline including LoRA
- `hf-smol-course` — SFT, DPO, GRPO with TRL

## References

- `references/model-merging-docs.md` — Official HF doc excerpts for TIES/DARE/Linear merging, paper links, API reference, and code patterns
