"""Output formatting and envelope contract engine for the SakThai CLI.

Standardizes:
1. --json (sak.cli/v1 envelope with {schema, ok, data, error, warnings}).
2. -q / --quiet (compact JSON when combined with --json, silent on success in TTY).
3. --no-color, NO_COLOR, FORCE_COLOR, and interactive TTY auto-detection.
4. Rainbow styling integration via sakthai.agent.ui and sakthai.agent.theme.
5. Standard exit codes:
   - 0: Success / ready / OK
   - 1: Execution failure / uncaught error
   - 2: Usage error (Click)
   - 3: Not ready (preflight unready, missing credentials)
   - 130: Interrupted (SIGINT)
"""

from __future__ import annotations

import functools
import json
import os
import sys
import traceback
from collections.abc import Callable
from typing import Any, TextIO

import click
from rich.console import Console

from ..agent.theme import PERSONA_AVATARS

CLI_SCHEMA_VERSION = "sak.cli/v1"
CLI_ENVELOPE_SCHEMA = "https://schemas.sakthai.family/v1/cli-envelope.json"

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_NOT_READY = 3
EXIT_INTERRUPTED = 130


class OutputContext:
    """Manages CLI streams, formatting, envelope creation, and rainbow flourishes."""

    def __init__(
        self,
        *,
        json_output: bool = False,
        quiet: bool = False,
        no_color: bool = False,
        legacy_json: bool = False,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
    ) -> None:
        self.json = json_output
        self.quiet = quiet
        self.legacy_json = legacy_json or (os.environ.get("SAK_JSON_LEGACY") == "1")
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.warnings: list[str] = []

        # Color suppression precedence:
        # 1. explicit --no-color flag
        # 2. NO_COLOR env var (any value)
        # 3. FORCE_COLOR env var ("1", "true")
        # 4. sys.stdout.isatty()
        if no_color or "NO_COLOR" in os.environ:
            self.no_color = True
        elif os.environ.get("FORCE_COLOR") in ("1", "true", "TRUE"):
            self.no_color = False
        else:
            self.no_color = not getattr(self.stdout, "isatty", lambda: False)()

        self._console: Console | None = None
        self._err_console: Console | None = None

    @property
    def console(self) -> Console:
        if self._console is None:
            self._console = Console(
                file=self.stdout,
                no_color=self.no_color,
                highlight=False,
            )
        return self._console

    @property
    def err_console(self) -> Console:
        if self._err_console is None:
            self._err_console = Console(
                file=self.stderr,
                no_color=self.no_color,
                highlight=False,
            )
        return self._err_console

    def emit(
        self,
        data: Any,
        *,
        tty_renderable: Any = None,
        text_fn: Callable[[], None] | None = None,
        exit_code: int = EXIT_OK,
    ) -> None:
        """Emit successful or completed data according to active flags."""
        if self.json:
            if self.legacy_json:
                payload = data
            else:
                payload = {
                    "schema": CLI_SCHEMA_VERSION,
                    "$schema": CLI_ENVELOPE_SCHEMA,
                    "ok": exit_code == EXIT_OK,
                    "data": data,
                    "error": None,
                    "warnings": list(self.warnings),
                }
            indent = None if self.quiet else 2
            separators = (",", ":") if self.quiet else None
            out_str = json.dumps(payload, indent=indent, separators=separators, default=str)
            self.stdout.write(out_str + "\n")
            self.stdout.flush()
            if exit_code != EXIT_OK:
                sys.exit(exit_code)
            return

        if self.quiet:
            if exit_code != EXIT_OK:
                sys.exit(exit_code)
            return

        if tty_renderable is not None:
            self.console.print(tty_renderable)
        elif text_fn is not None:
            text_fn()

        if exit_code != EXIT_OK:
            sys.exit(exit_code)

    def error(
        self,
        message: str,
        *,
        code: str = "ERROR",
        details: Any = None,
        exc: Exception | None = None,
        exit_code: int = EXIT_ERROR,
    ) -> None:
        """Emit an error according to active flags, adhering to the stream contract."""
        if self.json:
            if self.legacy_json:
                payload = {"error": message, "code": code, "details": details}
            else:
                payload = {
                    "schema": CLI_SCHEMA_VERSION,
                    "$schema": CLI_ENVELOPE_SCHEMA,
                    "ok": False,
                    "data": None,
                    "error": {
                        "code": code,
                        "message": message,
                        "type": type(exc).__name__ if exc else code,
                        "details": details,
                    },
                    "warnings": list(self.warnings),
                }
            indent = None if self.quiet else 2
            separators = (",", ":") if self.quiet else None
            out_str = json.dumps(payload, indent=indent, separators=separators, default=str)
            self.stdout.write(out_str + "\n")
            self.stdout.flush()

            debug_active = os.environ.get("SAK_DEBUG") == "1" or "--debug" in sys.argv
            if debug_active and exc is not None:
                traceback.print_exc(file=self.stderr)
            sys.exit(exit_code)

        # Human-readable / TTY error output
        if not self.no_color:
            self.err_console.print(f"[bold red]✗ Error ({code}):[/bold red] {message}")
        else:
            self.stderr.write(f"✗ Error ({code}): {message}\n")
            self.stderr.flush()

        debug_active = os.environ.get("SAK_DEBUG") == "1" or "--debug" in sys.argv
        if debug_active and exc is not None:
            traceback.print_exc(file=self.stderr)

        sys.exit(exit_code)

    def warn(self, message: str) -> None:
        """Record a warning and emit to stderr if not quiet/json."""
        self.warnings.append(message)
        if not self.quiet and not self.json:
            if not self.no_color:
                self.err_console.print(f"[bold yellow]! Warning:[/bold yellow] {message}")
            else:
                self.stderr.write(f"! Warning: {message}\n")
                self.stderr.flush()

    def rainbow_header(self, title: str, persona: str = "sakthai") -> None:
        """Print a full-width vibrant rainbow header in TTY mode."""
        if self.quiet or self.json:
            return
        avatar = PERSONA_AVATARS.get(persona, "🐘")
        header_text = f"── {avatar} {title} ──"
        if self.no_color:
            self.stdout.write(f"\n{header_text}\n")
            self.stdout.flush()
            return
        from ..agent.ui import rainbow_text

        self.console.print()
        self.console.print(rainbow_text(header_text, style="bold"))

    def rainbow_rule(self, width: int = 60) -> None:
        """Print a vibrant rainbow horizontal rule in TTY mode."""
        if self.quiet or self.json:
            return
        if self.no_color:
            self.stdout.write("─" * max(width, 1) + "\n")
            self.stdout.flush()
            return
        from ..agent.ui import rainbow_rule

        self.console.print(rainbow_rule(max(width, 1)))

    def rainbow_text(self, text: str, style: str = "") -> Any:
        """Return Rich Text with RAINBOW_STOPS gradient or plain string if no-color."""
        if self.no_color:
            return text
        from ..agent.ui import rainbow_text

        return rainbow_text(text, style=style)


def output_options(fn: Any) -> Any:
    """Click decorator injecting standard output options (--json, -q, --no-color, --legacy-json).

    Passes a typed `out: OutputContext` keyword argument to the decorated command.
    """

    @click.option(
        "--json",
        "json_output",
        is_flag=True,
        help="Emit a deterministic JSON report in sak.cli/v1 envelope.",
    )
    @click.option(
        "-q",
        "--quiet",
        "quiet_output",
        is_flag=True,
        help="Emit compact output or silent on success.",
    )
    @click.option(
        "--no-color",
        "no_color",
        is_flag=True,
        help="Disable colored output.",
    )
    @click.option(
        "--legacy-json",
        "legacy_json",
        is_flag=True,
        help="Emit raw legacy JSON payload without envelope.",
    )
    @functools.wraps(fn)
    def wrapper(
        *args: Any,
        json_output: bool = False,
        quiet_output: bool = False,
        no_color: bool = False,
        legacy_json: bool = False,
        **kwargs: Any,
    ) -> Any:
        out = OutputContext(
            json_output=json_output,
            quiet=quiet_output,
            no_color=no_color,
            legacy_json=legacy_json,
        )
        try:
            return fn(*args, out=out, **kwargs)
        except click.ClickException:
            raise
        except SystemExit:
            raise
        except Exception as exc:
            if out.json:
                out.error(str(exc), code="INTERNAL_ERROR", exc=exc, exit_code=EXIT_ERROR)
            raise

    return wrapper


__all__ = [
    "CLI_ENVELOPE_SCHEMA",
    "CLI_SCHEMA_VERSION",
    "EXIT_ERROR",
    "EXIT_INTERRUPTED",
    "EXIT_NOT_READY",
    "EXIT_OK",
    "EXIT_USAGE",
    "OutputContext",
    "output_options",
]
