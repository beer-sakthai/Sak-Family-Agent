# HF Learnings — Parquet Column Selection & Filter Pushdown Deep Dive

**Learned:** 2026-07-24
**Topic:** hf-datasets-parquet-column-selection-deep-dive

## Summary

Deep-dive into the Hugging Face Datasets library's Parquet integration,
focusing on column projection (`columns=`), filter/predicate pushdown
(`filters=`), row group skipping, fragment scan options, content-defined
chunking, and practical zero-cost analytics with DuckDB and Polars.

## Key Findings

### Column Projection
- `columns=` param on `Dataset.from_parquet()` filters at the PyArrow scan level
- Nested field prefixes work: `"a"` selects `a.b`, `a.c`, `a.d.e`
- Only projected column chunks are read from disk — skipped columns have zero I/O
- Feature schema is auto-filtered to match projected columns

### Filter Pushdown
- `filters=` accepts `ds.Expression`, `list[tuple]` (AND), `list[list[tuple]]` (DNF)
- Internally: `pq.filters_to_expression()` → `parquet_fragment.to_batches(filter=...)`
- Row group statistics (min/max/null_count) enable skipping entire row groups
- Works identically in streaming mode — row groups skipped before any data transfer

### Fragment Scan Options (v4.2.0+)
- `ParquetFragmentScanOptions` controls buffering and prefetching
- Custom `CacheOptions` for tuning HTTP range requests on remote Parquet
- Critical for streaming from HF Hub with large row groups

### Writing
- `to_parquet()` uses `pq.ParquetWriter` with content-defined chunking (256KB–1MB)
- Batch size auto-tunes toward 100MB uncompressed row groups
- Compression: snappy for normal columns, none for media (Image/Audio)
- Column encoding: PLAIN for media, dictionary for text

### Config Constants
- `MAX_ROW_GROUP_SIZE = "100MB"` — default target size
- `DEFAULT_CDC_OPTIONS = {"min_chunk_size": 262144, "max_chunk_size": 1048576, "norm_level": 0}`
- Separate row group size overrides for audio/image/binary datasets

## Sources
- Source code: `src/datasets/arrow_dataset.py` — `from_parquet()` (line 1491), `to_parquet()` (line 5625)
- Source code: `src/datasets/io/parquet.py` — `ParquetDatasetReader`, `ParquetDatasetWriter`
- Source code: `src/datasets/packaged_modules/parquet/parquet.py` — `ParquetConfig`, `Parquet._generate_tables()`
- Source code: `src/datasets/config.py` — `MAX_ROW_GROUP_SIZE`, `DEFAULT_CDC_OPTIONS`, `USE_PARQUET_EXPORT`
- https://huggingface.co/docs/datasets — main docs
