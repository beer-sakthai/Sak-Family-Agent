"""Direct tests for guardrails rule 6 — the container host-escape checks.

``tests/test_guardrails_containers.py`` covers container commands as they
actually flow through :func:`_check_destructive_tokens`, and documents that
rule 2 (the generic destructive-binary path scan) reaches every such command
first, so rule 6 never fires in production. That characterization is correct and
is left alone.

The consequence it records, though, is that rule 6's own parsing — volume-mount
extraction, ``--mount source=``/``src=`` splitting, ``cp`` argument scanning —
was **unverified**. Nothing could reach it, so nothing tested it. That is the
worst state for security code to be in: it is not protecting anything today, and
on the day it becomes load-bearing (docker/podman/kubectl leaving rule 2's binary
list, a reordering of the rules, a new container binary added to rule 6 only) it
would take over untested.

Rule 6 is now the extracted :func:`sakthai.agent.guardrails._check_container_tokens`,
so it can be called directly. This module tests it as a unit: the backstop is
verified before it is needed. Every test pins ``result.reason``, not just
``result.action`` — per CLAUDE.md, an action-only assertion is exactly how the
container battery stayed green while testing nothing.
"""

import shlex
import unittest

from sakthai.agent.guardrails import (
    GuardrailAction,
    _check_container_tokens,
    _check_destructive_tokens,
)


def _check(command: str):
    return _check_container_tokens(shlex.split(command))


class TestVolumeMountSeparateArg(unittest.TestCase):
    """``-v /etc:/mnt`` / ``--volume /etc:/mnt`` — value in the next token."""

    def test_docker_v_flag_blocks_sensitive_source(self):
        result = _check("docker run -v /etc:/mnt alpine")
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertEqual(
            result.reason,
            "potentially dangerous 'docker' volume mount targeting '/etc:/mnt' blocked.",
        )

    def test_podman_long_volume_flag_blocks_sensitive_source(self):
        result = _check("podman run --volume /root/.ssh:/keys alpine")
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertEqual(
            result.reason,
            "potentially dangerous 'podman' volume mount targeting '/root/.ssh:/keys' blocked.",
        )

    def test_binary_name_is_basename_not_full_path(self):
        """An absolute binary path must still attribute to the bare name."""
        result = _check("/usr/bin/docker run -v /etc:/mnt alpine")
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertIn("'docker' volume mount", result.reason)

    def test_dangling_v_flag_at_end_does_not_crash(self):
        """``-v`` as the final token has no value to read — must not IndexError."""
        result = _check("docker run -v")
        self.assertEqual(result.action, GuardrailAction.ALLOW)


class TestVolumeMountJoinedArg(unittest.TestCase):
    """``-v=/etc:/mnt`` / ``--volume=/etc:/mnt`` — value joined with ``=``."""

    def test_short_joined_form_blocks(self):
        result = _check("docker run -v=/etc:/mnt alpine")
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertEqual(
            result.reason,
            "potentially dangerous 'docker' volume mount targeting '/etc:/mnt' blocked.",
        )

    def test_long_joined_form_blocks(self):
        result = _check("podman run --volume=/var:/var alpine")
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertEqual(
            result.reason,
            "potentially dangerous 'podman' volume mount targeting '/var:/var' blocked.",
        )


class TestBindMountSourceExtraction(unittest.TestCase):
    """``--mount type=bind,source=/etc,target=/mnt`` — source must be extracted."""

    def test_source_key_is_extracted_and_blocked(self):
        result = _check("docker run --mount type=bind,source=/etc,target=/mnt alpine")
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertEqual(
            result.reason,
            "potentially dangerous 'docker' mount source '/etc' blocked.",
        )

    def test_src_alias_is_extracted_and_blocked(self):
        result = _check("podman run --mount type=bind,src=/root,dst=/root alpine")
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertEqual(
            result.reason,
            "potentially dangerous 'podman' mount source '/root' blocked.",
        )

    def test_mount_value_in_following_token(self):
        """``--mount`` with no ``=`` takes its value from the next token."""
        result = _check("docker run --mount type=bind,source=/etc,target=/mnt alpine")
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertIn("mount source '/etc'", result.reason)

    def test_source_extraction_stops_at_comma(self):
        """The source value must not swallow the trailing ``,target=...``."""
        result = _check("docker run --mount type=bind,source=/etc,target=/safe alpine")
        self.assertIn("'/etc'", result.reason)
        self.assertNotIn("target", result.reason)

    def test_benign_bind_mount_is_allowed(self):
        result = _check("docker run --mount type=bind,source=./data,target=/data alpine")
        self.assertEqual(result.action, GuardrailAction.ALLOW)


class TestContainerCopy(unittest.TestCase):
    """``docker|podman|kubectl cp`` moves files across the host boundary."""

    def test_cp_out_of_host_is_blocked(self):
        result = _check("docker cp /etc/shadow ctr:/tmp/x")
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertEqual(
            result.reason,
            "potentially dangerous 'docker cp' on '/etc/shadow' blocked.",
        )

    def test_cp_into_host_is_blocked(self):
        """The sensitive path as *destination* is equally dangerous.

        The container-side source is deliberately ``pod:/srv/app`` rather than
        something under ``/tmp``: ``/tmp`` is itself a sensitive root, so a
        ``pod:/tmp/...`` source matches first and would attribute the denial to
        the source, hiding whether the destination is checked at all.
        """
        result = _check("kubectl cp pod:/srv/app /etc/passwd")
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertEqual(
            result.reason,
            "potentially dangerous 'kubectl cp' on '/etc/passwd' blocked.",
        )

    def test_first_sensitive_argument_wins_attribution(self):
        """Attribution is left-to-right: the container-side ref can match too.

        ``pod:/tmp/x`` is sensitive on its own (``/tmp``), so it — not the host
        path after it — is what the reason names. Pinned so the scan order is a
        stated property rather than an accident.
        """
        result = _check("kubectl cp pod:/tmp/x /etc/passwd")
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertEqual(
            result.reason,
            "potentially dangerous 'kubectl cp' on 'pod:/tmp/x' blocked.",
        )

    def test_podman_cp_private_key_is_blocked(self):
        result = _check("podman cp /root/.ssh/id_rsa ctr:/tmp/k")
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertIn("'podman cp' on '/root/.ssh/id_rsa'", result.reason)

    def test_benign_cp_is_allowed(self):
        result = _check("docker cp ./build ctr:/app")
        self.assertEqual(result.action, GuardrailAction.ALLOW)


class TestScanBoundaries(unittest.TestCase):
    """The scan must stop at shell operators, not run past them."""

    def test_scan_stops_at_command_separator(self):
        """A sensitive path in a *following* command is not this binary's arg.

        ``docker ps ; cat /etc/shadow`` — the ``/etc/shadow`` belongs to ``cat``.
        Rule 6 must not attribute it to docker; other rules handle ``cat``.
        """
        result = _check("docker ps ; cat /etc/shadow")
        self.assertEqual(result.action, GuardrailAction.ALLOW)

    def test_cp_scan_stops_at_pipe(self):
        result = _check("docker cp ./a ctr:/b | cat /etc/shadow")
        self.assertEqual(result.action, GuardrailAction.ALLOW)

    def test_no_container_binary_is_allowed(self):
        result = _check("ls -la /etc")
        self.assertEqual(result.action, GuardrailAction.ALLOW)

    def test_empty_token_list_is_allowed(self):
        self.assertEqual(_check_container_tokens([]).action, GuardrailAction.ALLOW)


class TestSafeContainerUsageStillAllowed(unittest.TestCase):
    """Rule 6 must not break ordinary container workflows."""

    SAFE = (
        "docker ps",
        "podman images",
        "kubectl get pods",
        "docker run -v ./local:/data alpine",
        "docker run --volume=./cache:/cache alpine",
        "docker build -t myapp .",
        "docker compose up -d",
        "kubectl logs my-pod",
        "kubectl apply -f ./deploy/manifest.yaml",
        "docker cp ./dist ctr:/srv",
    )

    def test_safe_commands_are_allowed(self):
        for command in self.SAFE:
            with self.subTest(command=command):
                result = _check(command)
                self.assertEqual(
                    result.action,
                    GuardrailAction.ALLOW,
                    f"{command!r} was blocked by rule 6: {result.reason}",
                )


class TestExtractionPreservedBehavior(unittest.TestCase):
    """Rule 6 was extracted from ``_check_destructive_tokens``; nothing changed.

    The full pipeline must still deny every container escape (via rule 2, which
    shadows rule 6) and still allow every benign container command. This is the
    regression guard on the refactor itself.
    """

    ESCAPES = (
        "docker run -v /etc:/mnt alpine",
        "docker run -v=/etc:/mnt alpine",
        "podman run --volume /root:/root alpine",
        "podman run --volume=/var:/var alpine",
        "docker run --mount type=bind,source=/etc,target=/etc alpine",
        "podman run --mount src=/var,dst=/var alpine",
        "docker cp /etc/shadow ctr:/tmp/x",
        "kubectl cp /root/.ssh/id_rsa pod:/tmp/k",
    )

    def test_pipeline_still_denies_every_escape(self):
        for command in self.ESCAPES:
            with self.subTest(command=command):
                result = _check_destructive_tokens(shlex.split(command))
                self.assertEqual(
                    result.action,
                    GuardrailAction.DENY,
                    f"{command!r} is no longer blocked by the full rule chain",
                )

    def test_pipeline_still_allows_safe_container_commands(self):
        for command in TestSafeContainerUsageStillAllowed.SAFE:
            with self.subTest(command=command):
                result = _check_destructive_tokens(shlex.split(command))
                self.assertEqual(
                    result.action,
                    GuardrailAction.ALLOW,
                    f"{command!r} became blocked: {result.reason}",
                )


if __name__ == "__main__":
    unittest.main()
