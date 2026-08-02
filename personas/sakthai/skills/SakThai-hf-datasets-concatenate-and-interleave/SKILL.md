---
name: SakThai-hf-datasets-concatenate-and-interleave
description: "Complete reference on concatenating and interleaving Hugging Face Datasets — covering concatenate_datasets (axis=0/1), interleave_datasets (with probabilities, stopping strategies), map-style vs iterable internals, and v5 multi-shard considerations."
---

## Description
Covers `concatenate_datasets()` and `interleave_datasets()` from the `datasets.combine` module — the two primary ways to merge multiple datasets. Includes vertical/horizontal concatenation, probabilistic/cyclic interleaving, all three stopping strategies, map-style vs iterable implementation differences, resharding for parallelism, and edge cases.

## Key Resources
- [combine.py source (v5.0.0)](https://github.com/huggingface/datasets/blob/5.0.0/src/datasets/combine.py)
- [concatenate_datasets docs](https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.concatenate_datasets)
- [interleave_datasets docs](https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.interleave_datasets)
- [arrow_dataset.py internal implementations](https://github.com/huggingface/datasets/blob/5.0.0/src/datasets/arrow_dataset.py)
- [iterable_dataset.py internal implementations](https://github.com/huggingface/datasets/blob/5.0.0/src/datasets/iterable_dataset.py)

## Topics Covered
- `concatenate_datasets(dsets, axis=0)` — vertical stacking (rows) with schema alignment
- `concatenate_datasets(dsets, axis=1)` — horizontal stacking (columns) with row count matching
- Missing data filled with None via `_align_features`
- `interleave_datasets(datasets)` — cycling without replacement
- `interleave_datasets(datasets, probabilities=[...])` — probabilistic sampling
- Stopping strategies: `first_exhausted`, `all_exhausted`, `all_exhausted_without_replacement`
- Map-style interleave: clever `offsets + arange` index computation
- Iterable interleave: `CyclingMultiSourcesExamplesIterable` / `RandomlyCyclingMultiSourcesExamplesIterable`
- `IterableDataset.reshard()` for parallelism before interleaving
- Network-distributed interleaving via `_split_by_node`
- Anti-patterns: mixing DatasetDict without split selection, mixing Dataset+IterableDataset, row count mismatch on axis=1
