"""Tests for sakthai.extensions.install.

Git is never actually invoked: ``install`` is exercised by monkeypatching
``subprocess.run`` so the clone is simulated on the local filesystem. The
``sakthai_home`` fixture redirects the extensions dir and registry into tmp.
"""

from __future__ import annotations

import importlib
import json
import subprocess
import types
from collections.abc import Callable
from pathlib import Path

import pytest

# Import the submodule object explicitly. ``sakthai.extensions.__init__``
# re-exports ``install`` (the function), which shadows the submodule under both
# ``from ... import install`` and ``import ....install as ext``; importlib
# returns the real module from sys.modules instead.
ext = importlib.import_module("sakthai.extensions.install")


# -- helpers -------------------------------------------------------------


def _fake_clone(*, with_skill: bool = True, with_mcp: bool = True) -> Callable[..., object]:
    """Return a subprocess.run stand-in that materialises a cloned repo."""

    def _run(cmd: list[str], *args: object, **kwargs: object) -> object:
        dest = Path(cmd[-1])
        dest.mkdir(parents=True, exist_ok=True)
        if with_skill:
            skill = dest / "myskill"
            skill.mkdir()
            (skill / "SKILL.md").write_text("---\nname: myskill\n---\nbody\n", encoding="utf-8")
        if with_mcp:
            (dest / "gemini-extension.json").write_text(
                json.dumps({"mcpServers": {"srv": {}}}), encoding="utf-8"
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


# -- install -------------------------------------------------------------


def test_install_rejects_invalid_name(sakthai_home: Path) -> None:
    with pytest.raises(ext.ExtensionError, match="invalid extension name"):
        ext.install("https://example.com/foo/@bad")


def test_install_happy_path(sakthai_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ext.subprocess, "run", _fake_clone())
    result = ext.install("https://github.com/foo/bar")
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
    result = ext.install("https://github.com/foo/bar")
    assert result.already_installed is True
    assert result.skills_found == ["s1"]


def test_install_git_missing(sakthai_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*args: object, **kwargs: object) -> object:
        raise FileNotFoundError

    monkeypatch.setattr(ext.subprocess, "run", _raise)
    with pytest.raises(ext.ExtensionError, match="git is not available"):
        ext.install("https://github.com/foo/bar")


def test_install_clone_failure(sakthai_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(cmd: list[str], *args: object, **kwargs: object) -> object:
        raise subprocess.CalledProcessError(1, cmd, stderr="fatal: boom")

    monkeypatch.setattr(ext.subprocess, "run", _raise)
    with pytest.raises(ext.ExtensionError, match="git clone failed"):
        ext.install("https://github.com/foo/bar")


# -- list / remove -------------------------------------------------------


def test_list_extensions_empty(sakthai_home: Path) -> None:
    assert ext.list_extensions() == []


def test_remove_unknown_returns_false(sakthai_home: Path) -> None:
    assert ext.remove("nope") is False


def test_remove_installed(sakthai_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ext.subprocess, "run", _fake_clone())
    ext.install("https://github.com/foo/bar")
    clone_path = ext.extensions_dir() / "bar"
    assert clone_path.is_dir()
    assert ext.remove("bar") is True
    assert not clone_path.exists()
    assert ext.list_extensions() == []
