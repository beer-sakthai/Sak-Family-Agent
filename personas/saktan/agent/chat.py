"""Interactive multi-turn chat: persona identity, rendering, and the REPL loop.

Backs ``sakthai chat``. Two frontends share this module:

* the inline REPL (:func:`run_chat`) keeps `rich`/`prompt_toolkit` I/O at this
  module's edges (renderers take an injected ``Console``; the loop takes an
  injected ``read_input`` callable) so the conversation flow is testable
  without a real terminal;
* the full-screen Textual app (:mod:`sakthai.agent.tui`) mounts the pure Rich
  builders below (``user_panel``, ``reply_panel``, ``slash_result`` …), which
  take plain data and return renderables with no I/O of their own.
"""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
import sys
import time
from collections.abc import Callable
from typing import Any

from rich import box
from rich.console import Console, RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from .. import __version__, config
from ..memory.store import MemoryStore
from .loop import AgentError, run_agent
from .theme import (
    GLYPH_CANCEL,
    GLYPH_ERROR,
    GLYPH_RESULT,
    GLYPH_SUCCESS,
    GLYPH_TOOL,
    PERSONA_ACCENTS,
    USER_AVATAR,
    USER_COLOR,
)
from .theme import PERSONA_COLORS as THEME_PERSONA_COLORS
from .tools import Tool
from .ui import (
    chip,
    help_panel,
    memory_panel,
    persona_avatar,
    personas_panel,
    skills_panel,
    status_panel,
    tools_panel,
    welcome_panel,
)

logger = logging.getLogger(__name__)

PERSONA_LABELS: dict[str, str] = {
    "sakking": "SakKing",
    "sakthai": "SakThai",
    "saksee": "SakSee",
    "saksit": "SakSit",
    "sakjules": "SakJules",
    "saktan": "SakTan",
}

PERSONA_COLORS: dict[str, str] = {
    "sakking": "bright_magenta",
    "sakthai": "cyan",
    "saksee": "green",
    "saksit": "yellow",
    "sakjules": "bright_red",
    "saktan": "bright_blue",
}


def load_persona_soul(persona: str) -> str:
    """Read a persona's SOUL.md identity text.

    Returns "" (and logs a warning) if the file is unexpectedly missing —
    all six personas currently have one, so this is a defensive fallback,
    not the normal path.
    """
    path = config.persona_soul_path(persona)
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        logger.warning("No SOUL.md found for persona %r at %s; using base identity.", persona, path)
        return ""


def render_user_turn(console: Console, text: str) -> None:
    console.print(f"[bold]you[/bold]\n{text}\n")


def make_tool_renderer(console: Console) -> Callable[[str, dict[str, Any]], None]:
    """Build an ``on_event`` callback for ``run_agent`` that renders tool calls."""

    def _on_event(kind: str, payload: dict[str, Any]) -> None:
        if kind == "tool_call_start":
            console.print(f"[dim]⚙ running {payload['name']}({payload.get('input', {})}) …[/dim]")
            return
        if kind != "tool_call":
            return
        is_err = payload.get("is_error", False)
        status = "[red]✗[/red]" if is_err else "[green]✓[/green]"
        tag = "tool!" if is_err else "tool"
        elapsed = payload.get("elapsed")
        elapsed_str = f" [dim]⏱ {elapsed:.2f}s[/dim]" if elapsed is not None else ""
        console.print(
            f"[dim]⚙ {tag} {payload['name']}({payload.get('input', {})}) {status}{elapsed_str}[/dim]"
        )
        preview = payload.get("output_preview")
        if preview:
            console.print(f"[dim]  → {preview}[/dim]")

    return _on_event


def make_token_renderer(console: Console, persona: str) -> Callable[[str], None]:
    """Build an ``on_token`` callback for ``run_agent`` that streams a reply.

    Prints the persona's label once, then writes raw token text directly to
    the console's stream (bypassing rich's markup engine) so a stream of
    small deltas doesn't get re-wrapped or re-highlighted mid-word.
    """
    label = PERSONA_LABELS.get(persona, persona)
    color = PERSONA_COLORS.get(persona, "white")
    started = False

    def _on_token(text: str) -> None:
        nonlocal started
        if not started:
            console.print(f"[{color} bold]{label}[/{color} bold]", end=" ")
            started = True
        console.file.write(text)
        console.file.flush()

    return _on_token


def render_error(console: Console, exc: Exception) -> None:
    console.print(f"[red]error:[/red] {exc}")


def render_cancelled(console: Console) -> None:
    console.print("[yellow](cancelled)[/yellow]")


def status_line(store: MemoryStore, model: str, tool_count: int) -> str:
    n_facts = store.stats()["facts"]["total"]
    return f"{model} · {tool_count} tools · memory: {n_facts} facts"


def run_chat(
    *,
    persona: str,
    soul_text: str,
    tools: tuple[Tool, ...],
    model: str,
    provider: str | None,
    caveman: str | None,
    with_skills: tuple[str, ...],
    store: MemoryStore,
    console: Console,
    read_input: Callable[[], str | None],
    on_persona_change: Callable[[str], None] | None = None,
    confirm_tool: Callable[[str, dict[str, Any]], bool] | None = None,
) -> None:
    """Run an interactive multi-turn chat session (inline REPL).

    Like Claude Code, Gemini CLI, and AGY:
    - Welcome header with persona, model, provider, and active tools.
    - Full in-session slash commands (/help, /status, /persona, /model, /tools,
      /skills, /memory, /learn, /doctor, /clear, /reset, /goal, /exit).
    - Direct shell command execution with !<command>.
    - Graceful cancellation with Ctrl+C and clean termination with Ctrl+D / /exit.
    """
    prior_messages: list[dict[str, Any]] = []
    tool_renderer = make_tool_renderer(console)
    goal: str | None = None
    active_store = store
    active_persona = persona
    active_soul = soul_text
    active_model = model
    active_provider = provider

    console.print(
        welcome_panel(
            persona=active_persona,
            model=active_model,
            provider=active_provider,
            tool_count=len(tools),
            facts=active_store.stats()["facts"]["total"] if active_store else 0,
            version=__version__,
            goal=goal,
        )
    )

    try:
        while True:
            try:
                user_text = read_input()
            except KeyboardInterrupt:
                render_cancelled(console)
                continue
            if user_text is None or user_text.strip() in ("/exit", "/quit"):
                console.print("[dim]Goodbye! Keep growing.[/dim]")
                break
            stripped = user_text.strip()
            if not stripped:
                continue

            # Shell execution escape: !<cmd>
            if stripped.startswith("!"):
                cmd_str = stripped[1:].strip()
                if not cmd_str:
                    console.print("[dim]Usage: !<command> (e.g. !git status)[/dim]")
                    continue
                console.print(f"[dim]⚙ {cmd_str}[/dim]")
                try:
                    argv = shlex.split(cmd_str, posix=sys.platform != "win32")
                    if not argv:
                        continue
                    proc = subprocess.run(  # nosec B603 — shell=False, interactive terminal user escape
                        argv,
                        shell=False,
                        text=True,
                        capture_output=True,
                        timeout=60,
                    )
                    if proc.stdout:
                        console.print(proc.stdout.rstrip())
                    if proc.stderr:
                        console.print(f"[red]{proc.stderr.rstrip()}[/red]")
                    if proc.returncode != 0:
                        console.print(f"[dim red](exit {proc.returncode})[/dim red]")
                except Exception as exc:
                    console.print(f"[red]Error executing command:[/red] {exc}")
                continue

            # In-REPL slash commands
            if stripped.startswith("/"):
                verb, _, rest = stripped.partition(" ")
                verb = verb.strip().lower()
                rest = rest.strip()

                if verb == "/clear":
                    console.clear()
                    continue

                if verb in ("/reset", "/new"):
                    prior_messages.clear()
                    console.print(
                        "[dim]Conversation history reset. Persistent memory retained.[/dim]"
                    )
                    continue

                if verb == "/persona" and rest:
                    if rest in config.PERSONA_NAMES:
                        active_persona = rest
                        active_soul = load_persona_soul(active_persona)
                        if active_store is not store and active_store is not None:
                            active_store.close()
                        active_store = MemoryStore(config.persona_memory_db_path(active_persona))
                        p_provider, p_model = config.persona_model_defaults(active_persona)
                        if p_provider:
                            active_provider = p_provider
                        if p_model:
                            active_model = p_model
                        if on_persona_change:
                            on_persona_change(active_persona)
                        label = PERSONA_LABELS.get(active_persona, active_persona)
                        color = PERSONA_COLORS.get(active_persona, "cyan")
                        console.print(
                            f"[{color} bold]Switched to {label}[/{color} bold] · {active_model} ({active_provider})"
                        )
                        continue
                    else:
                        console.print(
                            f"[red]Unknown persona {rest!r}. Valid: {', '.join(config.PERSONA_NAMES)}[/red]"
                        )
                        continue

                if verb == "/model" and rest:
                    active_model = rest
                    console.print(f"[green]Model changed to:[/green] [bold]{active_model}[/bold]")
                    continue

                if verb == "/provider" and rest:
                    active_provider = rest
                    console.print(
                        f"[green]Provider changed to:[/green] [bold]{active_provider}[/bold]"
                    )
                    continue

                if verb == "/learn":
                    if rest and active_store:
                        active_store.add_fact(rest, source_session="cli")
                        console.print(
                            f"[green]✓ Fact stored in {active_persona} memory:[/green] {rest}"
                        )
                    else:
                        console.print("[dim]Usage: /learn <fact to store>[/dim]")
                    continue

                handled, goal, renderables = slash_result(
                    stripped,
                    persona=active_persona,
                    goal=goal,
                    store=active_store,
                    tools=tools,
                    model=active_model,
                    provider=active_provider,
                    turns=len(prior_messages),
                )
                if handled:
                    for r in renderables:
                        console.print(r)
                    continue

            # Standard chat turn
            render_user_turn(console, stripped)
            token_renderer = make_token_renderer(console, active_persona)
            try:
                prefix = goal_prompt_prefix(active_soul, goal)
                result = run_agent(
                    stripped,
                    history=prior_messages,
                    system_prompt_prefix=prefix,
                    model=active_model,
                    provider=active_provider,
                    tools=tools,
                    caveman=caveman,
                    skills=list(with_skills),
                    store=active_store,
                    on_event=tool_renderer,
                    on_token=token_renderer,
                    on_confirm=confirm_tool,
                    persona=active_persona,
                )
            except AgentError as exc:
                render_error(console, exc)
                continue
            except KeyboardInterrupt:
                render_cancelled(console)
                continue
            console.print()
            prior_messages = result.messages
            console.print(f"[dim]{status_line(active_store, active_model, len(tools))}[/dim]\n")
    finally:
        if active_store is not store and active_store is not None:
            active_store.close()


# ---------------------------------------------------------------------------
# Pure Rich builders for the full-screen Textual frontend (sakthai.agent.tui).
# Ported from the standalone sakthai-chat-cli; no I/O, so they're unit-testable.
# ---------------------------------------------------------------------------


def _truncate(value: str, limit: int = 80) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "…"


def user_panel(text: str) -> Panel:
    """The user's message as a blue titled panel (plain text, never markup)."""
    return Panel(
        Text(text),
        box=box.ROUNDED,
        title=f"[bold {USER_COLOR}]{USER_AVATAR} you[/bold {USER_COLOR}]",
        title_align="left",
        subtitle=f"[dim]{time.strftime('%H:%M')}[/dim]",
        subtitle_align="right",
        border_style=USER_COLOR,
    )


def tool_args_summary(name: str, args: dict[str, Any]) -> str:
    """Return a concise, readable summary of tool arguments for CLI/TUI traces."""
    if name in ("edit_file", "write_file", "read_file"):
        path = args.get("path", "")
        if name == "edit_file":
            old = str(args.get("old_text", ""))
            return (
                f"path={path!r}, old_text={old[:30]!r}…"
                if len(old) > 30
                else f"path={path!r}, old_text={old!r}"
            )
        if name == "write_file":
            content_len = len(str(args.get("content", "")))
            return f"path={path!r}, {content_len} chars"
        return f"path={path!r}"
    if name == "grep_search":
        pattern = args.get("pattern", "")
        glob = args.get("glob")
        return f"pattern={pattern!r}" + (f", glob={glob!r}" if glob else "")
    if name == "glob_files":
        return f"pattern={args.get('pattern', '')!r}"
    if name == "run_command":
        return f"{args.get('command', '')!r}"
    return f"{args}"


def format_diff_renderable(
    diff_text: str, added: int = 0, removed: int = 0, path: str = ""
) -> Panel:
    """Format a unified diff with green additions, red deletions, and cyan hunk headers."""
    text = Text()
    for line in diff_text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            text.append(line + "\n", style="bold")
        elif line.startswith("@@"):
            text.append(line + "\n", style="cyan")
        elif line.startswith("+"):
            text.append(line + "\n", style="green")
        elif line.startswith("-"):
            text.append(line + "\n", style="red")
        else:
            text.append(line + "\n", style="dim")

    title = f"Diff Preview: [bold]{path}[/bold]" if path else "Diff Preview"
    subtitle = (
        f"[green]+{added}[/green] / [red]-{removed}[/red] lines" if (added or removed) else None
    )
    return Panel(
        text,
        title=title,
        subtitle=subtitle,
        border_style="yellow",
        box=box.ROUNDED,
    )


def tool_trace(payload: dict[str, Any], *, persona: str | None = None) -> Text:
    """One trace renderable for a tool_call event: name + args, plus preview line."""
    accent = PERSONA_ACCENTS.get(persona or "", "cyan")
    line = Text()
    name = payload.get("name", "")
    args = payload.get("input", {})
    summary = tool_args_summary(name, args)
    line.append(f"{GLYPH_TOOL} {name}", style=f"bold {accent}")
    line.append(f"({_truncate(summary, 70)})", style="dim")
    if payload.get("is_error"):
        line.append(f" {GLYPH_ERROR}", style="bold red")
    else:
        line.append(f" {GLYPH_SUCCESS}", style="bold green")
    elapsed = payload.get("elapsed")
    if elapsed is not None:
        line.append(f" ⏱ {elapsed:.2f}s", style="dim")
    preview = payload.get("output_preview")
    if preview:
        line.append(f"\n  {GLYPH_RESULT} ", style=accent)
        line.append(str(preview), style="dim italic")
    return line


def tool_running_trace(payload: dict[str, Any], *, persona: str | None = None) -> Text:
    """Trace renderable for tool_call_start: running indicator with name + args."""
    accent = PERSONA_ACCENTS.get(persona or "", "cyan")
    line = Text()
    name = payload.get("name", "")
    args = payload.get("input", {})
    summary = tool_args_summary(name, args)
    line.append(f"{GLYPH_TOOL} {name}", style=f"bold {accent}")
    line.append(f"({_truncate(summary, 70)})", style="dim")
    line.append(" … running", style="dim italic")
    return line


def _reply_title(persona: str, matched: tuple[str, str] | None) -> tuple[str, str, str]:
    display = matched[0] if matched else persona
    label = PERSONA_LABELS.get(display, display)
    color = THEME_PERSONA_COLORS.get(display, "white")
    return label, color, persona_avatar(display)


def reply_panel(
    parts: list[str],
    *,
    persona: str,
    matched: tuple[str, str] | None,
    streaming: bool,
) -> Panel:
    """The persona reply panel: plain Text while streaming, Markdown when final."""
    label, color, avatar = _reply_title(persona, matched)
    body: RenderableType
    body = Text("".join(parts)) if streaming else Markdown("".join(parts))
    if streaming:
        subtitle: RenderableType = "[dim]▌ streaming…[/dim]"
    elif matched:
        subtitle = chip(f"best matched: {label} · {matched[1]}", accent=color, glyph=avatar)
    else:
        subtitle = f"[dim]{time.strftime('%H:%M')}[/dim]"
    return Panel(
        body,
        box=box.ROUNDED,
        title=f"[{color}]{avatar}[/{color}] [bold {color}]{label}[/bold {color}]",
        title_align="left",
        subtitle=subtitle,  # type: ignore[arg-type]
        subtitle_align="right",
        border_style=color,
    )


def error_text(exc: Exception) -> Text:
    return Text.from_markup(f"[bold red]{GLYPH_ERROR} error:[/bold red] {exc}")


def cancelled_text() -> Text:
    return Text.from_markup(f"[yellow]{GLYPH_CANCEL} cancelled[/yellow]")


def goal_prompt_prefix(soul_text: str, goal: str | None) -> str:
    """Fold an active session goal into the system-prompt prefix for the agent."""
    if not goal:
        return soul_text
    directive = (
        f"The user has pinned this session goal — keep it in mind and steer toward it: {goal}"
    )
    return f"{soul_text}\n\n{directive}".strip()


def slash_result(
    command: str,
    *,
    persona: str,
    goal: str | None,
    store: MemoryStore | None,
    tools: tuple[Tool, ...] = (),
    model: str = "sakthai",
    provider: str | None = None,
    turns: int = 0,
) -> tuple[bool, str | None, list[RenderableType]]:
    """Side-effect-free slash-command handler; returns (handled, goal, renderables)."""
    stripped = command.strip()
    if not stripped.startswith("/"):
        return False, goal, []
    verb, _, rest = stripped.partition(" ")
    verb = verb.strip().lower()
    rest = rest.strip()
    if verb == "/help":
        return True, goal, [help_panel(persona=persona)]
    if verb == "/tools":
        return True, goal, [tools_panel(tools, persona=persona)]
    if verb == "/skills":
        from ..skills import collect_skills, default_skill_roots

        skills = sorted(collect_skills(*default_skill_roots(persona)), key=lambda s: s.name)
        return True, goal, [skills_panel(skills, persona=persona)]
    if verb == "/memory":
        if store is None:
            return True, goal, []
        return True, goal, [memory_panel(store.list_facts(limit=15), persona=persona)]
    if verb == "/clear":
        return True, None, []
    if verb in ("/reset", "/new"):
        return (
            True,
            goal,
            [
                Text.from_markup(
                    "[dim]Conversation history reset. Persistent memory retained.[/dim]"
                )
            ],
        )
    if verb == "/goal":
        if not rest:
            msg = "goal cleared" if goal else "usage: /goal <what you want to accomplish>"
            return True, None, [Text.from_markup(f"[dim]{msg}[/dim]")]
        return True, rest, [Text.from_markup(f"[bold]🎯 goal set:[/bold] [italic]{rest}[/italic]")]
    if verb == "/status":
        facts_count = store.stats()["facts"]["total"] if store else 0
        obs_count = store.stats().get("observations", {}).get("total", 0) if store else 0
        return (
            True,
            goal,
            [
                status_panel(
                    persona=persona,
                    model=model,
                    provider=provider,
                    tool_count=len(tools),
                    facts=facts_count,
                    observations=obs_count,
                    goal=goal,
                    turns=turns,
                    cwd=os.getcwd(),
                )
            ],
        )
    if verb == "/persona":
        if not rest:
            return True, goal, [personas_panel()]
        if rest in config.PERSONA_NAMES:
            label = PERSONA_LABELS.get(rest, rest)
            return True, goal, [Text.from_markup(f"[green]Persona set to {label}[/green]")]
        return (
            True,
            goal,
            [
                Text.from_markup(
                    f"[red]Unknown persona {rest!r}. Valid: {', '.join(config.PERSONA_NAMES)}[/red]"
                )
            ],
        )
    if verb == "/model":
        if not rest:
            return True, goal, [Text.from_markup(f"Current model: [bold]{model}[/bold]")]
        return True, goal, [Text.from_markup(f"[green]Model set to:[/green] [bold]{rest}[/bold]")]
    if verb == "/provider":
        if not rest:
            return (
                True,
                goal,
                [Text.from_markup(f"Current provider: [bold]{provider or 'default'}[/bold]")],
            )
        return (
            True,
            goal,
            [Text.from_markup(f"[green]Provider set to:[/green] [bold]{rest}[/bold]")],
        )
    if verb == "/doctor":
        report = config.check_env()
        paths = report.get("paths", {})
        auth = report.get("auth", {})
        ready_tag = (
            "[green]READY[/green]" if report.get("ready") else "[yellow]ATTENTION NEEDED[/yellow]"
        )
        text = Text.from_markup(
            f"Environment Status: {ready_tag}\n"
            f"SakThai Home: [dim]{paths.get('sakthai_home')}[/dim]\n"
            f"Memory DB: [dim]{paths.get('memory_db')}[/dim] (exists: {paths.get('memory_db_exists')})\n"
            f"Providers: anthropic={auth.get('anthropic_ok')} gemini={auth.get('gemini_ok')} hf={auth.get('huggingface_ok')}"
        )
        return True, goal, [Panel(text, title="Diagnostics", box=box.ROUNDED)]
    if verb == "/learn":
        if rest and store:
            store.add_fact(rest, source_session="cli")
            return (
                True,
                goal,
                [Text.from_markup(f"[green]✓ Fact stored in {persona} memory:[/green] {rest}")],
            )
        return True, goal, [Text.from_markup("[dim]Usage: /learn <fact to store>[/dim]")]
    return False, goal, []
