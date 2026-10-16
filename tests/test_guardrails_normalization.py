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


# ---------------------------------------------------------------------------
# Case folding and separator handling (regression)
#
# _is_sensitive_path documents case-insensitive matching "across separators".
# Two spellings escaped it:
#   * the final absolute critical-root check compared exactly, so '/ETC/hosts'
#     passed while its own relative form 'ETC/hosts' was blocked -- and on a
#     case-insensitive filesystem (macOS by default, Windows) both name the
#     same file;
#   * components were split on os.sep only, so a Windows-style
#     'home\.ssh\id_rsa' collapsed to a single component and neither the
#     directory nor the basename check could see it.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/ETC/hosts",
        "/Etc/hosts",
        "/eTc/HoStS",
        "/VAR/log/auth.log",
        "/ROOT/anything",
        "/PROC/self/environ",
        "/Proc/self/environ",
        "/USR/local/bin",
        "/Boot/grub",
        "/DEV/mem",
    ],
)
def test_critical_roots_match_case_insensitively(path):
    """An uppercase critical root resolves to the same file on macOS/Windows."""
    assert _is_sensitive_path(path), f"Path {path} should be considered sensitive"


@pytest.mark.parametrize(
    "path",
    [
        "home\\.ssh\\id_rsa",
        "home\\.aws\\credentials",
        "C:\\Users\\a\\.aws\\credentials",
        "\\Users\\a\\.ssh\\id_ed25519",
        ".ssh\\id_rsa",
        "some\\nested\\.gnupg\\secring.gpg",
        "project\\.env",
        "a\\.SSH\\ID_RSA",
    ],
)
def test_windows_separators_are_split(path):
    """A backslash-separated path is matched component-wise, like a POSIX one."""
    assert _is_sensitive_path(path), f"Path {path} should be considered sensitive"


@pytest.mark.parametrize(
    "path",
    [
        "notes/readme.md",
        "src/main.py",
        "build\\output\\app.exe",
        "docs\\guide.md",
        "/opt/app/config.yaml",
        "/srv/data/file.txt",
    ],
)
def test_ordinary_paths_stay_allowed(path):
    """Folding and splitting must not start blocking ordinary project paths."""
    assert not _is_sensitive_path(path, allow_local=True), f"Path {path} should be allowed"
