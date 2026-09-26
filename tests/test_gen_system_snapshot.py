"""The System-view snapshot generator reads the repo, not a hand-typed list.

`scripts/gen_system_snapshot.py` feeds the hosted dashboard's only real-data
section. These tests pin its output to the live code — the persona tuple, the
tool registry, the click tree, the workflow files — so a refactor that breaks
a reader fails here instead of shipping a wrong or empty panel. They check
structure against the code, not the committed JSON's counts: skills are added
constantly, and a snapshot one skill behind is stale, not broken.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from sakthai import config
from sakthai.agent.tools import BUILTIN_TOOLS

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "gen_system_snapshot.py"


@pytest.fixture(scope="module")
def gen() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gen_system_snapshot", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def snapshot(gen: ModuleType) -> dict[str, Any]:
    result: dict[str, Any] = gen.build_snapshot()
    return result


def test_personas_match_the_config_tuple_with_one_lead(snapshot: dict[str, Any]) -> None:
    names = [p["name"] for p in snapshot["personas"]]
    assert names == list(config.PERSONA_NAMES)
    assert [p["name"] for p in snapshot["personas"] if p["lead"]] == ["sakthai"]


def test_personas_carry_role_model_and_skill_counts(snapshot: dict[str, Any]) -> None:
    for persona in snapshot["personas"]:
        provider, model = config.persona_model_defaults(persona["name"])
        assert (persona["provider"], persona["model"]) == (provider, model)
        assert persona["role"], f"{persona['name']} has no role in its workspace.yaml"
        skills_dir = config.persona_skills_dir(persona["name"])
        expected = sum(1 for p in skills_dir.iterdir() if (p / "SKILL.md").is_file())
        assert persona["skill_count"] == expected


def test_tools_are_the_builtin_registry(snapshot: dict[str, Any]) -> None:
    assert [t["name"] for t in snapshot["tools"]] == [t.name for t in BUILTIN_TOOLS]
    assert [t["name"] for t in snapshot["tools"] if t["mcp_only"]] == ["run_agent_loop"]
    assert all(t["summary"] for t in snapshot["tools"])


def test_cli_tree_comes_from_click(snapshot: dict[str, Any]) -> None:
    top = {c["name"]: c for c in snapshot["cli"]["commands"]}
    assert {"run", "chat", "mcp", "memory", "web"} <= set(top)
    assert "commands" not in top["run"]  # a leaf
    assert "forget" in {c["name"] for c in top["memory"]["commands"]}


def test_workflows_cover_every_file_and_read_bare_on_keys(snapshot: dict[str, Any]) -> None:
    files = sorted(p.name for p in (REPO_ROOT / ".github" / "workflows").glob("*.y*ml"))
    assert [w["file"] for w in snapshot["workflows"]] == files
    ci = next(w for w in snapshot["workflows"] if w["file"] == "ci.yml")
    # `on:` parses as the boolean True under YAML 1.1; triggers must survive that.
    assert "pull_request" in ci["triggers"]
    assert ci["gates_prs"] is True


def test_tests_section_reads_the_enforced_coverage_floor(snapshot: dict[str, Any]) -> None:
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert f"--cov-fail-under={int(snapshot['tests']['coverage_floor'])}" in ci_text
    assert snapshot["tests"]["test_functions"] > 0
    main_tree = snapshot["tests"]["trees"][0]
    assert main_tree["files"] == len(list((REPO_ROOT / "tests").glob("test_*.py")))


def test_package_lists_real_subsystems(snapshot: dict[str, Any]) -> None:
    names = {m["name"] for m in snapshot["package"]}
    assert {"agent", "memory", "mcp", "cli", "web", "config"} <= names
    assert all(m["lines"] > 0 for m in snapshot["package"])


def test_output_is_deterministic_apart_from_meta(gen: ModuleType) -> None:
    first = gen.build_snapshot()
    second = gen.build_snapshot()
    first.pop("meta")
    second.pop("meta")
    assert gen.render(first) == gen.render(second)
