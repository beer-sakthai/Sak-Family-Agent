"""Commands to install, list, inspect, validate, update, and remove extensions."""

from __future__ import annotations

import json
import sys
from typing import Any

import click

from ..config import PERSONA_NAMES
from ..extensions import (
    ExtensionError,
    get_extension_info,
    install_extension,
    list_extensions,
    update_extension,
    validate_extension,
)
from ..extensions import remove as remove_extension


@click.group()
def extensions() -> None:
    """Install and manage SakThai extensions from git."""


@extensions.command("install")
@click.argument("url")
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Install extension scoped to a specific persona.",
)
def extensions_install(url: str, persona: str | None) -> None:
    """Clone and register an extension from a git URL."""
    try:
        result = install_extension(url, persona=persona)
    except ExtensionError as exc:
        raise click.ClickException(str(exc)) from exc
    ext = result.extension
    scope_str = f" [persona: {persona}]" if persona else " [shared]"
    if result.already_installed:
        click.echo(f"already installed: {ext.name}{scope_str}  ({ext.path})")
        return
    click.echo(f"installed: {ext.name}{scope_str}")
    click.echo(f"  path  : {ext.path}")
    click.echo(f"  url   : {ext.url}")
    click.echo(f"  skills: {', '.join(result.skills_found) or '(none found)'}")
    if result.mcp_servers_found:
        click.echo(f"  mcp   : {', '.join(result.mcp_servers_found)}")


@extensions.command("list")
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="List extensions for a specific persona.",
)
@click.option(
    "--all-personas",
    is_flag=True,
    help="List extensions across all personas and shared scope.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output extension list in JSON format.",
)
def extensions_list(persona: str | None, all_personas: bool, as_json: bool) -> None:
    """List installed extensions."""
    installed = list_extensions(persona=persona, all_personas=all_personas)
    if as_json:
        data = [
            {
                "name": e.name,
                "url": e.url,
                "path": str(e.path),
                "skills": e.skills,
                "mcp_servers": e.mcp_servers,
                "persona": e.persona,
                "description": e.description,
                "version": e.version,
                "commit_sha": e.commit_sha,
            }
            for e in installed
        ]
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if not installed:
        scope = "all scopes" if all_personas else (f"persona '{persona}'" if persona else "shared")
        click.echo(f"(no extensions installed in {scope} — try `sakthai extensions install <url>`)")
        return

    for ext in installed:
        scope_tag = f"[{ext.persona}] " if ext.persona else "[shared] "
        click.echo(f"  {scope_tag}{ext.name:<20}  {ext.url}")
        if ext.description:
            click.echo(f"    desc  : {ext.description}")
        click.echo(f"    skills: {', '.join(ext.skills) or '(none)'}")
        click.echo(f"    mcp   : {', '.join(ext.mcp_servers) or '(none)'}")
        click.echo(f"    path  : {ext.path}")
        if ext.commit_sha:
            click.echo(f"    commit: {ext.commit_sha}")


@extensions.command("info")
@click.argument("name")
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Target a specific persona scope.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output extension details in JSON format.",
)
def extensions_info(name: str, persona: str | None, as_json: bool) -> None:
    """Show detailed metadata and discovered assets for an extension."""
    info = get_extension_info(name, persona=persona)
    if not info:
        raise click.ClickException(f"extension {name!r} not found in target scope")

    if as_json:
        payload = {
            "name": info.name,
            "url": info.url,
            "path": str(info.path),
            "skills": info.skills,
            "mcp_servers": info.mcp_servers,
            "persona": info.persona,
            "description": info.description,
            "version": info.version,
            "commit_sha": info.commit_sha,
        }
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    scope = info.persona or "shared"
    click.echo(f"# Extension: {info.name} (scope: {scope})")
    click.echo(f"  URL    : {info.url}")
    click.echo(f"  Path   : {info.path}")
    if info.description:
        click.echo(f"  Desc   : {info.description}")
    if info.version:
        click.echo(f"  Version: {info.version}")
    if info.commit_sha:
        click.echo(f"  Commit : {info.commit_sha}")
    click.echo(f"  Skills : {', '.join(info.skills) or '(none)'}")
    click.echo(f"  MCP    : {', '.join(info.mcp_servers) or '(none)'}")


@extensions.command("validate")
@click.argument("name", required=False, default=None)
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Target a specific persona scope.",
)
@click.option(
    "--all-personas",
    is_flag=True,
    help="Validate extensions across all personas.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output validation results in JSON format.",
)
def extensions_validate(
    name: str | None,
    persona: str | None,
    all_personas: bool,
    as_json: bool,
) -> None:
    """Validate containment, manifest schema, and skills for installed extensions."""
    to_validate: list[tuple[str, str | None]] = []
    if name:
        to_validate.append((name, persona))
    else:
        for ext in list_extensions(persona=persona, all_personas=all_personas):
            to_validate.append((ext.name, ext.persona))

    if not to_validate:
        click.echo("(no extensions to validate)")
        return

    results: list[dict[str, Any]] = []
    all_valid = True

    for ext_name, ext_persona in to_validate:
        try:
            res = validate_extension(ext_name, persona=ext_persona)
            if not res.valid:
                all_valid = False
            results.append(
                {
                    "name": res.name,
                    "persona": res.persona,
                    "valid": res.valid,
                    "containment_valid": res.containment_valid,
                    "manifest_valid": res.manifest_valid,
                    "skills_valid": res.skills_valid,
                    "skills_count": res.skills_count,
                    "mcp_servers_count": res.mcp_servers_count,
                    "diagnostics": res.diagnostics,
                }
            )
        except ExtensionError as exc:
            all_valid = False
            results.append(
                {
                    "name": ext_name,
                    "persona": ext_persona,
                    "valid": False,
                    "diagnostics": [str(exc)],
                }
            )

    if as_json:
        click.echo(
            json.dumps({"valid": all_valid, "results": results}, indent=2, ensure_ascii=False)
        )
        if not all_valid:
            sys.exit(1)
        return

    for r in results:
        status = "PASS" if r["valid"] else "FAIL"
        scope = f" [{r.get('persona') or 'shared'}]"
        click.echo(f"  [{status}] {r['name']}{scope}")
        if r.get("diagnostics"):
            for d in r["diagnostics"]:
                click.echo(f"    - {d}")

    if not all_valid:
        sys.exit(1)


@extensions.command("update")
@click.argument("name", required=False, default=None)
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Target a specific persona scope.",
)
@click.option(
    "--all",
    "update_all",
    is_flag=True,
    help="Update all installed extensions in the chosen scope.",
)
def extensions_update(name: str | None, persona: str | None, update_all: bool) -> None:
    """Pull latest updates from git and refresh registered skills & MCP servers."""
    if not name and not update_all:
        raise click.ClickException(
            "Specify an extension NAME or pass --all to update all extensions."
        )

    targets: list[tuple[str, str | None]] = []
    if name:
        targets.append((name, persona))
    else:
        for ext in list_extensions(persona=persona):
            targets.append((ext.name, persona))

    if not targets:
        click.echo("(no extensions found to update)")
        return

    any_failed = False
    for ext_name, ext_persona in targets:
        try:
            res = update_extension(ext_name, persona=ext_persona)
            scope = f" [{ext_persona or 'shared'}]"
            if res.success:
                click.echo(f"  [OK] {ext_name}{scope}: {res.message} ({res.commit_sha})")
            else:
                any_failed = True
                click.echo(f"  [FAIL] {ext_name}{scope}: {res.message}")
        except ExtensionError as exc:
            any_failed = True
            click.echo(f"  [ERROR] {ext_name}: {exc}")

    if any_failed:
        sys.exit(1)


@extensions.command("remove")
@click.argument("name")
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Remove extension from a specific persona scope.",
)
def extensions_remove(name: str, persona: str | None) -> None:
    """Remove an installed extension by NAME."""
    try:
        removed = remove_extension(name, persona=persona)
    except ExtensionError as exc:
        raise click.ClickException(str(exc)) from exc
    scope = f" from persona '{persona}'" if persona else ""
    if removed:
        click.echo(f"removed: {name}{scope}")
    else:
        raise click.ClickException(f"no extension named '{name}' is installed{scope}")
