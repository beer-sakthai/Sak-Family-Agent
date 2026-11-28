---
name: SakJules-workflow
version: 1.1.0
description: Master development lifecycle orchestrating models, evaluation, deployment, and monitoring across the 11-phase workflow.
category: devops
tags:
- automation
- workflow
---

# SakThai Master Development Workflow Protocol

Orchestrates all domain skills, CLI commands, and quality gates across the end-to-end 11-phase model development cycle.

## 1. Development Principles
- **Zero Cost Invariant**: Training and compute must utilize free-tier infrastructure (Kaggle T4, Colab free, HF Spaces).
- **Two-Tier Evaluation**: Every model candidate must pass deterministic benchmark checks (BFCL) before release.
- **Closed Learning Loop**: Every development run must conclude with error analysis and journal capture.

## 2. High-Level Lifecycle Flow
```
Data -> Train -> Eval -> Error Analysis -> Publish -> Deploy -> Discoverability -> Monitor -> Release -> Feedback -> Learn
```

## 3. Phase Checkpoints & Quality Gates
- **Pre-Train**: Verify dataset schemas and formatting.
- **Pre-Publish**: Verify GGUF quantization integrity and test inference generation locally.
- **Pre-Deploy**: Validate configuration files, secrets encryption, and endpoint healthcheck routes.
- **Post-Deploy**: Confirm discoverability tags and monitoring telemetry.

## 4. References & Detailed Guide
- Comprehensive 11-phase breakdown and command lookup tables: [11-Phase Development Cycle](references/11-phase-development-cycle.md)
