# HF Hub Audit Logs — Complete Reference

> Researched: 2026-07-25 | Source: huggingface.co/docs/hub/en/audit-logs

## Overview

Audit Logs enable organization admins to review actions taken by members, including membership changes, repository settings, and billing. Each log entry captures: who performed the action, the event type, a description, anonymized IP, and timestamp.

**Availability:** Team & Enterprise plans only (not free-tier). Accessible via organization settings UI or JSON export.

**Verified: No public API endpoint.** `huggingface_hub` v1.24.0 has zero audit-log methods. The only programmatic access is via the JSON export download from the org settings UI.

## Event Model

Each action has an **event name** in `scope.action` format (e.g., `repo.create`, `collection.delete`). This `type` field is used for filtering and appears in the JSON export.

### Scopes

| Scope | Description |
|-------|-------------|
| `org` | Organization management & security |
| `repo` | Repository administration |
| `collection` | Collection lifecycle |
| `spaces` | Spaces configuration |
| `resource_group` | Resource group administration |
| `jobs` | Job lifecycle |
| `scheduled_job` | Scheduled job lifecycle |
| `billing` | Payments, subscriptions, cloud marketplaces |

### Organization Management & Security

**Core changes:** `org.create`, `org.delete`, `org.restore`, `org.rename`

**Settings changes** (granular `org.settings.*` — available for actions after June 16, 2026):
- `org.settings.profile` — Profile, storage regions, resource groups, publisher gating
- `org.settings.regions` — Storage region configuration
- `org.settings.resource_groups` — Resource group settings
- `org.settings.publisher_gating` — Publisher gating
- `org.settings.inference_providers`, `.keys.add`, `.keys.remove`, `.usage` — Inference provider config
- `org.settings.sso`, `.enable`, `.disable` — SSO configuration
- `org.settings.security.repo_visibility`, `.2fa.enable`, `.2fa.disable`, `.auto_join.enable`, `.auto_join.disable`, `.members_privacy.enable`, `.members_privacy.disable`
- `org.settings.network`, `.ip_restriction.enable`, `.ip_restriction.disable`, `.auth_enforcement.enable`, `.auth_enforcement.disable`

**Backward compatibility note:** Events before June 16, 2026 use `org.update_settings` (legacy). Integrations parsing `type` should handle both.

**Security management:**
- `org.rotate_token` — API token rotation
- `org.token_approval.enabled`, `.disabled`, `.authorization_request`, `.authorization_request.authorized`, `.authorization_request.revoked`, `.authorization_request.denied`
- `org.sso_login`, `org.sso_join` — SSO logins and joins
- `org.update_join_settings` — Domain-based access config

### Membership & Access Control

- `org.add_user`, `org.remove_user`, `org.change_role`, `org.leave`
- `org.invite_user`, `org.invite.accept`, `org.invite.email`
- `org.join.from_domain`, `org.join.automatic`

### Content & Resource Management

**Repository events:** `repo.create`, `repo.delete`, `repo.move`, `repo.disable`, `repo.removeDisable`, `repo.duplication`, `repo.delete_doi`, `repo.update_resource_group`, `repo.update_settings`, `repo.delete_lfs_file`

**Collections:** `collection.create`, `collection.delete`

**Secrets (per-repo):** `repo.add_secret`, `repo.update_secret`, `repo.remove_secret`, `repo.add_secrets`, `repo.remove_secrets`

**Variables (per-repo):** `repo.add_variable`, `repo.update_variable`, `repo.remove_variable`, `repo.add_variables`, `repo.remove_variables`

**Spaces configuration:** `spaces.add_storage`, `spaces.remove_storage`, `spaces.update_hardware`, `spaces.update_sleep_time`

### Resource Groups

- `resource_group.create`, `resource_group.delete`, `resource_group.settings`
- `resource_group.add_users`, `resource_group.remove_users`, `resource_group.change_role`

### Jobs & Scheduled Jobs

- `jobs.create`, `jobs.cancel`
- `scheduled_job.create`, `scheduled_job.delete`, `scheduled_job.resume`, `scheduled_job.suspend`, `scheduled_job.run`

### Billing & Cloud Integration

**Payment:** `billing.update_payment_method`, `billing.create_customer`, `billing.remove_payment_method`

**Cloud marketplaces:** `billing.aws_add`, `billing.aws_remove`, `billing.gcp_add`, `billing.gcp_remove`, `billing.marketplace_approve`

**Subscriptions:** `billing.start_subscription`, `billing.renew_subscription`, `billing.cancel_subscription`, `billing.un_cancel_subscription`, `billing.update_subscription`, `billing.update_subscription_plan`, `billing.update_subscription_contract_details`

## Export

The complete audit log can be downloaded as JSON from the organization settings UI. The export itself is recorded as `org.audit_log.export` (not shown in the default UI view).

### Known JSON Export Fields

Based on the UI column structure documented by HF, each exported entry includes:

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Event name in `scope.action` format — primary filter key |
| `actor` | string | Who performed the action (username) |
| `description` | string | Human-readable summary of the change |
| `timestamp` | ISO 8601 | When the action occurred |
| `ip` | string | Anonymized IP address |
| `location` | string | Geolocation derived from IP |

The exact field names in the JSON download may differ from the table above; always inspect the first export to confirm schema before building automation.

## Audit Logs vs Webhooks — Coverage Comparison

Audit Logs and Webhooks are complementary monitoring tools. This table maps what each covers:

| Event Category | Audit Logs | Webhooks | Notes |
|----------------|:----------:|:--------:|-------|
| Org management & security | ✅ All events | ❌ Not available | Webhooks don't fire for org-level changes |
| Membership changes | ✅ All events | ❌ Not available | No webhook event for add/remove/role |
| Billing & subscriptions | ✅ All events | ❌ Not available | Financial events are audit-only |
| Resource groups | ✅ All events | ❌ Not available | |
| Repo create/delete/move | ✅ All events | ✅ `repo.update` | Webhooks provide real-time notification; audit logs provide history |
| Repo settings changes | ✅ All events | ✅ `repo.update` (config) | Webhooks include `config` object for changed keys |
| Secrets/variables | ✅ All events | ❌ Not available | Security-sensitive — audit-only for privacy |
| Spaces hardware/sleep | ✅ All events | ✅ `repo.update` (config) | Webhook payload includes hardware change |
| Code pushes | ❌ Not available | ✅ `repo.update` (code) | Only webhooks capture commit-level changes |
| Discussions & PRs | ❌ Not available | ✅ `discussion` | Only webhooks capture discussion/PR events |
| Comments | ❌ Not available | ✅ `comment` | Only webhooks capture new comments |

**Key takeaway:** Audit Logs and Webhooks have **zero overlap**. They cover disjoint event sets. A comprehensive monitoring strategy requires both:
- **Webhooks** for real-time repo, discussion, and code activity
- **Audit logs** (periodic export) for org management, security, billing, and compliance

## Automation Patterns

### Pattern 1: Periodic Export + Compliance Analysis

Since there is no real-time API, the recommended approach is a scheduled job:

```python
# Pseudocode — adapt paths to your org
# 1. Authenticate with a token that has org admin rights
# 2. Download JSON export from org settings (manual step, no API)
# 3. Parse and analyze:
import json

with open("audit_log_export.json") as f:
    entries = json.load(f)

# Filter for critical events
critical_scopes = {"org.add_user", "org.remove_user", "org.change_role",
                   "billing.*", "org.settings.security.*",
                   "repo.add_secret", "repo.remove_secret"}

alerts = [e for e in entries
          if any(e["type"].startswith(s.rstrip("*").rstrip("."))
                 for s in critical_scopes)]

if alerts:
    # Send to monitoring/SIEM
    for alert in alerts:
        print(f"[ALERT] {alert['type']} by {alert['actor']} at {alert['timestamp']}")
```

### Pattern 2: Webhook + Audit Log Correlation

For comprehensive org security monitoring:

1. **Webhooks** — Capture real-time repo events via a handler Space or HTTPS endpoint
2. **Audit Log export** — Download weekly (or after any security-sensitive action)
3. **Correlation** — Cross-reference webhook timestamps with audit log timestamps to build a complete activity timeline

### Pattern 3: Change Detection

Track changes to audit log export hashes to detect unauthorized configuration drift:

```bash
# Store baseline hash
sha256sum audit_log_export.json > baseline.hash

# On next export, compare
sha256sum -c baseline.hash || echo "Audit log changed — review new entries"
```

## Security Monitoring Playbook

Recommended response to common critical events:

| Event | Severity | Response |
|-------|----------|----------|
| `org.add_user` + `org.change_role` (to admin) | Critical | Verify with org owner; check if expected onboarding |
| `org.settings.security.2fa.disable` | Critical | Re-enable immediately; investigate who and why |
| `org.settings.inference_providers.keys.add` | High | Verify the key belongs to an approved provider; audit usage |
| `repo.add_secret` | Medium | Confirm secret belongs to the repo's service; rotate if suspicious |
| `billing.cancel_subscription` | High | Check with billing contact; may be planned or unauthorized |
| `org.rotate_token` | High | Confirm rotation was planned; check for related compromise indicators |

## Integration Patterns

Since there is no dedicated public API endpoint for audit logs documented, the primary consumption patterns are:

1. **UI-based review** — Organization admins browse logs through the settings UI
2. **JSON export + external analysis** — Download JSON for SIEM, monitoring, or compliance tooling
3. **Webhook-driven** — Pair with webhooks for real-time notification of repo/org events (note: webhooks do NOT cover org management, billing, or security events — only audit logs cover those)

The event `type` field (in `scope.action` format) is the key filter — use it to programmatically parse exported logs or to set up targeted webhook monitoring.

## Verified Constraints

- **`huggingface_hub` v1.24.0:** No `audit` methods exist on `HfApi`
- **`hf` CLI:** No audit log commands available
- **Webhooks:** Do not fire for org-level, billing, or resource group events — only for repo, discussion, and comment activity
- **Rate limit:** Webhooks are limited to 1,000 triggers per 24 hours (upgradable via PRO/Team/Enterprise)
