# HF Learnings — HF Hub User & Organization Profile API Deep Dive

## 2026-07-25: hf-hub-user-and-org-profile-api — Complete REST + Python SDK Reference (Topic #232)

### Summary
Comprehensive deep-dive on the Hugging Face Hub's User and Organization Profile API. Covers the full surface: identity endpoints (whoami-v2, user overview, org overview), social graph traversal (followers, following, org members, repo likers), storage/repo enumeration, pagination behavior, authentication requirements, and the Python SDK dataclass hierarchy. Previously the SKILL.md was 53 lines — now expanded to ~325 lines with verified live API testing.

### Key Findings from Live API Testing (2026-07-25)

#### 1. User vs Organization — Different Endpoints, Different Dataclasses
- User overview: `GET /api/users/{username}/overview` → `User` dataclass
- Org overview: `GET /api/organizations/{org}/overview` → `Organization` dataclass
- They are NOT interchangeable. Using `get_user_overview()` on an org returns 404.

#### 2. `User` Dataclass — Annotated + Dynamic Fields
The `User` dataclass has 17 annotated fields (via `__annotations__`) plus dynamic extras from the raw JSON:

**Annotated:** `username`, `fullname`, `avatar_url`, `details`, `is_following`, `is_pro`, `num_models`, `num_datasets`, `num_spaces`, `num_discussions`, `num_papers`, `num_upvotes`, `num_likes`, `num_following`, `num_followers`, `orgs`

**Dynamic extras (accessible via `__dict__`):** `user_type` (from `type`), `numBuckets`, `numFollowingOrgs`, `numKernels`, `createdAt`, `_id`

#### 3. `Organization` Dataclass Fields
`name` (not `username`!), `fullname`, `avatar_url`, `details`, `is_verified`, `is_following`, `num_users`, `num_models`, `num_spaces`, `num_datasets`, `num_followers`, `num_papers`, `plan` — plus dynamic extras: `numBuckets`, `numKernels`, `_id`

#### 4. Social Graph — Generators Without `limit`
- `list_user_followers()` / `list_user_following()` — generators that auto-paginate. NO `limit` parameter (tried keyword `limit=5` → TypeError).
- Each follower/following item is a partial `User` with: `username`, `fullname`, `avatar_url`, `is_pro`, `_id`
- `list_organization_members()` — returns full `User` objects (with num_* stats)

#### 5. `whoami()` Returns Dict (Not Dataclass)
Unlike other profile methods, `HfApi().whoami()` returns a plain dict with fields: `id`, `name`, `fullname`, `email`, `emailVerified`, `avatarUrl`, `type`, `isPro`, `canPay`, `billingMode`, `periodEnd`, `orgs`, `auth`. Supports `cache=True` for session caching.

#### 6. `list_user_repos()` — Auth-Sensitive
- No namespace → returns authenticated user's repos with storage info (sorted by storage desc)
- With namespace → returns org repos (requires org membership) OR 404 for other users

#### 7. `list_repo_likers()` — Works on Any Public Repo
Returns a generator of `User` objects for who liked a repo. Verified on `bert-base-uncased` (2,714 likers).

### Source
- Live API testing against `huggingface.co/api` endpoints (2026-07-25) with authenticated token
- Usernames tested: `Nanthasit`, `julien-c`, `HuggingFaceH4` (org), `huggingface` (org)
- `huggingface_hub` source: `hf_api.py` — `User` line ~1750, `Organization` line ~1683, `RepoStorageInfo` line ~1644
- REST API: https://huggingface.co/docs/hub/en/api
- Raw endpoints: `/api/whoami-v2`, `/api/users/{user}/overview`, `/api/organizations/{org}/overview`, `/api/users/{user}/followers`, `/api/settings/repositories`

### Skill Updated
`mlops/hf-hub-user-and-org-profile-api/SKILL.md` — expanded from 53 lines (v1.0.0) to ~325 lines (v2.0.0) with complete REST API reference, Python SDK patterns, dataclass field documentation (annotated + dynamic), authentication matrix, rate limits, social graph recipes, and storage audit patterns.
