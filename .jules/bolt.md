# Bolt's Journal

## 2025-05-15 - [SQL-based Tag Counting Optimization]

**Learning:** Using SQLite's `json_each` for aggregating data stored in JSON columns is significantly faster than fetching all rows and decoding them in Python. In this codebase, it provided a ~2.3x-2.6x speedup for the `MemoryStore.stats()` method.

**Action:** Prefer SQL-level JSON operations (like `json_each`, `json_extract`) over Python-level processing when aggregating or filtering on JSON columns in SQLite.

## 2025-05-16 - [SQL-based Dashboard Aggregation]

**Learning:** For dashboard views that involve time-series binning and KPI deltas, performing aggregation in SQL via `SUM(CASE...)` and `CAST((ts - start)/86400 AS INTEGER)` is significantly more efficient than fetching thousands of objects and processing them in Python. It avoids the overhead of object instantiation and JSON parsing for every row.

**Action:** Use SQL-level aggregation for dashboard metrics and limit row fetching only to the subset of records actually displayed in the UI.
