# 🚀 Sak-Family-Agent: Comprehensive System Documentation

---

## 1. Executive Summary & Core Philosophy

**Sak-Family-Agent** is an autonomous, multi-agent software engineering framework powered by Gemini CLI. Designed for high-reliability environments, it enforces a strict **Research → Strategy → Execution** lifecycle backed by fail-closed safety, git checkpointing, and rigorous verification gates.

### Core Principles
- **Context Efficiency:** Strategic tool usage and sub-agent delegation to minimize token consumption and maintain clean session histories.
- **Evidence Before Assertions:** Mandatory testing and validation (`verification-before-completion`) before claiming task completion.
- **Modular Extensibility:** Powered by modular skill packs and Model Context Protocol (MCP) servers.

---

## 2. System Architecture & Directory Structure

```
Sak-Family-Agent/
├── .agent/workflows/       # Orchestration workflows (cook, quickfix, feature, etc.)
├── docs/                   # Persistent knowledge base and documentation
│   ├── solutions/          # Solved problems and patterns
│   ├── decisions/          # Architecture Decision Records (ADRs)
│   └── architecture/       # System topology and design specs
├── plans/                  # Staged implementation plans
├── todos/                  # Tracked work items
└── src/                    # Application source code
```

---

## 3. Core Tooling Reference

Sak-Family-Agent interacts with the workspace and external environment through granular, purpose-built tools:

| Category | Tools | Purpose |
|----------|-------|---------|
| **File Operations** | `read_file`, `write_file`, `replace`, `glob`, `grep_search`, `list_directory` | Surgical code exploration and editing |
| **Execution & Process** | `run_shell_command`, `list_background_processes`, `read_background_output` | Command execution and background daemon management |
| **Version Control** | `kit_create_checkpoint`, `kit_restore_checkpoint`, `kit_list_checkpoints` | Workspace snapshots and instant rollback |
| **Team & Orchestration** | `kit_team_start`, `kit_team_status`, `kit_run_workflow`, `kit_handoff_agent` | Multi-agent collaboration and workflow automation |

---

## 4. Specialized Skills Ecosystem

Skills extend the agent's capabilities with domain-specific operating procedures:

- **Engineering Superpowers:** `brainstorming`, `writing-plans`, `executing-plans`, `systematic-debugging`, `test-driven-development`, `verification-before-completion`.
- **Security & Vulnerability:** `security-patcher`, `poc`, `dependency-manager`.
- **Cloud Infrastructure (Azure):** `azure-deploy`, `azure-prepare`, `azure-validate`, `azure-kubernetes`, `azure-compute`, `azure-storage`, `azure-enterprise-infra-planner`.
- **AI & Machine Learning (Hugging Face / Foundry):** `hf-cli`, `huggingface-gradio`, `huggingface-spaces`, `huggingface-zerogpu`, `train-sentence-transformers`, `trl-training`, `microsoft-foundry`, `genkit`.
- **OmA Orchestration:** `oma-goal`, `oma-team`, `oma-ralph`, `oma-autopilot`, `oma-checkpoint`, `oma-team-assemble`.

---

## 5. Model Context Protocol (MCP) Integrations

External tool bridges expanding agent capabilities beyond local execution:

- **Browser & UI Testing:** Puppeteer / Chrome DevTools MCP for headless browser automation, screenshots, and visual diffs.
- **AI UI Prototyping:** Stitch MCP (`stitch_create_project`, `stitch_generate_screen_from_text`, `stitch_update_screen`) for generating and iterating on frontend designs.
- **Cloud Resource Management:** Azure ARM, App Service, Cosmos, Key Vault, Container Apps, AKS, and Search MCP routers.
- **Vulnerability & Code Analysis:** OSV Scanner MCP for dependency vulnerability analysis.

---

## 6. Operational Workflows & Quality Gates

### Execution Pipeline
1. **Explore & Plan:** Use `/plan` or `ralplan` to design stage-gated implementation strategies.
2. **Execute:** Delegate to specialized sub-agents (`coder`, `debugger`, `backend-specialist`, `frontend-specialist`) via `@generalist` or team workflows (`/team start`, `/team run cook`).
3. **Verify:** Run typecheck, unit tests, and linting (`verification-before-completion`).
4. **Document:** Run `/compound` to record solved problems into `docs/solutions/`.
