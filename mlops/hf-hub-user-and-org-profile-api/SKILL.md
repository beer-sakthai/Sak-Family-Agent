---
name: hf-hub-user-and-org-profile-api
author: SakThai
license: MIT
description: Complete reference for Hugging Face Hub User and Organization Profile API — overview endpoints, social graph (followers/following), likes, repo enumeration, whoami authentication, and Python SDK integration
category: mlops
version: 1.0.0
tags: [huggingface, hub, api, users, organizations, profiles, social-graph, whoami]
---

# Hugging Face Hub User & Organization Profile API

Deep reference for the User and Organization Profile API on Hugging Face Hub. Covers REST endpoints, Python SDK methods (HfApi), data models (User, Organization, UserLikes, RepoStorageInfo), social graph operations, and authentication patterns.

## Key Endpoints

| Endpoint | Auth Required | Description |
|----------|--------------|-------------|
| `GET /api/whoami-v2` | Yes | Authenticated user identity |
| `GET /api/users/{username}/overview` | No | Public user profile overview |
| `GET /api/organizations/{org}/overview` | No | Public organization profile |
| `GET /api/users/{username}/followers` | No | Paginated user followers |
| `GET /api/users/{username}/following` | No | Paginated user follows |
| `GET /api/organizations/{org}/followers` | No | Paginated org followers |
| `GET /api/organizations/{org}/members` | Yes | Paginated org members |
| `GET /api/settings/repositories` | Yes | Authenticated user's repos with storage |
| `GET /api/organizations/{org}/settings/repositories` | Yes | Org's repos with storage |

## Data Models (huggingface_hub)

- **User**: username, fullname, avatar_url, details, is_following, is_pro, num_models/datasets/spaces/discussions/papers/upvotes/likes/following/followers, orgs
- **Organization**: avatar_url, name, fullname, details, is_verified, is_following, num_users/models/spaces/datasets/followers/papers, plan
- **UserLikes**: user, total, datasets, kernels, models, spaces
- **RepoStorageInfo**: id, type, updated_at, visibility, storage (bytes), storage_percent

## Python SDK Methods

All methods on `HfApi()`:
- `whoami(token, cache=False)`
- `get_user_overview(username)` → User
- `get_organization_overview(organization)` → Organization
- `list_user_followers(username)` → Iterable[User]
- `list_user_following(username)` → Iterable[User]
- `list_organization_followers(organization)` → Iterable[User]
- `list_organization_members(organization)` → Iterable[User]
- `list_user_repos(namespace=None)` → Iterable[RepoStorageInfo]
- `list_repo_likers(repo_id, repo_type)` → Iterable[User]

## Sources

- Source code: `huggingface_hub/hf_api.py` (User line 1750, Organization line 1683, UserLikes line 1614, RepoStorageInfo line 1644)
- Source code: `huggingface_hub/hf_api.py` — API methods at lines 2305, 11401, 11428, 11455, 11483, 11511, 11539, 3160, 3201
- Hub docs: https://huggingface.co/docs/hub/en/api
