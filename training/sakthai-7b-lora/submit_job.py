#!/usr/bin/env python3
"""Submit 7B training to HF Jobs."""
import sys
sys.path.insert(0, '/opt/data/.venv/lib/python3.13/site-packages')
from huggingface_hub import run_uv_job

token = open('/opt/data/profiles/sakthai/home/.cache/huggingface/token').read().strip()

job = run_uv_job(
    script="/opt/data/train_7b_v2.py",
    flavor="a10g-small",
    dependencies=[
        "transformers", "peft", "trl", "accelerate", "bitsandbytes",
        "datasets", "sentencepiece", "huggingface_hub", "torch",
    ],
    timeout="2h",
    secrets={"HF_TOKEN": token},
)
print(f"Job submitted: {job.id}")
print(f"Status: {job.status}")
print(f"Flavor: {job.flavor}")