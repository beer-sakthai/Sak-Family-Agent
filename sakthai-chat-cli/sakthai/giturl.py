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
_HELPER_TRANSPORT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*::")


def validate_git_url(url: str) -> str:
    """Return ``url`` stripped, or raise :class:`ValueError` if it is unsafe.

    Rejects empty values, values starting with ``-`` (option smuggling),
    remote-helper transports (``ext::…`` runs arbitrary commands), and URL
    schemes outside http(s)/ssh/git/file. scp-style ``user@host:path``
    addresses and local filesystem paths are allowed.
    """
    candidate = url.strip()
    if not candidate:
        raise ValueError("git URL must be a non-empty string")
    if candidate.startswith("-"):
        raise ValueError(f"git URL must not start with '-': {candidate!r}")
    if _HELPER_TRANSPORT_RE.match(candidate):
        raise ValueError(f"git remote-helper transport URLs are not allowed: {candidate!r}")
    if "://" in candidate:
        scheme = candidate.split("://", 1)[0].lower()
        if scheme not in _ALLOWED_SCHEMES:
            raise ValueError(f"unsupported git URL scheme {scheme!r}: {candidate!r}")
    return candidate
