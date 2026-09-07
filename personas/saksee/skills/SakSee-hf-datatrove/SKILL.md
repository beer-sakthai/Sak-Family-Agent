---
name: SakSee-SakThai-hf-datatrove
description: "Complete reference on Hugging Face DataTrove — the large-scale text data processing library for LLM training data pipelines. Covers pipeline blocks, executors (Local/Slurm/Ray/Jobs), deduplication (minhash/exact-substr/sentence), Synthetic data gener"
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

## Reading Data

Readers convert input formats into `Document` generators. Most readers accept:

- `data_folder` (str/DataFolder): input path
- `text_key` (str): dict key for text content (default: `"text"`)
- `id_key` (str): dict key for document ID (default: `"id"`)
- `default_metadata` (dict): metadata to add to every document
- `recursive` (bool): search subdirectories
- `glob_pattern` (str): file filter (e.g., `*/warc/*.warc.gz`)
- `adapter` (callable): custom function to map raw dict to Document fields
- `limit` (int): read only N samples (for testing)

### Available Readers

| Reader | Use For |
|--------|---------|
| `JsonlReader` | JSONL files (.jsonl.gz) |
| `ParquetReader` | Parquet files |
| `CsvReader` | CSV/TSV files |
| `HuggingFaceReader` | HF Hub datasets |
| `WarcReader` | WARC/ARC/WET files (CommonCrawl) |
| `TextFileReader` | Plain text files |

**HF Hub dataset reader:**
```python
from datatrove.pipeline.readers import HuggingFaceReader

# Stream a dataset from the Hub in sharded fashion
reader = HuggingFaceReader(
    "HuggingFaceFW/fineweb",
    split="train",
    streaming=True,       # recommended for large datasets
    text_key="text",
    glob_pattern="*sample/*.parquet",  # filter specific files
)
```

## Writing Data

Writers save `Document` objects to disk/cloud. Key options:

- `output_folder`: destination path
- `compression`: default `"gzip"`
- `output_filename`: template string with `${rank}`, `${id}`, and metadata variables

### Available Writers

| Writer | Use For |
|--------|---------|
| `JsonlWriter` | JSONL format |
| `ParquetWriter` | Parquet format |
| `HuggingFaceBucketWriter` | HF Storage Buckets (raw/intermediate) |
| `HuggingFaceDatasetWriter` | Published HF datasets |
| `TokenizedWriter` | Tokenized arrays (for training) |

### HF Hub Output Strategy

```python
from datatrove.pipeline.writers import HuggingFaceBucketWriter, HuggingFaceDatasetWriter

# For raw/intermediate output (S3-like, mutable, no versioning):
HuggingFaceBucketWriter(
    bucket="myorg/my-bucket",
    prefix="v1/raw",
    private=True,
    overwrite=True,  # delete existing files at prefix first
)

# For the published, ready-to-share dataset:
HuggingFaceDatasetWriter(
    dataset="myorg/my-dataset",
    private=True,
)
```

**Output filename template:**
```python
JsonlWriter(
    "output/",
    output_filename="${language}/data/${rank}.jsonl.gz",
    # Creates: output/en/data/00000.jsonl.gz, output/fr/data/00001.jsonl.gz
)
```

## Extracting Text

For raw web data (HTML from CommonCrawl WARC files), use the Trafilatura extractor:

```python
from datatrove.pipeline.extractors import Trafilatura

extractor = Trafilatura(
    prefer_links=True,     # keep hyperlinks as markdown
    include_comments=False # skip HTML comments
)
```

## Filtering Data

Filters return `True` to keep a document, `False` to remove it. Removed documents do not continue — but you can save them to an `exclusion_writer`.

### Available Filters

| Filter | What It Does |
|--------|-------------|
| `LanguageFilter` | Keep docs in specified languages (uses FastText) |
| `QualityFilter` | Composite quality score based on multiple signals |
| `SamplerFilter` | Randomly sample documents (use `rate` parameter) |
| `RegexFilter` | Remove docs matching regex patterns |
| `URLFilter` | Blocklist/allowlist URLs |
| `WordCountFilter` | Keep docs within word count range |
| `GopherQualityFilter` | DeepMind Gopher quality heuristics |
| `C4QualityFilter` | C4 dataset quality criteria |
| `FineWebQualityFilter` | FineWeb's custom quality heuristics |
| `SentenceCountFilter` | Keep docs within sentence count range |
| `MeanWordLengthFilter` | Keep docs within mean word length range |
| `CharacterRepetitionFilter` | Filter by character-level repetition ratio |
| `WordRepetitionFilter` | Filter by word-level repetition ratio |
| `SpecialCharFilter` | Filter by special character ratio |
| `StopWordsFilter` | Filter by stop word ratio |
| `BulkEmailFilter` | Remove bulk email/social media content |
| `CookiesFilter` | Remove cookie/consent popup text |

**Example — language + quality filter:**
```python
from datatrove.pipeline.filters import LanguageFilter, FineWebQualityFilter

pipeline = [
    ParquetReader("my_input/"),
    LanguageFilter(languages=["en", "fr", "de"]),
    FineWebQualityFilter(),
    JsonlWriter("my_output/"),
]
```

## Deduplication

Three levels of deduplication, each with different sensitivity and computational cost:

### 1. MinHash Deduplication (fuzzy dedup)

Best for finding near-duplicate documents. Uses MinHash signatures with LSH (Locality-Sensitive Hashing).

```python
# Full pipeline: minhash_deduplication.py
from datatrove.pipeline.dedup.minhash import (
    MinhashConfig, MinhashDedupFilter, MinhashDedupBuckets,
    MinhashLSH, MinhashDedupSignature, MinhashDedupCluster
)

# Stage 1: Compute MinHash signatures
stage1 = MinhashDedupSignature(
    output_folder="intermediate/sigs/",
)

# Stage 2: Bucket signatures by LSH
stage2 = MinhashDedupBuckets(
    output_folder="intermediate/buckets/",
    config=MinhashConfig(
        ngrams=5,          # 5-shingling
        num_bands=20,      # LSH bands
        num_rows=5,        # rows per band
        seed=42,
    ),
)

# Stage 3: Cluster duplicates
stage3 = MinhashDedupCluster(
    input_folder="intermediate/buckets/",
    output_folder="intermediate/clusters/",
)

# Stage 4: Filter duplicates from original data
stage4 = MinhashDedupFilter(
    data_folder="input/",
    clusters_folder="intermediate/clusters/",
    exclusion_writer=JsonlWriter("removed/"),
)
```

### 2. Exact Substring Dedup (aggressive)

Removes documents that share long exact substring overlaps. Requires [Google's deduplicate-text-datasets](https://github.com/google-research/deduplicate-text-datasets) tool.

### 3. Sentence-Level Exact Dedup (lightweight)

Removes documents where sentences exactly match another document's sentences:

```python
from datatrove.pipeline.dedup import SentenceDedupFilter
```

## Statistics Collection

Distributed statistics collection across shards:

```python
from datatrove.pipeline.stats import (
    DocStats, LangStats, WordStats, LineStats,
    ParagraphStats, SentenceStats, TokenStats,
)

pipeline = [
    ParquetReader("input/"),
    DocStats(),
    LangStats(),
    WordStats(),
    TokenStats(tokenizer="gpt2"),
    JsonlWriter("output/"),
]
```

Each stat type produces a `MetricStatsDict` object in the stats folder.

**Merging stats across machines:** Use the `merge_stats` script on the combined stats directory after multi-node runs.

## Tokenization

Tokenize data for training or count tokens:

```python
from datatrove.pipeline.tokens import Tokenizer, Counter

# Tokenize and save token IDs
pipeline = [
    JsonlReader("input/"),
    Tokenizer(
        tokenizer_name="path/to/tokenizer",
        save_metadata=["language"],  # preserve selected metadata
        output_folder="tokenized_output/",
    ),
]

# Count tokens only (no save)
pipeline = [
    JsonlReader("input/"),
    Counter(tokenizer="gpt2"),
]
```

## Synthetic Data Generation via Inference

DataTrove integrates with vLLM, SGLang, and OpenAI-compatible endpoints for LLM-based data generation at scale.

### InferenceRunner Block

```python
from datatrove.data import Document
from datatrove.executor.local import LocalPipelineExecutor
from datatrove.pipeline.inference.run_inference import (
    InferenceConfig, InferenceRunner
)
from datatrove.pipeline.writers import JsonlWriter

async def my_rollout(doc: Document, generate):
    """A rollout function — receives a doc and a generate() callback."""
    payload = {
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": doc.text}]}
        ],
        "max_tokens": 2048,
    }
    return await generate(payload)

documents = [Document(text="What's the weather?", id=str(i)) for i in range(100)]

config = InferenceConfig(
    server_type="vllm",              # "vllm", "sglang", "openai", or "dummy"
    model_name_or_path="Qwen/Qwen3-0.6B",
    rollouts_per_document=1,
    max_concurrent_generations=500,
)

LocalPipelineExecutor(
    pipeline=[
        documents,
        InferenceRunner(
            rollout_fn=my_rollout,
            config=config,
            skip_bad_requests=True,
            records_per_chunk=500,
            checkpoints_local_dir="/tmp/checkpoints/",
            output_writer=JsonlWriter("output/", output_filename="${rank}_chunk_${chunk_index}.jsonl"),
        ),
    ],
    logging_dir="logs/inference",
    tasks=1,
).run()
```

### Key Inference Features

| Feature | How |
|---------|-----|
| **Custom rollouts** | Async callable receives doc + `generate()` + `shared_context` |
| **Checkpointing** | `checkpoints_local_dir` + `records_per_chunk` for resumable generation |
| **Request dedup** | SQLite-backed `RequestCache` avoids re-sending completed payloads |
| **Skip bad requests** | `skip_bad_requests=True` — handles context-overflow errors gracefully |
| **Multi-rollout** | `rollouts_per_document > 1` runs same rollout multiple times per doc |
| **Progress monitoring** | `InferenceProgressMonitor` updates HF dataset card with progress bar + ETA |
| **Dataset card gen** | `InferenceDatasetCardGenerator` creates final stats card after completion |
| **Benchmarking** | Sweep experiments via YAML config + `launch_experiments.py` / `analyze_results.py` |

### Progress Monitoring

```python
from datatrove.pipeline.inference import (
    InferenceDatasetCardParams, InferenceProgressMonitor,
    InferenceDatasetCardGenerator,
)

params = InferenceDatasetCardParams(
    output_repo_id="myuser/output-dataset",
    input_dataset_name="simplescaling/s1K-1.1",
    input_dataset_split="train",
    model_name="Qwen/Qwen3-0.6B",
)

monitor_pipeline = [InferenceProgressMonitor(params=params, update_interval=3600)]
datacard_pipeline = [InferenceDatasetCardGenerator(params=params)]
```

## HF Storage Buckets Integration

DataTrove fully supports HF Storage Buckets — S3-like mutable object storage backed by Xet.

**Four ways to use buckets:**

| Approach | When to Use |
|----------|-------------|
| `HuggingFaceBucketWriter` | Large datasets, staged Xet uploads, auto-create bucket |
| Direct fsspec `hf://buckets/...` | Simple read/write via `HfFileSystem` |
| `hf-mount` (FUSE/NFS) | Best read performance, zero code changes |
| HF Jobs volume mounts | Zero setup on HF infra |

**Bucket as logging dir:**
```python
executor = LocalPipelineExecutor(
    pipeline=[...],
    logging_dir="hf://buckets/myorg/bucket/logs/",
    ...
)
```

## Practical Guides

### Processing CommonCrawl Dump

Full pipeline from WARC files → filtered text → HF Buckets:

> 🧩 **Reusable template:** [`templates/commoncrawl-pipeline.py`](skill://hf-datatrove/templates/commoncrawl-pipeline.py) — a complete, configurable CLI entry point supporting both Local and Slurm executors. Run it directly, or copy and customize:
> ```bash
> python3 templates/commoncrawl-pipeline.py \
>     --input s3://mybucket/cc_dump/ \
>     --output hf://buckets/myorg/clean-text/ \
>     --tasks 500 --workers 50 --languages en fr
> ```

```python
from datatrove.pipeline.readers import WarcReader
from datatrove.pipeline.extractors import Trafilatura
from datatrove.pipeline.filters import LanguageFilter, URLFilter, QualityFilter
from datatrove.pipeline.writers import HuggingFaceBucketWriter

pipeline = [
    WarcReader("s3://mybucket/cc_dump/", glob_pattern="*/warc/*.warc.gz"),
    Trafilatura(),
    URLFilter(excluded_domains=["spam.com", "ads.com"]),
    LanguageFilter(["en", "fr", "de", "es"]),
    QualityFilter(min_words=50, max_words=100000),
    HuggingFaceBucketWriter(bucket="myorg/processed-cc", prefix="v1/clean/"),
]
```

### Reproducing FineWeb

See [`examples/fineweb.py`](https://github.com/huggingface/datatrove/blob/main/examples/fineweb.py) — the complete pipeline used to create the FineWeb dataset.

### Custom Filters

Simple function-based filter:
```python
from datatrove.data import DocumentsPipeline

def my_word_count_filter(data: DocumentsPipeline, rank: int = 0, world_size: int = 1):
    """Keep docs with >50 words."""
    for doc in data:
        if len(doc.text.split()) > 50:
            yield doc

pipeline = [..., my_word_count_filter, ...]
```

Full block-based filter:
```python
from datatrove.pipeline.base import PipelineStep
from datatrove.data import DocumentsPipeline

class MyCustomFilter(PipelineStep):
    def __init__(self, min_word_count: int = 50):
        super().__init__()
        self.min_word_count = min_word_count

    def run(self, data: DocumentsPipeline, rank: int = 0, world_size: int = 1) -> DocumentsPipeline:
        for doc in data:
            with self.track_time():
                if len(doc.text.split()) >= self.min_word_count:
                    self.stat_update("kept", 1)
                    yield doc
                else:
                    self.stat_update("filtered", 1)
```

## DataTrove vs Alternatives

| Feature | DataTrove | Data-Juicer | Apache Beam | custom Python scripts |
|---------|-----------|-------------|-------------|----------------------|
| **Scale** | Trillion-token scale | GB-tier | Any scale | Developer-scale |
| **Resumable** | ✅ Built-in (completion markers) | ❌ | ✅ (via runner) | ❌ |
| **Dedup built-in** | ✅ MinHash, ExactSubstr, Sentence | ❌ | ❌ | ❌ |
| **Slurm** | ✅ Native | ⚠️ Scripts | ❌ | ❌ |
| **HF Buckets** | ✅ Native writers | ❌ | ❌ | ❌ |
| **Learning curve** | Low | Medium | High | Depends |
| **Custom blocks** | ✅ Simple | ✅ | ✅ | — |
| **Stats** | ✅ Distributed | ✅ | ❌ | ❌ |
| **Synthetic data** | ✅ InferenceRunner | ❌ | ❌ | ❌ |

## Pitfalls

- **Tasks > files = wasted tasks:** Some tasks will have zero data. Usually no benefit to setting `tasks > len(files)`.
- **Don't change task count on restart:** Changing `tasks` after partial completion changes file-to-task distribution — previously completed tasks may now process different files, causing data loss or duplication.
- **Files not auto-split:** A single 100GB file is processed by ONE task — split large files into chunks for parallelism.
- **Pickling issues in custom functions:** Lambda/inline-defined functions may fail to pickle for multiprocessing. Move imports inside the function body or use module-level functions.
- **Python 3.10+ only:** The `uv.lock` file specifies 3.10+. Some extras may require 3.11+.
- **Install extras:** Base install is bare (`uv sync`). Add `--extra io`, `--extra processing`, `--extra all` etc. for specific capabilities.
- **Streaming vs downloaded HF datasets:** `HuggingFaceReader(streaming=True)` is recommended for large datasets. `streaming=False` downloads all data first.
- **Logging dir reuse across pipelines:** Different pipelines should NOT share `logging_dir` — completions/stats from the first will contaminate the second.
- **`hf://buckets/...` vs `hf://datasets/...`:** Buckets are for raw/intermediate data; datasets are for published, versioned, ready-to-share data. Use the right one.
- **Randomize start for S3:** Set `randomize_start_duration=30` or `randomize_start=True` (Slurm) when many tasks read from the same S3/HF bucket simultaneously.
- **SLURM array size limit:** Default MaxArraySize is 1001. Exceed this and DataTrove splits into multiple array jobs automatically.
- **Tokenized data can't be re-filtered:** Once tokenized, you can't apply text-level filters. Filter BEFORE tokenizing.
- **Inference requires GPU:** The `InferenceRunner` needs GPU-equipped nodes. Use Slurm with GPU partition or HF Jobs with GPU hardware tier.
- **No built-in PII removal:** DataTrove doesn't have a built-in PII redactor — add a custom block with `Presidio`/`spaCy` NER if needed.

## Key Resources

| Resource | URL |
|----------|-----|
| Getting Started template | [`templates/commoncrawl-pipeline.py`](skill://hf-datatrove/templates/commoncrawl-pipeline.py) — CLI-ready CommonCrawl processor |
| GitHub repo | https://github.com/huggingface/datatrove |
| PyPI | `pip install datatrove[all]` |
| Examples | https://github.com/huggingface/datatrove/tree/main/examples |
| FineWeb pipeline | [`examples/fineweb.py`](https://github.com/huggingface/datatrove/blob/main/examples/fineweb.py) |
| HF Hub docs | https://huggingface.co/docs/hub/en/datasets-libraries#datatrove |
| Paper | Penedo et al. 2024 — `@misc{penedo2024datatrove}` |
| HF Storage Buckets | https://huggingface.co/docs/hub/storage-buckets |
| Nanotron integration | https://github.com/huggingface/nanotron (uses datatrove for preprocessing) |

## Getting Started

```bash
# 1. Install
uv venv datatrove --python 3.11
source datatrove/bin/activate
uv pip install datatrove[all]

# 2. Quick test — read JSONL, filter, write
python3 -c "
from datatrove.pipeline.readers import JsonlReader
from datatrove.pipeline.filters import SamplerFilter
from datatrove.pipeline.writers import JsonlWriter
from datatrove.executor import LocalPipelineExecutor

executor = LocalPipelineExecutor(
    pipeline=[
        JsonlReader('https://huggingface.co/datasets/allenai/c4/raw/main/en/'),
        SamplerFilter(rate=0.01),  # keep 1% for testing
        JsonlWriter('/tmp/c4_sample/'),
    ],
    logging_dir='/tmp/c4_logs/',
    tasks=2,
    workers=2,
)
executor.run()
print('Done')
"

# 3. Check output
ls /tmp/c4_sample/
```

**Key workflow pattern for LLM training data:**

```
Raw Data (CommonCrawl, web dump, etc.)
    ↓
Extract text (Trafilatura)
    ↓
Filter (Language → Quality → URL → WordCount)
    ↓
Deduplicate (Minhash → ExactSubstr → Sentence)
    ↓
Stats + Analysis
    ↓
Tokenize (Tokenizer/Counter)
    ↓
Tokenized output → Nanotron / Megatron training
```
