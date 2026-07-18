"""Tool execution guardrails to enforce safety and policy.

This module provides a ``GuardrailPolicy`` class that can be used to check
tool calls before and after execution against a set of configurable rules.
This allows for centralized policy enforcement, such as preventing dangerous
shell commands or blocking tools based on runtime configuration.

The design is based on Phase 3 of the plan in ``PLAN.md``.
"""

from __future__ import annotations

import contextlib
import fnmatch
import json
import logging
import os
import re
import shlex
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..config import SECRET_PATTERN
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


def _block_run_command_if_not_allowed(
    tool: Tool, _args: dict[str, Any], _store: MemoryStore
) -> GuardrailResult:
    """Deny the `run_command` tool if SAKTHAI_SHELL_ALLOW is not set."""
    if tool.name == "run_command" and not os.environ.get("SAKTHAI_SHELL_ALLOW"):
        return GuardrailResult(
            GuardrailAction.DENY,
            reason="Tool 'run_command' is disabled. Set SAKTHAI_SHELL_ALLOW to enable it.",
        )
    return GuardrailResult(GuardrailAction.ALLOW)


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
    ".bashrc",
    ".zshrc",
    ".profile",
    ".bash_profile",
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
}

# Private-key stems whose backup/rename variants (id_rsa.bak, id_ed25519.old,
# id_rsa.pem, …) carry the same key material and must also be blocked.
_SENSITIVE_KEY_STEMS = {
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
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


def _basename_is_sensitive(basename: str) -> bool:
    """Return True if a path basename names a sensitive file.

    Comparison is case-insensitive so that differently-cased references
    (``.AWS``, ``id_RSA``) on case-insensitive filesystems are still caught.
    Private-key stems match their backup/rename suffixes (``id_rsa.bak``).
    """
    lowered = basename.casefold()
    if lowered in _SENSITIVE_BASENAMES or any(
        lowered.startswith(p) for p in (".env.", "memory.db-")
    ):
        return True
    return any(lowered == stem or lowered.startswith(stem + ".") for stem in _SENSITIVE_KEY_STEMS)


def _is_sensitive_path(path: str, allow_local: bool = False) -> bool:
    """Return True if the path targets a sensitive system directory or uses traversal."""
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
    if ".." in path or path.startswith("~"):
        return True

    # Block access to known sensitive files and directories.
    normalized = os.path.normpath(path)
    parts = normalized.split(os.sep)
    basename = os.path.basename(normalized)

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
                for root in _CRITICAL_ROOTS:
                    if root.startswith(base_path):
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
        return any(normalized == c or normalized.startswith(c + "/") for c in _CRITICAL_ROOTS)
    return False


def _check_destructive_tokens(parts: list[str], context_sensitive: bool = False) -> GuardrailResult:
    """Recursively check tokens for destructive commands.

    If ``context_sensitive`` is True, discovery placeholders like '{}' and '+'
    are treated as sensitive paths (used by find -exec to target the discovered
    files).
    """
    if not parts:
        return GuardrailResult(GuardrailAction.ALLOW)

    # 1. Handle nested commands in wrappers (recursion)
    for i, part in enumerate(parts):
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
                if _is_binary(parts[j], ("bash", "sh", "zsh", "dash")):
                    shell_idx = j
                    break
                break  # Not a flag and not a shell

            if shell_idx != -1:
                try:
                    nested = shlex.split(parts[i + 1])
                    res = _check_destructive_tokens(nested, context_sensitive=context_sensitive)
                    if res.action == GuardrailAction.DENY:
                        return res
                except ValueError:
                    pass

        # 1b. eval "..." or exec "..."
        if _is_binary(part, ("eval", "exec")):
            rest = parts[i + 1 :]
            # If the next token looks like a quoted command string, split it.
            if len(rest) == 1 and " " in rest[0]:
                with contextlib.suppress(ValueError):
                    rest = shlex.split(rest[0])
            res = _check_destructive_tokens(rest, context_sensitive=context_sensitive)
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
            interpreters_with_c = ("python", "node", "perl", "ruby", "php")
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
        "docker",
        "podman",
        "kubectl",
        "chroot",
        "nsenter",
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
        "docker",
        "podman",
        "kubectl",
        "chroot",
        "nsenter",
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
    )

    for i, part in enumerate(parts):
        is_dest = _is_binary(part, destructive_binaries)
        is_exfil = _is_binary(part, exfiltration_binaries)
        if is_dest or is_exfil:
            binary_name = os.path.basename(part)
            is_interpreter = _is_binary(part, interpreters)
            # Inspect tokens following the binary until a separator is hit.
            for subpart in parts[i + 1 :]:
                if subpart in (";", "&&", "||", "|"):
                    break
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
                if is_interpreter and re.search(
                    r"(?:/etc|/root|/bin|/sbin|/usr|/var|/boot|/dev|/home|/sys|/proc|/tmp|/lib|/lib64)(?:/|$)|~|\.\.|"
                    + _SENSITIVE_NAME_RE,
                    subpart,
                ):
                    return GuardrailResult(
                        GuardrailAction.DENY,
                        reason=f"Potentially dangerous '{binary_name}' command with sensitive path in arguments blocked.",
                    )

    # 3. Specialized protection for dd (input/output file).
    for i, part in enumerate(parts):
        if _is_binary(part, "dd"):
            for subpart in parts[i + 1 :]:
                if subpart in (";", "&&", "||", "|"):
                    break
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
            if part in (";", "&&", "||", "|"):
                break
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
                if subpart in (";", "&&", "||", "|"):
                    break
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
                        if parts[k] in (";", "&&", "||", "|"):
                            break
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
        )
        if _is_binary(part, transparent_wrappers):
            # Most of these wrappers have flags. xargs and env are special.
            # We skip tokens that are likely arguments to the wrapper's flags.
            start_idx = i + 1
            while start_idx < len(parts) and parts[start_idx].startswith("-"):
                flag = parts[start_idx]
                if flag == "--":
                    start_idx += 1
                    break
                start_idx += 1
                # Skip the next token if this flag takes an argument.
                # This is a heuristic for common wrappers.
                if (
                    _is_binary(part, "timeout")
                    and flag in ("-s", "--signal", "-k", "--kill-after")
                    or _is_binary(part, "nice")
                    and flag in ("-n", "--adjustment")
                    or _is_binary(part, "ionice")
                    and flag in ("-c", "-n", "-p")
                    or _is_binary(part, "chrt")
                    and flag in ("-p")
                    or _is_binary(part, "taskset")
                    and flag in ("-p", "-c")
                    or _is_binary(part, "stdbuf")
                    and flag in ("-i", "-o", "-e")
                    or _is_binary(part, "nsenter")
                    and flag in ("-t", "--target", "-S", "--setuid", "-G", "--setgid")
                    or _is_binary(part, ("sudo", "doas"))
                    and flag
                    in (
                        "-u",
                        "-g",
                        "-p",
                        "-D",
                        "-R",
                        "-T",
                    )
                ):
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

            res = _check_destructive_tokens(parts[start_idx:], context_sensitive=context_sensitive)
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

            res = _check_destructive_tokens(exec_args, context_sensitive=targets_sensitive)
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
    if tool.name != "run_command":
        return GuardrailResult(GuardrailAction.ALLOW)

    command = args.get("command", "")
    if not isinstance(command, str):
        return GuardrailResult(GuardrailAction.ALLOW)

    try:
        parts = shlex.split(command)
    except ValueError:
        return GuardrailResult(GuardrailAction.DENY, reason="Malformed shell command.")

    return _check_destructive_tokens(parts)


def _enforce_verbose_listing(
    tool: Tool, args: dict[str, Any], _store: MemoryStore
) -> GuardrailResult:
    """If `run_command` is used for `ls`, enforce the `-l` flag."""
    if tool.name == "run_command" and isinstance(args.get("command"), str):
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
        if _is_sensitive_path(val, allow_local=True):
            return val
        if val.strip().startswith(("{", "[")):
            with contextlib.suppress(Exception):
                decoded = json.loads(val)
                if decoded != val:
                    res = _contains_sensitive_path(decoded)
                    if res is not None:
                        return res
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
    # run_command has its own specialized (and recursive) guardrails.
    if tool.name == "run_command":
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
    if re.search(SECRET_PATTERN, output):
        return GuardrailResult(
            GuardrailAction.DENY,
            reason="Tool output blocked because it appears to contain a secret.",
        )
    return GuardrailResult(GuardrailAction.ALLOW)


# Default set of rules to check *before* a tool is executed.
DEFAULT_PRE_RULES: list[PreGuardrailRule] = [
    _block_run_command_if_not_allowed,
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


DEFAULT_POLICY = GuardrailPolicy()
