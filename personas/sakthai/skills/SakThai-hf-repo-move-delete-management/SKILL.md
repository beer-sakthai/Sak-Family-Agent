---
name: SakThai-hf-repo-move-delete-management
description: ">   Complete reference for Hugging Face Hub repository lifecycle management —   renaming, transferring ownership, deleting, duplicating, checking existence,   and updating visibility/settings of models, datasets, and Spaces via the   huggingface_hub "
---

# HF Hub Repo Move, Delete & Lifecycle Management

## Overview

The Hugging Face Hub provides a comprehensive API for managing the full lifecycle of repositories — from creation through renaming, ownership transfer, visibility changes, and deletion. This reference covers the complete surface.

### Key Methods in `huggingface_hub.HfApi`

| Method | Purpose | Irreversible? |
|--------|---------|--------------|
| `move_repo()` | Rename or transfer a repo between namespaces | Yes (old URL redirects) |
| `delete_repo()` | Permanently delete a repository | Yes |
| `duplicate_repo()` | Server-side copy preserving git + LFS history | No |
| `repo_exists()` | Check if a repository exists | — |
| `update_repo_settings()` | Change visibility (public/private) and gating | No |
| `create_repo()` | Create a new repository | No |
| `permanently_delete_lfs_files()` | Remove LFS files and rewrite history | Yes |

---

## 1. `move_repo()` — Rename & Transfer Ownership

```python
from huggingface_hub import HfApi

api = HfApi()
api.move_repo(
    from_id="source-namespace/repo-name",
    to_id="target-namespace/repo-name",
    repo_type="model",        # "model" (default), "dataset", or "space"
    token="hf_...",           # optional; defaults to saved token
)
```

### Parameters

| Param | Type | Description |
|-------|------|-------------|
| `from_id` | `str` | Current repo ID: `namespace/repo-name` |
| `to_id` | `str` | Desired repo ID: `namespace/repo-name` |
| `repo_type` | `str \| None` | `"model"`, `"dataset"`, `"space"`, or `None` (defaults to model) |
| `token` | `str \| bool \| None` | HF access token; defaults to locally saved token |

### Raises

- `ValueError` — if `from_id` or `to_id` doesn't contain exactly one `/`
- `RepositoryNotFoundError` — if the source repo doesn't exist
- `HfHubHTTPError` — for permission or validation failures

### REST Endpoint

```
POST https://huggingface.co/api/repos/move
```

Payload:
```json
{
  "fromRepo": "source-namespace/repo-name",
  "toRepo": "target-namespace/repo-name",
  "type": "model"
}
```

### ✅ Allowed Move Operations

| From → To | Requirements |
|-----------|-------------|
| User A → User A (rename only) | Own the repo |
| Org → Org (rename only) | "write" or "admin" in the org |
| User → Org | Member of org with ≥ "contributor" rights |
| Org → Yourself | "admin" rights in the org |
| Org A → Org B | "admin" in source org AND ≥ "contributor" in target org |

### ❌ NOT Allowed

| Operation | Reason |
|-----------|--------|
| User A → User B (different users) | Hub doesn't support direct user-to-user transfer |
| Org → User (non-self) | Transfers only to yourself |
| Org A → Org B (insufficient rights) | Missing admin/contributor in source or target |

For unsupported cases, email `website@huggingface.co`.

### Behavior

- **Old URL redirects** — `hf.co/old-repo` redirects to `hf.co/new-repo`
- **Download counts preserved** — download stats carry over
- **Likes preserved** — existing likes are maintained
- **Redirect is automatic** — no manual DNS/URL updates needed

---

## 2. `delete_repo()` — Permanent Deletion

```python
api.delete_repo(
    repo_id="namespace/repo-name",
    repo_type="model",       # "model", "dataset", or "space"
    missing_ok=False,        # don't raise if repo doesn't exist
    token="hf_...",
)
```

### Parameters

| Param | Type | Description |
|-------|------|-------------|
| `repo_id` | `str` | Must contain `/` separator or allow `None` namespace for top-level repos |
| `repo_type` | `str \| None` | `"model"`, `"dataset"`, `"space"`, or `None` (model) |
| `missing_ok` | `bool` | If `True`, silently succeed if repo doesn't exist (default: `False`) |
| `token` | `str \| bool \| None` | Write token required |

### REST Endpoint

```
DELETE https://huggingface.co/api/repos/delete
```

Payload:
```json
{
  "name": "repo-name",
  "organization": "namespace-or-null",
  "type": "model"
}
```

### ⚠️ Important Notes

- **CAUTION: This is IRREVERSIBLE.** All data, commits, discussions, and settings are permanently lost.
- **Write token required** — read-only tokens will fail with 403.
- **Repo type validation** — raises `ValueError` if `repo_type` is not a valid type.
- **Namespace parsing** — `repo_id` is split at `/`: first part = organization, second = name. For user repos, the user's namespace is automatically resolved.

---

## 3. `duplicate_repo()` — Server-Side Copy

```python
api.duplicate_repo(
    from_id="source-org/source-repo",
    to_id="my-org/new-repo",       # optional; defaults to same name under your account
    repo_type="space",
    private=True,                  # make the copy private
    exist_ok=False,                # raise if target already exists
    space_hardware="cpu-basic",    # for Spaces: hardware spec
    space_sleep_time=3600,         # for Spaces: sleep after N seconds
    space_secrets=[{"key": "API_KEY", "value": "sk-..."}],
    space_variables=[{"key": "MODE", "value": "prod"}],
    token="hf_...",
)
```

### Key Points

- **Server-side copy** — no local download/upload needed
- **Full git + LFS history preserved** — all commits and large files carried over
- **Can copy across namespaces** — user→org, org→user, org→org
- **Space-specific settings** — hardware, storage, sleep time, secrets, env vars
- **Returns `RepoUrl`** — the URL of the newly created repo

### REST Equivalent

```
POST https://huggingface.co/api/repos/{repo_type}/duplicate
```

---

## 4. `repo_exists()` — Check If Repository Exists

```python
from huggingface_hub import repo_exists

# As a standalone function:
exists = repo_exists("google/gemma-7b")       # -> True
exists = repo_exists("google/not-a-repo")     # -> False

# Or via HfApi:
api = HfApi()
exists = api.repo_exists("meta-llama/Llama-2-7b", repo_type="model")
```

### Behavior

- Returns `True` if the repo exists (including gated repos you have access to)
- Returns `True` for **gated repos** (even without access) — `GatedRepoError` is caught internally
- Returns `False` only if the repo truly doesn't exist (`RepositoryNotFoundError`)
- Deleted repos return `False`

### Implementation Detail

```python
# Internally calls repo_info() and catches expected errors:
try:
    self.repo_info(repo_id=repo_id, repo_type=repo_type, token=token)
    return True
except GatedRepoError:
    return True     # repo exists but is gated
except RepositoryNotFoundError:
    return False
```

---

## 5. `update_repo_settings()` — Visibility & Gating

```python
api.update_repo_settings(
    repo_id="namespace/repo-name",
    private=True,                              # make private (alternative to visibility)
    visibility="public",                       # or "private", or "protected" (Spaces only)
    gated="manual",                            # "auto", "manual", or False (disable gating)
    repo_type="model",
    token="hf_...",
)
```

### Parameters

| Param | Type | Description |
|-------|------|-------------|
| `private` | `bool \| None` | `True` = private, `False` = public. Cannot use with `visibility`. |
| `visibility` | `"public" \| "private" \| "protected" \| None` | Explicit visibility. For Spaces, supports `"protected"` (requires auth to view). |
| `gated` | `"auto" \| "manual" \| False \| None` | Gate status. `"auto"` = auto-approve, `"manual"` = review required, `False` = open. |

### Visibility vs Private

| Setting | Effect |
|---------|--------|
| `private=True` | Sets repo to private |
| `private=False` | Sets repo to public |
| `visibility="public"` | Same as `private=False` |
| `visibility="private"` | Same as `private=True` |
| `visibility="protected"` | Spaces only: requires auth to view, but no specific access grant |

> **Note:** `private` and `visibility` are mutually exclusive — pass one or the other.

---

## 6. `permanently_delete_lfs_files()` — Remove Large Files

```python
from huggingface_hub import HfApi, list_lfs_files

api = HfApi()

# First, list LFS files
lfs_files = api.list_lfs_files("namespace/repo")

# Then permanently delete specific ones
api.permanently_delete_lfs_files(
    repo_id="namespace/repo",
    lfs_files=[lfs_files[0]],        # specific LFS files to delete
    rewrite_history=True,             # recommended: removes all pointers from git history
    repo_type="model",
)
```

### ⚠️ Warnings

- **IRREVERSIBLE** — once deleted, LFS files cannot be recovered
- **Rewrite history** — if `True`, all git references to the deleted files are stripped from commit history
- **Can corrupt repo** — removing files referenced by active commits may break the repository
- Use `list_lfs_files()` to enumerate candidates before deletion

---

## 7. Related Methods

| Method | Purpose |
|--------|---------|
| `create_repo()` | Create new repo |
| `delete_branch()` | Remove a branch |
| `delete_file()` / `delete_files()` | Delete files in a commit |
| `delete_folder()` | Delete an entire folder |
| `list_repo_files()` | List files in repo |
| `get_full_repo_name()` | Resolve repo ID with namespace |
| `verify_repo_checksums()` | Verify LFS file integrity |

---

## 8. Practical Patterns

### Rename Within Same Namespace

```python
# Just change the repo name, keep the same user/org
api.move_repo("myuser/old-name", "myuser/new-name")
```

### Transfer to Organization

```python
# Transfer repo from your user to your org
api.move_repo("myuser/repo-name", "myorg/repo-name")
```

### Safe Deletion with Existence Check

```python
if api.repo_exists("old-project/defunct-model"):
    api.delete_repo("old-project/defunct-model", missing_ok=True)
    print("Deleted")
else:
    print("Already gone")
```

### Duplicate a Space with Custom Config

```python
api.duplicate_repo(
    from_id="huggingface/spaces-demo",
    to_id="myuser/my-custom-space",
    repo_type="space",
    private=True,
    space_hardware="t4-small",
    space_sleep_time=300,
    space_secrets=[{"key": "HF_TOKEN", "value": "hf_..."}],
)
```

### Change Visibility Programmatically

```python
# Make public
api.update_repo_settings("myuser/research-model", private=False)

# Or using visibility parameter
api.update_repo_settings("myuser/research-model", visibility="public")

# Make a Space protected (auth-wall but not access-gated)
api.update_repo_settings("myuser/my-space", visibility="protected", repo_type="space")
```

---

## 9. Rate Limits & Restrictions

- **Move operations** — subject to standard HF rate limits (see [Rate Limits docs](https://huggingface.co/docs/hub/en/rate-limits))
- **Delete operations** — write operations count toward your API rate limit
- **Duplicate operations** — server-side copy may be queued; large repos take longer
- **Visibility changes** — instant propagation but Space URL may briefly cache old state
- **Gating changes** — take effect immediately for new requests; existing access grants persist until revoked

---

## 10. Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `RepositoryNotFoundError` | Repo doesn't exist | Use `repo_exists()` to check first, or pass `missing_ok=True` |
| `HfHubHTTPError` (403) | Insufficient permissions | Use a write token; ensure you have proper org rights |
| `HfHubHTTPError` (400) | Invalid request | Check `from_id`/`to_id` format (must have `/`) |
| `ValueError` | Invalid `repo_type` | Use "model", "dataset", or "space" |
| `HfHubHTTPError` (429) | Rate limited | Wait and retry with backoff |

---

## 11. Key URLs

| Resource | URL |
|----------|-----|
| Repo Settings (UI) | https://huggingface.co/{namespace}/{repo}/settings |
| Hub API Endpoints | https://huggingface.co/docs/hub/en/api |
| Rate Limits | https://huggingface.co/docs/hub/en/rate-limits |
| huggingface_hub docs | https://huggingface.co/docs/huggingface_hub/package_reference/hf_api |
| OpenAPI Spec | https://huggingface.co/.well-known/openapi.json |
| Repo Rename Docs | https://huggingface.co/docs/hub/en/repositories-settings |
