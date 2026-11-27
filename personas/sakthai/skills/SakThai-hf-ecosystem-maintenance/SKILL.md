---
name: SakThai-hf-ecosystem-maintenance
version: 1.0.0
description: HF ecosystem upkeep — download counts, cross-links, low-dl promotion,
  deprecation, Spaces. Complements health-check (finds issues → this fixes them).
category: mlops
tags:
- ecosystem
- hf
- huggingface
- maintenance
---

# HF Ecosystem Maintenance

Systematic upkeep and lifecycle operations for Beer's Hugging Face assets (23 models, 15 datasets, 6 Spaces, 1 collection).

> 📖 **Comprehensive Reference Library**: Consult 36 operational playbooks in [`./references/`](./references/) for deep-dive protocols.

---

## 🛠️ Core Upkeep Workflows

### 1. Refresh Download Counts on Model Cards
Download counts drift as the ecosystem grows. Sync model cards with current API telemetry:
```bash
# 1. Fetch current counts from HF REST API
curl -s -H "Authorization: Bearer $HF_TOKEN"   "https://huggingface.co/api/models?author=Nanthasit&sort=downloads&direction=-1"   -o /tmp/current_models.json

# 2. Download target README
curl -s -H "Authorization: Bearer $HF_TOKEN"   "https://huggingface.co/Nanthasit/<model>/raw/main/README.md" -o /tmp/readme.md

# 3. Patch stale numbers and upload via hf upload
hf upload Nanthasit/<model> /tmp/updated_readme.md README.md
```
*Note: Before editing, verify the model has no active `hf jobs` training commits. See [Active Training Card Overwrite](./references/active-training-card-overwrite.md).*

### 2. Audit & Refresh Collection Notes
Keep `sakthai-model-family` collection items annotated with clear model descriptions and benchmarks:
```bash
# Verify collection items
curl -s "https://huggingface.co/api/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02"   -o /tmp/collection.json
```
*See [Collection Lifecycle Management](./references/collection-lifecycle-management.md) and [Collection Note Refresh](./references/collection-note-refresh.md).*

### 3. Cross-Link Gap Enrichment
Ensure all model cards cross-reference their sibling datasets and quantized variants:
- Connect text models to `sakthai-combined-v6` or `sakthai-context-7b-tools`.
- Verify links resolve to public assets; fix private repo links.
*See [Cross-Link Gap Enrichment](./references/cross-link-gap-enrichment.md) and [Cross-Link Validity Check](./references/cross-link-validity-check.md).*

### 4. Low-Download Model Promotion & Deprecation
- Promote low-download models by cross-linking from high-traffic family flagships.
- Tag obsolete checkpoints with `deprecated` and point users to successor models.
*See [Target Selection Strategies](./references/target-selection-strategies.md) and [Deprecated Model Cross-Reference Cleanup](./references/deprecated-model-cross-reference-cleanup.md).*

---

## 🛡️ Governance & Triple-Gate Invariants
All Hub writes must satisfy SakThai's Triple Gate:
1. SakThai Charge $\ge 50\%$ (Active).
2. No active `deputy-chain` in memory.
3. Explicit `hub-approved` tag from Beer in family memory (`sakthai memory family --tag hub-approved`).

---

## 📚 Essential Reference Playbooks
- [Card Enrichment Patterns](./references/card-enrichment-patterns.md) — Standard markdown templates for model cards.
- [Dataset Card YAML Fixes](./references/dataset-card-yaml-fixes.md) — Valid schema tags and metadata.
- [Space Card Enrichment](./references/space-card-enrichment.md) — Spaces lifecycle and Gradio card layout.
- [Verification Patterns](./references/verification-patterns.md) — Pre-flight card integrity tests.
- [Deleted Repo Cleanup Sweep](./references/deleted-repo-cleanup-sweep.md) — Purging dead cross-links.
