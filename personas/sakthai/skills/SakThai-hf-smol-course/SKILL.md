---
name: SakThai-hf-smol-course
description: "Fine-tune LLMs with TRL, PEFT, and alignment methods."
---

# Fine-Tuning LLMs — a smol course

Reference for the [HF smol course](https://huggingface.co/learn/smol-course). Covers instruction tuning, preference alignment (DPO, GRPO), vision-language models, and model evaluation.

> **For a comprehensive deep-dive on the TRL library** — all 8 trainers (SFT, DPO, GRPO, PPO, Reward, KTO, ORPO, CPO), advanced config, PEFT interop, vLLM integration, and production best practices — see sibling skill [`hf-trl-deep-dive`](../hf-trl-deep-dive/SKILL.md). This one is the course portal overview; that one is the authoritative library reference.

## When to Use

- User wants to "fine-tune an LLM"
- User asks about SFT, DPO, GRPO, or RLHF
- User wants to align a model with human preferences
- User needs to evaluate a fine-tuned model
- User wants to understand the full fine-tuning pipeline: data → SFT → alignment

## Prerequisites

```bash
pip install transformers trl peft accelerate datasets bitsandbytes
# For GRPO with vLLM:
pip install vllm
# For evaluation:
pip install evaluate
```

GPU recommended (free: Kaggle, Colab, HF ZeroGPU Spaces). Base model from HF Hub.

## Complete TRL+PEFT Training Pipeline

### 1. Dataset Formatting

#### SFT Dataset Format (Instruction Tuning)
```json
// Format 1: Messages format (recommended)
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"},
    {"role": "assistant", "content": "The capital of France is Paris."}
  ]
}

// Format 2: Text format
{"text": "### Instruction: Explain quantum computing\\n\\n### Response: Quantum computing uses qubits..."}

// Format 3: ChatML format
{"text": "<|im_start|>user\\nWhat is 2+2?<|im_end|>\\n<|im_start|>assistant\\n4<|im_end|>"}
```

#### DPO Dataset Format (Preference Alignment)
```json
{
  "prompt": "Write a short poem about AI.",
  "chosen": "Silicon dreams wake, learning patterns from data streams, a new mind takes form.",
  "rejected": "AI is cool I guess it writes stuff sometimes."
}

// Or with multi-turn context
{
  "prompt": [
    {"role": "user", "content": "What is the best programming language?"}
  ],
  "chosen": [
    {"role": "assistant", "content": "It depends on your use case..."}
  ],
  "rejected": [
    {"role": "assistant", "content": "Python is the best, no contest."}
  ]
}
```

#### GRPO Dataset Format (Reasoning/RL)
```json
{
  "prompt": "What is the sum of the first 10 prime numbers?",
  "answer": "129"  // Answer used for reward computation
}

// GRPO doesn't need chosen/rejected pairs — it generates rollouts and rewards them
```

### 2. Loading and Processing Datasets
```python
from datasets import load_dataset

# Load SFT dataset
sft_dataset = load_dataset("json", data_files="sft_data.jsonl", split="train")

# Load preference dataset
dpo_dataset = load_dataset("json", data_files="dpo_data.jsonl", split="train")

# Apply chat template
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")

def format_sft(example):
    """Convert messages to tokenized format."""
    if "messages" in example:
        text = tokenizer.apply_chat_template(
            example["messages"], tokenize=False, add_generation_prompt=False
        )
    elif "text" in example:
        text = example["text"]
    else:
        raise ValueError("Unknown format")
    return {"text": text}

sft_dataset = sft_dataset.map(format_sft)

def format_dpo(example):
    """Format preference pairs with chat template."""
    if isinstance(example["prompt"], list):
        prompt = tokenizer.apply_chat_template(
            example["prompt"], tokenize=False, add_generation_prompt=True
        )
    else:
        prompt = example["prompt"]
    
    chosen = example["chosen"] + tokenizer.eos_token
    rejected = example["rejected"] + tokenizer.eos_token
    
    return {"prompt": prompt, "chosen": chosen, "rejected": rejected}

dpo_dataset = dpo_dataset.map(format_dpo)
```

### 3. Step 1: Supervised Fine-Tuning (SFT) with PEFT
```python
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, TrainingArguments
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer
import torch

model_name = "Qwen/Qwen2.5-1.5B-Instruct"

# Load base model
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

# Configure PEFT LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

model = get_peft_model(model, lora_config)
print(f"Trainable parameters: {model.num_parameters(only_trainable=True):,}")
print(f"Total parameters: {model.num_parameters():,}")

# Configure SFTTrainer
sft_args = TrainingArguments(
    output_dir="./sft-checkpoints",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_ratio=0.1,
    num_train_epochs=3,
    logging_steps=25,
    save_strategy="epoch",
    bf16=True,
    report_to=["tensorboard"],
    remove_unused_columns=False,
    gradient_checkpointing=True,
    max_grad_norm=1.0,
)

sft_trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=sft_args,
    train_dataset=sft_dataset,
    dataset_text_field="text",
    max_seq_length=2048,
    packing=True,
)

sft_trainer.train()
sft_trainer.save_model("./sft-final")
```

### 4. Step 2: Preference Alignment with DPO
```python
from trl import DPOTrainer

# Load SFT model as base for DPO
model = AutoModelForCausalLM.from_pretrained(
    "./sft-final",
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

# Reference model (frozen copy of SFT model)
ref_model = AutoModelForCausalLM.from_pretrained(
    "./sft-final",
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

dpo_args = TrainingArguments(
    output_dir="./dpo-checkpoints",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=5e-6,  # Lower LR than SFT
    warmup_ratio=0.1,
    num_train_epochs=2,
    logging_steps=10,
    save_strategy="epoch",
    bf16=True,
    report_to=["tensorboard"],
    gradient_checkpointing=True,
    remove_unused_columns=False,
)

dpo_trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,
    tokenizer=tokenizer,
    args=dpo_args,
    train_dataset=dpo_dataset,
    beta=0.1,  # Temperature for DPO loss (higher = more conservative)
    max_prompt_length=1024,
    max_length=2048,
)

dpo_trainer.train()
dpo_trainer.save_model("./dpo-final")
```

### 5. Step 3 (Optional): GRPO for Reasoning Tasks
```python
from trl import GRPOTrainer

# Use with vLLM for fast rollout generation
grpo_args = TrainingArguments(
    output_dir="./grpo-checkpoints",
    per_device_train_batch_size=8,
    gradient_accumulation_steps=2,
    learning_rate=1e-6,
    num_train_epochs=1,
    logging_steps=10,
    bf16=True,
    report_to=["tensorboard"],
)

def accuracy_reward(prompts, completions, answer):
    """Simple accuracy reward for math reasoning."""
    import re
    rewards = []
    for completion, ans in zip(completions, answer):
        # Extract answer from completion
        match = re.search(r'\\boxed{(\\d+)}', completion[0]["content"])
        if match and match.group(1) == str(ans):
            rewards.append(1.0)
        elif str(ans) in completion[0]["content"]:
            rewards.append(0.5)
        else:
            rewards.append(0.0)
    return rewards

grpo_trainer = GRPOTrainer(
    model=model,
    reward_funcs=[accuracy_reward],
    args=grpo_args,
    train_dataset=grpo_dataset,
    # vLLM integration for efficient rollout generation
    use_vllm=True,
    vllm_device="cuda:0",
)

grpo_trainer.train()
```

## GRPO vs DPO Comparison

| Aspect | DPO (Direct Preference Optimization) | GRPO (Group Relative Policy Optimization) |
|--------|--------------------------------------|------------------------------------------|
| **Approach** | Directly optimizes on preference pairs (chosen/rejected) | Generates multiple rollouts per prompt, rewards relative performance |
| **Data Requirement** | Static preference pairs (chosen + rejected) | Prompts + reward function (no pre-collected pairs needed) |
| **When to use** | Alignment after SFT, quality tuning | Reasoning tasks, math, code, multi-step problems |
| **Training Speed** | Faster (no online generation) | Slower (generates rollouts during training) |
| **GPU Memory** | Moderate (2x model: policy + reference) | High (policy + vLLM for generation) |
| **Key Hyperparameters** | `beta` (KL penalty strength) | `group_size` (rollouts per prompt), reward functions |
| **Stability** | Very stable | Requires careful reward engineering |
| **vLLM Integration** | Not needed | Essential for speed |
| **Output Quality** | Better for general human preferences | Better for verifiable tasks (math, code) |

### Decision Flowchart
```
Want to improve model?
├── Need instruction following? → SFT first
├── Need human preference alignment? → DPO
├── Need reasoning/math ability? → GRPO
└── Need both? → SFT → DPO → GRPO (sequential)
```

### When to Use Which

| Scenario | Recommended Method | Why |
|----------|-------------------|-----|
| Chat model alignment | DPO | Static preference pairs work well |
| Math reasoning | GRPO | Can generate + verify solutions |
| Code generation | GRPO | Test-based reward functions |
| Safety alignment | DPO | Careful chosen/rejected curation |
| Step-by-step reasoning | GRPO | Rewards intermediate reasoning |
| General purpose | SFT → DPO | Standard two-stage pipeline |

## Common Dataset Formats

### SFT Format Reference
```python
# Chat template (AutoTokenizer handles this)
tokenizer.apply_chat_template([
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hi!"},
    {"role": "assistant", "content": "Hello!"},
], tokenize=False)
# Result: "<|im_start|>system\nYou are helpful.<|im_end|>\n<|im_start|>user\nHi!<|im_end|>\n<|im_start|>assistant\nHello!<|im_end|>"
```

### Multi-turn DPO
```python
# For conversational preference data
def format_conversation_dpo(example):
    """Format multi-turn preference pairs."""
    prompt_messages = example["conversation"][:-2]  # Context up to last turn
    chosen_msg = example["conversation"][-2]         # Chosen assistant response
    rejected_msg = example["conversation"][-1]       # Rejected assistant response
    
    prompt = tokenizer.apply_chat_template(
        prompt_messages, tokenize=False, add_generation_prompt=True
    )
    
    # Ensure consistent formatting
    chosen = chosen_msg["content"] + tokenizer.eos_token
    rejected = rejected_msg["content"] + tokenizer.eos_token
    
    return {"prompt": prompt, "chosen": chosen, "rejected": rejected}
```

## Evaluation

### Basic Inference Test
```python
from transformers import pipeline

# Before vs After comparison
pipe = pipeline("text-generation", model="./dpo-final", tokenizer=tokenizer, device=0)
result = pipe("Explain transformers simply:", max_new_tokens=100)[0]["generated_text"]
print(result)

# Compare with base model
base_pipe = pipeline("text-generation", model=model_name, tokenizer=tokenizer, device=0)
base_result = base_pipe("Explain transformers simply:", max_new_tokens=100)[0]["generated_text"]
print("BEFORE:", base_result)
print("AFTER:", result)
```

### Automated Evaluation
```python
from evaluate import load

# Perplexity
perplexity = load("perplexity", module_type="metric")
results = perplexity.compute(
    model_id="./dpo-final",
    add_start_token=True,
    predictions=["The capital of France is Paris."]
)
print(f"Perplexity: {results['perplexities']}")

# Use lm-evaluation-harness for standard benchmarks
# pip install lm-eval
# lm_eval --model hf --model_args pretrained=./dpo-final --tasks mmlu,gsm8k --device cuda:0
```

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| `CUDA OOM` during SFT | Batch too large, no gradient checkpointing | Reduce batch_size, enable gradient_checkpointing |
| `DPO loss NaN` | Learning rate too high | Reduce LR to 5e-7 - 5e-6 |
| `GRPO rollout too slow` | No vLLM | `pip install vllm`, set `use_vllm=True` |
| `Chat template not found` | Missing tokenizer config | Use `AutoTokenizer.from_pretrained()` with proper model |
| `Dataset `text` field missing` | Wrong format | Use `dataset_text_field` correctly or apply formatting |
| `OOM during DPO` | Need reference model in memory | Use `peft=True` in DPOTrainer for memory efficiency |
| `GRPO reward always 0` | Reward function issue | Debug with simple hardcoded reward first |

## Pitfalls

- SFT first, THEN alignment (DPO/GRPO). Never skip SFT.
- Preference data requires chosen/rejected pairs — format matters.
- GRPO with vLLM needs GPU memory for both the model and rollout generation.
- Always evaluate on a held-out eval set; loss can drop while quality degrades.
- DPO learning rate should be 10-100x lower than SFT learning rate.
- GRPO reward functions must be carefully designed — bad rewards = bad results.
- Chat template must match the model's expected format — mismatches cause garbage output.
- PEFT (LoRA) saves memory but may not reach full fine-tuning quality on small datasets.
- For QLoRA, use 4-bit quantization: `load_in_4bit=True` with `BitsAndBytesConfig`.

## Verification

```python
from transformers import pipeline

# Run inference on a held-out prompt and compare before/after
pipe = pipeline("text-generation", model="./dpo-final", tokenizer=tokenizer, device=0)
print(pipe("Explain transformers simply:", max_new_tokens=100)[0]["generated_text"])
```

## Additional Resources

- [HF Smol Course](https://huggingface.co/learn/smol-course) — full interactive curriculum
- [TRL Documentation](https://huggingface.co/docs/trl) — all trainers and configs
- [PEFT Documentation](https://huggingface.co/docs/peft) — LoRA, QLoRA, IA3, etc.
- [TRL GitHub Examples](https://github.com/huggingface/trl/tree/main/examples) — complete training scripts
- [Sibling skill: hf-trl-deep-dive](../hf-trl-deep-dive/SKILL.md) — comprehensive TRL library reference
