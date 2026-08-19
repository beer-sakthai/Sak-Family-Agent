---
name: SakThai-hf-datasets-arrow-memory-architecture
description: "Deep reference on how HuggingFace Datasets manages memory through Apache Arrow \u2014\
  \ InMemoryTable vs MemoryMappedTable, ConcatenationTable, replay-based lazy transforms,\
  \ Arrow memory pools, and streaming memory patterns."
---

# HuggingFace Datasets Arrow Memory Architecture
**created:** 2026-07-25  
**type:** reference / deep-dive  
**depends_on:** hf-datasets-5-release

## Purpose

Deep reference on how HuggingFace Datasets manages memory through Apache Arrow — the dual-model table architecture (InMemoryTable vs MemoryMappedTable), ConcatenationTable block merging, replay-based lazy transforms, Arrow memory pools (mimalloc), batch sizing, and streaming memory patterns. Essential for debugging OOM, optimizing large dataset workflows, and understanding the `keep_in_memory` toggle.

## Key Concepts

| Concept | File | Description |
|---------|------|-------------|
| `InMemoryTable` | `table.py:695` | Loads entire Arrow file into RAM; pickling copies all data |
| `MemoryMappedTable` | `table.py:1046` | Maps file from disk; pickling only stores path + replays |
| `ConcatenationTable` | `table.py:1330` | Mix of InMemory/MemoryMapped blocks, concatenated on axis 0/1 |
| `Replay` | `table.py:1089` | Lazy transform log replayed on deserialisation |
| `IN_MEMORY_MAX_SIZE` | `config.py:232` | Environment toggle to force in-memory for small datasets |
| `ARROW_READER_BATCH_SIZE_IN_DATASET_ITER` | `config.py:193` | Preloaded record batch size for `Dataset.__iter__` |
| `is_small_dataset()` | `info_utils.py` | Returns True if dataset_size < IN_MEMORY_MAX_SIZE |
| `estimate_dataset_size()` | `file_utils.py` | Sum of stat().st_size over all Arrow files |

## Sources

- Source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/table.py`
- Source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/arrow_dataset.py`
- Source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/arrow_writer.py`
- Source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/config.py`
- Source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/formatting/formatting.py`
- Official docs: https://huggingface.co/docs/datasets/main/en/
