"""CLI commands for the Unified Agent Integration Platform."""

from __future__ import annotations

import json
from pathlib import Path

import click

from ..agent_platform.agent_engine import ModelTier, resolve_model_preset
from ..agent_platform.antigravity_agent import (
    AI_STUDIO_KEY_URL,
    AntigravityAgentRunner,
    AntigravityRunnerConfig,
)
from ..agent_platform.customizations import CustomizationRegistry
from ..agent_platform.dep_manager import detect_dependency_manager, wrap_with_isolated_runner
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


@platform_cmd.command("wrap-cmd")
@click.argument("command", type=str)
@click.option(
    "--path",
    "-p",
    "target_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd,
    help="Target workspace to detect runner from.",
)
@click.option("--force", "-f", is_flag=True, help="Force wrapping even for non-Python commands.")
def wrap_cmd(command: str, target_path: Path, force: bool) -> None:
    """Wrap command with detected isolated runner (uv, poetry, conda, etc.)."""
    wrapped = wrap_with_isolated_runner(command, workspace=target_path, force=force)
    click.echo(wrapped)


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


@platform_cmd.command("antigravity")
@click.argument("prompt", type=str)
@click.option(
    "--backend",
    "-b",
    type=click.Choice(["hosted", "openai", "litert"]),
    default="hosted",
    help="Backend execution engine.",
)
@click.option("--model", "-m", default="gemini-2.5-flash", help="Model identifier.")
@click.option(
    "--tier",
    "-t",
    type=click.Choice([t.value for t in ModelTier]),
    default=None,
    help="Model tier preset (fast, reasoning, local, lead). Overrides --model.",
)
@click.option("--base-url", default=None, help="Base URL for local OpenAI/Ollama server.")
@click.option("--model-path", default=None, help="Filesystem path to local LiteRT model weights.")
@click.option("--api-key", default=None, help="Explicit Gemini API key.")
def run_antigravity_cmd(
    prompt: str,
    backend: str,
    model: str,
    tier: str | None,
    base_url: str | None,
    model_path: str | None,
    api_key: str | None,
) -> None:
    """Run an autonomous Google Antigravity Agent with safety guardrails."""
    import asyncio
    import os
    import sys

    if tier:
        preset = resolve_model_preset(tier)
        model = preset.model_name

    resolved_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if backend == "hosted" and not resolved_key:
        click.echo("\n⚠️  [Authentication Required]")
        click.echo("To run with hosted Gemini models, set GEMINI_API_KEY,")
        click.echo(f"or create an API key at Google AI Studio: {AI_STUDIO_KEY_URL}")
        click.echo("Alternatively, pass '--backend openai' to connect to local Ollama.\n")
        sys.exit(1)

    runner_cfg = AntigravityRunnerConfig(
        backend=backend,
        model=model,
        api_key=resolved_key,
        base_url=base_url,
        model_path=model_path,
    )
    runner = AntigravityAgentRunner(config=runner_cfg)
    click.echo(f"🚀 Initializing Antigravity Agent [{backend.upper()}: {model}]...")

    async def _execute() -> None:
        async for token in runner.stream_chat(prompt):
            click.echo(token, nl=False)
        click.echo()

    try:
        asyncio.run(_execute())
    except Exception as exc:
        click.echo(f"❌ Execution failed: {exc}", err=True)
        sys.exit(1)
