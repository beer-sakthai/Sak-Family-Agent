# HF Learnings — Safetensors Library Architecture

## 2026-07-24: hf-safetensors-library-architecture — Safetensors v0.8.0 Internal Architecture Deep Dive (Topic #1 Deepened)

### Summary
Deep-dive into the `safetensors` Python library (v0.8.0) — the safe serialization format for tensors. Covers the Rust-backed core architecture, the safetensors binary format specification, the `safe_open` context manager with mmap/pread backends, the framework-specific Python adapter layers (torch, numpy, flax, tensorflow, mlx, paddle), zero-copy loading via `torch.frombuffer`/`np.frombuffer`, shared-tensor deduplication logic in `save_model`, and the `TensorSpec` descriptor that bridges Python memory to the Rust serializer.

### Source
- Installed safetensors v0.8.0 (`_safetensors_rust.abi3.so` Rust extension)
- `__init__.py` — re-exports `SafetensorError`, `TensorSpec`, `safe_open`, `deserialize`, `serialize`, `serialize_file`
- `torch.py` — PyTorch adapter (590 lines)
- `numpy.py` — NumPy adapter (198 lines)
- `flax.py` — JAX/Flax adapter (141 lines)
- `tensorflow.py` — TensorFlow adapter (142 lines)
- `mlx.py` — Apple MLX adapter (143 lines)
- `paddle.py` — PaddlePaddle adapter (308 lines)
- GitHub: https://github.com/huggingface/safetensors

### 1. Architecture Overview

safetensors uses a **Rust core** (`_safetensors_rust.abi3.so`) with thin Python adapter layers per framework. The Python side handles framework-specific conversions (dtype mapping, memory pointer extraction), while the Rust side handles binary format serialization, deserialization, mmap/pread I/O, and slice-based lazy loading.

```
Python ──safe_open──> Rust mmap/pread ──> Lazy pointer-based access
Python ──serialize──> Rust serialization ──> bytes
Python ──deserialize──> Rust deserialization ──> List[(name, {shape, dtype, data})]
```

Six framework adapters each expose the same four-function API:
- `save(tensors_dict) -> bytes` — serialize to bytes
- `save_file(tensors_dict, filename)` — serialize to file
- `load(bytes_data) -> tensors_dict` — deserialize from bytes
- `load_file(filename) -> tensors_dict` — load from file

Plus `save_model()` / `load_model()` for torch which handle shared-tensor deduplication.

### 2. Binary Format Specification

Every `.safetensors` file has exactly two parts:

**Header** (JSON, variable length, 8-byte aligned):
```
8 bytes: header_size as u64 (little-endian)
<header_size> bytes: UTF-8 JSON with structure:
{
  "__metadata__": {"key": "value", ...},  // optional
  "tensor_name": {
    "dtype": "F32",
    "shape": [1024, 768],
    "data_offsets": [0, 3145728]
  },
  ...
}
```
The header ends at offset `8 + header_size`. **Critical**: `header_size` must be a multiple of 8 (the align requirement).

**Tensor data** (raw binary, sequential):
```
<tensor_0 data: data_offsets[1] - data_offsets[0] bytes>
<tensor_1 data: data_offsets[1] - data_offsets[0] bytes>
...
```
Data offsets are absolute positions from the **start of the data segment** (immediately after the header), NOT from the file start.

### 3. Core Rust API (Exposed to Python)

`__init__.py` re-exports from the Rust extension (`_safetensors_rust`):

| Export | Purpose |
|---|---|
| `SafetensorError` | Custom exception for format/validation errors |
| `TensorSpec(dtype, shape, data_ptr, data_len)` | Descriptor for serialization — takes raw memory pointer |
| `safe_open(filename, framework, device, *, backend)` | Context manager for lazy/mmap loading |
| `deserialize(data) -> List[(name, dict)]` | Parse bytes into typed views (no framework conversion) |
| `serialize(tensor_dict, metadata) -> bytes` | Serialize TensorSpec dict to binary |
| `serialize_file(tensor_dict, filename, metadata) -> None` | Serialize directly to file |

The `TensorSpec` class validates dtypes at construction (not at serialize time). For packed dtypes like `float4_e2m1fn_x2`, it transparently doubles the last dimension of the shape so the spec always reflects logical element count.

### 4. safe_open — Lazy File Loading

`safe_open` is the primary loading interface, implemented in Rust with two backends:

```python
with safe_open("model.safetensors", framework="pt", device="cpu", backend="mmap") as f:
    tensor = f.get_tensor("embedding")       # one tensor
    tensors = f.get_tensors()                # all tensors (fast path for MPS+pread)
    keys = f.keys()                          # list of tensor names
    keys_by_offset = f.offset_keys()         # names ordered by file offset
    metadata = f.metadata()                  # header __metadata__
    sl = f.get_slice("embedding")            # slice view (lazy slicing before loading)
    part = sl[:, ::8]                        # actual load + slice
```

**Two backends controlled by `backend=`:**

| Backend | Mechanism | When to use |
|---|---|---|
| `"mmap"` (default) | Memory-map the file → OS page cache → tensors zero-copy from cached pages | General use, fast when data fits in page cache |
| `"pread"` | `pread(2)` syscall for each tensor's byte range into pre-allocated buffer | Apple MPS — reads into shared MTLBuffer without duplicating page cache |

On Apple Silicon MPS with `backend="pread"` + `get_tensors()`, there's a bulk-alloc fast path: allocates shared MTLBuffer, fills with parallel `pread(2)`, hands to torch via DLPack with zero extra copies.

API methods:
- `keys()` / `offset_keys()` — list tensor names (offset_keys is sorted by file offset for reproducibility)
- `get_tensor(name)` — read and convert one tensor
- `get_slice(name)` → returns `PySafeSlice` object for lazy sub-tensor reads (e.g., `sl[10:20, :]` materializes only the sliced bytes)
- `get_tensors()` — bulk read all, fast path on MPS+pread
- `metadata` property — returns `__metadata__` dict from header

### 5. Framework Adapter Architecture

Each adapter follows the same pattern: convert framework tensors to pointer-based `TensorSpec`, delegate to Rust core, then convert back.

#### 5a. numpy.py — Simplest, Foundation for Others

The numpy adapter is the thinnest wrapper and serves as the base for flax, tensorflow, and mlx adapters:

**Save path:**
```python
_flatten(tensor_dict, keep_alive) → Dict[str, TensorSpec]  # ptr + dtype + shape
    → serialize(flattened, metadata)                         # Rust: writes binary
```

**_flatten** creates `TensorSpec` from each ndarray using `tensor.ctypes.data` as `data_ptr` and `tensor.nbytes` as `data_len`. Handles big-endian byte swapping via `byteswap(inplace=False)` before serialization (keeps swapped copy alive via `keep_alive_buffer`).

**Load path:**
```python
deserialize(data) → List[(name, {dtype, shape, data: memoryview})]
    → _view2np(safeview) → Dict[str, ndarray]
```

**_view2np** uses `np.frombuffer(v["data"], dtype=dtype).reshape(v["shape"])` — zero-copy, numpy reads directly from the memoryview wrapper around the Rust buffer.

**Dtype mapping** (common six dtypes): `F64`, `F32`, `F16`, `I64`, `U64`, `I32`, `U32`, `I16`, `U16`, `I8`, `U8`, `BOOL`, `C64`.

#### 5b. torch.py — Most Complex (590 lines)

Extra complexity comes from **shared tensor detection** and **device handling**.

**Save path (`save_file`):**
1. `_evaluate_tensors_for_save(tensors)` — validates all are torch.Tensor, strided (not sparse), and **no tensors share memory** (calls `_find_shared_tensors`)
2. `_find_shared_tensors(state_dict)` — groups tensors by `(device, storage_ptr, storage_size)`. Then `_filter_shared_not_shared` resolves overlapping storage ranges to determine actual sharing.
3. `_to_ndarray(tensor)` — uses `ctypes.cast(tensor.data_ptr(), ...)` + `np.ctypeslib.as_array()` to create a **zero-copy numpy view** of the torch tensor's CPU memory. Handles big-endian byteswap, and float8/float4 types mapped to np.uint8 for storage.
4. `_flatten_as_ptr` builds `TensorSpec` from each ndarray view, keeping a reference alive to prevent GC during serialization.

**Load path (`load_file`):**
```python
safe_open(filename, framework="pt", device=device, backend=backend) as f
    → f.get_tensors()
```
_or via `load(data)`_:
```python
deserialize(data) → List[(name, {dtype, shape, data: memoryview})]
    → _view2torch(safeview) → Dict[str, torch.Tensor]
```

**_view2torch** uses `torch.frombuffer(v["data"], dtype=dtype).reshape(v["shape"])` — **zero-copy** from the deserialized Rust memoryview into a torch tensor. Empty tensors handled via `torch.empty()`.

**`save_model` — Shared Tensor Handling:**
`save_model()` handles the common PyTorch pattern where parameter views share the same underlying storage (e.g., tied weights, `weight` and `weight_orig` in weight-decoupled optimizers):
1. `_find_shared_tensors(state_dict)` discovers groups of names that share storage
2. `_filter_shared_not_shared` refines groups by checking actual memory overlap (not just same storage pointer but overlapping address ranges)
3. `_remove_duplicate_names` picks one `keep_name` per group (preferring `preferred_names` when given, avoiding `discard_names`)
4. Kept name gets saved; removed names are recorded in metadata for traceability
5. **Contiguous enforcement**: `force_contiguous=True` by default, calls `.contiguous()` on all tensors before save

**`load_model` — Reverse Dedup:**
On load, uses `preferred_names=state_dict.keys()` to keep the same names as the saved file, and filters out duplicates from the model's native state dict to get correct missing/unexpected lists.

#### 5c. Higher-Level Adapters (flax, tensorflow, mlx, paddle)

These all delegate to numpy.py:
- **flax.py**: `_jnp2np` converts JAX arrays to numpy → `numpy.save_file` → reverse on load
- **tensorflow.py**: `_tf2np` converts tf.Tensor to numpy → `numpy.save_file` → reverse on load
- **mlx.py**: `_mx2np` converts mx.array to numpy → `numpy.save_file` → reverse on load
- **paddle.py**: Two code paths — pre-3.2.0 uses numpy bridge; 3.2.0+ has direct Rust extension support with `frombuffer` and `safe_open(framework="paddle")`

### 6. Memory Management

**Zero-copy design**: safetensors never copies tensor data unnecessarily. The flow is:
- **Save**: Extract raw data pointer → Rust reads from that pointer → writes to file. No copy in Python.
- **Load (mmap)**: File → OS page cache → tensor reads from cached pages. No extra copy.
- **Load (bytes)**: deserialize → `torch.frombuffer` / `np.frombuffer` reads from the deserialized buffer in-place.

**Memory lifetime management**: The `keep_alive_buffer` / `keep_references_alive` lists in each adapter hold references to temporary numpy views and tensor objects. Without these, Python's GC could free the underlying memory while the Rust serializer is still reading from the pointer. The stub docs note a planned PyBuffer API (Python 3.11+) to handle this automatically via refcounts.

**Endianness**: Both `numpy._flatten` and `torch._to_ndarray` detect system byte order and byteswap big-endian tensors to little-endian before serialization. The `keep_alive_buffer` keeps the swapped copy alive during the Rust serialize call.

### 7. Shared Tensor Detection Algorithm (torch)

The function `_find_shared_tensors` is critical for safe PyTorch serialization:

```
For each (name, tensor) in state_dict:
    if tensor not on meta device and has non-zero storage:
        key = (device, storage_ptr(tensor), storage_size(tensor))
        group[key].add(name)

For each group with >1 name:
    compute (data_ptr, end_ptr) for each tensor in group
    sort by start address
    merge overlapping intervals → deduplicated groups
```

`_is_complete(tensor)` checks if the tensor's view covers the entire storage (start-to-end). Only complete tensors are eligible as `keep_name` candidates.

### 8. Supported Dtypes (Framework-Specific)

Common across all frameworks: F64, F32, F16, BF16, I64, I32, I16, I8, U8, BOOL, C64.

**Extra in torch.py**: U64/U32/U16 (torch 2.3.0+), F8_E4M3, F8_E4M3FNUZ, F8_E5M2, F8_E5M2FNUZ, F8_E8M0, F4_E2M1 (float4 packed).

**Extra in paddle.py**: F8_E4M3, F8_E5M2 (no uint64/uint32/uint16 yet).

Note that float8 and float4 dtypes are stored as raw bytes (mapped to `np.uint8` for numpy view) because numpy has no native float8 types.

### 9. Performance Considerations

- **MMAP is default** and best for CPU inference — tensors loaded on demand, cached by OS
- **PREAD for MPS** — avoids double memory consumption from page cache + MTLBuffer
- **PREAD for constrained environments** — `mmap` can fail on:
  - NFS/Samba/CIFS network filesystems
  - FUSE filesystems (common in containers, Docker, sandboxed environments)
  - Systems with low `vm.max_map_count` (e.g., default 65530 on Linux; large models with many shards can exceed this)
  - Very large models on low-RAM systems where mmap page cache competes with model memory
  - When you need deterministic file handle behavior (pread uses regular read syscalls)
  - **Recommendation**: If you see `SafetensorError` or segfaults loading safetensors from unusual paths, try `backend="pread"` first.
- **Zero-copy on both save and load** — no intermediate buffer copies in Python
- **`save_model(force_contiguous=True)`** ensures optimal memory layout but may trigger a memory copy for non-contiguous tensors
- **`get_slice()`** enables lazy loading of sub-tensors without reading the entire tensor from disk; **v0.8.0+** properly handles ellipsis `[...]` and strided slices `[:, ::8]` — before this fix, the step parameter was silently ignored in slicing
- **`get_tensors()` fast path** on MPS+pread bulk-allocates shared MTLBuffer and fills with parallel pread — dramatically faster than per-tensor reads
- **GIL-free serialization** (v0.8.0+): `serialize()` and `serialize_file()` release the GIL during writes, enabling true multithreaded saves from Python. Use `concurrent.futures.ThreadPoolExecutor` for parallel model saves.
- **macOS `F_NOCACHE`** (v0.8.0+): File writes use `F_NOCACHE` for direct I/O, yielding roughly 30% faster `save_file` on Apple Silicon.
- **`SafetensorError` is picklable** (v0.8.0+): Previously failed in multiprocessing contexts; now propagates correctly across process boundaries.

### 10. v0.8.0 Breaking Changes & Migration

| Change | Impact | Migration |
|--------|--------|-----------|
| `serialize`/`serialize_file` now take `TensorSpec` (not plain dicts) | Breaking for low-level API callers | High-level adapters (`safetensors.torch`, etc.) unchanged internally |
| Minimum Python 3.10 | Python 3.9 no longer supported | Upgrade to Python 3.10+ |
| `TensorIndexer::Narrow` now requires `step: NonZeroUsize` | Slices are now `start:stop:step` (was start:stop) | Check if using Rust API directly; Python API unaffected |
| `get_slice` handles ellipsis and strided slices | Fixes silent bug where `[:, ::8]` ignored step | No migration needed — just know it now works correctly |

### Key Takeaways
1. safetensors v0.8.0 is a Rust core (`_safetensors_rust.abi3.so`) with six framework adapters — torch is the most complex due to shared tensor detection
2. Binary format: 8-byte header length prefix → JSON header (8-byte aligned) → raw tensor data sequentially
3. `safe_open` supports two I/O backends: `mmap` (default, OS-managed page cache) and `pread` (explicit syscall, preferred for Apple MPS, and essential fallback when mmap fails on NFS/FUSE/container filesystems)
4. `TensorSpec(dtype, shape, data_ptr, data_len)` bridges Python memory to Rust serializer — caller must keep data alive during serialize
5. `save_model()` / `load_model()` handle shared storage deduplication via storage-pointer grouping and overlapping-address refinement
6. All framework adapters use zero-copy loading: `torch.frombuffer`, `np.frombuffer`, `paddle.base.core.frombuffer`
7. `get_slice()` enables lazy sub-tensor reads without loading the full tensor into memory; ellipsis/strided slices work correctly in v0.8.0+
8. **safetensors joined the PyTorch Foundation** (v0.8.0 announcement): strategic endorsement of the format, ensures long-term maintenance and ecosystem integration. Read more: https://huggingface.co/blog/safetensors-joins-pytorch-foundation
