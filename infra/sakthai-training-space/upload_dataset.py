# upload_dataset.py
# Push the JSONL dataset to the Hugging Face Hub as a Dataset repository.
# Usage: python upload_dataset.py --token hf_...

import argparse
from pathlib import Path

from datasets import Dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", default="data/sakthai_cycle_6_sft.jsonl")
    parser.add_argument("--repo_id", default="Nanthasit/sakthai-cycle-6-sft")
    parser.add_argument("--token", required=True)
    args = parser.parse_args()

    ds = Dataset.from_json(str(Path(args.jsonl).resolve()))
    print(f"Loaded {len(ds)} examples")

    ds.push_to_hub(
        args.repo_id,
        token=args.token,
        private=False,
        commit_message="Add SakThai 6-cycle SFT dataset",
    )
    print(f"Pushed to https://huggingface.co/datasets/{args.repo_id}")


if __name__ == "__main__":
    main()
