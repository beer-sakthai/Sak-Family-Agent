---
name: SakKing-agent-platform-deploy
version: 1.0.0
description: Deploy open models from Model Garden to Agent Platform endpoints and manage undeployment and endpoint lifecycle.
category: productivity
tags:
- agent
- cli
- deploy
- platform
- runner
---

# SakKing Agent Platform Deploy Protocol

## Overview

Deploys open models (Gemma, Llama, custom fine-tunes) from Model Garden to Agent Platform endpoints, monitors async deployment operations, and performs endpoint cleanup.

Operated by **SakKing** (`@sakking_agent_bot`), Deputy 1 and General Assistant/Runner of the House of Sak.

---

## 1. Safety Tiers & Execution Gates

Before running mutating commands, SakKing enforces strict safety confirmation tiers:

| Tier | Operations | Policy |
|:---|:---|:---|
| **Tier R (Read-Only)** | `list`, `describe`, `list-deployment-config` | Execute immediately to gather information. |
| **Tier M (Mutating)** | `deploy`, `undeploy-model` | Requires explicit user confirmation before executing. |
| **Tier D (Destructive)** | `delete` | Requires explicit typed confirmation ("I confirm"). |

---

## 2. Deployment Protocol Summary

```
Model Garden Query ──► Match Deployment Config (Machine Type / GPU)
                              │
                              ▼
          Create Endpoint ──► Deploy Model (Tier M Approval)
                              │
                              ▼
          Poll Operation Status ──► Verify Inference Health
```

1. **Query Model Garden**: Inspect deployment configurations for target model and region.
2. **Create Endpoint**: Provision endpoint resource in target GCP region.
3. **Deploy Model**: Submit deployment operation with appropriate machine type (`g2-standard-8`, L4/A100).
4. **Monitor**: Poll async operation until status reaches `done: true`.
5. **Undeploy / Cleanup**: Clean up endpoints when testing is complete.

---

## 3. Reference Documents

For complete gcloud command recipes, copy-deploy guides, and endpoint manifests:
- [Deployment Commands Reference](./references/deployment_commands.md)
- [1P Tuned Model Copy & Deployment Guide](./references/copy_deploy_guide.md)
- [Usage Guidelines](./references/usage.md)
