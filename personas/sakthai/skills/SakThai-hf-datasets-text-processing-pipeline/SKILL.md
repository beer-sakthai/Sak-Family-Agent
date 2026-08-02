---
name: SakThai-hf-datasets-text-processing-pipeline
description: "name: SakThai-hf-datasets-text-processing-pipeline"
---

# HF Datasets Text Processing and Deduplication Pipeline

## Description

Complete zero-cost reference for loading, cleaning, processing, and deduplicating text datasets using the `datasets` library (4.x/5.x). Covers text loading with `TextConfig` (line/paragraph/document modes), length/regex/batch filtering, exact deduplication via `filter()` with set-memory and pandas `drop_duplicates()`, fuzzy dedup with MinHash LSH (`datasketch`), batched `map()` for text transformation, streaming for large datasets, and full end-to-end pipeline orchestration. All techniques run on local CPU — no GPU, no API credits required.

## Files

- `references/hf-learnings.md` — Full reference with code examples, performance comparisons, and end-to-end pipeline

## Related Skills

- `hf-datasets-tabular-loading` — Loading tabular data with datasets
- `hf-datasets-from-parquet` — Loading Parquet files
- `hf-datasets-streaming-iterable-dataset` — Streaming large datasets
- `hf-datasets-5-release` — Datasets 5.x new features
- `hf-datasets-cache-management-deep-dive` — Cache management
- `hf-datasets-features-schema-casting` — Schema casting
