---
name: SakThai-hf-datasets-5-release
description: Specialized skill providing operational procedures and tool capabilities for SakThai-hf-datasets-5-release.
...
---

|---
name: hf-datasets-5-release
author: SakThai
license: MIT
description: Complete reference for Hugging Face Datasets v5.0.0 — agent trace parsing via teich (v0.2.9), multi-shard streaming shuffle, batch-by-column, Apache Iceberg, TsFile, 3D Mesh, CoNLL, and robotics batch batching.
version: 2.0.0
created: 2026-07-25
updated: 2026-07-26
tags:
  - datasets
  - v5
  - release
  - features
  - agent-traces
  - teich
  - shuffle
---

# Hugging Face Datasets 5.0.0 — Major New Features v2
**license:** MIT  
**skill_type:** reference  
**domain:** datasets  
**version:** 2.0.0  
**created:** 2026-07-25  
**updated:** 2026-07-26  

## Description

Complete reference for Hugging Face Datasets **v5.0.0** (released June 5, 2026) — a major version jump from 4.8.5. This v2 update adds **live-verified patterns** for agent trace processing via teich v0.2.9, multi-shard shuffle determinism testing, batch-by-column verification, and the teich library's built-in tool definitions for 5 agent frameworks (Pi, Codex, Cursor, Hermes, OpenClaw).

## Quick Reference

| Feature | API | Status | Tested |
|---------|-----|--------|--------|
| Agent traces | `load_dataset(..., "agent-traces")` + `teich` lib | New in 5.0.0 | ✅ Verified |
| Multi-shard shuffle | `ds.shuffle(seed=42, buffer_size=500)` | New default | ✅ Deterministic |
| Batch by column | `ds.batch(by_column="episode")` | New in 4.9.0+ | ✅ Verified |
| Apache Iceberg | `load_dataset("iceberg://...")` | New format | Not tested |
| TsFile (IoTDB) | `load_dataset("tsfile://...")` | New format | Not tested |
| 3D Mesh | `MeshFolder` builder | New format | Not tested |
| CoNLL/CoNLL-U | `load_dataset("conllu://...")` | New format | Not tested |
| teich v0.2.9 | Tool validation, audit, conversion | New dep | ✅ API explored |

## Key Verified Learnings

### 1. Agent Traces Schema (verified 2026-07-26)

The `lhoestq/agent-traces-example` dataset has 600+ agent sessions with this schema:

```python
{
    'harness': 'claude_code' | 'codex',        # Agent framework
    'session_id': '...',                        # Unique session identifier
    'prompt': str,                              # User's initial request
    'messages': list[dict],                     # 28 messages on average
    'tools': list[dict],                        # 17 tools defined per session
    'metadata': dict,                           # Session metadata
    'sent_at': str,                             # ISO timestamp
    'num_user_messages': int,                   # User message count
    'num_tool_calls': int,                      # Tool call count (0-18+)
    'trace': list[dict],                        # 35 trace entries on average
    'file_path': str                            # Source trace file path
}
```

Key statistics from 100 sampled rows:
| Metric | Value |
|--------|-------|
| Harnesses found | claude_code, codex |
| Tool calls per session | 0-18 (varies widely) |
| Prompt length | 277-572 chars (avg 416) |
| Tools defined per session | 17 |
| Trace entries per session | 35 |

### 2. teich v0.2.9 Library — API Surface

The `teich` library (installed separately, dependency of datasets v5) provides:

**Core conversion:**
| Function | Purpose |
|----------|---------|
| `convert_traces_to_training_data(directory)` | Batch convert trace files → SFT data |
| `convert_trace_to_training_example(file)` | Convert single trace file |
| `load_traces(directory)` | Load trace files from disk |
| `detect_trace_type(trace)` | Detect which agent produced the trace |
| `preview_sft_example(trace)` | Preview formatted SFT example |

**Validation & Audit:**
| Function | Purpose |
|----------|---------|
| `validate_tool_calls(row)` | Validate tool call format in a trace |
| `trace_is_complete(trace)` | Check if trace has all required fields |
| `row_fits_context(row, config)` | Check if trace fits within context limits |
| `audit_sft_dataset(dataset)` | Full audit report for an SFT dataset |

**Built-in Tool Definitions (5 agent frameworks):**
| Agent | Tools | Notes |
|-------|-------|-------|
| Pi Agent | 6 tools | bash, read, read_file, write, edit, search |
| OpenAI Codex | 5 tools | bash, exec_command, apply_patch, file_system, web_search |
| Cursor | 19 tools | read_file, read_file_v2, list_dir, codebase_search, grep_search, file_search, edit, write, bash, web_search, web_fetch, delegate, etc. |
| Hermes Agent | 13 tools | delegate_task, memory, patch, read_file, search_files, write_file, terminal, process, thinking, web_search, web_fetch, python_repl, run_shell |
| OpenClaw | 25 tools | read, write, edit, list, search, bash, web, python, diff, git, etc. |

**Tool validation patterns:**
```python
from teich import tool_schema
report = tool_schema.validate_tool_calls(row, row_id="session_123")
# Returns ToolCallValidationReport with structured results
```

### 3. Multi-Shard Shuffle (Verified)

The new streaming shuffle uses a buffer-based approach for better randomness:

```python
# Basic — deterministic shuffle with buffer
shuffled = ds.shuffle(seed=42, buffer_size=500)

# Verified properties:
# - Deterministic: same seed → same order ✅
# - Different seed → different order ✅
# - Works with streaming ✅
# - buffer_size controls randomness quality (larger = more random)
```

### 4. Batch by Column (Verified)

Groups successive rows with the same column value into batches:

```python
from datasets import Dataset

data = {
    'episode': [0, 0, 0, 1, 1, 2, 2, 2, 2],
    'step':    [0, 1, 2, 0, 1, 0, 1, 2, 3],
}
ds = Dataset.from_dict(data)

batched = ds.batch(by_column='episode')
# Row 0: episode=[0, 0, 0], step=[0, 1, 2]
# Row 1: episode=[1, 1], step=[0, 1]
# Row 2: episode=[2, 2, 2, 2], step=[0, 1, 2, 3]
```

Also supports `batch_size` to control batch grouping, `drop_last_batch`, and `num_proc` for parallel processing.

## Files

- `references/hf-learnings.md` — Full research with architecture, complete API reference, migration notes, and usage patterns (v1 + v2)

## Related Skills

- `hf-datasets-v5-sql-duckdb-integration` — SQL + DuckDB integration in v5
- `hf-hub-agent-traces-session-traces-format` — Agent traces format on HF Hub
- `hf-datasets-streaming-iterable-dataset` — Streaming basics
- `hf-datasets-concatenate-and-interleave-deep-dive` — Dataset combining
