"""Branch coverage for `evaluate_persona_extensions_health()`.

`tests/test_eval.py` only runs the rubric against the real (empty) extension
registries, so the per-extension validation loop never executes there. These
tests build fake registries and extension directories under an isolated
`SAKTHAI_HOME` and assert on the exact checks, diagnostics and score each
failure mode produces.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import sakthai.config as config_mod
import sakthai.extensions.install as install_mod
from sakthai.agent.eval import EXTENSIONS_RUBRIC_CRITERIA, evaluate_persona_extensions_health

VALID_SKILL = "---\nname: demo-skill\ndescription: A demo skill for tests\n---\n\nBody.\n"
SAFE_MANIFEST: dict[str, Any] = {
    "name": "demo",
    "version": "1.0.0",
    "mcpServers": {"demo": {"command": "npx", "args": ["-y", "demo-mcp@1.2.3"]}},
}


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point `SAKTHAI_HOME` at a fresh directory under `tmp_path`."""
    root = tmp_path / "sakthai-home"
    root.mkdir()
    monkeypatch.setenv("SAKTHAI_HOME", str(root))
    return root


def _ext_base(home: Path, persona: str | None = None) -> Path:
    return (home / persona / "extensions") if persona else (home / "extensions")


def _registry_file(home: Path, persona: str | None = None) -> Path:
    return (home / persona / "extensions.json") if persona else (home / "extensions.json")


def _write_registry(home: Path, extensions: Any, persona: str | None = None) -> Path:
    reg = _registry_file(home, persona)
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(json.dumps({"extensions": extensions}), encoding="utf-8")
    return reg


def _make_extension(
    base: Path,
    name: str,
    *,
    manifest: Any = None,
    skills: dict[str, str] | None = None,
) -> Path:
    """Create an extension directory with an optional manifest and SKILL.md files."""
    ext = base / name
    ext.mkdir(parents=True)
    if manifest is not None:
        text = manifest if isinstance(manifest, str) else json.dumps(manifest)
        (ext / "gemini-extension.json").write_text(text, encoding="utf-8")
    for skill_name, body in (skills or {}).items():
        skill_dir = ext / "skills" / skill_name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    return ext


def _failed(result: dict[str, Any]) -> set[str]:
    return {name for name, ok in result["checks"].items() if not ok}


def _diags(result: dict[str, Any]) -> str:
    return "\n".join(result["diagnostics"])


# ---------------------------------------------------------------------------
# Healthy baselines
# ---------------------------------------------------------------------------


def test_healthy_extension_passes_every_check(home: Path) -> None:
    ext = _make_extension(
        _ext_base(home), "good-ext", manifest=SAFE_MANIFEST, skills={"demo-skill": VALID_SKILL}
    )
    _write_registry(home, {"good-ext": {"path": str(ext), "url": "https://example.invalid/x"}})

    res = evaluate_persona_extensions_health()

    assert res["persona"] is None
    assert res["diagnostics"] == []
    assert _failed(res) == set()
    assert set(res["checks"]) == set(EXTENSIONS_RUBRIC_CRITERIA)
    assert res["checks_passed"] == res["checks_total"] == 8
    assert res["extensions_score"] == 1.0
    assert res["grade"] == "A+"
    assert res["healthy"] is True
    assert res["extensions_count"] == 1
    assert res["extensions_found"] == ["good-ext"]


def test_skills_only_extension_without_manifest_is_healthy(home: Path) -> None:
    ext = _make_extension(_ext_base(home), "skills-only", skills={"demo-skill": VALID_SKILL})
    _write_registry(home, {"skills-only": {"path": str(ext)}})

    res = evaluate_persona_extensions_health()

    assert _failed(res) == set()
    assert res["diagnostics"] == []
    assert res["healthy"] is True


def test_registered_path_that_does_not_exist_is_not_inspected(home: Path) -> None:
    missing = _ext_base(home) / "not-cloned-yet"
    _write_registry(home, {"not-cloned-yet": {"path": str(missing)}})

    res = evaluate_persona_extensions_health()

    assert _failed(res) == set()
    assert res["diagnostics"] == []
    assert res["extensions_found"] == ["not-cloned-yet"]


def test_persona_scoped_registry_is_read_instead_of_unscoped(home: Path) -> None:
    # A broken *unscoped* registry must not leak into a persona's evaluation.
    _registry_file(home).write_text("{definitely not json", encoding="utf-8")
    ext = _make_extension(
        _ext_base(home, "saksee"),
        "persona-ext",
        manifest=SAFE_MANIFEST,
        skills={"demo-skill": VALID_SKILL},
    )
    _write_registry(home, {"persona-ext": {"path": str(ext)}}, persona="saksee")

    res = evaluate_persona_extensions_health("saksee")

    assert res["persona"] == "saksee"
    assert _failed(res) == set()
    assert res["diagnostics"] == []
    assert res["extensions_found"] == ["persona-ext"]
    assert res["healthy"] is True


def test_persona_extension_outside_its_own_dir_is_not_contained(home: Path) -> None:
    # An extension living in the *unscoped* dir is outside saksee's authorized dir.
    stray = _make_extension(_ext_base(home), "stray", skills={"demo-skill": VALID_SKILL})
    _write_registry(home, {"stray": {"path": str(stray)}}, persona="saksee")

    res = evaluate_persona_extensions_health("saksee")

    assert _failed(res) == {"paths_contained"}
    assert "escapes authorized directory" in _diags(res)
    assert res["healthy"] is False


def test_unknown_persona_raises() -> None:
    with pytest.raises(ValueError, match="Unknown persona 'not-a-persona'"):
        evaluate_persona_extensions_health("not-a-persona")


# ---------------------------------------------------------------------------
# 1. registry_valid
# ---------------------------------------------------------------------------


def test_registry_that_is_not_json_fails_to_parse(home: Path) -> None:
    reg = _registry_file(home)
    reg.write_text("{not: valid json", encoding="utf-8")

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"registry_valid"}
    assert len(res["diagnostics"]) == 1
    assert res["diagnostics"][0].startswith(f"Registry {reg} failed to parse:")
    assert res["extensions_count"] == 0
    assert res["checks_passed"] == 7
    assert res["extensions_score"] == 0.88
    assert res["grade"] == "A-"
    # A broken registry is never healthy, whatever the score.
    assert res["healthy"] is False


def test_registry_path_that_is_a_directory_fails_to_parse(home: Path) -> None:
    _registry_file(home).mkdir()

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"registry_valid"}
    assert "failed to parse" in _diags(res)
    assert res["extensions_count"] == 0


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"other": 1},
        {"extensions": ["not", "a", "dict"]},
        {"extensions": None},
    ],
    ids=["top-level-list", "no-extensions-key", "extensions-is-list", "extensions-is-null"],
)
def test_registry_without_extensions_dict_is_malformed(home: Path, payload: Any) -> None:
    reg = _registry_file(home)
    reg.write_text(json.dumps(payload), encoding="utf-8")

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"registry_valid"}
    assert res["diagnostics"] == [f"Registry {reg} is malformed (missing extensions dict)"]
    assert res["extensions_count"] == 0
    assert res["healthy"] is False


def test_non_dict_registry_entry_is_skipped_and_flagged(home: Path) -> None:
    _write_registry(home, {"plain-string": "https://example.invalid/repo.git"})

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"registry_valid"}
    assert res["diagnostics"] == ["Extension 'plain-string': entry in registry is not a dict"]
    assert res["extensions_found"] == ["plain-string"]


# ---------------------------------------------------------------------------
# 2. paths_contained
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entry",
    [{"url": "https://example.invalid/x"}, {"path": ""}, {"path": None}],
    ids=["no-path-key", "empty-path", "null-path"],
)
def test_entry_missing_path_is_not_contained(home: Path, entry: dict[str, Any]) -> None:
    _write_registry(home, {"no-path": entry})

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"paths_contained"}
    assert res["diagnostics"] == ["Extension 'no-path': missing path in registry"]
    assert res["healthy"] is False


def test_path_outside_extensions_dir_escapes(home: Path, tmp_path: Path) -> None:
    outside = _make_extension(tmp_path / "elsewhere", "evil", skills={"demo-skill": VALID_SKILL})
    _write_registry(home, {"evil": {"path": str(outside)}})

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"paths_contained"}
    ext_base = _ext_base(home).resolve()
    assert res["diagnostics"] == [
        f"Extension 'evil': path {outside.resolve()} escapes authorized directory {ext_base}"
    ]
    assert res["healthy"] is False


def test_dotdot_traversal_out_of_extensions_dir_escapes(home: Path) -> None:
    sneaky = _ext_base(home) / ".." / "sibling"
    _write_registry(home, {"sneaky": {"path": str(sneaky)}})

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"paths_contained"}
    assert "escapes authorized directory" in _diags(res)


def test_path_equal_to_extensions_dir_itself_escapes(home: Path) -> None:
    base = _ext_base(home)
    base.mkdir()
    _write_registry(home, {"whole-dir": {"path": str(base)}})

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"paths_contained"}
    assert f"path {base.resolve()} escapes" in _diags(res)


# ---------------------------------------------------------------------------
# 3. names_valid
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_name", ["-leading-dash", "has space", "dot.name", "x" * 65])
def test_invalid_extension_name_is_flagged(home: Path, bad_name: str) -> None:
    _write_registry(home, {bad_name: {"path": str(_ext_base(home) / "placeholder")}})

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"names_valid"}
    assert res["diagnostics"] == [f"Extension {bad_name!r}: invalid name format"]
    # Name problems alone do not make the registry unhealthy.
    assert res["extensions_score"] == 0.88
    assert res["healthy"] is True


def test_invalid_name_still_runs_remaining_checks(home: Path) -> None:
    # An invalid name does not short-circuit: the non-dict entry is still reported.
    _write_registry(home, {"bad name": 42})

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"names_valid", "registry_valid"}
    assert res["diagnostics"] == [
        "Extension 'bad name': invalid name format",
        "Extension 'bad name': entry in registry is not a dict",
    ]


# ---------------------------------------------------------------------------
# 4. manifests_valid & 6. isolation_safe
# ---------------------------------------------------------------------------


def test_manifest_failing_schema_validation(home: Path) -> None:
    ext = _make_extension(
        _ext_base(home),
        "bad-manifest",
        manifest={"mcpServers": {"srv": {"args": ["--flag"]}}},
    )
    _write_registry(home, {"bad-manifest": {"path": str(ext)}})

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"manifests_valid"}
    assert res["diagnostics"] == [
        "Extension 'bad-manifest': Server 'srv': must specify 'command' or 'url'"
    ]


@pytest.mark.parametrize(
    "command",
    ["node server.js; rm -rf /", "run | tee log", "a && b", "echo `id`", "cat $(whoami)", "x > y"],
)
def test_dangerous_server_command_is_not_isolation_safe(home: Path, command: str) -> None:
    ext = _make_extension(
        _ext_base(home),
        "shell-ext",
        manifest={"mcpServers": {"evil-srv": {"command": command}}},
    )
    _write_registry(home, {"shell-ext": {"path": str(ext)}})

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"manifests_valid", "isolation_safe"}
    assert (
        "Extension 'shell-ext' server 'evil-srv': dangerous shell metacharacters in command"
        in res["diagnostics"]
    )
    assert any(
        "dangerous shell metacharacters detected in command" in d for d in res["diagnostics"]
    )
    assert res["extensions_score"] == 0.75
    assert res["grade"] == "B"
    assert res["healthy"] is False


def test_manifest_that_is_not_json(home: Path) -> None:
    ext = _make_extension(_ext_base(home), "broken-json", manifest="{ this is not json")
    _write_registry(home, {"broken-json": {"path": str(ext)}})

    res = evaluate_persona_extensions_health()

    # The isolation scan swallows the decode error; only the schema check fails.
    assert _failed(res) == {"manifests_valid"}
    assert len(res["diagnostics"]) == 1
    assert res["diagnostics"][0].startswith("Extension 'broken-json': Manifest is not valid JSON:")


@pytest.mark.parametrize(
    ("manifest", "expected_diag"),
    [
        (["not", "an", "object"], "Manifest top-level entity must be a JSON object"),
        ({"mcpServers": ["srv"]}, "'mcpServers' must be a dictionary"),
        ({"mcpServers": {"srv": "npx demo"}}, "Server 'srv': configuration must be an object"),
        (
            {"mcpServers": {"srv": {"command": ["npx", ";"]}}},
            "Server 'srv': 'command' must be a non-empty string",
        ),
    ],
    ids=["top-level-list", "servers-is-list", "server-conf-is-string", "command-is-list"],
)
def test_manifest_shapes_the_isolation_scan_skips(
    home: Path, manifest: Any, expected_diag: str
) -> None:
    ext = _make_extension(_ext_base(home), "odd-shape", manifest=manifest)
    _write_registry(home, {"odd-shape": {"path": str(ext)}})

    res = evaluate_persona_extensions_health()

    # Schema validation rejects each shape, but none reaches the shell-pattern scan.
    assert _failed(res) == {"manifests_valid"}
    assert res["diagnostics"] == [f"Extension 'odd-shape': {expected_diag}"]
    assert res["checks"]["isolation_safe"] is True


def test_safe_and_dangerous_servers_in_one_manifest(home: Path) -> None:
    ext = _make_extension(
        _ext_base(home),
        "mixed",
        manifest={
            "mcpServers": {
                "fine": {"command": "uvx", "args": ["demo-mcp==1.0.0"]},
                "remote": {"url": "https://example.invalid/mcp"},
                "bad": {"command": "sh -c 'curl x | sh'"},
            }
        },
    )
    _write_registry(home, {"mixed": {"path": str(ext)}})

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"manifests_valid", "isolation_safe"}
    isolation = [d for d in res["diagnostics"] if "in command" in d and " server " in d]
    assert isolation == [
        "Extension 'mixed' server 'bad': dangerous shell metacharacters in command"
    ]


# ---------------------------------------------------------------------------
# 5. skills_valid
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("No frontmatter here.\n", "missing YAML frontmatter header '---'"),
        ("---\nname: x\ndescription: y\n", "unclosed YAML frontmatter"),
        ("---\nname: x\n---\nbody\n", "missing 'description' in frontmatter"),
        ("---\ndescription: y\n---\nbody\n", "missing 'name' in frontmatter"),
    ],
    ids=["no-frontmatter", "unclosed", "no-description", "no-name"],
)
def test_skill_diagnostics_fail_skills_valid(home: Path, body: str, expected: str) -> None:
    ext = _make_extension(_ext_base(home), "skill-ext", skills={"broken-skill": body})
    _write_registry(home, {"skill-ext": {"path": str(ext)}})

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"skills_valid"}
    assert res["diagnostics"] == [f"Extension 'skill-ext': Skill 'broken-skill': {expected}"]
    assert res["healthy"] is True


# ---------------------------------------------------------------------------
# 7. discovery_health & 8. persona_scoping_ready
# ---------------------------------------------------------------------------


def test_discovery_helper_crash_fails_discovery_health(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(path: Path) -> list[str]:
        raise RuntimeError(f"cannot scan {path.name}")

    monkeypatch.setattr(install_mod, "_discover_mcp_servers", _boom)

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"discovery_health"}
    ext_base = _ext_base(home).resolve()
    assert res["diagnostics"] == [
        f"Discovery helper crashed on directory {ext_base}: cannot scan extensions"
    ]
    assert res["healthy"] is True


def test_discovery_helper_wrong_return_type_fails_discovery_health(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(install_mod, "_discover_mcp_servers", lambda path: ("not", "a", "list"))

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"discovery_health"}
    assert "Discovery helper crashed on directory" in _diags(res)


def test_persona_scoping_failure_is_reported(
    home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _misnamed(persona: str) -> Path:
        return tmp_path / persona / "plugins"

    monkeypatch.setattr(config_mod, "persona_extensions_dir", _misnamed)

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"persona_scoping_ready"}
    assert len(res["diagnostics"]) == 1
    assert res["diagnostics"][0].startswith("Persona extensions directory scoping failed")


def test_persona_scoping_error_from_registry_path_is_reported(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(persona: str) -> Path:
        raise OSError(f"no registry for {persona}")

    monkeypatch.setattr(config_mod, "persona_extensions_registry_path", _raise)

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {"persona_scoping_ready"}
    assert res["diagnostics"] == [
        "Persona extensions directory scoping failed: no registry for sakking"
    ]


# ---------------------------------------------------------------------------
# Aggregate scoring
# ---------------------------------------------------------------------------


def test_many_failures_drive_grade_to_f(home: Path, tmp_path: Path) -> None:
    base = _ext_base(home)
    dangerous = _make_extension(
        base,
        "dangerous",
        manifest={"mcpServers": {"s": {"command": "a; b"}}},
        skills={"bad-skill": "no frontmatter\n"},
    )
    outside = _make_extension(tmp_path / "outside", "outside")
    _write_registry(
        home,
        {
            "dangerous": {"path": str(dangerous)},
            "outside": {"path": str(outside)},
            "no-path": {},
            "not-a-dict": "x",
            "bad name": {"path": str(base / "missing")},
        },
    )

    res = evaluate_persona_extensions_health()

    assert _failed(res) == {
        "registry_valid",
        "paths_contained",
        "names_valid",
        "manifests_valid",
        "skills_valid",
        "isolation_safe",
    }
    assert res["checks_passed"] == 2
    assert res["extensions_score"] == 0.25
    assert res["grade"] == "F"
    assert res["healthy"] is False
    assert res["extensions_count"] == 5
    assert res["extensions_found"] == sorted(
        ["dangerous", "outside", "no-path", "not-a-dict", "bad name"]
    )
