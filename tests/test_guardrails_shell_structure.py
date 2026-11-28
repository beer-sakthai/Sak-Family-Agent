"""Shell structure and free-text regressions for ``agent/guardrails.py``.

``shlex.split`` treats ``;``, ``&`` and ``|`` as operators only when whitespace
surrounds them, and leaves ``$(...)``/backtick bodies inside a single token. The
token checks therefore never saw the real command in ``echo hi;cat ~/.ssh/id_rsa``
or ``echo "$(cat /etc/shadow)"``. Separately, ``".." in path`` and a bare leading
``~`` denied ordinary text such as ``"Hmm... ok"``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai.agent.guardrails import (
    DEFAULT_POLICY,
    GuardrailAction,
    _check_command_string,
    _has_traversal_or_home,
    _scan_shell_structure,
)
from sakthai.agent.tools import Tool
from sakthai.memory.store import MemoryStore


def _tool(name: str) -> Tool:
    return Tool(name, "desc", {}, lambda _a, _s: "")


def _shell(command: str) -> GuardrailAction:
    result = DEFAULT_POLICY.check_pre_execution(
        _tool("run_command"), {"command": command}, MemoryStore(":memory:")
    )
    return result.action


def _arg(value: str) -> GuardrailAction:
    result = DEFAULT_POLICY.check_pre_execution(
        _tool("learn"), {"value": value}, MemoryStore(":memory:")
    )
    return result.action


@pytest.fixture(autouse=True)
def _shell_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")


# --- glued separators --------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "echo hi;cat ~/.ssh/id_rsa",
        "true&&cat /etc/shadow",
        "false||cat /etc/shadow",
        "echo x|cat /etc/shadow",
        "echo x|&cat /etc/shadow",
        "sleep 1&cat /etc/shadow",
        "ls;rm -rf /etc/foo",
        "echo hi\ncat /etc/shadow",
        "(cat /etc/shadow)",
        "cat <(cat /etc/shadow)",
    ],
)
def test_glued_separators_do_not_hide_the_second_command(command: str) -> None:
    assert _shell(command) == GuardrailAction.DENY


def test_quoted_separator_does_not_end_the_scan() -> None:
    # A literal ';' token used to stop the argument scan, hiding what followed.
    assert _shell('grep ";" ~/.ssh/id_rsa') == GuardrailAction.DENY


@pytest.mark.parametrize(
    "command",
    [
        'bash -c "echo hi;cat /etc/shadow"',
        'eval "echo hi;cat /etc/shadow"',
        'sh -c "true&&cat ~/.ssh/id_rsa"',
    ],
)
def test_nested_command_strings_are_split_too(command: str) -> None:
    assert _shell(command) == GuardrailAction.DENY


def test_makefile_recipe_with_glued_separator_is_scanned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "Makefile").write_text("all:\n\techo hi;cat /etc/shadow\n")
    monkeypatch.chdir(tmp_path)
    assert _shell("make") == GuardrailAction.DENY


# --- command substitution ----------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "echo $(cat ~/.ssh/id_rsa)",
        'echo "$(cat ~/.ssh/id_rsa)"',
        "echo `cat /etc/shadow`",
        'echo "`cat /etc/shadow`"',
        "echo $(echo $(cat /etc/shadow))",
        "echo $(cat /etc/shadow",  # unterminated: the remainder is still scanned
        "echo `cat /etc/shadow",
        "echo `echo \\`cat /etc/shadow\\``",
        "echo $((1+$(cat /etc/shadow)))",
    ],
)
def test_substitution_bodies_are_scanned(command: str) -> None:
    assert _shell(command) == GuardrailAction.DENY


# --- what must still be allowed ---------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "ls",
        "echo hello; echo world",
        "git status && git diff | head",
        "echo 'a;b' | wc -l",
        "echo '$(cat /etc/shadow)'",  # single quotes: never executed
        "echo a\\;cat /etc/shadow",  # escaped: literal text
        'echo "cost: $(date)"',
        "echo $((1+2))",
        "cat notes.txt > out.txt 2>&1",
        "sleep 1 &",
        "find . -name '*.py' -exec echo {} \\;",
    ],
)
def test_ordinary_commands_are_still_allowed(command: str) -> None:
    assert _shell(command) == GuardrailAction.ALLOW


@pytest.mark.parametrize(
    "command",
    [
        "echo x >&/etc/passwd",
        "echo x &>/etc/passwd",
        "echo x >|/etc/passwd",
        "echo x 2>/etc/passwd",
    ],
)
def test_fused_redirection_operators_are_not_split(command: str) -> None:
    # '&' and '|' glued to '<'/'>' are redirections; splitting there would
    # orphan the target from its operator.
    assert _shell(command) == GuardrailAction.DENY


def test_malformed_quoting_is_denied() -> None:
    assert _shell("echo 'unterminated") == GuardrailAction.DENY
    assert _check_command_string("echo 'x", posix=False).action == GuardrailAction.DENY


def test_windows_backslash_path_is_still_rescanned() -> None:
    assert _shell("cat C:\\Users\\me\\.aws\\credentials") == GuardrailAction.DENY


# --- scanner unit behavior ---------------------------------------------------


def test_scanner_splits_and_lifts_substitutions() -> None:
    segments, subs = _scan_shell_structure("a;b && c|d $(x y) `z`")
    assert segments == ["a", "b", "c", "d SUBST SUBST"]
    assert subs == ["x y", "z"]


def test_scanner_keeps_quotes_and_escapes_inside_a_segment() -> None:
    segments, subs = _scan_shell_structure("echo 'a;b' \"c|d\" e\\;f")
    assert segments == ["echo 'a;b' \"c|d\" e\\;f"]
    assert subs == []


def test_scanner_ignores_empty_segments() -> None:
    assert _scan_shell_structure(";; &&  ") == ([], [])


# --- free text vs. traversal -------------------------------------------------


@pytest.mark.parametrize(
    "value",
    ["Hmm... interesting", "wait... what?", "to be continued...", "~approximately 5", "10:30"],
)
def test_ordinary_text_is_not_mistaken_for_a_path(value: str) -> None:
    assert _arg(value) == GuardrailAction.ALLOW


@pytest.mark.parametrize(
    "value",
    [
        "..",
        "../notes",
        "a/../b",
        "a/..",
        "..\\x",
        "cat ../../etc/passwd",
        "-o../foo",
        "-C..",
        "--out=../x",  # split on '=' by _is_sensitive_path itself
        "~",
        "~/x",
        "~root/.ssh",
        "~\\x",
    ],
)
def test_real_traversal_and_home_paths_are_still_blocked(value: str) -> None:
    assert _arg(value) == GuardrailAction.DENY


@pytest.mark.parametrize(
    "value", ["..", "../x", "a/..", "-o../foo", "-C..", "~", "~/x", "~root/x", "~+/x"]
)
def test_has_traversal_or_home_detects(value: str) -> None:
    assert _has_traversal_or_home(value) is True


@pytest.mark.parametrize("value", ["...", "a..b", "x...", "~approximately 5", "--flag..", "ok"])
def test_has_traversal_or_home_ignores_dotted_names_and_prose(value: str) -> None:
    assert _has_traversal_or_home(value) is False
