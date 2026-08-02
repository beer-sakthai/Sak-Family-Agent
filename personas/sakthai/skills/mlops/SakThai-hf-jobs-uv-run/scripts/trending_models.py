#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "huggingface-hub>=0.27",
# ]
# ///
"""List trending models on HF Hub — example for hf jobs uv run."""
from huggingface_hub import HfApi

api = HfApi()
models = api.list_models(sort="downloads", limit=5)

print("=== Top 5 Most Downloaded Models on HF Hub ===")
for model in models:
    print(f"  {model.modelId} — {model.downloads:,} downloads")
print("=== Done ===")
