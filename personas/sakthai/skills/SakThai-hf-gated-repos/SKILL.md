---
name: SakThai-hf-gated-repos
description: "Hugging Face Hub Gated Repositories — configure, manage, and programmatically approve access for gated models and datasets, including custom field forms, EU restrictions, the REST API, and the huggingface_hub Python library methods"
---

# HF Hub Gated Repositories

Trigger when: user asks about gated models/datasets, access control, granting/reviewing access requests, configuring gated repos, `extra_gated_fields`, programmatic access management, or EU access restrictions on the Hub.

## Overview

Gated repositories on the Hugging Face Hub allow model/dataset authors to require users to share their contact information (username + email) or answer custom questions before gaining access. Access can be **auto-approved** (immediate) or **manually reviewed**.

Both **models** and **datasets** support gating, with identical APIs and configuration options. Spaces do NOT support gating.

**Key concepts:**
- **Automatic approval** — default; any user gets access immediately after filling the form
- **Manual approval** — author must explicitly accept each request
- **Gating Group Collections** (Team/Enterprise) — grant/reject access to a collection of repos at once
- **EU disallowed** — optional flag to restrict access from EU countries based on IP geolocation

---

## Configuring a Gated Repository

### Enabling Gating

Via the **Hub UI**: Settings → Gating → "Enable Access request"

Or via **model/dataset card YAML metadata** (does NOT enable gating — only configures the form):

```yaml
---
license: mit
gated: true
extra_gated_prompt: "You agree to not use this model for harmful purposes."
extra_gated_fields:
  Company: text
  Country: country
  I agree to non-commercial use ONLY: checkbox
  Intended use:
    type: select
    options:
      - Research
      - Education
      - label: Other
        value: other
extra_gated_heading: "Custom heading for the gate form"
extra_gated_description: "Custom description shown to users"
extra_gated_button_content: "Agree & Request Access"
---
```

**Note:** `gated: true` in YAML does NOT auto-enable gating — it must be turned on via the UI settings. The YAML fields only customize the form shown to users **after** gating is enabled.

### Field types for `extra_gated_fields`

| Type | Description |
|------|-------------|
| `text` | Single-line text input |
| `checkbox` | Checkbox (boolean) |
| `date_picker` | Date picker |
| `country` | Country dropdown (ISO 3166-1 alpha-2) |
| `select` | Dropdown with custom options list |

For `select` fields, use the `options` key with an array of strings or `{label, value}` objects:

```yaml
  Custom select:
    type: select
    options:
      - Option A
      - Option B
      - label: Option C
        value: opt_c
```

### Restricting EU Access

Add to model/dataset card metadata:

```yaml
---
gated: true
extra_gated_eu_disallowed: true
---
```

This blocks access requests from IP addresses geolocated to EU countries. Only works when `gated: true` is already enabled.

### Global Fields

The Hub automatically collects the user's **username** and **email** in every gate form. Custom fields are added via `extra_gated_fields` in the card metadata.

---

## Reviewing Access Requests (Author/Admin)

### Via the Hub UI

Settings → "Review access requests" → modal with three lists:
- **Pending** — users waiting for approval (only when manual approval)
- **Accepted** — users with access; can reject or cancel (move to pending)
- **Rejected** — blocked users; cannot request again

### Via the REST API

Base URL: `https://huggingface.co`
Auth: Bearer token with **write** access to the repo

**Models:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/models/{repo_id}/user-access-request/pending` | List pending |
| `GET` | `/api/models/{repo_id}/user-access-request/accepted` | List accepted |
| `GET` | `/api/models/{repo_id}/user-access-request/rejected` | List rejected |
| `POST` | `/api/models/{repo_id}/user-access-request/handle` | Change status |
| `POST` | `/api/models/{repo_id}/user-access-request/grant` | Grant to user |

**Datasets:** Same paths, replace `/api/models/` with `/api/datasets/`.

**Handle payload:**
```json
{
  "status": "accepted",
  "user": "username",
  "rejectionReason": "Optional, max 200 chars"
}
```

Valid status values: `"accepted"`, `"rejected"`, `"pending"`

**Grant payload:**
```json
{
  "user": "username"
}
```

### Via the Python SDK (`huggingface_hub`)

```python
from huggingface_hub import HfApi
api = HfApi(token="hf_...")

# List access requests
pending = api.list_pending_access_requests("meta-llama/Llama-2-7b")
accepted = api.list_accepted_access_requests("meta-llama/Llama-2-7b")
rejected = api.list_rejected_access_requests("meta-llama/Llama-2-7b")

# Handle a request
api.accept_access_request("meta-llama/Llama-2-7b", "some_user")
api.reject_access_request("meta-llama/Llama-2-7b", "some_user",
                          reason="Does not meet criteria")
api.cancel_access_request("meta-llama/Llama-2-7b", "some_user")  # → pending

# Grant access without a prior request
api.grant_access("meta-llama/Llama-2-7b", "some_user")
```

For **datasets**, same methods but pass a dataset repo_id:

```python
api.accept_access_request("bigcode/the-stack-v2-dedup", "some_user")
```

### Download Access Report

Click the "Download user access report" button in the Settings UI → downloads a JSON array:

```json
[
  {
    "user": "julien-c",
    "fullname": "Julien Chaumond",
    "status": "accepted",
    "email": "j@huggingface.co",
    "time": "2024-01-15T10:30:00Z",
    "reviewedAt": "2024-01-15T11:00:00Z"
  }
]
```

---

## Accessing Gated Repositories (End User)

### Requesting Access

Must be logged in to a HF account. Visit the model/dataset page → fill the form → submit. You must share your username and email (plus any custom fields).

- **Automatic approval** → immediate access
- **Manual approval** → wait for author to accept

### Downloading Files

**Authentication is required** to download from gated repos. Options:

1. **`hf auth login`** (CLI) — saves token to `~/.cache/huggingface/token`
2. **`login()`** in Python:
   ```python
   from huggingface_hub import login
   login(token="hf_...")  # or interactive
   ```
3. **`token` parameter** in library methods:
   ```python
   from transformers import AutoModel
   model = AutoModel.from_pretrained("gated-org/model", token="hf_...")
   ```
4. **`huggingface_hub`** download:
   ```python
   from huggingface_hub import hf_hub_download
   path = hf_hub_download("gated-org/model", "model.safetensors",
                          token="hf_...")
   ```

---

## Organization-Level Gating

### Gate Access for Organization Members

For repos under an org, the author can enable "Also gate access for members of {org}".

**Bypasses:** Org admins, repo creator, Resource Group admins
**Must request:** Members with read/contributor/write org role, Resource Group members (non-admin)

### Gating Group Collections (Team/Enterprise)

Enterprise subscribers can create a **Gating Group Collection** to bulk-grant or bulk-reject access to ALL repos in a collection. Configured via the Enterprise dashboard.

---

## Advanced Use Cases

### Programmatic Approval from External Flow

Use case: Meta's Llama 2 approach — users request access on an external website, then the website calls the Hub API to grant access:

```python
from huggingface_hub import HfApi
import os

api = HfApi(token=os.environ["HF_WRITE_TOKEN"])

def grant_if_qualified(username: str, external_check_passed: bool):
    if external_check_passed:
        api.grant_access("meta-llama/Llama-2-7b", username)
        return True
    return False
```

### Payment-Gated Access

Use the Hub API to grant access after a user completes a payment (payment flow happens outside the Hub):

```python
# After payment is confirmed
api.grant_access("organization/paid-model", paying_user)
```

### Self-Service Approval Bot

A cron job that auto-accepts pending requests matching criteria:

```python
from huggingface_hub import HfApi

api = HfApi()
pending = api.list_pending_access_requests("my-org/gated-model")

for req in pending:
    # Auto-accept all — or add custom logic
    api.accept_access_request("my-org/gated-model", req.user)
```

---

## Pitfalls

- **`gated: true` in card YAML does NOT enable gating** — it only customizes the form UI. Gating must be enabled via the Hub Settings page.
- **Gating is repo-specific** — enabling on a model does NOT affect its dataset or vice versa.
- **Rejected users CANNOT re-request** — must be moved back to "pending" (cancel) first if you want to give them another chance.
- **`rejectionReason` is visible to the user** — max 200 characters, visible on the Hub page.
- **Write token required** — for all API access request operations. Read-only tokens will fail with 403.
- **Spaces do NOT support gating** — only models and datasets.
- **Gating is not a security mechanism** — it's a user-information-collection tool. Don't rely on it for true access control of sensitive data. Use **private repos** for that.
- **EU restriction uses IP geolocation** — may not be 100% accurate for VPN/proxy users.
- **Access report download** is a one-button action, not a scheduled export — no API endpoint for programmatic export of the full report.
