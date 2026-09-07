"""Live Hugging Face smoke test for CI."""

from __future__ import annotations

import os

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
