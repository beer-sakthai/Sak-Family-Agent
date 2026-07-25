# HF Hub Audit Logs — Complete Reference

> Researched: 2026-07-25 | Source: huggingface.co/docs/hub/en/audit-logs

## Overview

Audit Logs enable organization admins to review actions taken by members, including membership changes, repository settings, and billing. Each log entry captures: who performed the action, the event type, a description, anonymized IP, and timestamp.

**Availability:** Team & Enterprise plans only (not free-tier). Accessible via organization settings UI or JSON export.

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

## Integration Patterns

Since there is no dedicated public API endpoint for audit logs documented, the primary consumption patterns are:

1. **UI-based review** — Organization admins browse logs through the settings UI
2. **JSON export + external analysis** — Download JSON for SIEM, monitoring, or compliance tooling
3. **Webhook-driven** — Pair with webhooks for real-time notification of repo/org events

The event `type` field (in `scope.action` format) is the key filter — use it to programmatically parse exported logs or to set up targeted webhook monitoring.
