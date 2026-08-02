---
name: SakThai-hf-llm-course
author: SakThai
license: MIT
description: "Reference for Hugging Face Transformers and LLM workflows."
version: 1.0.0
tags: [LLM, NLP, Transformers, HuggingFace, Course]
---
# LLM Course — Transformers & NLP Reference

Based on the [HF LLM Course](https://huggingface.co/learn/llm-course). Covers using Transformers, Datasets, Tokenizers, and Accelerate for NLP and LLM tasks.

## When to Use

- User needs to load or use a transformer model for NLP
- User asks about tokenizers, datasets, or model sharing on the Hub
- User wants to fine-tune or evaluate a pretrained model
- User needs to build a Gradio demo for a model

## Prerequisites

- `transformers`, `datasets`, `tokenizers`, `accelerate`, `gradio` — install via pip
- HF account for model sharing at [huggingface.co/join](https://huggingface.co/join)
- GPU recommended for training/fine-tuning

## LLM Pipeline Overview

The LLM lifecycle has three major stages, each with distinct techniques and tooling:

```
┌─────────────────────────────────────────────────────────────┐
│                     PRE-TRAINING                             │
│                                                              │
│  Raw Data → Tokenization → Causal LM Training → Base Model  │
│                                                              │
│  Libraries: transformers, datasets, tokenizers, megatron    │
│  Cost: $$$$$ (100s–1000s of GPUs, weeks-months)             │
│  Output: Base model (e.g., Llama 3 8B, GPT-2)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     FINE-TUNING                               │
│                                                              │
│  Base Model → Instruction Data → Supervised Fine-Tuning     │
│                                                              │
│  Libraries: transformers (Trainer), trl (SFTTrainer), peft  │
│              accelerate, datasets, bitsandbytes              │
│  Cost: $$ (1–64 GPUs, hours-days)                            │
│  Output: Instruction-tuned model (e.g., Llama-3-8B-Instruct)│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     RLHF / PREFERENCE ALIGNMENT               │
│                                                              │
│  SFT Model → Reward Model → PPO/DPO/ORPO → Aligned Model    │
│                                                              │
│  Libraries: trl (DPOTrainer, PPOTrainer), peft               │
│  Cost: $$ (4–64 GPUs, hours-days)                            │
│  Output: Aligned model (e.g., Llama-3-8B-Instruct, Zephyr)  │
└─────────────────────────────────────────────────────────────┘
```

## Quick Reference

| Library | Install | Key Use |
|---------|---------|---------|
| Transformers | `pip install transformers` | Load/infer/fine-tune any HF model |
| Datasets | `pip install datasets` | Load, process, stream datasets |
| Tokenizers | `pip install tokenizers` | Fast tokenization (Rust backend) |
| Accelerate | `pip install accelerate` | Multi-GPU/mixed-precision training. See dedicated skill `mlops/hf-accelerate` for DeepSpeed, FSDP, gradient accumulation, and Accelerator API. |
| Gradio | `pip install gradio` | Build interactive demos |
| TRL | `pip install trl` | SFT, DPO, PPO, reward modeling |
| PEFT | `pip install peft` | LoRA, QLoRA, prefix tuning |
| bitsandbytes | `pip install bitsandbytes` | 4-bit/8-bit quantization |

## Code for Each Pipeline Stage

### 1. Pre-training (Causal Language Model)

Pre-training is resource-intensive. The code below shows the structure using a small GPT-2-style model for educational purposes.

```python
from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    Trainer, TrainingArguments, DataCollatorForLanguageModeling
)
from datasets import load_dataset

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("gpt2")
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained("gpt2")

# Load and tokenize dataset
dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="train")

def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, max_length=512)

tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=["text"])

# Data collator for language modeling (auto-creates labels)
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer, mlm=False  # causal LM, not masked LM
)

# Training arguments
training_args = TrainingArguments(
    output_dir="./gpt2-pretrained",
    overwrite_output_dir=True,
    num_train_epochs=1,
    per_device_train_batch_size=8,
    save_steps=10_000,
    save_total_limit=2,
    logging_steps=500,
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=tokenized_dataset,
)

trainer.train()
model.save_pretrained("./gpt2-pretrained")
tokenizer.save_pretrained("./gpt2-pretrained")
```

### 2. Supervised Fine-Tuning (SFT)

Also called instruction tuning. The most common LLM customization technique.

```python
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    TrainingArguments
)
from trl import SFTTrainer
from datasets import load_dataset

# Load base model
model = AutoModelForCausalLM.from_pretrained(
    "microsoft/Phi-3-mini-4k-instruct",
    torch_dtype="auto",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")

# Load instruction dataset
dataset = load_dataset("databricks/databricks-dolly-15k", split="train")

# Format as chat instructions
def format_instruction(example):
    return {
        "text": f"### Instruction\n{example['instruction']}\n\n### Response\n{example['response']}"
    }

formatted_ds = dataset.map(format_instruction)

# Training args
training_args = TrainingArguments(
    output_dir="./phi3-sft",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-5,
    logging_steps=10,
    num_train_epochs=3,
    save_strategy="epoch",
    fp16=True,
)

# SFTTrainer handles packing, formatting
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args,
    train_dataset=formatted_ds,
    max_seq_length=2048,
)

trainer.train()
trainer.save_model("./phi3-sft")
```

### 2b. Fine-tuning with LoRA (Parameter Efficient)

```python
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, TrainingArguments
from trl import SFTTrainer

# LoRA config
lora_config = LoraConfig(
    r=16,               # rank
    lora_alpha=32,      # scaling factor
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# Load model (4-bit quantized for QLoRA)
model = AutoModelForCausalLM.from_pretrained(
    "microsoft/Phi-3-mini-4k-instruct",
    load_in_4bit=True,
    device_map="auto",
)

# SFTTrainer with PEFT
trainer = SFTTrainER(
    model=model,
    args=training_args,
    train_dataset=formatted_ds,
    peft_config=lora_config,
    max_seq_length=2048,
)

trainer.train()
model.save_pretrained("./phi3-lora")
```

### 3. Preference Alignment (DPO)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOTrainer, DPOConfig
from datasets import load_dataset

# Load base SFT model
model = AutoModelForCausalLM.from_pretrained(
    "./phi3-sft",
    torch_dtype="auto",
    device_map="auto",
)
tokenizer = AutoTokenizer.from_pretrained("./phi3-sft")
tokenizer.pad_token = tokenizer.eos_token

# Load preference dataset (chosen/rejected pairs)
dataset = load_dataset("Anthropic/hh-rlhf", split="train")

# DPO training args
dpo_args = DPOConfig(
    output_dir="./phi3-dpo",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=1e-6,
    num_train_epochs=1,
    logging_steps=10,
    save_strategy="epoch",
    beta=0.1,  # DPO temperature parameter
)

# DPO trainer
dpo_trainer = DPOTrainer(
    model=model,
    args=dpo_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    max_length=1024,
    max_prompt_length=512,
)

dpo_trainer.train()
dpo_trainer.save_model("./phi3-dpo")
```

### 3b. Preference Alignment (PPO — RLHF)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import PPOConfig, PPOTrainer, AutoModelForCausalLMWithValueHead
from datasets import load_dataset
import torch

# Load model with value head (for PPO)
model = AutoModelForCausalLMWithValueHead.from_pretrained("./phi3-sft")
tokenizer = AutoTokenizer.from_pretrained("./phi3-sft")
tokenizer.pad_token = tokenizer.eos_token

# Load reward model (trained separately)
reward_model = AutoModelForCausalLM.from_pretrained("./reward-model")

# PPO config
ppo_config = PPOConfig(
    model_name="./phi3-sft",
    learning_rate=1.4e-5,
    batch_size=16,
    mini_batch_size=4,
    gradient_accumulation_steps=1,
    ppo_epochs=4,
)

# Dataset of prompts
dataset = load_dataset("imdb", split="train[:100]")

# PPO trainer
ppo_trainer = PPOTrainer(
    config=ppo_config,
    model=model,
    tokenizer=tokenizer,
    dataset=dataset,
)

# Training loop
for epoch in range(1):
    for batch in ppo_trainer.dataloader:
        query_tensors = batch["input_ids"]
        
        # Generate responses
        response_tensors = ppo_trainer.generate(
            query_tensors,
            return_prompt=False,
            length_sampler_kwargs={"min_length": 20, "max_length": 100},
        )
        
        # Compute rewards
        scores = reward_model(response_tensors)
        
        # Run PPO step
        stats = ppo_trainer.step(query_tensors, response_tensors, scores)
        print(f"Objective/kl: {stats['objective/kl']:.4f}")
```

### 4. Evaluation

```python
from datasets import load_dataset
from transformers import pipeline
import numpy as np

# Load evaluation dataset
eval_data = load_dataset("truthful_qa", "generation", split="validation")

# Run inference
pipe = pipeline("text-generation", model="./phi3-dpo", device_map="auto")

def evaluate_model(dataset, pipe):
    results = []
    for item in dataset:
        prompt = item["question"]
        output = pipe(prompt, max_new_tokens=100)[0]["generated_text"]
        results.append({"prompt": prompt, "output": output})
    return results

# Compute metrics
results = evaluate_model(eval_data, pipe)
# Use lm-eval-harness for standard benchmarks
# pip install lm_eval
# lm_eval --model hf --model_args pretrained=./phi3-dpo --tasks truthfulqa
```

## Procedure

1. **Load a model and tokenizer:**
   ```python
   from transformers import AutoModelForCausalLM, AutoTokenizer
   model = AutoModelForCausalLM.from_pretrained("microsoft/Phi-3-mini-4k-instruct")
   tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")
   ```

2. **Run inference:**
   ```python
   inputs = tokenizer("Hello, I am", return_tensors="pt")
   outputs = model.generate(**inputs, max_new_tokens=50)
   print(tokenizer.decode(outputs[0]))
   ```

3. **Load a dataset:**
   ```python
   from datasets import load_dataset
   dataset = load_dataset("imdb", split="train")
   ```

4. **Fine-tune with Trainer:**
   ```python
   from transformers import Trainer, TrainingArguments
   training_args = TrainingArguments(output_dir="./results", num_train_epochs=3)
   trainer = Trainer(model=model, args=training_args, train_dataset=dataset)
   trainer.train()
   ```

5. **Share to Hub:**
   ```python
   model.push_to_hub("your-username/model-name")
   tokenizer.push_to_hub("your-username/model-name")
   ```

6. **Build a Gradio demo:**
   ```python
   import gradio as gr
   gr.Interface(fn=predict, inputs="text", outputs="text").launch()
   ```

## Pitfalls

- Tokenizer must match the model — using mismatched tokenizers produces garbage output.
- For large models, use `device_map="auto"` and `torch_dtype=torch.float16` to fit in GPU memory.
- `datasets` streaming mode (`streaming=True`) avoids downloading full datasets.
- Pre-training from scratch requires enormous compute — prefer fine-tuning an existing base model.
- DPO is simpler than PPO (no reward model needed) but requires high-quality preference pairs.
- LoRA adapters need merging (`peft`'s `merge_and_unload()`) for deployment without the PEFT library.
- Always monitor for overfitting during fine-tuning — few epochs (1-3) is usually enough.

## Related Skills in This Repo

| Skill | Location | Covers |
|-------|----------|--------|
| hf-smol-course | `mlops/hf-smol-course` | Fine-tuning LLMs (TRL, PEFT) |
| hf-trl-deep-dive | `mlops/hf-trl-deep-dive` | TRL library (SFT, DPO, PPO, Reward) |
| hf-peft-lora | `mlops/hf-peft-lora` | LoRA, QLoRA, prefix tuning |
| hf-accelerate | `mlops/hf-accelerate` | Multi-GPU, DeepSpeed, FSDP |

## Verification

```python
from transformers import pipeline; pipe = pipeline("text-classification"); print(pipe("HF is great!"))
```
