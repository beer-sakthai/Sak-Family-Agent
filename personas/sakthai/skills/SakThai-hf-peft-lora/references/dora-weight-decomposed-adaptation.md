# DoRA — Weight-Decomposed Low-Rank Adaptation

DoRA (Weight-Decomposed Low-Rank Adaptation, [paper 2402.09353](https://huggingface.co/papers/2402.09353)) decomposes weight updates into **magnitude** and **direction** components. Direction uses standard LoRA, while magnitude gets a separate learnable parameter. This improves LoRA quality especially at low ranks.

## API — Single Flag

```python
from peft import LoraConfig

config = LoraConfig(use_dora=True, ...)  # That's it — everything else is same as LoRA
```

No other config changes needed. Dropout, target_modules, rank, alpha all work identically to LoRA.

## Ephemeral GPU Offload

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

## Inference Optimization — `DoraCaching`

DoRA is automatically optimized for `eval()` mode or when `lora_dropout=0` (reuses base model results for speed). For further speed at the cost of memory, use the `DoraCaching` helper:

```python
from peft.helpers import DoraCaching

model.eval()
with DoraCaching():
    output = model(inputs)
```

### Benchmark (meta-llama/Llama-3.1-8B) vs Standard LoRA

| Variant | Time overhead | Memory overhead |
|---------|:-------------:|:---------------:|
| DoRA (no cache) | +139% | +4% |
| DoRA (with caching) | +17% | +41% |

> **Recommendation:** For inference, call `model.merge_and_unload()` to merge DoRA weights back into the base — zero overhead.

## DoRA vs LoRA — Key Differences

| Aspect | LoRA | DoRA |
|--------|------|------|
| Parameter count | Same as DoRA (one extra magnitude vector per target module) | ~0.01–0.1% more (single magnitude scalar per module) |
| Low-rank quality | Baseline | **Superior at low ranks** (rank 8 difference > rank 64 difference) |
| Convergence speed | Faster initially | May need slightly more steps (hyperparams tuned for LoRA may underfit DoRA) |
| Supported layers | Most layer types | **embedding, linear, Conv2d only** |
| Inference overhead | Negligible | High if not merged — always `merge_and_unload()` for deployment |
| Quantized QDoRA | Works via bitsandbytes | Supported but **reported issues with DeepSpeed Zero2** |

## Fine-Tuning Example

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

From CLI (using PEFT examples script):
```bash
python examples/dora_finetuning/dora_finetuning.py \
    --base_model meta-llama/Meta-Llama-3-8B \
    --data_path timdettmers/openassistant-guanaco \
    --use_dora \
    --quantize \
    --batch_size 1 \
    --num_epochs 3
```

## Caveats & Pitfalls

- Limited to **embedding**, **linear**, and **Conv2d** layers — won't apply to attention output projections if they use other layer types.
- **Always merge for inference** — `peft_model.merge_and_unload()` removes the runtime overhead entirely.
- QDoRA (DoRA with 4-bit bitsandbytes) works but **avoid combining with DeepSpeed Zero2**.
- DoRA may require different hyperparameters than LoRA: start with the same `r`, `alpha`, and learning rate, but monitor convergence and increase steps if needed.
