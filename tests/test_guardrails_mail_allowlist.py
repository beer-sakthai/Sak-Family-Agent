"""SAKTHAI_MAIL_ALLOW: send_outlook_mail may only mail allow-listed recipients.

Regression for the prompt-injection exfiltration path: the recipient comes from
the model, and the guardrail used to allow any address.
"""

from __future__ import annotations

import pytest

from sakthai.agent.guardrails import DEFAULT_POLICY, GuardrailAction
from sakthai.agent.tools import tool_by_name
from sakthai.config import mail_allowlist
from sakthai.memory.store import MemoryStore


def _check(to: object) -> GuardrailAction:
    tool = tool_by_name("send_outlook_mail")
    assert tool is not None
    args = {"to": to, "subject": "s", "body": "b"}
    return DEFAULT_POLICY.check_pre_execution(tool, args, MemoryStore(":memory:")).action


def test_unset_allowlist_denies_every_recipient(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_MAIL_ALLOW", raising=False)
    assert _check("attacker@evil.test") == GuardrailAction.DENY
    assert _check("beer@example.com") == GuardrailAction.DENY


def test_denial_reason_names_the_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_MAIL_ALLOW", raising=False)
    tool = tool_by_name("send_outlook_mail")
    assert tool is not None
    result = DEFAULT_POLICY.check_pre_execution(
        tool, {"to": "x@y.test", "subject": "s", "body": "b"}, MemoryStore(":memory:")
    )
    assert result.reason is not None and "SAKTHAI_MAIL_ALLOW" in result.reason


@pytest.mark.parametrize(
    ("allow", "to", "expected"),
    [
        ("beer@example.com", "beer@example.com", GuardrailAction.ALLOW),
        ("beer@example.com", "  BEER@Example.com ", GuardrailAction.ALLOW),
        ("beer@example.com", "other@example.com", GuardrailAction.DENY),
        ("@example.com", "anyone@example.com", GuardrailAction.ALLOW),
        ("@example.com", "x@example.com.evil.test", GuardrailAction.DENY),
        ("@example.com", "x@sub.example.com", GuardrailAction.DENY),
        ("@example.com", "x@notexample.com", GuardrailAction.DENY),
        ("a@x.test, @example.com", "a@x.test", GuardrailAction.ALLOW),
        ("a@x.test", "a@x.test,attacker@evil.test", GuardrailAction.DENY),
        ("a@x.test", "Beer <attacker@evil.test>", GuardrailAction.DENY),
        # The domain used to be read off the last '@', so an allowed address
        # placed after the attacker's slipped a multi-recipient string through.
        ("@example.com", "attacker@evil.test,me@example.com", GuardrailAction.DENY),
        ("@example.com", "attacker@evil.test;me@example.com", GuardrailAction.DENY),
        ("@example.com", "attacker@evil.test me@example.com", GuardrailAction.DENY),
        ("@example.com", "Me <me@example.com>", GuardrailAction.DENY),
        ("@example.com", "attacker@evil.test@example.com", GuardrailAction.DENY),
        ("@example.com", "example.com", GuardrailAction.DENY),
    ],
)
def test_allowlist_matching(
    monkeypatch: pytest.MonkeyPatch, allow: str, to: str, expected: GuardrailAction
) -> None:
    monkeypatch.setenv("SAKTHAI_MAIL_ALLOW", allow)
    assert _check(to) == expected


def test_missing_recipient_is_left_to_the_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_MAIL_ALLOW", raising=False)
    assert _check("") == GuardrailAction.ALLOW
    assert _check(None) == GuardrailAction.ALLOW


def test_other_tools_are_unaffected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_MAIL_ALLOW", raising=False)
    tool = tool_by_name("recall")
    assert tool is not None
    result = DEFAULT_POLICY.check_pre_execution(tool, {"to": "x@y.test"}, MemoryStore(":memory:"))
    assert result.action == GuardrailAction.ALLOW


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", []),
        ("   ", []),
        ("A@X.test", ["a@x.test"]),
        ("a@x.test,@y.test", ["a@x.test", "@y.test"]),
        ("a@x.test, @y.test  b@z.test", ["a@x.test", "@y.test", "b@z.test"]),
    ],
)
def test_mail_allowlist_parsing(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: list[str]
) -> None:
    monkeypatch.setenv("SAKTHAI_MAIL_ALLOW", raw)
    assert mail_allowlist() == expected
