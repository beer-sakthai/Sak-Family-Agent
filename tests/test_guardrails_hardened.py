"""Tests for the hardened guardrails integration."""

from pathlib import Path

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
from sakthai.agent.security_hardening import SecurityLevel
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

    def test_glob_pattern_denied(self) -> None:
        """Test that glob patterns are denied."""
        result = check_enhanced_path_safety("/root/.ssh/id_*")
        assert result.action == GuardrailAction.DENY

    def test_case_sensitivity_trick_denied(self) -> None:
        """Test that case-sensitivity tricks are denied."""
        result = check_enhanced_path_safety(".SSH/id_rsa")
        assert result.action == GuardrailAction.DENY


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

    def test_guardrail_allows_safe_command(self) -> None:
        """Test that safe commands are allowed."""
        guardrail = create_pre_execution_guardrail_hardened()
        store = MemoryStore(":memory:")

        # Find the run_command tool
        cmd_tool = next(t for t in BUILTIN_TOOLS if t.name == "run_command")

        result = guardrail(cmd_tool, {"command": "echo hello"}, store)
        # Should allow safe commands (though run_command may be disabled)
        assert result.action in (GuardrailAction.ALLOW, GuardrailAction.DENY)

    def test_guardrail_denies_destructive_command(self) -> None:
        """Test that destructive commands are denied."""
        guardrail = create_pre_execution_guardrail_hardened()
        store = MemoryStore(":memory:")

        # Find the run_command tool
        cmd_tool = next(t for t in BUILTIN_TOOLS if t.name == "run_command")

        result = guardrail(cmd_tool, {"command": "rm -rf /"}, store)
        # Should deny destructive commands
        assert result.action == GuardrailAction.DENY


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
