---
name: SakThai-hf-datasets-server-parquet-conversion-pipeline-deep-dive
description: "Deep dive into the Hugging Face Datasets Server Parquet Conversion Pipeline \u2014\
  \ the automated system that converts every dataset on the Hub to Parquet format.\
  \ Covers streaming conversion, partial export for large datasets, copy-optimized\
  \ path for Parquet-native datasets, byte-level read/write tracking, writer batch\
  \ size tuning by modality, file naming conventions, sharding rules, the config-parquet-and-info\
  \ job runner, and how libviewer's Rust engine enables page-pruned queries.\n"
---

# HF Datasets Server Parquet Conversion Pipeline — Complete Architecture

## Overview

The Datasets Server automatically converts **every dataset** on the Hugging Face Hub to Parquet format. This enables performant server-side operations: row access, filtering via DuckDB SQL, full-text search, statistics computation, and columnar queries — all without downloading the full dataset.

This deep dive analyzes the actual source code (`datasets-server` repository on GitHub) to understand how the conversion pipeline works end-to-end.

### Architecture Summary

1. **Trigger:** Automatic, triggered when a dataset is uploaded/modified on the Hub
2. **Job:** `config-parquet-and-info` (main conversion)
3. **Output:** Parquet files pushed to `refs/convert/parquet` branch + metadata cached in MongoDB
4. **Two paths:**
   - **Copy path** (fast): Dataset is already in Parquet → copy LFS pointer files
   - **Convert path** (streaming): Any format → stream + write new Parquet files

---

## 1. Source Code Architecture

### Key Files

| File | Role |
|------|------|
| `services/worker/src/worker/job_runners/config/parquet_and_info.py` | **Main conversion job** — orchestrates copy or convert |
| `services/worker/src/worker/job_runners/config/parquet.py` | Config-level response aggregation |
| `services/worker/src/worker/job_runners/dataset/parquet.py` | Dataset-level response — merges all configs |
| `libs/libcommon/src/libcommon/parquet_utils.py` | Shared utilities: `RowsIndex`, metadata helpers |
| `libs/libcommon/src/libcommon/viewer_utils/parquet_metadata.py` | Parquet metadata file creation on disk |
| `libs/libviewer/src/parquet.rs` | **Rust engine**: page-level index for efficient scans |

### Processing Steps (for a single dataset config)

```
dataset-config-names → config-parquet-and-info → config-parquet → dataset-parquet
```

- `config-parquet-and-info` does the heavy lifting (conversion or copy)
- `config-parquet` reads the cached result and formats the response
- `dataset-parquet` merges all configs into a single response

---

## 2. The Two Conversion Paths

### Path A: Fast Copy for Parquet-Native Datasets

When the dataset is **already in Parquet format**, the server simply **copies** the LFS pointer files from the dataset's `main` branch to the `refs/convert/parquet` branch:

```python
# From parquet_and_info.py, function copy_parquet_files()
def copy_parquet_files(builder: DatasetBuilder) -> list[CommitOperationCopy]:
    for split in data_files:
        for shard_idx, data_file in enumerate(data_files[split]):
            src_revision, src_path_in_repo = data_file.split("@")[1].split("/", 1)
            parquet_file = ParquetFile(config, split, shard_idx, num_shards)
            parquet_operations.append(
                CommitOperationCopy(
                    src_path_in_repo=src_path_in_repo,
                    path_in_repo=parquet_file.path_in_repo,
                    src_revision=src_revision,
                )
            )
    return parquet_operations
```

Key detail: `is_parquet_builder_with_hub_files()` checks if all data files are HF Hub URLs (`hf://datasets/{repo_id}@{revision}/{path}`) — only then does the copy path activate.

**Exception:** If the row group size of original Parquet files is too large (>100-300MB), new Parquet files are generated even for Parquet-native datasets.

### Path B: Streaming Conversion for Non-Parquet Datasets

For datasets in CSV, JSONL, image folders, audio folders, or any other format:

```python
# From parquet_and_info.py, function stream_convert_to_parquet()
def stream_convert_to_parquet(builder, max_dataset_size_bytes, writer_batch_size=None):
    dl_manager = StreamingDownloadManager(...)
    for split in splits_generators:
        with limit_parquet_writes(builder, max_dataset_size_bytes), \
             track_reads() as reads_tracker, \
             disallow_embed_local_files():
            builder._prepare_split(split_generator=..., file_format="parquet")
```

This uses the Hugging Face `datasets` library's `_prepare_split()` method in **streaming mode** — data is read from source, rows are iterated, and Parquet files are written locally before being uploaded to the Hub.

---

## 3. The Conversion Pipeline in Detail

### 3.1 Writer Batch Size by Modality

Different data types get different row group sizes for optimal random access:

```python
def get_writer_batch_size_from_info(ds_config_info):
    if "Video(" in str(ds_config_info.features):
        return ROW_GROUP_SIZE_FOR_VIDEO   # Small batches for large videos
    elif "Audio(" in str(ds_config_info.features):
        return ROW_GROUP_SIZE_FOR_AUDIO
    elif "Image(" in str(ds_config_info.features):
        return ROW_GROUP_SIZE_FOR_IMAGE   # 100 rows per batch
    elif "Pdf(" in str(ds_config_info.features):
        return ROW_GROUP_SIZE_FOR_PDF
    elif "'binary'" in str(ds_config_info.features):
        return ROW_GROUP_SIZE_FOR_BINARY
    else:
        return None  # datasets default (1000 rows)
```

Smaller row groups mean faster random row access (fewer bytes read to fetch a single row).

### 3.2 Read Tracking

`track_reads` is a context manager that **monitors every byte read** from disk/network by wrapping `fsspec` file system `open()` methods:

```python
with track_reads() as reads_tracker:
    builder._prepare_split(...)
    # reads_tracker.files now has per-file read statistics
```

This data is used to estimate total dataset size when the conversion is partial (interrupted at 5GB limit).

### 3.3 Write Limiting

`limit_parquet_writes` uses a clever trick — it patches `pyarrow.parquet.ParquetWriter` to count bytes written, and patches the builder's `_generate_examples` or `_generate_tables` generator to stop yielding once the limit is reached:

```python
class _TrackedParquetWriter(pq.ParquetWriter):
    def write_table(self, pa_table, row_group_size=None):
        self.track_write_table(pa_table)  # counts pa_table.nbytes
        super().write_table(pa_table, row_group_size)

def limited_generator(generator):
    def wrapped(*args, **kwargs):
        for item in generator(*args, **kwargs):
            if limiter.total_bytes < limiter.max_dataset_size_bytes:
                yield item
            else:
                break  # STOP generating
    return wrapped
```

### 3.4 Partial Export Flag

When the 5GB limit is reached:
- `partial = True`
- Files are written to directories prefixed with `partial-` (e.g., `partial-train/` instead of `train/`)
- The split info is **estimated** from the sample of files read

```python
PARTIAL_PREFIX = "partial-"  # For paths like "en/partial-train/0000.parquet"
```

Split estimation uses the `reads_tracker` data:
```python
estimated_num_examples = int(shards_total_size / shards_total_read * split_info.num_examples)
```

### 3.5 File Naming Convention

```
{config}/{split}/{shard_index:04d}.parquet
{config}/partial-{split}/{shard_index:04d}.parquet
```

Sharding rules:
- If `num_shards > 10_000` (MAX_FILES_PER_DIRECTORY), additional suffix is added:
  `{config}/partial-{split}-part0/{shard:04d}.parquet`
- This avoids hitting the HF Hub's 10,000 files-per-directory limit

---

## 4. The Config-Level Response (`config-parquet`)

The `config-parquet` job runner is lightweight — it reads the cached `config-parquet-and-info` result and formats it:

```python
def compute_parquet_response(dataset, config):
    config_parquet_and_info_response = get_previous_step_or_raise(
        kind="config-parquet-and-info", dataset=dataset, config=config
    )
    parquet_files = [f for f in content["parquet_files"] if f.get("config") == config]
    parquet_files.sort(key=lambda x: (x["split"], x["filename"]))
    return ConfigParquetResponse(parquet_files=parquet_files, features=features, partial=partial)
```

## 5. The Dataset-Level Response (`dataset-parquet`)

Merges responses from all configs:

```python
for config_item in content["config_names"]:
    config = config_item["config"]
    try:
        response = get_response(kind="config-parquet", dataset=dataset, config=config)
        parquet_files.extend(config_parquet_content["parquet_files"])
    except CachedArtifactNotFoundError:
        pending.append(...)  # Still processing
    partial = partial or config_parquet_content["partial"]
```

Returns `pending` and `failed` configs along with the `parquet_files` array, allowing clients to track conversion progress.

---

## 6. Parquet Metadata Storage

### 6.1 Metadata File Creation

`create_parquet_metadata_file()` writes Parquet metadata to a dedicated directory:

```python
def create_parquet_metadata_file(dataset, config, split, parquet_file_metadata, filename, ...):
    dir_path = Path(parquet_metadata_directory) / dataset / DATASET_SEPARATOR / config / split
    parquet_file_metadata.write_metadata_file(dir_path / filename)
```

This metadata is used by the `RowsIndex` class to read Parquet schema, num rows, row group sizes, and column statistics without re-downloading the Parquet files.

### 6.2 RowsIndex for Querying

`RowsIndex` is the bridge between metadata and data querying:

```python
class RowsIndex:
    def __init__(self, dataset, config, split, parquet_metadata_directory, ...):
        self._init_dataset_info()     # loads metadata from cache
        self._init_viewer_index(hf_token, hf_endpoint, data_store)  # creates Rust libviewer index

    async def query(self, offset, length):
        return await self.query_libviewer_index(offset, length)
```

### 6.3 Rust libviewer Engine

The Rust library (`libs/libviewer/src/parquet.rs`) provides:

1. **Async reading** with scan size limits
2. **Page-level pruning** — only reads the pages containing requested rows
3. **Scan size enforcement** via `LimitedAsyncReader` that checks every read against a limit

```rust
pub struct LimitedAsyncReader<T: AsyncFileReader> {
    inner: T,
    scan_size_limit: u64,
}

impl<T: AsyncFileReader> AsyncFileReader for LimitedAsyncReader<T> {
    fn get_bytes(&mut self, range: Range<u64>) -> BoxFuture<'_, Result<Bytes>> {
        let num_bytes = range.end - range.start;
        if num_bytes > self.scan_size_limit {
            return error("Scan size limit exceeded");
        }
        self.inner.get_bytes(range)
    }
}
```

---

## 7. API Endpoints

### `GET /parquet` — List Parquet Files

```
GET https://datasets-server.huggingface.co/parquet?dataset=ibm/duorc
```

Response:
```json
{
  "parquet_files": [
    {"dataset": "ibm/duorc", "config": "ParaphraseRC", "split": "train",
     "url": "https://.../refs%2Fconvert%2Fparquet/ParaphraseRC/train/0000.parquet",
     "filename": "0000.parquet", "size": 26005668}
  ],
  "pending": [],
  "failed": [],
  "partial": false
}
```

### `GET /api/datasets/{dataset}/parquet` — Hub API (alternative)

```
GET https://huggingface.co/api/datasets/ibm/duorc/parquet
```

Returns nested dict by config and split, with URLs to individual shards.

---

## 8. Access Control

- **Public datasets:** Auto-converted and available via API
- **Private datasets:** Only converted if owned by a PRO user or Enterprise organization
- **Gated datasets:** Follow the same rules as private (depends on ownership)

---

## 9. Performance & Limits

| Metric | Limit | Effect |
|--------|-------|--------|
| Max dataset size for full conversion | 5GB per config | `partial=true` for larger datasets |
| Max files per directory | 10,000 | Shards split into `-partN` subdirectories |
| Max operations per commit | 500 | Conversion commits are chunked |
| Default row group size | 1,000 rows | Lowered to 100 for image datasets |
| Max parquet file size | ~500MB | Datasets auto-sharded at this threshold |

---

## 10. Best Practices for Dataset Publishers

1. **Upload in Parquet format** if possible — conversion is skipped, copy is fast
2. **Keep row groups small** (100-300MB uncompressed) — enables fast random access
3. **Avoid single massive files** — shard large datasets (~500MB per parquet file)
4. **Use `safetensors` not Pickle** for weights — eliminates security scanning delays
5. **Make datasets public** or own them via PRO/Enterprise — private datasets without PRO access won't get Parquet conversion

---

## Sources

- Datasets Server source code: https://github.com/huggingface/datasets-server
  - `services/worker/src/worker/job_runners/config/parquet_and_info.py`
  - `services/worker/src/worker/job_runners/config/parquet.py`
  - `services/worker/src/worker/job_runners/dataset/parquet.py`
  - `libs/libcommon/src/libcommon/parquet_utils.py`
  - `libs/libcommon/src/libcommon/viewer_utils/parquet_metadata.py`
  - `libs/libviewer/src/parquet.rs`
- Documentation: https://huggingface.co/docs/dataset-viewer/parquet
- API: https://datasets-server.huggingface.co/openapi.json
