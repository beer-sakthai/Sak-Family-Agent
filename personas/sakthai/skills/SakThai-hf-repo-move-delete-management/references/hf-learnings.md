# HF Hub Repository Lifecycle Management — Deep Dive

> **Topic:** `hf-hub-repo-lifecycle-management-deep-dive` — Deepening the existing shallow entry
> **Date researched:** 2026-07-25
> **Sources:** Official Hugging Face OpenAPI spec (`.well-known/openapi.md`), `huggingface_hub` v1.24.0 source code, HF Hub docs

## Overview

This deep-dive covers the complete repository lifecycle on the Hugging Face Hub:
creation, settings/visibility changes, gating, renaming/transfer, duplication,
super-squash, LFS file management, and permanent deletion. The SKILL.md covers
the basic Python API; this document adds the raw REST API details, edge cases,
response schemas, and advanced patterns learned from source documentation.

---

## 1. REST API Endpoints

All endpoints documented here come from the **Hub OpenAPI specification**
at `https://huggingface.co/.well-known/openapi.json` (or markdown version at
`https://huggingface.co/.well-known/openapi.md`). Base URL is `https://huggingface.co`.

### 1.1 Create Repository

```
POST /api/repos/create
```

**Request Body Schema** (combined from `allOf`):

```json
{
  "name": "string",                     // Required. Repo name only, not full path
  "organization": "string | null",      // Org namespace, or null for user account
  "region": "us | eu",                  // Cloud region for hosting
  "license": "string",                  // One of 70+ supported license identifiers
  "license_name": "string",            // Custom name when license="other" (pattern: ^[a-z0-9-.]+$)
  "license_link": "LICENSE | LICENSE.md | uri", // Link to custom license file
  "private": true | false | null,      // Cannot be specified with 'visibility'
  "visibility": "private | public | protected", // 'protected' only for Spaces
  "resourceGroupId": "string",         // 24-char hex ID for Enterprise resource groups
  "files": [                           // Optional initial files (e.g. README.md)
    {
      "content": "string",
      "path": "string",
      "encoding": "utf-8 | base64"     // Optional, defaults to utf-8
    }
  ],
  "type": "model | dataset | space"    // Defaults to "model"
}
```

**Notes:**
- `name` must be a valid slug (alphanumeric, hyphens, underscores, dots)
- `private` and `visibility` are **mutually exclusive** — the API rejects both
- `license` supports the full list including Llama 4 (`llama4`), Grok 2 (`grok2-community`),
  Gemma (`gemma`), OpenRAIL, CC licenses, and 60+ others
- `files` is an array — you can seed the repo with multiple initial files in one call
- `region` is new (2026) — `us` or `eu` for data residency control

### 1.2 Move/Rename Repository

```
POST /api/repos/move
```

**Request Body:**

```json
{
  "fromRepo": "source-namespace/repo-name",
  "toRepo": "target-namespace/repo-name",
  "type": "model | dataset | space | bucket | kernel"
}
```

**Key point about `type`:** Unlike most other endpoints, the move API uses
`type` with values `"model"`, `"dataset"`, `"space"`, `"bucket"`, or `"kernel"`.
This is the only endpoint that supports `"bucket"` and `"kernel"` as repo types
in the lifecycle management family.

### 1.3 Update Repository Settings

```
PUT /api/models/{namespace}/{repo}/settings
PUT /api/datasets/{namespace}/{repo}/settings
PUT /api/spaces/{namespace}/{repo}/settings
```

**Request Body** (from OpenAPI JSON Schema):

```json
{
  "private": true | false,
  "gated": "auto | manual | false",
  "visibility": "public | private | protected"
}
```

**Response:** Returns the updated repo settings object.

**Key observations from OpenAPI spec:**
- Unlike `create`, this endpoint uses the **repo-specific URL pattern**
  (`/api/models/{namespace}/{repo}/settings`) not the generic `/api/repos/` pattern
- `gated` values: `"auto"` (auto-approve access requests), `"manual"` (requires review),
  `false` (no gating — anyone can access)
- Changing gating to `false` on a previously gated repo may not retroactively revoke
  existing granted access (must be managed separately)

### 1.4 Delete Repository

```
DELETE /api/repos/delete
```

**Request Body:**

```json
{
  "name": "repo-name",
  "organization": "namespace-or-null",
  "type": "model | dataset | space"
}
```

**Important:** The Hub doesn't expose a `DELETE /api/repos/{id}` style endpoint —
deletion is a **POST with a body** that specifies name, organization, and type.
This is unusual compared to REST conventions.

### 1.5 Duplicate Repository

```
POST /api/repos/{repo_type}/duplicate
```

No OpenAPI schema available in the markdown spec — the Python SDK wraps this
server-side copy feature. The `repo_type` is inserted into the path
(e.g., `/api/repos/model/duplicate`, `/api/repos/dataset/duplicate`).

---

## 2. Super-Squash History

```
POST /api/models/{namespace}/{repo}/super-squash/{rev}
```

Squashes all commits on a branch into a single commit.

**Parameters:**
- `namespace` (path): User or org name
- `repo` (path): Repo name
- `rev` (path): Revision/branch to squash (typically `main`)

**Response:** Returns the new commit ID after the squash.

**Important caveats from the Python SDK:**
- Only works from the **head** of a branch (not arbitrary revisions)
- After squashing, the branch **cannot be merged** into another branch
  because history has diverged
- IRREVERSIBLE — old commits are permanently lost
- Storage quota effects are **not immediate** — reflected within ~36 hours

**Python SDK method:** `api.super_squash_history(repo_id, branch="main", commit_message="...", repo_type="model")`

---

## 3. LFS File Management

### 3.1 List LFS Files

```
GET /api/models/{namespace}/{repo}/lfs-files
```

**Parameters:**
- `namespace`, `repo` (path)
- `cursor` (query): Pagination cursor
- `limit` (query): Page size
- `xet` (query): Optional Xet-specific filter

**Response:** Returns a paginated list of LFS files with metadata (filename, size, sha, refs).

### 3.2 Batch Delete LFS Files

```
POST /api/models/{namespace}/{repo}/lfs-files/batch
```

**Request Body:**
```json
{
  "files": [
    {"sha": "sha256-oid"},
    ...
  ],
  "rewriteHistory": true | false
}
```

### 3.3 Delete Single LFS File

```
DELETE /api/models/{namespace}/{repo}/lfs-files/{sha}
```

**Parameters:**
- `rewriteHistory` (query): Whether to rewrite git history to remove LFS pointers

### 3.4 Duplicate Xet Files (Server-Side)

```
POST /api/models/{namespace}/{repo}/lfs-files/duplicate
```

Duplicates Xet-stored files from one repo to another **by hash** without
re-uploading bytes. The caller must then commit the files normally.

---

## 4. Repo Info & Existence Checking

### 4.1 `repo_info()` — Full Metadata

```python
api.repo_info("namespace/repo", repo_type="model", expand=["..."])
```

**`expand` parameter** accepts a list of expand properties depending on repo type:
- Models: `ExpandModelProperty_T` (e.g., `"cardData"`, `"siblings"`, `"downloads"`)
- Datasets: `ExpandDatasetProperty_T`
- Spaces: `ExpandSpaceProperty_T`

**Additional useful repo info endpoints from OpenAPI spec:**
- `GET /api/models/{namespace}/{repo}/scan` — Security scan status
- `GET /api/models/{namespace}/{repo}/treesize/{rev}/{path}` — Total size of repo/subfolder
- `GET /api/models/{namespace}/{repo}/jwt` — Generate JWT for repo access (dev mode Spaces)

### 4.2 `repo_exists()` — Implementation Detail

```python
# Source: huggingface_hub v1.24.0
# repo_exists() calls repo_info() and catches exceptions:
try:
    api.repo_info(repo_id=repo_id, repo_type=repo_type, token=token)
    return True
except GatedRepoError:
    return True     # Repo exists but is gated
except RepositoryNotFoundError:
    return False
```

This means:
- Returns `True` for **gated repos** you don't have access to (they exist, you just can't see contents)
- Returns `True` for **private repos** you have access to
- Returns `False` only if 404 (truly doesn't exist)
- Returns `True` for repos you deleted but are in the process of being garbage-collected

---

## 5. Advanced Patterns & Edge Cases

### 5.1 Creating a Repo with Initial Files

```python
from huggingface_hub import HfApi

api = HfApi()
url = api.create_repo(
    "myuser/my-model",
    repo_type="model",
    private=False,
    license="mit",
    exist_ok=True,
    # Can't pass initial files via Python SDK create_repo() directly
    # Instead, create then immediately upload:
)
# Then seed with initial files:
api.upload_file(
    path_or_fileobj=b"# My Model\n\nGreat model description",
    path_in_repo="README.md",
    repo_id="myuser/my-model",
)
```

The OpenAPI spec shows that the create endpoint **does** support initial `files`
in the request body, but the Python SDK's `create_repo()` doesn't expose this
parameter yet (as of v1.24.0). To seed with initial files, use a two-step:
create + upload.

### 5.2 Repository Regions (New in 2026)

The `region` parameter (`"us"` or `"eu"`) allows data residency control:
- **`us`**: US-based storage (default)
- **`eu`**: EU-based storage (GDPR compliance)

This is set at creation time and **cannot be changed** after creation.

### 5.3 Resource Groups (Enterprise Hub Only)

`resourceGroupId` is a 24-character hex string (MongoDB ObjectID format).
Resource groups control which org members can access which repos.
Found in the URL of the resource group's page on the Hub.

Only available for **Enterprise Hub** organizations.

### 5.4 Custom Licenses

When `license: "other"`, you must provide:
- `license_name`: A machine-readable slug (`pattern: ^[a-z0-9-.]+$`)
- `license_link`: Either `"LICENSE"` (file at repo root), `"LICENSE.md"`, or a full URI

### 5.5 Gating vs Visibility — The Difference

| Aspect | Visibility | Gating |
|--------|-----------|--------|
| What it controls | Who can **find/see** the repo | Who can **access/download** content |
| Values | `public`, `private`, `protected` (Spaces) | `auto`, `manual`, `false` |
| Effect of `public` | Anyone can see the repo page | Anyone can download |
| Effect of `private` | Only you + collaborators see it | Only you + collaborators can download |
| Effect of gated+public | Anyone sees the repo page | Must request/download grant to access |
| Effect of `protected` (Spaces) | Anyone sees it, must be logged in | Must be authenticated to view |

### 5.6 Move/Transfer Edge Cases

- **User A → User B** (different users): **NOT supported** via API. Must email
  `website@huggingface.co`.
- **Self-rename**: User A renames within own namespace — no permissions issue
- **Org → Self**: Requires `admin` role in the org
- **Org → Org**: Requires `admin` in source + `contributor` in target
- **Transfer preserves**: download counts, likes, discussions, webhooks
- **Old URL redirects**: `hf.co/old-path` → `hf.co/new-path` automatically

### 5.7 Super-Squash Workflow

Best practice for repos with many small commits:

```python
# 1. Before squashing, back up important refs
# 2. Squash
api.super_squash_history(
    "myuser/large-repo",
    branch="main",
    commit_message="Squash all history into single commit",
)
# 3. Wait ~36 hours for storage quota to reflect
# 4. Inform collaborators: they must re-clone (local history will conflict)
```

## 6. Error Reference

| HTTP Status | Error Class | Cause |
|-------------|-------------|-------|
| 404 | `RepositoryNotFoundError` | Repo doesn't exist |
| 403 | `HfHubHTTPError` | Insufficient permissions |
| 400 | `HfHubHTTPError` | Invalid request (e.g., bad name format) |
| 429 | `HfHubHTTPError` | Rate limit exceeded |
| - | `ValueError` | Invalid repo_type in Python SDK |

## 7. Key URLs Reference

| Resource | URL |
|----------|-----|
| OpenAPI spec (JSON) | `https://huggingface.co/.well-known/openapi.json` |
| OpenAPI spec (Markdown) | `https://huggingface.co/.well-known/openapi.md` |
| Repo Settings UI | `https://huggingface.co/{namespace}/{repo}/settings` |
| Create Repo (UI) | `https://huggingface.co/new` |
| huggingface_hub docs | `https://huggingface.co/docs/huggingface_hub/package_reference/hf_api` |
| HF Hub API Endpoints | `https://huggingface.co/docs/hub/en/api` |
| Repo Settings Docs | `https://huggingface.co/docs/hub/en/repositories-settings` |
| Storage Limits | `https://huggingface.co/docs/hub/en/storage-limits` |
| Rate Limits | `https://huggingface.co/docs/hub/en/rate-limits` |
