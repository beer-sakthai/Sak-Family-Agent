---
name: SakThai-hf-hub-user-and-org-profile-api
description: "Complete reference for Hugging Face Hub User and Organization Profile API \u2014\
  \ REST endpoints, Python SDK methods (get_user_overview, get_organization_overview,\
  \ whoami, list_user_followers/following/members, list_user_repos, list_repo_likers,\
  \ pagination behavior), User and Organization dataclass fields (annotated + dynamic\
  \ extras), auth patterns, social graph operations, and practical discovery recipes."
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

## 3. Engagement Endpoints

### 3.1 Repo Likers (Who Liked This Repo)

```
GET /api/models/{model_id}/likers
GET /api/datasets/{dataset_id}/likers
```

**Auth:** Optional (public for public repos)

**Python:** `HfApi().list_repo_likers(repo_id, repo_type="model")`

**Returns:** Generator yielding partial `User` objects with: `username`, `fullname`, `avatar_url`, `is_pro`, `_id`.

```python
from huggingface_hub import HfApi

api = HfApi()
likers = api.list_repo_likers("bert-base-uncased", repo_type="model")
count = 0
for liker in likers:
    count += 1
    if count <= 5:
        print(f"  {liker.fullname} (@{liker.username})")
print(f"Total likers: {count}")
```

---

## 4. Storage & Repo Management Endpoints

### 4.1 User Repos with Storage Info

```
GET /api/settings/repositories
GET /api/organizations/{org}/settings/repositories
```

**Auth:** Required (write token). Returns repos for the authenticated user OR an org they manage.

**Python:** `HfApi().list_user_repos(namespace=None)`

| Parameter | Behavior |
|-----------|----------|
| `namespace=None` | Returns current authenticated user's repos |
| `namespace="org-name"` | Returns repos for the specified org (requires membership) |
| `namespace="other-user"` | ❌ NOT supported for other users — returns 404 |

**Returns:** Generator yielding `RepoStorageInfo` objects:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Full repo ID (`namespace/repo-name`) |
| `type` | `str` | Repo type: `"model"`, `"dataset"`, `"space"`, `"bucket"` |
| `visibility` | `str` | `"public"` or `"private"` |
| `updated_at` | `datetime` | Last update timestamp |
| `storage` | `int` | Storage used in bytes |
| `storage_percent` | `float` | Storage as percentage of limit |

```python
from huggingface_hub import HfApi

api = HfApi()

# Own repos sorted by storage descending
repos = list(api.list_user_repos())
print(f"Total repos: {len(repos)}")
for r in repos[:5]:
    mb = r.storage / 1024 / 1024
    print(f"  {r.id} ({r.type}, {r.visibility}): {mb:.1f} MB ({r.storage_percent:.1f}%)")

# Org repos (requires org membership)
org_repos = list(api.list_user_repos(namespace="huggingface"))
```

---

## 5. Social Graph Visualization Patterns

### 5.1 Build a User Profile Summary

```python
from huggingface_hub import get_user_overview

def profile_summary(username: str) -> dict:
    """Summarize a HF user's public profile."""
    user = get_user_overview(username)
    return {
        "username": user.username,
        "fullname": user.fullname,
        "pro": user.is_pro,
        "models": user.num_models,
        "datasets": user.num_datasets,
        "spaces": user.num_spaces,
        "followers": user.num_followers,
        "following": user.num_following,
        "upvotes": user.num_upvotes,
        "orgs": [o.name for o in (user.orgs or [])],
        "created": getattr(user, "createdAt", None),
    }

info = profile_summary("Nanthasit")
for k, v in info.items():
    print(f"  {k}: {v}")
```

### 5.2 Mutual Follow Detection

```python
from huggingface_hub import HfApi

def mutual_follows(user_a: str, user_b: str) -> list[str]:
    """Find users who follow both A and B."""
    api = HfApi()
    a_followers = {f.username for f in api.list_user_followers(user_a)}
    b_followers = {f.username for f in api.list_user_followers(user_b)}
    return list(a_followers & b_followers)
```

### 5.3 Org Member Discovery with Role Inference

The `/organizations/{org}/members` endpoint returns all members. While the API doesn't return explicit roles through this endpoint, you can combine it with `whoami()` for your own orgs or use the org overview's `num_users` count for statistics.

### 5.4 Storage Audit

```python
from huggingface_hub import HfApi

def storage_audit(namespace: str = None) -> dict:
    """Report storage usage broken down by repo type."""
    api = HfApi()
    repos = list(api.list_user_repos(namespace=namespace))
    by_type = {}
    total_bytes = 0
    for r in repos:
        by_type.setdefault(r.type, {"count": 0, "bytes": 0})
        by_type[r.type]["count"] += 1
        by_type[r.type]["bytes"] += r.storage
        total_bytes += r.storage
    return {
        "total_repos": len(repos),
        "total_gb": total_bytes / 1024**3,
        "by_type": by_type,
    }
```

---

## 6. Authentication Notes

| Endpoint | Auth Required | Token Role | Notes |
|----------|--------------|------------|-------|
| `whoami-v2` | ✅ Required | Any | Returns full auth context |
| user overview | ❌ Optional | — | Public; token extends detail (e.g., `is_following`) |
| org overview | ❌ Optional | — | Same as user overview |
| followers / following | ❌ Optional | — | Public lists |
| org members | ✅ Required | Read | Requires org membership |
| user repos | ✅ Required | Write | Only for authenticated user's own repos |
| repo likers | ❌ Optional | — | Public for public repos |

---

## 7. Rate Limits

- **Unauthenticated**: ~100 requests/min (shared pool)
- **Authenticated**: Higher limits proportional to account tier
- **Social graph iteration**: Generators pace themselves — no special rate limit for follower/member enumeration beyond standard limits
- **Settings endpoints** (repos with storage): May have stricter limits due to compute overhead

---

## 8. Key Differences: Raw REST API vs Python SDK

| Aspect | Raw REST API | Python SDK |
|--------|-------------|------------|
| **Field naming** | camelCase | snake_case |
| **Pagination** | Manual `p=N` param | Auto-paginated generators |
| **Auth** | Raw header token | Managed via `HfApi()` or env |
| **Extra fields** | All fields returned | Dataclass holds extras in `__dict__` |
| **User vs Org** | Different URL paths | Different dataclasses (`User` vs `Organization`) |
| **Followers** | `api/users/{u}/followers` | `list_user_followers(u)` |
| **whoami** | `api/whoami-v2` | `api.whoami()` returns dict (not dataclass) |

---

## 9. Sources

- Live API testing against `huggingface.co/api/users`, `/api/organizations`, `/api/whoami-v2` (2026-07-25)
- `huggingface_hub` source v1.24.0+ — `hf_api.py`: `User` (line ~1750), `Organization` (line ~1683), `UserLikes` (line ~1614), `RepoStorageInfo` (line ~1644)
- Hub API docs: https://huggingface.co/docs/hub/en/api
- Source code: `HfApi.get_user_overview()`, `HfApi.get_organization_overview()`, `HfApi.list_user_followers()`, etc.
