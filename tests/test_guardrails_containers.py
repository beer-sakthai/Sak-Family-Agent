from __future__ import annotations

import sys
from pathlib import Path

# Add the persona path to sys.path before other imports
repo_root = Path(__file__).resolve().parent.parent
persona_path = repo_root / "personas" / "sakthai"
sys.path.append(str(persona_path))

import pytest  # noqa: E402

from sakthai.agent.guardrails import DEFAULT_POLICY, GuardrailAction  # noqa: E402
from sakthai.agent.tools import Tool  # noqa: E402
from sakthai.memory.store import MemoryStore  # noqa: E402


@pytest.fixture
def store():
    return MemoryStore(":memory:")


@pytest.fixture
def run_command_tool():
    return Tool("run_command", "desc", {}, lambda _a, _s: "")


@pytest.mark.parametrize(
    "command",
    [
        "docker run -v /etc:/mnt alpine",
        "podman run --volume /root:/root alpine",
        "docker run --mount type=bind,source=/etc,target=/etc alpine",
        "podman run --mount src=/var,dst=/var alpine",
        "kubectl cp /etc/shadow pod:/tmp/shadow",
        "kubectl cp pod:/tmp/shadow /etc/shadow",
        "nsenter -t 1 -m cat /etc/shadow",
        "chroot /etc",
        "chroot /mnt cat /etc/shadow",
        "sudo nsenter -t 1 -u cat /root/.ssh/id_rsa",
        "docker run -v=/etc:/etc alpine",
        "podman run --volume=/var:/var alpine",
    ],
)
def test_container_guardrails(command, run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert "blocked" in result.reason.lower()


def test_safe_container_commands(run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    safe_commands = [
        "docker ps",
        "podman images",
        "kubectl get pods",
        "docker run -v ./local:/data alpine",
        "nsenter --help",
        "chroot . ls",
    ]
    for command in safe_commands:
        result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
        assert result.action == GuardrailAction.ALLOW
