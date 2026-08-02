# DDUF (Diffusion Data Unified Format) — Complete Reference + Source Architecture Deep-Dive

## 2026-07-25: hf-hub-dduf-format (v2 — source architecture deep-dive)

### Summary
Source-code deep-dive into DDUF's implementation in `huggingface_hub v1.24.0+` (386 lines in `serialization/_dduf.py`) plus exploration of the JS SDK, Hub organization catalog, Diffusers integration, and remote HTTP Range request patterns. The previous learning covered the public API; this v2 goes into internals, ZIP offset calculation, validation logic, the lazy generator export pattern, and the broader ecosystem.

### Source Architecture: `_dduf.py`

The entire DDUF implementation lives in a single file: `huggingface_hub/serialization/_dduf.py` (386 lines). It exports three public functions and one dataclass:

| Export | Type | Purpose |
|--------|------|---------|
| `read_dduf_file()` | Function | Parse DDUF metadata (lightweight) |
| `export_entries_as_dduf()` | Function | Write DDUF from iterable (lazy) |
| `export_folder_as_dduf()` | Function | Write DDUF from folder (convenience) |
| `DDUFEntry` | Dataclass | File entry metadata + mmap/read_text helpers |

### Data Offset Calculation: `_get_data_offset()`

The most technically interesting internal function. DDUF needs to know where each file's data starts within the ZIP archive so it can memory-map or Range-request individual entries without decompressing. This is NOT stored directly in the ZIP central directory — it must be calculated from the local file header:

```
Step 1: Read header_offset from ZipInfo (central directory entry)
Step 2: Seek to header_offset, read 30-byte local file header
Step 3: Parse 2-byte little-endian fields:
  - bytes[26:28] → filename length
  - bytes[28:30] → extra field length
Step 4: data_offset = header_offset + 30 + filename_len + extra_field_len
```

The 30-byte fixed-size local file header structure:
| Offset | Size | Field |
|--------|------|-------|
| 0 | 4 | Local file header signature (0x04034b50) |
| 4 | 2 | Version needed |
| 6 | 2 | General purpose bit flag |
| 8 | 2 | Compression method |
| 10 | 2 | Last mod file time |
| 12 | 2 | Last mod file date |
| 14 | 4 | CRC-32 |
| 18 | 4 | Compressed size |
| 22 | 4 | Uncompressed size |
| 26 | 2 | Filename length |
| 28 | 2 | Extra field length |

This is why DDUF requires `ZIP_STORED` (no compression) — compressed entries would need full decompression to read, defeating memory-mapping and Range-based access.

### Validation Internals

#### Entry Name Validation: `_validate_dduf_entry_name()`

Three sequential checks:
1. **Extension whitelist** — splits on `.`, takes last element, checks against `DDUF_ALLOWED_ENTRIES` (`{".json", ".model", ".safetensors", ".txt"}`)
2. **No backslashes** — rejects Windows-style separators with `"\\\\" in entry_name`
3. **Max 1-level nesting** — strips leading/trailing `/`, checks `entry_name.count("/") > 1`

#### Structure Validation: `_validate_dduf_structure()`

Called after reading `model_index.json`:
1. Checks `model_index.json` is a `dict`
2. Extracts folder names: `{entry.split("/")[0] for entry in entry_names if "/" in entry}`
3. Each folder must be present as a key in `model_index.json`
4. Each folder must contain at least one of: `config.json`, `tokenizer_config.json`, `preprocessor_config.json`, `scheduler_config.json`

This cross-references the file structure against the index — ensuring no orphaned component directories.

### ZIP64 Support

DDUF uses `force_zip64=True` in `ZipFile.open()` for writing (`_dump_content_in_archive`). This enables:
- Single entries > 4GB (essential for large safetensors shards)
- Total archive > 4GB
- ZIP64 extra fields in local and central directory headers

The ZIP64 format is backward-compatible — readers without ZIP64 support see the ZIP64 "magic" values (0xFFFFFFFF for sizes) and can fall back.

### Lazy Generator Export Pattern

`export_entries_as_dduf()` accepts an `Iterable[tuple[str, str | Path | bytes]]` — this is the key design for memory efficiency:

```python
def as_entries(pipe):
    # Each yield is one entry; entries are serialized one at a time
    yield "vae/config.json", pipe.vae.to_json_string().encode()  # bytes
    yield "vae/diffusion_pytorch_model.safetensors", safetensors.torch.save(pipe.vae.state_dict())  # bytes
    yield "text_encoder/config.json", pipe.text_encoder.config.to_json_string().encode()
    yield "text_encoder/model.safetensors", safetensors.torch.save(pipe.text_encoder.state_dict())
```

**Internal write path** (`_dump_content_in_archive`):
- `bytes` → `archive_fh.write(content)` — direct write
- `str`/`Path` → `shutil.copyfileobj(content_fh, archive_fh, 8*1024*1024)` — 8MB chunked copy (avoids loading entire file into RAM)

The `8 * 1024 * 1024` (8MB) buffer size is a hardcoded sweet spot — large enough to utilize I/O bandwidth, small enough to fit in L3 cache and not waste memory.

### DDUF Hub Organization Catalog

The `DDUF` organization on Hugging Face hosts **11 models** as of July 2026:

| Model | Type | Variant |
|-------|------|---------|
| `DDUF/FLUX.1-dev-DDUF` | Text-to-Image | 12B, Flux pipeline |
| `DDUF/FLUX.1-schnell-DDUF` | Text-to-Image | 12B, Flux schnell |
| `DDUF/stable-diffusion-v1-4-DDUF` | Text-to-Image | SD 1.4 |
| `DDUF/stable-diffusion-xl-base-1.0-DDUF` | Text-to-Image | SDXL 1.0 |
| `DDUF/sdxl-turbo-DDUF` | Text-to-Image | SDXL Turbo |
| `DDUF/stable-diffusion-3.5-medium-DDUF` | Text-to-Image | SD 3.5 Medium |
| `DDUF/stable-diffusion-3.5-large-DDUF` | Text-to-Image | SD 3.5 Large |
| `DDUF/stable-diffusion-3.5-large-turbo-DDUF` | Text-to-Image | SD 3.5 Large Turbo |
| `DDUF/tiny-flux-dev-pipe-dduf` | Text-to-Image | Tiny test/dev variant |
| `DDUF/CogVideoX1.5-5B-DDUF` | Text-to-Video | CogVideoX 5B |
| `DDUF/CogVideoX1.5-5B-I2V-DDUF` | Image-to-Video | CogVideoX 5B I2V |

All were published Dec 13, 2024. The model IDs use the `-DDUF` suffix convention.

### JS SDK: `@huggingface/dduf` v0.0.2

A minimal TypeScript parser published as part of the `@huggingface/huggingface.js` monorepo:

```ts
import { checkDDUF } from "@huggingface/dduf";

// Async generator — yields entries one by one
for await (const entry of checkDDUF(url | blob, { log: console.log })) {
  console.log("file", entry);
}
```

**Install options:**
- npm/pnpm/yarn: `@huggingface/dduf`
- Deno via esm.sh: `import { checkDDUF } from "https://esm.sh/@huggingface/dduf"`
- Deno via npm: `import { checkDDUF } from "npm:@huggingface/dduf"`

**Input types:** `URL | Blob` — the SDK accepts either a remote URL (uses HTTP Range requests internally) or an in-memory Blob. This makes it suitable for both browser and Node.js environments.

The package is marked as "very alpha" — it currently only provides validation/parsing, not full export capabilities like the Python version.

### Remote Parsing with HTTP Range Requests

DDUF's ZIP-based structure enables remote parsing without full download:

1. **HTTP HEAD request** — determine file size (for non-seekable streams)
2. **HTTP Range request** — fetch the ZIP end-of-central-directory record (EOCD) at the end of the file: `Range: bytes=-22` for minimum, or scan backwards for EOCD signature (0x06054b50)
3. **Parse EOCD** — get central directory offset and size
4. **Range request central directory** — fetch the directory listing (all filenames, offsets, sizes)
5. **Selective entry Range requests** — fetch only the data for entries you need using their `offset` and `length`

This pattern means:
- Listing contents: ~1-2 HTTP requests (small payload)
- Loading specific weights: 1 HTTP request per safetensors file
- Total data transfer: exactly the weights you need, nothing more

The `DDUFEntry.offset` and `DDUFEntry.length` fields expose exactly the byte range needed for a Range request.

### Diffusers Integration Deep-Dive

Diffusers loads DDUF repos transparently via the standard `from_pretrained()` API:

```python
# Automatically detects DDUF format (checks org name or file extension)
pipe = DiffusionPipeline.from_pretrained("DDUF/FLUX.1-dev")
# OR load from local .dduf file
pipe = DiffusionPipeline.from_pretrained("./FLUX.1-dev.dduf")
```

The detection heuristic:
1. If the repo is under the `DDUF` organization → treat as DDUF
2. If the local path ends in `.dduf` → treat as DDUF
3. Otherwise → standard folder-based loading

When loading a DDUF model:
1. Download the single `.dduf` file (or use cached copy)
2. Call `read_dduf_file()` to parse the manifest
3. Read `model_index.json` from the entries to determine pipeline class
4. For each component, memory-map the safetensors file via `entry.as_mmap()`
5. Load configs via `entry.read_text()`

This means loading a DDUF model requires **no decompression step** — safetensors are memory-mapped directly from the `.dduf` file.

### Best Practices from Source Analysis

1. **Always use a generator for export** — `export_entries_as_dduf()` with a generator yields one entry at a time; avoid materializing all entries in memory as a list
2. **Keep `model_index.json` first** — validation checks it immediately; more importantly, it should precede component directory entries for clean streaming
3. **Name directories to match component names** — each directory name must appear as a key in `model_index.json`; mismatches cause `DDUFExportError`
4. **Include at least one config JSON per directory** — the four recognized config filenames are hardcoded: `config.json`, `tokenizer_config.json`, `preprocessor_config.json`, `scheduler_config.json`
5. **Use POSIX paths** — backslashes are explicitly rejected at the validation layer
6. **Avoid nested subdirectories** — any path with two or more `/` separators (after stripping root) is rejected
7. **Extensions are case-sensitive** — only `.json`, `.safetensors`, `.txt`, `.model` (lowercase)

### Error Handling Reference (from source)

| Exception | Raised By | Trigger |
|-----------|-----------|---------|
| `DDUFCorruptedFileError` | `read_dduf_file` | Missing `model_index.json`, invalid `model_index.json` content, non-ZIP_STORED entries, invalid entry names, corrupted ZIP structure |
| `DDUFExportError` | `export_entries_as_dduf` | Duplicate entries, invalid entry names, missing `model_index.json`, invalid content types, failed JSON parsing |
| `DDUFInvalidEntryNameError` | `_validate_dduf_entry_name` | Disallowed file extension, backslash separator, >1 level nesting |

### Comparison with Other Single-File Formats

| Aspect | DDUF | GGUF | single safetensors |
|--------|------|------|--------------------|
| Purpose | Full model pipeline (configs + weights) | Single quantized LLM format | Only weights (no configs) |
| Container | ZIP (STORE) | Custom binary header | Custom binary header |
| Remote parsable | ✅ (ZIP central dir) | ✅ (header-first) | ✅ (header-first) |
| Memory-mappable | ✅ | ✅ | ✅ |
| Config bundling | ✅ (JSON in ZIP) | ❌ (header only, limited) | ❌ |
| Max file size | ZIP64 unlimited | 64-bit unlimited | 64-bit unlimited |
| Pipeline components | ✅ (all in one file) | ❌ (single model only) | ❌ (single weight file) |

### References
- Source: `huggingface_hub/serialization/_dduf.py` (386 lines, v1.24.0)
- HF Hub Docs: https://huggingface.co/docs/hub/en/dduf
- HF Hub API: `huggingface_hub` v1.24.0+
- JS SDK: `@huggingface/dduf` v0.0.2 (npm/pnpm/yarn/deno)
- Validation Space: https://huggingface.co/spaces/DDUF/dduf-check
- DDUF Organization: https://huggingface.co/DDUF (11 models)
- ZIP format spec: https://en.wikipedia.org/wiki/ZIP_(file_format)#File_headers
