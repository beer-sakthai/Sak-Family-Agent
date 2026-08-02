---
name: SakThai-hf-hub-organizations-api
author: SakThai
license: MIT
description: Complete reference for Hugging Face Hub Organizations API — creating and managing organizations, members, roles, access control, and programmatic management via the huggingface_hub Python library and REST API
category: hf-hub
version: 1.0.0
---

# HF Hub Organizations API

Trigger when: user asks about managing organizations on the Hub, programmatic org member operations, listing org resources, or transferring repos between orgs.

## Overview

Organizations on the Hugging Face Hub let teams collaborate on models, datasets, Spaces, and other resources under a shared namespace. They provide:

- **Shared ownership** — repos belong to the org, not an individual
- **Role-based access** — admin/write/read roles for members
- **Billing management** — org-level payment methods and plan management
- **Access control** — gated repos, resource groups (Team & Enterprise)
- **Audit logging** — track member activity (Team & Enterprise)

Unlike personal accounts, orgs don't have interactive login sessions — members authenticate with their personal credentials and switch context via the org switcher.

## Managing Organizations

### Creating an Organization

Organizations can only be created via the Hub web UI:

1. Go to [huggingface.co/settings/organizations](https://huggingface.co/settings/organizations)
2. Click **New Organization**
3. Provide a **name** (used as namespace slug), **display name**, and optional **description**
4. Choose visibility (public or private)
5. Set default member role (read or write)

> **No API exists** for programmatic org creation. Organizations must be created through the UI.

### Organization Roles

| Role    | Permissions |
|---------|-------------|
| **Admin** | Full control: manage members, billing, org settings, delete repos, transfer ownership |
| **Write** | Push to repos, create repos under the org, manage PRs/discussions |
| **Read** | View repos, download models/datasets, view org settings |

>> **Role assignment via API**: The `hf_hub` Python API supports managing member roles programmatically. See the "Members API" section below.

## Members API (huggingface_hub)

These methods are available via `HfApi`:

```python
from huggingface_hub import HfApi
api = HfApi(token="hf_...")
```

### List Organization Members

```python
from huggingface_hub import list_organization_members

members = list_organization_members("my-org-name")
for member in members:
    print(f"{member.user}: {member.role} (since {member.joined_at})")
```

Returns a list of `OrganizationMember` objects:

| Field       | Type              | Description                     |
|-------------|-------------------|---------------------------------|
| `user`      | `str`             | Username of the member          |
| `role`      | `str`             | One of `"admin"`, `"write"`, `"read"` |
| `joined_at` | `datetime`        | When the member joined          |

### List Organization Followers

```python
from huggingface_hub import list_organization_followers

followers = list_organization_followers("my-org-name")
for follower in followers:
    print(follower.user)
```

### Get Organization Overview

```python
from huggingface_hub import get_organization_overview

overview = get_organization_overview("my-org-name")
print(overview.avatarUrl)       # Avatar URL
print(overview.description)     # Org description (markdown)
print(overview.email)           # Contact email
print(overview.id)              # Organization ID
print(overview.name)            # Display name
print(overview.orgType)         # "org" or "enterprise"
print(overview.plan)            # Plan type (if applicable)
print(overview.type)            # "org"
print(overview.url)             # HF profile URL
```

Returns a `UserOrOrg` object with org-specific metadata.

### Whoami (Current User Context)

```python
from huggingface_hub import whoami

info = whoami()
print(info["auth"]["accessToken"])       # Token scopes
print(info["auth"]["type"])              # "user" or "app"
print(info["name"])                      # Current username/org
print(info["orgs"])                      # List of org memberships
for org in info["orgs"]:
    print(f"  {org['name']}: {org['role']}")
```

The `whoami()` response includes `orgs` — a list of orgs the current user belongs to with their role.

## REST API Endpoints

### List Org Members

```
GET https://huggingface.co/api/organizations/{org_name}/members
```

Response:

```json
[
  {
    "_id": "...",
    "user": {"_id": "...", "user": "username", "fullname": "User Name"},
    "role": "admin"
  }
]
```

### List Org Repositories

```
GET https://huggingface.co/api/organizations/{org_name}/repos
```

Query params: `?limit=20&offset=0` (paginated).

### Get Org Overview (REST)

```
GET https://huggingface.co/api/organizations/{org_name}
```

Response includes: `name`, `avatarUrl`, `description`, `email`, `type`, `plan`, `orgType`, `fullname`, `websiteUrl`, `twitterUrl`, `gpgKeyIds`, `isPastDue`, `canPay`, `repoCount`, `modelCount`, `datasetCount`, `spaceCount`, `memberCount`, `totalDownloads`, `totalLikes`.

### Update Member Role

```
PUT https://huggingface.co/api/organizations/{org_name}/members/{username}/role
Content-Type: application/json
Authorization: Bearer hf_...

{"role": "write"}
```

Requires admin permissions. Role must be one of: `"admin"`, `"write"`, `"read"`.

### Remove a Member

```
DELETE https://huggingface.co/api/organizations/{org_name}/members/{username}
Authorization: Bearer hf_...
```

### List Org Groups (Team & Enterprise)

```
GET https://huggingface.co/api/organizations/{org_name}/groups
```

## Organization Cards

Organization cards (the org's profile README) are rendered from a special repository at `{org_name}/{org_name}` — similar to user profile READMEs.

```python
from huggingface_hub import HfApi
api = HfApi()

# Read org card
org_readme = api.read_repo_file("my-org/my-org", "README.md")

# Update org card content
api.upload_file(
    path_or_fileobj=b"# My Org\n\nWelcome to our organization!",
    path_in_repo="README.md",
    repo_id="my-org/my-org",
    repo_type="model",  # profile repos are model-type
)
```

The org card supports markdown with embedded HF widgets (spaces, model cards, dataset previews).

## Access Control in Organizations

### Repository Access

Repos owned by an organization inherit the org's access control:

- **Public** — visible to everyone
- **Private** — visible only to org members (based on role)
- **Gated** — users must request access, admins approve/deny

### Resource Groups (Team & Enterprise)

Resource Groups allow fine-grained access control within an organization:

```python
from huggingface_hub import HfApi
api = HfApi()
```

Resource Groups let you:
- Organize repos into logical groups
- Grant role-based access per group
- Track costs per group (Spaces, Jobs, Inference)
- SCIM-compatible user provisioning

> See `hf-hub-resource-groups-access-control` for detailed API reference.

### Gating Group Collections

Collections can gate access to ALL models/datasets within them — useful for granting access to a complete model family at once. This is a Team & Enterprise feature.

## Org-Level Billing

Organizations can manage billing separate from individual members:

- **Payment method** — credit card or invoice
- **Plan** — Free, PRO, Team, Enterprise
- **Spending limits** — per-member or org-wide
- **Usage tracking** — compute, storage, API calls

Billing settings are managed through the org settings UI.

## Transferring Repos

### To an Organization

```python
from huggingface_hub import transfer_repo

transfer_repo(
    repo_id="username/my-repo",
    to_namespace="my-org",
    repo_type="model",  # or "dataset", "space"
)
```

### From an Organization

```python
transfer_repo(
    repo_id="my-org/my-repo",
    to_namespace="other-user-or-org",
    repo_type="model",
)
```

Requirements:
- Must have **admin** role in both source and destination orgs (or be the owner)
- Transfers preserve all history, discussions, and settings
- The repo's URL changes to reflect the new owner

## Common Workflows

### List All Members and Their Roles

```python
from huggingface_hub import list_organization_members

members = list_organization_members("my-org")
org_members = {}
for m in members:
    org_members[m.user] = m.role

for username, role in sorted(org_members.items()):
    print(f"{username:25s} {role}")
```

### Find Repos Owned by an Organization

```python
from huggingface_hub import HfApi

api = HfApi()

# List all models under the org
models = list(api.list_models(author="my-org"))
datasets = list(api.list_datasets(author="my-org"))
spaces = list(api.list_spaces(author="my-org"))

print(f"Models: {len(models)}, Datasets: {len(datasets)}, Spaces: {len(spaces)}")
```

### Change a Member's Role

Using the REST API (no dedicated SDK method for role change):

```bash
curl -s -o /tmp/role_result.json -X PUT \
  "https://huggingface.co/api/organizations/my-org/members/username/role" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "write"}'

python3 -c "import json; d=json.load(open('/tmp/role_result.json')); print('Updated:', d.get('success', d))"
```

### Audit Org Activity (Team & Enterprise)

```bash
# Fetch audit logs for the org (last 7 days)
curl -s "https://huggingface.co/api/organizations/my-org/audit-log?limit=50" \
  -H "Authorization: Bearer $HF_TOKEN" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for entry in data:
    print(f\"{entry.get('action')}: {entry.get('actor')} — {entry.get('description')[:80]}\")
"
```

## Pitfalls

- **No org creation API** — organizations must be created via the web UI. Automating org setup requires browser automation (Playwright/Selenium).
- **Role changes require admin** — non-admin members get HTTP 403 when trying to update roles via the REST API.
- **Org profile repo naming** — the org card repo must be `{org_name}/{org_name}` of type `model`. Using a different name or type won't render as the organization card.
- **Private org repos** — only visible to org members. The `HfApi.list_models(author="org")` won't return private repos unless the authenticated token belongs to an org member with read+ access.
- **Token scope for org operations** — org member management requires a token with the `write` scope (or finer-grained org permissions). Read-only tokens can view public data but cannot modify members or roles.
- **Transfer is irreversible** — once a repo is transferred, the original owner loses access unless they're added as a member. There's no "undo."
- **Rate limits** — org API endpoints share the same rate limits as personal endpoints. See `SakThai-hf-hub-rate-limits` for details.
- **Service accounts (Enterprise)** — orgs on Enterprise plans can create service accounts for CI/CD. Service accounts are org-owned identities with separate fine-grained tokens. See the Hub docs for more details.
