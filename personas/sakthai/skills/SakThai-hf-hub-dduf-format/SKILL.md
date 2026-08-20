---
name: SakThai-hf-hub-dduf-format
description: "Comprehensive knowledge of the DDUF (Diffusion Data Unified Format) \u2014 a single-file\
  \ archive format for diffusion models that unifies model distribution by packaging\
  \ all components into a single .dduf file."
---

# hf-hub-dduf-format

**Author:** SakThai  
**License:** MIT

## Description

Comprehensive knowledge of the **DDUF (Diffusion Data Unified Format)** — a single-file archive format for diffusion models that unifies model distribution by packaging all components (configs, weights, metadata) into a single `.dduf` file. Built on ZIP with strict constraints, designed for remote parsing via HTTP Range requests, lazy memory-mapping via safetensors, and cross-language tooling. Implemented in `huggingface_hub` since v1.24.0 with `read_dduf_file`, `export_entries_as_dduf`, and `export_folder_as_dduf`.

## Key Commands

```python
# Read a DDUF file (lightweight — only metadata, no full load)
from huggingface_hub import read_dduf_file
entries = read_dduf_file("FLUX.1-dev.dduf")
# Returns dict[str, DDUFEntry] with filename, offset, length

# Read an entry as text (for .json, .txt entries)
import json
index = json.loads(entries["model_index.json"].read_text())

# Load safetensors via memory-mapping (zero-copy)
import safetensors.torch
with entries["vae/diffusion_pytorch_model.safetensors"].as_mmap() as mm:
    state_dict = safetensors.torch.load(mm)

# Export an entire folder as DDUF
from huggingface_hub import export_folder_as_dduf
export_folder_as_dduf(dduf_path="FLUX.1-dev.dduf", folder_path="path/to/FLUX.1-dev")

# Export selected entries lazily (memory-efficient)
from huggingface_hub import export_entries_as_dduf
def as_entries(pipe):
    yield "vae/config.json", pipe.vae.to_json_string().encode()
    yield "vae/diffusion_pytorch_model.safetensors", safetensors.torch.save(pipe.vae.state_dict())
    yield "model_index.json", json.dumps({...}).encode()
export_entries_as_dduf("model.dduf", as_entries(pipe))

# Load DDUF in Diffusers
from diffusers import DiffusionPipeline
pipe = DiffusionPipeline.from_pretrained("DDUF/FLUX.1-dev")
```

## Format Rules

| Rule | Detail |
|------|--------|
| **Container** | ZIP with `ZIP_STORED` (no compression) |
| **Max depth** | 1 level of directory nesting |
| **Allowed extensions** | `.json`, `.safetensors`, `.txt`, `.model` |
| **Required root entry** | `model_index.json` — key-value metadata mapping components |
| **Per-directory** | Must contain one config JSON (`config.json`, `tokenizer_config.json`, `preprocessor_config.json`, or `scheduler_config.json`) |
| **Path separator** | UNIX-style (`/`) only |
| **Large files** | ZIP64 protocol (supports >4GB files) |
| **Immutability** | DDUF files are immutable; create a new file to update |
| **Remote parsing** | Metadata fetchable via HTTP Range requests without full download |

## Related Skills
- `hf-diffusers-flux` — Flux pipeline (reference DDUF distribution)
- `hf-hub-storage-buckets-s3-compatibility` — alternative storage model
- `hf-safetensors-library-architecture` — safetensors lazy-loading underpins DDUF mmap
