#!/usr/bin/env python3
"""SakThai 7B LoRA training — simpler version for HF Jobs."""

import json
import os
import subprocess
import sys
import tempfile

# ── Config ────────────────────────────────────────────────────────
BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
# Pinned to an immutable commit (bandit B615). A mutable branch ref lets an
# upstream force-push silently change what this job downloads, and an unpinned
# run is not reproducible.
BASE_MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
DATASET_ID = "Nanthasit/sakthai-combined-v5"
ADAPTER_REPO = "Nanthasit/sakthai-context-7b-tools"

# Training artefacts land in a private per-run directory (mkdtemp is 0700)
# rather than a fixed /tmp path (bandit B108): a predictable name in a
# world-writable directory can be pre-created or symlinked by another user
# before this process writes to it.
ARTIFACT_DIR = os.environ.get("SAKTHAI_ARTIFACT_DIR") or tempfile.mkdtemp(prefix="sakthai-7b-")
ADAPTER_DIR = os.path.join(ARTIFACT_DIR, "7b-adapter")
METRICS_PATH = os.path.join(ARTIFACT_DIR, "metrics.json")

LORA_R = 16
LORA_ALPHA = 32
LR = 5e-5
NUM_EPOCHS = 4
BATCH_SIZE = 2
GRAD_ACCUM = 8
MAX_STEPS = 300
MAX_SEQ_LEN = 2048

print("=== Starting 7B training ===", flush=True)
print(f"BASE_MODEL={BASE_MODEL}, DATASET={DATASET_ID}", flush=True)

# ── Install deps ──────────────────────────────────────────────────
subprocess.run(
    [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-q",
        "transformers",
        "peft",
        "trl",
        "accelerate",
        "bitsandbytes",
        "datasets",
        "sentencepiece",
        "huggingface_hub",
        "torch",
    ],
    check=True,
)
print("Deps installed", flush=True)

# ── Auth (HF_TOKEN env var or file) ────────────────────────────────
from huggingface_hub import HfApi

token = os.environ.get("HF_TOKEN", "")
if not token:
    token_path = os.path.expanduser("~/.cache/huggingface/token")
    token = open(token_path).read().strip()
api = HfApi(token=token)
print(f"Auth OK: {api.whoami()['name']}", flush=True)

# ── Load dataset ──────────────────────────────────────────────────
from datasets import load_dataset

print("Loading dataset...", flush=True)
# Own-namespace dataset, republished by this project's own pipeline;
# pinning it would train against a stale snapshot of our own data.
dataset = load_dataset(DATASET_ID, split="train")  # nosec B615
print(f"Loaded {len(dataset)} examples", flush=True)


def fmt(msgs):
    text = ""
    for m in msgs:
        role = m["role"]
        if role == "system":
            text += f"<|im_start|>system\n{m['content']}<|im_end|>\n"
        elif role == "user":
            text += f"<|im_start|>user\n{m['content']}<|im_end|>\n"
        elif role == "assistant":
            if "tool_calls" in m:
                text += f"<|im_start|>assistant\n{json.dumps(m['tool_calls'])}<|im_end|>\n"
            else:
                text += f"<|im_start|>assistant\n{m['content']}<|im_end|>\n"
        elif role == "tool":
            text += f"<|im_start|>tool\n{m['content']}<|im_end|>\n"
    text += "<|im_start|>assistant\n"
    return text


dataset = dataset.map(lambda x: {"text": fmt(x["messages"])})
split = dataset.train_test_split(test_size=50, seed=42)
print(f"Train: {len(split['train'])}, Eval: {len(split['test'])}", flush=True)

# ── Load model ────────────────────────────────────────────────────
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)
print("Loading model...", flush=True)
model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    revision=BASE_MODEL_REVISION,
    quantization_config=bnb,
    device_map="auto",
    torch_dtype="auto",
    trust_remote_code=True,
)
tok = AutoTokenizer.from_pretrained(
    BASE_MODEL, revision=BASE_MODEL_REVISION, trust_remote_code=True
)
tok.pad_token = tok.eos_token
tok.padding_side = "right"
print(f"Loaded. Params: {model.num_parameters():,}", flush=True)

# ── LoRA ──────────────────────────────────────────────────────────
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

model = prepare_model_for_kbit_training(model)
lora = LoraConfig(
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora)
model.print_trainable_parameters()

# ── Training ──────────────────────────────────────────────────────
from trl import SFTConfig, SFTTrainer

args = SFTConfig(
    output_dir="/data/7b-lora",
    num_train_epochs=NUM_EPOCHS,
    max_steps=MAX_STEPS,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRAD_ACCUM,
    gradient_checkpointing=True,
    optim="paged_adamw_8bit",
    learning_rate=LR,
    lr_scheduler_type="linear",
    warmup_ratio=0.05,
    bf16=True,
    logging_steps=10,
    save_strategy="steps",
    save_steps=50,
    eval_strategy="steps",
    eval_steps=50,
    dataset_text_field="text",
    packing=False,
    report_to="none",
    remove_unused_columns=False,
)

# TRL dynamic loader: detect correct arg name at runtime
import inspect

sig_trainer = inspect.signature(SFTTrainer.__init__)
arg_name = "processing_class" if "processing_class" in sig_trainer.parameters else "tokenizer"
print(f"TRL detected, using argument: {arg_name}", flush=True)

trainer = SFTTrainer(
    model=model,
    args=args,
    train_dataset=split["train"],
    eval_dataset=split["test"],
    **{arg_name: tok},
)

print("Training...", flush=True)
trainer.train()
print("Done training!", flush=True)

# ── Save & push ───────────────────────────────────────────────────
trainer.save_model(ADAPTER_DIR)
tok.save_pretrained(ADAPTER_DIR)
print(f"Pushing to {ADAPTER_REPO}...", flush=True)
api.create_repo(ADAPTER_REPO, exist_ok=True)
api.upload_folder(
    folder_path=ADAPTER_DIR,
    repo_id=ADAPTER_REPO,
    repo_type="model",
    commit_message="SakThai 7B LoRA adapter",
)
print(f"Pushed! https://huggingface.co/{ADAPTER_REPO}", flush=True)

# ── Metrics ───────────────────────────────────────────────────────
log = trainer.state.log_history
with open(METRICS_PATH, "w") as f:
    json.dump({"base": BASE_MODEL, "dataset": DATASET_ID, "log": log}, f, indent=2)
api.upload_file(
    path_or_fileobj=METRICS_PATH,
    path_in_repo="training_metrics.json",
    repo_id=ADAPTER_REPO,
    repo_type="model",
)

final_loss = None
for e in log:
    if "loss" in e:
        final_loss = e["loss"]
print(f"Final loss: {final_loss}", flush=True)
print("=== DONE ===", flush=True)
