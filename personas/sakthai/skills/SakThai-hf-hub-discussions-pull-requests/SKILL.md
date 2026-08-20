---
name: SakThai-hf-hub-discussions-pull-requests
author: SakThai
license: MIT
description: Complete reference for the Hugging Face Hub Discussions & Pull Requests API — creating, managing, merging, and interacting with discussions and pull requests on the Hub programmatically via huggingface_hub Python SDK.
version: 1.0.0
tags: [huggingface, hub, discussions, pull-requests, pr, collaboration, api, community]
category: hf-hub
trigger: >
  When programmatically managing repository discussions or pull requests,
  when automating PR merges or change tracking across HF repos,
  when building collaborative workflows on the Hub.
---

# HF Hub Discussions & Pull Requests API

Complete reference for interacting with Hugging Face Hub discussions and pull requests programmatically through the `huggingface_hub` Python library (v1.25.1).

## Overview

The Hugging Face Hub supports two types of community interactions on repositories:
- **Discussions**: Free-form conversations, feature requests, or questions (no code changes)
- **Pull Requests**: Proposed changes to repository files that can be reviewed, discussed, and merged

Both are identified by a numeric ID scoped to the repository. PRs are a subtype of discussion with an associated diff and merge capability.

## Core API Methods

All methods are on `HfApi` (or directly importable as module-level functions).

### Listing Discussions & PRs

```python
from huggingface_hub import HfApi
api = HfApi()

discussions = api.get_repo_discussions(
    repo_id="username/repo-name",
    repo_type="model",  # "model" (default), "dataset", "space"
)
for discussion in discussions:
    print(f"#{discussion.num}: {discussion.title} ({discussion.status})")
    print(f"  Type: {'PR' if discussion.is_pull_request else 'Discussion'}")
```

### Getting Discussion/PR Details

```python
discussion = api.get_discussion_details(
    repo_id="username/repo-name",
    discussion_num=42,
    repo_type="dataset",
)
if discussion.is_pull_request:
    print(f"Merged: {discussion.merged}")
    print(f"Merge commit: {discussion.merge_commit_oid}")
    print(f"Target branch: {discussion.target_branch}")
```

### Creating a Discussion or PR

```python
# Discussion
api.create_discussion(repo_id="u/r", title="Hello", description="Body")

# Pull Request
api.create_discussion(repo_id="u/r", title="Fix", pull_request=True)
```

### Comments, Rename, Status, Merge

```python
api.comment_discussion(repo_id="u/r", discussion_num=42, comment="Nice!")
api.edit_discussion_comment(repo_id="u/r", discussion_num=42, comment_id=cid, new_comment="Updated")
api.delete_discussion_comment(repo_id="u/r", discussion_num=42, comment_id=cid)
api.rename_discussion(repo_id="u/r", discussion_num=42, new_title="Better title")
api.change_discussion_status(repo_id="u/r", discussion_num=42, new_status="closed")
api.merge_pull_request(repo_id="u/r", pull_request_num=42)
```

## Data Models

### Discussion
- `num`, `title`, `status` (open/closed), `is_pull_request`, `author`, `created_at`
- PR-only: `target_branch`, `merge_commit_oid`, `merged`, `conflicting`

### DiscussionEvent
- `id`, `type` (comment/status-change/title-change), `author`, `content`, `edited`, `hidden`, `parent_id`

## PR Branches

PRs get a `refs/pr/<num>` branch. Push commits to it:

```python
api.upload_file(
    path_or_fileobj=b"content",
    path_in_repo="file.txt",
    repo_id="u/r",
    revision=f"refs/pr/{pr.num}",
)
```

## REST API Endpoints

```
GET    /api/models/{id}/discussions/{num}
POST   .../comment        PATCH/PATCH .../comment/{cid}
PUT    .../status         PUT .../title
POST   .../discussions    POST .../merge
```

## Practical Patterns

### Automated Changelog PR
```python
pr = api.create_discussion(repo_id="u/r", title="Update", pull_request=True)
for path, content in updates.items():
    api.upload_file(path_or_fileobj=content, path_in_repo=path,
                    repo_id="u/r", revision=f"refs/pr/{pr.num}")
```

### List Open PRs
```python
open_prs = [d for d in api.get_repo_discussions("u/r")
            if d.is_pull_request and d.status == "open"]
```

## Best Practices
- Use descriptive titles
- Thread replies with `parent_id`
- Close stale discussions
- Push commits to PR branches before merge
- Check `discussion.conflicting` before merging
- Always specify `repo_type` (model/dataset/space)

## Pitfalls
- Empty PRs cannot be merged
- Missing `repo_type` causes 404s for non-model repos
- Aggressive polling triggers rate limits
- No force-push via HTTP API (use Git CLI)

## References
- [PRs & Discussions Docs](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions)
- [Community Guide](https://huggingface.co/docs/huggingface_hub/en/guides/community)
- [API Reference](https://huggingface.co/docs/huggingface_hub/v1.25.1/en/reference/discussions)
