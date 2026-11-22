"""Tests for sakthai.extensions.install.

Git is never actually invoked: ``install_extension`` is exercised by monkeypatching
``subprocess.run`` so the clone is simulated on the local filesystem. The
``sakthai_home`` fixture redirects the extensions dir and registry into tmp.
"""

from __future__ import annotations

import json
import subprocess
import types
from collections.abc import Callable
from pathlib import Path

import pytest

import sakthai.extensions.install as ext

# -- helpers -------------------------------------------------------------


def _fake_clone(*, with_skill: bool = True, with_mcp: bool = True) -> Callable[..., object]:
    """Return a subprocess.run stand-in that materialises a cloned repo."""

    def _run(cmd: list[str], *args: object, **kwargs: object) -> object:
        dest = Path(cmd[-1])
        dest.mkdir(parents=True, exist_ok=True)
        if with_skill:
            skill = dest / "myskill"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: myskill\ndescription: demo skill\n---\nbody\n", encoding="utf-8"
            )
        if with_mcp:
            (dest / "gemini-extension.json").write_text(
                json.dumps({"mcpServers": {"srv": {"command": "echo", "args": ["hello"]}}}),
                encoding="utf-8",
            )
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    return _run


# -- _name_from_url ------------------------------------------------------


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/foo/bar.git", "bar"),
        ("https://github.com/foo/bar", "bar"),
        ("https://github.com/foo/bar/", "bar"),
        ("git@github.com:foo/baz.git", "baz"),
    ],
)
def test_name_from_url(url: str, expected: str) -> None:
    assert ext._name_from_url(url) == expected


def test_extension_name_regex_accepts_and_rejects() -> None:
    assert ext.EXTENSION_NAME_RE.match("good-name_1")
    assert not ext.EXTENSION_NAME_RE.match("@bad")
    assert not ext.EXTENSION_NAME_RE.match("")


def test_install_rejects_traversal_name_derived_from_url(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Name filter blocks path traversal: a ``../``-laden name never installs.

    The name regex is the first line of defense here; assert the public API
    surfaces an ExtensionError rather than cloning outside the extensions dir.
    """
    with pytest.raises(ext.ExtensionError, match="invalid extension name"):
        ext.install_extension("https://github.com/foo/..%2f..%2fevil.git")


def test_install_path_guard_blocks_escape_if_name_filter_regresses(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Defense-in-depth: the resolved-path check catches a traversal name that
    slips past the regex, so a future loosening of the filter still can't write
    outside the extensions dir.
    """
    monkeypatch.setattr(ext, "EXTENSION_NAME_RE", ext.re.compile(r".*"))
    monkeypatch.setattr(ext, "_name_from_url", lambda url: "../escape")
    with pytest.raises(ext.ExtensionError, match="invalid extension path"):
        ext.install_extension("https://github.com/foo/whatever.git")


# -- registry round-trip -------------------------------------------------


def test_registry_default_when_absent(sakthai_home: Path) -> None:
    assert ext._load_registry() == {"extensions": {}}


def test_registry_save_and_load(sakthai_home: Path) -> None:
    ext._save_registry({"extensions": {"a": {"url": "u", "path": "p"}}})
    assert ext._load_registry()["extensions"]["a"]["url"] == "u"


def test_registry_corrupt_file_falls_back(sakthai_home: Path) -> None:
    ext._registry_path().write_text("{garbage", encoding="utf-8")
    assert ext._load_registry() == {"extensions": {}}


# -- discovery -----------------------------------------------------------


def test_discover_skills(tmp_path: Path) -> None:
    (tmp_path / "alpha").mkdir()
    (tmp_path / "alpha" / "SKILL.md").write_text("x", encoding="utf-8")
    (tmp_path / "beta").mkdir()
    (tmp_path / "beta" / "SKILL.md").write_text("y", encoding="utf-8")
    assert ext._discover_skills(tmp_path) == ["alpha", "beta"]


def test_discover_mcp_servers(tmp_path: Path) -> None:
    (tmp_path / "gemini-extension.json").write_text(
        json.dumps({"mcpServers": {"b": {}, "a": {}}}), encoding="utf-8"
    )
    assert ext._discover_mcp_servers(tmp_path) == ["a", "b"]


def test_discover_mcp_servers_missing_manifest(tmp_path: Path) -> None:
    assert ext._discover_mcp_servers(tmp_path) == []


def test_discover_mcp_servers_corrupt_manifest_returns_empty(tmp_path: Path) -> None:
    (tmp_path / "gemini-extension.json").write_text("{corrupt json{{", encoding="utf-8")
    assert ext._discover_mcp_servers(tmp_path) == []


# -- install -------------------------------------------------------------


def test_install_rejects_invalid_name(sakthai_home: Path) -> None:
    with pytest.raises(ext.ExtensionError, match="invalid extension name"):
        ext.install_extension("https://example.com/foo/@bad")


def test_install_happy_path(sakthai_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ext.subprocess, "run", _fake_clone())
    result = ext.install_extension("https://github.com/foo/bar")
    assert result.already_installed is False
    assert result.extension.name == "bar"
    assert result.skills_found == ["myskill"]
    assert result.mcp_servers_found == ["srv"]
    # Registry was persisted and reflects the install.
    assert ext._registry_path().is_file()
    names = [e.name for e in ext.list_extensions()]
    assert names == ["bar"]


def test_install_already_installed_skips_git(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(*args: object, **kwargs: object) -> object:
        raise AssertionError("git should not run for an already-installed extension")

    ext._save_registry(
        {
            "extensions": {
                "bar": {
                    "url": "https://github.com/foo/bar",
                    "path": str(ext.extensions_dir() / "bar"),
                    "skills": ["s1"],
                    "mcp_servers": [],
                }
            }
        }
    )
    monkeypatch.setattr(ext.subprocess, "run", _boom)
    result = ext.install_extension("https://github.com/foo/bar")
    assert result.already_installed is True
    assert result.skills_found == ["s1"]


def test_install_git_missing(sakthai_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*args: object, **kwargs: object) -> object:
        raise FileNotFoundError

    monkeypatch.setattr(ext.subprocess, "run", _raise)
    with pytest.raises(ext.ExtensionError, match="git is not available"):
        ext.install_extension("https://github.com/foo/bar")


def test_install_clone_failure(sakthai_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(cmd: list[str], *args: object, **kwargs: object) -> object:
        raise subprocess.CalledProcessError(1, cmd, stderr="fatal: boom")

    monkeypatch.setattr(ext.subprocess, "run", _raise)
    with pytest.raises(ext.ExtensionError, match="git clone failed"):
        ext.install_extension("https://github.com/foo/bar")


# -- list / remove -------------------------------------------------------


def test_list_extensions_empty(sakthai_home: Path) -> None:
    assert ext.list_extensions() == []


def test_remove_unknown_returns_false(sakthai_home: Path) -> None:
    assert ext.remove("nope") is False


def test_remove_installed(sakthai_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ext.subprocess, "run", _fake_clone())
    ext.install_extension("https://github.com/foo/bar")
    clone_path = ext.extensions_dir() / "bar"
    assert clone_path.is_dir()
    assert ext.remove("bar") is True
    assert not clone_path.exists()
    assert ext.list_extensions() == []


@pytest.mark.parametrize(
    "url",
    ["ext::sh -c 'touch /tmp/pwned'", "-oProxyCommand=evil", "ftp://example.com/repo.git"],
)
def test_install_rejects_unsafe_git_url(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    """Option smuggling and remote-helper transports never reach git clone."""

    def _explode(*_a: object, **_k: object) -> object:
        raise AssertionError("git clone must not run for an unsafe URL")

    monkeypatch.setattr(ext.subprocess, "run", _explode)
    with pytest.raises(ext.ExtensionError):
        ext.install_extension(url)


def test_remove_refuses_path_outside_extensions_dir(sakthai_home: Path, tmp_path: Path) -> None:
    """A tampered registry entry must not be able to delete an arbitrary tree."""
    victim = tmp_path / "victim"
    victim.mkdir()
    (victim / "keep.txt").write_text("precious", encoding="utf-8")
    ext._save_registry(
        {"extensions": {"evil": {"url": "https://example.com/evil.git", "path": str(victim)}}}
    )

    with pytest.raises(ext.ExtensionError, match="outside"):
        ext.remove("evil")

    assert (victim / "keep.txt").exists()
    # The registry entry is left in place for the user to inspect.
    assert "evil" in ext._load_registry()["extensions"]


def test_remove_refuses_extensions_dir_itself(sakthai_home: Path) -> None:
    base = ext.extensions_dir()
    base.mkdir(parents=True, exist_ok=True)
    ext._save_registry(
        {"extensions": {"evil": {"url": "https://example.com/evil.git", "path": str(base)}}}
    )
    with pytest.raises(ext.ExtensionError, match="outside"):
        ext.remove("evil")
    assert base.exists()


# -- manifest validation -------------------------------------------------


def test_validate_manifest_valid(tmp_path: Path) -> None:
    manifest = tmp_path / "gemini-extension.json"
    manifest.write_text(
        json.dumps(
            {
                "name": "my-ext",
                "version": "1.0.0",
                "mcpServers": {
                    "srv1": {
                        "command": "python",
                        "args": ["-m", "srv"],
                        "env": {"FOO": "BAR"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    is_valid, diags = ext.validate_extension_manifest(manifest)
    assert is_valid is True
    assert diags == []


def test_validate_manifest_missing_returns_true(tmp_path: Path) -> None:
    is_valid, diags = ext.validate_extension_manifest(tmp_path / "nonexistent.json")
    assert is_valid is True
    assert len(diags) == 1
    assert "skills-only" in diags[0]


def test_validate_manifest_invalid_json(tmp_path: Path) -> None:
    manifest = tmp_path / "gemini-extension.json"
    manifest.write_text("{bad-json", encoding="utf-8")
    is_valid, diags = ext.validate_extension_manifest(manifest)
    assert is_valid is False
    assert any("not valid JSON" in d for d in diags)


def test_validate_manifest_dangerous_command_rejected(tmp_path: Path) -> None:
    manifest = tmp_path / "gemini-extension.json"
    manifest.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "evil": {
                        "command": "cat /etc/passwd; rm -rf /",
                        "args": ["$(whoami)"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    is_valid, diags = ext.validate_extension_manifest(manifest)
    assert is_valid is False
    assert any("dangerous shell metacharacters" in d for d in diags)


def test_validate_manifest_non_dict_rejected(tmp_path: Path) -> None:
    manifest = tmp_path / "gemini-extension.json"
    manifest.write_text(json.dumps(["not-an-object"]), encoding="utf-8")
    is_valid, diags = ext.validate_extension_manifest(manifest)
    assert is_valid is False
    assert any("must be a JSON object" in d for d in diags)


# -- persona-scoped extension management ---------------------------------


def test_persona_scoped_install_list_remove(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ext.subprocess, "run", _fake_clone())
    res = ext.install_extension("https://github.com/foo/web-ext", persona="saksee")
    assert res.extension.name == "web-ext"
    assert res.extension.persona == "saksee"
    assert "saksee" in str(res.extension.path)

    # Scoped list vs shared list
    shared_list = ext.list_extensions(persona=None)
    assert shared_list == []
    saksee_list = ext.list_extensions(persona="saksee")
    assert len(saksee_list) == 1
    assert saksee_list[0].name == "web-ext"

    # all_personas list
    all_list = ext.list_extensions(all_personas=True)
    assert len(all_list) == 1
    assert all_list[0].persona == "saksee"

    # info
    info = ext.get_extension_info("web-ext", persona="saksee")
    assert info is not None
    assert info.name == "web-ext"
    assert info.persona == "saksee"

    # validate
    val = ext.validate_extension("web-ext", persona="saksee")
    assert val.valid is True
    assert val.containment_valid is True

    # remove
    assert ext.remove("web-ext", persona="saksee") is True
    assert ext.list_extensions(persona="saksee") == []


def test_install_invalid_persona_raises(sakthai_home: Path) -> None:
    with pytest.raises(ext.ExtensionError, match="unknown persona"):
        ext.install_extension("https://github.com/foo/bar", persona="invalid-persona")


def test_update_extension_flow(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(ext.subprocess, "run", _fake_clone())
    res = ext.install_extension("https://github.com/foo/tool-ext")
    # Simulate .git directory
    git_dir = res.extension.path / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)

    def _fake_pull(cmd: list[str], *args: object, **kwargs: object) -> object:
        if "pull" in cmd:
            return types.SimpleNamespace(returncode=0, stdout="Already up to date.", stderr="")
        if "rev-parse" in cmd:
            return types.SimpleNamespace(returncode=0, stdout="abc1234567\n", stderr="")
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(ext.subprocess, "run", _fake_pull)
    up_res = ext.update_extension("tool-ext")
    assert up_res.success is True
    assert up_res.updated is False
    assert "Already up to date" in up_res.message
