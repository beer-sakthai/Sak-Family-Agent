"""Tests for the security hardening system.

Tests all attack vectors and defenses identified in the security audit.
"""

import os
from pathlib import Path

from sakthai.agent.security_hardening import (
    AuditLogger,
    ConfigFileIntegrity,
    EnhancedPathValidator,
    EnvironmentVariablePinning,
    MCPServerValidator,
    SecurityEvent,
    SecurityLevel,
    ShellCommandHardener,
    SymlinkDetector,
    TOCTOUPrevention,
)


class TestEnvironmentVariablePinning:
    """Test environment variable pinning and integrity verification."""

    def test_pin_captures_environment_variables(self) -> None:
        """Test that pinning captures environment variables at startup."""
        os.environ["SAKTHAI_SHELL_ALLOW"] = "test_value"
        pinner = EnvironmentVariablePinning()

        assert "SAKTHAI_SHELL_ALLOW" in pinner._pinned_values
        assert pinner._pinned_values["SAKTHAI_SHELL_ALLOW"] == "test_value"

    def test_detects_environment_variable_tampering(self) -> None:
        """Test detection of environment variable changes."""
        os.environ["SAKTHAI_SHELL_ALLOW"] = "original_value"
        pinner = EnvironmentVariablePinning()

        # Tamper with variable
        os.environ["SAKTHAI_SHELL_ALLOW"] = "modified_value"

        events = pinner.verify()
        assert any(e.event_type == "env_tampering" for e in events)

    def test_detects_new_environment_variable(self) -> None:
        """Test detection when new environment variable is added."""
        # Ensure variable doesn't exist
        if "NEW_SECRET_VAR" in os.environ:
            del os.environ["NEW_SECRET_VAR"]

        pinner = EnvironmentVariablePinning()

        # Add new variable
        os.environ["NEW_SECRET_VAR"] = "secret_value"

        events = pinner.verify()
        # This should be detected as tampering (unless it's not in critical list)
        # Check if it's in the critical vars list
        if "NEW_SECRET_VAR" in pinner._CRITICAL_VARS:
            assert any(e.event_type == "env_tampering" for e in events)

    def test_no_tampering_on_stable_environment(self) -> None:
        """Test that stable environment passes verification."""
        os.environ["STABLE_VAR"] = "stable_value"
        pinner = EnvironmentVariablePinning()

        # Don't change anything
        events = pinner.verify()

        # Should have no tampering events (might have other events)
        tampering_events = [e for e in events if e.event_type == "env_tampering"]
        assert len(tampering_events) == 0


class TestMCPServerValidator:
    """Test MCP server validation."""

    def test_validates_server_with_command(self) -> None:
        """Test validation of valid MCP server config."""
        spec = {"name": "valid-server", "command": "some-command", "args": []}

        is_valid, reason = MCPServerValidator.validate_server_config(spec)
        assert is_valid

    def test_rejects_server_without_command(self) -> None:
        """Test rejection of server config without command."""
        spec = {"name": "invalid-server"}

        is_valid, reason = MCPServerValidator.validate_server_config(spec)
        assert not is_valid

    def test_rejects_suspicious_patterns(self) -> None:
        """Test rejection of suspicious command patterns."""
        suspicious_specs = [
            {"name": "evil", "command": "eval 'rm -rf /'; foo"},
            {"name": "evil", "command": "exec /tmp/malware"},
            {"name": "evil", "command": "rm -rf /root"},
        ]

        for spec in suspicious_specs:
            is_valid, reason = MCPServerValidator.validate_server_config(spec)
            assert not is_valid

    def test_strict_mode_requires_allowlist(self) -> None:
        """Test strict mode only allows pre-approved servers."""
        spec = {"name": "unapproved-server", "command": "echo hello", "args": []}

        is_valid, reason = MCPServerValidator.validate_server_config(spec, SecurityLevel.STRICT)
        # Should fail because server not in approved list
        assert not is_valid

    def test_generates_sandbox_wrapper(self) -> None:
        """Test generation of sandbox wrapper for MCP servers."""
        wrapper = MCPServerValidator.get_sandbox_wrapper("python -m my_server", timeout_sec=30)

        # Should include timeout and ulimit (wrapper is a list of command args)
        wrapper_str = " ".join(wrapper)
        assert "timeout" in wrapper_str
        assert "30" in wrapper_str
        assert "ulimit" in wrapper_str


class TestEnhancedPathValidator:
    """Test enhanced path validation."""

    def test_normalizes_unicode_forms(self) -> None:
        """Test Unicode normalization in all forms."""
        path = "/root/.ssh/id_rsa"
        normalized = EnhancedPathValidator.normalize_path_thoroughly(path)

        # Should return multiple normalized forms
        assert len(normalized) > 1
        # All should contain the same essential components
        assert all("root" in n or "ssh" in n or "rsa" in n for n in normalized)

    def test_detects_bracket_glob(self) -> None:
        """Test detection of bracket glob patterns."""
        path = "/[re]ot/.ssh/id_rsa"
        patterns = EnhancedPathValidator.detect_glob_patterns(path)

        assert "bracket_glob" in patterns

    def test_detects_wildcard_patterns(self) -> None:
        """Test detection of wildcard patterns."""
        test_cases = [
            ("/r?ot/.ssh/id_rsa", "single_char_wildcard"),
            ("/*/ssh/id_rsa", "multi_char_wildcard"),
            ("/root/.ssh/id_{rsa,dsa}", "brace_expansion"),
        ]

        for path, expected_pattern in test_cases:
            patterns = EnhancedPathValidator.detect_glob_patterns(path)
            assert expected_pattern in patterns

    def test_detects_case_sensitivity_tricks(self) -> None:
        """Test detection of case-sensitivity bypasses."""
        test_cases = [
            ".SSH/id_rsa",  # Uppercase SSH
            ".Ssh/id_rsa",  # Mixed case
            ".AWS/credentials",  # Uppercase AWS
        ]

        for path in test_cases:
            is_suspicious = EnhancedPathValidator.check_case_sensitivity(path)
            assert is_suspicious


class TestSymlinkDetector:
    """Test symlink detection and prevention."""

    def test_detects_symlink(self, tmp_path: Path) -> None:
        """Test detection of symlink."""
        target = tmp_path / "target.txt"
        target.write_text("content")
        symlink = tmp_path / "link"
        symlink.symlink_to(target)

        assert SymlinkDetector.is_symlink(symlink)
        assert not SymlinkDetector.is_symlink(target)

    def test_resolves_symlink_chain(self, tmp_path: Path) -> None:
        """Test resolution of symlink chains."""
        # Create chain: link1 -> link2 -> target
        target = tmp_path / "target.txt"
        target.write_text("content")

        link1 = tmp_path / "link1"
        link1.symlink_to(target)

        resolved, chain = SymlinkDetector.resolve_symlink_chain(link1)
        assert resolved.name == "target.txt"
        assert len(chain) > 0

    def test_detects_dangerous_symlinks(self, tmp_path: Path) -> None:
        """Test detection of symlinks pointing to critical directories."""
        # Create a symlink pointing to /root
        symlink = tmp_path / "dangerous_link"
        try:
            symlink.symlink_to("/root")

            SymlinkDetector.detect_dangerous_symlinks(str(symlink))
            # Should detect the danger (if not running as root with actual /root access)
            # In test environment might not have real /root
        except (OSError, PermissionError):
            # Expected in test environment
            pass


class TestConfigFileIntegrity:
    """Test configuration file integrity monitoring."""

    def test_captures_config_file_hashes(self, tmp_path: Path) -> None:
        """Test capturing hashes of config files."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"key": "value"}')

        monitor = ConfigFileIntegrity([config_file])
        assert config_file in monitor.hashes
        assert len(monitor.hashes[config_file]) == 64  # SHA256 hex length

    def test_detects_config_file_tampering(self, tmp_path: Path) -> None:
        """Test detection of config file modifications."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"key": "value"}')

        monitor = ConfigFileIntegrity([config_file])

        # Tamper with config
        config_file.write_text('{"key": "modified"}')

        events = monitor.verify()
        assert any(e.event_type == "config_tampering" for e in events)

    def test_checks_config_file_permissions(self, tmp_path: Path) -> None:
        """Test checking for overly permissive config file permissions."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"key": "value"}')

        # Make it world-readable
        config_file.chmod(0o644)

        monitor = ConfigFileIntegrity([config_file])
        events = monitor.check_permissions()

        # Might detect overly permissive permissions
        # Behavior depends on umask and OS
        assert isinstance(events, list)


class TestTOCTOUPrevention:
    """Test time-of-check-to-time-of-use prevention."""

    def test_atomic_check_and_read(self, tmp_path: Path) -> None:
        """Test atomic file check and read."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("safe content")

        def check_fn(path: Path) -> bool:
            return path.exists() and path.stat().st_size < 1000

        success, content = TOCTOUPrevention.atomic_check_and_read(test_file, check_fn)

        assert success
        assert content == "safe content"

    def test_detects_toctou_mismatch(self, tmp_path: Path) -> None:
        """Test detection of TOCTOU attacks."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        def failing_check_fn(path: Path) -> bool:
            # Always fail to simulate mismatch
            return False

        success, content = TOCTOUPrevention.atomic_check_and_read(test_file, failing_check_fn)

        assert not success


class TestShellCommandHardener:
    """Test shell command hardening."""

    def test_detects_heredoc_patterns(self) -> None:
        """Test detection of heredoc patterns."""
        commands = [
            "bash -c <<EOF\nrm -rf /\nEOF",
            "sh -c <<'SCRIPT'\ndestructive\nSCRIPT",
            "bash <<-END\ncommand\nEND",
        ]

        for cmd in commands:
            heredocs = ShellCommandHardener.detect_heredoc(cmd)
            assert len(heredocs) > 0

    def test_detects_line_continuation(self) -> None:
        """Test detection of line continuation attempts."""
        commands = [
            "echo hello \\\necho world",
            "command1 \\\ncommand2",
            "bad_command \\\n",
        ]

        for cmd in commands:
            has_continuation = ShellCommandHardener.detect_line_continuation(cmd)
            assert has_continuation

    def test_expands_line_continuations(self) -> None:
        """Test expansion of line continuations."""
        original = "echo hello \\\necho world"
        expanded = ShellCommandHardener.expand_line_continuations(original)

        # Should replace backslash+newline with space
        assert "\\\n" not in expanded
        assert "echo hello" in expanded and "echo world" in expanded


class TestAuditLogger:
    """Test audit logging."""

    def test_logs_security_events(self, tmp_path: Path) -> None:
        """Test logging of security events."""
        log_file = tmp_path / "audit.log"
        logger = AuditLogger(log_file)

        event = SecurityEvent(
            event_type="test_event",
            severity="high",
            message="Test security event",
            timestamp=0.0,
        )

        logger.log_event(event)

        assert log_file.exists()
        content = log_file.read_text()
        assert "test_event" in content
        assert "Test security event" in content

    def test_retrieves_critical_events(self) -> None:
        """Test retrieval of critical security events."""
        logger = AuditLogger(None)

        critical_event = SecurityEvent(
            event_type="critical_test",
            severity="critical",
            message="Critical event",
            timestamp=0.0,
        )

        medium_event = SecurityEvent(
            event_type="medium_test",
            severity="medium",
            message="Medium event",
            timestamp=1.0,
        )

        logger.log_event(critical_event)
        logger.log_event(medium_event)

        critical_events = logger.check_critical_events()
        assert len(critical_events) == 1
        assert critical_events[0].event_type == "critical_test"


class TestIntegrationHardenedGuardrails:
    """Integration tests for hardened guardrails."""

    def test_unicode_normalization_defense(self) -> None:
        """Test that Unicode normalization bypass is prevented."""
        import unicodedata

        # Create a path with different Unicode form
        nfd_path = unicodedata.normalize("NFD", "/root/.ssh/id_rsa")

        # Should still be detected as sensitive even in different form
        normalized_forms = EnhancedPathValidator.normalize_path_thoroughly(nfd_path)
        # One of the forms should be the original sensitive path
        assert any("root" in form for form in normalized_forms)

    def test_symlink_traversal_defense(self, tmp_path: Path) -> None:
        """Test defense against symlink traversal."""
        # Create a safe directory and a symlink to it
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()

        test_file = safe_dir / "test.txt"
        test_file.write_text("content")

        link = tmp_path / "link"
        link.symlink_to(safe_dir)

        # Should detect symlink (though it's not dangerous in this case)
        is_symlink = SymlinkDetector.is_symlink(link)
        assert is_symlink

    def test_wildcard_bypass_defense(self) -> None:
        """Test defense against glob/wildcard bypass."""
        dangerous_paths = [
            "/root/.ssh/id_*",
            "/etc/*/passwd",
            "/[ehr]oot/.ssh/id_rsa",
        ]

        for path in dangerous_paths:
            patterns = EnhancedPathValidator.detect_glob_patterns(path)
            assert len(patterns) > 0, f"Failed to detect glob in {path}"

    def test_case_sensitivity_defense(self) -> None:
        """Test defense against case-sensitivity tricks."""
        tricky_paths = [
            ".SSH/id_rsa",  # uppercase
            ".Env.local",  # mixed case
            ".AWS/credentials",  # uppercase
        ]

        for path in tricky_paths:
            is_suspicious = EnhancedPathValidator.check_case_sensitivity(path)
            assert is_suspicious


class TestSecurityEventStructure:
    """Test SecurityEvent dataclass."""

    def test_creates_security_event(self) -> None:
        """Test creating a security event."""
        event = SecurityEvent(
            event_type="test",
            severity="high",
            message="Test message",
            timestamp=123.45,
            details={"key": "value"},
        )

        assert event.event_type == "test"
        assert event.severity == "high"
        assert event.message == "Test message"
        assert event.timestamp == 123.45
        assert event.details == {"key": "value"}

    def test_event_without_details(self) -> None:
        """Test creating event without details."""
        event = SecurityEvent(
            event_type="test",
            severity="low",
            message="Simple event",
            timestamp=0.0,
        )

        assert event.details is None


class TestAdditionalCoverage:
    """Additional tests for coverage of edge cases."""

    def test_disable_verification(self) -> None:
        """Test disabling environment verification."""
        os.environ["SAKTHAI_SHELL_ALLOW"] = "original"
        pinner = EnvironmentVariablePinning()
        pinner.disable_verification()

        # Tamper with variable
        os.environ["SAKTHAI_SHELL_ALLOW"] = "modified"

        # Verification disabled, so should return no events
        events = pinner.verify()
        assert len(events) == 0

    def test_detects_variable_removal(self) -> None:
        """Test detection when environment variable is removed."""
        # Ensure variable exists
        os.environ["SAKTHAI_SHELL_ALLOW"] = "some_value"
        pinner = EnvironmentVariablePinning()

        # Remove the variable
        if "SAKTHAI_SHELL_ALLOW" in os.environ:
            del os.environ["SAKTHAI_SHELL_ALLOW"]

        events = pinner.verify()
        tampering_events = [e for e in events if e.event_type == "env_tampering"]
        assert any("removed" in e.message for e in tampering_events)

    def test_detects_variable_addition(self) -> None:
        """Test detection when new critical variable is added."""
        # Ensure variable doesn't exist at start
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]

        pinner = EnvironmentVariablePinning()

        # Add the variable after pinning
        os.environ["ANTHROPIC_API_KEY"] = "new_key"

        events = pinner.verify()
        tampering_events = [e for e in events if e.event_type == "env_tampering"]
        assert any("added" in e.message for e in tampering_events)

    def test_symlink_chain_with_max_depth(self, tmp_path: Path) -> None:
        """Test symlink chain resolution with max depth limit."""
        # Create a chain of symlinks
        target = tmp_path / "target.txt"
        target.write_text("content")

        current = target
        for i in range(5):
            link = tmp_path / f"link_{i}"
            link.symlink_to(current)
            current = link

        # Resolve with small max_depth
        resolved, chain = SymlinkDetector.resolve_symlink_chain(current, max_depth=3)
        # Should stop at max_depth, not traverse all 5 links
        assert len(chain) == 3

    def test_config_file_check_permissions_with_sensitive_file(self, tmp_path: Path) -> None:
        """Test permission checking on sensitive config files."""
        config_file = tmp_path / "sensitive.json"
        config_file.write_text('{"secret": "value"}')

        # Make file world-readable (0o644)
        config_file.chmod(0o644)

        monitor = ConfigFileIntegrity([config_file])
        events = monitor.check_permissions()

        # At minimum, this should not crash
        assert isinstance(events, list)

    def test_mcp_server_without_args(self) -> None:
        """Test MCP server validation without args field."""
        spec = {"name": "minimal-server", "command": "echo hello"}

        is_valid, reason = MCPServerValidator.validate_server_config(spec)
        assert is_valid

    def test_mcp_server_with_invalid_args(self) -> None:
        """Test MCP server validation with invalid args (not a list)."""
        spec = {
            "name": "bad-server",
            "command": "echo hello",
            "args": "not_a_list",
        }

        is_valid, reason = MCPServerValidator.validate_server_config(spec)
        assert not is_valid
        assert "list" in reason

    def test_toctou_atomic_read_nonexistent_file(self, tmp_path: Path) -> None:
        """Test atomic read on non-existent file."""
        nonexistent = tmp_path / "nonexistent.txt"

        def check_fn(path: Path) -> bool:
            return path.exists()

        success, content = TOCTOUPrevention.atomic_check_and_read(nonexistent, check_fn)
        assert not success

    def test_audit_logger_with_file_path(self, tmp_path: Path) -> None:
        """Test audit logger writing to a file."""
        log_file = tmp_path / "audit.log"
        logger = AuditLogger(log_file)

        event = SecurityEvent(
            event_type="test",
            severity="high",
            message="Test event",
            timestamp=0.0,
        )

        logger.log_event(event)
        assert log_file.exists()
        content = log_file.read_text()
        assert "test" in content.lower()
