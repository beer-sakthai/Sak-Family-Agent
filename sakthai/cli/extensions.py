"""Commands to install, list, and remove extensions."""

from __future__ import annotations

import click

from ..extensions import ExtensionError, list_extensions
from ..extensions import install as install_extension
from ..extensions import remove as remove_extension


@click.group()
def extensions() -> None:
    """Install and manage SakThai extensions from git."""


@extensions.command("install")
@click.argument("url")
def extensions_install(url: str) -> None:
    """Clone and register an extension from a git URL."""
    try:
        result = install_extension(url)
    except ExtensionError as exc:
        raise click.ClickException(str(exc)) from exc
    ext = result.extension
    if result.already_installed:
        click.echo(f"already installed: {ext.name}  ({ext.path})")
        return
    click.echo(f"installed: {ext.name}")
    click.echo(f"  path  : {ext.path}")
    click.echo(f"  url   : {ext.url}")
    click.echo(f"  skills: {', '.join(result.skills_found) or '(none found)'}")
    if result.mcp_servers_found:
        click.echo(f"  mcp   : {', '.join(result.mcp_servers_found)}")


@extensions.command("list")
def extensions_list() -> None:
    """List installed extensions."""
    installed = list_extensions()
    if not installed:
        click.echo("(no extensions installed — try `sakthai extensions install <url>`)")
        return
    for ext in installed:
        click.echo(f"  {ext.name:<20}  {ext.url}")
        click.echo(f"    skills: {', '.join(ext.skills) or '(none)'}")
        click.echo(f"    mcp   : {', '.join(ext.mcp_servers) or '(none)'}")
        click.echo(f"    path  : {ext.path}")


@extensions.command("remove")
@click.argument("name")
def extensions_remove(name: str) -> None:
    """Remove an installed extension by NAME."""
    if remove_extension(name):
        click.echo(f"removed: {name}")
    else:
        raise click.ClickException(f"no extension named '{name}' is installed")
