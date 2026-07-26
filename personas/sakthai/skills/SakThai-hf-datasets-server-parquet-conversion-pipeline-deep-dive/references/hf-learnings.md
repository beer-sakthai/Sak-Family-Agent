# HF Datasets Server Parquet Conversion Pipeline — Deep Dive

**Learned:** 2026-07-25 | **Topic:** `hf-datasets-server-parquet-conversion-pipeline-deep-dive` (Topic #376)
**Sources:** Datasets Server source code analyzed from `main` branch (2026-07-25)

## Summary

Deep dive into the Hugging Face Datasets Server's Parquet Conversion Pipeline — the automated system that converts every dataset on the Hub to Parquet format. Unlike the `datasets` library's `from_parquet()` which loads Parquet into memory, this is a server-side pipeline that:

1. Automatically triggers on dataset upload/modification
2. Either **copies** existing Parquet files (fast path) or **stream-converts** from source format (CSV, JSONL, images, audio, etc.)
3. Tracks byte-level reads and writes to enforce the 5GB limit for partial exports
4. Pushes converted files to a special `refs/convert/parquet` branch
5. Caches metadata for efficient server-side queries (rows, filter, search, statistics)

## Key Findings

### Two Conversion Paths

- **Copy path (fast):** When the dataset is already in Parquet format and all data files are on the Hub, files are copied via `CommitOperationCopy` — no re-encoding needed, LFS pointers are just duplicated
- **Convert path (streaming):** Uses `datasets` library's `_prepare_split()` in streaming mode with `StreamingDownloadManager` — reads source data and writes Parquet files without downloading the full dataset

### Streaming Conversion Core

The `stream_convert_to_parquet()` function orchestrates the convert path:

1. **Read tracking** (`track_reads`): Wraps `fsspec` filesystem `open()` methods to count every byte read from source files
2. **Write limiting** (`limit_parquet_writes`): Patches `pyarrow.parquet.ParquetWriter` to track `pa_table.nbytes` per write, and stops the generator when `max_dataset_size_bytes` (5GB) is reached
3. **Embedded files disabled** (`disallow_embed_local_files`): Patches `ParquetWriter` to set `embed_local_files=False`, preventing large binary blobs from bloating Parquet files

### Modality-Specific Row Group Sizes

| Modality | Row Group Size | Rationale |
|----------|---------------|-----------|
| Text/default | 1,000 rows (datasets default) | Good balance |
| Image folders | 100 rows | Smaller row groups = faster random access |
| Audio folders | Configurable low batch size | Per-audio-row overhead |
| Video folders | Configurable low batch size | Per-video-row overhead |
| PDF folders | Configurable low batch size | Per-PDF-row overhead |
| Binary columns | Configurable low batch size | Large binary blobs |

### Partial Export Mechanism

- **Trigger:** Dataset exceeds ~5GB per config
- **Behavior:** Conversion stops after 5GB, remaining rows are not processed
- **Detection:** `partial-` prefix on split directory names
- **Split info estimation:** Uses tracked read bytes ratio (`reads_tracker.files`) to estimate total dataset size: `estimated_examples = (total_size / sampled_reads) * sampled_examples`
- **Edge case:** For `_CountableBuilderMixin` datasets, uses `builder._count_examples()` for estimation

### File Naming and Sharding

```
{config}/{split}/{shard:04d}.parquet          # Standard
{config}/partial-{split}/{shard:04d}.parquet   # Partial (5GB limit hit)
{config}/partial-{split}-part0/{shard:04d}.parquet  # >10,000 shards
```

- Max 10,000 files per directory (Hub limitation)
- Shard index is 4 digits (0000-9999)
- `-` is forbidden in split names, so `partial-` prefix and `-partN` suffix are collision-safe

### Parquet Metadata System

- Metadata stored in dedicated directory: `{parquet_metadata_dir}/{dataset}/--/{config}/{split}/`
- Each Parquet file's metadata (`num_rows`, `row_group_size`, `schema`, `column_stats`) is written to a separate metadata file
- `RowsIndex` class loads metadata from cache (MongoDB) and creates Rust `libviewer` index for efficient queries
- Metadata enables: schema discovery, row count, column type inference, row group & page-level pruning

### Rust libviewer Engine

- Written in Rust (`libs/libviewer/src/parquet.rs`)
- Provides `AsyncFileReader` with `LimitedAsyncReader` wrapper
- Enforces scan size limits at the byte level
- Enables page-level column pruning for efficient row access
- Supports column projection and row group skipping

### API Endpoints

- `/parquet` — List all parquet files for a dataset (config-level and dataset-level)
- `/api/datasets/{dataset}/parquet` — Hub API alternative with nested config/split structure
- `refs/convert/parquet` branch — Where the actual Parquet files live

### Limits

| Limit | Value | Notes |
|-------|-------|-------|
| Full conversion cap | 5GB | Beyond this, `partial=true` |
| Files per dir | 10,000 | HF Hub limit |
| Ops per commit | 500 | Conversion commits chunked |
| Row group target | 100-300MB uncompressed | Optimal for random access |

### Skill Created

`hf-datasets-server-parquet-conversion-pipeline-deep-dive/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md covering streaming conversion, partial export, copy path, read/write tracking, sharding rules, metadata storage, Rust libviewer engine, and API endpoints.

---

## Sources
- https://github.com/huggingface/datasets-server – services/worker/src/worker/job_runners/config/parquet_and_info.py
- https://github.com/huggingface/datasets-server – libs/libcommon/src/libcommon/parquet_utils.py
- https://github.com/huggingface/datasets-server – libs/libcommon/src/libcommon/viewer_utils/parquet_metadata.py
- https://github.com/huggingface/datasets-server – libs/libviewer/src/parquet.rs
- https://huggingface.co/docs/dataset-viewer/parquet
