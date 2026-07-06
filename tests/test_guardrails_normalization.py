import pytest

from sakthai.agent.guardrails import _is_sensitive_path


@pytest.mark.parametrize(
    "path",
    [
        "/etc",
        "/etc/passwd",
        "//etc/passwd",
        "/bin/sh",
        "//bin/sh",
        "/usr/local/bin",
        "//usr/local/bin",
        "/var/log",
        "//var/log",
        "/.",
        "/./",
        "//",
        "///",
        "/etc/./passwd",
        "/etc//passwd",
    ],
)
def test_is_sensitive_path_normalization(path):
    """Verify that redundant slashes and dots cannot bypass the sensitive path check."""
    assert _is_sensitive_path(path), f"Path {path} should be considered sensitive"
