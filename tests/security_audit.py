from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from sakthai.agent.loop import _execute_tool, _save_session_log, AgentResult
from sakthai.memory.store import MemoryStore

def test_tool_output_redaction():
    print("Testing tool output redaction...")
    # Mock a tool that returns a secret
    secret = "sk-ant-api01-1234567890abcdef1234567890abcdef"
    os.environ["ANTHROPIC_API_KEY"] = secret

    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool.handler.return_value = f"My key is {secret}"

    output, is_error = _execute_tool(mock_tool, {}, MagicMock(spec=MemoryStore))

    assert secret not in output
    assert "[REDACTED]" in output
    print("  [OK] Success output redacted.")

    # Test error output redaction
    mock_tool.handler.side_effect = Exception(f"Failed with {secret}")
    output, is_error = _execute_tool(mock_tool, {}, MagicMock(spec=MemoryStore))

    assert secret not in output
    assert "[REDACTED]" in output
    assert is_error is True
    print("  [OK] Error output redacted.")

def test_session_log_security():
    print("Testing session log security...")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        os.environ["SAKTHAI_HOME"] = str(tmpdir)
        secret = "sk-1234567890abcdef1234567890abcdef"
        os.environ["OPENAI_API_KEY"] = secret

        task = f"User said {secret}"
        result = AgentResult(text=f"Response with {secret}", iterations=1, stop_reason="end_turn", tool_calls=[], usage={})

        _save_session_log(task, "gpt-4", [], result)

        s_dir = tmpdir / "sessions"
        assert s_dir.is_dir()
        # Permission check (0700)
        mode = os.stat(s_dir).st_mode & 0o777
        assert mode == 0o700, f"Expected 0700, got {oct(mode)}"

        files = list(s_dir.glob("*.json"))
        assert len(files) == 1
        log_file = files[0]

        # Permission check (0600)
        mode = os.stat(log_file).st_mode & 0o777
        assert mode == 0o600, f"Expected 0600, got {oct(mode)}"

        # Redaction check
        content = log_file.read_text(encoding="utf-8")
        assert secret not in content
        assert "[REDACTED]" in content
        print("  [OK] Session logs redacted and permissions restricted.")
    finally:
        shutil.rmtree(tmpdir)

def test_memory_db_security():
    print("Testing memory database security...")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        db_path = tmpdir / "memory.db"
        # Initializing MemoryStore should create DB and restrict permissions
        with MemoryStore(db_path=db_path) as store:
            pass

        # Parent dir check (0700)
        mode = os.stat(tmpdir).st_mode & 0o777
        assert mode == 0o700, f"Expected 0700, got {oct(mode)}"

        # DB file check (0600)
        mode = os.stat(db_path).st_mode & 0o777
        assert mode == 0o600, f"Expected 0600, got {oct(mode)}"
        print("  [OK] Memory database permissions restricted.")
    finally:
        shutil.rmtree(tmpdir)

if __name__ == "__main__":
    try:
        test_tool_output_redaction()
        test_session_log_security()
        test_memory_db_security()
        print("\nALL SECURITY AUDIT TESTS PASSED!")
    except AssertionError as e:
        print(f"\nAUDIT FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
