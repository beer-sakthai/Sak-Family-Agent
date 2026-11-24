# Workflows & Caveman Integration Audit

An analysis of the integration and compatibility gaps between `sakthai-agent-v2` and the `claude-code-workflows` and `caveman` extensions.

---

## 🔍 Core Findings & Gaps

### 1. Extension Paths & Discovery
* **Current state**: `sakthai/skills.py` scans bundled paths, local `library/`, and `~/.sakthai/extensions/`.
* **Gap**: Gemini/Claude extensions are installed under `~/.gemini/extensions/`. Users must manually copy extensions to run them under SakThai.
* **Recommendation**: Extend the default skill and tool discovery search paths to scan `~/.gemini/extensions/` automatically.

### 2. Namespaced Command Registry
* **Current State**: SakThai supports basic CLI flags and commands.
* **Gap**: No built-in parsing for namespaced commands (`/<plugin>:<command>`) from installed extensions.
* **Recommendation**: Add a command router in `sakthai/agent/registry.py` that intercepts namespaced slash commands and maps them to the appropriate extension tool/agent.

### 3. Native Caveman Mode Support
* **Current State**: `sakthai-understand-caveman` exists as a skill, but there is no runtime toggle to compress outputs.
* **Gap**: To get compressed output, the user must manually request it in natural language.
* **Recommendation**: Introduce a `--caveman [lite|full|ultra]` flag to `sakthai run` that injects the `caveman` compression prompt rules directly into the agent system prompt context.

### 4. Memory Compression Integration
* **Current State**: `sakthai memory sync` dumps raw SQL tables to incremental JSONL files (`facts.jsonl` and `observations.jsonl`).
* **Gap**: The JSONL files are not compressed, leading to growing context input sizes over time.
* **Recommendation**: Add a `--compress` flag to `sakthai memory sync` that uses the `caveman-compress` algorithm to shorten prose within facts and observations before committing to Git.

### 5. Delegated Cavecrew Subagents
* **Current State**: Subagents are spawned via `invoke_subagent` using standard `research` or `self` templates.
* **Gap**: No support for token-saving delegated roles (`cavecrew-investigator`, `cavecrew-builder`, `cavecrew-reviewer`).
* **Recommendation**: Register `cavecrew` subagent presets in the subagent definition schema to allow lightweight task execution.

---

## 🛠️ Action Plan

### Phase 1: Command & Path Unification (High Priority)
* Add `~/.gemini/extensions/` to default plugin search paths.
* Implement namespaced slash command parser in the agent loop.

### Phase 2: Native Caveman Runtime (Medium Priority)
* Thread a `--caveman` argument through the provider client configuration.
* Map intensity levels to output trimming rules.

### Phase 3: Sync & Memory Optimization (Low Priority)
* Integrate `caveman-compress` logic directly into the SQLite-to-JSONL export routine in `sakthai memory sync`.
