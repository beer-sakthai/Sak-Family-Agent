---
name: SakThai-hf-data-studio-sql-console
description: "HuggingFace Data Studio SQL console for dataset queries"
---

# SakThai HF Data Studio SQL Console Skill

## Purpose
Expert-level knowledge of Hugging Face's Data Studio SQL Console — the in-browser DuckDB SQL query engine for analyzing Hub datasets. Covers the DuckDB WASM architecture, SQL Console CRUD embeds API, `hf://` protocol with DuckDB CLI, `hf datasets sql` wrapper, natural language to SQL, leakage detection, histogram analysis, and Storage Buckets integration.

## Key Capabilities
1. Run DuckDB SQL queries directly on Hub datasets in the browser at zero cost
2. Create shareable query links and saved embeds with CRUD API
3. Use DuckDB v0.10.3+ `hf://` protocol for terminal-based dataset querying
4. Detect data leakage between train/test splits
5. Profile column distributions with DuckDB's `histogram()` function
6. Execute `hf datasets sql` CLI for scriptable dataset analysis
7. Query Storage Bucket data via DuckDB Python + HfFileSystem

## Related Skills
- mlops/hf-datasets-server-rest-api
- mlops/hf-datasets-parquet-column-selection
- mlops/hf-hub-storage-buckets-deep-dive
