from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

# Add the directory containing driver.py to sys.path
DRIVER_DIR = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "run-sakthai-chat-cli"
sys.path.insert(0, str(DRIVER_DIR))

import driver  # noqa: E402


def test_interactive_chat_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock driver dependencies to avoid spawning servers or processes
    monkeypatch.setattr(driver, "start_stub", lambda _port: None)
    monkeypatch.setattr(driver, "_tmux", lambda *_args: "")
    monkeypatch.setattr(
        driver, "subprocess", type("FakeSubprocess", (), {"run": lambda *args, **kwargs: None})
    )

    # Mock time.sleep to raise KeyboardInterrupt
    def mock_sleep(secs: float) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(time, "sleep", mock_sleep)

    # Call interactive_chat and assert it handles KeyboardInterrupt and returns 0
    res = driver.interactive_chat(1234)
    assert res == 0


def test_main_stub_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock driver dependencies to avoid spawning servers or processes
    monkeypatch.setattr(driver, "start_stub", lambda _port: None)

    # Mock time.sleep to raise KeyboardInterrupt
    def mock_sleep(secs: float) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(time, "sleep", mock_sleep)

    # Mock sys.argv to choose 'stub' command
    monkeypatch.setattr(sys, "argv", ["driver.py", "stub", "--port", "1234"])

    # Call main and assert it handles KeyboardInterrupt and returns 0
    res = driver.main()
    assert res == 0


def test_main_chat_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock driver dependencies to avoid spawning servers or processes
    monkeypatch.setattr(driver, "start_stub", lambda _port: None)
    monkeypatch.setattr(driver, "_tmux", lambda *_args: "")
    monkeypatch.setattr(
        driver, "subprocess", type("FakeSubprocess", (), {"run": lambda *args, **kwargs: None})
    )

    # Mock time.sleep to raise KeyboardInterrupt
    def mock_sleep(secs: float) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(time, "sleep", mock_sleep)

    # Mock sys.argv to choose 'chat' command
    monkeypatch.setattr(sys, "argv", ["driver.py", "chat", "--port", "1234"])

    # Call main and assert it handles KeyboardInterrupt and returns 0
    res = driver.main()
    assert res == 0
