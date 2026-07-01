# Bolt's Performance Journal

## 2025-05-15 - [SQL-based Tag Counting Optimization]
**Learning:** Using SQLite's `json_each` for aggregating data stored in JSON columns is significantly faster than fetching all rows and decoding them in Python. In this codebase, it provided a ~2.3x-2.6x speedup for the `MemoryStore.stats()` method.
**Action:** Prefer SQL-level JSON operations (like `json_each`, `json_extract`) over Python-level processing when aggregating or filtering on JSON columns in SQLite.

## 2026-07-01 - [Batch Fact Insertion Optimization]
**Learning:** SQLite's default behavior is to wrap every individual INSERT in its own transaction (and commit), which involves significant fsync overhead. For bulk fact ingestion (e.g., from files or session consolidation), batching insertions into a single transaction using a new `add_facts` method provides a massive performance boost (~22x speedup).
**Action:** Use `MemoryStore.add_facts` for any bulk ingestion instead of looping over `add_fact`.
