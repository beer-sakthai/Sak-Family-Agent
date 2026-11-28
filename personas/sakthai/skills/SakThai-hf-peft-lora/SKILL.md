---
name: SakThai-hf-peft-lora
version: 1.0.0
description: Deep dive into Hugging Face PEFT library — LoRA/QLoRA configuration,
  training, inference, multi-adapter management, merging, and Hub integration.
category: training
tags:
- adapters
- beyond
- efficient
- fine-tuning
- hf
- huggingface
- lora
- mlops
- peft
- qlora
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

### 9. Advanced Model Merging (TIES / DARE / Linear / SVD)

PEFT supports multi-adapter merging via `add_weighted_adapter()` to combine multiple fine-tuned adapters into a single adapter layer:

- **TIES**: Trims low-magnitude parameters and resolves sign conflicts (`combination_type="ties"`).
- **DARE**: Drops parameters randomly and rescales remaining weights (`combination_type="dare_ties"` or `"dare_linear"`).
- **Linear / SVD**: Standard weighted averaging or singular value decomposition.

```python
# Example: TIES merge across multiple domain adapters
model.add_weighted_adapter(
    adapters=["norobots", "adcopy", "sql"],
    weights=[2.0, 1.0, 1.0],
    adapter_name="merged_adapter",
    combination_type="ties",
    density=0.2,
)
model.set_adapter("merged_adapter")
```

For complete merging cookbook code and parameter specifications, see [Model Merging Documentation Reference](./references/model-merging-docs.md).

### 10. DoRA (Weight-Decomposed Low-Rank Adaptation)

DoRA decomposes weight updates into magnitude and direction components, yielding superior quality at low ranks (`LoraConfig(use_dora=True)`).

- Requires merging for inference via `peft_model.merge_and_unload()` to eliminate runtime latency overhead.
- Supported layers: `embedding`, `linear`, `Conv2d`.

For benchmarks, caching helpers (`DoraCaching`), and training examples, see [DoRA Reference](./references/dora-weight-decomposed-adaptation.md).

---

## Deep Dive References

For exhaustive reference specifications, cookbook snippets, and extended documentation:
- [PEFT Method Variants, Prompt Tuning & Architecture Specs](./references/peft-method-variants-and-troubleshooting.md)
- [PEFT Model Merging Official Docs & Recipes](./references/model-merging-docs.md)
- [DoRA Weight-Decomposed Low-Rank Adaptation](./references/dora-weight-decomposed-adaptation.md)

