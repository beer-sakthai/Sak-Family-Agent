import importlib.util
import socket
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Dynamically import run_asset_monitor.py from .github/workflows
REPO_ROOT = Path(__file__).parent.parent
workflow_path = REPO_ROOT / ".github" / "workflows" / "run_asset_monitor.py"

spec = importlib.util.spec_from_file_location("run_asset_monitor", workflow_path)
assert spec is not None and spec.loader is not None
run_asset_monitor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = run_asset_monitor
spec.loader.exec_module(run_asset_monitor)
is_safe_url = run_asset_monitor.is_safe_url
verify_url = run_asset_monitor.verify_url


def test_is_safe_url_valid():
    # Test safe, valid public domains
    with patch("socket.getaddrinfo") as mock_getaddrinfo:
        # Mocking resolution of example.com to a public IP
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", 443))
        ]
        is_safe, host, port, ip = is_safe_url("https://example.com")
        assert is_safe is True
        assert host == "example.com"
        assert port == 443
        assert ip == "93.184.216.34"


def test_is_safe_url_direct_public_ip():
    # Direct safe IPv4 address
    is_safe, host, port, ip = is_safe_url("https://8.8.8.8")
    assert is_safe is True
    assert host == "8.8.8.8"
    assert port == 443
    assert ip == "8.8.8.8"


def test_is_safe_url_invalid_schemes():
    # Invalid protocols must be blocked immediately
    for url in [
        "file:///etc/passwd",
        "gopher://localhost",
        "ftp://1.1.1.1",
        "data:text/plain,hello",
    ]:
        is_safe, _, _, _ = is_safe_url(url)
        assert is_safe is False


def test_is_safe_url_loopback_and_private():
    # Loopback and private IPs should be blocked
    for url in [
        "http://127.0.0.1",
        "http://[::1]",
        "https://10.0.0.1",
        "http://192.168.1.100",
        "https://172.16.5.5",
        "http://169.254.169.254",
        "http://0.0.0.0",
    ]:
        is_safe, _, _, _ = is_safe_url(url)
        assert is_safe is False


def test_is_safe_url_malicious_hostname_resolution():
    # Hostname resolving to private/loopback IP should be blocked
    with patch("socket.getaddrinfo") as mock_getaddrinfo:
        # Mocking resolution to localhost
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 80))
        ]
        is_safe, _, _, _ = is_safe_url("http://malicious-domain.local")
        assert is_safe is False


def test_is_safe_url_resolution_failure():
    with patch("socket.getaddrinfo", side_effect=socket.gaierror("Name or service not known")):
        is_safe, _, _, _ = is_safe_url("http://nonexistent-domain-xyz.com")
        assert is_safe is False


@patch("subprocess.run")
def test_verify_url_safe(mock_run):
    # Mock subprocess.run for a successful HTTP response
    mock_res = MagicMock()
    mock_res.stdout = "200"
    mock_run.return_value = mock_res

    with patch("socket.getaddrinfo") as mock_getaddrinfo:
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", 443))
        ]
        assert verify_url("https://example.com", "Example") is True

        # Check that curl was called with safe options and pinned resolution
        called_args = mock_run.call_args[0][0]
        assert "curl" in called_args
        assert "--proto" in called_args
        assert "-all,http,https" in called_args
        assert "--resolve" in called_args
        assert "example.com:443:93.184.216.34" in called_args


@patch("subprocess.run")
def test_verify_url_unsafe_blocked(mock_run):
    # If the URL resolves to localhost, subprocess.run should never be called
    with patch("socket.getaddrinfo") as mock_getaddrinfo:
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 80))
        ]
        assert verify_url("http://localhost-or-private", "Target") is False
        mock_run.assert_not_called()
