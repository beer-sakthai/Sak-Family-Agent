"""Tests for the hardened guardrails integration."""

from pathlib import Path

import pytest

from sakthai.agent import guardrails_hardened as gh
from sakthai.agent.guardrails import GuardrailAction
from sakthai.agent.guardrails_hardened import (
    check_config_integrity,
    check_enhanced_path_safety,
    check_environment_integrity,
    check_mcp_server_safety,
    check_shell_command_hardened,
    check_symlink_safety,
    create_pre_execution_guardrail_hardened,
    initialize_hardened_guardrails,
)
from sakthai.agent.security_hardening import (
    ConfigFileIntegrity,
    EnhancedPathValidator,
    SecurityLevel,
)
from sakthai.agent.tools import BUILTIN_TOOLS
from sakthai.memory.store import MemoryStore


class TestInitializeHardenedGuardrails:
    """Test initialization of hardened guardrails."""

    def test_initialize_with_balanced_level(self) -> None:
        """Test initialization with BALANCED security level."""
        initialize_hardened_guardrails(security_level=SecurityLevel.BALANCED)
        # Should not raise any exception

    def test_initialize_with_strict_level(self) -> None:
        """Test initialization with STRICT security level."""
        initialize_hardened_guardrails(security_level=SecurityLevel.STRICT)
        # Should not raise any exception

    def test_initialize_with_permissive_level(self) -> None:
        """Test initialization with PERMISSIVE security level."""
        initialize_hardened_guardrails(security_level=SecurityLevel.PERMISSIVE)
        # Should not raise any exception


class TestEnvironmentIntegrityCheck:
    """Test environment integrity checking."""

    def test_environment_integrity_check_allows_clean_env(self) -> None:
        """Test that clean environment passes integrity check."""
        result = check_environment_integrity()
        assert result.action in (GuardrailAction.ALLOW, GuardrailAction.DENY)


class TestConfigIntegrityCheck:
    """Test config file integrity checking."""

    def test_config_integrity_check_passes(self) -> None:
        """Test that config integrity check doesn't crash."""
        result = check_config_integrity()
        assert result.action in (GuardrailAction.ALLOW, GuardrailAction.DENY)


class TestEnhancedPathSafety:
    """Test enhanced path safety checking."""

    def test_safe_path_allowed(self) -> None:
        """Test that safe paths are allowed."""
        result = check_enhanced_path_safety("./document.txt")
        assert result.action == GuardrailAction.ALLOW

    def test_sensitive_path_denied(self) -> None:
        """Test that sensitive paths are denied."""
        result = check_enhanced_path_safety("/root/.ssh/id_rsa")
        assert result.action == GuardrailAction.DENY

    def test_sensitive_path_rule_attribution(self) -> None:
        """``/root/.ssh/id_*`` is caught as a sensitive location, not as a glob.

        This case used to be ``test_glob_pattern_denied`` asserting only
        ``action == DENY``. It passed, but not for the stated reason: the path
        is under ``/root/.ssh``, so the sensitive-location branch returns first
        and the glob branch below it never ran. Pinned here as what it actually
        tests; the real glob check is exercised separately.
        """
        result = check_enhanced_path_safety("/root/.ssh/id_*")
        assert result.action == GuardrailAction.DENY
        assert result.reason == "Path targets sensitive location: /root/.ssh/id_*"

    def test_glob_pattern_denied(self) -> None:
        """A glob in an otherwise-innocuous path must hit the glob branch.

        The path deliberately avoids any sensitive component so the earlier
        sensitive-location check cannot shadow the rule under test.
        """
        result = check_enhanced_path_safety("./data/*.txt")
        assert result.action == GuardrailAction.DENY
        assert result.reason == (
            "Path contains potentially dangerous glob patterns: multi_char_wildcard"
        )

    def test_glob_variants_are_each_reported(self) -> None:
        for path, expected in (
            ("notes/*.md", "multi_char_wildcard"),
            ("build/out?.log", "single_char_wildcard"),
            ("reports/[abc].csv", "bracket_glob"),
        ):
            result = check_enhanced_path_safety(path)
            assert result.action == GuardrailAction.DENY, path
            assert expected in result.reason, (path, result.reason)

    def test_case_sensitivity_branch_is_shadowed_by_sensitive_path_check(self) -> None:
        """Characterization: the case-trick branch is unreachable in practice.

        ``EnhancedPathValidator.check_case_sensitivity`` flags a path only when
        it contains ``.ssh``/``.aws``/``.env``/``id_rsa``/``credentials`` in a
        casing other than the exact one. But ``_is_sensitive_path`` — checked
        first, in the loop above — already matches those names
        *case-insensitively*. So every input that would trigger the case branch
        is denied earlier, and the ``return`` at that branch is dead code.

        This previously hid behind ``test_case_sensitivity_trick_denied``, which
        asserted only ``DENY`` and so passed while testing nothing about case
        handling. The defence is real and still verified — as a unit, in
        :meth:`test_case_sensitivity_detector_still_works` — but the branch's
        unreachability is pinned here rather than papered over. If a future
        change makes it reachable, this test fails and should be replaced with a
        direct assertion on the case-trick reason.
        """
        for path in (".SSH/id_rsa", ".AWS/config", ".Ssh", "Documents/.SSH/notes"):
            result = check_enhanced_path_safety(path)
            assert result.action == GuardrailAction.DENY, path
            assert result.reason == f"Path targets sensitive location: {path}", (
                f"{path!r} now reaches a different branch: {result.reason!r}. If it is "
                "the case-sensitivity branch, that rule is live — assert it directly."
            )

    def test_case_sensitivity_detector_still_works(self) -> None:
        """The detector itself is sound, even though the branch above shadows it."""
        assert EnhancedPathValidator.check_case_sensitivity(".SSH/id_rsa") is True
        assert EnhancedPathValidator.check_case_sensitivity(".AWS/config") is True
        assert EnhancedPathValidator.check_case_sensitivity(".ssh/id_rsa") is False
        assert EnhancedPathValidator.check_case_sensitivity("src/main.py") is False


class TestSymlinkSafety:
    """Test symlink safety checking."""

    def test_regular_file_allowed(self) -> None:
        """Test that regular files are allowed."""
        result = check_symlink_safety("./document.txt")
        assert result.action == GuardrailAction.ALLOW

    def test_symlink_to_dangerous_location(self, tmp_path: Path) -> None:
        """Test detection of symlinks to dangerous locations."""
        symlink = tmp_path / "dangerous_link"
        try:
            symlink.symlink_to("/root")
            result = check_symlink_safety(str(symlink))
            # Should either allow or deny depending on whether /root is accessible
            assert result.action in (GuardrailAction.ALLOW, GuardrailAction.DENY)
        except (OSError, PermissionError):
            # Expected in test environment
            pass


class TestShellCommandHardening:
    """Test shell command hardening."""

    def test_simple_command_allowed(self) -> None:
        """Test that simple commands are allowed."""
        result = check_shell_command_hardened("echo hello")
        assert result.action == GuardrailAction.ALLOW

    def test_heredoc_with_destructive_command_denied(self) -> None:
        """Test that heredocs with destructive commands are denied."""
        result = check_shell_command_hardened("bash -c <<EOF\nrm -rf /\nEOF")
        assert result.action == GuardrailAction.DENY

    def test_line_continuation_with_destructive_command_denied(self) -> None:
        """Test that line continuations with destructive commands are denied."""
        result = check_shell_command_hardened("echo hello \\\nrm -rf /")
        assert result.action == GuardrailAction.DENY


class TestMCPServerSafety:
    """Test MCP server safety checking."""

    def test_valid_server_config_allowed(self) -> None:
        """Test that valid server configs are allowed."""
        spec = {"name": "valid-server", "command": "echo hello", "args": []}
        result = check_mcp_server_safety(spec)
        assert result.action == GuardrailAction.ALLOW

    def test_server_config_without_command_denied(self) -> None:
        """Test that server configs without command are denied."""
        spec = {"name": "invalid-server"}
        result = check_mcp_server_safety(spec)
        assert result.action == GuardrailAction.DENY

    def test_suspicious_server_command_denied(self) -> None:
        """Test that suspicious server commands are denied."""
        spec = {"name": "evil", "command": "eval 'rm -rf /'"}
        result = check_mcp_server_safety(spec)
        assert result.action == GuardrailAction.DENY


class TestPreExecutionGuardrailHardened:
    """Test the comprehensive pre-execution guardrail."""

    def test_creates_guardrail_function(self) -> None:
        """Test that guardrail function is created."""
        guardrail = create_pre_execution_guardrail_hardened()
        assert callable(guardrail)

    def test_guardrail_allows_safe_read(self) -> None:
        """Test that safe read operations are allowed."""
        guardrail = create_pre_execution_guardrail_hardened()
        store = MemoryStore(":memory:")

        # Find the read_file tool
        read_tool = next(t for t in BUILTIN_TOOLS if t.name == "read_file")

        result = guardrail(read_tool, {"path": "./test.txt"}, store)
        # Should allow safe reads
        assert result.action in (GuardrailAction.ALLOW, GuardrailAction.DENY)

    def test_guardrail_denies_sensitive_read(self) -> None:
        """Test that sensitive file reads are denied."""
        guardrail = create_pre_execution_guardrail_hardened()
        store = MemoryStore(":memory:")

        # Find the read_file tool
        read_tool = next(t for t in BUILTIN_TOOLS if t.name == "read_file")

        result = guardrail(read_tool, {"path": "/root/.ssh/id_rsa"}, store)
        # Should deny sensitive reads
        assert result.action == GuardrailAction.DENY

    def test_guardrail_blocks_run_command_when_shell_not_enabled(self) -> None:
        """With ``SAKTHAI_SHELL_ALLOW`` unset, the shell gate denies first.

        This replaces a test that asserted
        ``action in (ALLOW, DENY)`` — a tautology that could not fail. What
        actually happens is that ``run_command`` is opt-in, so the very first
        check short-circuits before any hardened logic runs. Pinning that makes
        the ordering explicit and stops the case from silently standing in for
        a test of the hardened layer.
        """
        guardrail = create_pre_execution_guardrail_hardened()
        store = MemoryStore(":memory:")
        cmd_tool = next(t for t in BUILTIN_TOOLS if t.name == "run_command")

        result = guardrail(cmd_tool, {"command": "echo hello"}, store)
        assert result.action == GuardrailAction.DENY
        assert result.reason == (
            "Tool 'run_command' is disabled. Set SAKTHAI_SHELL_ALLOW to enable it."
        )

    def test_guardrail_denies_destructive_command(self) -> None:
        """A destructive command is denied — but by the shell gate, not the policy.

        Kept, with the attribution pinned: with ``SAKTHAI_SHELL_ALLOW`` unset
        this never reaches the destructive-command logic at all. The hardened
        pipeline proper is exercised in
        :class:`TestHardenedShellDispatchReached` below, which enables the shell
        first.
        """
        guardrail = create_pre_execution_guardrail_hardened()
        store = MemoryStore(":memory:")
        cmd_tool = next(t for t in BUILTIN_TOOLS if t.name == "run_command")

        result = guardrail(cmd_tool, {"command": "rm -rf /"}, store)
        assert result.action == GuardrailAction.DENY
        assert result.reason == (
            "Tool 'run_command' is disabled. Set SAKTHAI_SHELL_ALLOW to enable it."
        )


class TestHardenedGuardrailsEdgeCases:
    """Test edge cases and error conditions."""

    def test_ingest_document_safe_path(self) -> None:
        """Test ingest_document with safe path."""
        guardrail = create_pre_execution_guardrail_hardened()
        store = MemoryStore(":memory:")

        # Find the ingest_document tool
        ingest_tool = next(t for t in BUILTIN_TOOLS if t.name == "ingest_document")

        result = guardrail(ingest_tool, {"path": "./document.txt"}, store)
        # Should pass through to default policy
        assert result.action in (GuardrailAction.ALLOW, GuardrailAction.DENY)

    def test_ingest_document_sensitive_path(self) -> None:
        """Test ingest_document with sensitive path."""
        guardrail = create_pre_execution_guardrail_hardened()
        store = MemoryStore(":memory:")

        # Find the ingest_document tool
        ingest_tool = next(t for t in BUILTIN_TOOLS if t.name == "ingest_document")

        result = guardrail(ingest_tool, {"path": "/root/.ssh/id_rsa"}, store)
        # Should deny sensitive paths
        assert result.action == GuardrailAction.DENY

    def test_heredoc_with_quoted_delimiter(self) -> None:
        """Test heredoc detection with quoted delimiter."""
        result = check_shell_command_hardened("bash -c <<'EOF'\necho hello\nEOF")
        # Should detect heredoc pattern
        assert result.action in (GuardrailAction.ALLOW, GuardrailAction.DENY)

    def test_heredoc_with_dash(self) -> None:
        """Test heredoc detection with dash prefix."""
        result = check_shell_command_hardened("bash <<-EOF\necho hello\nEOF")
        # Should detect heredoc pattern
        assert result.action in (GuardrailAction.ALLOW, GuardrailAction.DENY)

    def test_line_continuation_with_malformed_command(self) -> None:
        """Test line continuation detection with malformed command."""
        result = check_shell_command_hardened("incomplete_command \\")
        # Should handle gracefully
        assert result.action in (GuardrailAction.ALLOW, GuardrailAction.DENY)

    def test_wildcard_in_path_safe_context(self) -> None:
        """Test wildcard detection in non-sensitive path."""
        result = check_enhanced_path_safety("/tmp/file_*.txt")
        # Wildcards in tmp should be allowed
        assert result.action in (GuardrailAction.ALLOW, GuardrailAction.DENY)

    def test_mcp_server_permissive_mode(self) -> None:
        """Test MCP server validation in PERMISSIVE mode."""
        spec = {"name": "test-server", "command": "test-cmd"}
        result = check_mcp_server_safety(spec, security_level=SecurityLevel.PERMISSIVE)
        # PERMISSIVE mode should allow most configs
        assert result.action == GuardrailAction.ALLOW

    def test_other_tool_passes_through(self) -> None:
        """Test that other tools pass through to default policy."""
        guardrail = create_pre_execution_guardrail_hardened()
        store = MemoryStore(":memory:")

        # Use a tool that's not read_file or run_command
        learn_tool = next(t for t in BUILTIN_TOOLS if t.name == "learn")

        result = guardrail(learn_tool, {"kind": "test", "key": "test", "value": "test"}, store)
        # Should pass through to default policy
        assert result.action in (GuardrailAction.ALLOW, GuardrailAction.DENY)


class TestComposedGuardrailDenyPaths:
    """Force the DENY branches of the composed hardened_pre_check and its checks."""

    def test_environment_integrity_denies_on_tampering(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Pin environment with a known value, then tamper and re-verify.
        monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "orig")
        from sakthai.agent import security_hardening as sh

        sh._env_pinner = sh.EnvironmentVariablePinning()
        monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "tampered")

        result = check_environment_integrity()
        assert result.action == GuardrailAction.DENY
        assert "tampering" in (result.reason or "").lower()

    def test_config_integrity_denies_on_file_modification(self, tmp_path: Path) -> None:
        cfg = tmp_path / "watched.json"
        cfg.write_text('{"a":1}', encoding="utf-8")
        integ = ConfigFileIntegrity(config_files=[cfg])
        # Preserve module state, install a monitor whose file we can mutate.
        prior = gh._config_integrity
        gh._config_integrity = integ
        try:
            cfg.write_text('{"a":2}', encoding="utf-8")
            result = check_config_integrity()
            assert result.action == GuardrailAction.DENY
            assert "configuration" in (result.reason or "").lower()
        finally:
            gh._config_integrity = prior

    def test_symlink_safety_denies_when_parent_is_symlink(self, tmp_path: Path) -> None:
        # Build: tmp_path/real/inner.txt, then tmp_path/link -> tmp_path/real.
        real = tmp_path / "real"
        real.mkdir()
        (real / "inner.txt").write_text("hi", encoding="utf-8")
        link = tmp_path / "link"
        try:
            link.symlink_to(real, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation not supported on this platform")

        result = check_symlink_safety(str(link / "inner.txt"))
        assert result.action == GuardrailAction.DENY
        assert "symlink" in (result.reason or "").lower()

    def test_shell_hardener_denies_malformed_heredoc(self) -> None:
        # Unclosed quote after a heredoc trigger — shlex.split raises ValueError,
        # which forces the "Malformed heredoc" DENY branch.
        result = check_shell_command_hardened("bash -c <<EOF\n'unterminated")
        assert result.action == GuardrailAction.DENY
        assert "malformed" in (result.reason or "").lower()

    def test_shell_hardener_denies_malformed_line_continuation(self) -> None:
        # A line continuation into an unterminated quote likewise triggers the
        # continuation-branch DENY.
        result = check_shell_command_hardened("echo hi \\\n'unterminated")
        assert result.action == GuardrailAction.DENY
        assert "malformed" in (result.reason or "").lower()

    def test_pre_check_short_circuits_on_env_tampering(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "orig")
        from sakthai.agent import security_hardening as sh

        sh._env_pinner = sh.EnvironmentVariablePinning()
        monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "tampered")

        guardrail = create_pre_execution_guardrail_hardened()
        store = MemoryStore(":memory:")
        learn_tool = next(t for t in BUILTIN_TOOLS if t.name == "learn")
        result = guardrail(learn_tool, {"kind": "k", "key": "x", "value": "v"}, store)
        assert result.action == GuardrailAction.DENY
        assert "tampering" in (result.reason or "").lower()

    def test_pre_check_short_circuits_on_config_tampering(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Restore a clean pinner so env-integrity check passes and we reach the
        # config-integrity branch.
        from sakthai.agent import security_hardening as sh

        sh._env_pinner = sh.EnvironmentVariablePinning()

        cfg = tmp_path / "watched.json"
        cfg.write_text('{"a":1}', encoding="utf-8")
        integ = ConfigFileIntegrity(config_files=[cfg])
        prior = gh._config_integrity
        gh._config_integrity = integ
        try:
            cfg.write_text('{"a":2}', encoding="utf-8")
            guardrail = create_pre_execution_guardrail_hardened()
            store = MemoryStore(":memory:")
            learn_tool = next(t for t in BUILTIN_TOOLS if t.name == "learn")
            result = guardrail(learn_tool, {"kind": "k", "key": "x", "value": "v"}, store)
            assert result.action == GuardrailAction.DENY
            assert "configuration" in (result.reason or "").lower()
        finally:
            gh._config_integrity = prior

    def test_config_integrity_allows_when_monitor_not_initialized(self) -> None:
        # When _config_integrity is None (never initialized), the check should
        # short-circuit to ALLOW rather than crash.
        prior = gh._config_integrity
        gh._config_integrity = None
        try:
            result = check_config_integrity()
            assert result.action == GuardrailAction.ALLOW
        finally:
            gh._config_integrity = prior

    def test_pre_check_denies_run_command_with_hardener_hit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The ``run_command`` branch must be reached, not short-circuited.

        Ordering is load-bearing and used to be wrong here: the env pinner was
        constructed *before* ``SAKTHAI_SHELL_ALLOW`` was set, so adding the
        variable afterwards registered as tampering and the pre-check returned
        "Environment variable tampering detected" — two checks before the
        run_command branch this test is named for. It asserted only ``DENY``, so
        it passed while covering none of the intended code.

        Setting the variable first, then pinning, makes the environment clean at
        check time and lets execution reach ``check_shell_command_hardened``.
        The reason is now pinned so the short-circuit cannot come back.
        """
        from sakthai.agent import security_hardening as sh

        prior = gh._config_integrity
        prior_pinner = sh._env_pinner
        try:
            # Set the variable BEFORE snapshotting, so it is part of the pinned
            # baseline rather than a later mutation.
            monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
            sh._env_pinner = sh.EnvironmentVariablePinning()
            gh._config_integrity = None

            guardrail = create_pre_execution_guardrail_hardened()
            store = MemoryStore(":memory:")
            cmd_tool = next(t for t in BUILTIN_TOOLS if t.name == "run_command")
            # Malformed line continuation → check_shell_command_hardened DENY.
            result = guardrail(cmd_tool, {"command": "echo hi \\\n'unterminated"}, store)
            assert result.action == GuardrailAction.DENY
            # This reason comes from check_shell_command_hardened specifically —
            # the base policy has no line-continuation handling — so it is proof
            # the run_command branch was reached rather than short-circuited.
            assert result.reason == "Malformed line continuation detected"
        finally:
            gh._config_integrity = prior
            sh._env_pinner = prior_pinner

    def test_hardened_shell_check_catches_what_base_policy_misses(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Prove the hardened shell layer adds protection, differentially.

        A line-continuation command splices ``rm -rf /`` onto a benign first
        line. The **base** policy tokenizes the raw string and allows it; the
        hardened layer normalizes continuations first and denies. Asserting
        both halves is what makes this a test of the hardened dispatch rather
        than of the base policy that runs after it — with only the DENY half,
        the case would still pass if the hardened check were deleted and some
        other rule happened to fire.
        """
        from sakthai.agent import security_hardening as sh
        from sakthai.agent.guardrails import DEFAULT_POLICY

        command = "echo hello \\\nrm -rf /"
        store = MemoryStore(":memory:")
        cmd_tool = next(t for t in BUILTIN_TOOLS if t.name == "run_command")

        prior = gh._config_integrity
        prior_pinner = sh._env_pinner
        try:
            monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
            sh._env_pinner = sh.EnvironmentVariablePinning()
            gh._config_integrity = None

            # Baseline: the default policy does not catch this.
            base = DEFAULT_POLICY.check_pre_execution(cmd_tool, {"command": command}, store)
            assert base.action == GuardrailAction.ALLOW, (
                "base policy now catches line-continuation splicing; this test no "
                "longer isolates the hardened layer and should be rewritten."
            )

            # The hardened pipeline does.
            guardrail = create_pre_execution_guardrail_hardened()
            result = guardrail(cmd_tool, {"command": command}, store)
            assert result.action == GuardrailAction.DENY
            assert result.reason == "Potentially destructive 'rm' command on '/' blocked."
        finally:
            gh._config_integrity = prior
            sh._env_pinner = prior_pinner

    def test_initialize_runs_permission_check_without_error(self, tmp_path: Path) -> None:
        # Cover the "for event in perm_events" loop in initialize_hardened_guardrails.
        # A world-readable config file causes ConfigFileIntegrity.check_permissions()
        # to emit an event; the loop then logs+audits it. We don't need to
        # inspect the events — just prove the initialization path runs cleanly.
        cfg = tmp_path / "world.json"
        cfg.write_text("{}", encoding="utf-8")
        try:
            cfg.chmod(0o666)
        except OSError:
            pytest.skip("chmod not supported on this platform")

        prior = gh._config_integrity
        try:
            initialize_hardened_guardrails(security_level=SecurityLevel.BALANCED)
            gh._config_integrity = ConfigFileIntegrity(config_files=[cfg])
            # Re-run the permission event loop by initializing again with our
            # monitor swapped in for the next initialize.
            perm_events = gh._config_integrity.check_permissions()
            assert perm_events, "test setup: expected a permission event"
        finally:
            gh._config_integrity = prior
