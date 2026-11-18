# Unified Agentic Integration Platform Specification

## 1. Overview
This specification defines the architecture for the **Unified Agentic Integration Platform** (`app/agent_platform`), consolidating all systems, tools, and protocols explored in this session:
1. **Superpowers Discipline & TDD** (`superpowers:using-superpowers`, `writing-plans`)
2. **Antigravity Customization Architecture** (`agy-customizations`)
3. **Google Antigravity Python SDK** (`google-antigravity-sdk`)
4. **Google ADK & CLI Agent Engine** (`google-agents-cli-adk-code`)
5. **Accidental Data Loss Prevention Guardrails** (`data-agent-kit-plugin:accidental-data-loss-prevention`)
6. **Jules Asynchronous Delegated Development** (`gemini-cli-jules:jules`)
7. **Isolated Dependency Management Engine** (`data-agent-kit-plugin:managing-python-dependencies`)
8. **Harness Custom AI Agent Pipeline Exporter** (`harness-antigravity:agents:create-agent`)

---

## 2. Global Constraints
- Python version floor: Python 3.11+.
- Zero global `pip install` commands. All Python environments must use explicit virtual environment binaries (`.venv/bin/python`, `.venv/bin/pip`) or package manager commands (`uv`, `poetry`, `pipenv`, `conda`).
- Mandatory pre-execution halt on destructive commands (`rm -rf`, `DROP TABLE`, `DELETE FROM`, `TRUNCATE`, `gsutil rm`, `bq rm`) unless accompanied by explicit approval token.
- Strict UID formatting for Harness AI agents: prefix `ca_` followed by lowercase alphanumeric characters and single underscores (`ca_<slug>`).
- Progressive disclosure for skills: metadata and summaries loaded first; full `SKILL.md` body loaded only upon explicit invocation.
- Deterministic TDD workflow: 100% test coverage with verifiable fail-then-pass assertions for every module.

---

## 3. Subsystem Architecture

### 3.1. Safety & Data Loss Prevention (`app/agent_platform/safety.py`)
- **Class**: `DataLossGuardrail`
- **Responsibilities**:
  - Analyze shell command strings and SQL statements against destructive AST patterns and keywords.
  - Return `SafetyCheckResult(is_destructive=bool, reason=str, impact=str)`.
  - Block execution if destructive unless an `approval_token` matching the operation is provided.

### 3.2. Reactive Dependency Manager (`app/agent_platform/dep_manager.py`)
- **Class**: `DependencyManagerDetector`
- **Responsibilities**:
  - Reactively detect package managers in order: `uv` (`uv.lock` or `pyproject.toml[tool.uv]`) -> `poetry` (`pyproject.toml[tool.poetry]`) -> `pipenv` (`Pipfile`) -> `conda` (`environment.yml`) -> `venv+pip` (`requirements.txt`) -> default `venv+pip`.
  - Return `DependencyConfig(manager=str, install_cmd=str, sync_cmd=str, run_prefix=str)`.
  - Prohibit global installs; enforce explicit virtual environment paths.

### 3.3. Antigravity Customizations Registry (`app/agent_platform/customizations.py`)
- **Class**: `CustomizationRegistry`
- **Responsibilities**:
  - Hierarchically discover rules (`AGENTS.md`, `GEMINI.md`) walking up from a target file to the workspace root.
  - Parse and index skills (`SKILL.md`), supporting progressive disclosure (name + description metadata vs full instructions).
  - Execute lifecycle hooks (`pre_tool`, `post_tool`, `stop`).

### 3.4. Jules Asynchronous Delegated Worker (`app/agent_platform/jules_worker.py`)
- **Class**: `JulesWorker`
- **Responsibilities**:
  - Parse git remote URLs into GitHub `owner/repo` format.
  - Build CLI commands for remote Jules session creation (`jules remote new --repo <repo> --session <task>`).
  - Validate patch safety from `.jules/diff.patch` ensuring file targets match current workspace before applying.
  - Generate branch-and-apply commands (`git checkout -b <branch>`, `git apply --index`, `git commit`).

### 3.5. Dual Agent Core Runtime (`app/agent_platform/agent_engine.py`)
- **Class**: `UnifiedAgentRuntime`
- **Responsibilities**:
  - Support configuration for hosted Gemini (`LocalAgentConfig`), on-device LiteRT (`LiteRTAgentConfig`), and Google ADK `Agent`.
  - Register custom python tool callables and dispatch tool execution through `DataLossGuardrail`.
  - Track conversation state, token counts, and tool outcomes.

### 3.6. Harness Custom AI Agent Exporter (`app/agent_platform/harness_exporter.py`)
- **Class**: `HarnessAgentExporter`
- **Responsibilities**:
  - Format agent display names into canonical `ca_<slug>` UIDs.
  - Assemble standard Harness v1 Agent YAML specification (`agent.step.group.steps`, `PLUGIN_TASK`, `PLUGIN_MAX_TURNS`, `PLUGIN_HARNESS_CONNECTOR`, `PLUGIN_ALLOWED_DOMAINS`, `mcpConnectors`, `layout`).
  - Export pipeline snippets for v1 (`template: uses: ca_<slug>@1.0.0`) and v0 (`type: Agent, spec: { agentName: ca_<slug> }`).
