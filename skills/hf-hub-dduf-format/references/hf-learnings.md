# DDUF (Diffusion Data Unified Format) — Complete Reference

## 2026-07-25: hf-hub-dduf-format

### Summary
Deep dive into the **DDUF (Diffusion Data Unified Format)** — a single-file archive format for diffusion models introduced by Hugging Face to unify model distribution. DDUF packages all components of a diffusion model (configs, weights, metadata) into a single `.dduf` file built on ZIP, with strict constraints, designed for remote parsing, lazy memory-mapping, and cross-language tooling. First-class Python support lives in `huggingface_hub v1.24.0+`.

### Motivation & Design Goals
Before DDUF, diffusion models were distributed as folders with dozens/hundreds of files (safetensors shards, JSON configs, tokenizer files). This made downloading, sharing, and versioning cumbersome. DDUF solves this by:

1. **Single-file distribution** — one file contains everything needed to load a pipeline
2. **Remote-parsable** — metadata and file structure can be fetched using HTTP Range requests without downloading the entire file
3. **Language-agnostic** — tooling can be implemented in Python, JavaScript, Rust, C++, etc.
4. **Lazy-loading** — weights can be memory-mapped directly from the archive without loading everything into RAM
5. **Follows Diffusers structure** — each model component is stored in its own directory, matching the Diffusers `from_pretrained` layout

### Format Specification

#### Container: ZIP (ZIP_STORED)
DDUF uses the ZIP format with **no compression** (`ZIP_STORED`). Rationale:
- Enables direct memory mapping of large files (compression breaks offsets)
- Ensures consistent and predictable remote file access via Range requests
- Prevents CPU overhead during file reading
- ZIP64 protocol is supported for files >4GB

#### Allowed File Types
| Extension | Purpose |
|-----------|---------|
| `.json` | Config files, model_index.json |
| `.safetensors` | Model weights (can be memory-mapped) |
| `.txt` | Textual metadata or descriptions |
| `.model` | Tokenizer model data (e.g., BPE merges) |

#### Directory Structure Rules
- **Max nesting**: 1 level of directories (e.g., `vae/config.json` but not `vae/subdir/file.json`)
- **Path separators**: UNIX-style (`/`) only; backslashes are rejected
- **Root requirement**: `model_index.json` must exist at root — a JSON dict mapping component names to their class/version info
- **Per-directory requirement**: Each directory must contain at least one config JSON: `config.json`, `tokenizer_config.json`, `preprocessor_config.json`, or `scheduler_config.json`
- **No duplicate entries**: Same filename cannot appear twice

#### Immutability
DDUF files are designed to be **immutable**. To update a model, create a new DDUF file.

### Python API (`huggingface_hub`)

#### `read_dduf_file(dduf_path) -> dict[str, DDUFEntry]`
Lightweight read — only parses metadata (ZIP central directory), does NOT load file contents into memory.

Returns a dictionary where:
- **Key**: filename in the archive (e.g., `"vae/diffusion_pytorch_model.safetensors"`)
- **Value**: `DDUFEntry(filename, length, offset, dduf_path)` dataclass

#### `DDUFEntry` Methods
| Method | Description |
|--------|-------------|
| `.as_mmap()` | Context manager yielding a `memoryview` slice — for safetensors loading |
| `.read_text()` | Read entry as UTF-8 string — for `.json` and `.txt` files |

#### `export_entries_as_dduf(dduf_path, entries)`
Lower-level export from an iterable of `(filename, content)` tuples. Content can be:
- `str`/`Path` — path to file on disk (copied into archive)
- `bytes` — raw bytes written directly

Entries are processed lazily (one at a time) — memory-efficient for large models.

#### `export_folder_as_dduf(dduf_path, folder_path)`
High-level export — scans a folder, adds allowed files, validates structure. Skips files with disallowed extensions or nested deeper than 1 directory.

#### Error Handling
| Exception | Cause |
|-----------|-------|
| `DDUFCorruptedFileError` | Corrupt ZIP, missing `model_index.json`, invalid structure |
| `DDUFExportError` | Invalid entry names, duplicate entries, export failures |
| `DDUFInvalidEntryNameError` | Disallowed file extension, backslash separators, >1 level nesting |

### Diffusers Integration
Diffusers has built-in DDUF support. Models stored in DDUF format on the Hub can be loaded directly:

```python
from diffusers import DiffusionPipeline
pipe = DiffusionPipeline.from_pretrained("DDUF/FLUX.1-dev")
```

The DDUF organization on the Hub (`https://huggingface.co/DDUF`) hosts popular diffusion models in DDUF format.

### Validation
A community Space provides validation: [DDUF/dduf-check](https://huggingface.co/spaces/DDUF/dduf-check)

### Comparison with Alternatives

| Aspect | DDUF | Raw folder | TAR |单个 safetensors |
|--------|------|------------|-----|-----------------|
| Single file | ✅ | ❌ | ✅ | ❌ (no configs) |
| Remote parsable | ✅ (ZIP central dir) | ❌ | ❌ (TOC at end) | ✅ |
| Memory-mappable | ✅ | ✅ | ❌ | ✅ |
| Cross-language | ✅ | ❌ (Depends on library) | ✅ | ✅ |
| Max file size | No limit (ZIP64) | No limit | No limit | No limit |
| Config bundling | ✅ | ✅ | ✅ | ❌ |

### Key Takeaways
1. DDUF is **not competing with safetensors** — it wraps safetensors files inside a ZIP container alongside configs
2. The `ZIP_STORED` (no compression) constraint is intentional — it enables memory-mapping and Range-request-based remote access
3. DDUF is designed for **diffusion models** first, but the format is generic enough for other ML model types
4. The `model_index.json` is the entry point — it tells loaders what components exist and their class names
5. Immutability means DDUF is best for **distribution/release** rather than development iteration

### References
- Source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/huggingface_hub/serialization/_dduf.py`
- HF Docs: https://huggingface.co/docs/hub/en/dduf
- HF Hub API: `huggingface_hub` v1.24.0+
- Validation Space: https://huggingface.co/spaces/DDUF/dduf-check
- DDUF Organization: https://huggingface.co/DDUF
