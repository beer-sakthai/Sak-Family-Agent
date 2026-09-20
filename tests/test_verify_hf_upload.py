"""Tests for sakthai.scripts.verify_hf_upload, used by verify-assets.yml."""

import socket
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from sakthai.scripts import verify_hf_upload


@patch("socket.getaddrinfo")
@patch("subprocess.run")
def test_verify_url_success_on_200_status(
    mock_subprocess_run: MagicMock, mock_getaddrinfo: MagicMock
) -> None:
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
    ]
    mock_result = MagicMock()
    mock_result.stdout = "200"
    mock_subprocess_run.return_value = mock_result

    result = verify_hf_upload.verify_url("https://example.com/success", "Test Resource")

    assert result is True
    mock_subprocess_run.assert_called_once_with(
        [
            "curl",
            "-s",
            "-o",
            "/dev/null",
            "-w",
            "%{http_code}",
            "--resolve",
            "example.com:443:93.184.216.34",
            "https://example.com/success",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )


@patch("socket.getaddrinfo")
@patch("subprocess.run")
def test_verify_url_failure_on_404_status(
    mock_subprocess_run: MagicMock, mock_getaddrinfo: MagicMock
) -> None:
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
    ]
    mock_result = MagicMock()
    mock_result.stdout = "404"
    mock_subprocess_run.return_value = mock_result

    result = verify_hf_upload.verify_url("https://example.com/notfound", "Test Resource")

    assert result is False
    mock_subprocess_run.assert_called_once()


@patch("socket.getaddrinfo")
@patch("subprocess.run")
def test_verify_url_error_on_subprocess_exception(
    mock_subprocess_run: MagicMock, mock_getaddrinfo: MagicMock
) -> None:
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
    ]
    mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="curl", timeout=30)

    result = verify_hf_upload.verify_url("https://example.com/timeout", "Test Resource")

    assert result is False
    mock_subprocess_run.assert_called_once()


def test_verify_url_blocks_option_smuggling() -> None:
    result = verify_hf_upload.verify_url("-v", "Resource")
    assert result is False


def test_verify_url_blocks_invalid_scheme() -> None:
    result = verify_hf_upload.verify_url("ftp://example.com", "Resource")
    assert result is False


@patch("socket.getaddrinfo")
def test_verify_url_blocks_private_ip(mock_getaddrinfo: MagicMock) -> None:
    # Resolve to loopback IP
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
    ]
    result = verify_hf_upload.verify_url("https://example.com", "Resource")
    assert result is False

    # Resolve to private IP
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.5", 443))
    ]
    result = verify_hf_upload.verify_url("https://example.com", "Resource")
    assert result is False

    # Resolve to link-local IP
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 443))
    ]
    result = verify_hf_upload.verify_url("https://example.com", "Resource")
    assert result is False


@patch("sakthai.scripts.verify_hf_upload.verify_url")
@patch("sys.exit")
def test_main_success_with_multiple_urls(
    mock_sys_exit: MagicMock, mock_verify_url: MagicMock
) -> None:
    mock_verify_url.return_value = True
    test_urls = ["http://url1.com", "http://url2.com"]
    with patch.object(sys, "argv", ["verify_hf_upload.py"] + test_urls):
        verify_hf_upload.main()

    assert mock_verify_url.call_count == 2
    mock_verify_url.assert_any_call(test_urls[0], "Resource #1")
    mock_verify_url.assert_any_call(test_urls[1], "Resource #2")
    mock_sys_exit.assert_not_called()


@patch("sakthai.scripts.verify_hf_upload.verify_url")
@patch("sys.exit")
def test_main_failure_with_one_bad_url(
    mock_sys_exit: MagicMock, mock_verify_url: MagicMock
) -> None:
    mock_verify_url.side_effect = [True, False]
    test_urls = ["http://success.com", "http://fail.com"]
    with patch.object(sys, "argv", ["verify_hf_upload.py"] + test_urls):
        verify_hf_upload.main()

    assert mock_verify_url.call_count == 2
    mock_sys_exit.assert_called_once_with(1)


@patch("sakthai.scripts.verify_hf_upload.verify_url")
@patch("sys.exit")
def test_main_exits_with_no_urls(
    mock_sys_exit: MagicMock, mock_verify_url: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    with patch.object(sys, "argv", ["verify_hf_upload.py"]):
        verify_hf_upload.main()

    mock_verify_url.assert_not_called()
    mock_sys_exit.assert_called_once_with(1)

    captured = capsys.readouterr()
    assert "Usage: python3 verify_hf_upload.py <url1>" in captured.out
