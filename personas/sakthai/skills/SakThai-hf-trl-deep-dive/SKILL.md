---
name: SakThai-hf-trl-deep-dive
author: SakThai
license: MIT
description: "Comprehensive reference for Hugging Face TRL v1.9.0 — all 14 trainers (4 categories: online, offline, reward, distillation), multi-environment GRPO, KTO stability, vLLM/DeepSpeed/PEFT interop, Liger Kernel, OpenEnv/Harbor, VLM alignment."
version: 2.0.0
tags: [TRL, RLHF, DPO, GRPO, PPO, SFT, KTO, RLOO, PRM, Alignment, FineTuning, HuggingFace, RL, vLLM, LigerKernel]
related_skills: [hf-smol-course, hf-smolagents, hf-cookbook]
---

# TRL v1.9.0 — Complete Post-Training Toolkit

Complete reference for the [TRL library v1.9.0](https://huggingface.co/docs/trl/en/index) — alignment and RL fine-tuning for LLMs/VLMs. **TRL v1** (March 2026) was a major rewrite adding 6 new trainers, multi-environment agentic RL, VLM alignment, and knowledge distillation.

## When to Use

- User wants to align a model after SFT (DPO, GRPO, KTO)
- User asks which preference optimization method to choose from 14 options
- User needs to chain SFT → alignment in one pipeline
- User hits errors with TRL data formatting, packing, or vLLM integration
- User needs reward model training for RLHF or process rewards
- User wants knowledge distillation (GKD, MiniLLM)
- User is doing reasoning/RL fine-tuning with GRPO + reward functions

## Quick Install

```bash
pip install trl transformers accelerate peft datasets bitsandbytes
# For online methods with fast rollout generation:
pip install vllm        # GRPO, RLOO, OnlineDPO, NashMD, XPO ⚡️
# Optional speedups:
pip install liger-kernel  # Fused GRPO ops (~40% memory savings)
# For sandboxed environments:
pip install harbor openenv
```

## Architecture Overview — 4 Categories, 14 Trainers

TRL v1.9.0 organizes trainers into 4 categories:

### Online Methods (RL-based, generate during training)

| Trainer | Status | vLLM ⚡️ | Data | Ref Model | Use Case |
|---------|--------|----------|------|-----------|----------|
| **GRPOTrainer** | ✅ Stable | ⚡️ | Prompts + reward fns | No | Reasoning tasks, multi-reward (DAPO default) |
| **RLOOTrainer** | ✅ Stable | ⚡️ | Prompts + reward fns | No | REINFORCE LOO, non-Gaussian rewards |
| **OnlineDPOTrainer** | 🧪 | ⚡️ | Prompts + reward model | Yes | On-policy DPO, stronger alignment |
| **NashMDTrainer** | 🧪 | ⚡️ | Prompts + reward model | Yes | Game-theoretic alignment |
| **PPOTrainer** | 🧪 | ❌ | Prompts + reward model | Yes | Legacy — GRPO supersedes |
| **XPOTrainer** | 🧪 | ⚡️ | Prompts + reward model | Yes | Exploit-Explore for creative tasks |

### Offline Methods (static dataset)

| Trainer | Status | Data Required | Ref Model | Use Case |
|---------|--------|---------------|-----------|----------|
| **SFTTrainer** | ✅ Stable | Prompts + completions | No | First step — always start here |
| **DPOTrainer** | ✅ Stable | Chosen/rejected pairs | Yes | Best all-round alignment |
| **KTOTrainer** | ✅ Stable | Completion + label | Yes | Unpaired/preference-on-label |
| **BCOTrainer** | 🧪 | Chosen/rejected pairs | No | Binary CE variant |
| **CPOTrainer** | 🧪 | Chosen/rejected pairs | No | Contrastive, reference-free |
| **ORPOTrainer** | 🧪 | Chosen/rejected pairs | No | Odds ratio, reference-free |

### Reward Modeling

| Trainer | Status | Description |
|---------|--------|-------------|
| **RewardTrainer** | ✅ Stable | Bradley-Terry reward model |
| **PRMTrainer** | 🧪 | Process Reward Model (step-level) |

### Knowledge Distillation

| Trainer | Status | Description |
|---------|--------|-------------|
| **GKDTrainer** | 🧪 | Generalized KD (KL-divergence) |
| **MiniLLMTrainer** | 🧪 | Generative distillation (sequence-level) |

## Detailed Trainer Usage

### 1. SFTTrainer — Supervised Fine-Tuning

```python
from trl import SFTTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from datasets import load_dataset

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B")
tokenizer.pad_token = tokenizer.eos_token

dataset = load_dataset("HuggingFaceH4/ultrachat_200k", split="train[:1000]")

# Option A: Formatting function (most flexible)
def formatting_func(example):
    return [f"<|user|>\n{msg['content']}\n<|assistant|>\n"
            for msg in example["messages"]]

# Option B: Use chat template
def chat_format(example):
    return tokenizer.apply_chat_template(
        example["messages"], tokenize=False, add_generation_prompt=False
    )

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=TrainingArguments(
        output_dir="./sft-qwen",
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        max_steps=100,
        logging_steps=10,
        save_strategy="steps",
        save_steps=50,
        fp16=True,
        report_to="none",
    ),
    train_dataset=dataset,
    formatting_func=formatting_func,  # or callable that returns text
    max_seq_length=2048,
    packing=True,  # pack sequences for efficiency
)
trainer.train()
trainer.save_model("./sft-qwen-final")
```

**Key parameters:**
- `packing=True` — concatenates sequences to fill `max_seq_length` (boosts throughput 2-3x)
- `formatting_func` — transforms dataset rows to text strings
- `dataset_text_field` — alternative: name of column containing already-formatted text
- `max_seq_length` — truncation + packing target

**With PEFT (QLoRA):**
```python
from peft import LoraConfig, get_peft_model

peft_config = LoraConfig(
    r=16, lora_alpha=32, target_modules="all-linear",
    lora_dropout=0.05, bias="none", task_type="CAUSAL_LM"
)
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=...,
    train_dataset=dataset,
    peft_config=peft_config,  # enables QLoRA automatically
    formatting_func=formatting_func,
    max_seq_length=2048,
)
```

### 2. DPOTrainer — Direct Preference Optimization

```python
from trl import DPOTrainer

# Dataset must have: prompt, chosen, rejected columns
# Or: formatted with chosen/rejected in messages format
dpo_dataset = load_dataset("trl-lib/ultrafeedback_binarized", split="train[:1000]")

dpo_trainer = DPOTrainer(
    model=model,  # the SFT-tuned model
    ref_model=None,  # auto-copies model if None
    tokenizer=tokenizer,
    args=TrainingArguments(
        output_dir="./dpo-qwen",
        per_device_train_batch_size=4,
        learning_rate=1e-6,
        max_steps=200,
        fp16=True,
        report_to="none",
    ),
    train_dataset=dpo_dataset,
    beta=0.1,  # KL penalty — lower = stronger alignment
    max_length=1024,  # max prompt + response length
    max_prompt_length=512,  # prompt-only truncation
)
dpo_trainer.train()
```

**Key beta values (DPO):**
- `0.5` — very conservative, minimal drift
- `0.1` — default, good balance
- `0.05` — stronger alignment, risk of forgetting
- `0.01` — aggressive, use only with high-quality data

**DPO loss variants** (set via `loss_type`):
- `"dpo"` (default) — standard DPO
- `"ipo"` — Identity Preference Optimization, more stable
- `"kto_pair"` — KTO-style pair loss
- `"cpo"` — Contrastive Preference Optimization
- `"simpo"` — SimPO, reference-model-free with length-normalized reward

### 3. GRPOTrainer — Group Relative Policy Optimization (v0.15+)

Best for **reasoning tasks** (math, code) where you can define reward functions.

```python
from trl import GRPOTrainer

# Define reward functions
def correctness_reward(prompts, completions, **kwargs):
    """Reward based on correct final answer (example for math)."""
    rewards = []
    for prompt, completion in zip(prompts, completions):
        if "answer" in completion.lower():
            rewards.append(1.0)
        else:
            rewards.append(0.0)
    return rewards

def format_reward(prompts, completions, **kwargs):
    """Reward for proper output format (e.g., <｜end▁of▁thinking｜>\n...)."""
    rewards = []
    for completion in completions:
        if "答" in completion:
            rewards.append(0.5)
        else:
            rewards.append(0.0)
    return rewards

trainer = GRPOTrainer(
    model=model,
    reward_funcs=[correctness_reward, format_reward],
    args=TrainingArguments(
        output_dir="./grpo-qwen",
        per_device_train_batch_size=4,
        gradient_accumulation_steps=2,
        learning_rate=5e-6,
        max_steps=100,
        fp16=True,
        report_to="none",
    ),
    train_dataset=dataset,  # just prompts!
)
trainer.train()
```

**Key details:**
- Generates `num_generations` (default 8) responses per prompt per step
- Reward functions receive: `prompts`, `completions`, plus optional `**kwargs`
- Returns list of float rewards (one per completion)
- Uses vLLM automatically if `vllm` is installed (set `use_vllm=False` to disable)
- No reference model needed — policy is self-regularizing
- **Loss types** (TRL v1): `loss_type="dapo"` (default), `"grpo"`, `"vespo"`, `"sapo"`, `"dr_grpo"`
- **Multi-environment** (TRL v1): Pass dict of reward function sets per env name
- **Liger Kernel**: Install `liger-kernel` for fused GRPO ops (~40% memory savings)

### 3b. RLOOTrainer — REINFORCE Leave-One-Out (TRL v1+)

```python
from trl import RLOOTrainer

# Similar API to GRPOTrainer but uses LOO variance reduction
trainer = RLOOTrainer(
    model=model,
    reward_funcs=[accuracy_reward],
    args=TrainingArguments(
        output_dir="./rloo-model",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=5e-6,
        max_steps=200,
    ),
    train_dataset=dataset,
)
trainer.train()
```

**Use when:** Reward distribution is naturally non-Gaussian (e.g., binary pass/fail, sparse rewards). RLOO's leave-one-out baseline handles non-smooth rewards better than GRPO's group normalization.

### 4. PPOTrainer — Classic RLHF Loop (🧪 Experimental)

```python
from trl import PPOTrainer, PPOConfig, AutoModelForCausalLMWithValueHead

# Full RLHF pipeline (requires a trained reward model)
ppo_model = AutoModelForCausalLMWithValueHead.from_pretrained("./sft-model")
ref_model = AutoModelForCausalLMWithValueHead.from_pretrained("./sft-model")

ppo_config = PPOConfig(
    model_name="./sft-model",
    learning_rate=1.41e-5,
    batch_size=16,
    mini_batch_size=4,
    gradient_accumulation_steps=2,
)

ppo_trainer = PPOTrainer(
    config=ppo_config,
    model=ppo_model,
    ref_model=ref_model,
    tokenizer=tokenizer,
    dataset=dataset,
)

# Training loop (manual iteration required)
for batch in ppo_trainer.dataloader:
    query_tensors = batch["input_ids"]
    # Generate responses
    response_tensors = ppo_trainer.generate(query_tensors, **gen_kwargs)
    # Score with reward model
    rewards = reward_model(query_tensors, response_tensors)
    # PPO step
    stats = ppo_trainer.step(query_tensors, response_tensors, rewards)
    ppo_trainer.log_stats(stats, batch, rewards)
```

### 5. RewardTrainer — Train a Reward Model

```python
from trl import RewardTrainer

reward_model = AutoModelForSequenceClassification.from_pretrained(
    "base-model", num_labels=1
)
# Or use AutoModelForCausalLMWithValueHead

trainer = RewardTrainer(
    model=reward_model,
    tokenizer=tokenizer,
    args=TrainingArguments(
        output_dir="./reward-model",
        per_device_train_batch_size=4,
        learning_rate=1e-5,
        max_steps=500,
    ),
    train_dataset=dpo_dataset,  # same chosen/rejected format
)
trainer.train()
```

### 6. KTOTrainer — Kahneman-Tversky Optimization ✅ (Stable since TRL v1)

KTO is now **stable** (graduated from 🧪). KTO only needs a completion + binary label (good/bad) — no paired data required.

```python
from trl import KTOTrainer

# Dataset format: {prompt, completion, label}
# label=True → desirable completion, label=False → undesirable
kto_trainer = KTOTrainer(
    model=model,
    ref_model=ref_model,  # auto-copies model if None
    tokenizer=tokenizer,
    args=TrainingArguments(...),
    train_dataset=kto_dataset,  # has prompt, completion, label
)
kto_trainer.train()
```

### 7. ORPOTrainer — Odds Ratio Preference Optimization

```python
from trl import ORPOTrainer

# No reference model needed! Uses odds ratio internally.
orpo_trainer = ORPOTrainer(
    model=model,
    tokenizer=tokenizer,
    args=TrainingArguments(...),
    train_dataset=dpo_dataset,  # chosen/rejected format
)
orpo_trainer.train()
```

## TRLPipeline — Chain SFT → Alignment

The high-level pipeline that runs SFT then DPO/GRPO in one workflow:

```python
from trl import TRLPipeline

pipeline = TRLPipeline(
    model_name="Qwen/Qwen2.5-1.5B",
    sft_dataset="HuggingFaceH4/ultrachat_200k",
    dpo_dataset="trl-lib/ultrafeedback_binarized",
    output_dir="./trl-pipeline-output",
    sft_args={"max_steps": 100, "learning_rate": 2e-4},
    dpo_args={"max_steps": 200, "beta": 0.1},
    use_peft=True,
    lora_r=16,
)
pipeline.run()  # runs SFT → saves → runs DPO → saves final
```

## Data Format Reference

### SFT Data
```json
// Option 1: Text field
{"text": "<|user|>Hello<|assistant|>Hi there!"}
// Option 2: Messages (use apply_chat_template)
{"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]}
// Option 3: Custom columns (use formatting_func)
{"prompt": "Hello", "completion": "Hi there!"}
```

### DPO / Reward Data
```json
{"prompt": "Hello", "chosen": "Hi there!", "rejected": "Go away"}
// Or messages format:
{
  "chosen": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}],
  "rejected": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Go away"}]
}
```

### GRPO Data
```json
{"prompt": "Solve: 2+2=?"}
// Reward functions compute scores from completions
```

### KTO Data
```json
{"prompt": "Hello", "completion": "Hi there!", "label": true}
{"prompt": "Hello", "completion": "Go away", "label": false}
```

## PEFT Integration

All TRL trainers accept `peft_config`. Best practices:

```python
peft_config = LoraConfig(
    r=16,  # rank — higher = more capacity, more memory
    lora_alpha=32,  # scaling factor — typically 2x r
    target_modules="all-linear",  # ~q_proj,v_proj,k_proj,o_proj,gate_proj,down_proj,up_proj
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# For DPO/GRPO, pass peft_config to the trainer
# After training, merge if needed:
from peft import PeftModel
merged = PeftModel.from_pretrained(base_model, adapter_path).merge_and_unload()
```

## vLLM Integration

All ⚡️-marked online trainers (GRPO, RLOO, OnlineDPO, NashMD, XPO) use vLLM for fast rollout generation:

- **GRPOTrainer** auto-detects vLLM and uses it by default
- **Co-location mode** (vllm_device="cuda:0") runs vLLM on the same GPU as training, sharing memory
- **Separate GPU mode** (vllm_device="cuda:1") runs vLLM on a dedicated GPU for maximum throughput
- **LoRA support**: Set `vllm_enable_lora=True` in trainer config for PEFT + vLLM

```python
# Install: pip install vllm
# Use vLLM backend (faster generation):
trainer = GRPOTrainer(
    model=model,
    reward_funcs=[...],
    args=...,
    train_dataset=dataset,
    use_vllm=True,  # default if vllm installed
    vllm_device="cuda:0",  # same GPU or separate
    vllm_gpu_memory_utilization=0.3,  # reserve memory for training
    vllm_enable_lora=False,  # set True for PEFT + vLLM
)
```

For PPO, vLLM replaces the model's own generate for rollout collection.

## Common Pitfalls

1. **Skipping SFT before alignment** — DPO/GRPO on a base model is much worse. Always SFT first.
2. **Wrong data format** — DPO expects `{prompt, chosen, rejected}` keys, not just `{input, output}`. KTO expects `{prompt, completion, label}` (binary). GRPO expects just `{prompt}` + reward functions.
3. **Reference model mismatch** — DPO ref_model must be the same as the SFT model state; use `ref_model=None` to auto-copy. For KTO, ref_model is also required.
4. **Packing DPOTrainer** — DPO does NOT support `packing=True` (unlike SFT). Each row must be a single example. Same for KTO and all non-SFT trainers.
5. **GRPO with tiny batch** — GRPO needs 8+ generations per prompt to get meaningful group-relative advantages. RLOO can work with fewer if rewards are sparse.
6. **Tokenizer padding side** — Set `tokenizer.pad_token = tokenizer.eos_token` and `padding_side="right"` (or "left" for DPO).
7. **vLLM + online training memory** — vLLM consumes ~30% extra GPU memory. Subtract via `vllm_gpu_memory_utilization`. Liger Kernel reduces GRPO memory by ~40%.
8. **TRLPipeline multiple GPUs** — Not well tested with distributed. Use individual trainers for multi-GPU.
9. **Beta too low in DPO** — Beta < 0.01 can cause collapse. Keep between 0.01 and 0.5.
10. **Reward over-optimization** — Train reward models on diverse data; eval on held-out prompts to detect hacking.
11. **KTO without ref_model** — Unlike CPO/ORPO, KTO still requires a reference model. Use `ref_model=None` to auto-copy from model.
12. **DPO loss_type selection** — TRL v1 supports: `"dpo"`, `"ipo"`, `"kto_pair"`, `"cpo"`, `"simpo"`. IPO is more stable but slower convergence. SimPO is reference-model-free.
13. **GRPO loss_type="dapo" is default** — DAPO uses token-level normalization to avoid length bias. If you notice training instability with very long sequences, switch to `loss_type="grpo"` (sample-level).
14. **Process rewards (PRM)** — PRMTrainer is experimental. Requires step-level reward annotations. Useful for math/code chain-of-thought evaluation.

## Evaluation

```python
# After training, test generation
from transformers import pipeline
pipe = pipeline("text-generation", model=trained_model, tokenizer=tokenizer)
print(pipe("Explain RLHF in one sentence:", max_new_tokens=100)[0]["generated_text"])

# For DPO/GRPO comparison, compute reward scores
# Use lm-eval-harness for standardized benchmarks
# Or load a reward model to score outputs
```

## Memory Optimization Tips

| Technique | Memory Savings | Trade-off |
|-----------|---------------|-----------|
| QLoRA (4-bit) | ~4x | Slightly lower quality |
| Gradient checkpointing | ~30% | 20% slower |
| Sequence packing (SFT) | 2-3x throughput | Slightly harder debugging |
| Smaller batch size + grad accum | Constant memory | More step time |
| remove_unused_columns=True | Minimal | Loses metadata |
| fp16/bf16 | ~2x | bf16 preferred for stability |

## References

See [`references/external-links.md`](references/external-links.md) for paper links, release notes, and a recommended reading order.

- [TRL Documentation v1.9.0](https://huggingface.co/docs/trl/en/index) — Full API
- [TRL GitHub](https://github.com/huggingface/trl) — Source code, issues, examples
- [TRL v1 Blog Post](https://huggingface.co/blog/trl-v1) — Major release announcement (March 2026)
- [OpenEnv](https://huggingface.co/blog/openenv) — Open agent evaluation environment
- [smol-course](https://github.com/huggingface/smol-course) — Learn post-training with TRL
- [HF Alignment Handbook](https://github.com/huggingface/alignment-handbook)
