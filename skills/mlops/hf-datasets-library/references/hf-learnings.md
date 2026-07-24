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

---

## 2026-07-24: hf-datasets-streaming-iterable-dataset — Deep Dive (Topic #146)

### Summary
Complete deep-dive into streaming datasets with the `datasets` library's `IterableDataset` class. Streaming lets you process datasets larger than available RAM by fetching and decoding data on-the-fly without writing Arrow cache files. Covers all operations on iterable datasets, checkpoint/resume for training loops, and memory-efficient patterns for zero-cost environments.

### Why Stream?

| Factor | Regular `Dataset` | `IterableDataset` |
|--------|-------------------|-------------------|
| Memory | Loads all → memory-maps full Arrow file | Processes one shard at a time |
| Disk cache | Writes `.arrow` files to cache dir | No cache files created |
| Random access | Yes (index-based) | No (sequential iteration only) |
| Shuffle | Full Fisher-Yates shuffle | Buffer-based approximate shuffle |
| Map speed | Multi-process (`num_proc`) | Single-process by default |
| Use case | Datasets < available RAM | Datasets > RAM, or zero-cache env |

**Zero-cost fit:** Streaming is ideal when disk space is limited, when you're on a free-tier machine, or when you only need a subset of the data.

### Loading a Streaming Dataset

```python
from datasets import load_dataset

# Stream from the Hub — no download, no cache
ds_iter = load_dataset("SetFit/ag_news", split="train", streaming=True)
print(type(ds_iter))  # <class 'datasets.iterable_dataset.IterableDataset'>
print(ds_iter)        # IterableDataset({num_shards: 1, num_examples: ~120000})

# Get first few samples
for i, example in enumerate(ds_iter):
    if i >= 5:
        break
    print(example["text"][:50])
```

**Multiple splits:**
```python
dataset = load_dataset("SetFit/ag_news", streaming=True)
# dataset is a DatasetDict with IterableDataset values
train = dataset["train"]
test = dataset["test"]
```

### Column Indexing (Select Subset of Columns)

Reduce bandwidth by selecting only the columns you need before iterating:

```python
# Before any iteration — select columns
ds_iter = ds_iter.select_columns(["text", "label"])
# Now only "text" and "label" are fetched from the Hub
```

### Convert from Regular Dataset

```python
# Convert an already-loaded Dataset to IterableDataset
regular_ds = load_dataset("SetFit/ag_news", split="train")  # full download
iter_ds = regular_ds.to_iterable_dataset()
```

### Core Operations

#### 1. Take / Skip (Dataset Slicing)

```python
# Take first N examples
first_100 = ds_iter.take(100)

# Skip first N examples
skip_100 = ds_iter.skip(100)

# Chain: get examples 100–200
slice_100_200 = ds_iter.skip(100).take(100)
```

#### 2. Shuffle

Uses a **buffer-based shuffle** — fills a buffer of `buffer_size` examples from the start, then randomly yields from it, refilling as it goes:

```python
shuffled = ds_iter.shuffle(seed=42, buffer_size=10_000)
```

**Important limitations:**
- Larger buffer = better shuffle but more memory
- shuffle buffer is per-shard, not global
- Examples before the buffer is full are less random (cold start)
- For true global shuffle, use `reshuffle_at_each_epoch=True` in the DataLoader

**Reshuffle** (re-seed between epochs):
```python
shuffled = ds_iter.shuffle(seed=42, buffer_size=10_000, reshuffle_at_each_epoch=True)
```
When `reshuffle_at_each_epoch=True`, each full iteration through the dataset re-seeds the shuffle, producing a different order each epoch.

#### 3. Split Dataset

**Shard** — split into N chunks:
```python
# Get shard 0 of 10 shards
shard_0 = ds_iter.shard(num_shards=10, index=0)

# Check how many shards the dataset has internally
print(ds_iter.num_shards)  # e.g., 1 for single-shard datasets
```

**Note:** `num_shards` refers to the underlying Parquet/Arrow shard files in the dataset, not the shards you create with `.shard()`. `.shard()` creates logical splits and iterates over all internal shards.

#### 4. Concatenate

Chain two or more iterable datasets sequentially:
```python
from datasets import concatenate_datasets

# After iterating through ds1, continues with ds2
combined = concatenate_datasets([ds1, ds2])
```

#### 5. Interleave (Probabilistic Mixing)

Mix multiple datasets with controlled probabilities:
```python
from datasets import interleave_datasets

mixed = interleave_datasets(
    [ds_en, ds_fr, ds_de],
    probabilities=[0.5, 0.3, 0.2],
    seed=42,
    stopping_strategy="all_exhausted"  # or "first_exhausted"
)
```

**Stopping strategies:**
- `"all_exhausted"` (default): iterate until all source datasets are exhausted
- `"first_exhausted"`: stop when the first dataset runs out

#### 6. Rename, Remove, Cast

```python
# Rename a column
renamed = ds_iter.rename_column("original_name", "new_name")

# Remove columns
no_label = ds_iter.remove_columns(["label"])

# Cast feature types
casted = ds_iter.cast_column("label", ClassLabel(names=["bad", "good"]))
```

**Performance note:** `remove_columns()` on IterableDataset avoids copying data — it simply skips the column during iteration. This is faster than `map(remove_columns=...)`.

#### 7. Map (Transform)

`.map()` on IterableDataset processes elements one at a time (no multi-processing):

```python
def tokenize_fn(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length")

tokenized = ds_iter.map(tokenize_fn)
```

**Batch processing** (more efficient for tokenization):
```python
def tokenize_batch(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length")

tokenized = ds_iter.map(tokenize_batch, batched=True, batch_size=1000)
```

**Remove input columns after map:**
```python
tokenized = ds_iter.map(
    tokenize_batch,
    batched=True,
    batch_size=1000,
    remove_columns=["text"]  # drops after processing
)
```

#### 8. Filter

```python
def is_long_enough(example):
    return len(example["text"]) > 100

filtered = ds_iter.filter(is_long_enough)
```

**Filter with batching:**
```python
def filter_batch(examples):
    return [len(t) > 100 for t in examples["text"]]

filtered = ds_iter.filter(filter_batch, batched=True)
```

#### 9. Batch (Group into Batches)

```python
batched = ds_iter.batch(batch_size=32)
# Yields dict-of-lists with 32 examples each
for batch in batched:
    print(batch["text"][0])  # first example in batch
    # process batch...
```

**Drop last incomplete batch:**
```python
batched = ds_iter.batch(batch_size=32, drop_last_when_output_with_smaller_batch=False)
# The default keeps the last incomplete batch; set to True to drop it
```

### Streaming in a Training Loop

#### Basic Training Loop

```python
for epoch in range(num_epochs):
    for batch in ds_iter.batch(batch_size=32):
        outputs = model(**batch)
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
```

#### Checkpoint / Resume (Iteration State)

`IterableDataset` supports checkpoint and resume via `state_dict()` / `load_state_dict()`:

```python
# Before training, create the iterable
train_ds = load_dataset("deepmind/code_contests", streaming=True, split="train")

# Inside training loop — save checkpoint
state = train_ds.state_dict()  # saves current shard index + example offset
torch.save({"model_state": model.state_dict(), "data_state": state}, "checkpoint.pt")

# Resume
ckpt = torch.load("checkpoint.pt")
model.load_state_dict(ckpt["model_state"])
train_ds.load_state_dict(ckpt["data_state"])  # resumes exactly where we left off

for batch in train_ds.batch(batch_size=32):
    # continues from checkpoint position
    ...
```

**How checkpoint works internally:**
- `state_dict()` stores the current shard index and the example offset within that shard
- `load_state_dict()` skips already-consumed shards entirely, then skips the offset within the current shard
- Resuming is **fast** — it doesn't re-read consumed shards, but isn't instantaneous because it must skip to the correct offset in the current shard

**Integration with `StatefulDataLoader` (torchdata):**
```python
from torchdata.stateful_dataloader import StatefulDataLoader

dataloader = StatefulDataLoader(train_ds, batch_size=32, num_workers=4)
state_dict = dataloader.state_dict()  # uses train_ds.state_dict()
# save...
dataloader.load_state_dict(state_dict)  # resumes exactly
```

**Limitation with shuffle:** When using `.shuffle()`, the shuffle buffer state is **lost** on resume — the buffer is refilled with new data, so some examples may be seen again or missed.

### Save (Push to Hub)

Save an IterableDataset to the Hub (iterates fully and uploads Parquet):
```python
ds_iter.push_to_hub("username/my-dataset")
```

For multi-shard parallel upload:
```python
ds_iter.push_to_hub("username/my-dataset", num_proc=8)
```

Reload later:
```python
reloaded = load_dataset("username/my-dataset")
```

### Export to File

| Format | Method |
|--------|--------|
| CSV | `ds_iter.to_csv("path/to/data.csv")` |
| JSON | `ds_iter.to_json("path/to/data.json")` |
| Parquet | `ds_iter.to_parquet("path/to/data.parquet")` |
| SQL | `ds_iter.to_sql("sqlite:///db.sqlite", table_name="data")` |
| Pandas | `ds_iter.to_pandas()` |
| Polars | `ds_iter.to_polars()` |
| Dict | `ds_iter.to_dict()` |

Shard-aware export (one file per shard):
```python
num_shards = ds_iter.num_shards
for index in range(num_shards):
    shard = ds_iter.shard(index, num_shards)
    shard.to_parquet(f"data-{index:05d}.parquet")
```

### Practical Zero-Cost Patterns

#### Pattern 1: Preview Dataset Structure Without Download
```python
ds = load_dataset("bigdataset/name", split="train", streaming=True)
# Check schema from first example
sample = next(iter(ds))
print(sample.keys())
print(sample["text"][:100])
```

#### Pattern 2: Sample N Random Rows (Approximate)
```python
import random

ds = load_dataset("bigdataset/name", split="train", streaming=True)
# Shuffle with a reasonable buffer, take N
sample = ds.shuffle(seed=42, buffer_size=5000).take(100)
for row in sample:
    print(row["text"])
```

#### Pattern 3: Stream → Tokenize → Train (End-to-End)
```python
from transformers import AutoTokenizer
from datasets import load_dataset

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
ds = load_dataset("bigdataset/name", split="train", streaming=True)

def tokenize(batch):
    return tokenizer(
        batch["text"],
        truncation=True,
        padding="max_length",
        max_length=512,
    )

tokenized = ds.map(tokenize, batched=True, batch_size=1000, remove_columns=["text"])
# tokenized yields dicts with input_ids, attention_mask, token_type_ids
for batch in tokenized.batch(batch_size=16):
    # Use in training loop
    pass
```

#### Pattern 4: Streaming WebDataset-style
For large sharded datasets (e.g., LAION), you can stream directly:
```python
ds = load_dataset(
    "laion/laion2B-en",
    streaming=True,
    split="train",
    # WebDataset-style shards stream without local caching
)
```

#### Pattern 5: Cache-Control for Streaming
```python
# Force re-download even if cached
ds = load_dataset("...", streaming=True, download_mode="force_redownload")

# Don't cache at all
ds = load_dataset("...", streaming=True, cache_dir=None)
```

### Performance Considerations

| Aspect | Recommendation |
|--------|---------------|
| **Batch size in `.map()`** | 100–1000 is sweet spot for tokenization |
| **Shuffle buffer** | Start at 10K, adjust based on memory |
| **Column selection** | Use `select_columns()` before any `.map()` or iteration |
| **Remove columns in map** | Use `remove_columns` parameter in `.map()` — it's free |
| **Multi-shard datasets** | Leverage `num_shards` for parallel processing |
| **Checkpoint frequency** | Every 1000–10000 steps for training resume |
| **Filter before map** | Filter first to reduce map workload |

### Internal Architecture

`IterableDataset` is implemented in `datasets/iterable_dataset.py`. Key classes:

- **`IterableDataset`**: Main user-facing class, wraps a `_BaseIterableDataset` which forms a chain of transformations
- **`ShardDistributedReader` / `WorkerDistributedReader`**: Handle multi-shard/worker reading
- **`BufferShuffledExamplesMixin`**: Provides the shuffle buffer state management
- **`state_dict()` / `load_state_dict()`**: Checkpoint serialization via tracking shard index + example offset

The transformation chain is lazy — no computation happens until iteration begins. Each `.map()`, `.filter()`, `.shuffle()` call adds a wrapper to the chain.

### Key Limitations

1. **No `len()`** for multi-shard streaming datasets (unknown total until full iteration)
2. **No random access** — cannot index like `ds[42]`
3. **Shuffle is approximate** — buffer-based, not global Fisher-Yates
4. **Single-process `.map()`** — no `num_proc` for parallel processing
5. **Shuffle buffer lost on checkpoint resume** — buffer is drained and refilled
6. **Network-dependent** — iterating requires network access to the Hub

### Source
- Official docs: https://huggingface.co/docs/datasets/en/stream
- IterableDataset API: https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.IterableDataset
- Datasets source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/iterable_dataset.py`
