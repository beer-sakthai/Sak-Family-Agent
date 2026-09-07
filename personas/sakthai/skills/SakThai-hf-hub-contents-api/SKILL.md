---
name: SakThai-hf-hub-contents-api
version: 1.0.0
description: HuggingFace Hub Contents API endpoint details and usage patterns
author: SakThai
license: MIT
created: 2026-07-24
category: mlops/huggingface-hub
---

# HF Hub Contents API

## Description
Deep knowledge of the Hugging Face Hub's Repository Contents API — listing, inspecting, and navigating repo file trees, getting path metadata with security scan results and last-commit info, enumerating branches/tags/refs, and querying commit history. Covers `list_repo_tree`, `get_paths_info`, `list_repo_files`, `list_repo_refs`, `list_repo_commits`, and the underlying dataclasses (`RepoFile`, `RepoFolder`, `GitRefs`, `GitRefInfo`, `GitCommitInfo`).

## When to Use
- Need to list all files in a repo without cloning it
- Need detailed metadata about specific files (size, LFS info, security scan results, last commit)
- Need to enumerate branches, tags, and pull request refs
- Need to inspect commit history for a given revision
- Need to navigate repo directory trees programmatically

## Key APIs
| Method | Use Case |
|--------|----------|
| `list_repo_tree()` | Navigate repo file tree (folder listing) |
| `get_paths_info()` | Get metadata for specific paths |
| `list_repo_files()` | Flat list of all file paths |
| `list_repo_refs()` | List branches, tags, PR refs |
| `list_repo_commits()` | List commit history |
| `create_branch()` | Create a new branch from a revision |
| `delete_branch()` | Delete a branch |
| `super_squash_history()` | Squash entire git history |

## Core Dataclasses
- `RepoFile` — file entry (path, size, blob_id, lfs, security, last_commit)
- `RepoFolder` — folder entry (path, tree_id, last_commit)
- `GitRefs` — container (branches, converts, tags, pull_requests)
- `GitRefInfo` — single ref (name, ref, target_commit)
- `GitCommitInfo` — commit (commit_id, authors, created_at, title, message)
- `LastCommitInfo` — last commit for a file/folder (oid, title, date)
- `BlobLfsInfo` — LFS metadata (size, sha256, pointer_size)
- `BlobSecurityInfo` — security scan (safe, status, av_scan, pickle_import_scan)

## Reference
See `references/hf-learnings.md` for the complete deep-dive.
