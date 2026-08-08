---
name: SakThai-hf-stack-v3
description: "The Stack v3 (HuggingFaceCode/stack-v3-train + stack-v3-full) — the largest open source-code dataset. Pipeline, schema, access patterns, and curation details for using it in code-LLM pre-training."
---

# The Stack v3 — Largest Open Code Dataset

## What it is

The Stack v3 = Hugging Face's biggest, most current open dataset of source code, crawled directly from GitHub, purpose-built for pre-training code LLMs with **full-repository context**. Successor to The Stack v2 (bigcode/the-stack-v2). Released 2026-07-29 by HuggingFaceCode. License: **ODC-By 1.0** (plus original repo licenses still apply to the code itself).

Key differences vs v2:
1. **File contents inline** — decoded UTF-8 embedded in the dataset (self-contained, no join step).
2. **Crawl cutoff 2025-08-07** — ~2 extra years of code vs v2.
3. **Language-agnostic near-dedup** with Jaccard verification (v2 was per-language, unverified).

## Scale

| | v1 | v2 | v3 |
|---|---|---|---|
| cutoff | 2022 | 2023 | 2025-08-07 |
| full | 6.4 TB | 67.5 TB | 113.7 TB |
| dedup | 2.9 TB | 32.1 TB | 99.3 TB |
| train | ~200B tokens | 2.0 TB / ~550B tok | **15.9 TB / ~4.9T tokens** |
| languages | 358 | 618 | 713 (train) / 770 (full) |

- train: 173M repos, 713 languages, 15.9 TB
- full: 224M repos, 43.9B files crawled, 113.7 TB (incl. stubs for binary/oversized/undetected)
- Snapshot = single tarball of default branch at HEAD commit; no git history. Forks <5 stars skipped. Files >5 MB / binary / symlinks dropped. Repos capped at 1M files.

## Two releases

| Repo | What | Best for |
|---|---|---|
| `HuggingFaceCode/stack-v3-train` | Near-dedup + quality-filtered, grouped by repo, contents inline | Pre-training out of the box |
| `HuggingFaceCode/stack-v3-full` | **HF Storage Bucket** (not a dataset repo), `metadata/` + `contents/` parts joined on `content_id` | Research, custom filtering, own dedup (has `dedup_cluster` IDs + stubs) |

## Schema (train)

Row = repository: `repo_path`, `repo_id`, `commit_id`, `github_metadata` (branch, commit_count, repo_created_at, is_fork, is_org_owned, forked_from, stars, forks, issues, pull_requests), `num_files`, `files[]`:
- `content_id` — SHA-1 of content
- `content` — inline UTF-8, PII-redacted
- `size_bytes`, `file_path`, `file_timestamp`
- `language` — go-enry (GitHub Linguist port)
- `is_vendor` — vendored/third-party flag
- `license_type` — `permissive` | `no_license` (non_permissive excluded entirely)
- `detected_licenses` — SPDX ids from ScanCode

## Pipeline (Spark, in order)

1. UTF-8 decode (cchardet fallback) → go-enry language/vendor → SHA-1 content addressing
2. **License:** ScanCode on license files → propagate through directory tree (LICENSE at root covers subtree) → classify permissive (Blue Oak Council + ScanCode permissive/PD) / no_license / non_permissive → **non_permissive excluded**
3. **Near-dedup:** MinHash (256 perms, 5-grams, min 5 tokens) + LSH, Jaccard ≥ 0.7, connected components, **language-agnostic + verified**; representative chosen by stars → forks → permissive → earliest created
4. **Quality heuristics** (StarCoder2-style): <25% alphabetic drop; avg line >100 / max line >1000 drop (data/markup exempt); >100K lines drop; config formats capped 512 lines; base64/hex/LFS/auto-gen markers drop; HTML visible-text ≥100 chars & ≥20%; blocklist; byte budgets for XML/HTML/JSON/JS; >1.5 GB repos downsampled
5. **PII:** bigcode/starpii → placeholders `<EMAIL>`, `<KEY>`, `<NAME>`, `<PASSWORD>`, synthetic private IPs
6. **Notebooks:** outputs/images/volatile metadata stripped, kept as structured JSON (full keeps raw)
7. **Grouping** by repository

## Access patterns

```python
from datasets import load_dataset
ds = load_dataset("HuggingFaceCode/stack-v3-train", split="train", streaming=True)
for repo in ds:
    py = [f for f in repo["files"] if f["language"] == "Python"]
```

- No per-language configs — filter in-stream
- DuckDB/Polars direct over Parquet: `hf://datasets/HuggingFaceCode/stack-v3-train/data/*.parquet` via `HfFileSystem`
- Per-language stats: `stats/train/stats_by_language.json`, `stats/full/stats_by_language.json`
- Opt-out: "Am I in The Stack?" Space + bigcode-project/opt-out-v2; applied before each patch release

## Pitfalls

| Pitfall | Mitigation |
|---|---|
| 15.9 TB is huge | Use `streaming=True` for tests; cache_dir + num_proc for real loads |
| `stack-v3-full` is a Storage Bucket, not dataset repo | Use bucket access patterns (hf://... / HfFileSystem), not load_dataset |
| Language mix skewed | Widely used langs (C, JS, Python) dominate; niche langs thin |
| May contain malicious code | Normal for GitHub crawls; scan/curate for production use |
| License attribution imperfect | ScanCode + GitHub metadata accuracy; provenance fields provided per file |

## References

- Card: https://huggingface.co/datasets/HuggingFaceCode/stack-v3-train
- Full (bucket): https://huggingface.co/buckets/HuggingFaceCode/stack-v3-full
- arXiv: lozhkov2026stack-v3 (The Stack v3: The Largest Open Code Dataset); methodology from StarCoder2/The Stack v2 (arXiv:2402.19173)
- Related: sakthai-hf-cosmopedia (synthetic), SakThai-hf-fineweb-dataset-processing (web text)
