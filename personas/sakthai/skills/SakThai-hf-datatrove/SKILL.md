---
name: SakThai-hf-datatrove
version: 1.0.0
description: Complete reference on Hugging Face DataTrove — the large-scale text data
  processing library for LLM training data pipelines. Covers pipeline blocks, executors
  (Local/Slurm/Ray/Jobs), deduplication (minhash/exact-substr/sentence), Synthetic
  data generation via inference rollouts, HF Storage Buckets integration, and the
  FineWeb replication pipeline.
category: mlops
tags:
- datatrove
- hf
- huggingface
author: SakThai
license: MIT
---

# HF DataTrove — Large-Scale Data Processing for LLM Training

**Trigger when:** user asks about large-scale data processing, cleaning datasets for LLM training, deduplication (minhash/exact-substr/sentence), CommonCrawl processing, FineWeb replication, synthetic data generation pipelines, running data pipelines on Slurm/Ray/HF Jobs, or the `datatrove` library itself.

## Overview

DataTrove is Hugging Face's **library for processing, filtering, and deduplicating text data at very large scale**. It provides prebuilt processing blocks with a framework for custom functionality. Pipelines are platform-agnostic — they run locally, on Slurm clusters, Ray clusters, or on [Hugging Face Jobs](https://huggingface.co/docs/huggingface_hub/en/guides/jobs) without code changes.

| Attribute | Value |
|-----------|-------|
| **Repository** | https://github.com/huggingface/datatrove |
| **PyPI** | `pip install datatrove` (with extras) |
| **License** | Apache-2.0 |
| **Stars** | 3.2k |
| **Python** | >=3.10 |
| **Used By** | FineWeb, FineWeb-Edu, FineWeb-2, DCLM, Cosmopedia, Smol-scale |
| **Key Cite** | Penedo et al. 2024 — `@misc{penedo2024datatrove}` |

**Core design principles:**
- **Platform-agnostic**: Same pipeline code runs on laptop, Slurm, Ray, or HF Jobs
- **Resumable**: Tracks completed tasks via marker files — restarting re-runs only failed tasks
- **Low memory**: Processes documents in streaming generators, not loading everything into RAM
- **Extensible**: Custom blocks via inheritance from `PipelineStep`, `BaseFilter`, `BaseExtractor`, `BaseReader`, or `DiskWriter`

## Architecture

### The DataTrove Document

Every pipeline processes [`Document`](https://github.com/huggingface/datatrove/blob/main/src/datatrove/data.py) objects:

```python
from datatrove.data import Document

doc = Document(
    text="the actual text content",
    id="unique-string-id",
    metadata={"source": "commoncrawl", "lang": "en"}  # optional dict
)
```

Each pipeline block takes a generator of `Document` and returns a generator of `Document`.

### Pipeline Block Types

| Block Type | Module | Purpose | Examples |
|-----------|--------|---------|---------|
| **Reader** | `datatrove.pipeline.readers` | Read data from storage formats | `JsonlReader`, `ParquetReader`, `CsvReader`, `HuggingFaceReader`, `WarcReader` |
| **Writer** | `datatrove.pipeline.writers` | Save processed data | `JsonlWriter`, `ParquetWriter`, `HuggingFaceBucketWriter`, `HuggingFaceDatasetWriter`, `TokenizedWriter` |
| **Extractor** | `datatrove.pipeline.extractors` | Extract text from raw formats | `Trafilatura` (HTML→text) |
| **Filter** | `datatrove.pipeline.filters` | Remove documents by criteria | `LanguageFilter`, `QualityFilter`, `SamplerFilter`, `RegexFilter`, `URLFilter`, `WordCountFilter`, `GopherQualityFilter`, `C4QualityFilter`, `FineWebQualityFilter` |
| **Stats** | `datatrove.pipeline.stats` | Collect distributed statistics | `DocStats`, `LangStats`, `LineStats`, `WordStats`, `TokenStats`, `SentenceStats` |
| **Tokens** | `datatrove.pipeline.tokens` | Tokenize or count tokens | `Tokenizer`, `OpenAITokenizer`, `Counter` |
| **Dedup** | `datatrove.pipeline.dedup` | Deduplicate data | `MinhashDedup`, `ExactSubstrDedup`, `SentenceDedupFilter` |
| **Inference** | `datatrove.pipeline.inference` | LLM-based data generation | `InferenceRunner` with rollout functions |

### Full Pipeline Example

```python
from datatrove.pipeline.readers import ParquetReader
from datatrove.pipeline.filters import SamplerFilter
from datatrove.pipeline.writers import JsonlWriter

pipeline = [
    ParquetReader(data_folder="/my/input/data"),
    SamplerFilter(rate=0.5),          # keep 50% of documents randomly
    JsonlWriter(output_folder="/my/output/data"),
]
```

## Terminology

| Term | Definition |
|------|------------|
| **Pipeline** | List of processing steps (read → filter → write, etc.) |
| **Executor** | Runs a pipeline on a specific environment (Local, Slurm, Ray, Jobs) |
| **Job** | Execution of a pipeline on an executor |
| **Task** | A job comprises multiple tasks, each processes one shard of data |
| **File** | An individual input file (.json, .csv, .parquet, .warc) — each file is processed by a single task |
| **Shard** | A group of input files assigned to a specific task |
| **Worker** | Compute resource executing one task at a time (e.g., one CPU core) |

> ⚠️ **File-to-task mapping:** Each file is processed by a single task. DataTrove does NOT split a single file across tasks. To fully parallelize, have multiple medium-sized files rather than one giant file.

> ⚠️ **Tasks > files:** If `tasks > files`, some tasks will have no data. Usually no reason to set `tasks > files`.

## Executors

Pipelines are platform-agnostic. The same pipeline list works on any executor.

### Common Executor Options

- `pipeline`: list of pipeline steps
- `logging_dir`: DataFolder path for logs, stats, completions
- `skip_completed`: bool (default `True`) — skip already completed tasks on re-run
- `randomize_start_duration`: int (default `0`) — max seconds to stagger task starts

### LocalPipelineExecutor

Runs on a local machine. Uses Python multiprocessing.

```python
from datatrove.executor import LocalPipelineExecutor

executor = LocalPipelineExecutor(
    pipeline=[ParquetReader("input/"), JsonlWriter("output/")],
    logging_dir="logs/",
    tasks=100,           # total shards
    workers=10,          # parallel tasks (CPU cores)
    start_method="fork",  # multiprocessing start method
)
executor.run()
```

**Multi-node parallelism** (e.g., multiple machines): Use `local_tasks` and `local_rank_offset` to split total tasks across machines. All machines must use the same `tasks` value.

### SlurmPipelineExecutor

Runs on a Slurm cluster using job arrays.

```python
from datatrove.executor import SlurmPipelineExecutor

executor = SlurmPipelineExecutor(
    pipeline=[...],
    logging_dir="logs/",
    tasks=500,
    workers=100,             # run 100 tasks simultaneously
    time="10:00:00",         # 10 hours
    partition="hopper-cpu",
    job_name="data_processing",
    cpus_per_task=1,
    mem_per_cpu_gb=2,
    depends=other_executor,  # chain dependency
)
executor.run()
```

**Chained dependencies:** Pass one executor as `depends=` to another — the second only starts after the first completes successfully.

### RayPipelineExecutor

Runs on a Ray cluster.

```python
import ray
from datatrove.executor import RayPipelineExecutor

ray.init()
executor = RayPipelineExecutor(
    pipeline=[...],
    logging_dir="logs/",
    tasks=500,
    workers=100,
    cpus_per_task=1,
    mem_per_cpu_gb=2,
)
executor.run()
```

### JobsPipelineExecutor (Experimental)

**Experimental — may change or be removed.** Runs pipelines on [Hugging Face Jobs](https://huggingface.co/docs/huggingface_hub/en/guides/jobs). Each block of tasks runs in a cloud Job.

```python
from datatrove.executor import JobsPipelineExecutor

executor = JobsPipelineExecutor(
    pipeline=[...],
    logging_dir="hf://buckets/myorg/bucket/logs",
    tasks=500,
    workers=50,
    job_name="my-datatrove-job",
)
executor.run()
```

### Resume / Restart Behavior

DataTrove creates **completion markers** (empty files) in `${logging_dir}/completions/` for each successfully completed task. When re-launched, only incomplete tasks run.

> ⚠️ **Critical:** Do NOT change `tasks` count when restarting failed tasks — it affects input file distribution (sharding) and previously completed tasks may process different files.

## Logging & Stats Structure

```
mylogspath/exp1/
├── executor.json            # executor + pipeline config dump
├── launch_script.slurm      # Slurm config (if on Slurm)
├── executor.pik             # pickled executor
├── ranks_to_run.json        # list of tasks being run
├── logs/
│   ├── task_00000.log
│   ├── task_00001.log       # per-task log files
│   └── ...
├── completions/
│   ├── 00004                # empty marker files
│   ├── 00007
│   └── ...
└── stats/
    ├── 00000.json           # per-task stats
    ├── 00001.json
    ├── ...
    └── stats.json           # global merged stats
```

---

## Deep Dive Reference

For exhaustive reference specifications, cookbook snippets, and extended documentation, see [DataTrove Pipeline & Transformations Guide](./references/datatrove-pipelines-and-transforms.md).
