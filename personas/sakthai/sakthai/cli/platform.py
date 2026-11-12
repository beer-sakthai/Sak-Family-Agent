"""CLI commands for the Unified Agent Integration Platform."""

from __future__ import annotations

import json
from pathlib import Path

import click

from ..agent_platform.customizations import CustomizationRegistry
from ..agent_platform.dep_manager import detect_dependency_manager
from ..agent_platform.harness_exporter import export_harness_agent_spec, generate_harness_uid
from ..agent_platform.safety import DataLossGuardrail


@click.group()
def platform_cmd() -> None:
    """Unified AI agent platform, safety guardrails & spec bridge."""


@platform_cmd.command("detect-deps")
@click.option(
    "--path",
    "-p",
    "target_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd,
    help="Target directory to inspect for package/dependency managers.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit result as JSON.")
def detect_deps(target_path: Path, as_json: bool) -> None:
    """Detect isolated Python dependency managers (uv, poetry, conda, etc.)."""
    detection = detect_dependency_manager(target_path)
    if as_json:
        data = {
            "manager": detection.manager,
            "install_cmd": detection.install_cmd,
            "sync_cmd": detection.sync_cmd,
            "isolated_exec": detection.isolated_exec,
            "target_path": str(target_path),
        }
        click.echo(json.dumps(data, indent=2))
        return

    click.echo(f"Workspace:     {target_path}")
    click.echo(f"Manager:       {detection.manager}")
    click.echo(f"Install cmd:   {detection.install_cmd}")
    click.echo(f"Sync cmd:      {detection.sync_cmd}")
    click.echo(f"Isolated exec: {detection.isolated_exec}")


@platform_cmd.command("check-safety")
@click.argument("command", type=str)
@click.option(
    "--token",
    "-t",
    "approval_token",
    type=str,
    default=None,
    help="Explicit approval token (APPROVE_<digest>) to bypass guardrail.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit result as JSON.")
def check_safety(command: str, approval_token: str | None, as_json: bool) -> None:
    """Inspect shell command or SQL query for accidental data loss risk."""
    guardrail = DataLossGuardrail()
    res = guardrail.verify_or_halt(command, approval_token=approval_token)
    expected_token = guardrail.generate_approval_token(command)

    if as_json:
        data = {
            "command": command,
            "is_destructive": res.is_destructive,
            "blocked": res.blocked,
            "reason": res.reason,
            "impact": res.impact,
            "approval_token_required": expected_token if res.is_destructive else None,
        }
        click.echo(json.dumps(data, indent=2))
        return

    if not res.is_destructive:
        click.echo(f"✓ Command verified safe: {command}")
        return

    if res.blocked:
        click.echo("❌ BLOCKED: Potential accidental data loss detected!")
        click.echo(f"  Reason:         {res.reason}")
        click.echo(f"  Impact:         {res.impact}")
        click.echo(f"  Required Token: {expected_token}")
        click.echo("  To bypass, re-run with: --token " + expected_token)
    else:
        click.echo("⚠️  WARNING: Destructive operation authorized via token:")
        click.echo(f"  Reason: {res.reason}")
        click.echo(f"  Impact: {res.impact}")


@platform_cmd.command("skills")
@click.option(
    "--path",
    "-p",
    "search_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd,
    help="Directory tree to scan for SKILL.md bundles.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit skills as JSON.")
def list_skills(search_path: Path, as_json: bool) -> None:
    """Discover skills with progressive disclosure metadata."""
    registry = CustomizationRegistry(workspace_root=search_path)
    skills = registry.list_available_skills()
    if as_json:
        data = [{"name": s.name, "description": s.description, "path": s.path} for s in skills]
        click.echo(json.dumps(data, indent=2))
        return

    if not skills:
        click.echo(f"No SKILL.md files found under {search_path}")
        return

    click.echo(f"Discovered {len(skills)} skill(s) under {search_path}:")
    for s in skills:
        click.echo(f"\n• {s.name}")
        click.echo(f"  Path: {s.path}")
        click.echo(f"  Desc: {s.description}")


@platform_cmd.command("export-harness")
@click.option("--name", "-n", required=True, help="Agent display name.")
@click.option("--task", "-t", required=True, help="Agent task instructions.")
@click.option(
    "--mcp",
    "-m",
    "mcp_tools",
    multiple=True,
    help="MCP connector identifiers (can be passed multiple times).",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(writable=True, path_type=Path),
    default=None,
    help="Save YAML output to file instead of stdout.",
)
def export_harness(
    name: str,
    task: str,
    mcp_tools: tuple[str, ...],
    output_file: Path | None,
) -> None:
    """Export a production-ready Harness v1 Agent YAML specification."""
    tools = list(mcp_tools) if mcp_tools else None
    yaml_content = export_harness_agent_spec(
        name=name,
        task=task,
        mcp_connectors=tools,
    )
    uid = generate_harness_uid(name)
    if output_file:
        output_file.write_text(yaml_content, encoding="utf-8")
        click.echo(f"✓ Harness agent spec written to {output_file} (UID: {uid})")
    else:
        click.echo(yaml_content)
