
import sys
import os

# Add the package path to sys.path
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

from sakthai.agent.guardrails import _check_destructive_tokens, GuardrailAction

def test_command(cmd):
    parts = cmd.split()
    result = _check_destructive_tokens(parts)
    print(f"Command: {cmd}")
    print(f"Action: {result.action}")
    if result.reason:
        print(f"Reason: {result.reason}")
    print("-" * 20)

commands = [
    "docker run -v /etc:/mnt alpine rm -rf /mnt",
    "podman run --mount src=/etc,target=/mnt alpine ls /mnt",
    "kubectl --namespace=prod cp /etc/shadow my-pod:/tmp/shadow",
    "docker cp my-container:/etc/shadow /etc/shadow",
    "podman cp /etc/shadow my-container:/tmp/shadow",
    "nsenter -t 1 -m rm -rf /",
    "nsenter --target 1 --mount -- ls /",
    "chroot /host /bin/bash",
    "tar -czf backup.tar.gz /etc",
    "zip -r backup.zip .",
    "kubectl get pods",
]

for cmd in commands:
    test_command(cmd)
