"""Validation for user-supplied git remote/clone URLs.

Git accepts more than plain URLs: remote-helper transports such as
``ext::sh -c ...`` execute arbitrary commands on fetch/clone, and a value
beginning with ``-`` can be parsed as an option by subcommands invoked
without a ``--`` separator. Every user-supplied URL handed to a git
subprocess (memory sync remotes, extension clone URLs) goes through
:func:`validate_git_url` first.
"""

from __future__ import annotations

import re

_ALLOWED_SCHEMES = frozenset({"http", "https", "ssh", "git", "file"})

# A remote-helper transport prefix: ``<helper>::<address>`` (e.g. ``ext::``,
# ``fd::``). The two colons must be consecutive, so ``ssh://host`` and
# scp-style ``user@host:path`` addresses do not match.
_HELPER_TRANSPORT_RE = re.compile(r"^[A-Za-z0-9+._-]+::")


def validate_git_url(url: str) -> str:
    """Return ``url`` stripped, or raise :class:`ValueError` if it is unsafe.

    Rejects empty values, values starting with ``-`` (option smuggling),
    remote-helper transports (``ext::…`` runs arbitrary commands), URL
    schemes outside http(s)/ssh/git/file, and control characters (such as
    newlines, carriage returns, tabs, and null bytes). scp-style
    ``user@host:path`` addresses and local filesystem paths are allowed.
    ASCII control characters, remote-helper transports (``ext::…`` runs
    arbitrary commands), option-smuggling host arguments, and URL schemes
    outside http(s)/ssh/git/file. scp-style ``user@host:path`` addresses and
    local filesystem paths are allowed.
    """
    candidate = url.strip()
    if not candidate:
        raise ValueError("git URL must be a non-empty string")
    if any(c in candidate for c in "\n\r\t\x00"):
        raise ValueError(f"git URL must not contain control characters: {candidate!r}")
    if any(ord(c) < 32 or ord(c) == 127 for c in candidate):
        raise ValueError(f"git URL contains invalid control characters: {candidate!r}")
    if candidate.startswith("-"):
        raise ValueError(f"git URL must not start with '-': {candidate!r}")
    if "@-" in candidate:
        raise ValueError(f"git URL host must not start with '-': {candidate!r}")
    if _HELPER_TRANSPORT_RE.match(candidate):
        raise ValueError(f"git remote-helper transport URLs are not allowed: {candidate!r}")
    if "://" in candidate:
        scheme, rest = candidate.split("://", 1)
        scheme_lower = scheme.lower()
        if scheme_lower not in _ALLOWED_SCHEMES:
            raise ValueError(f"unsupported git URL scheme {scheme!r}: {candidate!r}")
        if rest.startswith("-"):
            raise ValueError(f"git URL target host must not start with '-': {candidate!r}")
    return candidate
