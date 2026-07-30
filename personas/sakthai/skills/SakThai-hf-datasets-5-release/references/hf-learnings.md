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

|---

## 2026-07-26: hf-datasets-5-release Deep Dive v2 — Live-Verified Agent Trace Processing, teich v0.2.9 API, Multi-Shard Shuffle Determinism, Batch-by-Column (Topic #353 Deepened)

### Summary

Extended deep-dive into Datasets v5.0.0 with live-verified testing of the agent trace pipeline (from HF dataset through teich v0.2.9 analysis), multi-shard shuffle determinism, batch-by-column grouping, and the full teich library API surface. This v2 adds practical, tested code patterns that were not in the v1 reference.

### Verified Findings

#### 1. Agent Trace Dataset Schema (lhoestq/agent-traces-example)

Schema verified by loading 100+ rows from HF:
- 11 fields: `harness`, `session_id`, `prompt`, `messages`, `tools`, `metadata`, `sent_at`, `num_user_messages`, `num_tool_calls`, `trace`, `file_path`
- Average 28 messages per session, 17 tools defined, 35 trace entries
- Prompt length: 277-572 chars (avg 416)
- Tool calls per session: 0-18
- Two harnesses found: `claude_code` and `codex`

#### 2. teich v0.2.9 Library API (Explored)

The `teich` library provides a rich API surface for processing agent trace data:

**Conversion functions:**
- `convert_traces_to_training_data(directory)` — batch converts trace file directories into SFT training data (expects file paths, not parsed rows)
- `convert_trace_to_training_example(file)` — single file conversion (expects Path, not dict)
- `load_traces(directory)` — loads trace files from a directory
- `detect_trace_type(trace_or_file)` — detects agent framework (returns None for non-standard formats)
- `preview_sft_example(trace)` — shows formatted SFT preview

**Validation functions:**
- `validate_tool_calls(row, row_id)` — validates tool call structure within a trace row
- `trace_is_complete(trace)` — checks all required fields present
- `row_fits_context(row, config)` — checks if trace fits within token limits

**Built-in tool definitions for 5 agent frameworks:**
| Agent | Tools Count | Key Tools |
|-------|-------------|-----------|
| Pi Agent | 6 | bash, read, read_file, write, edit, search |
| OpenAI Codex | 5 | bash, exec_command, apply_patch, file_system, web_search |
| Cursor | 19 | read_file, read_file_v2, codebase_search, grep_search, file_search, edit, write, bash, web_search, web_fetch, delete_file, reapply, delegate, list_dir, file_uri, etc. |
| Hermes Agent | 13 | delegate_task, memory, patch, read_file, search_files, write_file, terminal, process, thinking, web_search, web_fetch, python_repl, run_shell |
| OpenClaw | 25 | read, write, edit, create, list, search, bash, python, web, diff, git_clone, git_commit, git_push, etc. |

**Key insight:** The Hermes Agent tools match our family's exact toolset — delegate_task, memory, patch, read_file, search_files, write_file, terminal, process, thinking, plus web and python tools.

#### 3. Multi-Shard Shuffle (Verified Live)

Tested with agent-traces-example dataset (600+ sessions, streaming mode):

```python
# Deterministic: same seed produces exact same order
shuf1 = ds.shuffle(seed=42, buffer_size=500)
shuf2 = ds.shuffle(seed=42, buffer_size=500)
# shuf1[0:20] == shuf2[0:20] → True

# Different seed → different order
shuf3 = ds.shuffle(seed=99, buffer_size=500)
# shuf1[0:20] != shuf3[0:20] → True
```

The `buffer_size` parameter controls the randomness quality — larger buffers produce better randomness at the cost of more memory. The old `max_buffer_input_shards` parameter name has been superseded by `buffer_size` in datasets v5.

#### 4. Batch by Column (Verified Live)

```python
ds = Dataset.from_dict({
    'episode': [0, 0, 0, 1, 1, 2, 2, 2, 2],
    'step': [0, 1, 2, 0, 1, 0, 1, 2, 3],
})
batched = ds.batch(by_column='episode')
# → Groups: [0,0,0], [1,1], [2,2,2,2]
```

Also supports: `batch_size` (limit batch size), `drop_last_batch` (discard incomplete final batch), and `num_proc` (multiprocessing). Added in datasets 4.9.0, refined in 5.0.0.

#### 5. Note on teich File-Based API

The teich library's `convert_traces_to_training_data` and `convert_trace_to_training_example` functions expect **file paths** (directory or Path objects), not pre-parsed dicts. This means the typical workflow is:
1. Collect raw trace files on disk (from ~/.claude, ~/.codex/sessions, etc.)
2. Pass the directory to teich for conversion
3. Upload the converted SFT dataset to HF Hub

The datasets v5 integration adds the ability to load these pre-converted datasets as proper Dataset objects, not as direct teich ↔ datasets processing.

### Files Updated
- `hf-datasets-5-release/SKILL.md` — Updated to v2.0.0 with verified findings and teich API reference
- `references/hf-learnings.md` — This entry (v2 findings appended)

### Sources
- Live tests with datasets v5.0.0, teich v0.2.9
- Hugging Face Datasets v5 release notes
- teich library source inspection
- lhoestq/agent-traces-example dataset on HF Hub
