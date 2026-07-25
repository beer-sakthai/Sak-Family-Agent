# HF Learnings — Hugging Face Datasets 5.0.0 New Features Deep Dive

## 2026-07-25: hf-datasets-5-release — Hugging Face Datasets 5.0.0 Complete Reference (Topic #353)

### Summary

Comprehensive deep dive into Hugging Face Datasets **v5.0.0** (released June 5, 2026) — a major version increment from 4.8.5. Version 5.0.0 introduces **agent trace parsing** (via the `teich` library for turning coding agent sessions into auditable SFT data), **multi-shard streaming shuffle** (dramatically better randomness in streaming mode), **batch-by-column** for robotics episodes, and **four new data formats** (Apache Iceberg, TsFile/IoTDB, 3D Mesh/MeshFolder, CoNLL/CoNLL-U). This version also carries critical bug fixes for Parquet streaming, Lance datasets, composed splits, and SQL export.

Key insight: Datasets 5.0.0 is a **capability expansion** release — it doesn't break existing APIs but adds entirely new data modalities (3D meshes, time-series IoT), new ingestion pipelines (Iceberg tables, agent traces), and a fundamentally better streaming shuffle that fixes the long-standing "cold start clustering" problem.

---

### 1. Agent Traces (via `teich` Library)

**What it is:** Native support for loading, parsing, and training on agent traces — the output of coding agents like Claude Code, Codex, Pi, and others — using the `teich` library (new optional dependency).

**The `teich` library** (PyPI: `teich`) is a standalone agent data infrastructure package that:
- Normalizes raw agent traces into OpenAI-style `messages` and `tools` format
- Preserves tool schemas, reasoning traces, metadata, and provenance
- Renders through any target tokenizer's chat template
- Records typed supervision spans before tokenization
- Applies response-only labels for TRL/Unsloth trainer tokenization
- Reports dropped, oversized, trimmed, malformed, and fully masked rows

**API:**

```python
# Load agent traces as a dataset (messages column auto-parsed)
from datasets import load_dataset
ds = load_dataset("lhoestq/agent-traces-example", split="train")
ds[0]["messages"]
# [{'role': 'user', 'content': 'Download a random dataset...'}, ...]

# Train directly with TRL
# trl sft --dataset-name lhoestq/agent-traces-example ...
```

**Discover agent traces datasets:** https://huggingface.co/datasets?format=format:agent-traces&sort=trending

**Dependencies:** `teich` is an optional dependency — install via `pip install datasets[teich]` or `pip install teich`.

---

### 2. Next-Level Streaming Shuffle (Multi-Shard Buffer)

**What changed:** The default streaming shuffle now pulls from **multiple input shards** simultaneously instead of a single shard, producing dramatically better randomness — especially in the "cold start" (first few thousand examples).

**Old behavior** (pre-5.0): Single-shard buffer → consecutive examples were clustered together, producing near-identical cold start and nominal regime sequences.

**New behavior** (5.0.0): Multi-shard buffer (`max_buffer_input_shards=10`) → sequences are randomly interspersed from the start.

**API:**

```python
ds = load_dataset(..., streaming=True)
ds = ds.shuffle(seed=42)

# Configure manually:
ds = ds.shuffle(seed=42, buffer_size=1000, max_buffer_input_shards=10)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `seed` | `None` | Random seed for reproducibility |
| `buffer_size` | `1000` | Number of examples in local shuffle buffer |
| `max_buffer_input_shards` | `10` | How many input shards to fetch from concurrently |

**Breaking change note:** The old single-shard shuffle can be restored with `max_buffer_input_shards=1`.

**Checkpointing still works:** `ds.state_dict()` and `ds.load_state_dict()` are fully compatible with the new shuffle mechanism.

**Performance:** Uses threads to fetch first examples in parallel from input shards — no cold-start penalty.

---

### 3. Batch by Column (Robotics / Episodic Data)

**What it is:** A new `by_column` parameter on `Dataset.batch()` that groups consecutive rows with the same column value into a single batch — purpose-built for robotics datasets where you need to group frames by episode.

**API:**

```python
from datasets import Dataset

ds = Dataset.from_dict({
    "episode": [0] * 10 + [1] * 10,
    "frame": list(range(10)) * 2
})

# Group by episode
batched = ds.batch(by_column="episode")
for x in batched:
    print(x)
# {'episode': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'frame': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}
# {'episode': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 'frame': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}
```

Also works with `IterableDataset` via `.to_iterable_dataset().batch(by_column=...)`.

---

### 4. New Supported Data Formats

#### 4.1 Apache Iceberg

**What it is:** Native support for loading datasets from **Apache Iceberg** tables — an open table format for petabyte-scale analytic datasets.

```python
ds = load_dataset("iceberg://catalog/namespace/table")
```

Requires optional Iceberg dependencies. Enables direct ingestion of data lakehouse tables without intermediate Parquet/CSV export.

#### 4.2 TsFile (Apache IoTDB)

**What it is:** Support for **TsFile** — the columnar storage format of Apache IoTDB, designed for time-series IoT data. The builder produces per-device wide format.

```python
ds = load_dataset("tsfile://path/to/data.tsfile")
# Or use the packaged builder
```

Key use case: Industrial IoT sensor data, device telemetry, time-series analytics training.

#### 4.3 3D Mesh Support + MeshFolder Builder

**What it is:** Native 3D mesh dataset loading with a new `MeshFolder` builder that organizes mesh files (`.obj`, `.stl`, `.ply`, `.glb`, etc.) into structured datasets.

```python
from datasets import load_dataset

# Load a folder of mesh files
ds = load_dataset("mesh_folder", data_dir="/path/to/meshes")
```

Features:
- Multi-format support (OBJ, STL, PLY, GLB, GLTF)
- `embed_external_files=True` for self-contained dataset packaging
- Integration with 3D ML workflows (mesh classification, generation, reconstruction)

#### 4.4 CoNLL / CoNLL-U Format

**What it is:** Native loader for the **CoNLL** (Conference on Natural Language Learning) tab-separated format widely used in NER, POS tagging, and dependency parsing.

```python
ds = load_dataset("conllu", data_files="myfile.conllu")
```

Supports:
- CoNLL-2003 / CoNLL-2000 formats (token-level NER/chunking)
- CoNLL-U format (universal dependencies with morphological features)
- Standard column mappings (WORD, POS, CHUNK, NER tags)

---

### 5. Important Bug Fixes & Improvements

| Fix | PR | Impact |
|-----|----|--------|
| Parquet streaming hang at end of script | #8176 | Fixed infinite loop in streaming Parquet reader |
| Parquet reshard fix | #8193 | Correct shard boundaries after resharding |
| Parquet `columns` arg fix | #8210 | Column selection now works reliably |
| Lance streaming `storage_options` | #8166 | Lance dataset streaming now accepts storage config |
| Composed splits in streaming | #8220 | `split="train+test"` now works with streaming iterable datasets |
| `to_sql` with `num_proc` | #7791 | Multi-process SQL export |
| `map` progress bar fix | #8170 | Progress bar no longer exceeds total when `load_from_cache_file=False` |
| `ClassLabel` unknown labels doc | #7645 | Corrected documentation for unknown label handling |
| `Json()` null handling | #8231 | `None` stays as `None` instead of `"null"` string |
| Iterable skip over full Arrow blocks | #8236 | Fixed edge case in skip logic |
| FSSpec 2026.4.0 support | #8175 | Compatibility with latest fsspec |
| `library_name/version` in push paths | #8161 | Metadata propagation for dataset push/delete |

---

### 6. Migration Guide (4.8.x → 5.0.0)

**Likely breaking — verify in your codebase:**

| Change | Migration Action |
|--------|-----------------|
| Streaming shuffle uses multi-shard by default | If you relied on single-shard ordering, add `max_buffer_input_shards=1` to `.shuffle()` |
| `Json()` column `None` handling | Previously serialized `None` as `"null"` string; now kept as `None` — check downstream null handling |
| `teich` optional dep for agent traces | Install `pip install datasets[teich]` or `pip install teich` |
| New format dependencies | Iceberg/TsFile/3D mesh may need optional extras: `pip install datasets[iceberg]`, etc. |

---

### Skill Created

`hf-datasets-5-release/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with complete documentation.

### Sources

- https://github.com/huggingface/datasets/releases/tag/5.0.0 — Official release notes
- https://pypi.org/project/teich/ — Teich library (agent trace parsing)
- https://huggingface.co/docs/datasets/main/en/ — Datasets documentation main branch
- https://iceberg.apache.org/ — Apache Iceberg table format
- https://iotdb.apache.org/ — Apache IoTDB + TsFile format
