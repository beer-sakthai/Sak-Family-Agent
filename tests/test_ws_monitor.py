from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Add the script folder to sys.path so we can import ws_monitor
SCRIPT_DIR = Path(__file__).resolve().parents[1] / "sakthai-chat-cli" / "personas" / "sakthai" / "skills" / "creative" / "comfyui" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import ws_monitor  # noqa: E402


def test_parse_args_defaults() -> None:
    args = ws_monitor.parse_args([])
    assert args.host == ws_monitor.DEFAULT_LOCAL_HOST  # type: ignore[attr-defined]
    assert args.api_key is None
    assert args.client_id is None
    assert args.prompt_id is None
    assert args.previews is None
    assert not args.no_color
    assert args.timeout == 600.0


def test_parse_args_custom() -> None:
    args = ws_monitor.parse_args([
        "--host", "example.com",
        "--api-key", "test-key",
        "--client-id", "my-client",
        "--prompt-id", "my-prompt",
        "--previews", "/tmp/previews",
        "--no-color",
        "--timeout", "120.0"
    ])
    assert args.host == "example.com"
    assert args.api_key == "test-key"
    assert args.client_id == "my-client"
    assert args.prompt_id == "my-prompt"
    assert args.previews == "/tmp/previews"
    assert args.no_color
    assert args.timeout == 120.0


def test_get_ws_connection_details() -> None:
    args = argparse.Namespace(
        host="localhost:8188",
        api_key=None,
        client_id="fixed-client-id",
        previews=None,
        no_color=False,
        timeout=600.0
    )
    ws_url, display_url, client_id = ws_monitor.get_ws_connection_details(args)
    assert "ws://localhost:8188/ws?clientId=fixed-client-id" in ws_url
    assert ws_url == display_url
    assert client_id == "fixed-client-id"


def test_handle_binary_frame_none(tmp_path: Path) -> None:
    # None message or too short msg should do nothing and return original counter
    cnt = ws_monitor.handle_binary_frame(b"", tmp_path, 5)
    assert cnt == 5


def test_handle_binary_frame_preview(tmp_path: Path) -> None:
    # 8 bytes header (type=1, img_type=2) + image bytes
    import struct
    header = struct.pack(">II", 1, 2)
    img_data = b"fake-png-bytes"
    msg = header + img_data

    cnt = ws_monitor.handle_binary_frame(msg, tmp_path, 0)
    assert cnt == 1

    saved_file = tmp_path / "preview_00000.png"
    assert saved_file.exists()
    assert saved_file.read_bytes() == img_data


def test_handle_text_message_status(capsys: Any) -> None:
    msg_json = '{"type": "status", "data": {"status": {"exec_info": {"queue_remaining": 3}}}}'
    ret = ws_monitor.handle_text_message(msg_json, None, False)
    assert ret is None
    captured = capsys.readouterr()
    assert "[status] queue_remaining=3" in captured.out


def test_handle_text_message_executing(capsys: Any) -> None:
    msg_json = '{"type": "executing", "data": {"node": "12", "prompt_id": "p1"}}'
    ret = ws_monitor.handle_text_message(msg_json, None, False)
    assert ret is None
    captured = capsys.readouterr()
    assert "[executing] node=12" in captured.out


def test_handle_text_message_progress(capsys: Any) -> None:
    msg_json = '{"type": "progress", "data": {"value": 5, "max": 10, "node": "15"}}'
    ret = ws_monitor.handle_text_message(msg_json, None, False)
    assert ret is None
    captured = capsys.readouterr()
    assert "[progress] 5/10 ( 50.0%) node=15" in captured.out


def test_handle_text_message_executed(capsys: Any) -> None:
    msg_json = '{"type": "executed", "data": {"node": "10", "output": {"images": [{"filename": "img.png"}]}}}'
    ret = ws_monitor.handle_text_message(msg_json, None, False)
    assert ret is None
    captured = capsys.readouterr()
    assert "[executed] node=10 images=1" in captured.out


def test_handle_text_message_success_filtered() -> None:
    msg_json = '{"type": "execution_success", "data": {"prompt_id": "my-prompt"}}'
    # Filter matches
    ret = ws_monitor.handle_text_message(msg_json, "my-prompt", False)
    assert ret == 0


def test_handle_text_message_success_unfiltered() -> None:
    msg_json = '{"type": "execution_success", "data": {"prompt_id": "my-prompt"}}'
    # No filter
    ret = ws_monitor.handle_text_message(msg_json, None, False)
    assert ret is None


def test_handle_text_message_error_filtered() -> None:
    msg_json = '{"type": "execution_error", "data": {"prompt_id": "my-prompt", "exception_type": "ValueError", "exception_message": "Invalid model", "traceback": "mock_tb"}}'
    ret = ws_monitor.handle_text_message(msg_json, "my-prompt", False)
    assert ret == 1


def test_handle_text_message_interrupted_filtered() -> None:
    msg_json = '{"type": "execution_interrupted", "data": {"prompt_id": "my-prompt"}}'
    ret = ws_monitor.handle_text_message(msg_json, "my-prompt", False)
    assert ret == 1


def test_handle_text_message_unknown_type(capsys: Any) -> None:
    msg_json = '{"type": "some_random_type", "data": {"foo": "bar"}}'
    ret = ws_monitor.handle_text_message(msg_json, None, False)
    assert ret is None
    captured = capsys.readouterr()
    assert "[some_random_type]" in captured.out
    assert '{"foo": "bar"}' in captured.out
