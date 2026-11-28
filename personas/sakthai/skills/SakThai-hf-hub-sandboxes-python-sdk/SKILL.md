---
name: SakThai-hf-hub-sandboxes-python-sdk
version: 1.1.0
description: Remote execution, code sandboxing, and Landlock container management protocol using Hugging Face Hub Sandboxes Python SDK.
category: mlops
tags:
- cloud
- compute
- hf
- hub
- huggingface
- huggingface-hub
- isolation
- jobs
- python
- remote-execution
- sandboxes
- sdk
---

# Hugging Face Sandboxes Python SDK Protocol

Operational protocol for provisioning, orchestrating, and executing code within remote Hugging Face cloud sandboxes via `huggingface_hub` (v1.24.0+).

## 1. Core Concepts & Operating Modes
- **Dedicated Sandbox (`Sandbox.create`)**: Full VM job isolation for GPU/heavy compute.
- **Pooled Sandboxes (`SandboxPool`)**: Fast ephemeral execution sharing a VM via Linux Landlock + UID isolation.
- **Zero Local Footprint**: Code runs on remote infrastructure via `sbx-server` static HTTP daemon.

## 2. Standard Workflow
1. **Provision**: Instantiate `Sandbox.create(hardware=...)` or acquire from `SandboxPool`.
2. **Transfer**: Upload input datasets, scripts, or wheels via `sandbox.upload_file`.
3. **Execute**: Run non-interactive or streaming commands with `sandbox.run(...)`.
4. **Collect & Terminate**: Download output artifacts and call `sandbox.terminate()` to prevent idle compute costs.

## 3. References & Deep Dive Guides
- Full architecture, SDK methods, and Landlock isolation: [Sandboxes Architecture](references/sandboxes-sdk-architecture.md)
- HF Learning Notes: [HF Learnings](references/hf-learnings.md) | [Sandboxes Learnings](references/SakThai-hf-hub-sandboxes_hf-learnings.md)
