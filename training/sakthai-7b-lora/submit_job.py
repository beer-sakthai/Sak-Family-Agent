# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "huggingface_hub>=0.27.0",
# ]
# ///
#!/usr/bin/env python3
"""Submit SakThai 7B training job to Hugging Face Jobs."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from huggingface_hub import get_token, run_uv_job


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit SakThai 7B training to HF Jobs.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print job submission plan without executing."
    )
    parser.add_argument(
        "--flavor", default="a10g-small", help="HF Jobs hardware flavor (default: a10g-small)."
    )
    parser.add_argument("--timeout", default="2h", help="Job timeout limit (default: 2h).")
    args = parser.parse_args()

    train_script = Path(__file__).resolve().parent / "train.py"
    token = os.environ.get("HF_TOKEN") or get_token()

    plan = (
        f"HF Jobs 7B Training Submission Plan:\n"
        f"  Script : {train_script}\n"
        f"  Flavor : {args.flavor}\n"
        f"  Timeout: {args.timeout}\n"
        f"  Auth   : {'HF_TOKEN present' if token else 'No token found'}"
    )

    if args.dry_run:
        print(f"[dry-run] {plan}")
        return

    if not token:
        raise SystemExit("Error: HF_TOKEN is required to submit training jobs to Hugging Face.")

    print(f"Submitting job...\n{plan}")
    job = run_uv_job(
        script=str(train_script),
        flavor=args.flavor,
        dependencies=[
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
        timeout=args.timeout,
        secrets={"HF_TOKEN": token},
    )
    print(f"Job submitted: {job.id}")
    print(f"Status: {job.status}")
    print(f"Flavor: {job.flavor}")


if __name__ == "__main__":
    main()
