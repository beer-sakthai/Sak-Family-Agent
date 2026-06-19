# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "torch==2.5.1",
#     "transformers==4.46.3",
#     "peft==0.13.2",
#     "accelerate==1.1.1",
# ]
# ///
"""
Smoke-test the SakThai tool-calling adapter.

Loads the Qwen2.5 base + the LoRA adapter, then runs a handful of prompts —
some that *should* trigger a tool call and some that should be answered
directly — and prints what the model emits. Use this to confirm the fine-tune
actually learned the tool-call format before wiring it into the agent or
deploying it.

Reuses the single source of tool/system definitions from the dataset builder
(../hf-jobs/build_toolcalling_dataset.py) so eval matches training exactly.

Run locally (GPU recommended, CPU works slowly):
    uv run training/serving/eval_toolcalling.py

Or on HF Jobs (no local GPU):
    hf jobs uv run --flavor t4-small --secrets HF_TOKEN training/serving/eval_toolcalling.py

Knobs via env:
    BASE_MODEL    default Qwen/Qwen2.5-1.5B-Instruct
    ADAPTER_REPO  default Nanthasit/sakthai-toolcalling-1.5b-lora
"""
import os
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Reuse the exact TOOLS / SYSTEM_PROMPT the model was trained on.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hf-jobs"))
from build_toolcalling_dataset import TOOLS, SYSTEM_PROMPT  # noqa: E402

BASE_MODEL = os.environ.get("BASE_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
ADAPTER_REPO = os.environ.get("ADAPTER_REPO", "Nanthasit/sakthai-toolcalling-1.5b-lora")

# (prompt, expectation) — expectation is just a human hint printed alongside output.
PROBES = [
    ("Remember that I prefer dark mode in all my apps.", "-> learn"),
    ("What do you have saved about my startup?", "-> search"),
    ("Run `git status` for me.", "-> run_command"),
    ("Delete fact 7.", "-> forget"),
    ("Text me on Telegram: standup in 10 minutes.", "-> send_telegram_message"),
    ("What does the Dream stage mean?", "-> answer directly, no tool"),
    ("What's 12 times 11?", "-> answer directly, no tool"),
]


def main() -> None:
    print(f"== Loading base {BASE_MODEL} + adapter {ADAPTER_REPO}")
    tokenizer = AutoTokenizer.from_pretrained(ADAPTER_REPO)
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    model = PeftModel.from_pretrained(base, ADAPTER_REPO)
    model.eval()

    for prompt, hint in PROBES:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        inputs = tokenizer.apply_chat_template(
            messages,
            tools=TOOLS,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(model.device)
        with torch.no_grad():
            out = model.generate(
                inputs,
                max_new_tokens=256,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )
        completion = tokenizer.decode(out[0][inputs.shape[-1]:], skip_special_tokens=False)
        print("\n" + "=" * 72)
        print(f"USER: {prompt}   (expected {hint})")
        print(f"MODEL: {completion.strip()}")


if __name__ == "__main__":
    main()
