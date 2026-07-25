---
name: hf-datasets-5-release
author: SakThai
license: MIT
description: Complete reference for Hugging Face Datasets v5.0.0 — agent trace parsing, multi-shard streaming shuffle, Apache Iceberg, TsFile, 3D Mesh, CoNLL, and robotics batch batching.
version: 1.0.0
created: 2026-07-25
tags:
  - datasets
  - v5
  - release
  - features
---

# Hugging Face Datasets 5.0.0 — Major New Features
**license:** MIT  
**skill_type:** reference  
**domain:** datasets  
**version:** 1.0.0  
**created:** 2026-07-25  
**updated:** 2026-07-25  

## Description

Complete reference for Hugging Face Datasets **v5.0.0** (released June 5, 2026) — a major version jump from 4.8.5 with agent trace parsing, multi-shard streaming shuffle, new data formats (Apache Iceberg, TsFile, 3D Mesh, CoNLL), and robotics batch batching. This skill covers every new feature, API surface, and behavior change.

## Quick Reference

| Feature | API | Status |
|---------|-----|--------|
| Agent traces | `load_dataset(..., format="agent-traces")` + `teich` lib | New in 5.0.0 |
| Multi-shard shuffle | `ds.shuffle(seed=42, max_buffer_input_shards=10)` | New default |
| Batch by column | `ds.batch(by_column="episode")` | New |
| Apache Iceberg | `load_dataset("iceberg://...")` | New format |
| TsFile (IoTDB) | `load_dataset("tsfile://...")` | New format |
| 3D Mesh | `MeshFolder` builder | New format |
| CoNLL/CoNLL-U | `load_dataset("conllu://...")` | New format |

## Files

- `references/hf-learnings.md` — Full research with architecture, complete API reference, migration notes, and usage patterns

## Related Skills

- `hf-datasets-agent-traces-json-type` — Agent traces JSON type
- `hf-datasets-500-new-features-multi-shard-shuffle` — Multi-shard shuffle deep dive
- `hf-datasets-5-batch-by-column` — Batch by column feature
- `hf-datasets-streaming-iterable-dataset` — Streaming basics
- `hf-datasets-concatenate-and-interleave-deep-dive` — Dataset combining
