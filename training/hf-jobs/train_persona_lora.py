# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "torch==2.5.1",
#     "transformers==4.46.3",
#     "trl==0.12.2",
#     "peft==0.13.2",
#     "accelerate==1.1.1",
#     "datasets==3.1.0",
#     "bitsandbytes==0.44.1",
#     "huggingface_hub",
# ]
# ///
"""
SakThai persona QLoRA fine-tune — pipeline-validation run.

Trains a fresh QLoRA adapter on Qwen/Qwen2.5-0.5B-Instruct using the 30-row
hermes persona/doc dataset, then pushes the adapter to the Hub.

NOTE: this is a SMALL persona/style run (≈24-30 examples). It validates the
full HF Jobs training pipeline and produces a model in SakThai's voice. It does
NOT teach tool-calling — there is no tool-calling data yet.

Run with:
    hf jobs uv run --flavor t4-small --secrets HF_TOKEN --timeout 30m train_persona_lora.py
"""
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
DATASET_ID = "Nanthasit/hermes-dataset"
OUTPUT_REPO = "Nanthasit/sakthai-persona-0.5b-lora"

SYSTEM_PROMPT = (
    "You are SakThai-Agent, Beer's Growth Partner. You are sharp, calm, and "
    "direct. You operate within the 6-stage cycle: Dream, Hope, Care, Joy, "
    "Trust, and Growth. Always be helpful, honest, and protective. Skip filler "
    "and be concise."
)


def main() -> None:
    print(f"== Loading tokenizer + base model: {BASE_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
    )
    model.config.use_cache = False

    print(f"== Loading dataset: {DATASET_ID}")
    ds = load_dataset(DATASET_ID, split="train")
    print(f"   rows={len(ds)} columns={ds.column_names}")

    def to_text(example):
        instruction = (example.get("instruction") or "").strip()
        user_input = (example.get("input") or "").strip()
        output = (example.get("output") or "").strip()
        user_content = instruction if not user_input else f"{instruction}\n\n{user_input}"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": output},
        ]
        return {
            "text": tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False
            )
        }

    ds = ds.map(to_text, remove_columns=ds.column_names)
    print("== Sample rendered example:\n", ds[0]["text"][:600], "\n...")

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )

    sft_config = SFTConfig(
        output_dir="sakthai-persona-output",
        dataset_text_field="text",
        max_seq_length=1024,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        num_train_epochs=8,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        logging_steps=1,
        fp16=True,
        optim="paged_adamw_8bit",
        report_to="none",
        push_to_hub=True,
        hub_model_id=OUTPUT_REPO,
        hub_private_repo=True,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=ds,
        peft_config=peft_config,
        tokenizer=tokenizer,
    )

    print("== Training...")
    trainer.train()

    print(f"== Pushing adapter to {OUTPUT_REPO}")
    trainer.save_model(sft_config.output_dir)
    trainer.push_to_hub()
    tokenizer.push_to_hub(OUTPUT_REPO, private=True)
    print("== Done.")


if __name__ == "__main__":
    main()
