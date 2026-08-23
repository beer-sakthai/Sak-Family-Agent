# scripts/sft_cycle6.py
# SFT fine-tune Nanthasit/sakthai-coder-3b on the SakThai 6-cycle dataset.
# Designed for a Docker GPU Space with TRL + DeepSpeed installed.

import os
import sys
from dataclasses import dataclass, field
from typing import Optional

from datasets import load_dataset
from peft import LoraConfig, TaskType
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    HfArgumentParser,
    TrainingArguments,
)
from trl import SFTConfig, SFTTrainer


@dataclass
class ScriptArguments:
    model_name: str = field(default="Nanthasit/sakthai-coder-3b")
    dataset_name: str = field(default="Nanthasit/sakthai-cycle-6-sft")
    output_dir: str = field(default="/workspace/outputs/sakthai-coder-3b-cycle6")
    num_train_epochs: float = field(default=3.0)
    per_device_train_batch_size: int = field(default=1)
    gradient_accumulation_steps: int = field(default=4)
    learning_rate: float = field(default=2.5e-5)
    max_seq_length: int = field(default=2048)
    lora_r: int = field(default=32)
    lora_alpha: int = field(default=64)
    lora_dropout: float = field(default=0.05)
    use_lora: bool = field(default=True)
    deepspeed: Optional[str] = field(default="/workspace/configs/deepspeed_zero2.json")
    bf16: bool = field(default=True)
    fp16: bool = field(default=False)
    report_to: str = field(default="none")
    push_to_hub: bool = field(default=False)
    hub_model_id: Optional[str] = field(default=None)


def main():
    parser = HfArgumentParser((ScriptArguments, TrainingArguments))
    args, training_args = parser.parse_args_into_dataclasses()

    # Patch TrainingArguments with SFT-specific fields via SFTConfig
    sft_config = SFTConfig(
        output_dir=args.output_dir,
        num_train_epochs=args.num_train_epochs,
        per_device_train_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=2,
        bf16=args.bf16,
        fp16=args.fp16,
        deepspeed=args.deepspeed if args.deepspeed else None,
        report_to=args.report_to if args.report_to != "none" else [],
        push_to_hub=args.push_to_hub,
        hub_model_id=args.hub_model_id,
        max_seq_length=args.max_seq_length,
        packing=False,
        dataset_text_field="messages",
    )

    # Merge any explicit TrainingArguments CLI overrides that SFTConfig didn't capture
    for k, v in vars(training_args).items():
        if hasattr(sft_config, k) and v is not None:
            setattr(sft_config, k, v)

    print(f"Loading model: {args.model_name}")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        trust_remote_code=True,
        torch_dtype="auto",
        device_map=None,  # let DeepSpeed / Accelerate handle placement
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    print(f"Loading dataset: {args.dataset_name}")
    dataset = load_dataset(args.dataset_name, split="train")

    peft_config = None
    if args.use_lora:
        print("Using LoRA")
        peft_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            bias="none",
        )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=sft_config,
        peft_config=peft_config,
    )

    trainer.train()

    print(f"Saving final model to {args.output_dir}")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    if args.push_to_hub:
        print("Pushing to Hub...")
        trainer.push_to_hub()

    print("Training complete.")


if __name__ == "__main__":
    main()
