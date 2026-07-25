# HF Learnings: Gated Repositories — Deep Dive (2026-07-24)

## Topic: hf-hub-gated-repos (Deep Dive #2 — Gating Group Collections, Notifications, Advanced Settings)

### Summary
Comprehensive deep-dive into Hugging Face Hub gated repositories, covering new features beyond the baseline SKILL.md: Gating Group Collections (Team/Enterprise), notification frequency configuration, gate form UI customization (`extra_gated_heading`, `extra_gated_description`, `extra_gated_button_content`), location-based enforcement (Enterprise Plus), and the full lifecycle of access revocation.

### New Insights Beyond the SKILL

---

### 1. Gating Group Collections (Team & Enterprise)

**What it is:** Organizations on Team/Enterprise plans can create a **Gating Group Collection** — a collection where granting access to ONE repo grants access to ALL models and datasets in the collection. Users request access once.

**Requirements:**
- Collection owner must be an **organization** (not a user)
- Organization must be on Team or Enterprise plan
- All models/datasets in the collection must be owned by the **same organization**
- Each repo can belong to at most **one Gating Group Collection** (but can be in unlimited regular collections)
- Only models and datasets are gated — Spaces and Papers in the collection are unaffected

**How to enable:**
1. Go to the collection page
2. Click "Gating group" in bottom-right corner
3. Click "Configure Access Requests"
4. Choose Automatic approval or Manual Review

**User experience:** A Gating Group Collection shows a special icon. Users submit ONE access request on any repo in the collection and get access to all repos (including future ones added to the collection).

**Customization limit:** Gate parameters (`extra_gated_fields`, `extra_gated_prompt`) must be configured **per-repo** — there is no centralized way to set collection-wide gate parameters. You must keep the YAML in sync across all repos manually.

---

### 2. Notification Configuration

Both per-repo gating and Gating Group Collections support notification settings:

| Setting | Options | Default |
|---------|---------|---------|
| Notification frequency | `once a day` or `real-time` | Once a day (for manual approval) |
| Notification email | Custom email address | Primary email (user) or first 5 org admins |

Configured in the repo's gating settings, under "Notification frequency" and "Notifications email" fields.

---

### 3. Gate Form UI Customization

Beyond `extra_gated_fields` and `extra_gated_prompt`, three YAML fields customize the gate form's appearance:

```yaml
---
gated: true
extra_gated_heading: "Acknowledge license to accept the repository"
extra_gated_description: "Our team may take 2-3 days to process your request"
extra_gated_button_content: "Acknowledge license"
---
```

| Field | Purpose | Default |
|-------|---------|---------|
| `extra_gated_heading` | Custom heading above the form | "Access this repository" |
| `extra_gated_description` | Description shown to users | (none) |
| `extra_gated_button_content` | Button label | "Agree and send request to access repo" |

---

### 4. Location-Based Enforcement (Enterprise Plus)

Enterprise Plus organizations can set **Advanced Gating** policies in Publisher Analytics settings:

**Enforcement levels:**
| Level | Behavior |
|-------|----------|
| **Gated repositories** | Access requests from blocked locations are auto-rejected for all org's gated repos |
| **All repositories** | Auto-reject + deny downloads from ALL repos (including public). Blocked visitors see "not available in your region" on repo page. Dataset viewer disabled. |

**Blocked locations:**
- **Blocked countries** — by ISO 3166-1 alpha-2 code
- **Blocked regions** — specific territories not covered by country list

**Important:** Enforcement applies to all visitors from blocked locations, **including signed-in users and org members** (no exemption).

---

### 5. Access Revocation Lifecycle

Key lifecycle rules:
- **Authors can reject at any time** — even users who were auto-approved can be rejected later
- **Rejected users cannot re-request** — they must first be moved back to "pending" (via `cancel_access_request` / "Cancel" in UI)
- **Rejection reason** is visible to the user (max 200 chars)
- **Granting access** (`grant_access`) works without a prior pending request — useful for external approval flows (e.g., payment, external website)

---

### 6. Dataset Gating Notes

Dataset gating is **identical** to model gating in functionality, with two differences:
1. **API base path:** `/api/datasets/{repo_id}/` instead of `/api/models/{repo_id}/`
2. **Python SDK:** Same method names (`accept_access_request`, `list_pending_access_requests`, etc.) — pass a dataset `repo_id`

---

### 7. API Reference (Updated)

**REST API:**

| Method | Endpoint (Models) | Endpoint (Datasets) |
|--------|------------------|-------------------|
| GET | `/api/models/{repo_id}/user-access-request/pending` | `/api/datasets/{repo_id}/user-access-request/pending` |
| GET | `/api/models/{repo_id}/user-access-request/accepted` | `/api/datasets/{repo_id}/user-access-request/accepted` |
| GET | `/api/models/{repo_id}/user-access-request/rejected` | `/api/datasets/{repo_id}/user-access-request/rejected` |
| POST | `/api/models/{repo_id}/user-access-request/handle` | `/api/datasets/{repo_id}/user-access-request/handle` |
| POST | `/api/models/{repo_id}/user-access-request/grant` | `/api/datasets/{repo_id}/user-access-request/grant` |

**Python huggingface_hub methods** (all accept both model and dataset `repo_id`):

| Method | Purpose |
|--------|---------|
| `api.list_pending_access_requests(repo_id)` | List pending requests |
| `api.list_accepted_access_requests(repo_id)` | List accepted users |
| `api.list_rejected_access_requests(repo_id)` | List rejected users |
| `api.accept_access_request(repo_id, user)` | Accept a user |
| `api.reject_access_request(repo_id, user, reason)` | Reject with optional reason (max 200 chars) |
| `api.cancel_access_request(repo_id, user)` | Move back to pending (un-reject) |
| `api.grant_access(repo_id, user)` | Grant without prior request |

### Resources
- Gated models: https://huggingface.co/docs/hub/en/models-gated
- Gated datasets: https://huggingface.co/docs/hub/en/datasets-gated
- Gating Group Collections: https://huggingface.co/docs/hub/en/enterprise-gating-group-collections
- huggingface_hub source: https://github.com/huggingface/huggingface_hub (HfApi class)
