---
name: SakThai-hf-hub-user-and-org-profile-api
version: 1.0.0
description: Complete reference for Hugging Face Hub User and Organization Profile
  API — REST endpoints, Python SDK methods (get_user_overview, get_organization_overview,
  whoami, list_user_followers/following/members, list_user_repos, list_repo_likers,
  pagination behavior), User and Organization dataclass fields (annotated + dynamic
  extras), auth patterns, social graph operations, and practical discovery recipes.
category: mlops
tags:
- access
- api
- control
- followers
- groups
- hf
- hub
- huggingface
- members
- org
- organizations
- profile
- profiles
- resource
- social-graph
- user
- users
- whoami
author: SakThai
license: MIT
updated: 2026-07-25
---

# Hugging Face Hub User & Organization Profile API — Deep Dive

Complete reference for the Hugging Face Hub's User and Organization Profile API.
Covers all REST endpoints, Python SDK methods via `huggingface_hub.HfApi()`,
dataclass fields (annotated + dynamic extras from API), authentication patterns,
social graph traversal (followers/following/members), repo enumeration with
storage info, and practical discovery recipes.

## Core Concepts

The Hub exposes four categories of user/org profile operations:

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Identity** | `whoami`, user/org overview | Current user identity, public profile snapshots |
| **Social Graph** | followers, following, members | Who follows whom, org membership |
| **Engagement** | likes | Who liked a specific repo |
| **Storage** | user repos list | Repo list with storage consumption per repo |

### API Layer Differentiation

| Aspect | Raw REST API | Python SDK (`huggingface_hub`) |
|--------|-------------|-------------------------------|
| **Field names** | camelCase (`avatarUrl`, `numModels`) | snake_case (`avatar_url`, `num_models`) |
| **Extra fields** | All fields returned | Dataclass stores extras via `__dict__` |
| **Pagination** | Manual `?p=N` query params | Generators (auto-paginate with yield) |
| **Auth** | `Authorization: Bearer hf_...` header | Token from `~/.cache/huggingface/token` |

---

## 1. Identity Endpoints

### 1.1 Whoami — Authenticated User Identity

```
GET /api/whoami-v2
```

**Auth:** Required (access token with any role)

**Python:** `HfApi().whoami(token=None, cache=False)`

**Returns dict with:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | MongoDB ObjectId |
| `name` | str | Username |
| `fullname` | str | Display full name |
| `email` | str | Email address |
| `emailVerified` | bool | Email verified |
| `avatarUrl` | str | Avatar URL |
| `type` | str | User type (`"user"`) |
| `isPro` | bool | PRO subscription active |
| `canPay` | bool | Payment method on file |
| `billingMode` | str | `"prepaid"` or `"postpaid"` |
| `periodEnd` | int | Unix timestamp of billing period end |
| `orgs` | list[dict] | Organizations the user belongs to |
| `auth` | dict | Auth token info: `{type, accessToken: {displayName, role, createdAt}}` |

**`cache=True` behavior:** Caches the response for the session lifetime. Skip cache with `cache=False` (default).

```python
from huggingface_hub import HfApi
api = HfApi()
me = api.whoami()
print(f"Logged in as {me['name']} ({me['fullname']})")
print(f"PRO: {me['isPro']}, Email verified: {me['emailVerified']}")
for org in me['orgs']:
    print(f"  Org: {org['name']} (role: {org.get('role', 'member')})")
```

### 1.2 User Overview — Public Profile

```
GET /api/users/{username}/overview
```

**Auth:** Optional (public for non-hidden users; token extends visibility)

**Python:** `HfApi().get_user_overview(username)`

**Returns `User` dataclass** with annotated + dynamic extra fields:

#### Annotated Fields (`User.__annotations__`)

| Field | Type | Description |
|-------|------|-------------|
| `username` | `str` | HF username |
| `fullname` | `str` | Display name |
| `avatar_url` | `str` | Avatar CDN URL |
| `details` | `str \| None` | Bio/description (Markdown) |
| `is_following` | `bool \| None` | Whether the authenticated user follows this user |
| `is_pro` | `bool \| None` | PRO status |
| `num_models` | `int \| None` | Public model count |
| `num_datasets` | `int \| None` | Public dataset count |
| `num_spaces` | `int \| None` | Space count |
| `num_discussions` | `int \| None` | Discussion/PR count |
| `num_papers` | `int \| None` | Papers submitted |
| `num_upvotes` | `int \| None` | Total upvotes received |
| `num_likes` | `int \| None` | Total likes given |
| `num_following` | `int \| None` | People they follow |
| `num_followers` | `int \| None` | People following them |
| `orgs` | `list[Organization]` | Organizations they belong to |

#### Dynamic Extra Fields (from raw API JSON, not in annotations but accessible)

| Field | Source (camelCase) | Type | Description |
|-------|-------------------|------|-------------|
| `user_type` | `type` | `str` | `"user"` |
| `numBuckets` | `numBuckets` | `int` | Storage bucket count |
| `numFollowingOrgs` | `numFollowingOrgs` | `int` | Organizations they follow |
| `numKernels` | `numKernels` | `int` | Kernel/Gist count |
| `createdAt` | `createdAt` | `str` (ISO) | Account creation date |
| `_id` | `_id` | `str` | MongoDB ObjectId |

```python
from huggingface_hub import get_user_overview

user = get_user_overview("julien-c")
print(f"{user.fullname} (@{user.username})")
print(f"  {user.num_models} models, {user.num_datasets} datasets")
print(f"  {user.num_followers} followers, {user.num_following} following")
print(f"  PRO: {user.is_pro}")
print(f"  Bio: {user.details[:100] if user.details else 'N/A'}")

# Dynamic extras (assessable but not typed)
print(f"  Account created: {user.createdAt}")
print(f"  User type: {user.user_type}")
```

### 1.3 Organization Overview — Public Org Profile

```
GET /api/organizations/{org}/overview
```

**Auth:** Optional. Returns `Organization` dataclass.

**Python:** `HfApi().get_organization_overview(organization)`

**Note:** This is a DIFFERENT endpoint from user overview — uses `/organizations/` path, not `/users/`. Do not use `get_user_overview()` for orgs.

#### `Organization` Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Org short name (e.g., `"huggingface"`) |
| `fullname` | `str` | Display name (e.g., `"Hugging Face"`) |
| `avatar_url` | `str` | Avatar CDN URL |
| `details` | `str \| None` | Org description |
| `is_verified` | `bool \| None` | Verified badge status |
| `is_following` | `bool \| None` | Whether the authenticated user follows this org |
| `num_users` | `int \| None` | Member count |
| `num_models` | `int \| None` | Public model count |
| `num_datasets` | `int \| None` | Public dataset count |
| `num_spaces` | `int \| None` | Space count |
| `num_followers` | `int \| None` | People following the org |
| `num_papers` | `int \| None` | Papers submitted |
| `plan` | `str \| None` | Org plan: `"community"`, `"pro"`, `"team"`, `"enterprise"` |

#### Dynamic Extra Fields

| Field | Source | Type | Description |
|-------|--------|------|-------------|
| `numBuckets` | `numBuckets` | `int` | Storage bucket count |
| `numKernels` | `numKernels` | `int` | Kernel count |
| `_id` | `_id` | `str` | MongoDB ObjectId |

```python
from huggingface_hub import get_organization_overview

org = get_organization_overview("huggingface")
print(f"Org: {org.fullname} (@{org.name})")
print(f"  Verified: {org.is_verified}, Plan: {org.plan}")
print(f"  {org.num_users} members")
print(f"  {org.num_models} models, {org.num_datasets} datasets, {org.num_spaces} spaces")
print(f"  {org.num_followers} followers")
```

---

## 2. Social Graph Endpoints

### 2.1 User Followers

```
GET /api/users/{username}/followers?p=0
```

**Auth:** Optional

**Python:** `HfApi().list_user_followers(username)`

**Returns:** Generator yielding partial `User` objects with fields: `username`, `fullname`, `avatar_url`, `is_pro`, `_id`.

**Pagination:** Use the generator — it auto-paginates across all pages. There is NO `limit` parameter on the Python method.

```python
from huggingface_hub import HfApi

api = HfApi()
followers = api.list_user_followers("julien-c")

# Iterate all followers
count = 0
for follower in followers:
    count += 1
    if count <= 3:
        print(f"  {follower.fullname} (@{follower.username})")

print(f"Total: {count} followers fetched")
```

### 2.2 User Following

```
GET /api/users/{username}/following?p=0
```

**Auth:** Optional

**Python:** `HfApi().list_user_following(username)`

**Returns:** Generator yielding partial `User` objects (same shape as followers).

### 2.3 Organization Followers

```
GET /api/organizations/{org}/followers?p=0
```

**Auth:** Optional

**Python:** `HfApi().list_organization_followers(organization)`

**Returns:** Generator yielding partial `User` objects.

### 2.4 Organization Members

```
GET /api/organizations/{org}/members?p=0
```

**Auth:** Required (read token). Only returns org members. Non-members get 403.

**Python:** `HfApi().list_organization_members(organization)`

**Returns:** Generator yielding full `User` objects (with num_* stats).

```python
from huggingface_hub import HfApi

api = HfApi()
members = list(api.list_organization_members("huggingface"))
print(f"Total members: {len(members)}")
for m in members[:5]:
    print(f"  {m.fullname} (@{m.username}) — PRO={m.is_pro}")
```

---

---

## Deep Dive Reference

For exhaustive reference specifications, cookbook snippets, and extended documentation, see [User & Org Profile API: Engagement, Storage & Social Graph](./references/user-org-engagement-and-storage.md).
