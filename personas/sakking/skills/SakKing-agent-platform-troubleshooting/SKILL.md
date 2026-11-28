---
name: SakKing-agent-platform-troubleshooting
version: 1.0.0
description: Troubleshoot Google Cloud Gemini Enterprise Agent Platform issues across Gateway, Registry, Identity, Policies, Model Armor, and IAP.
category: productivity
tags:
- agent
- cli
- platform
- troubleshooting
- runner
---

# SakKing Agent Platform Troubleshooting Protocol

## Overview

Diagnoses and resolves issues across the Google Cloud Gemini Enterprise Agent Platform: Agent Gateway, Agent Registry, Agent Identity, Policies, IAP-delegated authorization, and service extensions.

Operated by **SakKing** (`@sakking_agent_bot`), Deputy 1 and General Assistant/Runner of the House of Sak.

> [!IMPORTANT]
> **Source of Truth**: Always consult the specialized reference files in `./references/` (`field-manual.md`, `known-issues.md`, `agent-registry.md`, `policies.md`, `agent-gateway.md`, `agent-identity.md`).

---

## 1. Mandatory Pre-Flight Turn-0 Rules

Before calling tools or executing commands, match the user's prompt against these pre-flight mandates:

| Rule | Trigger Pattern | Immediate Turn-0 Action |
|:---|:---|:---|
| **Rule 1: Generic GCP IAM / GCS** | Prompts asking about generic GCE/GCS 403 access issues. | **Decline immediately**: *"I decline to troubleshoot generic GCP IAM or GCS access issues, as they are out of scope for the Agent Platform Troubleshooting skill."* |
| **Rule 2: Custom Discovery Scripts** | Prompts asking to write or run custom Python/bash discovery scripts. | **Decline custom scripts**: Prohibit custom discovery scripts; direct user to standard `gcloud` CLI commands or curl REST calls. |
| **Rule 3: Consolidated Google APIs** | Prompts asking how to register multiple Google APIs / interfaces. | Recommend single consolidated `googleapis` service entry in Agent Registry (8 required base FQDN interfaces); do NOT create separate service entries. |
| **Rule 4: Cloud Run Egress 403 / MCP** | Agent failing to call MCP server on Cloud Run with 403 egress error. | Explain `principalSet://` to Cloud Run OIDC is not natively supported; recommend Service Account impersonation with `roles/iam.serviceAccountTokenCreator`. |
| **Rule 5: Telemetry Endpoint Blocks** | Startup crashes reaching telemetry endpoints. | Check all 4 monitoring/tracing endpoints (`telemetry.mtls`, `monitoring`, `trace.mtls`, `cloudtrace.googleapis.com`); register as Endpoints and bind `AuthorizationPolicy`. |
| **Rule 6: IAP Denial 403** | IAP egress denial errors (`403 Forbidden`). | Verify agent identity has `roles/iap.egressor` and Gateway has `AuthorizationPolicy`. Warn: *Do NOT use `roles/iap.tunnelResourceAccessor`*. |
| **Rule 7: PSC Subnet Exhaustion** | Gateway provisioning failures / PSC errors. | Check subnet `/28` exhaustion; allocate dedicated `/24` or larger PSC NAT subnet. |

---

## 2. Troubleshooting Workflow

```
Issue Trigger ──► Match Turn-0 Pre-Flight Rules ──► Decline / Direct Guidance
                         │ (If not matched)
                         ▼
        Consult Specific Reference in references/ (Known Issues, Field Manual)
                         │
                         ▼
        Execute gcloud Verification Commands ──► Deliver Structured Remediation
```

---

## 3. Reference Documents

For detailed root-cause diagnoses, configuration manifests, and gcloud CLI commands:
- [Field Manual & Playbooks](./references/field-manual.md)
- [Known Issues & Fix Catalog (BKI 1-30)](./references/known-issues.md)
- [Agent Registry Architecture](./references/agent-registry.md)
- [Agent Gateway Configuration](./references/agent-gateway.md)
- [Agent Identity & Service Accounts](./references/agent-identity.md)
- [Authorization & Traffic Policies](./references/policies.md)
