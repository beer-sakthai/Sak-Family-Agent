---
name: SakKing-hf-peft
description: "Hugging Face PEFT (Parameter-Efficient Fine-Tuning): library overview, method taxonomy (LoRA, QLoRA, adapters, soft prompts, selective), training/inference workflow, and ecosystem integration with Transformers/Accelerate."
tags: [huggingface, peft, lora, qlora, adapters, fine-tuning, efficient, mlops]
version: 1.0.0
---

# Hugging Face PEFT — Parameter-Efficient Fine-Tuning

**Fine-tune large models by updating only a small fraction of parameters**, keeping base weights frozen. The Hugging Face `peft` library unifies dozens of methods behind a single API.

## Core Problem

Full fine-tuning of LLMs requires:
- Enough VRAM to store the full model in fp16/bf16 **plus** optimizer states and gradients (often 3–4× model size).
- Storing a full copy of the weights for every downstream task.
- Consumer hardware becomes impractical for models above ~7B–13B parameters.

PEFT solves this by introducing lightweight trainable subsets that can be stored (MBs) and swapped in minutes.

## Library at a Glance

| Component | Purpose |
|-----------|---------|
| `PeftConfig` | Stores hyperparameters for a given PEFT method (base class). |
| `get_peft_model(model, peft_config)` | Wraps a base model and injects trainable adapter layers. |
| `PeftModel` | The wrapped model; supports `save_pretrained()`, `merge_and_unload()`. |
| `AutoPeftModel` / `AutoPeftConfig` | Load configs and models from the Hub without knowing the method. |
| Method-specific configs | `LoraConfig`, `AdaLoraConfig`, `PromptTuningConfig`, `PrefixTuningConfig`, etc. |

Install:
```bash
pip install peft
```

## PEFT Method Taxonomy

### 1. Additive Methods
Inject new, trainable layers or embeddings into the model while keeping original weights frozen.

| Method | Mechanism | Trainable Params | Notes |
|--------|-----------|------------------|-------|
| **Adapter** | Small bottleneck layers inserted after attention/MLP blocks. | ~1–5% | Need extra inference latency unless merged. |
| **Prompt Tuning** | Prepend continuous soft token embeddings to the input. | Very few | Sensitive to initialization and prompt length. |
| **Prefix Tuning** | Prepend key/value prefix vectors to every transformer layer. | ~1% | Stronger than prompt tuning; can match fine-tuning. |
| **P-tuning** | LSTM-parameterized prompt encoder + soft tokens. | Very few | Good for NLU tasks; less popular now. |
| **IA³** | Scale and shift activations via learned vectors. | <0.1% | Extremely lightweight; element-wise rescaling. |

### 2. Reparameterization-Based Methods
Represent weight updates as small learnable matrices and merge them into the base model at inference.

| Method | Mechanism | Key Parameters |
|--------|-----------|----------------|
| **LoRA** | Two low-rank matrices A (down) and B (up); update = B·A frozen. | `r` (rank), `lora_alpha`, `lora_dropout` |
| **QLoRA** | 4-bit (or 8-bit) frozen base + LoRA; backprop through dequantization. | Same as LoRA + `bnb_4bit_quant_type` |
| **DoRA** | Decomposes each weight magnitude + direction; trains both independently. | Like LoRA but with weight decomposition |
| **PiSSA** | Initializes LoRA with top singular vectors of the original weight. | Same as LoRA |
| **OLoRA** | Orthogonal LoRA initialization for stability. | Same as LoRA |
| **rsLoRA** | Rank-stabilized LoRA scaling for better convergence. | Same as LoRA |
| **LoHa** | Low-rank Hadamard product representation (A ○ B). | `r`, `rank_dropout` |
| **LoKr** | Low-rank Kronecker product representation. | `r` |
| **X-LoRA** | Mixture of LoRA experts; dynamic weighted combination. | `r`, `num_experts` |
| **KronA** | Kronecker-factorized updates adapters. | `kron_dim` |

**LoRA key facts** (the most dominant method):
- Trainable params = `r × (d_in + d_out) × #layers`
- Can be merged into base weights with `model.merge_and_unload()` — **zero inference overhead**.
- Base weights remain in fp16/bf16 (or 4-bit in QLoRA); adapters are tiny MB-size files.
- `r` typically 4–64; `lora_alpha = 2×r` is a common rule of thumb.
- Target modules by regex, e.g. `target_modules=["q_proj", "v_proj"]`.

### 3. Selective Methods
Only fine-tune a subset of the full frozen parameters (bias terms, specific layers).

| Method | Mechanism |
|--------|-----------|
| **BitFit** | Train only the bias terms; ~0.1% of weights. |
| **DiffPruning** | Learn a binary mask to select weights; gradient struggles with discrete mask. |
| **FAR** | Freeze and reconfigure specific layers; minimal overhead. |
| **FishMask** | Uses Fisher information to select important parameters. |

## Training Workflow (LoRA example)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, TaskType, get_peft_model
from transformers import Trainer, TrainingArguments

# 1. Load base model
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf", load_in_4bit=True)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")

# 2. Configure LoRA
peft_cfg = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
)

# 3. Wrap model
model = get_peft_model(model, peft_cfg)
model.print_trainable_parameters()
# trainable params: 4,194,304 || all params: 6,742,525,184 || trainable%: 0.06%

# 4. Train
args = TrainingArguments(
    output_dir="./peft-lora-llama",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    num_train_epochs=1,
    fp16=True,
)
trainer = Trainer(model=model, args=args, train_dataset=dataset, tokenizer=tokenizer)
trainer.train()

# 5. Save adapter only
model.save_pretrained("./peft-lora-llama-adapter")
```

> **Note:** `load_in_4bit=True` requires `bitsandbytes`. PEFT also supports 8-bit, NF4, and FP4 quantization via `bitsandbytes` or `torchao`.

## Inference with Adapters

```python
from peft import PeftModel, PeftConfig

base = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")
model = PeftModel.from_pretrained(base, "./peft-lora-llama-adapter")

# Fast path: merge adapter into base (no runtime overhead)
model = model.merge_and_unload()
# Now model is a normal causal LM with your fine-tuned weights.
```

**Switching adapters at runtime:**
```python
model.load_adapter("./adapter-a", adapter_name="a")
model.load_adapter("./adapter-b", adapter_name="b")
model.set_adapter("a")  # switches to adapter-a
```

## Integration Ecosystem

| Library | Integration |
|---------|-------------|
| **Transformers** | `AutoModel` + PEFT; `Trainer`/`Seq2SeqTrainer` works out of the box. |
| **Diffusers** | `load_lora_weights()` and `unload_lora_weights()` for Stable Diffusion. |
| **Accelerate** | Works with custom loops; PEFT handles device placement. |
| **BitsAndBytes** | 4-bit/8-bit quantization (`load_in_4bit`, `load_in_8bit`) for QLoRA. |
| **TRL** | `SFTTrainer`, `PPOTrainer`, `DPOTrainer` support PEFT configs directly. |
| **AutoTrain** | UI/CLI point-and-click fine-tuning uses PEFT under the hood. |
| **Hub** | Upload adapters as separate repos; set `safetensors` for safer sharing. |

## Supported Modalities & Tasks

- **Text Generation** — causal LM, Llama, Qwen, Phi, etc.
- **Seq2Seq** — T5, FLAN-T5, mT0.
- **Image Classification** — ViT, ConvNeXt with adapters.
- **Text-to-Image** — Stable Diffusion / Diffusers LoRA / LoHa.
- **Automatic Speech Recognition** — Whisper adapters.
- **Token Classification** — NER, POS.
- **Multimodal** — LLaVA, CLIP.

## Key Best Practices

1. **Target modules** matter. For LLaMA/Mistral/Qwen, attention proj layers (`q_proj`, `v_proj`, sometimes `k_proj`, `o_proj`) are standard. Check the model architecture if unsure.
2. **Rank selection** — `r=8` is a good default. Higher rank = more capacity but larger adapter + higher overfit risk.
3. **Quantization + LoRA** — QLoRA (4-bit) fits ~7B models on a 6–8 GB GPU; 13B models on 16 GB.
4. **Learning rate** — LoRA needs a higher LR than full fine-tuning. Typical: `2e-4` to `5e-4`.
5. **Adapter merging** — Always merge before pushing to production inference to avoid extra latency.
6. **Safetensors** — PEPT supports `save_pretrained(..., safe_serialization=True)`; use it.
7. **Catastrophic forgetting** — Because base weights are frozen, forgetting is reduced, but domain shift can still occur. Use a small amount of original data or regularization if needed.

## Common Pitfalls

- **Forgetting to set `task_type`** — `LoraConfig` requires the correct `TaskType`; mismatches cause shape errors.
- **Target module mismatch** — Some architectures name projections differently (`Q_PROJ` vs `q_proj`). Use `model.named_modules()` to inspect.
- **LoRA + DP+FSDP** — PEFT works with DeepSpeed ZeRO and Fully Sharded Data Parallel, but you must apply `get_peft_model` *before* wrapping with `prepare_model_for_kbit_training`.
- **Inference latency** — If you load the base model and adapter separately without merging, each forward pass has extra overhead. Merge for deployment.
- **Saving full model by accident** — `model.save_pretrained()` without `PeftModel` logic will dump the whole model; use `model.save_pretrained()` on the `PeftModel` wrapper to save only adapters.
- **QLoRA compatibility** — Requires `bitsandbytes` with CUDA. CPU inference still loads base in fp16 or int8.

## When to Use PEFT

| Scenario | Recommended Method |
|----------|-------------------|
| Consumer GPU (6–16 GB VRAM) | QLoRA (LoRA + 4-bit) |
| Multiple tasks from one base | LoRA + adapter switching |
| Very limited VRAM or CPU | IA³ / BitFit (minimal VRAM) |
| Fast experimentation | LoRA (easy to merge and unload) |
| Extreme compression | DoRA / QLoRA |
| Multimodal fine-tuning | Diffusers LoRA / LoHa |

## Quick Reference: `LoraConfig` Parameters

```python
LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    inference_mode=False,       # set True at inference
    r=8,                        # LoRA rank
    lora_alpha=32,              # scaling factor
    lora_dropout=0.05,          # regularize adapter
    bias="none",                # or "all", "lora_only"
    target_modules=[...],       # module names to adapt
    modules_to_save=[...],      # additional layers to unfreeze
    fan_in_fan_out=False,       # for layers where IO dims are swapped
    loft_config=None,           # LoftQ for QLoRA initialization
)
```

## Useful Docs & Resources

- **Main docs**: https://huggingface.co/docs/peft
- **GitHub**: https://github.com/huggingface/peft
- **Quicktour**: https://huggingface.co/docs/peft/en/quicktour
- **Methods guide**: https://huggingface.co/blog/samuellimabraz/peft-methods
- **Transformers + PEFT**: https://huggingface.co/docs/transformers/en/peft
- **Diffusers + PEFT**: https://huggingface.co/docs/diffusers/main/en/api/loaders/peft
- **Beyond LoRA blog**: https://huggingface.co/blog/peft-beyond-lora

---

## Cross-References

- **`hf-bitsandbytes`** — 4-bit/8-bit quantization backend required for QLoRA. Covers `BitsAndBytesConfig`, installation per hardware, compute-dtype selection (bfloat16 vs float16), NF4/FP4 data types, 8-bit optimizers, and custom quantized linear layers.
- **`hf-accelerate`** — Device mapping, distributed launchers, and `BnbQuantizationConfig` for non-Transformers PyTorch models.
- **`hf-trl`** (if installed) — `SFTTrainer`, `PPOTrainer`, and `DPOTrainer` wrap PEFT configs directly.
