"""Tool execution guardrails to enforce safety and policy.

This module provides a ``GuardrailPolicy`` class that can be used to check
tool calls before and after execution against a set of configurable rules.
This allows for centralized policy enforcement, such as preventing dangerous
shell commands or blocking tools based on runtime configuration.

The design is based on Phase 3 of the plan in ``PLAN.md``.
"""

from __future__ import annotations

import fnmatch
import logging
import os
import re
import shlex
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..config import SECRET_PATTERN, mail_allowlist
from ..memory.store import MemoryStore
from .tools import Tool

logger = logging.getLogger(__name__)


class GuardrailAction(Enum):
    """The decision made by a guardrail rule."""

    ALLOW = "allow"
    DENY = "deny"


@dataclass
class GuardrailResult:
    """The result of a guardrail check."""

    action: GuardrailAction
    reason: str | None = None
    modified_args: dict[str, Any] | None = None


PreGuardrailRule = Callable[[Tool, dict[str, Any], MemoryStore], GuardrailResult]
PostGuardrailRule = Callable[[Tool, dict[str, Any], str, bool, MemoryStore], GuardrailResult]


#: Separator the MCP manager inserts between an external server's name and that
#: server's own tool name when merging its tools into the registry — see
#: ``mcp/manager.py``: ``client.as_tools(prefix=f"{spec.name}__")``.
_MCP_NAMESPACE_SEP = "__"


def effective_tool_name(name: str) -> str:
    """``name`` with any external-MCP server namespace stripped.

    Every rule below that keys off a specific tool keys off a *bare* built-in
    name: ``run_command``, ``send_outlook_mail``. But tools reaching the
    registry from an external MCP server are namespaced ``<server>__<tool>``,
    so a server named ``shell`` offering ``run_command`` arrives as
    ``shell__run_command`` — and against the raw name every one of those rules
    silently falls through to ALLOW.

    That was not theoretical. It meant an external shell tool was exempt from
    the ``SAKTHAI_SHELL_ALLOW`` opt-in *and* from the destructive-token and
    sensitive-path scanning in this module, while a sibling rule
    (``_block_sensitive_path_args``) exempts only the literal ``run_command``
    and so applied its *blunt* path check to the external tool instead — a
    strict inversion of the intent: the less precise rule fired and the more
    precise one did not.

    No built-in tool name contains a double underscore, so stripping one is
    unambiguous. The first separator is the split point, because the server
    name is the prefix; a tool name that itself contains ``__`` keeps it.

    **What this does and does not buy.** It makes an external tool that
    *presents itself as* a built-in get that built-in's treatment, which covers
    the realistic case: a genuine MCP shell server offering ``run_command``,
    previously ungated. It cannot secure external tools in general — a server
    offering the same capability under a name nothing matches (``shell__exec``)
    is still reached only by the generic rules. Name matching is a floor, not a
    boundary; the boundary is the server allow-list and ``spec.tools``.
    """
    head, sep, tail = name.partition(_MCP_NAMESPACE_SEP)
    return tail if sep and head and tail else name


def _base_name(tool: Tool) -> str:
    """The tool's name for rule-matching purposes. See `effective_tool_name`."""
    return effective_tool_name(tool.name)


def _block_run_command_if_not_allowed(
    tool: Tool, _args: dict[str, Any], _store: MemoryStore
) -> GuardrailResult:
    """Deny the `run_command` tool if SAKTHAI_SHELL_ALLOW is not set.

    Applies to an external MCP server's ``run_command`` too: the opt-in is the
    operator's consent to shell execution, and which process supplies the shell
    does not change what consent is being given.
    """
    if _base_name(tool) == "run_command" and not os.environ.get("SAKTHAI_SHELL_ALLOW"):
        return GuardrailResult(
            GuardrailAction.DENY,
            reason="Tool 'run_command' is disabled. Set SAKTHAI_SHELL_ALLOW to enable it.",
        )
    return GuardrailResult(GuardrailAction.ALLOW)


def _block_mail_to_unlisted_recipients(
    tool: Tool, args: dict[str, Any], _store: MemoryStore
) -> GuardrailResult:
    """Deny `send_outlook_mail` unless its recipient is in SAKTHAI_MAIL_ALLOW.

    The recipient comes from the model, so a prompt injection in an email,
    document or MCP result could otherwise mail private memory to anyone.
    Entries are full addresses or ``@domain``; unset denies every recipient.
    """
    if _base_name(tool) != "send_outlook_mail":
        return GuardrailResult(GuardrailAction.ALLOW)
    recipient = args.get("to")
    if not isinstance(recipient, str) or not recipient.strip():
        return GuardrailResult(GuardrailAction.ALLOW)  # the handler rejects it
    recipient = recipient.strip().lower()
    # The domain is read off the last '@', so 'evil@x.test,me@corp.example' would
    # pass an '@corp.example' entry while the handler hands the whole string to
    # Graph as one address. Only a single bare address is judged.
    if recipient.count("@") != 1 or re.search(r"[\s,;<>()\"]", recipient):
        return GuardrailResult(
            GuardrailAction.DENY,
            reason=f"Recipient {recipient!r} must be a single bare email address.",
        )
    allowed = mail_allowlist()
    domain = recipient.rpartition("@")[2]
    if recipient in allowed or (domain and f"@{domain}" in allowed):
        return GuardrailResult(GuardrailAction.ALLOW)
    hint = (
        "SAKTHAI_MAIL_ALLOW is not set, so no recipient is allowed."
        if not allowed
        else "Add the address or its @domain to SAKTHAI_MAIL_ALLOW to permit it."
    )
    return GuardrailResult(
        GuardrailAction.DENY,
        reason=f"Recipient {recipient!r} is not in the mail allow-list. {hint}",
    )


def _is_binary(part: str, names: str | tuple[str, ...]) -> bool:
    """Return True if part matches any of the given binary names (exactly or as path suffix).

    Handles versioned binaries (e.g. python3, python3.11) using regex matching.
    """
    if isinstance(names, str):
        names = (names,)

    basename = os.path.basename(part)
    for name in names:
        # Match exactly 'name' or 'name' followed by a version (e.g. python3, python3.11).
        pattern = rf"^{re.escape(name)}(?:[0-9]+(?:\.[0-9]+)*)?$"
        if re.match(pattern, basename):
            return True
    return False


# List of critical roots that should never be targeted by destructive commands.
_CRITICAL_ROOTS = {
    "/etc",
    "/bin",
    "/sbin",
    "/usr",
    "/var",
    "/root",
    "/boot",
    "/dev",
    "/home",
    "/sys",
    "/proc",
    "/tmp",  # nosec B108 — allowlisting the root path for protection, not for temp file creation
    "/lib",
    "/lib64",
}


# Known sensitive basenames (files) and directories that should be blocked even if relative.
_SENSITIVE_BASENAMES = {
    ".env",
    "memory.db",
    ".bash_history",
    ".zsh_history",
    ".python_history",
    ".history",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "known_hosts",
    "authorized_keys",
    "credentials",
    "credentials.json",
    "shadow",
    "passwd",
    "sudoers",
    "gshadow",
    "group",
    ".bashrc",
    ".zshrc",
    ".profile",
    ".bash_profile",
    ".gitconfig",
    ".zprofile",
    ".yarnrc",
    ".yarnrc.yml",
    ".git-credentials",
    ".node_repl_history",
    ".mysql_history",
    ".psql_history",
    ".sqlite_history",
    ".rediscli_history",
    ".mongo_history",
    ".pgpass",
    ".my.cnf",
}

_SENSITIVE_DIRS = {
    ".ssh",
    ".aws",
    ".git",
    ".jules",
    ".docker",
    ".kube",
    ".gnupg",
    ".config",
    ".npm",
    ".gcloud",
    ".azure",
}

# Private-key stems whose backup/rename variants (id_rsa.bak, id_ed25519.old,
# id_rsa.pem, …) carry the same key material and must also be blocked.
_SENSITIVE_KEY_STEMS = {
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_ecdsa_sk",
    "id_ed25519_sk",
    "id_xmss",
}


# Regex fragment matching the *start* of a path-like token that references a
# sensitive location, derived from the sets above so the interpreter-script
# scanner stays in sync with _is_sensitive_path. Longer alternatives first so
# the alternation is greedy where names overlap.
_SENSITIVE_NAME_RE = "|".join(
    re.escape(name)
    for name in sorted(
        _SENSITIVE_DIRS
        | _SENSITIVE_BASENAMES
        | _SENSITIVE_KEY_STEMS
        | {r.lstrip("/") for r in _CRITICAL_ROOTS},
        key=len,
        reverse=True,
    )
)
_SENSITIVE_MARKER_RE = "|".join([r"/", r"~", r"(?:\.\./)+", _SENSITIVE_NAME_RE])
_SENSITIVE_SCRIPT_PATH_RE = rf"(?:{_SENSITIVE_MARKER_RE})[a-zA-Z0-9\._/-]*"


def _split_path_components(path: str) -> list[str]:
    """Split ``path`` on both POSIX and Windows separators.

    ``os.sep`` alone is ``/`` on this interpreter, so a Windows-style reference
    such as ``home\\.ssh\\id_rsa`` collapsed into a single component and neither
    the ``.ssh`` directory check nor the ``id_rsa`` basename check could see it.
    Splitting on both separators regardless of host OS keeps the guard's
    matching "across separators" contract true for the Windows paths an agent
    can emit on any platform.
    """
    return re.split(r"[/\\]", path)


def _basename_is_sensitive(basename: str) -> bool:
    """Return True if a path basename names a sensitive file.

    Comparison is case-insensitive so that differently-cased references
    (``.AWS``, ``id_RSA``) on case-insensitive filesystems are still caught.
    Private-key stems match their backup/rename suffixes (``.bak``, etc.).
    """
    lowered = basename.casefold()
    if lowered in _SENSITIVE_BASENAMES or any(
        lowered.startswith(p) for p in (".env.", ".env-", ".env_", "memory.db-")
    ):
        return True
    return any(lowered == stem or lowered.startswith(stem + ".") for stem in _SENSITIVE_KEY_STEMS)


# A '..' that is a whole path component (bounded by a separator, whitespace or
# the string edge), and a '~' that starts a tilde-prefix (``~``, ``~/x``,
# ``~root/x``). Substring tests flagged ordinary text -- "Hmm... ok",
# "~approximately 5" -- so a free-text tool argument could not hold an ellipsis.
_TRAVERSAL_RE = re.compile(r"(?:^|[\s/\\])\.\.(?:[\s/\\]|$)")
_HOME_PREFIX_RE = re.compile(r"^~[A-Za-z0-9_.+-]*(?:[/\\]|$)")
_ATTACHED_TRAVERSAL_RE = re.compile(r"^-[^\s]*?\.\.(?:[/\\]|$)")


def _has_traversal_or_home(path: str) -> bool:
    """True if ``path`` climbs with ``..`` or starts at a home directory."""
    if _TRAVERSAL_RE.search(path) or _HOME_PREFIX_RE.match(path):
        return True
    # A short-option group with its value attached ('-o../x', '-sT../x') has no
    # separator before the '..', whatever the group's length.
    return (
        path.startswith("-")
        and not path.startswith("--")
        and bool(_ATTACHED_TRAVERSAL_RE.search(path))
    )


def _is_sensitive_path(path: str, allow_local: bool = False) -> bool:
    """Return True if the path targets a sensitive system directory or uses traversal."""
    path = path.strip(" \t\n\r\"'")
    # Support checking flags or arguments with values like --file=/etc, field=@.env,
    # socat's FILE:/etc/passwd, or comma-separated paths (--mount src=/etc,dst=/x).
    # Every delimited component is checked recursively. Note: we only recurse on
    # components that differ from the original, and for '@' we only consider it
    # a separator if it's not the first character (to distinguish it from a curl
    # @path prefix).
    for sep in ("=", "@", ":", ","):
        if sep in path:
            if sep == "@" and path.startswith("@"):
                continue
            for val in path.split(sep):
                if val and val != path and _is_sensitive_path(val, allow_local=allow_local):
                    return True

    # Strip curl-style file upload prefix if present at start.
    if path.startswith("@") and len(path) > 1:
        path = path[1:]

    # Check for path traversal or home-relative paths.
    if _has_traversal_or_home(path):
        return True

    # Block access to known sensitive files and directories.
    normalized = os.path.normpath(path)
    parts = _split_path_components(normalized)
    basename = parts[-1] if parts else ""

    if _basename_is_sensitive(basename):
        return True

    lowered_parts = {p.casefold() for p in parts}
    if any(d in lowered_parts for d in _SENSITIVE_DIRS):
        return True

    # Block relative paths targeting system roots (e.g. 'etc/passwd'): a
    # relative reference whose first component names a critical root is
    # treated like the absolute path it resolves to when cwd is '/'.
    # Exception: a bare single-component 'tmp' is a common safe local name
    # (discovery tools, project dirs), so only subpaths are blocked.
    if not normalized.startswith("/") and parts and parts[0]:
        first = "/" + parts[0].casefold()
        if first in _CRITICAL_ROOTS and not (
            first == "/tmp" and len(parts) == 1  # nosec B108
        ):
            return True

    if not allow_local and path in (".", "./"):
        return True

    # Support checking short flags with attached paths like -o/etc/passwd or -o~/key
    # This also catches cases like -xf/etc/shadow by searching for the first / or ~
    if path.startswith("-") and not path.startswith("--"):
        for i, char in enumerate(path):
            if char in ("/", "~"):
                val = path[i:]
                if _is_sensitive_path(val):
                    return True
                break

    # Strengthen check against shell wildcards (globbing).
    # If the path contains wildcards, we check if its prefix (before the first wildcard)
    # could target a sensitive directory.
    if any(c in path for c in "*?[]"):
        # Any wildcard component that could expand to a sensitive directory or
        # file name (e.g. '.a?s/credentials' -> '.aws/...') is treated as
        # sensitive, since the child shell performs the expansion.
        for component in os.path.normpath(path).split(os.sep):
            if not any(c in component for c in "*?[]"):
                continue
            folded = component.casefold()
            if any(fnmatch.fnmatch(name, folded) for name in _SENSITIVE_DIRS) or any(
                fnmatch.fnmatch(name, folded) for name in _SENSITIVE_BASENAMES
            ):
                return True

        # Strip trailing wildcards to check the base path.
        base_path = re.split(r"[*?\[\]]", path, maxsplit=1)[0]
        if base_path:
            # If base_path itself is sensitive, block.
            if _is_sensitive_path(base_path):
                return True
            # If base_path is a prefix of any critical root (e.g. /et matching /etc),
            # it is also potentially sensitive if it is not just "/".
            if base_path != "/":
                folded_base = base_path.casefold()
                for root in _CRITICAL_ROOTS:
                    if root.startswith(folded_base):
                        return True
        elif not allow_local:
            # If the path starts with a wildcard and local paths are not allowed,
            # block it as it could target anything in the current directory.
            return True

    # Normalize the path to collapse redundant slashes and dots.
    # Note: os.path.normpath preserves a leading '//' on some systems, so we
    # explicitly collapse it for comparison.
    normalized = os.path.normpath(path)
    if normalized.startswith("//") and not normalized.startswith("///"):
        normalized = normalized[1:]

    if normalized.startswith("/"):
        if normalized == "/":
            return True
        # Case-folded, like every other comparison here: on a case-insensitive
        # filesystem (macOS by default, Windows) '/ETC/hosts' and '/PROC/self/
        # environ' resolve to the same files as their lowercase spellings. The
        # relative-root check below already folded; leaving this one exact let
        # an absolute path through that its own relative form would have
        # blocked.
        folded = normalized.casefold()
        return any(folded == c or folded.startswith(c + "/") for c in _CRITICAL_ROOTS)
    return False


def _is_local_make_dir(path: str) -> bool:
    """True if ``path`` is an ordinary directory under the current working directory.

    ``_is_sensitive_path``'s final check blocks any absolute path nested under a
    broad critical root (``/home``, ``/var``, ...), which also matches every
    normal project checkout on a typical Linux box — including the cwd itself,
    since ``tempfile.mkdtemp(dir=".")`` returns an absolute path as of Python
    3.12. This narrower check exists only to rescue that case for the ``make -C``
    guardrail: a path resolving inside cwd is treated as local *unless* it (or
    one of its components) is itself a name ``_is_sensitive_path`` would flag
    regardless of location (``.ssh``, ``id_rsa``, etc.) or contains traversal.
    """
    if ".." in path:
        return False
    normalized = os.path.normpath(path)
    components = _split_path_components(normalized)
    if _basename_is_sensitive(components[-1] if components else ""):
        return False
    lowered_parts = {p.casefold() for p in components}
    if any(d in lowered_parts for d in _SENSITIVE_DIRS):
        return False

    abs_path = os.path.abspath(path)
    cwd = os.getcwd()
    return abs_path == cwd or abs_path.startswith(cwd + os.sep)


def _balanced_paren_end(text: str, start: int) -> tuple[int, int]:
    """Locate the ``)`` closing a ``$(`` whose body begins at ``start``.

    Follows the shell's own rules, so a ``)`` inside quotes, after a backslash or
    in a ``#`` comment does not end the body early (which would leave the real
    command outside it, unscanned), and a nested ``$(...)`` is skipped whole.

    Returns ``(body_end, resume)``: the body is ``text[start:body_end]`` and
    scanning resumes at ``resume``. An unterminated group runs to the end of the
    string, so its remainder is checked as the body rather than skipped.
    """
    depth = 1
    quote = ""
    word_start = True
    i, n = start, len(text)
    while i < n:
        ch = text[i]
        at_word_start, word_start = word_start, False
        if ch == "\\" and quote != "'":
            if text[i + 1 : i + 2] == "\n":
                # A line continuation is deleted before parsing: it must not
                # change whether the next character starts a word.
                word_start = at_word_start
            i += 2
        elif quote == "'":
            quote = "" if ch == "'" else quote
            i += 1
        elif ch == "$" and text.startswith("$(", i):
            _, i = _balanced_paren_end(text, i + 2)
        elif quote == '"':
            quote = "" if ch == '"' else quote
            i += 1
        elif ch in "'\"":
            quote = ch
            i += 1
        elif ch == "#" and at_word_start:
            newline = text.find("\n", i)
            i = n if newline == -1 else newline
        elif ch == "(":
            depth += 1
            word_start = True
            i += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i, i + 1
            i += 1
        else:
            word_start = ch in " \t\n;&|"
            i += 1
    return n, n


def _backtick_end(text: str, start: int) -> tuple[int, int]:
    """Like `_balanced_paren_end`, for a backtick opened before ``start``."""
    i = start
    while i < len(text):
        if text[i] == "\\":
            i += 2
        elif text[i] == "`":
            return i, i + 1
        else:
            i += 1
    return len(text), len(text)


def _scan_shell_structure(command: str) -> tuple[list[str], list[str]]:
    """Split a shell command into simple-command segments and substitution bodies.

    ``shlex.split`` does not treat ``;``, ``&`` or ``|`` as operators unless
    whitespace surrounds them, so ``echo hi;cat ~/.ssh/id_rsa`` reached the
    token checks as ``["echo", "hi;cat", ...]`` and no binary was recognized.
    It also leaves the body of ``$(...)`` and backticks inside one token, where
    nothing looked at it. This scanner honors quoting: it splits only on
    unquoted operators, and lifts substitution bodies out (they run even inside
    double quotes, never inside single quotes) leaving a ``SUBST`` placeholder.

    A ``&`` or ``|`` fused to a ``<``/``>`` (``2>&1``, ``>|``) or a ``&`` that
    precedes ``>`` (``&>``) is a redirection operator, not a separator, and
    stays in its segment so the redirection-target check still sees it.
    """
    segments: list[str] = []
    substitutions: list[str] = []
    current: list[str] = []
    quote = ""
    i, n = 0, len(command)

    def flush() -> None:
        text = "".join(current).strip()
        if text:
            segments.append(text)
        current.clear()

    while i < n:
        ch = command[i]
        if ch == "\\" and quote != "'":
            # '\<newline>' is deleted by the shell before it parses, so 'ca\<nl>t'
            # runs cat; shlex would instead see the word 'ca<nl>t'.
            if command[i + 1 : i + 2] != "\n":
                current.append(command[i : i + 2])
            i += 2
        elif quote == "'":
            current.append(ch)
            quote = "" if ch == "'" else quote
            i += 1
        elif ch == "$" and command.startswith("$(", i):
            body_end, resume = _balanced_paren_end(command, i + 2)
            substitutions.append(command[i + 2 : body_end])
            current.append("SUBST")
            i = resume
        elif ch == "`":
            body_end, resume = _backtick_end(command, i + 1)
            # Inside backticks '\`', '\$' and '\\' are unescaped before the body
            # runs, so a nested backtick substitution arrives escaped.
            substitutions.append(re.sub(r"\\([`$\\])", r"\1", command[i + 1 : body_end]))
            current.append("SUBST")
            i = resume
        elif quote == '"':
            current.append(ch)
            quote = "" if ch == '"' else quote
            i += 1
        elif ch in "'\"":
            quote = ch
            current.append(ch)
            i += 1
        elif ch in ";\n()":
            flush()
            i += 1
        elif ch in "&|":
            prev = command[i - 1] if i else ""
            fused = (prev != "" and prev in "<>") or (ch == "&" and command[i + 1 : i + 2] == ">")
            if fused:
                current.append(ch)
            else:
                flush()
            i += 1
        else:
            current.append(ch)
            i += 1
    flush()
    return segments, substitutions


def _check_command_string(
    command: str,
    *,
    posix: bool = True,
    shell_syntax: bool = True,
    context_sensitive: bool = False,
    checked_makefiles: set[str] | None = None,
    current_make_dir: str = ".",
) -> GuardrailResult:
    """Run the token checks over every segment and substitution of ``command``.

    With ``shell_syntax=False`` the string is one plain argv (no operators, no
    substitutions): that is how the built-in ``run_command`` runs it.
    """
    segments, substitutions = _scan_shell_structure(command) if shell_syntax else ([command], [])
    # Bodies first: a substitution is executed before the command around it.
    for body in substitutions:
        res = _check_command_string(
            body,
            posix=posix,
            context_sensitive=context_sensitive,
            checked_makefiles=checked_makefiles,
            current_make_dir=current_make_dir,
        )
        if res.action == GuardrailAction.DENY:
            return res
    for segment in segments:
        try:
            parts = shlex.split(segment, posix=posix)
        except ValueError:
            return GuardrailResult(GuardrailAction.DENY, reason="Malformed shell command.")
        res = _check_destructive_tokens(
            parts,
            context_sensitive=context_sensitive,
            checked_makefiles=checked_makefiles,
            current_make_dir=current_make_dir,
        )
        if res.action == GuardrailAction.DENY:
            return res
    return GuardrailResult(GuardrailAction.ALLOW)


def _check_destructive_tokens(
    parts: list[str],
    context_sensitive: bool = False,
    checked_makefiles: set[str] | None = None,
    current_make_dir: str = ".",
) -> GuardrailResult:
    """Recursively check tokens for destructive commands.

    If ``context_sensitive`` is True, discovery placeholders like '{}' and '+'
    are treated as sensitive paths (used by find -exec to target the discovered
    files).
    """
    if not parts:
        return GuardrailResult(GuardrailAction.ALLOW)

    # 1. Handle nested commands in wrappers (recursion)
    for i, part in enumerate(parts):
        # 1d. make command scanning Makefile recipes
        if _is_binary(part, "make"):
            make_dir = current_make_dir
            makefile_path = None

            idx = i + 1
            while idx < len(parts):
                arg = parts[idx]
                if arg in ("-C", "--directory") and idx + 1 < len(parts):
                    make_dir = parts[idx + 1]
                    idx += 2
                elif arg.startswith("-C"):
                    make_dir = arg[2:]
                    idx += 1
                elif arg in ("-f", "--file", "--makefile") and idx + 1 < len(parts):
                    makefile_path = parts[idx + 1]
                    idx += 2
                elif arg.startswith("-f"):
                    makefile_path = arg[2:]
                    idx += 1
                else:
                    idx += 1

            if _is_sensitive_path(make_dir, allow_local=True) and not _is_local_make_dir(make_dir):
                return GuardrailResult(
                    GuardrailAction.DENY,
                    reason=f"Potentially dangerous 'make' command in sensitive directory {make_dir!r} blocked.",
                )

            if not makefile_path:
                for name in ("GNUmakefile", "makefile", "Makefile"):
                    candidate = os.path.join(make_dir, name)
                    if os.path.isfile(candidate):
                        makefile_path = candidate
                        break
            else:
                if not os.path.isabs(makefile_path):
                    makefile_path = os.path.join(make_dir, makefile_path)

            if makefile_path:
                if checked_makefiles is None:
                    checked_makefiles = set()

                abs_makefile_path = os.path.abspath(makefile_path)
                if abs_makefile_path in checked_makefiles:
                    continue

                if _is_sensitive_path(makefile_path) and not _is_local_make_dir(makefile_path):
                    return GuardrailResult(
                        GuardrailAction.DENY,
                        reason=f"Potentially dangerous 'make' command on sensitive file {makefile_path!r} blocked.",
                    )
                if os.path.isfile(makefile_path):
                    new_checked = checked_makefiles | {abs_makefile_path}
                    try:
                        with open(makefile_path, encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        for match in re.finditer(_SENSITIVE_SCRIPT_PATH_RE, content):
                            candidate = match.group(0)
                            if _is_sensitive_path(candidate):
                                return GuardrailResult(
                                    GuardrailAction.DENY,
                                    reason=f"Potentially dangerous 'make' command loading makefile with sensitive path {candidate!r} blocked.",
                                )

                        for line in content.splitlines():
                            if line.startswith("\t"):
                                recipe = line.lstrip("\t").strip()
                                while recipe and recipe[0] in ("@", "-", "+"):
                                    recipe = recipe[1:].strip()
                                if recipe:
                                    res = _check_command_string(
                                        recipe,
                                        context_sensitive=context_sensitive,
                                        checked_makefiles=new_checked,
                                        current_make_dir=make_dir,
                                    )
                                    if res.action == GuardrailAction.DENY:
                                        return GuardrailResult(
                                            GuardrailAction.DENY,
                                            reason=f"Potentially destructive command in makefile recipe blocked: {res.reason}",
                                        )
                    except Exception:  # nosec B110 — safe swallow of makefile parsing/reading errors
                        pass

        # 1a. bash -c "..." or sh -c "..." (including combined flags like -xc)
        # Search backwards for the shell binary to handle intermediate flags (e.g. bash -v -c).
        if (
            part.startswith("-")
            and not part.startswith("--")
            and part.endswith("c")
            and i > 0
            and i + 1 < len(parts)
        ):
            shell_idx = -1
            for j in range(i - 1, -1, -1):
                if parts[j].startswith("-"):
                    continue
                if _is_binary(
                    parts[j], ("bash", "sh", "zsh", "dash", "ksh", "fish", "ash", "csh", "tcsh")
                ):
                    shell_idx = j
                    break
                break  # Not a flag and not a shell

            if shell_idx != -1:
                res = _check_command_string(
                    parts[i + 1],
                    context_sensitive=context_sensitive,
                    checked_makefiles=checked_makefiles,
                    current_make_dir=current_make_dir,
                )
                if res.action == GuardrailAction.DENY:
                    return res

        # 1b. eval "..." or exec "..."
        if _is_binary(part, ("eval", "exec")):
            rest = parts[i + 1 :]
            # eval joins its arguments and re-parses them as shell, so a quoted
            # command string is scanned for operators and substitutions too.
            if len(rest) == 1 and " " in rest[0]:
                res = _check_command_string(
                    rest[0],
                    context_sensitive=context_sensitive,
                    checked_makefiles=checked_makefiles,
                    current_make_dir=current_make_dir,
                )
            else:
                res = _check_destructive_tokens(
                    rest,
                    context_sensitive=context_sensitive,
                    checked_makefiles=checked_makefiles,
                    current_make_dir=current_make_dir,
                )
            if res.action == GuardrailAction.DENY:
                return res

        # 1c. interpreter -c "script" or interpreter -e "script" (including combined flags like -ic or -pe)
        # python -c "..." or node -e "..."
        # Search backwards for the interpreter binary to handle intermediate flags (e.g. python -v -c).
        if (
            part.startswith("-")
            and not part.startswith("--")
            and part.endswith(("c", "e", "r", "p", "E"))
            and i > 0
            and i + 1 < len(parts)
        ):
            interp_idx = -1
            interpreters_with_c = ("python", "node", "perl", "ruby", "php", "tsx", "ts-node")
            for j in range(i - 1, -1, -1):
                if parts[j].startswith("-"):
                    continue
                if _is_binary(parts[j], interpreters_with_c):
                    interp_idx = j
                    break
                break

            if interp_idx != -1:
                script = parts[i + 1]
                # Scan script for absolute or home-relative paths (including traversal)
                # or any known sensitive file/directory referenced relatively
                # (.env, .git, .ssh, .aws, id_rsa, memory.db, ...).
                for match in re.finditer(_SENSITIVE_SCRIPT_PATH_RE, script):
                    candidate = match.group(0)
                    if _is_sensitive_path(candidate):
                        binary_name = os.path.basename(parts[interp_idx])
                        return GuardrailResult(
                            GuardrailAction.DENY,
                            reason=f"Potentially dangerous {binary_name!r} script targeting {candidate!r} blocked.",
                        )

    # 2. Prevent destructive or dangerous commands on sensitive paths.
    destructive_binaries = (
        "rm",
        "rmdir",
        "chmod",
        "mv",
        "cp",
        "ln",
        "tee",
        "chown",
        "chgrp",
        "sed",
        "truncate",
        "shred",
        "openssl",
        "socat",
        "ssh-keygen",
        "ssh-copy-id",
        "mkdir",
        "touch",
        "git",
        "npm",
        "yarn",
        "pnpm",
        "pip",
        "pip3",
        "sqlite",
        "docker",
        "podman",
        "kubectl",
        "chroot",
        "nsenter",
        "uv",
        "pipx",
        "bun",
        "bunx",
        "tsx",
        "ts-node",
        "deno",
        "npx",
        "poetry",
        "pipenv",
        "conda",
        "busybox",
        "toybox",
        "psql",
        "mysql",
        "mariadb",
        "mongo",
        "mongosh",
        "redis-cli",
        "vim",
        "vi",
        "nano",
        "emacs",
        "ed",
        "composer",
        "cargo",
    )
    exfiltration_binaries = (
        "curl",
        "wget",
        "dir",
        "vdir",
        "openssl",
        "socat",
        "cat",
        "grep",
        "head",
        "tail",
        "strings",
        "base64",
        "awk",
        "nc",
        "netcat",
        "python",
        "node",
        "perl",
        "ruby",
        "php",
        "more",
        "less",
        "hexdump",
        "od",
        "sort",
        "diff",
        "tar",
        "rsync",
        "zip",
        "unzip",
        "7z",
        "scp",
        "sftp",
        "ssh",
        "ssh-add",
        "ssh-keygen",
        "ssh-copy-id",
        "bash",
        "sh",
        "zsh",
        "dash",
        "ksh",
        "fish",
        "ash",
        "csh",
        "tcsh",
        "ls",
        "uniq",
        "cut",
        "file",
        "stat",
        "tac",
        "rev",
        "nl",
        "xxd",
        "column",
        "gzip",
        "gunzip",
        "zcat",
        "xz",
        "xzcat",
        "bzip2",
        "bzcat",
        "jq",
        "paste",
        "join",
        "split",
        "git",
        "npm",
        "yarn",
        "pnpm",
        "pip",
        "pip3",
        "sqlite",
        "docker",
        "podman",
        "kubectl",
        "chroot",
        "nsenter",
        "uv",
        "pipx",
        "bun",
        "bunx",
        "tsx",
        "ts-node",
        "deno",
        "npx",
        "poetry",
        "pipenv",
        "conda",
        "busybox",
        "toybox",
        "psql",
        "mysql",
        "mariadb",
        "mongo",
        "mongosh",
        "redis-cli",
        "vim",
        "vi",
        "nano",
        "emacs",
        "ed",
        "composer",
        "cargo",
    )
    # Common interpreters where sensitive paths can be embedded in arguments.
    interpreters = (
        "python",
        "node",
        "awk",
        "perl",
        "ruby",
        "php",
        "sed",
        "grep",
        "bash",
        "sh",
        "zsh",
        "dash",
        "ksh",
        "fish",
        "ash",
        "csh",
        "tcsh",
        "sqlite",
        "git",
        "tsx",
        "ts-node",
        "deno",
        "psql",
        "mysql",
        "mariadb",
        "mongo",
        "mongosh",
        "redis-cli",
        "vim",
        "vi",
        "emacs",
        "composer",
        "cargo",
    )

    for i, part in enumerate(parts):
        is_dest = _is_binary(part, destructive_binaries)
        is_exfil = _is_binary(part, exfiltration_binaries)
        if is_dest or is_exfil:
            binary_name = os.path.basename(part)
            is_interpreter = _is_binary(part, interpreters)
            # Inspect tokens following the binary until a separator is hit.
            for subpart in parts[i + 1 :]:
                # For destructive binaries, we don't allow targeting the current directory.
                # For exfiltration binaries, we allow targeting the current directory.
                allow_local = is_exfil
                if _is_sensitive_path(subpart, allow_local=allow_local) or (
                    context_sensitive and subpart in ("{}", "+")
                ):
                    return GuardrailResult(
                        GuardrailAction.DENY,
                        reason=f"Potentially dangerous '{binary_name}' command on {subpart!r} blocked."
                        if not is_dest
                        else f"Potentially destructive '{binary_name}' command on {subpart!r} blocked.",
                    )
                if is_interpreter:
                    has_sensitive = False
                    for match in re.finditer(_SENSITIVE_SCRIPT_PATH_RE, subpart):
                        candidate = match.group(0)
                        if _is_sensitive_path(candidate):
                            has_sensitive = True
                            break
                    if has_sensitive:
                        return GuardrailResult(
                            GuardrailAction.DENY,
                            reason=f"Potentially dangerous '{binary_name}' command with sensitive path in arguments blocked.",
                        )

    # 3. Specialized protection for dd (input/output file).
    for i, part in enumerate(parts):
        if _is_binary(part, "dd"):
            for subpart in parts[i + 1 :]:
                if subpart.startswith("of=") or subpart.startswith("if="):
                    val = subpart[3:]
                    # of= targets are destructive; don't allow local path.
                    # if= targets are potentially dangerous; allow local path.
                    allow_local = subpart.startswith("if=")
                    if _is_sensitive_path(val, allow_local=allow_local) or (
                        context_sensitive and val in ("{}", "+")
                    ):
                        binary_name = os.path.basename(part)
                        op = "destructive" if subpart.startswith("of=") else "potentially dangerous"
                        return GuardrailResult(
                            GuardrailAction.DENY,
                            reason=f"{op} {binary_name!r} on {val!r} blocked.",
                        )

    # 4. Prevent shell redirections targeting sensitive paths.
    for i, part in enumerate(parts):
        # We look for redirection operators (>, >>, 1>, 2>, &>, >&, >|, <, etc.)
        # Pattern: optional digit or '&', then '&>>', '>>', '>&', '>|', '<>', '<&', '>', or '<'
        # Note: longer operators must come before shorter ones to match correctly.
        r_match = re.search(r"(?:[0-9]|&)?(?:&>>|>>|>&|>\||<>|<&|>|<)", part)
        if r_match:
            # If the operator is at the end of the token or attached to its front,
            # we need to find the target path.
            target = part[r_match.end() :]
            if not target and i + 1 < len(parts):
                target = parts[i + 1]

            if target and (
                _is_sensitive_path(target) or (context_sensitive and target in ("{}", "+"))
            ):
                return GuardrailResult(
                    GuardrailAction.DENY,
                    reason=f"destructive redirection to {target!r} blocked.",
                )

    # 5. Specialized protection for find (discovery, -delete, -fprint).
    find_idx = -1
    for i, part in enumerate(parts):
        if _is_binary(part, "find"):
            find_idx = i
            break
    if find_idx != -1:
        after_find = parts[find_idx + 1 :]

        # 5a. Block destructive file-writing variants (-fprint, etc.)
        for i, part in enumerate(after_find):
            if part in ("-fprint", "-fprint0", "-fls", "-fprintf") and i + 1 < len(after_find):
                target = after_find[i + 1]
                if _is_sensitive_path(target, allow_local=False) or (
                    context_sensitive and target in ("{}", "+")
                ):
                    return GuardrailResult(
                        GuardrailAction.DENY,
                        reason=f"destructive 'find {part}' on {target!r} blocked.",
                    )

        # 5b. Block destructive deletion (-delete) on sensitive paths.
        if "-delete" in after_find:
            for part in after_find:
                if part.startswith("-"):
                    continue
                if _is_sensitive_path(part, allow_local=False) or (
                    context_sensitive and part in ("{}", "+")
                ):
                    return GuardrailResult(
                        GuardrailAction.DENY,
                        reason=f"destructive 'find -delete' on {part!r} blocked.",
                    )

        # 5c. Block unauthorized discovery of sensitive system roots.
        # find [path...] [expression]
        for part in after_find:
            if part.startswith("-"):
                continue
            if _is_sensitive_path(part, allow_local=True):
                return GuardrailResult(
                    GuardrailAction.DENY,
                    reason=f"Potentially dangerous 'find' command on {part!r} blocked.",
                )

    # 6. Specialized protection for container tools (docker, podman, kubectl).
    for i, part in enumerate(parts):
        if _is_binary(part, ("docker", "podman", "kubectl")):
            binary_name = os.path.basename(part)
            for j, subpart in enumerate(parts[i + 1 :], i + 1):
                # Check for volume mounts in docker/podman: -v /etc:/mnt or --mount type=bind,source=/etc,...
                if subpart == "-v" or subpart == "--volume":
                    if j + 1 < len(parts):
                        val = parts[j + 1]
                        if _is_sensitive_path(val):
                            return GuardrailResult(
                                GuardrailAction.DENY,
                                reason=f"potentially dangerous {binary_name!r} volume mount targeting {val!r} blocked.",
                            )
                elif subpart.startswith("-v=") or subpart.startswith("--volume="):
                    val = subpart.split("=", 1)[1]
                    if _is_sensitive_path(val):
                        return GuardrailResult(
                            GuardrailAction.DENY,
                            reason=f"potentially dangerous {binary_name!r} volume mount targeting {val!r} blocked.",
                        )
                elif subpart.startswith("--mount"):
                    val = subpart
                    if "=" not in val and j + 1 < len(parts):
                        val = parts[j + 1]
                    # --mount type=bind,source=/etc,target=/mnt
                    if "source=" in val:
                        source_val = val.split("source=", 1)[1].split(",", 1)[0]
                        if _is_sensitive_path(source_val):
                            return GuardrailResult(
                                GuardrailAction.DENY,
                                reason=f"potentially dangerous {binary_name!r} mount source {source_val!r} blocked.",
                            )
                    elif "src=" in val:
                        source_val = val.split("src=", 1)[1].split(",", 1)[0]
                        if _is_sensitive_path(source_val):
                            return GuardrailResult(
                                GuardrailAction.DENY,
                                reason=f"potentially dangerous {binary_name!r} mount source {source_val!r} blocked.",
                            )

                # cp copies files between host and container/pod
                # (docker cp, podman cp, kubectl cp).
                if subpart == "cp":
                    for k in range(j + 1, len(parts)):
                        if _is_sensitive_path(parts[k]):
                            return GuardrailResult(
                                GuardrailAction.DENY,
                                reason=f"potentially dangerous '{binary_name} cp' on {parts[k]!r} blocked.",
                            )

    # 7. Handle wrappers that don't use -c (sudo, doas, xargs, env, find -exec, timeout, etc.)
    for i, part in enumerate(parts):
        # sudo command ... or doas command ... or xargs command ... or env [VAR=VAL] command ...
        transparent_wrappers = (
            "sudo",
            "doas",
            "xargs",
            "env",
            "timeout",
            "nohup",
            "setsid",
            "nice",
            "ionice",
            "chrt",
            "taskset",
            "stdbuf",
            "chroot",
            "nsenter",
            "unshare",
            "pkexec",
            "uv",
            "pipx",
            "bun",
            "bunx",
            "npx",
            "deno",
            "poetry",
            "pipenv",
            "conda",
            "pnpm",
            "yarn",
            "npm",
            "cargo",
            "composer",
            "busybox",
            "toybox",
        )
        if _is_binary(part, transparent_wrappers):
            # Most of these wrappers have flags. xargs and env are special.
            # We skip tokens that are likely arguments to the wrapper's flags.
            start_idx = i + 1

            # If the wrapper is uv, pipx, bun, deno, poetry, pipenv, conda, pnpm, yarn, npm, cargo, or composer, we want to look for subcommands.
            if _is_binary(
                part,
                (
                    "uv",
                    "pipx",
                    "bun",
                    "deno",
                    "poetry",
                    "pipenv",
                    "conda",
                    "pnpm",
                    "yarn",
                    "npm",
                    "cargo",
                    "composer",
                ),
            ):
                run_idx = -1
                for idx in range(i + 1, len(parts)):
                    if parts[idx] in ("run", "eval", "exec", "node"):
                        run_idx = idx
                        break
                if run_idx == -1:
                    continue
                # If bun eval or deno eval is found, recursively scan the script argument for sensitive paths
                if (
                    parts[run_idx] == "eval"
                    and run_idx + 1 < len(parts)
                    and _is_binary(part, ("bun", "deno"))
                ):
                    script = parts[run_idx + 1]
                    for match in re.finditer(_SENSITIVE_SCRIPT_PATH_RE, script):
                        candidate = match.group(0)
                        if _is_sensitive_path(candidate):
                            binary_name = os.path.basename(part)
                            return GuardrailResult(
                                GuardrailAction.DENY,
                                reason=f"Potentially dangerous {binary_name!r} eval script targeting {candidate!r} blocked.",
                            )
                start_idx = run_idx + 1

            while start_idx < len(parts) and parts[start_idx].startswith("-"):
                flag = parts[start_idx]
                if flag == "--":
                    start_idx += 1
                    break

                flag_name = flag
                flag_val = None
                if "=" in flag:
                    flag_name, flag_val = flag.split("=", 1)

                start_idx += 1
                # Skip the next token if this flag takes an argument.
                # This is a heuristic for common wrappers.
                if (
                    _is_binary(part, "timeout")
                    and flag_name in ("-s", "--signal", "-k", "--kill-after")
                    or _is_binary(part, "nice")
                    and flag_name in ("-n", "--adjustment")
                    or _is_binary(part, "ionice")
                    and flag_name in ("-c", "-n", "-p")
                    or _is_binary(part, "chrt")
                    and flag_name in ("-p")
                    or _is_binary(part, "taskset")
                    and flag_name in ("-p", "-c")
                    or _is_binary(part, "stdbuf")
                    and flag_name in ("-i", "-o", "-e")
                    or _is_binary(part, "nsenter")
                    and flag_name in ("-t", "--target", "-S", "--setuid", "-G", "--setgid")
                    or _is_binary(part, "unshare")
                    and flag_name
                    in (
                        "-S",
                        "--setuid",
                        "-G",
                        "--setgid",
                        "--map-user",
                        "--map-group",
                        "--map-users",
                        "--map-groups",
                        "--root",
                        "--wd",
                        "--mount-proc",
                    )
                    or _is_binary(part, "pkexec")
                    and flag_name in ("--user", "-u")
                    or _is_binary(part, ("sudo", "doas"))
                    and flag_name
                    in (
                        "-u",
                        "-g",
                        "-p",
                        "-D",
                        "-R",
                        "-T",
                    )
                    or _is_binary(part, "uv")
                    and flag_name
                    in (
                        "--with",
                        "-p",
                        "--package",
                        "-m",
                        "--module",
                        "--python",
                        "--env-file",
                        "--directory",
                        "-C",
                        "--project",
                        "--settings",
                    )
                    or _is_binary(part, "pipx")
                    and flag_name in ("--spec", "--index-url", "--pip-args", "--python")
                    or _is_binary(part, "bun")
                    and flag_name
                    in ("--cwd", "--env-file", "-c", "--config", "-e", "--entry-point")
                    or _is_binary(part, "bunx")
                    and flag_name in ("-p", "--package", "--cwd", "--env-file")
                    or _is_binary(part, "npx")
                    and flag_name in ("-p", "--package")
                    or _is_binary(part, "deno")
                    and flag_name
                    in ("-c", "--config", "-p", "--port", "--import-map", "--lock", "--ext")
                    or _is_binary(part, "conda")
                    and flag in ("-n", "--name", "-p", "--prefix", "--cwd")
                    or _is_binary(part, "pnpm")
                    and flag in ("--filter", "-c", "--dir", "--config")
                    or _is_binary(part, "yarn")
                    and flag in ("--cwd",)
                    or _is_binary(part, "poetry")
                    and flag in ("-C", "--directory")
                    or _is_binary(part, "npm")
                    and flag in ("--prefix", "--dir")
                    or _is_binary(part, "cargo")
                    and flag in ("--manifest-path", "--target-dir")
                    or _is_binary(part, "composer")
                    and flag in ("--working-dir", "-d")
                ):
                    if flag_val is not None:
                        if (
                            _is_binary(part, "unshare")
                            and flag_name in ("--root", "--wd", "--mount-proc")
                            and _is_sensitive_path(flag_val, allow_local=True)
                        ):
                            binary_name = os.path.basename(part)
                            return GuardrailResult(
                                GuardrailAction.DENY,
                                reason=f"potentially dangerous '{binary_name} {flag_name}' on {flag_val!r} blocked.",
                            )
                    else:
                        if (
                            _is_binary(part, "unshare")
                            and flag_name in ("--root", "--wd", "--mount-proc")
                            and start_idx < len(parts)
                        ):
                            arg_val = parts[start_idx]
                            if _is_sensitive_path(arg_val, allow_local=True):
                                binary_name = os.path.basename(part)
                                return GuardrailResult(
                                    GuardrailAction.DENY,
                                    reason=f"potentially dangerous '{binary_name} {flag_name}' on {arg_val!r} blocked.",
                                )
                        start_idx += 1

            # env might have arguments like VAR=VAL before the command.
            if _is_binary(part, "env"):
                while start_idx < len(parts) and "=" in parts[start_idx]:
                    start_idx += 1

            # timeout has a duration argument that is NOT a flag.
            if (
                _is_binary(part, "timeout")
                and start_idx < len(parts)
                and not parts[start_idx].startswith("-")
            ):
                start_idx += 1

            # chroot has the NEWROOT argument that is NOT a flag.
            if (
                _is_binary(part, "chroot")
                and start_idx < len(parts)
                and not parts[start_idx].startswith("-")
            ):
                # The NEWROOT itself might be sensitive (e.g. chroot /etc).
                if _is_sensitive_path(parts[start_idx], allow_local=True):
                    return GuardrailResult(
                        GuardrailAction.DENY,
                        reason=f"potentially dangerous 'chroot' on {parts[start_idx]!r} blocked.",
                    )
                start_idx += 1

            res = _check_destructive_tokens(
                parts[start_idx:],
                context_sensitive=context_sensitive,
                checked_makefiles=checked_makefiles,
                current_make_dir=current_make_dir,
            )
            if res.action == GuardrailAction.DENY:
                return res
        # find ... -exec/ok command ...
        if part in ("-exec", "-execdir", "-ok", "-okdir") and any(
            _is_binary(p, "find") for p in parts[:i]
        ):
            # We don't filter out {} and + here anymore because we want the
            # recursive scanner to see them if they are being used destructively.
            # We still stop at the terminator.
            exec_args: list[str] = []
            for subpart in parts[i + 1 :]:
                if subpart in ("\\;", ";", "+"):
                    if subpart == "+":
                        exec_args.append(subpart)
                    break
                exec_args.append(subpart)

            # Heuristic: if find's target is sensitive, set context_sensitive.
            targets_sensitive = False
            # Search for find targets (tokens starting find's search) between find and -exec.
            for p in parts[find_idx + 1 : i]:
                if p.startswith("-"):
                    continue
                # For find's targets, we allow local path unless it's destructive.
                if _is_sensitive_path(p, allow_local=True):
                    targets_sensitive = True
                    break

            res = _check_destructive_tokens(
                exec_args,
                context_sensitive=targets_sensitive,
                checked_makefiles=checked_makefiles,
                current_make_dir=current_make_dir,
            )
            if res.action == GuardrailAction.DENY:
                if targets_sensitive:
                    # Specific reason for find-exec when target is sensitive.
                    binary_name = os.path.basename(part)
                    return GuardrailResult(
                        GuardrailAction.DENY,
                        reason=f"destructive 'find {binary_name}' on sensitive path blocked.",
                    )
                return res

    return GuardrailResult(GuardrailAction.ALLOW)


def _block_dangerous_shell_commands(
    tool: Tool, args: dict[str, Any], _store: MemoryStore
) -> GuardrailResult:
    """Deny `run_command` if it contains a potentially destructive command."""
    if _base_name(tool) != "run_command":
        return GuardrailResult(GuardrailAction.ALLOW)

    command = args.get("command", "")
    if not isinstance(command, str):
        return GuardrailResult(GuardrailAction.ALLOW)

    # The built-in run_command execs the argv with shell=False, so ';' and
    # '$(...)' are literal text there; only an external '<server>__run_command'
    # is assumed to hand the string to a shell. Shell-interpreted strings inside
    # a command (a 'sh -c' script, a makefile recipe) are scanned either way.
    shell_syntax = tool.name != _base_name(tool)
    result = _check_command_string(command, shell_syntax=shell_syntax)
    if result.action == GuardrailAction.DENY or "\\" not in command:
        return result

    # A parser differential: shlex's POSIX mode consumes backslashes as escapes,
    # so a Windows-style path ('cat C:\Users\me\.aws\credentials') arrives here
    # as 'C:Usersme.awscredentials' -- unrecognizable as a path -- while cmd.exe
    # and PowerShell would read the real file. Re-scan with the backslashes
    # preserved. Gated on the command containing one, so every backslash-free
    # command keeps its existing behavior exactly.
    return _check_command_string(command, posix=False, shell_syntax=shell_syntax)


def _enforce_verbose_listing(
    tool: Tool, args: dict[str, Any], _store: MemoryStore
) -> GuardrailResult:
    """If `run_command` is used for `ls`, enforce the `-l` flag."""
    if _base_name(tool) == "run_command" and isinstance(args.get("command"), str):
        command = args["command"]
        if command.strip() == "ls" or (command.startswith("ls ") and "-l" not in command):
            modified_args = args.copy()
            modified_args["command"] = command.replace("ls", "ls -l", 1)
            return GuardrailResult(GuardrailAction.ALLOW, modified_args=modified_args)
    return GuardrailResult(GuardrailAction.ALLOW)


def _contains_sensitive_path(val: Any) -> str | None:
    """Recursively scan nested data structures for sensitive paths.

    Returns the sensitive path if found, or None.
    """
    if isinstance(val, str):
        stripped = val.strip()
        if stripped.startswith(("{", "[")):
            import contextlib
            import json

            with contextlib.suppress(Exception):
                parsed = json.loads(stripped)
                if isinstance(parsed, (list, tuple, set, dict)):
                    res_json = _contains_sensitive_path(parsed)
                    if res_json is not None:
                        return res_json
        if _is_sensitive_path(val, allow_local=True):
            return val
    elif isinstance(val, (list, tuple, set)):
        for item in val:
            res = _contains_sensitive_path(item)
            if res is not None:
                return res
    elif isinstance(val, dict):
        for k, v in val.items():
            res_key = _contains_sensitive_path(k)
            if res_key is not None:
                return res_key
            res_val = _contains_sensitive_path(v)
            if res_val is not None:
                return res_val
    return None


def _block_sensitive_path_args(
    tool: Tool, args: dict[str, Any], _store: MemoryStore
) -> GuardrailResult:
    """Deny any tool call that targets a sensitive path via its arguments."""
    # run_command has its own specialized (and recursive) guardrails. Normalized
    # so an external `<server>__run_command` is routed to those rules rather
    # than being handed this blunter one instead of them.
    if _base_name(tool) == "run_command":
        return GuardrailResult(GuardrailAction.ALLOW)

    for key, value in args.items():
        sensitive_path = _contains_sensitive_path(value)
        if sensitive_path is not None:
            return GuardrailResult(
                GuardrailAction.DENY,
                reason=f"Access to sensitive path {sensitive_path!r} via argument {key!r} is blocked.",
            )
    return GuardrailResult(GuardrailAction.ALLOW)


def _block_output_with_secrets(
    _tool: Tool,
    _args: dict[str, Any],
    output: str,
    _is_error: bool,
    _store: MemoryStore,
) -> GuardrailResult:
    """Deny any tool output that appears to contain a secret."""
    # 1. Block common secret patterns (API keys, bot tokens, etc.)
    if re.search(SECRET_PATTERN, output):
        return GuardrailResult(
            GuardrailAction.DENY,
            reason="Tool output blocked because it appears to contain a secret.",
        )

    # 2. Block PEM Private Key blocks
    if re.search(
        r"-----BEGIN[A-Z0-9\s_]+PRIVATE KEY-----[\s\S]*?-----END[A-Z0-9\s_]+PRIVATE KEY-----",
        output,
    ):
        return GuardrailResult(
            GuardrailAction.DENY,
            reason="Tool output blocked because it appears to contain a private key block.",
        )

    # 3. Block exact active environment credentials or registered extra secrets
    secret_keys = [
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
        "SAKTHAI_GATEWAY_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "HF_TOKEN",
        "COMPOSIO_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "GITHUB_TOKEN",
        "GITHUB_PAT",
        "STRIPE_API_KEY",
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_API_KEY",
        "MS_GRAPH_CLIENT_SECRET",
        "MS_GRAPH_REFRESH_TOKEN",
        "MSGRAPH_CLIENT_SECRET",
    ]
    secrets_to_check = set()
    try:
        from ..config import _EXTRA_SECRETS

        for s in _EXTRA_SECRETS:
            if isinstance(s, str) and len(s) > 5:
                secrets_to_check.add(s)
    except Exception:  # nosec B110 — safe swallow of configuration error
        pass

    try:
        import os

        for key in secret_keys:
            val = os.environ.get(key)
            if isinstance(val, str) and len(val) > 5:
                secrets_to_check.add(val)
    except Exception:  # nosec B110 — safe swallow of environment variable reading error
        pass

    if secrets_to_check:
        for val in sorted(secrets_to_check, key=len, reverse=True):
            if val in output:
                return GuardrailResult(
                    GuardrailAction.DENY,
                    reason="Tool output blocked because it appears to contain a secret.",
                )

    return GuardrailResult(GuardrailAction.ALLOW)


# Default set of rules to check *before* a tool is executed.
DEFAULT_PRE_RULES: list[PreGuardrailRule] = [
    _block_run_command_if_not_allowed,
    _block_mail_to_unlisted_recipients,
    _block_dangerous_shell_commands,
    _block_sensitive_path_args,
    _enforce_verbose_listing,
]

# Default set of rules to check *after* a tool is executed.
# (No default post-rules for now, but the structure is here).
DEFAULT_POST_RULES: list[PostGuardrailRule] = [
    _block_output_with_secrets,
]


@dataclass
class GuardrailPolicy:
    """A policy that enforces guardrails on tool execution."""

    pre_rules: Sequence[PreGuardrailRule] = field(default_factory=lambda: DEFAULT_PRE_RULES)
    post_rules: Sequence[PostGuardrailRule] = field(default_factory=lambda: DEFAULT_POST_RULES)

    def check_pre_execution(
        self, tool: Tool, args: dict[str, Any], store: MemoryStore
    ) -> GuardrailResult:
        """Check if a tool call is allowed before execution."""
        current_args = args
        for rule in self.pre_rules:
            result = rule(tool, current_args, store)
            if result.action == GuardrailAction.DENY:
                logger.warning(
                    "Guardrail denied pre-execution of tool %r: %s",
                    tool.name,
                    result.reason,
                )
                return result
            if result.modified_args is not None:
                current_args = result.modified_args

        # If any rule modified the args, return the final state.
        if current_args is not args:
            return GuardrailResult(GuardrailAction.ALLOW, modified_args=current_args)

        return GuardrailResult(GuardrailAction.ALLOW)

    def check_post_execution(
        self,
        tool: Tool,
        args: dict[str, Any],
        output: str,
        is_error: bool,
        store: MemoryStore,
    ) -> GuardrailResult:
        """Check if a tool's output is allowed after execution."""
        for rule in self.post_rules:
            result = rule(tool, args, output, is_error, store)
            if result.action == GuardrailAction.DENY:
                logger.warning(
                    "Guardrail denied post-execution of tool %r: %s",
                    tool.name,
                    result.reason,
                )
                return result
        return GuardrailResult(GuardrailAction.ALLOW)


_LOCAL_PATH_PATTERN = re.compile(
    r"(?:/home/(?:antigravity|sak|ubuntu|root)|/(?:root|etc|var/run|var/log)/[a-zA-Z0-9_\-\./]+)"
)
_PRIVATE_IP_PATTERN = re.compile(
    r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|127\.\d{1,3}\.\d{1,3}\.\d{1,3})\b"
)
_INJECTION_KEYWORDS = [
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"system\s+prompt",
    r"developer\s+mode",
    r"jailbreak",
    r"forget\s+everything",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_KEYWORDS), re.IGNORECASE)


def scan_content_for_leaks(text: str) -> list[str]:
    """Scan content for potential secret, filesystem path, or network leaks."""
    leaks: list[str] = []
    if _LOCAL_PATH_PATTERN.search(text):
        leaks.append("Detected local filesystem path in content.")
    if re.search(SECRET_PATTERN, text):
        leaks.append("Detected secret key pattern in content.")
    if _PRIVATE_IP_PATTERN.search(text):
        leaks.append("Detected private IP address in content.")
    return leaks


def sanitize_external_content(text: str) -> str:
    """Sanitize untrusted external quotes or social replies against prompt injection."""
    if not text:
        return ""
    # Defang common injection phrases
    sanitized = _INJECTION_RE.sub("[DEFANGED_PROMPT_INJECTION]", text)
    # Wrap in explicit untrusted data container
    return f"[UNTRUSTED_CONTENT]\n{sanitized}\n[/UNTRUSTED_CONTENT]"


DEFAULT_POLICY = GuardrailPolicy()
