"""Manage extensions: clone skill/MCP bundles from git into ~/.sakthai."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import (
    PERSONA_NAMES,
    persona_extensions_dir,
    persona_extensions_registry_path,
    sakthai_home,
)
from ..giturl import validate_git_url

# A safe single-path-segment name derived from the repo URL.
EXTENSION_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")

# Detection pattern for command injection or dangerous metacharacters in manifests.
DANGEROUS_SHELL_PATTERNS = re.compile(r"[;&|`$><]|\$\(")


class ExtensionError(Exception):
    """Raised when an extension cannot be installed or located."""


@dataclass
class ExtensionInfo:
    name: str
    url: str
    path: Path
    skills: list[str] = field(default_factory=list)
    mcp_servers: list[str] = field(default_factory=list)
    persona: str | None = None
    description: str = ""
    version: str = ""
    commit_sha: str = ""


@dataclass
class InstallResult:
    extension: ExtensionInfo
    already_installed: bool = False
    skills_found: list[str] = field(default_factory=list)
    mcp_servers_found: list[str] = field(default_factory=list)


@dataclass
class ExtensionValidationResult:
    name: str
    valid: bool
    path: Path
    containment_valid: bool
    manifest_valid: bool
    skills_valid: bool
    skills_count: int = 0
    mcp_servers_count: int = 0
    diagnostics: list[str] = field(default_factory=list)
    persona: str | None = None


@dataclass
class ExtensionUpdateResult:
    name: str
    success: bool
    updated: bool
    message: str
    commit_sha: str = ""
    persona: str | None = None


def extensions_dir(persona: str | None = None) -> Path:
    if persona is not None:
        return persona_extensions_dir(persona)
    return sakthai_home() / "extensions"


def _registry_path(persona: str | None = None) -> Path:
    if persona is not None:
        return persona_extensions_registry_path(persona)
    return sakthai_home() / "extensions.json"


def _load_registry(persona: str | None = None) -> dict[str, Any]:
    path = _registry_path(persona)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("extensions"), dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"extensions": {}}


def _save_registry(data: dict[str, Any], persona: str | None = None) -> None:
    path = _registry_path(persona)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _name_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1].removesuffix(".git")


def _get_git_commit(path: Path) -> str:
    """Read HEAD commit SHA if path is a git repo, or return empty string."""
    git_dir = path / ".git"
    if not git_dir.exists():
        return ""
    try:
        res = subprocess.run(  # nosec B603 B607
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return res.stdout.strip()[:10]
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def validate_extension_manifest(manifest_path: Path) -> tuple[bool, list[str]]:
    """Validate gemini-extension.json schema, command integrity, and safety."""
    diagnostics: list[str] = []
    if not manifest_path.exists():
        return True, ["No gemini-extension.json manifest present (skills-only extension)"]
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return False, [f"Manifest is not valid JSON: {exc}"]

    if not isinstance(data, dict):
        return False, ["Manifest top-level entity must be a JSON object"]

    servers = data.get("mcpServers")
    if servers is not None:
        if not isinstance(servers, dict):
            return False, ["'mcpServers' must be a dictionary"]
        for srv_name, srv_conf in servers.items():
            if not isinstance(srv_conf, dict):
                diagnostics.append(f"Server {srv_name!r}: configuration must be an object")
                continue
            cmd = srv_conf.get("command")
            url = srv_conf.get("url")
            if not cmd and not url:
                diagnostics.append(f"Server {srv_name!r}: must specify 'command' or 'url'")
            if cmd:
                if not isinstance(cmd, str) or not cmd.strip():
                    diagnostics.append(f"Server {srv_name!r}: 'command' must be a non-empty string")
                elif DANGEROUS_SHELL_PATTERNS.search(cmd):
                    diagnostics.append(
                        f"Server {srv_name!r}: dangerous shell metacharacters detected in command: {cmd!r}"
                    )
            args = srv_conf.get("args")
            if args is not None:
                if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
                    diagnostics.append(f"Server {srv_name!r}: 'args' must be a list of strings")
                elif any(DANGEROUS_SHELL_PATTERNS.search(a) for a in args):
                    diagnostics.append(
                        f"Server {srv_name!r}: dangerous shell metacharacters detected in arguments"
                    )
            env = srv_conf.get("env")
            if env is not None and (
                not isinstance(env, dict)
                or not all(isinstance(k, str) and isinstance(v, str) for k, v in env.items())
            ):
                diagnostics.append(
                    f"Server {srv_name!r}: 'env' must be a dictionary of string key-values"
                )

    is_valid = len(diagnostics) == 0
    return is_valid, diagnostics


def _discover_skills(path: Path) -> list[str]:
    return sorted(md.parent.name for md in path.rglob("SKILL.md"))


def _discover_skills_with_validation(path: Path) -> tuple[list[str], list[str]]:
    """Return (skill_names, diagnostics) for all SKILL.md found under path."""
    skills: list[str] = []
    diagnostics: list[str] = []
    try:
        for md in sorted(path.rglob("SKILL.md")):
            skill_name = md.parent.name
            skills.append(skill_name)
            try:
                text = md.read_text(encoding="utf-8", errors="replace")
                if not text.startswith("---"):
                    diagnostics.append(
                        f"Skill {skill_name!r}: missing YAML frontmatter header '---'"
                    )
                elif "---" not in text[3:]:
                    diagnostics.append(f"Skill {skill_name!r}: unclosed YAML frontmatter")
                else:
                    fm = text[3:].split("---", 1)[0]
                    if "name:" not in fm:
                        diagnostics.append(f"Skill {skill_name!r}: missing 'name' in frontmatter")
                    if "description:" not in fm:
                        diagnostics.append(
                            f"Skill {skill_name!r}: missing 'description' in frontmatter"
                        )
            except OSError as exc:
                diagnostics.append(f"Failed to read skill {skill_name!r}: {exc}")
    except OSError as exc:
        diagnostics.append(f"Failed to scan skills in {path}: {exc}")
    return skills, diagnostics


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


def _read_manifest_metadata(path: Path) -> tuple[str, str]:
    """Return (description, version) from gemini-extension.json if present."""
    manifest = path / "gemini-extension.json"
    if not manifest.exists():
        return "", ""
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return str(data.get("description", "")), str(data.get("version", ""))
    except (json.JSONDecodeError, OSError):
        pass
    return "", ""


def _info_from_registry(
    name: str, data: dict[str, Any], persona: str | None = None
) -> ExtensionInfo:
    return ExtensionInfo(
        name=name,
        url=data["url"],
        path=Path(data["path"]),
        skills=data.get("skills", []),
        mcp_servers=data.get("mcp_servers", []),
        persona=data.get("persona", persona),
        description=data.get("description", ""),
        version=data.get("version", ""),
        commit_sha=data.get("commit_sha", ""),
    )


def install_extension(url: str, persona: str | None = None) -> InstallResult:
    """Clone ``url`` into the extensions dir and register its skills/MCP servers."""
    if persona is not None and persona not in PERSONA_NAMES:
        raise ExtensionError(f"unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

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
    base = extensions_dir(persona).resolve()
    dest = (base / name).resolve()
    if dest.parent != base:
        raise ExtensionError(f"invalid extension path: {dest}")

    registry = _load_registry(persona)
    if name in registry["extensions"]:
        info = _info_from_registry(name, registry["extensions"][name], persona=persona)
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
    desc, ver = _read_manifest_metadata(dest)
    commit = _get_git_commit(dest)

    registry["extensions"][name] = {
        "url": url,
        "path": str(dest),
        "skills": skills,
        "mcp_servers": mcp_servers,
        "persona": persona,
        "description": desc,
        "version": ver,
        "commit_sha": commit,
    }
    _save_registry(registry, persona=persona)
    return InstallResult(
        extension=ExtensionInfo(
            name=name,
            url=url,
            path=dest,
            skills=skills,
            mcp_servers=mcp_servers,
            persona=persona,
            description=desc,
            version=ver,
            commit_sha=commit,
        ),
        skills_found=skills,
        mcp_servers_found=mcp_servers,
    )


def list_extensions(
    persona: str | None = None,
    all_personas: bool = False,
) -> list[ExtensionInfo]:
    if all_personas:
        results: list[ExtensionInfo] = []
        # 1. Shared extensions
        shared_reg = _load_registry(persona=None)
        for name, data in shared_reg["extensions"].items():
            results.append(_info_from_registry(name, data, persona=None))
        # 2. Per-persona extensions
        for p in PERSONA_NAMES:
            p_reg = _load_registry(persona=p)
            for name, data in p_reg["extensions"].items():
                results.append(_info_from_registry(name, data, persona=p))
        return results

    registry = _load_registry(persona)
    return [
        _info_from_registry(name, data, persona=persona)
        for name, data in registry["extensions"].items()
    ]


def remove(name: str, persona: str | None = None) -> bool:
    """Remove an extension and its clone. Returns False if it wasn't installed.

    Raises :class:`ExtensionError` (without touching the registry or the
    filesystem) when the registered path resolves outside the extensions
    directory — a tampered or corrupted registry entry must not be able to
    delete an arbitrary tree.
    """
    if persona is not None and persona not in PERSONA_NAMES:
        raise ExtensionError(f"unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    registry = _load_registry(persona)
    if name not in registry["extensions"]:
        return False
    data = registry["extensions"].pop(name)
    path = Path(data["path"])
    if path.exists():
        base = extensions_dir(persona).resolve()
        resolved = path.resolve()
        if resolved == base or not resolved.is_relative_to(base):
            raise ExtensionError(
                f"refusing to delete {path}: registered path resolves outside "
                f"the extensions directory {base}"
            )
        shutil.rmtree(resolved)
    _save_registry(registry, persona=persona)
    return True


def validate_extension(
    name: str,
    persona: str | None = None,
) -> ExtensionValidationResult:
    """Validate an installed extension's containment, manifest schema, and skills."""
    if persona is not None and persona not in PERSONA_NAMES:
        raise ExtensionError(f"unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    registry = _load_registry(persona)
    if name not in registry["extensions"]:
        raise ExtensionError(f"extension {name!r} is not installed")

    data = registry["extensions"][name]
    path = Path(data["path"])
    diagnostics: list[str] = []

    base = extensions_dir(persona).resolve()
    resolved = path.resolve()
    containment_valid = resolved != base and resolved.is_relative_to(base)
    if not containment_valid:
        diagnostics.append(f"Extension path {path} resolves outside extensions directory {base}")

    if not path.exists():
        diagnostics.append(f"Extension path does not exist on disk: {path}")
        return ExtensionValidationResult(
            name=name,
            valid=False,
            path=path,
            containment_valid=containment_valid,
            manifest_valid=False,
            skills_valid=False,
            diagnostics=diagnostics,
            persona=persona,
        )

    # Validate manifest
    manifest_file = path / "gemini-extension.json"
    manifest_valid, manifest_diags = validate_extension_manifest(manifest_file)
    if not manifest_valid:
        diagnostics.extend(manifest_diags)

    # Validate skills
    skills, skill_diags = _discover_skills_with_validation(path)
    skills_valid = len(skill_diags) == 0
    if not skills_valid:
        diagnostics.extend(skill_diags)

    mcp_servers = _discover_mcp_servers(path)

    overall_valid = containment_valid and manifest_valid and skills_valid
    return ExtensionValidationResult(
        name=name,
        valid=overall_valid,
        path=path,
        containment_valid=containment_valid,
        manifest_valid=manifest_valid,
        skills_valid=skills_valid,
        skills_count=len(skills),
        mcp_servers_count=len(mcp_servers),
        diagnostics=diagnostics,
        persona=persona,
    )


def update_extension(
    name: str,
    persona: str | None = None,
) -> ExtensionUpdateResult:
    """Safely update an extension via git pull --ff-only and re-sync its registry entry."""
    if persona is not None and persona not in PERSONA_NAMES:
        raise ExtensionError(f"unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    registry = _load_registry(persona)
    if name not in registry["extensions"]:
        raise ExtensionError(f"extension {name!r} is not installed")

    data = registry["extensions"][name]
    path = Path(data["path"])
    if not path.exists():
        raise ExtensionError(f"extension path {path} does not exist on disk")

    git_dir = path / ".git"
    if not git_dir.exists():
        return ExtensionUpdateResult(
            name=name,
            success=False,
            updated=False,
            message=f"Extension {name!r} is not a git repository",
            persona=persona,
        )

    old_commit = _get_git_commit(path)
    try:
        proc = subprocess.run(  # nosec B603 B607
            ["git", "-C", str(path), "pull", "--ff-only"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        new_commit = _get_git_commit(path)
        updated = "Already up to date." not in proc.stdout and old_commit != new_commit
        skills = _discover_skills(path)
        mcp_servers = _discover_mcp_servers(path)
        desc, ver = _read_manifest_metadata(path)

        data["skills"] = skills
        data["mcp_servers"] = mcp_servers
        data["commit_sha"] = new_commit
        if desc:
            data["description"] = desc
        if ver:
            data["version"] = ver
        _save_registry(registry, persona=persona)

        msg = "Updated successfully" if updated else "Already up to date"
        return ExtensionUpdateResult(
            name=name,
            success=True,
            updated=updated,
            message=msg,
            commit_sha=new_commit,
            persona=persona,
        )
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or "").strip() or str(exc)
        return ExtensionUpdateResult(
            name=name,
            success=False,
            updated=False,
            message=f"git pull failed: {err}",
            commit_sha=old_commit,
            persona=persona,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return ExtensionUpdateResult(
            name=name,
            success=False,
            updated=False,
            message=f"Update failed: {exc}",
            commit_sha=old_commit,
            persona=persona,
        )


def get_extension_info(
    name: str,
    persona: str | None = None,
) -> ExtensionInfo | None:
    """Return ExtensionInfo for name in persona scope, or None if not found."""
    registry = _load_registry(persona)
    if name not in registry["extensions"]:
        return None
    return _info_from_registry(name, registry["extensions"][name], persona=persona)
