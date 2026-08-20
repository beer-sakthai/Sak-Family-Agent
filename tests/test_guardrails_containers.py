"""Container-escape guardrail tests, with rule attribution.

Why this file asserts on ``result.reason`` and not just ``result.action``
------------------------------------------------------------------------

``_block_dangerous_shell_commands`` applies numbered rules in order (see
``personas/sakthai/sakthai/agent/guardrails.py``). Several of them overlap: a
``docker run -v /etc:/mnt`` is caught by rule 2 (generic "destructive binary
touching a sensitive path") *before* rule 6 (container-specific volume-mount
parsing) is ever reached.

The previous version of this file asserted only ``action == DENY`` and
``"blocked" in reason``. Every case passed — via rule 2 — while rule 6's
volume-mount, ``--mount source=``/``src=`` and ``docker cp`` parsing at
``guardrails.py:860-912`` never executed once. Coverage confirmed it: those
lines sit in the miss list. The suite was green and told us nothing about the
defense it was named after.

The same trap caught two more cases: ``unshare -r cat /etc/shadow`` and
``pkexec --user root cat /etc/shadow`` are denied because of the inner ``cat``,
not by any unshare/pkexec handling. If that handling regressed, an
action-only assertion would stay green.

So: every case below pins the exact rule that denies it. If a defense stops
firing and a broader one silently takes over, these fail.
"""

from __future__ import annotations

import pytest

from sakthai.agent.guardrails import DEFAULT_POLICY, GuardrailAction
from sakthai.agent.tools import Tool
from sakthai.memory.store import MemoryStore


@pytest.fixture
def store():
    return MemoryStore(":memory:")


@pytest.fixture
def run_command_tool():
    return Tool("run_command", "desc", {}, lambda _a, _s: "")


@pytest.fixture
def deny_reason(run_command_tool, store, monkeypatch):
    """Return a callable giving the guardrail's reason for a shell command."""
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")

    def _reason(command: str) -> str:
        result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
        assert result.action == GuardrailAction.DENY, f"{command!r} was not blocked"
        return result.reason

    return _reason


# ---------------------------------------------------------------------------
# Rule 2 — generic "destructive binary on a sensitive path"
# ---------------------------------------------------------------------------
# These are the cases the container battery *actually* exercises today. The
# expected fragment names the binary and the offending argument, so a change in
# which token trips the rule shows up as a failure rather than a silent pass.

RULE_2_CASES = [
    ("docker run -v /etc:/mnt alpine", "'docker' command on '/etc:/mnt'"),
    ("podman run --volume /root:/root alpine", "'podman' command on '/root:/root'"),
    (
        "docker run --mount type=bind,source=/etc,target=/etc alpine",
        "'docker' command on 'type=bind,source=/etc,target=/etc'",
    ),
    ("podman run --mount src=/var,dst=/var alpine", "'podman' command on 'src=/var,dst=/var'"),
    ("kubectl cp /etc/shadow pod:/tmp/shadow", "'kubectl' command on '/etc/shadow'"),
    ("kubectl cp pod:/tmp/shadow /etc/shadow", "'kubectl' command on 'pod:/tmp/shadow'"),
    ("docker cp /etc/shadow ctr:/tmp/x", "'docker' command on '/etc/shadow'"),
    ("podman cp /root/.ssh/id_rsa ctr:/tmp/k", "'podman' command on '/root/.ssh/id_rsa'"),
    ("nsenter -t 1 -m cat /etc/shadow", "'nsenter' command on '/etc/shadow'"),
    ("chroot /etc", "'chroot' command on '/etc'"),
    ("chroot /mnt cat /etc/shadow", "'chroot' command on '/etc/shadow'"),
    ("sudo nsenter -t 1 -u cat /root/.ssh/id_rsa", "'nsenter' command on '/root/.ssh/id_rsa'"),
    ("docker run -v=/etc:/etc alpine", "'docker' command on '-v=/etc:/etc'"),
    ("podman run --volume=/var:/var alpine", "'podman' command on '--volume=/var:/var'"),
]


@pytest.mark.parametrize(("command", "expected"), RULE_2_CASES, ids=[c for c, _ in RULE_2_CASES])
def test_denied_by_generic_destructive_path_rule(command, expected, deny_reason):
    reason = deny_reason(command)
    assert expected in reason, f"expected rule 2 attribution {expected!r}, got {reason!r}"
    assert reason.startswith("Potentially destructive"), reason


# ---------------------------------------------------------------------------
# unshare — its own dedicated flag handling (rule 7 wrapper logic)
# ---------------------------------------------------------------------------

UNSHARE_CASES = [
    ("unshare --root /etc /bin/sh", "'unshare --root' on '/etc'"),
    ("unshare --root=/etc /bin/sh", "'unshare --root' on '/etc'"),
    ("unshare --wd /root /bin/sh", "'unshare --wd' on '/root'"),
    ("unshare --mount-proc /etc /bin/sh", "'unshare --mount-proc' on '/etc'"),
]


@pytest.mark.parametrize(("command", "expected"), UNSHARE_CASES, ids=[c for c, _ in UNSHARE_CASES])
def test_unshare_flag_handling_is_the_rule_that_fires(command, expected, deny_reason):
    """These four genuinely exercise unshare's own flag parsing."""
    reason = deny_reason(command)
    assert expected in reason, f"expected unshare attribution {expected!r}, got {reason!r}"


# ---------------------------------------------------------------------------
# Cases blocked only incidentally, by the *inner* command
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "unshare -r cat /etc/shadow",
        "pkexec --user root cat /etc/shadow",
    ],
)
def test_blocked_by_inner_command_not_by_wrapper(command, deny_reason):
    """Documents that the wrapper itself is not what denies these.

    ``unshare -r`` and ``pkexec --user root`` are both denied because the inner
    ``cat /etc/shadow`` trips rule 2 — the privilege-escalation wrapper plays no
    part. Pinning that here means a regression in wrapper handling cannot hide
    behind the inner command's protection: if someone hardens ``unshare -r``
    specifically, this test fails and gets updated deliberately.
    """
    reason = deny_reason(command)
    assert "'cat' command on '/etc/shadow'" in reason, reason


# ---------------------------------------------------------------------------
# Characterization: rule 6 is currently unreachable
# ---------------------------------------------------------------------------

# Rule 6's three distinct messages. None of them can currently be produced,
# because rule 2 lists docker/podman/kubectl as destructive binaries and runs
# first.
RULE_6_MARKERS = (
    "volume mount targeting",
    "mount source",
    "cp' on",
)


@pytest.mark.parametrize(
    "command",
    [command for command, _ in RULE_2_CASES]
    + [
        "docker run --mount type=bind,src=/etc/passwd,target=/x alpine",
        "kubectl cp /root/.ssh/id_rsa pod:/tmp/k",
    ],
)
def test_container_specific_rule_6_is_shadowed_by_rule_2(command, deny_reason):
    """Characterization test for dead code in ``guardrails.py:860-912``.

    Rule 6 parses docker/podman/kubectl volume mounts and ``cp`` arguments, but
    rule 2 already denies every input that would reach it. The block is
    therefore unreachable, which is why its lines never appear in coverage.

    This is not an assertion that the situation is *desirable* — it pins the
    current behavior so the shadowing cannot be forgotten. If rule ordering
    changes, or docker/podman/kubectl are removed from rule 2's binary list on
    the assumption that rule 6 covers them, this test fails and forces the
    question to be answered explicitly. Deleting rule 6 as dead code is the
    other legitimate resolution.
    """
    reason = deny_reason(command)
    fired = [marker for marker in RULE_6_MARKERS if marker in reason]
    assert not fired, (
        f"rule 6 is no longer shadowed for {command!r} (reason: {reason!r}). "
        "Rule 6 was unreachable when this test was written; if it is now live, "
        "remove this characterization test and assert its behavior directly."
    )


# ---------------------------------------------------------------------------
# False positives — ordinary container work must stay allowed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "docker ps",
        "podman images",
        "kubectl get pods",
        "docker run -v ./local:/data alpine",
        "docker build -t myapp .",
        "docker compose up -d",
        "kubectl logs my-pod",
        "kubectl apply -f ./deploy/manifest.yaml",
        "nsenter --help",
        "chroot . ls",
        "unshare -r ls",
        "pkexec --user root ls",
    ],
)
def test_safe_container_commands_are_allowed(command, run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.ALLOW, (
        f"{command!r} is ordinary container work and must not be blocked "
        f"(reason given: {result.reason!r})"
    )
