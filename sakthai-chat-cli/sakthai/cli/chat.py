"""The ``chat`` command: launch the full-screen Textual chat app."""

from __future__ import annotations

import sys

import click

from .. import config
from ..agent.chat import load_persona_soul
from ..agent.tui import SakThaiApp
from ..memory.store import MemoryStore
from .agent import _tool_context

# This standalone repo defaults chat to the fine-tuned SakThai model, served
# locally by Ollama as the model tag ``sakthai`` — the merged weights from
# Nanthasit/sakthai-context-1.5b-merged, registered by
# scripts/setup_local_model.sh (see README "Serving"). Any other backend stays
# reachable via ``--provider``/``--model``.
DEFAULT_CHAT_PROVIDER = "ollama"
DEFAULT_CHAT_MODEL = "sakthai"


@click.command()
@click.option(
    "--persona",
    type=click.Choice(config.PERSONA_NAMES),
    default="sakthai",
    show_default=True,
    help="Which Sak Family persona to chat with.",
)
@click.option("--model", default=DEFAULT_CHAT_MODEL, show_default=True, help="Model identifier.")
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["anthropic", "google", "openai", "ollama", "gateway"]),
    default=DEFAULT_CHAT_PROVIDER,
    show_default=True,
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
    """Open an interactive full-screen chat session with a Sak Family persona.

    Type /exit or press Ctrl+D to end the session. Conversation history is
    kept in-process for this session only; continuity across separate
    `sakthai chat` runs comes from persistent memory, same as `sakthai run`.
    """
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise click.ClickException(
            "chat needs an interactive terminal. For non-interactive use, try: "
            'sakthai run "<task>".'
        )
    soul_text = load_persona_soul(persona)
    store = MemoryStore()
    try:
        with _tool_context(no_mcp=no_mcp, verbose=False) as tools:
            app = SakThaiApp(
                persona=persona,
                soul_text=soul_text,
                tools=tools,
                model=model,
                provider=provider,
                caveman=caveman,
                with_skills=with_skills,
                store=store,
            )
            app.run()
    finally:
        store.close()
