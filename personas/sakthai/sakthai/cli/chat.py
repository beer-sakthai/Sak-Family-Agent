"""The ``chat`` command: an interactive multi-turn REPL with a Sak Family persona."""

from __future__ import annotations

from collections.abc import Callable

import click
from rich.console import Console

from .. import config
from ..agent.chat import load_persona_soul, run_chat
from ..agent.loop import DEFAULT_MODEL
from ..memory.store import MemoryStore
from .agent import _tool_context


def _make_read_input() -> Callable[[], str | None]:
    from prompt_toolkit import PromptSession

    session: PromptSession[str] = PromptSession()

    def _read() -> str | None:
        try:
            return session.prompt("> ")
        except EOFError:
            return None

    return _read


@click.command()
@click.option(
    "--persona",
    type=click.Choice(config.PERSONA_NAMES),
    default="sakthai",
    show_default=True,
    help="Which Sak Family persona to chat with.",
)
@click.option("--model", default=DEFAULT_MODEL, show_default=True, help="Model identifier.")
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["anthropic", "google", "openai", "ollama", "gateway"]),
    help="LLM provider backend.",
)
@click.option(
    "--no-mcp",
    is_flag=True,
    help="Don't load external MCP servers (from ~/.sakthai/mcp.json and extensions).",
)
@click.option(
    "--with-skills",
    "with_skills",
    multiple=True,
    help="Inject the named skill's instructions into the system prompt (repeatable).",
)
@click.option(
    "--caveman",
    type=click.Choice(["lite", "full", "ultra", "wenyan-lite", "wenyan-full", "wenyan-ultra"]),
    help="Enable Caveman token compression at the specified intensity level.",
)
def chat(
    persona: str,
    model: str,
    provider: str | None,
    no_mcp: bool,
    with_skills: tuple[str, ...],
    caveman: str | None,
) -> None:
    """Open an interactive multi-turn chat session with a Sak Family persona.

    Type /exit or press Ctrl+D to end the session. Conversation history is
    kept in-process for this session only; continuity across separate
    `sakthai chat` runs comes from persistent memory, same as `sakthai run`.
    """
    soul_text = load_persona_soul(persona)
    console = Console()
    store = MemoryStore()
    try:
        with _tool_context(no_mcp=no_mcp, verbose=False) as tools:
            run_chat(
                persona=persona,
                soul_text=soul_text,
                tools=tools,
                model=model,
                provider=provider,
                caveman=caveman,
                with_skills=with_skills,
                store=store,
                console=console,
                read_input=_make_read_input(),
            )
    finally:
        store.close()
