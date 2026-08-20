"""Tests for sakthai.giturl — user-supplied git URL validation."""

from __future__ import annotations

import pytest

from sakthai.giturl import validate_git_url


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/user/repo.git",
        "http://internal.host/repo.git",
        "ssh://git@github.com/user/repo.git",
        "git://example.com/repo.git",
        "file:///srv/git/repo.git",
        "git@github.com:user/repo.git",  # scp-style
        "/srv/git/local-repo",  # plain absolute path
        "../sibling/repo",  # plain relative path
        "ssh://[::1]/repo.git",  # IPv6 host must not trip the helper check
    ],
)
def test_accepts_safe_urls(url: str) -> None:
    assert validate_git_url(url) == url


def test_strips_surrounding_whitespace() -> None:
    assert validate_git_url("  https://example.com/repo.git ") == "https://example.com/repo.git"


@pytest.mark.parametrize("url", ["", "   "])
def test_rejects_empty(url: str) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        validate_git_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "-oProxyCommand=evil",
        "--upload-pack=touch /tmp/pwned",
    ],
)
def test_rejects_option_smuggling(url: str) -> None:
    with pytest.raises(ValueError, match="start with '-'"):
        validate_git_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "ext::sh -c 'touch /tmp/pwned'",
        "fd::17",
    ],
)
def test_rejects_remote_helper_transports(url: str) -> None:
    with pytest.raises(ValueError, match="remote-helper"):
        validate_git_url(url)


@pytest.mark.parametrize("url", ["ftp://example.com/repo.git", "gopher://example.com/repo"])
def test_rejects_unknown_schemes(url: str) -> None:
    with pytest.raises(ValueError, match="unsupported git URL scheme"):
        validate_git_url(url)
