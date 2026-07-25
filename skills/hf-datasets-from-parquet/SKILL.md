# hf-datasets-from-parquet

**author:** SakThai
**license:** MIT

Expertise in creating Hugging Face Datasets from Parquet files using `Dataset.from_parquet()` and `to_parquet()`. Covers the full call chain through `ParquetDatasetReader`, `Parquet` (ArrowBasedBuilder), PyArrow `ParquetFileFormat`, filter pushdown, column projection, row group sharding, content-defined chunking (CDC), and write-side compression strategies. Includes zero-cost analytics patterns using DuckDB/Polars against Hub Parquet URLs.

## Key Areas

- `from_parquet()` static method — parameters, streaming vs map-style, remote URIs
- Internal architecture — `ParquetDatasetReader.read()` → `Parquet._generate_tables()` → PyArrow fragment scanning
- Row group sharding — `_generate_more_gen_kwargs()` splits files by individual row groups
- Filter pushdown — `pq.filters_to_expression()` and row group statistics skipping
- Column projection — `columns=` parameter for reading only needed columns
- FragmentScanOptions (v4.2.0+) — CacheOptions tuning for remote Parquet
- Bad file handling — `on_bad_files` parameter (error/warn/skip)
- Content-defined chunking — `DEFAULT_CDC_OPTIONS` (256KB-1MB)
- Compression strategy — Snappy for text, None for media, dictionary for text
- Config constants — `MAX_ROW_GROUP_SIZE`, `USE_PARQUET_EXPORT`, row group size overrides
- Integration with Datasets Server `/parquet` endpoint for zero-cost analytics
