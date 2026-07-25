---
author: SakThai
license: MIT
---

# HF Hub Fork & Sync — Server-Side Repo Duplication & File Copy

## Overview
Server-side repo duplication (`duplicate_repo`) and file copying (`copy_files`) enable full-history, zero-download copies on the Hub. These operations preserve git history, LFS objects, and (optionally) Space configuration — all without a local round-trip.

**Key capabilities:**
- `duplicate_repo` — full server-side repo clone (model, dataset, or Space)
- `duplicate_space` — deprecated; use `duplicate_repo` with `repo_type="space"`
- `copy_files` — copy individual files or folders between repos/buckets via `hf://` URIs
- REST endpoint: `POST /api/{models|datasets|spaces}/{from_id}/duplicate`

## Quick Reference
| Operation | Function | REST Endpoint |
|-----------|----------|---------------|
| Duplicate repo | `duplicate_repo(from_id, to_id, ...)` | `POST /api/{type}/{from_id}/duplicate` |
| Duplicate Space (legacy) | `duplicate_space(from_id, to_id, ...)` | same endpoint |
| Copy files | `copy_files(source, destination, ...)` | `CommitOperationCopy` internally |

For detailed API reference, usage patterns, error handling, and Space-specific options, see `references/hf-learnings.md`.
