## 2025-05-15 - [SQL-based Tag Counting Optimization]
**Learning:** Using SQLite's `json_each` for aggregating data stored in JSON columns is significantly faster than fetching all rows and decoding them in Python. In this codebase, it provided a ~2.3x-2.6x speedup for the `MemoryStore.stats()` method.
**Action:** Prefer SQL-level JSON operations (like `json_each`, `json_extract`) over Python-level processing when aggregating or filtering on JSON columns in SQLite.
