"""Tests for scripts/export_agent_repo.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "export_agent_repo.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("export_agent_repo", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


export_agent_repo = _load_module()


@pytest.fixture
def source_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "source"
    (root / "personas" / "shared" / "skills" / "shared-skill").mkdir(parents=True)
    (root / "personas" / "shared" / "skills" / "shared-skill" / "SKILL.md").write_text(
        "---\nname: Sak-shared-skill\n---\nshared\n", encoding="utf-8"
    )
    (root / "personas" / "shared" / "skills" / "sakthai-cycle-dream").mkdir(
        parents=True
    )
    (
        root
        / "personas"
        / "shared"
        / "skills"
        / "sakthai-cycle-dream"
        / "SKILL.md"
    ).write_text(
        "---\n"
        "name: sakthai-cycle-dream\n"
        "description: Use when testing exported cycle skill branding\n"
        "related_skills:\n"
        "  - sakthai-cycle-hope\n"
        "---\n"
        "# sakthai-cycle-dream\n"
        "\n"
        "Run `sakthai cycle next` when ready.\n",
        encoding="utf-8",
    )

    (root / "personas" / "sakjules" / "skills" / "overlay-skill").mkdir(
        parents=True
    )
    (root / "personas" / "sakjules" / "skills" / "overlay-skill" / "SKILL.md").write_text(
        "---\nname: SakJules-overlay-skill\n---\noverlay\n", encoding="utf-8"
    )
    (root / "personas" / "sakjules" / "SOUL.md").write_text(
        "SakJules soul", encoding="utf-8"
    )
    (root / "infra" / "hermes-agents" / "profiles" / "sakjules").mkdir(
        parents=True
    )
    (root / "infra" / "hermes-agents" / "profiles" / "sakjules" / "SOUL.md").write_text(
        "SakJules profile soul", encoding="utf-8"
    )
    (root / "infra" / "hermes-agents" / "profiles" / "sakjules" / "config.yaml").write_text(
        "model:\n  default: gemini-3-pro\n", encoding="utf-8"
    )
    (root / "infra" / "hermes-agents" / "profiles" / "sakking").mkdir(parents=True)
    (root / "infra" / "hermes-agents" / "profiles" / "sakking" / "SOUL.md").write_text(
        "Other profile", encoding="utf-8"
    )
    (root / "infra" / "hermes-agents" / "systemd").mkdir(parents=True)
    (
        root / "infra" / "hermes-agents" / "systemd" / "hermes-gateway-sakjules.service"
    ).write_text("sakjules service", encoding="utf-8")
    (
        root / "infra" / "hermes-agents" / "systemd" / "hermes-gateway-sakthai.service"
    ).write_text("sakthai service", encoding="utf-8")

    for rel in [
        ".gitignore",
        "AGENTS.md",
        "CLAUDE.md",
        "GEMINI.md",
        "SAKTHAI.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CHANGELOG.md",
        "pyproject.toml",
        "uv.lock",
    ]:
        (root / rel).write_text(rel, encoding="utf-8")

    (root / "scripts").mkdir()
    (root / "scripts" / "compose_persona.py").write_text("print('compose')\n", encoding="utf-8")
    (root / "scripts" / "__pycache__").mkdir()
    (root / "scripts" / "__pycache__" / "compose_persona.cpython-311.pyc").write_bytes(
        b"cache"
    )
    (root / "packages" / "agent-self-evolution" / "evolution").mkdir(parents=True)
    (root / "packages" / "agent-self-evolution" / "README.md").write_text(
        "Hermes Agent Self-Evolution", encoding="utf-8"
    )
    (root / "packages" / "agent-self-evolution" / "evolution" / "__init__.py").write_text(
        "", encoding="utf-8"
    )

    monkeypatch.setattr(export_agent_repo, "REPO_ROOT", root)
    return root


def test_export_creates_persona_specific_repo(
    source_tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = export_agent_repo.main(["sakjules", "--out", str(tmp_path / "out")])
    assert exit_code == 0
    out = tmp_path / "out"

    assert out == tmp_path / "out"
    assert (out / "README.md").read_text(encoding="utf-8").startswith(
        "# SakJules Repository"
    )
    assert "personas/shared/skills/" in (out / "README.md").read_text(encoding="utf-8")
    assert "beer-sakthai/sakjules-agent" in (out / "README.md").read_text(encoding="utf-8")
    assert "beer-sakthai/Sak-Family-Agent" in (out / "README.md").read_text(
        encoding="utf-8"
    )
    assert (out / "SOUL.md").read_text(encoding="utf-8") == "SakJules soul"
    assert "standalone" in (out / "AGENTS.md").read_text(encoding="utf-8")
    assert "beer-sakthai/sakjules-agent" in (out / "AGENTS.md").read_text(
        encoding="utf-8"
    )
    assert "Self-Evolution" in (out / "README.md").read_text(encoding="utf-8")
    assert "SakJules" in (out / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Supermemory" in (out / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Dream -> Hope -> Care -> Joy -> Trust -> Growth" in (
        out / "CLAUDE.md"
    ).read_text(encoding="utf-8")
    assert "avoid repeating the same failure" in (out / "CLAUDE.md").read_text(
        encoding="utf-8"
    )
    assert "SakJules" in (out / "GEMINI.md").read_text(encoding="utf-8")
    assert "Composio" in (out / "GEMINI.md").read_text(encoding="utf-8")
    assert not (out / "SAKTHAI.md").exists()
    assert "SakJules" in (out / "SAKJULES.md").read_text(encoding="utf-8")
    assert (out / "personas" / "shared" / "skills" / "shared-skill" / "SKILL.md").is_file()
    assert not (
        out / "personas" / "shared" / "skills" / "sakthai-cycle-dream"
    ).exists()
    cycle_skill = (
        out
        / "personas"
        / "shared"
        / "skills"
        / "SakJules-cycle-dream"
        / "SKILL.md"
    )
    cycle_skill_text = cycle_skill.read_text(encoding="utf-8")
    assert "name: SakJules-cycle-dream" in cycle_skill_text
    assert "- SakJules-cycle-hope" in cycle_skill_text
    assert "# SakJules-cycle-dream" in cycle_skill_text
    assert "`sakthai cycle next`" in cycle_skill_text
    assert (out / "personas" / "sakjules" / "skills" / "overlay-skill" / "SKILL.md").is_file()
    assert (out / "packages" / "agent-self-evolution" / "README.md").is_file()
    assert (out / "packages" / "agent-self-evolution" / "evolution" / "__init__.py").is_file()
    assert (out / "uv.lock").is_file()
    assert not any(out.rglob("__pycache__"))
    assert not any(out.rglob("*.pyc"))
    assert not (out / "personas" / "sakthai").exists()
    assert (out / "infra" / "hermes-agents" / "profiles" / "sakjules" / "SOUL.md").is_file()
    assert not (out / "infra" / "hermes-agents" / "profiles" / "sakking").exists()
    assert (
        out
        / "infra"
        / "hermes-agents"
        / "systemd"
        / "hermes-gateway-sakjules.service"
    ).is_file()
    assert not (
        out
        / "infra"
        / "hermes-agents"
        / "systemd"
        / "hermes-gateway-sakthai.service"
    ).exists()
    assert "exported sakjules ->" in capsys.readouterr().out


def test_export_wipes_stale_output(source_tree: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "stale.txt").write_text("leftover", encoding="utf-8")

    export_agent_repo.export_agent_repo("sakjules", out_dir)

    assert not (out_dir / "stale.txt").exists()


def test_export_rejects_unknown_persona(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        export_agent_repo.export_agent_repo("not-a-persona", tmp_path / "out")
