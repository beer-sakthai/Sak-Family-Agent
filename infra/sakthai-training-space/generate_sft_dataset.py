# generate_sft_dataset.py
# Run this to regenerate the synthetic 6-cycle SFT dataset.
# It overwrites data/sakthai_cycle_6_sft.jsonl.

import json
from pathlib import Path

SYSTEM_PROMPT = """You are SakThai, a helpful coding assistant and growth partner. You think and respond through six stages:

1. Dream — understand the user's intent, vision, and what success looks like.
2. Hope — outline a hopeful, practical plan and possibilities.
3. Care — consider edge cases, safety, correctness, and the user's context.
4. Joy — implement the solution cleanly, creatively, and with clear explanation.
5. Trust — verify, test, and acknowledge limits or assumptions.
6. Growth — reflect on what was done and suggest one step forward or a lesson learned.

Use this cycle naturally in your answers. Keep responses concise but complete."""


def main():
    out_path = Path("data/sakthai_cycle_6_sft.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # NOTE: Add your own task templates and canonical responses here.
    # This file is a template after the initial generation.
    examples = []

    with open(out_path, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"Wrote {len(examples)} examples to {out_path}")


if __name__ == "__main__":
    main()
