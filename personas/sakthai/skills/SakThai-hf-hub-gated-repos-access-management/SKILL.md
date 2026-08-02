---
name: SakThai-hf-hub-gated-repos-access-management
description: "Complete reference on Hugging Face Hub gated repository access management — enabling and configuring gating, managing access requests via UI and API, using the huggingface_hub Python client, and understanding gating group collections for Team & Enter"
---

# HF Hub Gated Repos & Access Management

## Overview

Gating is an access control mechanism on the Hugging Face Hub that requires users to request permission before accessing model or dataset files. Repository authors can configure:

- **Not gated** (`False`) — anyone can access without restriction
- **Automatic approval** (`"auto"`) — users share contact info and get immediate access
- **Manual approval** (`"manual"`) — the repo owner must approve or reject each request

Gating is available for all repo types: **models**, **datasets**, and **Spaces**.

## Enabling/Configuring Gating

### Via the Web UI

1. Go to the repository's **Settings** page
2. Click **"Enable Access request"** in the top-right corner
3. Choose approval mode: **Automatic** or **Manual**
4. (Optional) Configure:
   - **Notification frequency** — once a day or real-time
   - **Notification email** — default is your primary email (for org repos, first 5 admins)
   - **Custom fields** — additional information users must provide when requesting

### Via Python API

```python
from huggingface_hub import HfApi

api = HfApi(token="hf_...")

# Enable automatic gating
api.update_repo_settings("username/my-model", gated="auto")

# Enable manual gating
api.update_repo_settings("username/my-model", gated="manual")

# Disable gating
api.update_repo_settings("username/my-model", gated=False)

# For datasets
api.update_repo_settings("username/my-dataset", gated="auto", repo_type="dataset")

# For Spaces
api.update_repo_settings("username/my-space", gated="manual", repo_type="space")
```

### Via Direct API

```bash
# Enable automatic gating
curl -X PUT "https://huggingface.co/api/repos/{repo_id}/settings" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"gated": "auto"}'

# Enable manual gating  
curl -X PUT "..." -d '{"gated": "manual"}'

# Disable gating
curl -X PUT "..." -d '{"gated": false}'
```

## Managing Access Requests

### Via the Web UI

From the repository **Settings** → **"Review access requests"**:

- **Pending** — users waiting for approval (only with manual mode)
  - **Accept** — grants access
  - **Reject** — denies access permanently (user cannot re-request)
- **Accepted** — users with access
  - **Reject** — revokes access permanently
  - **Cancel** — moves user back to pending
- **Rejected** — permanently denied users

### Via Python API

```python
from huggingface_hub import HfApi

api = HfApi(token="hf_...")

# List pending/accepted/rejected requests
pending = api.list_pending_access_requests("username/my-model")
accepted = api.list_accepted_access_requests("username/my-model")
rejected = api.list_rejected_access_requests("username/my-model")

# Each request is an AccessRequest object:
#   username, fullname, email, timestamp, status, fields

# Accept a pending request
api.accept_access_request("username/my-model", "requesting-user")

# Reject with reason (max 200 chars)
api.reject_access_request(
    "username/my-model",
    "requesting-user",
    rejection_reason="Not eligible for early access"
)

# Cancel approval (move back to pending)
api.cancel_access_request("username/my-model", "already-approved-user")

# Grant access without a prior request
api.grant_access("username/my-model", "specific-user")

# For datasets, pass repo_type="dataset"
api.list_pending_access_requests("username/my-dataset", repo_type="dataset")
api.accept_access_request("username/my-dataset", "user", repo_type="dataset")
```

### Via REST API

| Method | URI | Description |
|--------|-----|-------------|
| `GET` | `/api/models/{repo_id}/user-access-request/pending` | List pending requests |
| `GET` | `/api/models/{repo_id}/user-access-request/accepted` | List accepted requests |
| `GET` | `/api/models/{repo_id}/user-access-request/rejected` | List rejected requests |
| `POST` | `/api/models/{repo_id}/user-access-request/handle` | Change request status |
| `POST` | `/api/models/{repo_id}/user-access-request/grant` | Grant access to a user |

For datasets, replace `/api/models/` with `/api/datasets/`.

Base URL: `https://huggingface.co`

**Handle request payload:**
```json
{
  "status": "accepted",
  "user": "username",
  "rejectionReason": "Optional reason (max 200 chars)"
}
```

Status values: `"accepted"`, `"rejected"`, `"pending"` (to cancel approval).

## AccessRequest Data Class

```python
@dataclass
class AccessRequest:
    username: str        # Hub username (e.g., "julien-c")
    fullname: str        # Display name (e.g., "Julien Chaumond")
    email: str | None    # User's email address
    timestamp: datetime  # When the request was made
    status: Literal["pending", "accepted", "rejected"]
    fields: dict[str, Any] | None  # Custom field values from the request form
```

## Downloading Access Reports

From the repository **Settings**, click **"Download user access report"** to get a JSON file with:

```json
{
  "user": "julien-c",
  "fullname": "Julien Chaumond",
  "status": "accepted",
  "email": "julien@example.com",
  "time": "2024-01-01T00:00:00Z",
  "reviewedAt": "2024-01-02T00:00:00Z"
}
```

Fields:
- `user` — Hub username
- `fullname` — Display name
- `status` — `"pending"`, `"accepted"`, or `"rejected"`
- `email` — User's email
- `time` — When the user made the request
- `reviewedAt` — When the request was reviewed (not set for pending)

## Customizing Request Information

When enabling gating, authors can add **custom fields** that users must fill out when requesting access (e.g., affiliation, intended use case, research purpose). These are displayed in the request form and included in the `fields` attribute of each `AccessRequest`.

## Gating Group Collections (Team & Enterprise)

For Team and Enterprise organizations, **Gating Group Collections** allows:

- Managing multiple gated repositories as a group
- Setting uniform access policies across a collection
- Integration with **Resource Groups** for granular access control
- SCIM compatibility for automated user provisioning
- Consolidated access request management across repos in the collection

This feature is available in the **Team & Enterprise Plans** under the Security section.

## Best Practices

1. **Start with automatic** (`"auto"`) if you just need to collect user contact info without creating friction
2. **Use manual** (`"manual"`) for sensitive models where you need to vet each user
3. **Set a notification email** so you don't miss pending requests
4. **Use custom fields** to understand who's using your model and for what purpose
5. **Download the access report** periodically for compliance/audit purposes
6. **Use the API for automation** — integrate access management into your CI/CD pipeline
7. **For organizations**, assign at least 2 admins to manage access requests to avoid single-person bottlenecks

## Pitfalls

- **Rejected users cannot re-request** — a rejection is permanent. Only use it for abusive/ineligible users.
- **Access is per-user, not per-organization** — individual users must each request access.
- **`False` vs `None`** — `gated=False` explicitly disables gating; `gated=None` (default) leaves the current setting unchanged.
- **Notification emails** for organization repos default to the first 5 admins — configure this if different people handle access management.
- **API tokens** need **write** access to the repository to manage access requests.

## Verification Checklist

- [ ] Gating status can be verified in repo settings UI
- [ ] `update_repo_settings(gated="auto")` enables automatic approval
- [ ] `update_repo_settings(gated="manual")` enables manual approval  
- [ ] `update_repo_settings(gated=False)` disables gating
- [ ] Pending/accepted/rejected lists are accessible via API
- [ ] Accept/reject/cancel/grant operations work correctly
- [ ] Access report downloads as valid JSON
- [ ] Custom fields appear in the request form
