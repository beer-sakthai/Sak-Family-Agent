---
name: SakThai-hf-datasets-from-parquet
description: "Deep dive into the Hugging Face Datasets library's `Dataset.from_parquet()` and `Dataset.to_parquet()`\
  \ methods. Covers the complete call chain \u2014 static method through `ParquetDatasetReader`,\
  \ the `Parquet` ArrowBasedBuilder, and PyArrow's `ParquetFileFormat` fragment scanning.\
  \ Includes full API surface, row group sharding architecture, filter pushdown via\
  \ `pq.filters_to_expression()`, column projection, content-defined chunking (CDC),\
  \ compression strategy per column type, bad file handling (v4.2.0+), `FragmentScanOptions`\
  \ for remote Parquet caching, and integration with the Datasets Server `/parquet`\
  \ endpoint for zero-cost analytics."
---

## Key Areas

- `from_parquet()` static method — 11 parameters (columns, filters, fragment_scan_options, on_bad_files, num_proc, etc.)
- Internal architecture — `ParquetDatasetReader.read()` → `Parquet._generate_tables()` → `ParquetFileFormat.make_fragment()` → `to_batches()`
- Row group sharding — `_generate_more_gen_kwargs()` splits each Parquet file by individual row groups for lazy loading
- Filter pushdown — `pq.filters_to_expression()` → PyArrow `to_batches(filter=...)` using row group column statistics
- Column projection — `columns=` parameter reads only selected column chunks; supports nested prefix matching
- FragmentScanOptions (v4.2.0+) — `ParquetFragmentScanOptions(cache_options=CacheOptions(...))` for remote Parquet HTTP range tuning
- Bad file handling — `on_bad_files` parameter: `"error" | "warn" | "skip"` (v4.2.0+)
- Content-defined chunking — `DEFAULT_CDC_OPTIONS = {"min_chunk_size": 262144, "max_chunk_size": 1048576}` for row group boundaries
- Compression strategy — Snappy for text, `"none"` for media (Image/Audio/Binary), dictionary encoding for text, PLAIN for media
- Config constants — `MAX_ROW_GROUP_SIZE = "100MB"`, `USE_PARQUET_EXPORT`, per-media-type row group size overrides
- Remote URI writing — supports `hf://`, `s3://`, `gs://` via fsspec with `storage_options` dict
- Integration with Datasets Server `/parquet` endpoint for zero-cost analytics with DuckDB/Polars
