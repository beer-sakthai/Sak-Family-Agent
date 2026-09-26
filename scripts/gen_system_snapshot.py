#!/usr/bin/env python3
"""Snapshot this repository's own structure for the dashboard's System view.

The hosted dashboard (Vercel) has no ``~/.sakthai`` and no live agent behind
it, so every runtime section there shows sample data. What it *can* show for
real is the repo itself: the personas and their models, the package's
subsystems, the built-in tools, the CLI tree, the CI workflows and the test
trees. This script reads all of that from the code and config — nothing is
typed in by hand — and writes it to
``apps/sak_agent_dashboard/src/data/system-snapshot.json``.

Usage::

    python scripts/gen_system_snapshot.py            # write the file
    make system-snapshot                              # same

Output is deterministic apart from ``meta`` (source commit and date), which the
dashboard shows so a stale snapshot is visible rather than silently wrong.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# There is no root-level `sakthai/` package; the installed one lives here.
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

import click  # noqa: E402
import yaml  # noqa: E402

from sakthai import config  # noqa: E402
from sakthai.agent.tools import BUILTIN_TOOLS  # noqa: E402
from sakthai.cli import main as cli_main  # noqa: E402

OUTPUT_PATH = REPO_ROOT / "apps" / "sak_agent_dashboard" / "src" / "data" / "system-snapshot.json"
PACKAGE_DIR = REPO_ROOT / "personas" / "sakthai" / "sakthai"
LEAD_PERSONA = "sakthai"

# Tools the agent loop never offers the model (see agent/tools.py: the nested
# loop filters it out to prevent self-recursion). MCP clients still see it.
MCP_ONLY_TOOLS = frozenset({"run_agent_loop"})

# Test trees outside tests/, per CLAUDE.md. Each is (label, dir, glob, runner).
_OTHER_TEST_TREES = (
    ("agent_workflow_framework", "apps/agent_workflow_framework/tests", "test_*.py", "apps.yml"),
    ("sak_agent_dashboard", "apps/sak_agent_dashboard/src/tests", "*.test.ts*", "apps.yml"),
    ("sakthai-chat-cli", "sakthai-chat-cli/tests", "test_*.py", "subprojects.yml"),
    ("teams-copilot-mcp", "services/teams-copilot-mcp/tests", "test_*.py", "subprojects.yml"),
)


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _first_sentence(text: str, limit: int = 160) -> str:
    text = " ".join(text.split())
    match = re.match(r"(.+?[.!?])(\s|$)", text)
    sentence = match.group(1) if match else text
    return sentence if len(sentence) <= limit else sentence[: limit - 1].rstrip() + "…"


def _skill_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _personas() -> list[dict[str, Any]]:
    personas = []
    for name in config.PERSONA_NAMES:
        workspace = _read_yaml(REPO_ROOT / "personas" / name / "config" / "workspace.yaml")
        provider, model = config.persona_model_defaults(name)
        mcp = {}
        mcp_path = config.persona_mcp_config_path(name)
        if mcp_path.is_file():
            try:
                mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                mcp = {}
        servers = mcp.get("mcpServers") or mcp.get("servers") or {}
        server_names = sorted(servers) if isinstance(servers, dict) else sorted(
            s.get("name", "?") for s in servers if isinstance(s, dict)
        )
        personas.append(
            {
                "name": name,
                "lead": name == LEAD_PERSONA,
                "role": str(workspace.get("role") or ""),
                "domain": str(workspace.get("domain") or ""),
                "provider": provider,
                "model": model,
                "skill_count": len(_skill_dirs(config.persona_skills_dir(name))),
                "mcp_servers": server_names,
            }
        )
    return personas


def _package() -> list[dict[str, Any]]:
    """Top-level modules and subpackages of the installed package, with LOC."""
    entries = []
    for path in sorted(PACKAGE_DIR.iterdir()):
        if path.name.startswith(("_", ".")) or path.name == "__pycache__":
            continue
        if path.is_dir():
            files = sorted(path.rglob("*.py"))
            if not files:
                continue
            kind = "package"
        elif path.suffix == ".py":
            files = [path]
            kind = "module"
        else:
            continue
        lines = sum(len(f.read_text(encoding="utf-8").splitlines()) for f in files)
        entries.append(
            {"name": path.stem, "kind": kind, "files": len(files), "lines": lines}
        )
    return entries


def _tools() -> list[dict[str, Any]]:
    return [
        {
            "name": tool.name,
            "summary": _first_sentence(tool.description),
            "mcp_only": tool.name in MCP_ONLY_TOOLS,
        }
        for tool in BUILTIN_TOOLS
    ]


def _cli(command: click.Command, name: str) -> dict[str, Any]:
    node: dict[str, Any] = {
        "name": name,
        "help": command.get_short_help_str(limit=100),
    }
    if isinstance(command, click.Group):
        node["commands"] = [
            _cli(sub, sub_name)
            for sub_name, sub in sorted(command.commands.items())
            if not sub.hidden
        ]
    return node


def _workflows() -> list[dict[str, Any]]:
    workflows = []
    for path in sorted((REPO_ROOT / ".github" / "workflows").glob("*.y*ml")):
        data = _read_yaml(path)
        # YAML 1.1 reads a bare `on:` key as the boolean True.
        on = data.get("on", data.get(True, {}))
        if isinstance(on, str):
            triggers = [on]
        elif isinstance(on, list):
            triggers = [str(t) for t in on]
        elif isinstance(on, dict):
            triggers = [str(t) for t in on]
        else:
            triggers = []
        jobs = data.get("jobs") or {}
        workflows.append(
            {
                "file": path.name,
                "name": str(data.get("name") or path.stem),
                "triggers": sorted(triggers),
                "gates_prs": any(t in ("pull_request", "pull_request_target") for t in triggers),
                "jobs": sorted(
                    str(job.get("name") or job_id) if isinstance(job, dict) else str(job_id)
                    for job_id, job in jobs.items()
                ),
            }
        )
    return workflows


def _count_test_functions(files: list[Path]) -> int:
    count = 0
    for file in files:
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        count += sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name.startswith("test_")
        )
    return count


def _tests() -> dict[str, Any]:
    main_files = sorted((REPO_ROOT / "tests").glob("test_*.py"))
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    floor = re.search(r"--cov-fail-under=(\d+(?:\.\d+)?)", ci_text)
    trees = [
        {
            "name": "sakthai (tests/)",
            "path": "tests",
            "files": len(main_files),
            "runner": "ci.yml",
        }
    ]
    for label, rel, pattern, runner in _OTHER_TEST_TREES:
        root = REPO_ROOT / rel
        files = sorted(root.rglob(pattern)) if root.is_dir() else []
        trees.append({"name": label, "path": rel, "files": len(files), "runner": runner})
    return {
        "coverage_floor": float(floor.group(1)) if floor else None,
        "test_functions": _count_test_functions(main_files),
        "trees": trees,
    }


def _skills() -> dict[str, Any]:
    library = REPO_ROOT / "library"
    categories = sorted(p for p in library.iterdir() if p.is_dir()) if library.is_dir() else []
    shared = _skill_dirs(REPO_ROOT / "personas" / "shared" / "skills")
    return {
        "shared": [p.name for p in shared],
        "library_categories": [
            {"name": c.name, "skills": len(_skill_dirs(c))} for c in categories if _skill_dirs(c)
        ],
    }


def _meta() -> dict[str, Any]:
    def git(*args: str) -> str:
        try:
            return subprocess.run(  # noqa: S603 - fixed argv, no shell
                ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return ""

    return {
        "source_commit": git("rev-parse", "--short", "HEAD") or None,
        "source_date": git("log", "-1", "--format=%cI") or None,
        "generator": "scripts/gen_system_snapshot.py",
    }


def build_snapshot() -> dict[str, Any]:
    """Everything the System view renders. Pure apart from ``meta``."""
    return {
        "meta": _meta(),
        "personas": _personas(),
        "package": _package(),
        "tools": _tools(),
        "cli": _cli(cli_main, "sakthai"),
        "workflows": _workflows(),
        "tests": _tests(),
        "skills": _skills(),
    }


def render(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render(build_snapshot()), encoding="utf-8")
    print(f"wrote {_rel(OUTPUT_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
