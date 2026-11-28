"""Branch coverage for OutputContext, @output_options, and the system pilot commands."""

from __future__ import annotations

import io
import json
import re
import sys
from types import SimpleNamespace
from typing import Any

import click
import pytest
from click.testing import CliRunner

import sakthai.cli.system as system_mod
from sakthai.cli import main
from sakthai.cli._output import (
    EXIT_ERROR,
    EXIT_INTERRUPTED,
    EXIT_NOT_READY,
    OutputContext,
    output_options,
)


@pytest.fixture(autouse=True)
def _clean_output_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("NO_COLOR", "FORCE_COLOR", "SAK_DEBUG", "SAK_JSON_LEGACY"):
        monkeypatch.delenv(name, raising=False)


def _ctx(**kwargs: Any) -> tuple[OutputContext, io.StringIO, io.StringIO]:
    out_buf, err_buf = io.StringIO(), io.StringIO()
    return OutputContext(stdout=out_buf, stderr=err_buf, **kwargs), out_buf, err_buf


def _color_ctx(monkeypatch: pytest.MonkeyPatch, **kwargs: Any) -> tuple[Any, ...]:
    monkeypatch.setenv("FORCE_COLOR", "1")
    out, out_buf, err_buf = _ctx(**kwargs)
    assert out.no_color is False
    return out, out_buf, err_buf


def test_consoles_are_cached_and_bound_to_their_streams() -> None:
    out, out_buf, err_buf = _ctx()
    assert out.console is out.console
    assert out.err_console is out.err_console
    out.console.print("to-stdout")
    out.err_console.print("to-stderr")
    assert "to-stdout" in out_buf.getvalue()
    assert "to-stderr" in err_buf.getvalue()


def test_emit_quiet_is_silent_and_only_exits_on_failure() -> None:
    out, out_buf, _ = _ctx(quiet=True)
    out.emit({"a": 1})
    assert out_buf.getvalue() == ""
    with pytest.raises(SystemExit) as exc_info:
        out.emit({"a": 1}, exit_code=EXIT_NOT_READY)
    assert exc_info.value.code == EXIT_NOT_READY
    assert out_buf.getvalue() == ""


def test_emit_renders_renderable_or_text_fn_then_exits_with_code() -> None:
    out, out_buf, _ = _ctx()
    out.emit({}, tty_renderable="rendered-text")
    assert "rendered-text" in out_buf.getvalue()

    calls: list[str] = []
    out.emit({}, text_fn=lambda: calls.append("called"))
    assert calls == ["called"]

    with pytest.raises(SystemExit) as exc_info:
        out.emit({}, text_fn=lambda: calls.append("again"), exit_code=EXIT_NOT_READY)
    assert exc_info.value.code == EXIT_NOT_READY
    assert calls == ["called", "again"]


def test_error_legacy_json_is_the_bare_payload() -> None:
    out, out_buf, err_buf = _ctx(json_output=True, legacy_json=True)
    with pytest.raises(SystemExit) as exc_info:
        out.error("nope", code="E_LEGACY")
    assert exc_info.value.code == EXIT_ERROR
    assert json.loads(out_buf.getvalue()) == {"error": "nope", "code": "E_LEGACY", "details": None}
    assert err_buf.getvalue() == ""


def test_error_json_prints_traceback_to_stderr_only_when_debugging(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SAK_DEBUG", "1")
    out, out_buf, err_buf = _ctx(json_output=True)
    try:
        raise ValueError("kaboom")
    except ValueError as exc:
        with pytest.raises(SystemExit):
            out.error("kaboom", code="BOOM", exc=exc)
    assert "ValueError: kaboom" in err_buf.getvalue()
    payload = json.loads(out_buf.getvalue())
    assert payload["error"]["type"] == "ValueError"
    assert "Traceback" not in out_buf.getvalue()


def test_error_human_plain_writes_to_stderr_with_optional_traceback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out, out_buf, err_buf = _ctx()
    with pytest.raises(SystemExit) as exc_info:
        out.error("plain failure", code="E_PLAIN", exit_code=4)
    assert exc_info.value.code == 4
    assert err_buf.getvalue() == "✗ Error (E_PLAIN): plain failure\n"
    assert out_buf.getvalue() == ""

    monkeypatch.setenv("SAK_DEBUG", "1")
    out2, _, err_buf2 = _ctx()
    try:
        raise RuntimeError("with-trace")
    except RuntimeError as exc:
        with pytest.raises(SystemExit):
            out2.error("with-trace", exc=exc)
    assert "RuntimeError: with-trace" in err_buf2.getvalue()


def test_error_human_color_goes_through_the_stderr_console(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out, out_buf, err_buf = _color_ctx(monkeypatch)
    with pytest.raises(SystemExit):
        out.error("colorful failure", code="E_COLOR")
    assert "Error (E_COLOR)" in err_buf.getvalue()
    assert "colorful failure" in err_buf.getvalue()
    assert out_buf.getvalue() == ""


def test_warn_records_always_and_prints_only_for_humans(monkeypatch: pytest.MonkeyPatch) -> None:
    out, _, err_buf = _ctx()
    out.warn("plain warning")
    assert err_buf.getvalue() == "! Warning: plain warning\n"
    assert out.warnings == ["plain warning"]

    color, _, color_err = _color_ctx(monkeypatch)
    color.warn("colored warning")
    assert "Warning:" in color_err.getvalue() and "colored warning" in color_err.getvalue()

    for silent in ({"quiet": True}, {"json_output": True}):
        quiet_out, _, quiet_err = _ctx(**silent)
        quiet_out.warn("hidden")
        assert quiet_err.getvalue() == ""
        assert quiet_out.warnings == ["hidden"]


def test_rainbow_helpers_are_silent_in_quiet_and_json_modes() -> None:
    for silent in ({"quiet": True}, {"json_output": True}):
        out, out_buf, _ = _ctx(**silent)
        out.rainbow_header("Hidden")
        out.rainbow_rule()
        assert out_buf.getvalue() == ""


def test_rainbow_helpers_plain_when_color_is_off() -> None:
    out, out_buf, _ = _ctx()
    out.rainbow_header("Plain Title", persona="sakthai")
    assert "Plain Title" in out_buf.getvalue()
    out.rainbow_rule(width=5)
    assert "─" * 5 + "\n" in out_buf.getvalue()
    out.rainbow_rule(width=0)
    assert out_buf.getvalue().endswith("─\n")
    assert out.rainbow_text("plain") == "plain"


def test_rainbow_helpers_style_when_color_is_on(monkeypatch: pytest.MonkeyPatch) -> None:
    out, out_buf, _ = _color_ctx(monkeypatch)
    out.rainbow_header("Vivid Title", persona="not-a-persona")
    assert "\x1b[" in out_buf.getvalue()
    assert "Vivid Title" in re.sub(r"\x1b\[[0-9;]*m", "", out_buf.getvalue())
    before = len(out_buf.getvalue())
    out.rainbow_rule(width=12)
    assert len(out_buf.getvalue()) > before
    styled = out.rainbow_text("gradient")
    assert getattr(styled, "plain", None) == "gradient"


def test_output_options_wrapper_outside_a_click_context_builds_a_context() -> None:
    wrapped = output_options(lambda out: out)
    assert isinstance(wrapped(), OutputContext)


def _command(raiser: Any) -> click.Command:
    @click.command()
    @output_options
    def cmd(out: OutputContext) -> None:
        raiser()

    return cmd


def _raise(exc: BaseException) -> Any:
    def raiser() -> None:
        raise exc

    return raiser


@pytest.mark.parametrize("interrupt", [KeyboardInterrupt(), click.Abort()])
def test_output_options_maps_interrupts_to_exit_130(interrupt: BaseException) -> None:
    result = CliRunner().invoke(_command(_raise(interrupt)), [])
    assert result.exit_code == EXIT_INTERRUPTED
    assert "INTERRUPTED" in result.output


def test_output_options_wraps_unexpected_errors_in_json_mode() -> None:
    result = CliRunner().invoke(_command(_raise(RuntimeError("boom"))), ["--json"])
    assert result.exit_code == EXIT_ERROR
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "INTERNAL_ERROR"
    assert payload["error"]["type"] == "RuntimeError"
    assert payload["error"]["message"] == "boom"


def test_output_options_reraises_unexpected_errors_without_json() -> None:
    result = CliRunner().invoke(_command(_raise(RuntimeError("boom"))), [])
    assert isinstance(result.exception, RuntimeError)
    assert result.exit_code == EXIT_ERROR


def test_output_options_passes_through_system_exit_and_click_exceptions() -> None:
    exit_result = CliRunner().invoke(_command(_raise(SystemExit(7))), [])
    assert exit_result.exit_code == 7

    click_result = CliRunner().invoke(_command(_raise(click.ClickException("nope"))), [])
    assert click_result.exit_code == 1
    assert "nope" in click_result.output


@pytest.mark.parametrize("command", ["doctor", "status"])
def test_quiet_unready_exits_not_ready_with_an_error(
    command: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = {"ready": False}
    monkeypatch.setattr(system_mod, "check_env", lambda: env)
    result = CliRunner().invoke(main, [command, "-q"])
    assert result.exit_code == EXIT_NOT_READY
    assert "NOT_READY" in result.output


def test_registry_cache_failure_is_reported_not_raised(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def broken() -> Any:
        raise RuntimeError("cache unreadable")

    monkeypatch.setattr("sakthai.mcp.registry.read_cache", broken)
    system_mod._report_mcp_supply_chain()
    assert "could not check the registry cache: cache unreadable" in capsys.readouterr().out


def test_registry_report_confirms_servers_that_are_all_active(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sakthai.mcp.registry.read_cache", lambda: {"srv": object()})
    monkeypatch.setattr("sakthai.mcp.registry.check_configured_servers", lambda *a, **k: [])
    monkeypatch.setattr("sakthai.mcp.load_server_specs", lambda: [SimpleNamespace(name="srv")])
    system_mod._report_mcp_supply_chain()
    assert "all 1 configured server(s) active upstream" in capsys.readouterr().out


def test_web_serve_closes_the_server_after_ctrl_c(monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[bool] = []

    class FakeServer:
        def serve_forever(self) -> None:
            raise KeyboardInterrupt

        def server_close(self) -> None:
            closed.append(True)

    monkeypatch.setattr("sakthai.web.server.serve", lambda host, port: FakeServer())
    result = CliRunner().invoke(main, ["web", "serve", "--port", "0"])
    assert result.exit_code == 0
    assert "Stopped." in result.output
    assert closed == [True]


def test_sys_argv_debug_flag_enables_the_traceback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["sakthai", "doctor", "--debug"])
    out, _, err_buf = _ctx()
    try:
        raise ValueError("flagged")
    except ValueError as exc:
        with pytest.raises(SystemExit):
            out.error("flagged", exc=exc)
    assert "ValueError: flagged" in err_buf.getvalue()
