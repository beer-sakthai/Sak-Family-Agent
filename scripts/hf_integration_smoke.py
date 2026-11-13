"""Live Hugging Face smoke test for CI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "personas" / "sakthai") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

from sakthai.agent.tools import tool_by_name
from sakthai.memory.store import MemoryStore


def main() -> None:
    tool = tool_by_name("huggingface_inference")
    if tool is None:
        raise RuntimeError("huggingface_inference tool is not registered")
    with MemoryStore() as store:
        result = tool.handler(
            {
                "prompt": "Reply with exactly: Sak Family HF integration is working.",
                "model": os.environ.get("SAKTHAI_HF_SMOKE_MODEL", "google/gemma-2-2b-it"),
                "max_tokens": 32,
            },
            store,
        )
    if "Sak Family HF integration is working" not in result:
        raise RuntimeError(f"Unexpected Hugging Face response: {result!r}")
    print("Hugging Face live integration passed.")


if __name__ == "__main__":
    main()
