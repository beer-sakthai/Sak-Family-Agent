# User & Org Profile API: Engagement, Storage & Social Graph

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
