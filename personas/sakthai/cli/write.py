"""The ``sakthai write`` CLI command for LaunchDarkly AgentControl writing assistance."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ..agent.writing_assistant import (
    generate_writing_with_agentcontrol,
    get_writing_assistant_config,
    inspect_writing_config,
)
from ..config import PERSONA_NAMES


@click.command("write")
@click.argument("prompt", required=False)
@click.option(
    "--persona",
    type=click.Choice(list(PERSONA_NAMES), case_sensitive=False),
    default="sakthai",
    show_default=True,
    help="Which Sak Family persona perspective to write with.",
)
@click.option(
    "--user",
    "user_id",
    default="sakthai-writer",
    show_default=True,
    help="User identifier for LaunchDarkly context targeting.",
)
@click.option(
    "--raw",
    is_flag=True,
    help="Output only the raw generated text without panel formatting.",
)
@click.option(
    "--inspect",
    "inspect_mode",
    is_flag=True,
    help="Inspect the remote LaunchDarkly AgentControl config and exit.",
)
@click.option(
    "--fallback",
    "force_fallback",
    is_flag=True,
    help="Force local House of Sak fallback mode (bypass LaunchDarkly invoke).",
)
@click.option(
    "--json",
    "json_mode",
    is_flag=True,
    help="Output result as JSON object.",
)
def write_cmd(
    prompt: str | None,
    persona: str,
    user_id: str,
    raw: bool,
    inspect_mode: bool,
    force_fallback: bool,
    json_mode: bool,
) -> None:
    """Assist with writing, rewriting, summarizing, and drafting using LaunchDarkly AgentControl.

    Reads model parameters and prompt instructions dynamically from LaunchDarkly
    AgentControl (gensandees-writing-assistant), falling back smoothly to local House of
    Sak writing workflows if LaunchDarkly is unreachable or credentials are unset.
    """
    console = Console()
    cfg = get_writing_assistant_config()

    if inspect_mode:
        data = asyncio.run(inspect_writing_config(user_id=user_id, persona=persona, config=cfg))
        if json_mode or raw:
            click.echo(json.dumps(data, indent=2))
        else:
            config_inner = data.get("config") or {}
            model_info = config_inner.get("model") or {}
            provider_info = config_inner.get("provider") or {}
            instructions = config_inner.get("instructions") or ""

            console.print(
                Panel(
                    f"[bold cyan]AI Config Key:[/bold cyan] {cfg.ai_config_key}\n"
                    f"[bold cyan]Provider:[/bold cyan] {provider_info.get('name', 'N/A')}\n"
                    f"[bold cyan]Model:[/bold cyan] {model_info.get('name', 'N/A')}\n"
                    f"[bold cyan]Enabled:[/bold cyan] {data.get('enabled', False)}\n\n"
                    f"[bold]System Instructions:[/bold]\n{instructions}",
                    title="[bold green]LaunchDarkly AgentControl Inspection[/bold green]",
                    border_style="green",
                )
            )
        return

    # If prompt not passed in args, read from stdin if piped, else prompt user
    if not prompt:
        if not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()
        else:
            prompt = click.prompt("Enter writing instruction or text to rewrite")

    if not prompt:
        click.echo("Error: prompt cannot be empty.", err=True)
        sys.exit(1)

    result = asyncio.run(
        generate_writing_with_agentcontrol(
            prompt,
            user_id=user_id,
            persona=persona,
            config=cfg,
            force_fallback=force_fallback,
        )
    )

    if json_mode:
        out: dict[str, Any] = {
            "content": result.content,
            "provider": result.provider,
            "model": result.model,
            "mode": result.mode,
            "source": result.source,
            "usage": result.usage,
            "summary": result.summary,
            "error": result.error,
        }
        click.echo(json.dumps(out, indent=2))
        return

    if raw:
        click.echo(result.content)
        return

    # Rich formatted output
    header = (
        f"[bold]Provider:[/bold] {result.provider} | "
        f"[bold]Model:[/bold] {result.model} | "
        f"[bold]Source:[/bold] {result.source}"
    )
    if result.summary:
        console.print(
            Panel(
                result.summary,
                title="[bold yellow]Summary of Changes[/bold yellow]",
                border_style="yellow",
            )
        )

    console.print(
        Panel(
            Markdown(result.content),
            title=f"[bold green]Writing Assistant ({persona})[/bold green]",
            subtitle=header,
            border_style="blue",
        )
    )
