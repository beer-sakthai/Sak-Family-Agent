from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "personas" / "sakthai") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

# ruff: noqa: E402
from scripts.telegram_send import discover_chat_id


def test_discover_chat_id_redacts_secrets_in_exception(capsys):
    token = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    url_with_token = f"https://api.telegram.org/bot{token}/getUpdates"

    with patch(
        "urllib.request.urlopen",
        side_effect=URLError(f"Connection refused to {url_with_token}"),
    ):
        result = discover_chat_id(token)

    assert result is None
    captured = capsys.readouterr()
    assert token not in captured.err
    assert "[REDACTED]" in captured.err
