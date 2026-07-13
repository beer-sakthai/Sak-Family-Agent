"""Manage extensions: clone skill/MCP bundles from git into ~/.sakthai."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import sakthai_home
from ..giturl import validate_git_url

# A safe single-path-segment name derived from the repo URL.
EXTENSION_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")


class ExtensionError(Exception):
    """Raised when an extension cannot be installed or located."""


@dataclass
class ExtensionInfo:
    name: str
    url: str
    path: Path
    skills: list[str] = field(default_factory=list)
    mcp_servers: list[str] = field(default_factory=list)


@dataclass
class InstallResult:
    extension: ExtensionInfo
    already_installed: bool = False
    skills_found: list[str] = field(default_factory=list)
    mcp_servers_found: list[str] = field(default_factory=list)


def extensions_dir() -> Path:
    return sakthai_home() / "extensions"


def _registry_path() -> Path:
    return sakthai_home() / "extensions.json"


def _load_registry() -> dict[str, Any]:
    path = _registry_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("extensions"), dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"extensions": {}}


def _save_registry(data: dict[str, Any]) -> None:
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _name_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1].removesuffix(".git")


def _discover_skills(path: Path) -> list[str]:
    return sorted(md.parent.name for md in path.rglob("SKILL.md"))


def _discover_mcp_servers(path: Path) -> list[str]:
    manifest = path / "gemini-extension.json"
    if not manifest.exists():
        return []
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    servers = data.get("mcpServers", {})
    return sorted(servers.keys()) if isinstance(servers, dict) else []


def _info_from_registry(name: str, data: dict[str, Any]) -> ExtensionInfo:
    return ExtensionInfo(
        name=name,
        url=data["url"],
        path=Path(data["path"]),
        skills=data.get("skills", []),
        mcp_servers=data.get("mcp_servers", []),
    )


def install_extension(url: str) -> InstallResult:
    """Clone ``url`` into the extensions dir and register its skills/MCP servers."""
    try:
        url = validate_git_url(url)
    except ValueError as exc:
        raise ExtensionError(str(exc)) from exc
    name = _name_from_url(url)
    if not EXTENSION_NAME_RE.match(name):
        raise ExtensionError(
            f"invalid extension name '{name}' derived from URL. Names must start with "
            "a letter or number and contain only alphanumerics, underscores, or hyphens "
            "(max 64 chars)."
        )
    base = extensions_dir().resolve()
    dest = (base / name).resolve()
    if dest.parent != base:
        raise ExtensionError(f"invalid extension path: {dest}")

    registry = _load_registry()
    if name in registry["extensions"]:
        info = _info_from_registry(name, registry["extensions"][name])
        return InstallResult(
            extension=info,
            already_installed=True,
            skills_found=info.skills,
            mcp_servers_found=info.mcp_servers,
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(  # nosec B603 B607 — fixed argv, no shell
            ["git", "clone", "--depth=1", "--", url, str(dest)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise ExtensionError(f"git clone failed: {(exc.stderr or '').strip() or exc}") from exc
    except FileNotFoundError as exc:
        raise ExtensionError("git is not available on PATH") from exc

    skills = _discover_skills(dest)
    mcp_servers = _discover_mcp_servers(dest)
    registry["extensions"][name] = {
        "url": url,
        "path": str(dest),
        "skills": skills,
        "mcp_servers": mcp_servers,
    }
    _save_registry(registry)
    return InstallResult(
        extension=ExtensionInfo(
            name=name, url=url, path=dest, skills=skills, mcp_servers=mcp_servers
        ),
        skills_found=skills,
        mcp_servers_found=mcp_servers,
    )


def list_extensions() -> list[ExtensionInfo]:
    registry = _load_registry()
    return [_info_from_registry(name, data) for name, data in registry["extensions"].items()]


def remove(name: str) -> bool:
    """Remove an extension and its clone. Returns False if it wasn't installed.

    Raises :class:`ExtensionError` (without touching the registry or the
    filesystem) when the registered path resolves outside the extensions
    directory — a tampered or corrupted registry entry must not be able to
    delete an arbitrary tree.
    """
    registry = _load_registry()
    if name not in registry["extensions"]:
        return False
    data = registry["extensions"].pop(name)
    path = Path(data["path"])
    if path.exists():
        base = extensions_dir().resolve()
        resolved = path.resolve()
        if resolved == base or not resolved.is_relative_to(base):
            raise ExtensionError(
                f"refusing to delete {path}: registered path resolves outside "
                f"the extensions directory {base}"
            )
        shutil.rmtree(resolved)
    _save_registry(registry)
    return True
