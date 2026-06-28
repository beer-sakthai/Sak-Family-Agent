---
name: hf-safetensors
description: "Hugging Face SafeTensors: secure, fast, framework-agnostic tensor serialization format — alternatives to pickle/PyTorch, with mmap, sharding, and audit-backed safety."
tags: [huggingface, safetensors, serialization, security, mlops]
---

# Hugging Face SafeTensors

**Secure, fast, and framework-agnostic tensor storage** for machine learning.

## What Problem Does It Solve?

PyTorch and other frameworks traditionally serialize models using Python’s `pickle` (or torch-specific pickle). Pickle can **execute arbitrary code** during deserialization — a critical vulnerability when loading models from untrusted sources. SafeTensors eliminates this by design.

## File Format

A `.safetensors` file is simply:

```
| 8-byte LE header size | JSON header | Raw tensor buffers |
```

- **JSON header** — UTF-8, describes every tensor: `names`, `shapes`, `dtypes`, and `data_offsets`.
- **Raw buffers** — flat binary, one after another; no framing or compression.
- **No code execution** — the file can never trigger deserialization logic because it stores only data.

### Header Parsing Benefits
- The header is tiny and can be fetched with a single HTTP **Range request**.
- Hugging Face Hub uses this to display model card metadata (names, shapes, param counts) without downloading the full file.
- In JavaScript: `huggingface.js` provides `parseSafetensorsMetadata`.

## Core APIs (Python)

```python
from safetensors.torch import save_file, load_file
from safetensors import safe_open

# Save a state dict
save_file({"weight": torch.randn(1000, 1000)}, "model.safetensors")

# Load everything back
tensors = load_file("model.safetensors")

# Selective / lazy loading (mmap + zero-copy)
with safe_open("model.safetensors", framework="pt") as f:
    weight = f.get_tensor("weight")   # only this tensor is read
```

| Function | Purpose |
|----------|---------|
| `save_file(tensors, path)` | Serialize a dict of tensors |
| `load_file(path)` | Load all tensors back |
| `safe_open(path, framework="pt")` | Lazy loading; inspect `keys()`, `metadata` before reading |
| `safe_open(..., device="cuda")` | Load directly to GPU (zero-copy where possible) |

## Security Model

1. **No arbitrary objects** — only numeric tensors and their metadata.
2. **No custom unpickler** — there is no execution hook in the format.
3. **Trail of Bits audit (2023)** — external security review confirmed the library is [really safe](https://huggingface.co/blog/safetensors-security-audit).
4. **Supply-chain resilience** — even a maliciously crafted file cannot run code on load; at worst it can cause a DoS via huge metadata, but parsers reject absurd sizes.

## Performance Characteristics

- **Memory mapping** — `mmap` lets the OS page in only what you read.
- **Partial loading** — load 1 of 100 shards without touching the rest.
- **Faster than pickle** — BERT base loads ~3× faster; medium models see 10×+ improvements.
- **Zero-copy reads** — when loading to CPU the buffer maps directly into memory.

## Sharded Checkpoints

Large models are split across many files:

```
model.safetensors.index.json  # maps tensor_name -> shard_filename + offset
model-00001-of-00005.safetensors
model-00002-of-00005.safetensors
...
model.safetensors.index.json format:
{
  "metadata": { ... },
  "weight_map": {
    "encoder.layers.0.attn.q.weight": "model-00001-of-00005.safetensors",
    ...
  }
}
```

`transformers` and `diffusers` handle sharded loading automatically when `safetensors` is installed.

## Framework Support

Official bindings:
- **Python** — `safetensors` (Rust core via PyO3)
- **JavaScript/Node** — `@huggingface/safetensors`
- **R** — `safetensors` on CRAN (pure R implementation)

Framework integrations:
- PyTorch, TensorFlow, JAX, PaddlePaddle, NumPy

## Converting Existing Models

```python
from transformers import AutoModel
from safetensors.torch import save_file

model = AutoModel.from_pretrained("bert-base-uncased")
save_file(model.state_dict(), "bert-base-uncased.safetensors")
```

## Ecosystem Adoption

SafeTensors is increasingly the default:
- `transformers` saves in safetensors when installed.
- Civitai, Stable Diffusion Web UI (AUTOMATIC1111), LLaMA.cpp (`convert.py`), dfdx, torch (R) all use it.
- Hugging Face Hub prefers safetensors over pickle for new uploads.

## Common Pitfalls

- **Metadata vs. tensors** — `metadata` is stored *inside* the JSON header; use `f.metadata()` to retrieve it.
- **Dtypes** — only `F16`, `F32`, `F64`, `I16`, `I32`, `I64`, `U8`, `BOOL` are standard; custom dtypes require extensions.
- **Partial files** — if a shard is corrupt, load the rest with `safe_open` (parser stops on first error unless you use low-level APIs).
- **Python version** — the Rust core requires Python ≥3.8; wheels are available for x86_64 Linux, macOS, and Windows.

## When to Use

- Distributing fine-tuned models to the community.
- Loading shared checkpoints from the Hub without trusting the uploader.
- Reducing load times for large models via mmap and sharding.
- Exchanging tensors across frameworks (Python ↔ R ↔ JS).

## References

- Docs: https://huggingface.co/docs/safetensors
- Repo: https://github.com/huggingface/safetensors
- Audit: https://huggingface.co/blog/safetensors-security-audit
- Metadata parsing: https://github.com/huggingface/safetensors/blob/main/docs/source/metadata_parsing.mdx
