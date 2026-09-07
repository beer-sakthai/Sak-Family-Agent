---
name: SakThai-hf-hub-resource-groups-access-control
description: "Hugging Face Hub Resource Groups — fine-grained access control for organizations, group management via UI and API, auto-join, SCIM integration, cost attribution, and programmatic member assignment."
---

# HF Hub Resource Groups (Access Control)

Trigger when: user asks about organization access control, team-based repo permissions, resource groups, fine-grained access, org member roles, restricting repo visibility by team, auto-join, or cost attribution per team.

## Overview

Resource Groups allow Hugging Face organization administrators to group related repositories together and control which members have access to specific repos — enabling different teams to work on independent sets of repositories.

**Key requirements:**
- Team or Enterprise subscription plan required. 402 error returned otherwise.
- Resource Groups are managed at the Organization level.
- A repository can belong to **only one** Resource Group.
- Organization collections can also be assigned to a Resource Group.
- An organization member can belong to **several** Resource Groups.

## Member Roles in Resource Groups

| Role | Permissions |
|------|------------|
| `read` | Read access to repositories within the Resource Group |
| `contributor` | Read + write rights to repos the user personally creates within the group |
| `write` | Full write access to all repositories in the group (create, delete, rename) |
| `admin` | Write + manage group membership (add/remove members, change roles) + manage existing repos |

Organization admins can manage **all** resource groups inside the org, including moving repos in/out of any group.

Private repositories in a Resource Group are **only visible** to members of that group. Public repos are visible to everyone.

## Management via UI

1. Navigate to Organization Settings → "Resource Group" tab
2. Create a group with a meaningful name
3. Add repositories and users to it
4. When adding users, you can search by email if it matches the org's email domain

## Auto-Join

Auto-join automatically adds org members to a Resource Group at a specified role — both existing and future members.

**Scope options:**
- All org members (including `no_access` role)
- Read+ members only (excludes `no_access` role)

**Enabling:**
- UI: Open Resource Group settings → check "Auto-include org members" → select role
- API: See Configure auto-join via API

**Auto-join and SCIM are mutually exclusive** on the same Resource Group.

## Who Can Create Resource Groups

| Setting | Allowed roles |
|---------|--------------|
| Admins only (default) | Only org admins |
| Write | Write + Admin |
| Contributor | Contributor + Write + Admin |
| Read+ | Any org member |

UI-only note: non-admin members who create a Resource Group via UI are automatically added as admin. Via API, this does NOT happen automatically — API callers must include at least one admin user.

## Cost Attribution (Enterprise)

Resource Groups serve as cost attribution units:

| Service | How attribution works |
|---------|----------------------|
| Spaces | Automatically attributed to the group the Space belongs to |
| Jobs | Pass `namespace` = resource group ID |
| Inference Providers | `X-HF-Bill-To` header or `bill_to` SDK param |
| Inference Endpoints | Automatically attributed to the group the model belongs to |

Dedicated API endpoint available to retrieve cost attribution data.

## Resource Groups API

### Authentication

Create a fine-grained token with "Write access to organizations settings / member management" permission scoped to your org at `https://huggingface.co/settings/tokens`.

```
Authorization: Bearer <your_access_token>
```

Base URL: `https://huggingface.co`

### List Resource Groups

```http
GET /api/organizations/{org_name}/resource-groups
```

Example response:
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "name": "Cohort 2024",
    "description": "Members in this group",
    "users": [...],
    "repos": [...]
  }
]
```

### Add Users to a Resource Group

```http
POST /api/organizations/{org_name}/resource-groups/{resource_group_id}/users
Content-Type: application/json

{
  "users": [
    { "user": "member1", "role": "read" },
    { "user": "member2", "role": "read" }
  ]
}
```

### Change Member Role (Org + Resource Groups)

```http
PUT /api/organizations/{org_name}/members/{username}/role
Content-Type: application/json

{
  "role": "read",
  "resourceGroups": [
    { "id": "507f1f77bcf86cd799439011", "role": "read" }
  ]
}
```

If `resourceGroups` is omitted or `[]`, the user is removed from all resource groups.

### Resolve Email to Username

```http
GET /api/organizations/{org_name}/members?email={email}&limit=1
```

Only works when the email domain matches the org's allowed domains.

### Auto-Join API

Enable/disable auto-join on a Resource Group via the programmatic access control API.

### Error Codes

| Code | Meaning |
|------|---------|
| 400 | Invalid body (invalid role, bad resource group ID) |
| 402 | Org has no subscription |
| 403 | Not allowed (lacks Write on org, or resource group not in org) |
| 404 | Organization or user not found |

## Python Example — Change Member Role

```python
import os
import requests

BASE_URL = "https://huggingface.co"
HF_TOKEN = os.environ.get("HF_TOKEN", "")

def change_member_role(org_name, username, role, resource_groups=None):
    payload = {"role": role, "resourceGroups": resource_groups or []}
    r = requests.put(
        f"{BASE_URL}/api/organizations/{org_name}/members/{username}/role",
        headers={"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"},
        json=payload,
    )
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()
```

## Bash Example — Add Users from Email List

```bash
ORG_NAME="my-org"
RG_ID="507f1f77bcf86cd799439011"
EMAIL="member@org.com"

# Step 1: resolve email to username
MEMBERS=$(curl -s -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/organizations/$ORG_NAME/members?email=$EMAIL&limit=1")
USERNAME=$(echo "$MEMBERS" | jq -r '(.[0] // {} | .user // "")')

# Step 2: add to resource group
curl -s -X POST -H "Authorization: Bearer $HF_TOKEN" -H "Content-Type: application/json" \
  -d "{\"users\":[{\"user\":\"$USERNAME\",\"role\":\"read\"}]}" \
  "https://huggingface.co/api/organizations/$ORG_NAME/resource-groups/$RG_ID/users"
```

## Key Differences from Gated Repos

| Feature | Gated Repos | Resource Groups |
|---------|-------------|-----------------|
| Scope | Per-repo access requests | Org-level team-based access |
| Plan required | Free + PRO | Team / Enterprise |
| User-facing | Users request access | Admins assign members |
| Auto-approval | Configurable per repo | Auto-join on groups |
| Multi-repo grouping | No | Yes |
| Cost attribution | No | Yes (Enterprise) |

## References

- Official docs: https://huggingface.co/docs/hub/main/security-resource-groups
- Programmatic access API: https://huggingface.co/docs/hub/main/programmatic-user-access-control
- Team & Enterprise plans: https://huggingface.co/docs/hub/teams-and-enterprise
