# HF Learnings — Datasets Library v5

## 2026-07-24: hf-datasets-library-v5 — Deep Dive v2 (Topic #19, Datasets v5.0.0)

### Summary
Deep-dive into Hugging Face `datasets` v5.0.0 (major version jump) — covering the Polars integration (`from_polars`/`to_polars`), SQL/Spark connectors, interleave/concatenate with axis support, IterableDataset enhancements, native Image/Audio features, and the internal Arrow table architecture.

### Key New Features in v5.0.0

| Feature | Description |
|---------|-------------|
| **Polars integration** | `from_polars()` / `to_polars()` — direct zero-copy Arrow interop |
| **SQL round-trip** | `from_sql()` / `to_sql()` — SQLAlchemy/SQLite3 support |
| **Spark support** | `from_spark()` — PySpark DataFrame conversion |
| **Interleave datasets** | Probabilistic mixing with 3 stopping strategies |
| **Concatenate axis** | `axis=1` for horizontal merge |
| **IterableDataset parity** | Full API parity with Dataset (batch, skip, take, repeat, reshard) |
| **Image/Audio** | Mature multimodal feature types |
| **push_to_hub** | Now works with IterableDataset |

### Source
Datasets v5.0.0 installed at `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/`

### Resources
- Docs: https://huggingface.co/docs/datasets/en/index
- Changelog: https://github.com/huggingface/datasets/releases
- Audio dataset guide: https://huggingface.co/docs/datasets/en/audio_dataset
- Process audio guide: https://huggingface.co/docs/datasets/en/audio_process
- Audio feature API ref: https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.Audio

---

## 2026-07-24: hf-datasets-audio-processing-deep-dive — Complete Audio Pipeline (Topic #113)

### Summary
Deep-dive into audio processing with Hugging Face `datasets` — covering the `Audio` feature type, loading strategies, resampling, map-based preprocessing, streaming, filtering, augmentation, WebDataset support, and Transformer model integration. Everything is CPU-friendly and zero-GPU.

### 1. The `Audio` Feature Type

Every audio column in a `datasets` Dataset uses the `datasets.Audio` feature. When you access an example, the audio file is **decoded on-the-fly** into a NumPy array (or torch Tensor with the torchcodec backend) with its sampling rate.

```python
from datasets import Audio, load_dataset

ds = load_dataset("PolyAI/minds14", "en-US", split="train")
example = ds[0]["audio"]
# Returns: {'path': '/.../0000.wav', 'array': np.array([...]), 'sampling_rate': 8000}
```

**The decoded dict contains:**
- `path` (`str`): Original file path
- `array` (`np.ndarray`): Audio waveform with shape `(channels,)` or `(channels, samples)`
- `sampling_rate` (`int`): Sample rate in Hz

### 2. Loading and Decoding Audio

**Streaming audio from Hub (zero local download):**
```python
ds_stream = load_dataset("PolyAI/minds14", "en-US", split="train", streaming=True)
for i, example in enumerate(ds_stream):
    audio = example["audio"]  # decoded on-demand
    if i > 2:
        break
```

**Local files:**
```python
from datasets import Dataset, Audio

ds = Dataset.from_dict({"audio": ["/path/to/file1.wav", "/path/to/file2.wav"]})
ds = ds.cast_column("audio", Audio())
```

**Audio sampling:** Audio files are decoded at their native sampling rate by default. You can resample by specifying `sampling_rate`:
```python
from datasets import Audio

# Force all audio to 16kHz
ds = ds.cast_column("audio", Audio(sampling_rate=16000))
```

### 3. Advanced Audio Processing

**Batch decode and resample via `.map()`:**
```python
def process_audio(batch):
    audios = batch["audio"]
    # audios are already decoded dicts with 'array' and 'sampling_rate'
    batch["processed"] = [{"array": a["array"] * 0.5, "sampling_rate": a["sampling_rate"]} for a in audios]
    return batch

ds = ds.map(process_audio, batched=True, batch_size=100)
```

**Memory-efficient decoding:** Audio features are decoded lazily only when accessed. Use `Audio(decode=False)` to store raw bytes without decoding:
```python
ds = ds.cast_column("audio", Audio(decode=False))
# {'path': '/path/to/file.wav', 'bytes': None}  # no array decoded
```

### 4. Resources
- https://huggingface.co/docs/datasets/en/audio_dataset
- https://huggingface.co/docs/datasets/en/audio_process
- https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.Audio

---

## 2026-07-24: hf-datasets-image-processing-deep-dive — Complete Image Pipeline (Topic #114)

### Summary
Deep-dive into image processing with Hugging Face `datasets` — covering the `Image` feature type, loading strategies (paths, PIL, bytes), resizing, map-based preprocessing, streaming, WebDataset, Lance, and integration with Transformers image processors.

### 1. The `Image` Feature Type

```python
from datasets import Image, load_dataset

ds = load_dataset("nateraw/food", split="train")
example = ds[0]["image"]
# Returns: PIL.Image.Image (decoded on-demand)
```

**Input types for encoding:**
| Input | Behaviour |
|-------|-----------|
| `str` | Loaded as file path |
| `pathlib.Path` | Absolute path |
| `bytes` / `bytearray` | In-memory image bytes |
| `PIL.Image.Image` | Encoded to bytes (JPEG default) |
| `dict` with `{"path": ..., "bytes": ...}` | Pass-through |

**Decode options:**
```python
Image(decode=True)    # Default: decode to PIL Image
Image(decode=False)   # Store as {path, bytes} dict, no decode
```

### 2. Storage Layer

Arrow storage uses `struct<bytes: binary, path: string>` — identical pattern to Audio and Video features.

**Cast from string (path):** `cast_storage()` converts `pa.string()` → struct by treating the string as a path.

**PIL auto-detection:** When creating a TypedSequence with PIL images, the writer auto-detects `PIL.Image.Image` objects and encodes them:
```python
# Auto-encoded when building:
ds = Dataset.from_dict({"image": [pil_img1, pil_img2]})
# Features are inferred as Image()
```

### 3. Preprocessing

**Via `.map()` with batched decode:**
```python
from datasets import Features, Image

def transform(batch):
    batch["image"] = [img.resize((224, 224)) for img in batch["image"]]
    return batch

ds = ds.map(transform, batched=True, batch_size=100)
```

### 4. Resources
- https://huggingface.co/docs/datasets/en/image_dataset
- https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.Image

---

## 2026-07-24: hf-datasets-arrow-parquet-writer-internals (Topic #126) — Datasets v5 Serialization Deep Dive

### Summary
Complete architecture deep-dive into how Hugging Face `datasets` v5.0.0 serializes data — the Arrow IPC and Parquet writer pipelines, type inference via `TypedSequence`/`OptimizedTypedSequence`, batch sizing across Arrow record batches and Parquet row groups, schema building with embedded metadata, content-defined chunking (CDC), fingerprint-based caching, and sharding for parallel generation. Source-verified against the installed v5.0.0 codebase.

### 1. Writer Architecture Overview

Datasets v5 has two writer classes in `arrow_writer.py`:

```
ArrowWriter (base)          → writes Arrow IPC format (.arrow files)
  └── ParquetWriter (subclass) → writes Apache Parquet format (.parquet files)
```

Both are used through `DatasetBuilder` in `builder.py`, which orchestrates the full generate → write → finalize pipeline.

**Write flow:**
```
Generator → examples dicts → ArrowWriter.write() → buffered in current_examples
    → write_examples_on_file() → _write_batch() → pa.Table.from_arrays()
    → _write_table() → pa.RecordBatchStreamWriter.write_table() (Arrow) / pq.ParquetWriter.write_table() (Parquet)
    → finalize() → close stream → return (num_examples, num_bytes)
```

### 2. ArrowWriter — Full API

```python
class ArrowWriter:
    def __init__(
        self,
        schema: Optional[pa.Schema] = None,
        features: Optional[Features] = None,
        path: Optional[str] = None,
        stream: Optional[pa.NativeFile] = None,
        fingerprint: Optional[str] = None,
        writer_batch_size: Optional[int] = None,    # Max records per Arrow batch
        disable_nullable: bool = False,
        update_features: bool = False,
        on_mixed_types: Optional[Literal["use_json"]] = "use_json",
        with_metadata: bool = True,
        unit: str = "examples",
        embed_local_files: bool = False,
        storage_options: Optional[dict] = None,
    )
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `schema` | `pa.Schema` | None | Pre-defined Arrow schema (alternative to `features`) |
| `features` | `Features` | None | `datasets.Features` dict — used to build schema |
| `path` | `str` | None | Local/remote filesystem path for output file |
| `stream` | `pa.NativeFile` | None | Open arrow write stream (mutually exclusive with path) |
| `fingerprint` | `str` | None | Dataset state fingerprint — embedded in metadata |
| `writer_batch_size` | `int` | dynamic | Arrow record batch size (in rows) |
| `disable_nullable` | `bool` | False | Set all fields non-nullable in schema |
| `update_features` | `bool` | False | Allow schema evolution (extend features from incoming data) |
| `on_mixed_types` | `str` | "use_json" | Strategy for mixed-type columns: encode to JSON |
| `with_metadata` | `bool` | True | Embed DatasetInfo + fingerprint in schema metadata |
| `unit` | `str` | "examples" | Unit label for logging |
| `embed_local_files` | `bool` | False | Embed local file bytes into the table |
| `storage_options` | `dict` | None | Filesystem options (passed to fsspec) |

#### Core Methods

| Method | Purpose |
|--------|---------|
| `write(example)` | Buffer a single dict example; flush when batch size reached |
| `write_row(row)` | Buffer a single-row `pa.Table`; flush when batch size reached |
| `write_batch(batch_examples)` | Write a full batch dict`<str, list>` immediately (flushes buffered examples first) |
| `write_table(pa_table)` | Write a `pa.Table` immediately (flushes buffered rows first) |
| `finalize(close_stream=True)` | Flush buffers, close writer and stream, return (num_examples, num_bytes) |

**Important detail about `write()`:** Uses the `writer_batch_size` to control memory. For image/audio/video datasets, the batch size auto-tunes down via `get_arrow_writer_batch_size_from_features()`:
- Image datasets: `config.ARROW_RECORD_BATCH_SIZE_FOR_IMAGE_DATASETS` (default: 100)
- Audio datasets: `config.ARROW_RECORD_BATCH_SIZE_FOR_AUDIO_DATASETS` (default: 100)
- Video datasets: `config.ARROW_RECORD_BATCH_SIZE_FOR_VIDEO_DATASETS` (default: 10)
- Binary datasets: `config.ARROW_RECORD_BATCH_SIZE_FOR_BINARY_DATASETS` (default: 100)

This prevents Arrow buffer overflows (each record batch must be < 2GB uncompressed). The SDK scans features recursively via `_visit()` to determine the strictest limit.

#### Internal Buffering

`ArrowWriter` maintains **two** separate write-pools:
1. `current_examples`: list of `(example_dict, key)` tuples — flushed via `write_examples_on_file()`
2. `current_rows`: list of single-row `pa.Table` objects — flushed via `write_rows_on_file()`

When a new `write_batch()` or `write_table()` comes in, the corresponding pool is flushed first (FIFO ordering preserved).

### 3. ParquetWriter — Parquet-Specific Configuration

```python
class ParquetWriter(ArrowWriter):
    def __init__(self, *args, use_content_defined_chunking=True, write_page_index=True, **kwargs):
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `use_content_defined_chunking` | `True` | Enable CDC (content-defined chunking) — sets metadata flag + `DEFAULT_CDC_OPTIONS` dict |
| `write_page_index` | `True` | Write page index for fast row-group-level skipping |

#### Compression Strategy (auto-configured)

ParquetWriter auto-configures compression per-column based on feature type:

```python
compression={
    col: "none" if require_storage_embed(feature) else "snappy"
    for col, feature in self._features.items()
}
use_dictionary=[col for col, feature in self._features.items() if not require_storage_embed(feature)]
column_encoding={
    col: "PLAIN" for col, feature in self._features.items() if require_storage_embed(feature)
}
```

**Rule:** Columns that embed external files (Image, Audio, Video — binary bytes) use:
- `compression="none"` — binary data is already compressed
- `use_dictionary=False` — high cardinality makes dict encoding wasteful
- `encoding="PLAIN"` — no further encoding

Other columns get:
- `compression="snappy"` — fast, good compression ratio
- `use_dictionary=True` — dictionary encoding for low-cardinality string columns

#### Writer Batch Size for Parquet Row Groups

The `writer_batch_size` parameter in ParquetWriter controls **Parquet row group size**, NOT Arrow record batch size (which is a separate concept). Two heuristics determine the optimal size:

**A) Feature-based (`get_writer_batch_size_from_features()`):**
Uses `PARQUET_ROW_GROUP_SIZE_FOR_*` config constants for Image/Audio/Video/Binary — similar to Arrow batch sizing but tuned for Parquet columnar storage.

**B) Data-size-based (`get_writer_batch_size_from_data_size()`):**
```python
def get_writer_batch_size_from_data_size(num_rows: int, num_bytes: int) -> int:
    return max(1, num_rows * MAX_ROW_GROUP_SIZE // num_bytes) if num_bytes > 0 else 1
```
Aims for row groups of **100MB uncompressed** maximum — matching HF Dataset Viewer expectations for fast random access.

#### Content-Defined Chunking (CDC)

When `use_content_defined_chunking=True` (default), the writer sets Parquet key-value metadata:
```python
{"content_defined_chunking": json.dumps(DEFAULT_CDC_OPTIONS)}
```

Default CDC options from `config.py`:
- `config.DEFAULT_CDC_OPTIONS` — controls how Parquet splits data into chunks at natural boundaries
- CDC splits on content boundaries rather than fixed row counts, enabling more efficient deduplication and compression
- Supported by modern Parquet readers for predicate pushdown at chunk granularity

To disable: `ParquetWriter(..., use_content_defined_chunking=False)`

### 4. TypedSequence — Type Inference & Encoding

`TypedSequence` is the core data-normalization layer. It wraps a list/iterable of raw Python data and converts it to a `pa.Array` with proper type handling.

```python
class TypedSequence:
    def __init__(
        self,
        data: Iterable,
        type: Optional[FeatureType] = None,
        try_type: Optional[FeatureType] = None,
        optimized_int_type: Optional[FeatureType] = None,
        on_mixed_types: Optional[Literal["use_json"]] = None,
    )
```

**Three type modes:**

| Mode | Parameter | Behaviour |
|------|-----------|-----------|
| **Strict** | `type` | Enforces exact feature type; raises on mismatch |
| **Trial** | `try_type` | Attempts the type; falls back to inferred type on failure |
| **Inferred** | both None | Auto-detect from data content |

**Auto-detection pipeline (when both type and try_type are None):**

1. **Custom object check** — `_infer_custom_type_and_encode()`:
   - PIL images → `Image()` feature + encode to bytes
   - pdfplumber PDFs → `Pdf()` feature + encode
   - Returns `(encoded_data, feature_type)` — data is immediately encoded

2. **Arrow array construction** — `pa.array()`:
   - `_ArrayXDExtensionType` → uses `to_pyarrow_listarray()`
   - `np.ndarray` → `numpy_to_pyarrow_listarray()`
   - Lists → `cast_to_python_objects()` then `pa.array()`

3. **Mixed-type handling** — when `on_mixed_types="use_json"`:
   - Scans for struct columns that intermix different types
   - Encodes them as JSON strings using `ujson_dumps()`
   - Uses `pyarrow.json.read_json()` for parsing
   - Iteratively discovers fields that change types between rows

**Overflow protection:** On overflow errors, raises `OverflowError` with suggestion to reduce `writer_batch_size`.

#### OptimizedTypedSequence — Column-Aware Int Optimization

```python
class OptimizedTypedSequence(TypedSequence):
    def __init__(self, data, type=None, try_type=None, col=None, ...):
```

Auto-reduces integer precision for known ML columns when no explicit type is given:

| Column | Optimized Type | Rationale |
|--------|---------------|-----------|
| `attention_mask` | `int8` | Binary tensor (0/1); never needs >1 byte |
| `special_tokens_mask` | `int8` | Binary mask |
| `input_ids` | `int32` | Typical vocab 0-50k, max ~500k; int64 wastes 4 bytes/token |
| `token_type_ids` | `int8` | Binary mask (values 0,1,2 in XLNet) |

This saves significant storage for tokenized datasets: if `input_ids` is stored as `int64` by default, switching to `int32` halves storage.

**Important:** Optimization only applies when the type would otherwise be fully inferred (no explicit `type` or `try_type`). The actual optimal type is verified — if data doesn't fit (`"not in range"` error), it falls back gracefully to `int64`.

### 5. Schema Building & Metadata

Schema is constructed in `_build_schema()`:

```python
def _build_schema(self, inferred_schema: pa.Schema):
    # Case 1: features provided, update_features=False (default)
    #   → Use original features/schema, ignore inferred
    # Case 2: features provided, update_features=True
    #   → Keep existing features for matching fields, use inferred for new fields
    # Case 3: no features provided
    #   → Use fully inferred features from data
```

**Metadata embedding** (`_build_metadata()`):
```python
{"huggingface": json.dumps({
    "info": {"features": asdict(features)},
    "fingerprint": fingerprint,
})}
```

This metadata is stored in the Arrow schema (key `"huggingface"`) and survives Parquet conversion. It's how `Dataset.from_parquet()` can reconstruct the original `Features` without a separate config file.

### 6. Fingerprinting & Caching (fingerprint.py)

**Purpose:** Provide one deterministic fingerprint per dataset state. After every transform (`.map()`, `.select()`, `.filter()`, etc.), the fingerprint updates. Re-running the same transforms in a different session yields the same fingerprint, enabling cache reuse.

**Core mechanism:**

```python
class Hasher:
    # Uses xxhash for deterministic hashing of Python objects
    # Supports: scalars, bytes, str, list, tuple, dict, set, bool, None, slice,
    #   datetime, np.ndarray, torch.Tensor, tf.Tensor, jax.Array, pa.Table,
    #   pa.ChunkedArray, pa.Array, functions, callables, partial, code objects
```

**Cache flow:**
1. `Dataset.map(fn)` → compute fingerprint of fn + input fingerprint
2. Check cache path `~/.cache/huggingface/datasets/<fingerprint>/`
3. If cache exists → memory-map and return
4. If not → apply transform, write to cache, update fingerprint

**Caching can be disabled:**
```python
dataset.map(fn, disable_nullable=True)  # no caching
# Or globally:
from datasets import disable_caching
disable_caching()
```

**Temporary cache:** `_TempCacheDir` manages temp Arrow files with cleanup that properly releases Arrow references before deleting to avoid Windows permission errors.

### 7. Sharding for Parallel Generation (utils/sharding.py)

**`_number_of_shards_in_gen_kwargs(gen_kwargs)`** — Counts parallel shards from generator kwargs. When `gen_kwargs` contains lists, each list entry represents a data source shard. Constraint: all lists must have the same length (or only one list exists) — otherwise sharding is "ambiguous" and raises `RuntimeError`.

**`_split_gen_kwargs(gen_kwargs, max_num_jobs)`** — Distributes shard indices across worker processes:
```python
# gen_kwargs = {"data_dir": ["shard0", "shard1", ..., "shard9"]}
# max_num_jobs = 3
# Returns: [
#   {"data_dir": ["shard0", "shard1", "shard2", "shard3"]},
#   {"data_dir": ["shard4", "shard5", "shard6"]},
#   {"data_dir": ["shard7", "shard8", "shard9"]},
# ]
```

**`_distribute_shards(num_shards, max_num_jobs)`** — Divides N shards into M jobs as evenly as possible, preserving order. Uses:
```python
num_shards_per_job = num_shards // max_num_jobs
remainder = num_shards % max_num_jobs
# First `remainder` jobs get one extra shard each
```

**Shuffling:** `_shuffle_gen_kwargs()` shuffles all same-length lists identically to keep entangled data (e.g., shard + shard_metadata) in sync.

### 8. Complete Write Pipeline Flow

```
DatasetBuilder._prepare_split()
  ↓
for gen_kwargs in _split_gen_kwargs(gen_kwargs, num_proc):
  ↓ worker process
  DatasetBuilder._run_split_generators()
    ↓
  for generator in split_generators:
    ↓
    for example in generator():
    ↓
    ArrowWriter.write(example)     # buffer in-memory
      ↓ when batch_size reached
    write_examples_on_file()
      ↓
    _write_batch()
      ↓ TypedSequence → pa.array() for each column
      ↓ pa.Table.from_arrays()
      ↓
    _write_table()
      ↓ table_cast() to match schema
      ↓ embed_local_files() if enabled
      ↓
    pa_writer.write_table()        # Arrow IPC stream
    # OR pq_writer.write_table()   # Parquet columnar + row groups
      ↓
  finalize()
    ↓ flush remaining buffers, close writer, close stream
    ↓ return (num_examples, num_bytes)
```

### 9. BuilderConfig & Config ID System

`BuilderConfig` (in `builder.py`) defines dataset configuration uniqueness:

```python
@dataclass
class BuilderConfig:
    name: str = "default"
    version: Optional[Version] = Version("0.0.0")
    data_dir: Optional[str] = None
    data_files: Optional[Union[DataFilesDict, DataFilesPatternsDict]] = None
    description: Optional[str] = None
```

**`create_config_id()`** generates a unique cache directory identifier:

1. Start with config `name`
2. Add suffix for config_kwargs (excluding name, version):
   - String/bool/int/float kwargs → `key=value` encoding, hashed if >32 chars
   - Complex kwargs → full hash
3. If custom_features provided → hash features into suffix
4. `MAX_DATASET_CONFIG_ID_READABLE_LENGTH` limits raw suffix length

This ensures two datasets with different:
- data_files patterns
- config kwargs
- custom features

...get different cache directories even if they share the same `BuilderConfig.name`.

### 10. Zero-Cost Best Practices

1. **Choose the right format:**
   - Arrow IPC (`.arrow`): Fastest for read/write, good for single-node ML
   - Parquet (`.parquet`): Best for cloud storage, column pruning, and HF Dataset Viewer compatibility
   - JSONL (`.jsonl`): Human-readable, but 5-10x slower than Arrow for large datasets

2. **Pre-define `Features`** when creating datasets — saves the cost of schema inference and ensures deterministic type behavior.

3. **Set `writer_batch_size` for memory-constrained environments:**
   ```python
   # Smaller row groups for Parquet (default aims for 100MB)
   # For image datasets, use smaller batches
   ArrowWriter(features=features, writer_batch_size=50)
   ```

4. **Disable nullable for production datasets** — saves storage by not tracking nullability in schema:
   ```python
   ArrowWriter(features=features, disable_nullable=True)
   ```

5. **Use `embed_local_files=False`** for datasets with external files — only embed bytes when you need self-contained Arrow files.

6. **Prefont `OptimizedTypedSequence` column optimization** — naming your columns `input_ids`, `attention_mask`, etc. triggers automatic int precision reduction in `OptimizedTypedSequence`.

7. **Prefer `ParquetWriter` over `ArrowWriter`** when uploading to the Hub — HF Dataset Viewer reads Parquet natively and can do predicate pushdown.

8. **Use streaming for large-to-huge datasets** — `load_dataset(streaming=True)` avoids writing Arrow files entirely.

### 11. Source Code Map

| Module | Key Contents | Lines |
|--------|-------------|-------|
| `arrow_writer.py` | `ArrowWriter`, `ParquetWriter`, `TypedSequence`, `OptimizedTypedSequence` | 828 |
| `builder.py` | `DatasetBuilder`, `BuilderConfig`, `_prepare_split`, `_run_split_generators`, `_download_and_prepare` | 1916 |
| `table.py` | `table_cast`, `cast_array_to_feature`, `embed_table_storage` | 2482 |
| `config.py` | Batch size constants, CDC options, feature-based batch/row-group defaults | 277 |
| `fingerprint.py` | `Hasher`, caching control, `_TempCacheDir` | 480 |
| `utils/sharding.py` | `_number_of_shards_in_gen_kwargs`, `_split_gen_kwargs`, `_distribute_shards` | 92 |
| `features/features.py` | Feature type system, `_visit()`, `get_nested_type()`, `cast_to_python_objects()` | ~4000 |

### 12. Resources
- ArrowWriter source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/arrow_writer.py`
- Builder source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/builder.py`
- Table source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/table.py`
- PyArrow IPC: https://arrow.apache.org/docs/python/ipc.html
- Parquet format: https://parquet.apache.org/docs/
- HF Dataset Viewer: https://huggingface.co/docs/hub/en/datasets-viewer
