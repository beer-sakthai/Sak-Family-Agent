# CPU LoRA Training — Memory Optimization

When fine-tuning small models (0.5B-1.5B) on CPU without GPU, memory is the primary constraint. Standard Hugging Face Trainer with float32 model + optimizer + gradients can exceed available RAM on typical machines (8 GB total, ~4 GB free after OS + other services).

## Memory Budget

| Component | 0.5B (494M params) | 1.5B (1.5B params) |
|-----------|:-------------------:|:-------------------:|
| Model (float32) | ~2 GB | ~6 GB |
| Optimizer (AdamW) | ~1 GB | ~3 GB |
| Gradients | ~1 GB | ~3 GB |
| Activations (no checkpoint) | ~500 MB | ~1.5 GB |
| **Total** | **~4.5 GB** | **~13.5 GB** |

Without GPU, the 0.5B model is the only practical option for a 7-8 GB machine.

## Required Optimizations

### 1. Gradient Checkpointing

Without this, activations for ALL layers are stored simultaneously, doubling memory for the backward pass. With it, activations are recomputed on the fly, trading ~2x speed for ~50% memory:

```python
model.gradient_checkpointing_enable()
```

### 2. Reduce Sequence Length

Training examples should be truncated to the minimum viable length. 512 tokens for a simple tool-calling example is wasteful — 256 is sufficient:

```python
def tokenize_fn(examples):
    tok = tokenizer(examples["text"], truncation=True, max_length=256, padding=False)
    tok["labels"] = tok["input_ids"].copy()
    return tok
```

### 3. Float32 Only

CPU doesn't benefit from fp16/bf16. Cast to float32 and disable mixed precision:

```python
model = AutoModelForCausalLM.from_pretrained(
    ..., torch_dtype=torch.float32, low_cpu_mem_usage=True
)

training_args = TrainingArguments(
    ..., fp16=False, bf16=False
)
```

### 4. Minimal Batch with Gradient Accumulation

```python
per_device_train_batch_size=1,
gradient_accumulation_steps=4,
```

### 5. Disable Pin Memory

DataLoader pin_memory is a GPU optimization. On CPU it adds overhead:

```python
dataloader_pin_memory=False,
remove_unused_columns=False,
```

## Labels Requirement

Causal LM models do NOT auto-compute loss from `input_ids` alone. The `Trainer` expects a `labels` key in the model inputs. Copy `input_ids`:

```python
tok["labels"] = tok["input_ids"].copy()
```

Without this, Trainer raises:
```
ValueError: The model did not return a loss from the inputs, only the following keys: logits.
```

## Expected Performance

| Model | Settings | Steps/s | ETA (200 examples, 3 epochs) |
|-------|----------|:-------:|:----------------------------:|
| 0.5B | Basic | OOM | — |
| 0.5B | + gradient checkpointing | ~10s/it | ~25 min |
| 0.5B | + max_length=256 | ~18s/it | ~45 min |

## OOM Diagnosis

When training is killed:
- Exit code -9 = SIGKILL = OOM killer
- No Python traceback — process just vanishes
- Fix order: add gradient checkpointing first (biggest impact), then reduce max_length, then reduce model size

If still OOM after all optimizations, the model is too large for this machine — switch to a smaller base model or use cloud GPU. For Food-Penguin, the 0.5B model is the only option for CPU training.
