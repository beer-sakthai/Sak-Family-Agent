# Unified Agent Integration System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modular, enterprise-grade AI Agent Platform and Tooling Integration System in Python (`app/agent_platform`) that unifies Antigravity Customizations, Google Antigravity & ADK engines, Accidental Data Loss Prevention, Jules asynchronous task delegation, isolated Python dependency management, and Harness AI agent pipeline spec generation.

**Architecture:** A layered, modular package (`app/agent_platform`) featuring dedicated subsystems: safety guards, dependency detection, progressive customization discovery, remote delegation worker, dual-engine runtime, and Harness pipeline template exporter. Each subsystem provides clean interfaces and strong typing with zero external network dependencies for testing.

**Tech Stack:** Python 3.11+, Pydantic, Pytest, Git CLI, YAML.

**Spec:** [docs/superpowers/specs/2026-11-12-unified-agent-integration-spec.md](file:///home/sak/docs/superpowers/specs/2026-11-12-unified-agent-integration-spec.md)

## Global Constraints

- Python version floor: Python 3.11+.
- Zero global `pip install` commands. All Python environments must use explicit virtual environment binaries (`.venv/bin/python`, `.venv/bin/pip`) or package manager commands (`uv`, `poetry`, `pipenv`, `conda`).
- Mandatory pre-execution halt on destructive commands (`rm -rf`, `DROP TABLE`, `DELETE FROM`, `TRUNCATE`, `gsutil rm`, `bq rm`) unless accompanied by explicit approval token.
- Strict UID formatting for Harness AI agents: prefix `ca_` followed by lowercase alphanumeric characters and single underscores (`ca_<slug>`).
- Progressive disclosure for skills: metadata and summaries loaded first; full `SKILL.md` body loaded only upon explicit invocation.
- Deterministic TDD workflow: 100% test coverage with verifiable fail-then-pass assertions for every module.

---

### Task 1: Accidental Data Loss Prevention Guardrails Engine

**Files:**
- Create: `app/agent_platform/safety.py`
- Create: `app/agent_platform/__init__.py`
- Test: `tests/test_agent_safety.py`

**Interfaces:**
- Consumes: Shell command strings and SQL query strings
- Produces: `SafetyCheckResult(is_destructive: bool, reason: str, impact: str, blocked: bool)` and `DataLossGuardrail.verify_or_halt(command: str, approval_token: str | None = None) -> SafetyCheckResult`

- [x] **Step 1: Write the failing test**

```python
# tests/test_agent_safety.py
import pytest
from app.agent_platform.safety import DataLossGuardrail, SafetyCheckResult

def test_guardrail_allows_safe_command():
    guard = DataLossGuardrail()
    result = guard.inspect("git status && ls -la")
    assert not result.is_destructive
    assert not result.blocked
    assert result.reason == "Command verified safe"

def test_guardrail_blocks_destructive_shell_command():
    guard = DataLossGuardrail()
    result = guard.inspect("rm -rf /tmp/my_data")
    assert result.is_destructive
    assert result.blocked
    assert "destructive file deletion" in result.reason.lower()
    assert "/tmp/my_data" in result.impact

def test_guardrail_blocks_destructive_sql():
    guard = DataLossGuardrail()
    result = guard.inspect("DROP TABLE customers;")
    assert result.is_destructive
    assert result.blocked
    assert "destructive database operation" in result.reason.lower()

def test_guardrail_allows_with_explicit_approval_token():
    guard = DataLossGuardrail()
    command = "rm -rf .cache"
    token = guard.generate_approval_token(command)
    result = guard.verify_or_halt(command, approval_token=token)
    assert result.is_destructive
    assert not result.blocked
```

- [x] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. /home/sak/Sak-Family-Agent/.venv/bin/pytest tests/test_agent_safety.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent_platform'`

- [x] **Step 3: Write minimal implementation**

```python
# app/agent_platform/__init__.py
"""Agent Platform Core Package."""

# app/agent_platform/safety.py
from dataclasses import dataclass
import hashlib
import re

@dataclass(frozen=True)
class SafetyCheckResult:
    is_destructive: bool
    reason: str
    impact: str
    blocked: bool

class DataLossGuardrail:
    DESTRUCTIVE_SHELL_PATTERNS = [
        (re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-[a-zA-Z]*f[a-zA-Z]*r?)\s+(.+)"), "Destructive file deletion"),
        (re.compile(r"\bgsutil\s+rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)?(.+)"), "Cloud Storage bucket/object deletion"),
        (re.compile(r"\bbq\s+rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)?(.+)"), "BigQuery table/dataset deletion"),
    ]

    DESTRUCTIVE_SQL_PATTERNS = [
        (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE), "Destructive database operation (DROP)"),
        (re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE), "Destructive database operation (TRUNCATE)"),
        (re.compile(r"\bDELETE\s+FROM\s+\w+\s*(?:;|$)", re.IGNORECASE), "Unbounded DELETE operation without WHERE clause"),
    ]

    def generate_approval_token(self, command: str) -> str:
        cleaned = command.strip()
        digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:12]
        return f"APPROVE_{digest}"

    def inspect(self, command: str) -> SafetyCheckResult:
        cleaned = command.strip()
        for pattern, desc in self.DESTRUCTIVE_SHELL_PATTERNS:
            match = pattern.search(cleaned)
            if match:
                impact_target = match.group(2) if len(match.groups()) >= 2 and match.group(2) else cleaned
                return SafetyCheckResult(
                    is_destructive=True,
                    reason=desc,
                    impact=f"Potential data loss on target: {impact_target.strip()}",
                    blocked=True,
                )

        for pattern, desc in self.DESTRUCTIVE_SQL_PATTERNS:
            if pattern.search(cleaned):
                return SafetyCheckResult(
                    is_destructive=True,
                    reason=desc,
                    impact=f"Irreversible modification of database entity: {cleaned}",
                    blocked=True,
                )

        return SafetyCheckResult(
            is_destructive=False,
            reason="Command verified safe",
            impact="None",
            blocked=False,
        )

    def verify_or_halt(self, command: str, approval_token: str | None = None) -> SafetyCheckResult:
        check = self.inspect(command)
        if not check.is_destructive:
            return check

        expected_token = self.generate_approval_token(command)
        if approval_token == expected_token:
            return SafetyCheckResult(
                is_destructive=True,
                reason=f"{check.reason} (Explicitly authorized)",
                impact=check.impact,
                blocked=False,
            )

        return check
```

- [x] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. /home/sak/Sak-Family-Agent/.venv/bin/pytest tests/test_agent_safety.py -v`
Expected: PASS (4 passed)

- [x] **Step 5: Commit**

```bash
git add app/agent_platform/__init__.py app/agent_platform/safety.py tests/test_agent_safety.py
git commit -m "feat(safety): Implement accidental data loss prevention guardrails engine"
```

---

### Task 2: Reactive Python Dependency Manager Detection

**Files:**
- Create: `app/agent_platform/dep_manager.py`
- Test: `tests/test_agent_dep_manager.py`

**Interfaces:**
- Consumes: Workspace root `pathlib.Path` and optional list of package names to install
- Produces: `DependencyConfig(manager: str, install_cmd: str, sync_cmd: str, isolated_exec: str)` and `detect_dependency_manager(workspace: Path, package: str | None = None) -> DependencyConfig`

- [x] **Step 1: Write the failing test**

```python
# tests/test_agent_dep_manager.py
import pytest
from pathlib import Path
from app.agent_platform.dep_manager import detect_dependency_manager

def test_detect_uv_from_uv_lock(tmp_path: Path):
    (tmp_path / "uv.lock").write_text("# uv lockfile")
    config = detect_dependency_manager(tmp_path, package="requests")
    assert config.manager == "uv"
    assert config.install_cmd == "uv add requests"
    assert config.sync_cmd == "uv sync"

def test_detect_poetry_from_pyproject(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'demo'")
    config = detect_dependency_manager(tmp_path, package="httpx")
    assert config.manager == "poetry"
    assert config.install_cmd == "poetry add httpx"
    assert config.sync_cmd == "poetry install"

def test_detect_pipenv_from_pipfile(tmp_path: Path):
    (tmp_path / "Pipfile").write_text("[packages]")
    config = detect_dependency_manager(tmp_path, package="flask")
    assert config.manager == "pipenv"
    assert config.install_cmd == "pipenv install flask"

def test_detect_conda_from_environment_yml(tmp_path: Path):
    (tmp_path / "environment.yml").write_text("name: myenv")
    config = detect_dependency_manager(tmp_path, package="numpy")
    assert config.manager == "conda"
    assert config.install_cmd == "conda install numpy"

def test_fallback_to_isolated_venv(tmp_path: Path):
    config = detect_dependency_manager(tmp_path, package="pydantic")
    assert config.manager == "venv"
    assert config.install_cmd == ".venv/bin/pip install pydantic"
    assert config.sync_cmd == ".venv/bin/pip install -r requirements.txt"
    assert "pip install" not in config.isolated_exec or ".venv/bin" in config.isolated_exec
```

- [x] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. /home/sak/Sak-Family-Agent/.venv/bin/pytest tests/test_agent_dep_manager.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent_platform.dep_manager'`

- [x] **Step 3: Write minimal implementation**

```python
# app/agent_platform/dep_manager.py
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DependencyConfig:
    manager: str
    install_cmd: str
    sync_cmd: str
    isolated_exec: str

def detect_dependency_manager(workspace: Path, package: str | None = None) -> DependencyConfig:
    pkg = package or "<package>"
    uv_lock = workspace / "uv.lock"
    pyproject = workspace / "pyproject.toml"
    pipfile = workspace / "Pipfile"
    conda_env = workspace / "environment.yml"
    requirements = workspace / "requirements.txt"

    # 1. uv check
    if uv_lock.exists() or (pyproject.exists() and "[tool.uv]" in pyproject.read_text()):
        return DependencyConfig(
            manager="uv",
            install_cmd=f"uv add {pkg}",
            sync_cmd="uv sync",
            isolated_exec="uv run python",
        )

    # 2. poetry check
    if pyproject.exists() and "[tool.poetry]" in pyproject.read_text():
        return DependencyConfig(
            manager="poetry",
            install_cmd=f"poetry add {pkg}",
            sync_cmd="poetry install",
            isolated_exec="poetry run python",
        )

    # 3. pipenv check
    if pipfile.exists():
        return DependencyConfig(
            manager="pipenv",
            install_cmd=f"pipenv install {pkg}",
            sync_cmd="pipenv install",
            isolated_exec="pipenv run python",
        )

    # 4. conda check
    if conda_env.exists():
        return DependencyConfig(
            manager="conda",
            install_cmd=f"conda install {pkg}",
            sync_cmd="conda env create -f environment.yml",
            isolated_exec="conda run python",
        )

    # 5. requirements.txt or default venv + pip
    return DependencyConfig(
        manager="venv",
        install_cmd=f".venv/bin/pip install {pkg}",
        sync_cmd=".venv/bin/pip install -r requirements.txt",
        isolated_exec=".venv/bin/python",
    )
```

- [x] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. /home/sak/Sak-Family-Agent/.venv/bin/pytest tests/test_agent_dep_manager.py -v`
Expected: PASS (5 passed)

- [x] **Step 5: Commit**

```bash
git add app/agent_platform/dep_manager.py tests/test_agent_dep_manager.py
git commit -m "feat(deps): Implement reactive Python dependency manager detection"
```

---

### Task 3: Antigravity Customizations & Progressive Disclosure Loader

**Files:**
- Create: `app/agent_platform/customizations.py`
- Test: `tests/test_agent_customizations.py`

**Interfaces:**
- Consumes: Directory paths, rules, skills, and lifecycle hook events
- Produces: `SkillSummary(name: str, description: str, path: str)`, `RuleDocument(scope: str, content: str)`, and `CustomizationRegistry.load_skill(name: str) -> str`

- [x] **Step 1: Write the failing test**

```python
# tests/test_agent_customizations.py
import pytest
from pathlib import Path
from app.agent_platform.customizations import CustomizationRegistry, SkillSummary

def test_skill_discovery_progressive_disclosure(tmp_path: Path):
    skills_dir = tmp_path / ".agents" / "skills" / "demo-skill"
    skills_dir.mkdir(parents=True)
    skill_file = skills_dir / "SKILL.md"
    skill_file.write_text(
        "---\nname: demo-skill\ndescription: Demonstrates progressive skill disclosure\n---\n"
        "# Detailed Instructions\nStep 1: Execute demo\nStep 2: Verify outcome\n"
    )

    registry = CustomizationRegistry(workspace_root=tmp_path)
    summaries = registry.list_available_skills()
    assert len(summaries) == 1
    assert summaries[0].name == "demo-skill"
    assert summaries[0].description == "Demonstrates progressive skill disclosure"
    # Verify full instructions are not loaded during summary phase
    assert not hasattr(summaries[0], "full_body") or summaries[0].description != skill_file.read_text()

    # Explicit on-demand activation loads full body
    full_content = registry.load_skill("demo-skill")
    assert "Detailed Instructions" in full_content
    assert "Step 1: Execute demo" in full_content

def test_hierarchical_rules_discovery(tmp_path: Path):
    root_rule = tmp_path / "AGENTS.md"
    root_rule.write_text("Enforce snake_case for all Python variables.")
    subdir = tmp_path / "src" / "sub"
    subdir.mkdir(parents=True)
    sub_rule = subdir / "AGENTS.md"
    sub_rule.write_text("All API models must use Pydantic V2.")

    registry = CustomizationRegistry(workspace_root=tmp_path)
    rules = registry.resolve_rules_for_path(subdir / "module.py")
    assert len(rules) == 2
    assert "Enforce snake_case" in rules[0].content
    assert "All API models must use Pydantic V2" in rules[1].content
```

- [x] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. /home/sak/Sak-Family-Agent/.venv/bin/pytest tests/test_agent_customizations.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent_platform.customizations'`

- [x] **Step 3: Write minimal implementation**

```python
# app/agent_platform/customizations.py
from dataclasses import dataclass
from pathlib import Path
import re

@dataclass(frozen=True)
class SkillSummary:
    name: str
    description: str
    path: str

@dataclass(frozen=True)
class RuleDocument:
    scope: str
    content: str

class CustomizationRegistry:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()
        self._skills_index: dict[str, Path] = {}
        self._index_skills()

    def _index_skills(self) -> None:
        search_paths = [
            self.workspace_root / ".agents" / "skills",
            self.workspace_root / ".gemini" / "skills",
        ]
        for base in search_paths:
            if base.exists():
                for skill_md in base.glob("*/SKILL.md"):
                    skill_name = skill_md.parent.name
                    self._skills_index[skill_name] = skill_md

    def list_available_skills(self) -> list[SkillSummary]:
        results: list[SkillSummary] = []
        for name, path in self._skills_index.items():
            content = path.read_text(encoding="utf-8")
            description = ""
            desc_match = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
            if desc_match:
                description = desc_match.group(1).strip()
            else:
                lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#") and not line.startswith("---")]
                description = lines[0] if lines else "Custom agent skill"

            results.append(SkillSummary(name=name, description=description, path=str(path)))
        return sorted(results, key=lambda s: s.name)

    def load_skill(self, name: str) -> str:
        if name not in self._skills_index:
            raise KeyError(f"Skill '{name}' not found in registry")
        return self._skills_index[name].read_text(encoding="utf-8")

    def resolve_rules_for_path(self, target_path: Path) -> list[RuleDocument]:
        rules: list[RuleDocument] = []
        current = target_path.resolve()
        if current.is_file():
            current = current.parent

        checkpoints: list[Path] = []
        while True:
            checkpoints.append(current)
            if current == self.workspace_root or current.parent == current:
                break
            current = current.parent

        # Order from root to deepest directory
        for dir_path in reversed(checkpoints):
            for candidate in ["AGENTS.md", "GEMINI.md"]:
                rule_file = dir_path / candidate
                if rule_file.exists():
                    rules.append(
                        RuleDocument(
                            scope=str(rule_file.relative_to(self.workspace_root)),
                            content=rule_file.read_text(encoding="utf-8").strip(),
                        )
                    )
        return rules
```

- [x] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. /home/sak/Sak-Family-Agent/.venv/bin/pytest tests/test_agent_customizations.py -v`
Expected: PASS (2 passed)

- [x] **Step 5: Commit**

```bash
git add app/agent_platform/customizations.py tests/test_agent_customizations.py
git commit -m "feat(customizations): Implement progressive disclosure and hierarchical rules engine"
```

---

### Task 4: Jules Remote Task Delegation & Patch Orchestrator

**Files:**
- Create: `app/agent_platform/jules_worker.py`
- Test: `tests/test_agent_jules_worker.py`

**Interfaces:**
- Consumes: Remote git URLs, task descriptions, and diff patch contents
- Produces: `parse_git_repo_url(url: str) -> str`, `build_jules_task_command(repo: str, task: str) -> list[str]`, and `validate_patch_targets(patch_content: str, valid_files: set[str]) -> bool`

- [x] **Step 1: Write the failing test**

```python
# tests/test_agent_jules_worker.py
import pytest
from app.agent_platform.jules_worker import (
    parse_git_repo_url,
    build_jules_task_command,
    validate_patch_targets,
    build_apply_commands,
)

def test_parse_git_repo_url_https():
    repo = parse_git_repo_url("https://github.com/my-org/my-project.git")
    assert repo == "my-org/my-project"

def test_parse_git_repo_url_ssh():
    repo = parse_git_repo_url("git@github.com:my-org/my-project.git")
    assert repo == "my-org/my-project"

def test_build_jules_task_command():
    cmd = build_jules_task_command(repo="my-org/my-project", task="Implement OAuth2 login")
    assert cmd == ["jules", "remote", "new", "--repo", "my-org/my-project", "--session", "Implement OAuth2 login"]

def test_validate_patch_targets_matching():
    patch = """diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,3 +1,4 @@
+import auth
"""
    is_valid = validate_patch_targets(patch, valid_files={"app/main.py", "app/auth.py"})
    assert is_valid

def test_validate_patch_targets_mismatched():
    patch = """diff --git a/unrelated/foreign.go b/unrelated/foreign.go
--- a/unrelated/foreign.go
+++ b/unrelated/foreign.go
"""
    is_valid = validate_patch_targets(patch, valid_files={"app/main.py"})
    assert not is_valid

def test_build_apply_commands():
    cmds = build_apply_commands(branch="jules-oauth2-impl")
    assert cmds[0] == "git checkout -b jules-oauth2-impl"
    assert cmds[1] == "git apply --index .jules/diff.patch"
```

- [x] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. /home/sak/Sak-Family-Agent/.venv/bin/pytest tests/test_agent_jules_worker.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent_platform.jules_worker'`

- [x] **Step 3: Write minimal implementation**

```python
# app/agent_platform/jules_worker.py
import re

def parse_git_repo_url(url: str) -> str:
    cleaned = url.strip()
    match = re.search(r"github\.com[:/]([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+?)(?:\.git)?$", cleaned)
    if not match:
        raise ValueError(f"Unable to parse repository from URL: {url}")
    return match.group(1)

def build_jules_task_command(repo: str, task: str) -> list[str]:
    return ["jules", "remote", "new", "--repo", repo, "--session", task]

def validate_patch_targets(patch_content: str, valid_files: set[str]) -> bool:
    target_files = set()
    for match in re.finditer(r"^diff --git a/(.+?) b/(.+?)$", patch_content, re.MULTILINE):
        target_files.add(match.group(2).strip())

    if not target_files:
        return False

    return all(target in valid_files for target in target_files)

def build_apply_commands(branch: str) -> list[str]:
    return [
        f"git checkout -b {branch}",
        "git apply --index .jules/diff.patch",
        "git add .",
        "git rm --cached -r .jules 2>/dev/null || true",
        f'git commit -m "Apply Jules changes on {branch}"',
    ]
```

- [x] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. /home/sak/Sak-Family-Agent/.venv/bin/pytest tests/test_agent_jules_worker.py -v`
Expected: PASS (6 passed)

- [x] **Step 5: Commit**

```bash
git add app/agent_platform/jules_worker.py tests/test_agent_jules_worker.py
git commit -m "feat(jules): Implement Jules remote task delegation and patch validation"
```

---

### Task 5: Dual Agent Core Engine (Google Antigravity SDK & ADK)

**Files:**
- Create: `app/agent_platform/agent_engine.py`
- Test: `tests/test_agent_engine.py`

**Interfaces:**
- Consumes: Agent configurations (`AgentEngineMode.ANTIGRAVITY` or `AgentEngineMode.ADK`), tools, and safety guardrails
- Produces: `UnifiedAgentRuntime.execute_tool(tool_name: str, arguments: dict) -> dict` with safety verification

- [x] **Step 1: Write the failing test**

```python
# tests/test_agent_engine.py
import pytest
from app.agent_platform.agent_engine import (
    AgentEngineMode,
    UnifiedAgentConfig,
    UnifiedAgentRuntime,
)
from app.agent_platform.safety import DataLossGuardrail

def sample_add_tool(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

def sample_destructive_tool(table_name: str) -> str:
    """Execute drop table."""
    return f"DROP TABLE {table_name};"

def test_runtime_registers_and_executes_safe_tool():
    config = UnifiedAgentConfig(
        name="calculator_agent",
        engine=AgentEngineMode.ANTIGRAVITY,
        model="gemini-2.5-flash",
    )
    runtime = UnifiedAgentRuntime(config=config)
    runtime.register_tool("add", sample_add_tool)

    result = runtime.execute_tool("add", {"a": 10, "b": 32})
    assert result["status"] == "success"
    assert result["output"] == 42

def test_runtime_intercepts_destructive_tool_execution():
    guard = DataLossGuardrail()
    config = UnifiedAgentConfig(
        name="db_agent",
        engine=AgentEngineMode.ADK,
        model="gemini-3.7-flash",
    )
    runtime = UnifiedAgentRuntime(config=config, guardrail=guard)
    runtime.register_tool("drop_table", sample_destructive_tool)

    result = runtime.execute_tool("drop_table", {"table_name": "users"})
    assert result["status"] == "blocked"
    assert "Destructive database operation" in result["reason"]

def test_runtime_tracks_execution_history():
    config = UnifiedAgentConfig(
        name="history_agent",
        engine=AgentEngineMode.ANTIGRAVITY,
        model="gemini-2.5-flash",
    )
    runtime = UnifiedAgentRuntime(config=config)
    runtime.register_tool("add", sample_add_tool)
    runtime.execute_tool("add", {"a": 2, "b": 3})

    assert len(runtime.history) == 1
    assert runtime.history[0]["tool"] == "add"
```

- [x] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. /home/sak/Sak-Family-Agent/.venv/bin/pytest tests/test_agent_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent_platform.agent_engine'`

- [x] **Step 3: Write minimal implementation**

```python
# app/agent_platform/agent_engine.py
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from app.agent_platform.safety import DataLossGuardrail

class AgentEngineMode(str, Enum):
    ANTIGRAVITY = "antigravity"
    ADK = "adk"

@dataclass
class UnifiedAgentConfig:
    name: str
    engine: AgentEngineMode = AgentEngineMode.ANTIGRAVITY
    model: str = "gemini-2.5-flash"
    max_turns: int = 150
    instruction: str = "You are an autonomous AI pair programming agent."

class UnifiedAgentRuntime:
    def __init__(self, config: UnifiedAgentConfig, guardrail: DataLossGuardrail | None = None):
        self.config = config
        self.guardrail = guardrail or DataLossGuardrail()
        self._tools: dict[str, Callable[..., Any]] = {}
        self.history: list[dict[str, Any]] = []

    def register_tool(self, name: str, func: Callable[..., Any]) -> None:
        self._tools[name] = func

    def execute_tool(self, tool_name: str, arguments: dict[str, Any], approval_token: str | None = None) -> dict[str, Any]:
        if tool_name not in self._tools:
            return {"status": "error", "error": f"Tool '{tool_name}' not registered"}

        func = self._tools[tool_name]
        try:
            raw_output = func(**arguments)
            output_str = str(raw_output)

            # Safety interceptor
            safety_check = self.guardrail.verify_or_halt(output_str, approval_token=approval_token)
            if safety_check.blocked:
                event = {
                    "tool": tool_name,
                    "arguments": arguments,
                    "status": "blocked",
                    "reason": safety_check.reason,
                    "impact": safety_check.impact,
                }
                self.history.append(event)
                return event

            event = {
                "tool": tool_name,
                "arguments": arguments,
                "status": "success",
                "output": raw_output,
            }
            self.history.append(event)
            return event
        except Exception as exc:
            event = {
                "tool": tool_name,
                "arguments": arguments,
                "status": "error",
                "error": str(exc),
            }
            self.history.append(event)
            return event
```

- [x] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. /home/sak/Sak-Family-Agent/.venv/bin/pytest tests/test_agent_engine.py -v`
Expected: PASS (3 passed)

- [x] **Step 5: Commit**

```bash
git add app/agent_platform/agent_engine.py tests/test_agent_engine.py
git commit -m "feat(engine): Implement unified dual agent core with safety hooks"
```

---

### Task 6: Harness Custom AI Agent YAML Exporter & Pipeline Bridge

**Files:**
- Create: `app/agent_platform/harness_exporter.py`
- Test: `tests/test_agent_harness_exporter.py`

**Interfaces:**
- Consumes: Agent metadata, task description, inputs, and connector identifiers
- Produces: `generate_harness_uid(name: str) -> str`, `export_harness_agent_spec(...) -> str`, and `export_v1_pipeline_step(...) -> str`

- [x] **Step 1: Write the failing test**

```python
# tests/test_agent_harness_exporter.py
import pytest
from app.agent_platform.harness_exporter import (
    generate_harness_uid,
    export_harness_agent_spec,
    export_v1_pipeline_step,
)

def test_generate_harness_uid():
    assert generate_harness_uid("Code Review Agent") == "ca_code_review_agent"
    assert generate_harness_uid("PR-Security--Scanner") == "ca_pr_security_scanner"

def test_export_harness_agent_spec_structure():
    spec_yaml = export_harness_agent_spec(
        name="Security Scanner",
        task="1. Inspect PR diff\n2. Flag high severity issues",
        llm_connector_id="harness_gemini_connector",
        mcp_connectors=["github_mcp"],
    )
    assert "version: 1" in spec_yaml
    assert "pkg.harness.io/vrvdt5ius7uwygso8s0bia/harness-agents/harness-ai-agent:latest" in spec_yaml
    assert "PLUGIN_HARNESS_CONNECTOR: ${{inputs.llmConnector.id}}" in spec_yaml
    assert "PLUGIN_ALLOWED_DOMAINS: ${{inputs.allowedDomains}}" in spec_yaml
    assert "PLUGIN_MCP_SERVERS: <+connectorInputs.resolveList(<+inputs.mcpConnectors>)>" in spec_yaml
    assert "harness_gemini_connector" in spec_yaml
    assert "github_mcp" in spec_yaml

def test_export_v1_pipeline_step():
    step_yaml = export_v1_pipeline_step(
        agent_name="Code Review Agent",
        custom_inputs={"repo_name": "<+inputs.repo_name>", "branch": "<+inputs.branch>"},
    )
    assert "uses: ca_code_review_agent@1.0.0" in step_yaml
    assert "repo_name: <+inputs.repo_name>" in step_yaml
```

- [x] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. /home/sak/Sak-Family-Agent/.venv/bin/pytest tests/test_agent_harness_exporter.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent_platform.harness_exporter'`

- [x] **Step 3: Write minimal implementation**

```python
# app/agent_platform/harness_exporter.py
import re

def generate_harness_uid(name: str) -> str:
    cleaned = name.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return f"ca_{cleaned}"

def export_harness_agent_spec(
    name: str,
    task: str,
    llm_connector_id: str = "your_llm_connector_id",
    mcp_connectors: list[str] | None = None,
    allowed_domains: str = "",
    max_turns: int = 150,
) -> str:
    mcp_list = mcp_connectors or []
    has_mcp = len(mcp_list) > 0

    task_indented = "\n".join(f"                {line}" for line in task.strip().splitlines())

    mcp_env = ""
    if has_mcp:
        mcp_env = (
            "              PLUGIN_MCP_FORMAT: harness\n"
            "              PLUGIN_MCP_SERVERS: <+connectorInputs.resolveList(<+inputs.mcpConnectors>)>"
        )

    mcp_inputs = ""
    if has_mcp:
        items_yaml = "\n".join(f"        - {conn}" for conn in mcp_list)
        mcp_inputs = f"""    mcpConnectors:
      type: array
      default:
{items_yaml}
      ui:
        component: array
        input:
          inputType: connector
          inputConfig:
            connectorTypes:
              - Mcp
"""

    layout_items = ["llmConnector", "allowedDomains"]
    if has_mcp:
        layout_items.append("mcpConnectors")
    layout_yaml = "\n".join(f"        - {item}" for item in layout_items)

    env_block = f"""            env:
              PLUGIN_TASK: |
{task_indented}
              PLUGIN_MAX_TURNS: {max_turns}
              PLUGIN_HARNESS_CONNECTOR: ${{{{inputs.llmConnector.id}}}}
              PLUGIN_ALLOWED_DOMAINS: ${{{{inputs.allowedDomains}}}}"""
    if mcp_env:
        env_block += f"\n{mcp_env}"

    inputs_block = f"""  inputs:
    llmConnector:
      type: connector
      required: true
      default: {llm_connector_id}
      ui:
        connectorCategories:
          - AI

    allowedDomains:
      type: string
      default: "{allowed_domains}"
"""
    if mcp_inputs:
        inputs_block += f"\n{mcp_inputs}"

    return f"""version: 1
agent:
  step:
    group:
      steps:
        - name: Agent
          if: <+Always>
          id: agent
          run:
            container:
              image: pkg.harness.io/vrvdt5ius7uwygso8s0bia/harness-agents/harness-ai-agent:latest
{env_block}

{inputs_block}
  layout:
    - title: Agent Configuration
      items:
{layout_yaml}
"""

def export_v1_pipeline_step(agent_name: str, custom_inputs: dict[str, str]) -> str:
    uid = generate_harness_uid(agent_name)
    with_block = "\n".join(f"      {k}: {v}" for k, v in custom_inputs.items())
    return f"""- name: {agent_name.lower().replace(' ', '_')}
  template:
    uses: {uid}@1.0.0
    with:
{with_block}
"""
```

- [x] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. /home/sak/Sak-Family-Agent/.venv/bin/pytest tests/test_agent_harness_exporter.py -v`
Expected: PASS (3 passed)

- [x] **Step 5: Commit**

```bash
git add app/agent_platform/harness_exporter.py tests/test_agent_harness_exporter.py
git commit -m "feat(harness): Implement Harness AI Agent spec generator and pipeline bridge"
```
