"""The ``chat`` command: an interactive multi-turn session with a Sak Family persona.

Two frontends: the full-screen Textual app (:class:`sakthai.agent.tui.SakThaiApp`,
ported from the standalone ``sakthai-chat-cli``) and the inline prompt_toolkit
REPL (:func:`sakthai.agent.chat.run_chat`). ``--ui auto`` picks the TUI on a real
terminal and the inline REPL otherwise, so pipes and CI keep working.
"""

from __future__ import annotations

import contextlib
import sys
from collections.abc import Callable
from typing import Any

import click
from rich.console import Console

from .. import config
from ..agent.chat import load_persona_soul, run_chat
from ..memory.store import MemoryStore
from .agent import _tool_context

# Default chat to the fine-tuned SakThai model served locally by Ollama (model
# tag "sakthai"), so `sakthai chat` runs free/offline. Override with
# --provider/--model for cloud backends.
DEFAULT_CHAT_PROVIDER = "ollama"
DEFAULT_CHAT_MODEL = "sakthai"

UI_CHOICES = ("auto", "tui", "inline")


def _is_interactive() -> bool:
    return bool(sys.stdin.isatty() and sys.stdout.isatty())


def _resolve_ui(ui: str) -> str:
    """Map ``--ui`` to the concrete frontend: ``"tui"`` or ``"inline"``."""
    if ui == "auto":
        return "tui" if _is_interactive() else "inline"
    if ui == "tui" and not _is_interactive():
        raise click.ClickException(
            "--ui tui needs an interactive terminal. Use --ui inline, or for "
            'non-interactive use try: sakthai run "<task>".'
        )
    return ui


def _make_tui_app(**kwargs: Any) -> Any:
    # Lazy import keeps Textual off the CLI's startup path for other commands.
    from ..agent.tui import SakThaiApp

    return SakThaiApp(**kwargs)


def _make_read_input(prompt: str = "> ") -> Callable[[], str | None]:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import FileHistory

    history_file = config.sakthai_home() / "cli_history"
    with contextlib.suppress(OSError):
        history_file.parent.mkdir(parents=True, exist_ok=True)

    completer = WordCompleter(
        [
            "/help",
            "/status",
            "/persona",
            "/model",
            "/provider",
            "/tools",
            "/skills",
            "/memory",
            "/learn",
            "/doctor",
            "/goal",
            "/clear",
            "/reset",
            "/exit",
            "/quit",
        ],
        ignore_case=True,
    )

    try:
        session: PromptSession[str] = PromptSession(
            history=FileHistory(str(history_file)),
            completer=completer,
        )
    except TypeError:
        session = PromptSession()
    except Exception:
        session = PromptSession()

    def _read() -> str | None:
        try:
            return str(session.prompt(prompt))
        except EOFError:
            return None
        except KeyboardInterrupt:
            return ""

    return _read


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
    type=click.Choice(["anthropic", "google", "openai", "ollama", "gateway", "huggingface"]),
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
@click.option(
    "--ui",
    type=click.Choice(UI_CHOICES),
    default="auto",
    show_default=True,
    help="auto = full-screen TUI on a terminal, inline REPL otherwise.",
)
def chat(
    persona: str,
    model: str,
    provider: str | None,
    no_mcp: bool,
    with_skills: tuple[str, ...],
    caveman: str | None,
    ui: str,
) -> None:
    """Open an interactive multi-turn chat session with a Sak Family persona.

    Type /exit or press Ctrl+D to end the session. Conversation history is
    kept in-process for this session only; continuity across separate
    `sakthai chat` runs comes from persistent memory, same as `sakthai run`.
    """
    # Like `run --persona`, the persona's own config.yaml picks the model when
    # the caller did not. Unlike `run`, the pair is taken whole and only when
    # neither flag was passed (asked of click, not inferred from the value):
    # `--provider ollama` alone keeps the CLI's own pair rather than sending a
    # Hub model name to Ollama, and `--provider ollama --model sakthai` still
    # means local Ollama even though those are also the defaults.
    ctx = click.get_current_context()
    flags_given = any(
        ctx.get_parameter_source(name) is not click.core.ParameterSource.DEFAULT
        for name in ("model", "provider")
    )
    if not flags_given:
        default_provider, default_model = config.persona_model_defaults(persona)
        if default_provider and default_model:
            provider, model = default_provider, default_model

    frontend = _resolve_ui(ui)
    soul_text = load_persona_soul(persona)
    # Each persona gets its own memory shard (~/.sakthai/<persona>/memory.db),
    # matching the SAKTHAI_HOME-per-persona convention used in production.
    store = MemoryStore(config.persona_memory_db_path(persona))
    try:
        with _tool_context(no_mcp=no_mcp, verbose=False, persona=persona) as tools:
            if frontend == "tui":
                _make_tui_app(
                    persona=persona,
                    soul_text=soul_text,
                    tools=tools,
                    model=model,
                    provider=provider,
                    caveman=caveman,
                    with_skills=with_skills,
                    store=store,
                ).run()
                return
            active_p = [persona]
            run_chat(
                persona=persona,
                soul_text=soul_text,
                tools=tools,
                model=model,
                provider=provider,
                caveman=caveman,
                with_skills=with_skills,
                store=store,
                console=Console(),
                read_input=_make_read_input(),
                on_persona_change=lambda new_p: active_p.__setitem__(0, new_p),
            )
    finally:
        store.close()
