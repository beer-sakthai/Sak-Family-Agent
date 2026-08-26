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
"""Train and evaluate the SakThai 1.5B coding adapter on a Hugging Face GPU.

The run keeps a deterministic holdout split, reports holdout loss/perplexity,
checks whether generated Python probes compile, and uploads ``eval-results.json``
with the adapter. The published repository is private by default.

Run on Hugging Face Jobs::

    hf jobs uv run --flavor l4x1 --secrets HF_TOKEN --timeout 2h \
      training/hf-jobs/train_eval_coder_lora.py

Environment overrides:
    BASE_MODEL   (Qwen/Qwen2.5-Coder-1.5B-Instruct)
    DATASET_ID   (Nanthasit/sakthai-combined-v6)
    OUTPUT_REPO  (Nanthasit/sakthai-coder-1.5b-v2-lora)
    EPOCHS       (3)
"""

from __future__ import annotations

import ast
import json
import math
import os
import re
from typing import Any

import torch
from datasets import Dataset, DatasetDict, load_dataset
from huggingface_hub import HfApi
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

_DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
_DEFAULT_BASE_REVISION = "2e1fd397ee46e1388853d2af2c993145b0f1098a"
BASE_MODEL = os.environ.get("BASE_MODEL", _DEFAULT_BASE_MODEL)
# Pinned to an immutable commit (bandit B615). A mutable branch ref lets an
# upstream force-push silently change what this job downloads, and an unpinned
# run is not reproducible. Only the default model carries the pin — an override
# supplies its own revision, or tracks that repo's default branch.
BASE_MODEL_REVISION = os.environ.get(
    "BASE_MODEL_REVISION",
    _DEFAULT_BASE_REVISION if BASE_MODEL == _DEFAULT_BASE_MODEL else None,
)
DATASET_ID = os.environ.get("DATASET_ID", "Nanthasit/sakthai-combined-v6")
OUTPUT_REPO = os.environ.get("OUTPUT_REPO", "Nanthasit/sakthai-coder-1.5b-v2-lora")
EPOCHS = float(os.environ.get("EPOCHS", "3"))
RESULTS_FILE = "eval-results.json"

SYSTEM_PROMPT = (
    "You are SakThai Coder, a precise software-engineering assistant. Produce secure, "
    "maintainable code, explain important trade-offs concisely, and follow the user's constraints."
)

CODE_PROBES = (
    "Write a typed Python function named clamp that limits a float to an inclusive range.",
    "Write a Python function named unique_ordered that removes duplicates while preserving order.",
    "Write a Python function named is_safe_relative_path that rejects absolute paths and '..'.",
)


def _messages_for_row(row: dict[str, Any]) -> list[dict[str, str]] | None:
    """Convert supported Hub dataset row layouts to chat messages."""
    messages = row.get("messages")
    if isinstance(messages, list) and messages:
        normalized = []
        for message in messages:
            if not isinstance(message, dict) or message.get("role") not in {
                "system",
                "user",
                "assistant",
            }:
                return None
            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                return None
            normalized.append({"role": message["role"], "content": content.strip()})
        return normalized

    instruction = row.get("instruction") or row.get("prompt") or row.get("question")
    answer = row.get("output") or row.get("response") or row.get("answer")
    if not isinstance(instruction, str) or not isinstance(answer, str):
        return None
    user_input = row.get("input")
    if isinstance(user_input, str) and user_input.strip():
        instruction = f"{instruction.strip()}\n\n{user_input.strip()}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": instruction.strip()},
        {"role": "assistant", "content": answer.strip()},
    ]


def _extract_python(text: str) -> str:
    """Extract the first fenced Python block, falling back to the full response."""
    match = re.search(r"```(?:python|py)?\s*\n(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()


def _python_compiles(text: str) -> bool:
    try:
        ast.parse(_extract_python(text))
    except SyntaxError:
        return False
    return True


def _prepare_splits(raw: DatasetDict, tokenizer: Any) -> tuple[Dataset, Dataset]:
    source = raw["train"] if "train" in raw else next(iter(raw.values()))

    def render(row: dict[str, Any]) -> dict[str, str | bool]:
        messages = _messages_for_row(row)
        if not messages:
            return {"text": "", "valid": False}
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": text, "valid": True}

    rendered = source.map(render, remove_columns=source.column_names).filter(
        lambda row: row["valid"]
    )
    rendered = rendered.remove_columns("valid")
    if len(rendered) < 10:
        raise ValueError(f"Dataset must contain at least 10 usable rows; found {len(rendered)}")

    if "test" in raw:
        holdout = raw["test"].map(render, remove_columns=raw["test"].column_names)
        holdout = holdout.filter(lambda row: row["valid"]).remove_columns("valid")
        if len(holdout):
            return rendered, holdout
    split = rendered.train_test_split(test_size=0.1, seed=42)
    return split["train"], split["test"]


def _run_code_probes(model: Any, tokenizer: Any) -> list[dict[str, Any]]:
    results = []
    for prompt in CODE_PROBES:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(model.device)
        with torch.no_grad():
            output = model.generate(
                inputs,
                max_new_tokens=256,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )
        completion = tokenizer.decode(output[0][inputs.shape[-1] :], skip_special_tokens=True)
        results.append(
            {"prompt": prompt, "completion": completion, "compiles": _python_compiles(completion)}
        )
    return results


def main() -> None:
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL, revision=BASE_MODEL_REVISION, trust_remote_code=False
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        revision=BASE_MODEL_REVISION,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        ),
        device_map="auto",
        trust_remote_code=False,
    )
    model.config.use_cache = False

    # Own-namespace dataset, republished by this project's own pipeline;
    # pinning it would train against a stale snapshot of our own data.
    train_dataset, eval_dataset = _prepare_splits(
        load_dataset(DATASET_ID),  # nosec B615
        tokenizer,
    )
    print(f"train rows={len(train_dataset)} eval rows={len(eval_dataset)}")

    trainer = SFTTrainer(
        model=model,
        args=SFTConfig(
            output_dir="sakthai-coder-output",
            dataset_text_field="text",
            max_seq_length=2048,
            packing=False,
            per_device_train_batch_size=1,
            per_device_eval_batch_size=1,
            gradient_accumulation_steps=8,
            learning_rate=2e-4,
            num_train_epochs=EPOCHS,
            warmup_ratio=0.05,
            lr_scheduler_type="cosine",
            logging_steps=5,
            bf16=True,
            optim="paged_adamw_8bit",
            gradient_checkpointing=True,
            eval_strategy="epoch",
            save_strategy="epoch",
            save_total_limit=1,
            report_to="none",
            push_to_hub=True,
            hub_model_id=OUTPUT_REPO,
            hub_private_repo=True,
        ),
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        peft_config=LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=[
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
        ),
        tokenizer=tokenizer,
    )

    trainer.train()
    metrics = trainer.evaluate()
    eval_loss = float(metrics["eval_loss"])
    probes = _run_code_probes(trainer.model, tokenizer)
    report = {
        "base_model": BASE_MODEL,
        "dataset": DATASET_ID,
        "output_repo": OUTPUT_REPO,
        "eval_loss": eval_loss,
        "perplexity": math.exp(min(eval_loss, 20)),
        "python_compile_rate": sum(item["compiles"] for item in probes) / len(probes),
        "probes": probes,
    }
    with open(RESULTS_FILE, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    trainer.save_model(trainer.args.output_dir)
    trainer.push_to_hub()
    tokenizer.push_to_hub(OUTPUT_REPO, private=True)
    HfApi().upload_file(
        path_or_fileobj=RESULTS_FILE,
        path_in_repo=RESULTS_FILE,
        repo_id=OUTPUT_REPO,
        repo_type="model",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
