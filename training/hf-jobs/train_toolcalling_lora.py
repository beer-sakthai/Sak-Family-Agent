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
SakThai tool-calling QLoRA fine-tune.

Teaches a Qwen2.5-Instruct base to call SakThai-Agent's 8 BUILTIN_TOOLS (and to
answer directly when no tool is needed), by SFT on the messages+tools dataset
`Nanthasit/sakthai-toolcalling-v1`. Each row is rendered with the model's own
chat template via `tokenizer.apply_chat_template(..., tools=...)`, so the model
learns the exact `<tool_call>` serialization Qwen emits at inference time.

Unlike train_persona_lora.py (which only teaches voice/style on the hermes data),
this run teaches *behaviour*: when and how to emit a tool call.

Run on HF Jobs (no local GPU needed):
    hf jobs uv run --flavor l4x1 --secrets HF_TOKEN --timeout 1h train_toolcalling_lora.py

`--secrets HF_TOKEN` forwards your local token so the job can pull the (private)
base/dataset and `push_to_hub`. Monitor with `hf jobs logs -f <id>`.

Knobs via env (all optional):
    BASE_MODEL   default Qwen/Qwen2.5-1.5B-Instruct  (set Qwen/Qwen2.5-3B-Instruct for more capacity)
    OUTPUT_REPO  default Nanthasit/sakthai-toolcalling-1.5b-lora
    DATASET_ID   default Nanthasit/sakthai-toolcalling-v1
    EPOCHS       default 4
"""
import json
import os

import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

BASE_MODEL = os.environ.get("BASE_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
DATASET_ID = os.environ.get("DATASET_ID", "Nanthasit/sakthai-toolcalling-v1")
OUTPUT_REPO = os.environ.get("OUTPUT_REPO", "Nanthasit/sakthai-toolcalling-1.5b-lora")
EPOCHS = float(os.environ.get("EPOCHS", "4"))


def _normalize_messages(messages):
    """Coerce dataset rows back to the shape Qwen's chat template expects.

    The dataset stores tool-call `arguments` as a JSON object, but some loaders
    surface it as a JSON string. Qwen's template calls `arguments | tojson`, so
    we make sure it's always a dict.
    """
    out = []
    for m in messages:
        msg = {"role": m["role"], "content": m.get("content") or ""}
        calls = m.get("tool_calls")
        if calls:
            norm_calls = []
            for c in calls:
                fn = c["function"]
                args = fn.get("arguments")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except (json.JSONDecodeError, TypeError):
                        args = {}
                norm_calls.append(
                    {"type": "function", "function": {"name": fn["name"], "arguments": args}}
                )
            msg["tool_calls"] = norm_calls
        out.append(msg)
    return out


def main() -> None:
    print(f"== Loading tokenizer + base model: {BASE_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
    )
    model.config.use_cache = False

    print(f"== Loading dataset: {DATASET_ID}")
    ds = load_dataset(DATASET_ID)
    print(f"   splits={list(ds.keys())}")

    def to_text(example):
        text = tokenizer.apply_chat_template(
            _normalize_messages(example["messages"]),
            tools=example["tools"],
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": text}

    train_ds = ds["train"].map(to_text, remove_columns=ds["train"].column_names)
    eval_ds = (
        ds["test"].map(to_text, remove_columns=ds["test"].column_names)
        if "test" in ds
        else None
    )
    print(f"   train rows={len(train_ds)}", f"eval rows={len(eval_ds)}" if eval_ds else "")
    print("== Sample rendered example:\n", train_ds[0]["text"][:900], "\n...")

    # Wider target_modules than the persona run: tool-calling needs MLP capacity,
    # not just attention, to learn argument formatting reliably.
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )

    sft_config = SFTConfig(
        output_dir="sakthai-toolcalling-output",
        dataset_text_field="text",
        max_seq_length=2048,  # tool defs are long; don't truncate them away
        packing=False,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        num_train_epochs=EPOCHS,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        logging_steps=1,
        bf16=True,
        optim="paged_adamw_8bit",
        gradient_checkpointing=True,
        eval_strategy="epoch" if eval_ds else "no",
        save_strategy="epoch",
        save_total_limit=1,
        report_to="none",
        push_to_hub=True,
        hub_model_id=OUTPUT_REPO,
        hub_private_repo=True,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
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
