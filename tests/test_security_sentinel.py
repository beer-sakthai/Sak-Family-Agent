from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from sakthai.agent.tools import _send_telegram_message
from sakthai.memory.store import MemoryStore

# Ensure scripts folder can be imported
REPO_ROOT = Path(__file__).resolve().parent.parent


def _ensure_repo_root_on_syspath() -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


def test_telegram_token_leak_in_error() -> None:
    """Verify that an invalid TELEGRAM_BOT_TOKEN is not leaked in the error message."""
    sensitive_token = "12345:sensitive_secret_data"
    os.environ["TELEGRAM_BOT_TOKEN"] = sensitive_token
    os.environ["TELEGRAM_CHAT_ID"] = "67890"

    # Use a token that fails the format regex ^[0-9]+:[a-zA-Z0-9_-]+$
    # or just use any invalid token and ensure it's not in the result.
    os.environ["TELEGRAM_BOT_TOKEN"] = "INVALID TOKEN WITH SECRET 12345"

    store = MagicMock(spec=MemoryStore)
    result = _send_telegram_message({"message": "hello"}, store)

    assert "Error: Invalid TELEGRAM_BOT_TOKEN format" in result
    assert "INVALID TOKEN" not in result
    assert "SECRET" not in result
    assert "12345" not in result


def test_telegram_send_mcp_robustness() -> None:
    """Verify that send_via_mcp gracefully handles different malformed/unexpected inputs from the subprocess."""
    _ensure_repo_root_on_syspath()
    from scripts.telegram_send import send_via_mcp

    # 1. Test invalid JSON output (should ignore it and not crash)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="this is not JSON\n"
            '{"jsonrpc": "2.0", "id": 2, "result": {"content": [{"text": "Telegram message sent successfully"}]}}',
        )
        res = send_via_mcp("test message")
        assert res == 0

    # 2. Test unexpected non-dictionary JSON input (e.g. list, string)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="[1, 2, 3]\n"
            '"just a string"\n'
            '{"jsonrpc": "2.0", "id": 2, "result": {"content": [{"text": "Telegram message sent successfully"}]}}',
        )
        res = send_via_mcp("test message")
        assert res == 0

    # 3. Test unexpected nested structures (e.g. result not dict, content not list, content empty list, content elements not dict)
    for bad_stdout in [
        # result is not a dict
        '{"jsonrpc": "2.0", "id": 2, "result": "not a dict"}',
        # content is not a list
        '{"jsonrpc": "2.0", "id": 2, "result": {"content": "not a list"}}',
        # content is an empty list
        '{"jsonrpc": "2.0", "id": 2, "result": {"content": []}}',
        # first element of content is not a dict
        '{"jsonrpc": "2.0", "id": 2, "result": {"content": ["not a dict"]}}',
        # text field missing in first element of content
        '{"jsonrpc": "2.0", "id": 2, "result": {"content": [{}]}}',
    ]:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=bad_stdout)
            res = send_via_mcp("test message")
            assert (
                res == 1
            )  # Should not crash, but should return failure status (1) since no reply was successfully extracted


if __name__ == "__main__":
    test_telegram_token_leak_in_error()
    test_telegram_send_mcp_robustness()
    print("Security test passed.")
