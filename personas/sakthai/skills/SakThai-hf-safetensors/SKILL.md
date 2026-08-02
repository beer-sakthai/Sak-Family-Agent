---
name: SakThai-hf-safetensors
author: SakThai
license: MIT
description: "A skill for Hf Safetensors."
version: 0.1.0
---

# SakThai HF Safetensors Skill

author: SakThai
license: MIT

## Purpose
Expert knowledge of the safetensors library (v0.8.0) — the safe tensor serialization format powering Hugging Face model storage. Covers the Rust-backed core architecture, binary format specification, framework adapters (torch, numpy, flax, tensorflow, mlx, paddle), zero-copy mmap/pread loading, shared tensor deduplication, and integration with transformers/diffusers.

## When to activate
- User asks about `.safetensors` file format, structure, or internals
- Debugging model loading errors (`SafetensorError`, shared tensor issues, mmap failures)
- Optimizing model save/load performance (choosing mmap vs pread backend)
- Understanding how transformers loads model weights under the hood
- Building custom serialization pipelines for large models
- Investigating weight splitting (safetensors index files in sharded models)
- **Diagnosing mmap failures** in container/NFS/FUSE environments → recommend `backend="pread"`

## Quick Diagnostic: mmap vs pread

When loading safetensors fails with `SafetensorError` or segfault, try switching backends first:

```python
from safetensors import safe_open

# If this fails:
with safe_open("model.safetensors", framework="pt", device="cpu") as f:
    tensors = f.get_tensors()

# Try pread backend:
with safe_open("model.safetensors", framework="pt", device="cpu", backend="pread") as f:
    tensors = f.get_tensors()
```

The `pread` backend uses regular `read()` syscalls instead of `mmap()`, which avoids:
- NFS/FUSE filesystem mmap incompatibilities
- `vm.max_map_count` limits on container hosts
- Double page-cache consumption on low-RAM systems

## Sources
- Installed package at `/opt/data/.venv-sakthai/lib/python3.14/site-packages/safetensors/`
- GitHub: https://github.com/huggingface/safetensors
- HF docs: https://huggingface.co/docs/safetensors/index

## Key files in the skill
- `references/hf-learnings.md` — full deep-dive reference document
