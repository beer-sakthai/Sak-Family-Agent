# Sak-Family-Agent Whole-Repository Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate package and pipeline duplication across all 6 agent personas (`personas/*`), enforce canonical `sys.path` resolution across all maintenance scripts (`scripts/`), purge 284 committed temporary subagent scratch files from `apps/*/.agents/`, package and isolate `apps/agent_workflow_framework/`, and lock in repository-wide structural invariants with automated unit tests and a refreshed dashboard snapshot.

**Architecture:** We unify all 6 personas (`sakthai`, `sakking`, `saksee`, `saksit`, `sakjules`, `saktan`) around a single source of truth: `personas/sakthai/sakthai/` is the sole canonical Python package (`personas/shared/sakthai` and `personas/{sakking,saksee,saksit,sakjules,saktan}/sakthai` resolve to it via relative symlinks), and `personas/shared/agent-self-evolution/` is the sole canonical self-evolution pipeline (`personas/{sakthai,sakking,saksee,saksit,sakjules,saktan}/agent-self-evolution` resolve to it via relative symlinks). Every subsystem boundary (`personas/`, `infra/hermes-agents/`, `scripts/`, `apps/agent_workflow_framework/`, `apps/sak_agent_dashboard/`) gets an explicit unit test gate that runs in `<0.2s` under standard `python3 -m unittest`.

**Tech Stack:** Python 3.11+ (`unittest`, `pathlib`, `argparse`, `tomllib`), Next.js 15 / TypeScript (`apps/sak_agent_dashboard`), Git symlinks, `uv` / `pyproject.toml`.

**Spec:** [`AGENTS.md`](../../../AGENTS.md), [`GEMINI.md`](../../../GEMINI.md), and [`PLAN.md`](../../../PLAN.md)

## Global Constraints

- **Single Canonical Package (`AGENTS.md`):** The installable core package (`sakthai`) lives at `personas/sakthai/sakthai/` — not at the repo root.
- **Script Path Resolution (`AGENTS.md`):** Any development/maintenance script in the `scripts/` folder that imports `sakthai` without relying on the installed environment must insert the canonical package path into `sys.path` explicitly (`sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))`).
- **Persona Parity Invariants (`tests/test_persona_guardrails_parity.py`, `tests/test_persona_web_server_parity.py`):** All 6 personas (`sakthai`, `sakking`, `saksee`, `saksit`, `sakjules`, `saktan`) must resolve `sakthai/agent/guardrails.py` and `sakthai/web/server.py` identically to `personas/sakthai/sakthai/` and carry identical 10-item `personas/<slug>/` and 7-item `infra/hermes-agents/` directory layouts.
- **Code Style & Coverage (`AGENTS.md`):** Python 3.11+ conventions, 4-space indentation, 100-character line length, type annotations on public code paths, and minimum 96% test coverage on the core package.
- **No Unpinned MCP Packages (`tests/test_persona_security_config.py`):** Never introduce `npx -y <pkg>@latest` or `/home/beern` paths in any persona config or markdown file.

---

## File Structure & Responsibility Map

| Path | Action | Responsibility |
|---|---|---|
| `tests/test_persona_structure_parity.py` | **Create** | Enforces 10-item layout in `personas/<slug>/`, 7-item layout in `infra/hermes-agents/`, symlink deduplication of `sakthai` and `agent-self-evolution`, and rich H2 parity across `BACKPACK.md`, `CYCLE.md`, `MEMORY.md`, `HANDOFF.md`, `PLAN.md`. |
| `personas/shared/sakthai` | **Replace dir with symlink** | Relative symlink `../sakthai/sakthai` replacing the stale 78-file duplicate copy so `sakjules`, `saktan`, `sakking`, `saksee`, and `saksit` all point to the 92-file canonical package. |
| `personas/{sakking,saksee,saksit}/sakthai` | **Replace dirs with symlinks** | Relative symlink `../shared/sakthai` replacing partial/drifted shadow folders (`cli/system.py`, `web/server.py`, `agent/guardrails.py`). |
| `personas/sakthai/agent-self-evolution` | **Replace dir with symlink** | Relative symlink `../shared/agent-self-evolution` so all 6 personas share the single `personas/shared/agent-self-evolution/` directory. |
| `tests/test_persona_guardrails_parity.py` | **Modify (`L14`)** | Include all 6 personas (`"saktan"` added to `PERSONAS`) and assert canonical symlink resolution. |
| `tests/test_scripts_sys_path.py` | **Create** | Verifies every `scripts/*.py` file that imports `sakthai` inserts `personas/sakthai` into `sys.path` before importing `sakthai`. |
| `scripts/hf_integration_smoke.py` | **Modify (`L1-L10`)** | Add `REPO_ROOT` and `sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))`. |
| `scripts/setup_servicequotebot.py` | **Modify (`L1-L15`)** | Add `REPO_ROOT` and `sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))`. |
| `scripts/telegram_send.py` | **Modify (`L22-L38`)** | Add `sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))` alongside `REPO_ROOT`. |
| `tests/test_repo_hygiene.py` | **Create** | Asserts zero committed subagent scratch directories (`apps/*/.agents/`, `.manus/`, root `profiles/`) exist in the repository and `.gitignore` blocks `.agents/` inside `apps/*/`. |
| `apps/agent_workflow_framework/.agents/` | **Delete (208 files)** | Remove committed subagent scratch/dispatch/briefing logs from `apps/agent_workflow_framework/`. |
| `apps/agent_workflow_framework/ORIGINAL_REQUEST.md` | **Delete** | Remove committed scratch prompt artifact from `apps/agent_workflow_framework/`. |
| `apps/sak_agent_dashboard/.agents/` | **Delete (76 files)** | Remove committed subagent scratch/dispatch/briefing logs from `apps/sak_agent_dashboard/`. |
| `.gitignore` | **Modify** | Ignore `apps/*/.agents/` and `.workflow_runs/` so scratch runs never pollute git status. |
| `apps/agent_workflow_framework/pyproject.toml` | **Create** | Standard PEP 621 package metadata with `agent-workflow = "agent_workflow.cli:main"` console script entry point. |
| `apps/agent_workflow_framework/agent_workflow/cli.py` | **Modify (`L29-L173`)** | Add `--storage-dir` (or `AGENT_WORKFLOW_STORAGE_DIR` env var fallback) to `run`, `inspect`, and `list` subcommands and wire into `WorkflowExecutor(storage_dir=...)` and `RunHistoryStore(storage_dir=...)`. |
| `apps/agent_workflow_framework/verify.py` | **Modify (`L47-L95`)** | Isolate verification workflow runs inside a `tempfile.TemporaryDirectory()` via `AGENT_WORKFLOW_STORAGE_DIR` so running `verify.py` never writes `.workflow_runs/` into the repo tree. |
| `apps/agent_workflow_framework/tests/test_cli.py` | **Modify** | Add unit tests for `--storage-dir`, `AGENT_WORKFLOW_STORAGE_DIR`, and `pyproject.toml` console script registration. |
| `apps/sak_agent_dashboard/src/data/system-snapshot.json` | **Modify (Regenerate)** | Refresh the dashboard system snapshot via `scripts/gen_system_snapshot.py` so the Next.js UI reflects the refactored repository state. |

---

### Task 1: Deduplicate `sakthai` Package & `agent-self-evolution` Across All 6 Personas

**Files:**
- Create: `tests/test_persona_structure_parity.py`
- Modify: `tests/test_persona_guardrails_parity.py:13-33`
- Modify (Replace dir with symlink): `personas/shared/sakthai` → `../sakthai/sakthai`
- Modify (Replace dirs with symlinks): `personas/sakking/sakthai`, `personas/saksee/sakthai`, `personas/saksit/sakthai` → `../shared/sakthai`
- Modify (Replace dir with symlink): `personas/sakthai/agent-self-evolution` → `../shared/agent-self-evolution`
- Test: `tests/test_persona_structure_parity.py`, `tests/test_persona_guardrails_parity.py`, `tests/test_persona_web_server_parity.py`

**Interfaces:**
- Consumes: `personas/{sakthai,sakking,saksee,saksit,sakjules,saktan}/` and `infra/hermes-agents/{default,profiles/*}/` filesystem layout.
- Produces: Single canonical `personas/sakthai/sakthai/` package resolved by all 6 personas (`(REPO_ROOT / "personas" / p / "sakthai").resolve() == (REPO_ROOT / "personas" / "sakthai" / "sakthai").resolve()`) and single canonical `personas/shared/agent-self-evolution/` resolved by all 6 personas.

- [x] **Step 1: Write the failing test in `tests/test_persona_structure_parity.py` and update `tests/test_persona_guardrails_parity.py`**

Create `tests/test_persona_structure_parity.py`:

```python
"""Verify structural parity and symlink deduplication across all 6 Sak Family personas."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS = ("sakthai", "sakking", "saksee", "saksit", "sakjules", "saktan")
EXPECTED_PERSONA_ITEMS = {
    "BACKPACK.md",
    "CYCLE.md",
    "HANDOFF.md",
    "MEMORY.md",
    "PLAN.md",
    "SOUL.md",
    "agent-self-evolution",
    "config",
    "sakthai",
    "skills",
}
EXPECTED_CONFIG_ITEMS = {
    "config.yaml",
    "gateway_voice_mode.json",
    "mcp.json",
    "workspace.yaml",
}
EXPECTED_HERMES_ITEMS = {
    "BACKPACK.md",
    "CYCLE.md",
    "HANDOFF.md",
    "MEMORY.md",
    "PLAN.md",
    "SOUL.md",
    "config.yaml",
}


class TestPersonaStructureParity(unittest.TestCase):
    def test_every_persona_has_exact_ten_top_level_items(self) -> None:
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                pdir = REPO_ROOT / "personas" / persona
                actual = {item.name for item in pdir.iterdir()}
                self.assertEqual(actual, EXPECTED_PERSONA_ITEMS)

    def test_every_persona_has_exact_four_config_files(self) -> None:
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                cdir = REPO_ROOT / "personas" / persona / "config"
                actual = {item.name for item in cdir.iterdir()}
                self.assertEqual(actual, EXPECTED_CONFIG_ITEMS)

    def test_all_personas_resolve_to_single_canonical_sakthai_package(self) -> None:
        canonical = (REPO_ROOT / "personas" / "sakthai" / "sakthai").resolve()
        self.assertTrue(canonical.is_dir())
        shared = REPO_ROOT / "personas" / "shared" / "sakthai"
        self.assertTrue(shared.is_symlink(), "personas/shared/sakthai must be a symlink")
        self.assertEqual(shared.resolve(), canonical)
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                pkg_path = REPO_ROOT / "personas" / persona / "sakthai"
                if persona != "sakthai":
                    self.assertTrue(
                        pkg_path.is_symlink(),
                        f"personas/{persona}/sakthai must be a symlink, not a duplicate directory",
                    )
                self.assertEqual(pkg_path.resolve(), canonical)

    def test_all_personas_resolve_to_single_canonical_self_evolution_dir(self) -> None:
        canonical = (REPO_ROOT / "personas" / "shared" / "agent-self-evolution").resolve()
        self.assertTrue(canonical.is_dir())
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                evo_path = REPO_ROOT / "personas" / persona / "agent-self-evolution"
                self.assertTrue(
                    evo_path.is_symlink(),
                    f"personas/{persona}/agent-self-evolution must be a symlink to ../shared/agent-self-evolution",
                )
                self.assertEqual(evo_path.resolve(), canonical)

    def test_hermes_profiles_expose_all_seven_items(self) -> None:
        hermes_root = REPO_ROOT / "infra" / "hermes-agents"
        targets = [hermes_root / "default"] + [
            hermes_root / "profiles" / p for p in PERSONAS if p != "sakthai"
        ]
        for target in targets:
            with self.subTest(target=str(target.relative_to(REPO_ROOT))):
                actual = {item.name for item in target.iterdir()}
                self.assertEqual(actual, EXPECTED_HERMES_ITEMS)


if __name__ == "__main__":
    unittest.main()
```

Also update `PERSONAS` in `tests/test_persona_guardrails_parity.py` (line 14) to include `"saktan"`:

```python
PERSONAS = ["sakthai", "sakjules", "saktan", "sakking", "saksee", "saksit"]
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_persona_structure_parity.py -v`
Expected: FAIL (`AssertionError: False is not true : personas/shared/sakthai must be a symlink` and `personas/sakthai/agent-self-evolution must be a symlink`).

- [x] **Step 3: Replace duplicate directories with relative symlinks**

Run:

```python
python3 -c '
import os, pathlib, shutil

root = pathlib.Path("/home/sak/Sak-Family-Agent")

# 1. Replace personas/shared/sakthai directory with symlink -> ../sakthai/sakthai
shared_sakthai = root / "personas/shared/sakthai"
if shared_sakthai.exists() and not shared_sakthai.is_symlink():
    shutil.rmtree(shared_sakthai)
if not shared_sakthai.exists():
    os.symlink("../sakthai/sakthai", shared_sakthai)

# 2. Replace personas/{sakking,saksee,saksit}/sakthai directories with symlink -> ../shared/sakthai
for p in ["sakking", "saksee", "saksit"]:
    p_sakthai = root / "personas" / p / "sakthai"
    if p_sakthai.exists() and not p_sakthai.is_symlink():
        shutil.rmtree(p_sakthai)
    if not p_sakthai.exists():
        os.symlink("../shared/sakthai", p_sakthai)

# 3. Replace personas/sakthai/agent-self-evolution directory with symlink -> ../shared/agent-self-evolution
sakthai_evo = root / "personas/sakthai/agent-self-evolution"
if sakthai_evo.exists() and not sakthai_evo.is_symlink():
    shutil.rmtree(sakthai_evo)
if not sakthai_evo.exists():
    os.symlink("../shared/agent-self-evolution", sakthai_evo)
'
```

- [x] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests/test_persona_structure_parity.py tests/test_persona_guardrails_parity.py tests/test_persona_web_server_parity.py -v`
Expected: PASS (all 7 tests pass with 0 duplicate `.py` files drifting across `personas/`).

- [x] **Step 5: Commit**

```bash
git add personas/ tests/test_persona_structure_parity.py tests/test_persona_guardrails_parity.py
git commit -m "refactor(personas): deduplicate sakthai package and agent-self-evolution via canonical symlinks"
```

---

### Task 2: Enforce Canonical `sys.path` Resolution Across All `scripts/*.py`

**Files:**
- Create: `tests/test_scripts_sys_path.py`
- Modify: `scripts/hf_integration_smoke.py:1-12`
- Modify: `scripts/setup_servicequotebot.py:1-16`
- Modify: `scripts/telegram_send.py:22-38`
- Test: `tests/test_scripts_sys_path.py`

**Interfaces:**
- Consumes: All `.py` files in `scripts/` that contain `import sakthai` or `from sakthai`.
- Produces: Guaranteed `sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))` in every script before any `sakthai` import, enforced by `tests/test_scripts_sys_path.py`.

- [x] **Step 1: Write the failing test in `tests/test_scripts_sys_path.py`**

Create `tests/test_scripts_sys_path.py`:

```python
"""Enforce AGENTS.md rule: scripts importing sakthai must insert personas/sakthai into sys.path."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"


def _imports_sakthai(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "sakthai" or alias.name.startswith("sakthai.") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == "sakthai" or node.module.startswith("sakthai.")):
                return True
    return False


class TestScriptsSysPath(unittest.TestCase):
    def test_all_scripts_importing_sakthai_insert_canonical_sys_path(self) -> None:
        script_files = sorted(SCRIPTS_DIR.glob("*.py"))
        self.assertGreater(len(script_files), 0)
        for path in script_files:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            if _imports_sakthai(tree) or "from sakthai" in source or "import sakthai" in source:
                with self.subTest(script=path.name):
                    self.assertIn(
                        "sys.path.insert",
                        source,
                        f"scripts/{path.name} imports sakthai without inserting personas/sakthai into sys.path",
                    )
                    self.assertIn(
                        "personas",
                        source,
                        f"scripts/{path.name} must reference personas/sakthai in its sys.path setup",
                    )


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_scripts_sys_path.py -v`
Expected: FAIL on `hf_integration_smoke.py`, `setup_servicequotebot.py`, and `telegram_send.py`.

- [x] **Step 3: Add canonical `sys.path.insert` to the three scripts**

Update `scripts/hf_integration_smoke.py` lines 1–10:

```python
"""Live Hugging Face smoke test for CI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "personas" / "sakthai") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

from sakthai.agent.tools import tool_by_name
from sakthai.memory.store import MemoryStore
```

Update `scripts/setup_servicequotebot.py` lines 1–14:

```python
#!/usr/bin/env python3
"""Bundle a customer-specific ServiceQuoteBot deployment."""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "personas" / "sakthai") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

from sakthai.learn.ingest import ingest_document
from sakthai.memory.store import MemoryStore
```

Update `scripts/telegram_send.py` lines 31–36:

```python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "personas" / "sakthai") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))
ENV_FILE = REPO_ROOT / ".env"
```

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_scripts_sys_path.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add scripts/hf_integration_smoke.py scripts/setup_servicequotebot.py scripts/telegram_send.py tests/test_scripts_sys_path.py
git commit -m "refactor(scripts): enforce canonical personas/sakthai sys.path resolution across all scripts"
```

---

### Task 3: Purge Committed Subagent Scratch Logs (`apps/*/.agents/`) & Enforce Repo Hygiene

**Files:**
- Create: `tests/test_repo_hygiene.py`
- Delete: `apps/agent_workflow_framework/.agents/` (208 files)
- Delete: `apps/agent_workflow_framework/ORIGINAL_REQUEST.md`
- Delete: `apps/sak_agent_dashboard/.agents/` (76 files)
- Modify: `.gitignore`
- Test: `tests/test_repo_hygiene.py`

**Interfaces:**
- Consumes: Repository directory tree and `.gitignore`.
- Produces: Clean `apps/agent_workflow_framework/` and `apps/sak_agent_dashboard/` directories free of ephemeral subagent dispatch logs, guarded by `tests/test_repo_hygiene.py`.

- [x] **Step 1: Write the failing test in `tests/test_repo_hygiene.py`**

Create `tests/test_repo_hygiene.py`:

```python
"""Verify repository hygiene: no committed scratch directories (.manus, profiles, apps/*/.agents)."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PATHS = (
    REPO_ROOT / ".manus",
    REPO_ROOT / "profiles",
    REPO_ROOT / "apps" / "agent_workflow_framework" / ".agents",
    REPO_ROOT / "apps" / "agent_workflow_framework" / "ORIGINAL_REQUEST.md",
    REPO_ROOT / "apps" / "sak_agent_dashboard" / ".agents",
)


class TestRepoHygiene(unittest.TestCase):
    def test_no_forbidden_scratch_directories_exist(self) -> None:
        for path in FORBIDDEN_PATHS:
            with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                self.assertFalse(
                    path.exists(),
                    f"Ephemeral scratch path {path.relative_to(REPO_ROOT)} must not exist in the repository",
                )

    def test_root_agents_dir_contains_only_project_rules(self) -> None:
        agents_dir = REPO_ROOT / ".agents"
        self.assertTrue(agents_dir.is_dir())
        items = [p.name for p in agents_dir.iterdir()]
        self.assertEqual(items, ["AGENTS.md"])

    def test_gitignore_blocks_subproject_agents_and_workflow_runs(self) -> None:
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("apps/*/.agents/", gitignore)
        self.assertIn(".workflow_runs/", gitignore)


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_repo_hygiene.py -v`
Expected: FAIL (`apps/agent_workflow_framework/.agents`, `apps/agent_workflow_framework/ORIGINAL_REQUEST.md`, and `apps/sak_agent_dashboard/.agents` still exist).

- [x] **Step 3: Remove ephemeral scratch directories and update `.gitignore`**

Run:

```python
python3 -c '
import pathlib, shutil

root = pathlib.Path("/home/sak/Sak-Family-Agent")
for rel in [
    "apps/agent_workflow_framework/.agents",
    "apps/agent_workflow_framework/ORIGINAL_REQUEST.md",
    "apps/sak_agent_dashboard/.agents",
]:
    target = root / rel
    if target.is_dir():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()

gitignore = root / ".gitignore"
text = gitignore.read_text(encoding="utf-8")
additions = []
if "apps/*/.agents/" not in text:
    additions.append("apps/*/.agents/")
if ".workflow_runs/" not in text:
    additions.append(".workflow_runs/")
if additions:
    gitignore.write_text(text.rstrip() + "\n\n# Subagent scratch & workflow run artifacts\n" + "\n".join(additions) + "\n", encoding="utf-8")
'
```

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_repo_hygiene.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add -A apps/agent_workflow_framework/.agents apps/agent_workflow_framework/ORIGINAL_REQUEST.md apps/sak_agent_dashboard/.agents .gitignore tests/test_repo_hygiene.py
git commit -m "chore(hygiene): remove 284 ephemeral subagent scratch files from apps/*/.agents"
```

---

### Task 4: Package `apps/agent_workflow_framework` & Add `--storage-dir` Run Isolation

**Files:**
- Create: `apps/agent_workflow_framework/pyproject.toml`
- Modify: `apps/agent_workflow_framework/agent_workflow/cli.py:29-173`
- Modify: `apps/agent_workflow_framework/verify.py:47-105`
- Modify: `apps/agent_workflow_framework/tests/test_cli.py`
- Test: `apps/agent_workflow_framework/tests/test_cli.py`

**Interfaces:**
- Consumes: `RunHistoryStore(storage_dir: str = ".workflow_runs")` and `WorkflowExecutor(storage_dir: str = ".workflow_runs")`.
- Produces:
  - `apps/agent_workflow_framework/pyproject.toml` defining `name = "agent-workflow-framework"` and `[project.scripts] agent-workflow = "agent_workflow.cli:main"`
  - `build_parser()` in `agent_workflow/cli.py` accepting `--storage-dir` (defaulting to `os.environ.get("AGENT_WORKFLOW_STORAGE_DIR", ".workflow_runs")`)
  - `cmd_run(filepath: str, run_id: Optional[str] = None, storage_dir: str = ".workflow_runs") -> int`
  - `cmd_inspect(run_id: str, step_id: Optional[str] = None, storage_dir: str = ".workflow_runs") -> int`
  - `cmd_list(storage_dir: str = ".workflow_runs") -> int`
  - `verify.py` executing all CLI and programmatic verification scenarios inside a `tempfile.TemporaryDirectory()` so zero `.workflow_runs/` artifacts pollute the working tree.

- [x] **Step 1: Write the failing tests in `apps/agent_workflow_framework/tests/test_cli.py`**

Append to `apps/agent_workflow_framework/tests/test_cli.py`:

```python
    def test_cli_storage_dir_flag_isolates_runs(self):
        """Verify --storage-dir writes and lists runs exclusively in the custom directory."""
        with tempfile.TemporaryDirectory() as custom_dir:
            yaml_path = str(FIXTURES_DIR / "linear_workflow.yaml")
            code = cli_main(["--storage-dir", custom_dir, "run", yaml_path, "--run-id", "isolated-run-1"])
            self.assertEqual(code, 0)
            self.assertTrue((Path(custom_dir) / "isolated-run-1.json").is_file())

            list_code = cli_main(["--storage-dir", custom_dir, "list"])
            self.assertEqual(list_code, 0)

            inspect_code = cli_main(["--storage-dir", custom_dir, "inspect", "isolated-run-1"])
            self.assertEqual(inspect_code, 0)

    def test_pyproject_toml_defines_console_entry_point(self):
        """Verify pyproject.toml exists and registers agent-workflow CLI script."""
        import tomllib
        pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
        self.assertTrue(pyproject_path.is_file(), "apps/agent_workflow_framework/pyproject.toml must exist")
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        self.assertEqual(data["project"]["name"], "agent-workflow-framework")
        self.assertEqual(
            data["project"]["scripts"]["agent-workflow"],
            "agent_workflow.cli:main",
        )
```

- [x] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=/home/sak/Sak-Family-Agent/apps/agent_workflow_framework:/home/sak/Sak-Family-Agent/.venv/lib/python3.11/site-packages python3 -m unittest discover -s apps/agent_workflow_framework/tests -p "test_cli.py" -v`
Expected: FAIL (`unrecognized arguments: --storage-dir` and `apps/agent_workflow_framework/pyproject.toml must exist`).

- [x] **Step 3: Create `apps/agent_workflow_framework/pyproject.toml` and update `agent_workflow/cli.py` and `verify.py`**

Create `apps/agent_workflow_framework/pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agent-workflow-framework"
version = "0.1.0"
description = "Lightweight async DAG workflow engine with retry, state passing, and JSON run persistence"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "PyYAML>=6.0.1",
]

[project.scripts]
agent-workflow = "agent_workflow.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["agent_workflow"]
```

Update `apps/agent_workflow_framework/agent_workflow/cli.py` to support `--storage-dir` (and `AGENT_WORKFLOW_STORAGE_DIR` fallback):

```python
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from agent_workflow.dag import validate_workflow_dag
from agent_workflow.executor import WorkflowExecutor
from agent_workflow.models import RunStatus, StepStatus
from agent_workflow.parser import parse_workflow_file, WorkflowParseError
from agent_workflow.persistence import RunHistoryStore, RunNotFoundError


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser for agent_workflow CLI."""
    parser = argparse.ArgumentParser(
        prog="agent-workflow",
        description="Agent Workflow Framework CLI — Validate, Execute, and Inspect DAG Workflows.",
    )
    parser.add_argument(
        "--storage-dir",
        dest="storage_dir",
        default=os.environ.get("AGENT_WORKFLOW_STORAGE_DIR", ".workflow_runs"),
        help="Directory to store and read workflow run history (default: .workflow_runs).",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # 1. validate
    val_p = subparsers.add_parser("validate", help="Pre-flight validation of workflow definition files.")
    val_p.add_argument("file", help="Path to YAML or JSON workflow definition file.")

    # 2. run
    run_p = subparsers.add_parser("run", help="Execute workflow definition file.")
    run_p.add_argument("file", help="Path to YAML or JSON workflow definition file.")
    run_p.add_argument("--run-id", dest="run_id", help="Optional custom run ID.")

    # 3. inspect
    insp_p = subparsers.add_parser("inspect", help="Inspect past run history by run_id or file.")
    insp_p.add_argument("run_id", help="Run ID or path to run history JSON file.")
    insp_p.add_argument("--step", dest="step_id", help="Optional specific step ID to inspect.")

    # 4. list
    subparsers.add_parser("list", help="List stored workflow runs in .workflow_runs/.")

    return parser
```

And thread `storage_dir: str = ".workflow_runs"` into `cmd_run`, `cmd_inspect`, `cmd_list`, and `cli_main` in `apps/agent_workflow_framework/agent_workflow/cli.py`:
- In `cmd_run`: `executor = WorkflowExecutor(storage_dir=storage_dir)`
- In `cmd_inspect`: `store = RunHistoryStore(storage_dir=storage_dir)`
- In `cmd_list`: `store = RunHistoryStore(storage_dir=storage_dir)`
- In `cli_main`: pass `storage_dir=parsed.storage_dir` to `cmd_run`, `cmd_inspect`, and `cmd_list`.

In `apps/agent_workflow_framework/verify.py`, wrap `main()` execution with a `tempfile.TemporaryDirectory()` exported as `os.environ["AGENT_WORKFLOW_STORAGE_DIR"] = tmp_dir` and pass `storage_dir=os.environ.get("AGENT_WORKFLOW_STORAGE_DIR", ".workflow_runs")` to `WorkflowExecutor(...)` and `HistoryStore(...)`.

- [x] **Step 4: Run tests and `verify.py` to verify they pass**

Run: `PYTHONPATH=/home/sak/Sak-Family-Agent/apps/agent_workflow_framework:/home/sak/Sak-Family-Agent/.venv/lib/python3.11/site-packages python3 apps/agent_workflow_framework/verify.py`
Expected: PASS (all unit tests and Scenarios 1–5 pass, and `.workflow_runs` is not created in `apps/agent_workflow_framework/`).

- [x] **Step 5: Commit**

```bash
git add apps/agent_workflow_framework/pyproject.toml apps/agent_workflow_framework/agent_workflow/cli.py apps/agent_workflow_framework/verify.py apps/agent_workflow_framework/tests/test_cli.py
git commit -m "feat(agent_workflow): add pyproject.toml and --storage-dir isolation"
```

---

### Task 5: Refresh Dashboard System Snapshot & Sync Master `PLAN.md`

**Files:**
- Modify: `apps/sak_agent_dashboard/src/data/system-snapshot.json`
- Modify: `PLAN.md`
- Test: `tests/test_gen_system_snapshot.py`

**Interfaces:**
- Consumes: Refactored `personas/`, `scripts/`, `tests/`, and `.github/workflows/` layout via `scripts/gen_system_snapshot.py`.
- Produces: Up-to-date `apps/sak_agent_dashboard/src/data/system-snapshot.json` and updated `PLAN.md` with completed refactor items removed from the open backlog.

- [x] **Step 1: Run `scripts/gen_system_snapshot.py --check` to see if snapshot is stale**

Run: `PYTHONPATH=/home/sak/Sak-Family-Agent/personas/sakthai:/home/sak/Sak-Family-Agent/.venv/lib/python3.11/site-packages python3 scripts/gen_system_snapshot.py`
Expected: Writes updated test module count and persona skill metadata to `apps/sak_agent_dashboard/src/data/system-snapshot.json`.

- [x] **Step 2: Run the full fast structural & hygiene unittest suite**

Run: `python3 -m unittest tests/test_persona_structure_parity.py tests/test_persona_guardrails_parity.py tests/test_persona_web_server_parity.py tests/test_scripts_sys_path.py tests/test_repo_hygiene.py -v`
Expected: PASS (all tests green).

- [x] **Step 3: Update `PLAN.md` and immediately re-read `PLAN.md`**

Remove the completed P1 items (`P1 — Packaging & Import Ergonomics` and `P1 — Evaluation Isolation`) and the completed refactor plan item from `PLAN.md`, then immediately re-read `PLAN.md` to verify surrounding content is intact.

- [x] **Step 4: Commit**

```bash
git add apps/sak_agent_dashboard/src/data/system-snapshot.json PLAN.md docs/superpowers/plans/2026-11-13-whole-repo-refactor.md
git commit -m "chore(refactor): refresh system snapshot and update master PLAN.md"
```
