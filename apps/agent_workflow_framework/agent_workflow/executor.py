"""Asynchronous execution engine and action handlers for agent_workflow.

Provides WorkflowExecutor to run DAG workflow definitions with parallel task scheduling,
state interpolation, step retries, downstream failure short-circuiting, and action handlers.
"""

import ast
import asyncio
import copy
import json
import os
import shlex
import sys
import time
import types
import unicodedata
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Set

from agent_workflow.dag import validate_workflow_dag, build_topological_batches
from agent_workflow.models import (
    WorkflowDefinition,
    StepDefinition,
    StepResult,
    StepStatus,
    RunHistory,
    RunStatus,
)
from agent_workflow.persistence import RunHistoryStore
from agent_workflow.state import StateContext, StateInterpolationError


class ExecutionError(Exception):
    """Base exception for workflow execution failures."""
    pass


# str.format and str.format_map resolve attribute paths written inside the
# format string, which the AST validator cannot see. See the check in the
# python action for the escape this closes.
_FORMAT_METHODS = frozenset({"format", "format_map"})


class _SafeJSON:
    """Serialisation-only stand-in for the ``json`` module in the python sandbox.

    The sandbox used to place the real ``json`` module into its globals as a
    convenience. That single object defeated the entire builtins blocklist: a
    module's own imports are plain, non-dunder attributes, so the AST dunder
    rule never sees them and attribute traversal walks straight out of the
    sandbox. Every one of these reached full RCE without naming a dunder or a
    blocked builtin::

        json.codecs.builtins.open('/etc/passwd').read()
        json.codecs.sys.modules['os'].popen('id').read()
        json.decoder.re.enum.bltns.open(...)      # independent route to builtins
        json.decoder.re.enum.sys.modules[...]     # independent route to sys

    Patching names off the module is whack-a-mole (there are at least four
    disjoint routes to ``builtins``/``sys`` through ``codecs``, ``re`` and
    ``enum``). The fix is to not expose a module at all: this facade carries
    only the two serialisation functions workflows actually use. Their
    ``__globals__`` would lead back to the module namespace, but that is a
    dunder and so is already blocked by the AST validator.

    ``dump``/``load`` are deliberately absent: they take file objects, which a
    sandbox with no ``open`` cannot produce.
    """

    __slots__ = ()

    dumps = staticmethod(json.dumps)
    loads = staticmethod(json.loads)


def _assert_no_modules(namespace: Dict[str, Any], where: str) -> None:
    """Fail closed if a module object ever reaches the python sandbox.

    Defence in depth for the escape described on :class:`_SafeJSON`. Any module
    in the sandbox namespace is an escape route, because module attributes are
    non-dunder and therefore invisible to the AST validator. This makes that
    class of mistake fail loudly at execution time rather than silently
    reopening the sandbox.

    Containers are searched too, not just top-level values: the AST validator
    only inspects attribute and *name* nodes, so a module nested one subscript
    deep (``params['a']['inner'].system(...)``) would be reached without the
    expression ever naming a dunder. No action currently returns a container
    holding a module, so this is not a live hole — but a top-level-only check
    would not be the guarantee this function's name implies.
    """

    def _walk(value: Any, path: str, seen: Set[int]) -> None:
        if isinstance(value, types.ModuleType):
            raise PermissionError(
                f"Module '{value.__name__}' exposed as '{path}' in {where} is "
                "not permitted in the python sandbox."
            )
        # Cycle guard: workflow params are plain data, but they are not
        # guaranteed acyclic, and this must not be the thing that hangs a run.
        if id(value) in seen:
            return
        if isinstance(value, dict):
            seen.add(id(value))
            for key, item in value.items():
                _walk(item, f"{path}[{key!r}]", seen)
        elif isinstance(value, (list, tuple, set, frozenset)):
            seen.add(id(value))
            for index, item in enumerate(value):
                _walk(item, f"{path}[{index}]", seen)

    for name, value in namespace.items():
        _walk(value, name, set())


def _validate_url(url_str: str) -> None:
    """SSRF Protection & URL Validation.

    Raises ValueError or RuntimeError if the URL is invalid, uses a forbidden
    scheme, or resolves to a private/non-global/multicast IP address.
    """
    url_str = str(url_str).strip()
    if url_str.startswith("-"):
        raise ValueError(f"Option smuggling detected in URL: {url_str}")

    if any(ord(c) < 32 or ord(c) == 127 for c in url_str):
        raise ValueError("Control characters are not allowed in URLs")

    # Strip URL fragment identifiers (#...) prior to URL parsing and DNS resolution
    # to prevent fragment-based host/path parser confusion or SSRF bypasses.
    if "#" in url_str:
        url_str = url_str.split("#", 1)[0]

    try:
        parsed = urllib.parse.urlparse(url_str)
    except Exception as e:
        raise ValueError(f"Invalid URL: {url_str}. Error: {e}")

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise ValueError(f"Forbidden URL scheme '{scheme}'. Only HTTP and HTTPS are allowed.")

    if parsed.username or parsed.password or "@" in (parsed.netloc or ""):
        raise ValueError("Userinfo (username/password) credentials in URLs are prohibited")

    if "\\" in (parsed.netloc or ""):
        raise ValueError("Backslash characters are not allowed in URL authority component")

    host = parsed.hostname
    if not host:
        raise ValueError(f"URL missing hostname: {url_str}")

    port = parsed.port
    if not port:
        port = 443 if scheme == "https" else 80

    try:
        import socket
        import ipaddress
        addrinfos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        for _family, _type, _proto, _canon, sockaddr in addrinfos:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                continue

            if getattr(ip, "ipv4_mapped", None):
                ip = ip.ipv4_mapped

            if (
                not ip.is_global
                or ip.is_multicast
                or ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
            ):
                raise ValueError(
                    f"SSRF Protection Blocked: Host '{host}' resolved to non-public/private IP: {ip_str}"
                )
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"DNS Resolution failed for host '{host}': {e}")


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """A custom redirect handler that validates target URLs against SSRF before following them."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> Optional[urllib.request.Request]:
        _validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _validate_filepath(filepath: Any) -> Path:
    """Validate a filepath to prevent path traversal and access to sensitive/system directories/files."""
    if not filepath:
        raise ValueError("File path cannot be empty.")

    path_str = str(filepath).strip().lstrip("@")
    if not path_str:
        raise ValueError("File path cannot be empty.")

    if any(ord(c) < 32 or ord(c) == 127 for c in path_str):
        raise ValueError("Control characters are not allowed in file paths")

    # Block path traversal segments like '..' or leading '~'. Backslashes are
    # normalized first so Windows-style separators can't smuggle a '..' segment
    # past a POSIX-only split.
    normalized_str = path_str.replace("\\", "/")
    if (
        ".." in path_str.split(os.sep)
        or ".." in normalized_str.split("/")
        or path_str.startswith("~")
    ):
        raise PermissionError(f"Directory path traversal or user home shortcut is prohibited: '{path_str}'")

    # Critical system roots (e.g., /etc, /bin, /var, /boot, /dev, /lib, /lib64, /proc, /sys, /sbin, /usr)
    system_roots = {
        "etc", "bin", "var", "boot", "dev", "lib", "lib64", "proc", "sys", "sbin", "usr", "root", "opt",
    }

    # Block relative paths targeting system roots (e.g., 'etc/hosts', 'var/log/syslog').
    # Exception: a bare single-component 'tmp' is allowed as a common safe local name.
    if not (path_str.startswith("/") or path_str.startswith("\\")):
        rel_parts = [p.lower() for p in Path(normalized_str).parts if p]
        if rel_parts:
            first_component = rel_parts[0]
            if first_component in system_roots and not (first_component == "tmp" and len(rel_parts) == 1):
                raise PermissionError(f"Access to critical system directory is prohibited: '{path_str}'")

    # Blocks access to sensitive directories (e.g., .git, .ssh, .aws)
    sensitive_dirs = {
        ".git", ".ssh", ".aws", ".jules", ".config", ".npm",
        ".docker", ".kube", ".gnupg", ".gcloud", ".azure",
    }

    # Blocks access to credential/sensitive file basenames (e.g., .env, memory.db, id_rsa)
    sensitive_basenames = {
        ".env", "memory.db", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "id_ecdsa_sk", "id_ed25519_sk", "id_xmss",
        "known_hosts", "authorized_keys", "credentials", "credentials.json", "shadow", "passwd", "sudoers",
        ".bash_history", ".zsh_history", ".python_history", ".history", ".netrc", ".npmrc", ".pypirc",
        "gshadow", "group", ".bashrc", ".zshrc", ".profile", ".bash_profile", ".gitconfig", ".zprofile",
        ".yarnrc", ".yarnrc.yml", ".git-credentials", ".node_repl_history", ".mysql_history", ".psql_history",
        ".sqlite_history", ".rediscli_history", ".mongo_history", ".pgpass", ".my.cnf"
    }
    sensitive_suffixes = (".pem", ".key", ".pfx", ".p12")

    # Prefix variants: .env.production / .env-prod / .env_local, and the SQLite
    # sidecars memory.db-wal / memory.db-shm / memory.db-journal.
    sensitive_prefixes = (".env.", ".env-", ".env_", "memory.db-")

    # Renamed or backed-up private keys (id_rsa.bak, id_ed25519.pub, ...).
    sensitive_key_stems = (
        "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "id_ecdsa_sk", "id_ed25519_sk", "id_xmss",
    )

    # Check for wildcards (globbing)
    if any(c in path_str for c in "*?[]"):
        import fnmatch
        import re

        # Split normalized path to check each component
        parts = [p.lower() for p in Path(path_str).parts]

        # 1. Check if any wildcard component could expand to a sensitive directory or file
        for part in parts:
            if any(c in part for c in "*?[]"):
                # Check match against sensitive directories
                if any(fnmatch.fnmatch(s_dir, part) for s_dir in sensitive_dirs):
                    raise PermissionError(f"Access to sensitive directory via wildcards is prohibited: '{path_str}'")

                # Check match against sensitive basenames, prefixes, suffixes, key stems
                test_targets = set(sensitive_basenames)
                for prefix in sensitive_prefixes:
                    test_targets.add(f"{prefix}test")
                for suffix in sensitive_suffixes:
                    test_targets.add(f"test{suffix}")
                for stem in sensitive_key_stems:
                    test_targets.add(f"{stem}.test")

                if any(fnmatch.fnmatch(target, part) for target in test_targets):
                    raise PermissionError(f"Access to sensitive file via wildcards is prohibited: '{path_str}'")

        # 2. Strip trailing wildcards to check the base path prefix
        base_path = re.split(r"[*?\[\]]", path_str, maxsplit=1)[0]
        if base_path:
            # If base_path has traversal, block
            if ".." in base_path.split(os.sep) or ".." in base_path.replace("\\", "/").split("/"):
                raise PermissionError(f"Directory path traversal is prohibited: '{path_str}'")

            # If the base_path resolves or starts with a system root
            if base_path.startswith("/") or base_path.startswith("\\"):
                normalized_base = base_path.replace("\\", "/").lower()
                if normalized_base == "/":
                    raise PermissionError(f"Access to root directory via wildcards is prohibited: '{path_str}'")
                for root in system_roots:
                    if f"/{root}".startswith(normalized_base) or normalized_base.startswith(f"/{root}/"):
                        raise PermissionError(f"Access to critical system directory via wildcards is prohibited: '{path_str}'")
            else:
                # Relative path: check if first component is a system root or matches system root prefix
                base_parts = [p.lower() for p in Path(base_path.replace("\\", "/")).parts if p]
                if base_parts:
                    first = base_parts[0]
                    for root in system_roots:
                        if root.startswith(first) or first.startswith(root):
                            raise PermissionError(f"Access to critical system directory via wildcards is prohibited: '{path_str}'")

    # Resolve target absolute to Path
    try:
        target = Path(path_str).resolve()
    except Exception as exc:
        raise ValueError(f"Invalid file path '{path_str}': {exc}")

    parts = [p.lower() for p in target.parts]

    if target.is_absolute():
        root_part = target.anchor
        non_root_parts = [p for p in target.parts if p != root_part]
        if non_root_parts:
            first_dir = non_root_parts[0].lower()
            if first_dir in system_roots:
                raise PermissionError(f"Access to critical system directory is prohibited: '{path_str}'")

    if any(part in sensitive_dirs for part in parts):
        raise PermissionError(f"Access to sensitive directory is prohibited: '{path_str}'")

    filename = target.name.lower()

    if (
        filename in sensitive_basenames
        or filename.startswith(sensitive_prefixes)
        or filename.endswith(sensitive_suffixes)
        or any(filename.startswith(stem + ".") for stem in sensitive_key_stems)
    ):
        raise PermissionError(f"Access to sensitive file is prohibited: '{path_str}'")

    return target


def _extract_shell_subcommands(cmd_str: str) -> List[str]:
    """Extract individual subcommands from a shell command string by splitting on
    command separators (;, &&, ||, \\n, \\r) and extracting command substitutions
    ($(...) and `...`).
    """
    subcommands: List[str] = []

    def _parse(text: str) -> None:
        text = text.strip()
        if not text:
            return

        current_cmd = []
        i = 0
        n = len(text)
        in_single_quote = False
        in_double_quote = False
        escaped = False

        while i < n:
            char = text[i]

            if escaped:
                current_cmd.append(char)
                escaped = False
                i += 1
                continue

            if char == "\\" and not in_single_quote:
                escaped = True
                current_cmd.append(char)
                i += 1
                continue

            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
                current_cmd.append(char)
                i += 1
                continue

            if char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                current_cmd.append(char)
                i += 1
                continue

            if not in_single_quote:
                # Check for command substitution $(...) and process substitution <(...) or >(...)
                import re
                ps_match = re.match(r"^(\$\(|[<>]\s*\()", text[i:])
                if ps_match:
                    prefix_len = ps_match.end()
                    depth = 1
                    j = i + prefix_len
                    sub_escaped = False
                    sub_sq = False
                    sub_dq = False
                    while j < n and depth > 0:
                        c = text[j]
                        if sub_escaped:
                            sub_escaped = False
                        elif c == "\\" and not sub_sq:
                            sub_escaped = True
                        elif c == "'" and not sub_dq:
                            sub_sq = not sub_sq
                        elif c == '"' and not sub_sq:
                            sub_dq = not sub_sq
                        elif not sub_sq and not sub_dq:
                            if c == "(":
                                depth += 1
                            elif c == ")":
                                depth -= 1
                        if depth > 0:
                            j += 1
                    inner = text[i+prefix_len:j]
                    if inner.strip():
                        _parse(inner)
                    current_cmd.append(text[i:j+1])
                    i = j + 1
                    continue

                # Check for backtick command substitution `...`
                if char == "`":
                    j = i + 1
                    sub_escaped = False
                    while j < n:
                        c = text[j]
                        if sub_escaped:
                            sub_escaped = False
                        elif c == "\\":
                            sub_escaped = True
                        elif c == "`":
                            break
                        j += 1
                    inner = text[i+1:j]
                    if inner.strip():
                        _parse(inner)
                    current_cmd.append(text[i:j+1])
                    i = j + 1
                    continue

            if not in_single_quote and not in_double_quote:
                # Check for separators: &&, ||, ;, \n, \r
                if text[i:i+2] in ("&&", "||"):
                    cmd = "".join(current_cmd).strip()
                    if cmd:
                        subcommands.append(cmd)
                    current_cmd = []
                    i += 2
                    continue
                elif char in (";", "\n", "\r"):
                    cmd = "".join(current_cmd).strip()
                    if cmd:
                        subcommands.append(cmd)
                    current_cmd = []
                    i += 1
                    continue

            current_cmd.append(char)
            i += 1

        cmd = "".join(current_cmd).strip()
        if cmd:
            subcommands.append(cmd)

    _parse(cmd_str)
    return subcommands or [cmd_str]


def _validate_shell_command(cmd_str: str) -> None:
    """Validate a shell command to prevent access to sensitive/system paths."""
    import shlex
    import re

    def _check_token(token: str) -> None:
        token = token.strip()
        if not token:
            return

        # Replace backslashes with forward slashes for cross-platform consistency
        normalized = token.replace("\\", "/")

        # Split on any character that is not a valid path character (A-Z, a-z, 0-9, dot, underscore, slash, tilde, hyphen, wildcards)
        # to extract potential paths embedded in options, lists, scripts, or arguments.
        sub_tokens = re.split(r"[^a-zA-Z0-9\._/~\-\*\?\[\]]", normalized)
        for sub in sub_tokens:
            sub = sub.strip()
            if not sub:
                continue
            # Strip curl-style upload prefix if present
            if sub.startswith("@"):
                sub = sub.lstrip("@")

            try:
                _validate_filepath(sub)
            except PermissionError as exc:
                raise PermissionError(f"Prohibited sensitive path in shell command: {exc}") from exc
            except (ValueError, OSError):
                # Not path-shaped (empty, control chars, unreadable) — nothing to
                # validate. PermissionError, the actual finding, is re-raised above;
                # any other exception is unexpected and deliberately propagates.
                pass

    subcommands = _extract_shell_subcommands(str(cmd_str))

    for subcmd in subcommands:
        cmd_str_stripped = subcmd.strip()
        if not cmd_str_stripped:
            continue

        # 1. Prevent pipeline-to-interpreter command execution bypasses (e.g. curl ... | sh or curl ... |& bash)
        if "|" in cmd_str_stripped:
            segments = re.split(r"\|&?", cmd_str_stripped)
            for segment in segments[1:]:
                segment = segment.strip(" \t\n\r\"'()$&;")
                if segment:
                    try:
                        words = shlex.split(segment)
                    except Exception:
                        words = segment.split()

                    # Robust helper to find the actual executable command by unwrapping environment variables,
                    # flags, and common transparent wrappers (including shell/system/package wrappers).
                    wrappers = {
                        "env", "sudo", "doas", "xargs", "timeout", "nohup", "setsid", "nice",
                        "ionice", "chrt", "taskset", "stdbuf", "chroot", "nsenter", "unshare",
                        "pkexec", "uv", "pipx", "bun", "bunx", "npx", "deno", "poetry",
                        "pipenv", "conda", "pnpm", "yarn", "npm", "cargo", "composer",
                        "busybox", "toybox", "builtin", "command",
                    }

                    interpreters = (
                        "sh",
                        "bash",
                        "zsh",
                        "dash",
                        "ksh",
                        "fish",
                        "ash",
                        "csh",
                        "tcsh",
                        "python",
                        "node",
                        "perl",
                        "ruby",
                        "php",
                        "deno",
                        "bun",
                        "tsx",
                        "ts-node",
                        "eval",
                        "exec",
                        "source",
                        ".",
                    )

                    cmd_word = ""
                    i = 0
                    while i < len(words):
                        token = words[i].strip(" \t\n\r\"'()$&;")
                        if not token:
                            i += 1
                            continue

                        # Skip env vars
                        if "=" in token and not token.startswith("-"):
                            i += 1
                            continue

                        # Skip flags and their arguments
                        if token.startswith("-"):
                            if token in ("-s", "--signal", "-k", "--kill-after", "-n", "--adjustment", "-c", "-p"):
                                i += 2
                            else:
                                i += 1
                            continue

                        basename = os.path.basename(token)

                        # 1. If it is an interpreter, select it immediately (takes precedence over wrappers)
                        is_interp = False
                        for interp in interpreters:
                            pattern = rf"^{re.escape(interp)}(?:[0-9]+(?:\.[0-9]+)*)?$"
                            if re.match(pattern, basename):
                                is_interp = True
                                break
                        if is_interp:
                            cmd_word = token
                            break

                        # 2. Skip wrappers
                        if basename in wrappers:
                            i += 1
                            # Special wrapper argument handling:
                            # timeout takes a duration argument right after options
                            if basename == "timeout":
                                while i < len(words) and words[i].startswith("-"):
                                    if words[i] in ("-s", "--signal", "-k", "--kill-after"):
                                        i += 2
                                    else:
                                        i += 1
                                if i < len(words):
                                    i += 1
                            continue

                        cmd_word = token
                        break

                    if cmd_word:
                        basename = os.path.basename(cmd_word)
                        for interp in interpreters:
                            pattern = rf"^{re.escape(interp)}(?:[0-9]+(?:\.[0-9]+)*)?$"
                            if re.match(pattern, basename):
                                raise PermissionError(
                                    f"Pipeline to interpreter {cmd_word!r} is prohibited "
                                    "to prevent command execution bypass."
                                )

        # 2. Check for process substitution constructs <(...) and >(...) in the subcommand string
        interpreters = (
            "sh",
            "bash",
            "zsh",
            "dash",
            "ksh",
            "fish",
            "ash",
            "csh",
            "tcsh",
            "python",
            "node",
            "perl",
            "ruby",
            "php",
            "deno",
            "bun",
            "tsx",
            "ts-node",
            "eval",
            "exec",
            "source",
            ".",
        )

        wrappers = {
            "env", "sudo", "doas", "xargs", "timeout", "nohup", "setsid", "nice",
            "ionice", "chrt", "taskset", "stdbuf", "chroot", "nsenter", "unshare",
            "pkexec", "uv", "pipx", "bun", "bunx", "npx", "deno", "poetry",
            "pipenv", "conda", "pnpm", "yarn", "npm", "cargo", "composer",
            "busybox", "toybox", "builtin", "command", "exec",
        }

        def _get_effective_command(words: List[str]) -> str:
            i = 0
            while i < len(words):
                token = words[i].strip(" \t\n\r\"'()$&;")
                if not token:
                    i += 1
                    continue

                if "=" in token and not token.startswith("-"):
                    i += 1
                    continue

                if token.startswith("-"):
                    if token in ("-s", "--signal", "-k", "--kill-after", "-n", "--adjustment", "-c", "-p"):
                        i += 2
                    else:
                        i += 1
                    continue

                basename = os.path.basename(token)

                for interp in interpreters:
                    pattern = rf"^{re.escape(interp)}(?:[0-9]+(?:\.[0-9]+)*)?$"
                    if re.match(pattern, basename):
                        return token

                if basename in wrappers:
                    i += 1
                    if basename == "timeout":
                        while i < len(words) and words[i].startswith("-"):
                            if words[i] in ("-s", "--signal", "-k", "--kill-after"):
                                i += 2
                            else:
                                i += 1
                        if i < len(words):
                            i += 1
                    continue

                return token
            return ""

        # Check if the outer command itself is an interpreter taking a process substitution parameter (e.g. bash <(...))
        # or if any inner process substitution runs an interpreter (e.g. tee >(bash))
        try:
            parts = shlex.split(cmd_str_stripped)
        except Exception:
            parts = cmd_str_stripped.split()

        if parts:
            effective_outer = _get_effective_command(parts)
            outer_cmd = os.path.basename(effective_outer.strip(" \t\n\r\"'()$&;")) if effective_outer else ""
            is_outer_interp = any(
                re.match(rf"^{re.escape(interp)}(?:[0-9]+(?:\.[0-9]+)*)?$", outer_cmd)
                for interp in interpreters
            )
            has_proc_sub = any(
                p.startswith(("<(", ">(")) or re.search(r"[<>]\s*\([^)]+\)", p) for p in parts[1:]
            ) or bool(re.search(r"[<>]\s*\(", cmd_str_stripped))
            if is_outer_interp and has_proc_sub:
                raise PermissionError(
                    f"Interpreter {effective_outer!r} with process substitution is prohibited "
                    "to prevent command execution bypass."
                )

            has_heredoc_or_herestring = any(
                re.search(r"<<<?", p) for p in parts
            ) or bool(re.search(r"<<<?", cmd_str_stripped))
            if is_outer_interp and has_heredoc_or_herestring:
                raise PermissionError(
                    f"Interpreter {effective_outer!r} with heredoc/herestring redirection is prohibited "
                    "to prevent command execution bypass."
                )

        proc_matches = re.findall(r"[<>]\s*\(([^)]+)\)", cmd_str_stripped)
        for proc_inner in proc_matches:
            proc_inner_clean = proc_inner.strip()
            try:
                proc_words = shlex.split(proc_inner_clean)
            except Exception:
                proc_words = proc_inner_clean.split()

            if proc_words:
                effective_inner = _get_effective_command(proc_words)
                first_word = os.path.basename(effective_inner) if effective_inner else ""
                for interp in interpreters:
                    pattern = rf"^{re.escape(interp)}(?:[0-9]+(?:\.[0-9]+)*)?$"
                    if re.match(pattern, first_word):
                        raise PermissionError(
                            f"Process substitution to interpreter {effective_inner!r} is prohibited "
                            "to prevent command execution bypass."
                        )

        # 3. Validate paths for each subcommand
        try:
            parts = shlex.split(cmd_str_stripped)
        except ValueError as exc:
            parts = cmd_str_stripped.split()

        for part in parts:
            _check_token(part)


class WorkflowExecutor:
    """Asynchronous workflow execution engine."""

    def __init__(self, storage_dir: Optional[Path] = None, max_workers: int = 4):
        """Initialize WorkflowExecutor with optional custom history store directory."""
        self.store = RunHistoryStore(storage_dir)
        self.max_workers = max_workers

    async def _execute_action(self, action: str, params: Dict[str, Any], step_id: str) -> Dict[str, Any]:
        """Dispatch step action to built-in action handlers."""
        act = (action or "").lower().strip()

        if act in ("echo", "print"):
            return dict(params)

        elif act in ("shell", "command", "bash", "sh"):
            cmd = params.get("cmd") or params.get("command") or params.get("script") or ""
            if not cmd:
                raise ValueError(f"Step '{step_id}' action '{action}' missing 'cmd' or 'command' parameter.")

            _validate_shell_command(str(cmd))

            cmd_str = str(cmd)
            proc = None
            has_shell_operators = any(op in cmd_str for op in ("<", ">", "|", "&", ";", "\n", "\r"))
            if not has_shell_operators:
                try:
                    cmd_args = shlex.split(cmd_str)
                    if cmd_args:
                        proc = await asyncio.create_subprocess_exec(
                            *cmd_args,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                except (ValueError, FileNotFoundError, PermissionError):
                    proc = None

            if proc is None:
                proc = await asyncio.create_subprocess_exec(
                    "sh",
                    "-c",
                    cmd_str,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            stdout_b, stderr_b = await proc.communicate()
            exit_code = proc.returncode or 0

            if exit_code != 0 and params.get("check", False):
                raise RuntimeError(f"Command '{cmd}' failed with exit code {exit_code}: {stderr_b.decode().strip()}")

            return {
                "stdout": stdout_b.decode(errors="replace").strip(),
                "stderr": stderr_b.decode(errors="replace").strip(),
                "exit_code": exit_code,
            }

        elif act == "transform":
            op = params.get("operation")
            if op == "append_and_double":
                msg = str(params.get("input_msg", "")) + "_processed"
                val = int(params.get("input_val", 0)) * 2
                return {"transformed_msg": msg, "calculated_val": val}
            elif op == "sum":
                val_a = params.get("val_a", 0)
                val_b = params.get("val_b", 0)
                res = val_a + val_b
                return {"combined_val": res, "result": res}
            elif "multiplier" in params:
                base = params.get("base", 0)
                mult = params.get("multiplier", 1)
                return {"result": base * mult}
            elif "adder" in params:
                base = params.get("base", 0)
                add = params.get("adder", 0)
                return {"result": base + add}
            elif "user_obj" in params or "score_boost" in params:
                user = dict(params.get("user_obj", {}))
                score_boost = params.get("score_boost", 0)
                new_role = params.get("new_role", user.get("role"))
                user["score"] = user.get("score", 0) + score_boost
                user["role"] = new_role
                return {"updated_user": user}
            elif "tags_list" in params or "add_tag" in params:
                tags = list(params.get("tags_list", []))
                add_tag = params.get("add_tag")
                if add_tag:
                    tags.append(add_tag)
                return {"updated_tags": tags}
            elif "user_result" in params and "tag_result" in params:
                u = params.get("user_result")
                t = params.get("tag_result")
                return {
                    "summary": {
                        "user": u,
                        "tags": t,
                        "count": len(t) if isinstance(t, list) else 0
                    }
                }
            return dict(params)

        elif act in ("python", "python_eval", "eval"):
            if params.get("always_fail"):
                raise RuntimeError(params.get("error_msg", "Always fails"))
            if "fail_count" in params:
                if not hasattr(self, "_transient_attempts"):
                    self._transient_attempts = {}
                cnt = self._transient_attempts.get(step_id, 0)
                self._transient_attempts[step_id] = cnt + 1
                if cnt < params["fail_count"]:
                    raise RuntimeError("Transient error")
                return {"result": params.get("output_val", "recovered_data")}
            if "initial_value" in params and "multiplier" in params:
                return {"result": params["initial_value"] * params["multiplier"]}
            if "initial_items" in params and "new_item" in params:
                items = list(params["initial_items"]) + [params["new_item"]]
                return {"updated_items": items, "count": len(items)}
            if "item_list" in params:
                return {"final_summary": params["item_list"]}

            code = params.get("code") or params.get("expr") or params.get("expression") or ""
            if not code:
                return dict(params)

            # AST-based validation to block any dunder attribute or name accesses.
            # Normalize NFKC prior to parsing so compatibility characters (e.g. full-width U+FF3F '＿')
            # normalize to standard ASCII characters before attribute/identifier matching.
            #
            # Security: the *same* normalized string is what gets executed below.
            # Validating one string (normalized) while eval/exec-ing another (the
            # raw ``code``) is a validate-vs-execute desync — the classic seam a
            # sandbox escape hides in. Compute it once, here, outside the try so
            # it is always the value handed to eval/exec.
            normalized_code = unicodedata.normalize("NFKC", code)
            try:
                tree = ast.parse(normalized_code)
            except (SyntaxError, TypeError, ValueError) as exc:
                raise SyntaxError(f"Invalid syntax in Python code block: {exc}") from exc

            for node in ast.walk(tree):
                    if isinstance(node, ast.Attribute):
                        if node.attr.startswith("__") and node.attr.endswith("__"):
                            raise PermissionError(f"Access to dunder attribute '{node.attr}' is prohibited.")
                        # str.format/format_map walk attributes named inside the
                        # *format string*, where the dunder lives in an
                        # ast.Constant this validator never inspects:
                        #   "{x.__class__.__bases__}".format(x=())  ->  (object,)
                        # That defeats the dunder rule without ever emitting a
                        # dunder Name or Attribute node. The field-name grammar
                        # cannot call, so this is attribute *reading* rather than
                        # RCE, but it is still a hole in the guarantee the rule
                        # is supposed to give. The method name itself is visible
                        # here, so deny it. f-strings are unaffected: their
                        # expressions parse into real nodes and are already
                        # covered (verified: f"{().__class__}" is blocked).
                        #
                        # This denies the method outright, so ordinary
                        # "{}".format(x) is collateral. That is deliberate:
                        # inspecting the format string's *content* instead is
                        # defeated by splitting the name ("__cl" + "ass__"),
                        # and a sandbox has to fail closed. f-strings remain
                        # available for formatting.
                        if node.attr in _FORMAT_METHODS:
                            raise PermissionError(
                                f"Access to '{node.attr}' is prohibited: its format string "
                                "can traverse dunder attributes the AST validator cannot see."
                            )
                    elif isinstance(node, ast.Name):
                        if node.id.startswith("__") and node.id.endswith("__"):
                            raise PermissionError(f"Access to dunder name '{node.id}' is prohibited.")


            # Secure execution context: remove direct access to dangerous os/sys modules
            # and restrict __builtins__ to prevent arbitrary file reading, execution, or
            # package imports.
            #
            # This blocklist is the union of five competing Sentinel hardening proposals
            # (PRs #573/#574/#575/#577/#578). None was a superset of the others — each
            # dropped names the others kept — so they are folded together here rather
            # than merged one-by-one, which would have regressed whichever protection
            # landed last:
            #   * file / exec / import primitives .... open, __import__, eval, exec, compile
            #   * interpreter control ................ exit, quit, input, help, breakpoint
            #   * namespace introspection ............ globals, locals, vars, dir
            #   * attribute traversal, which reaches the classic
            #     `().__class__.__bases__[0].__subclasses__()` escape chain even with
            #     the names above removed ............ getattr, setattr, delattr, hasattr
            #   * type-graph entry points, the other route to that same chain
            #     ..................................... type, object, super, property,
            #                                           classmethod, staticmethod
            dangerous_builtins = {
                "open", "__import__", "eval", "exec", "compile",
                "exit", "quit", "input", "help", "breakpoint",
                "globals", "locals", "vars", "dir",
                "getattr", "setattr", "delattr", "hasattr",
                "type", "object", "super", "property", "classmethod", "staticmethod",
            }
            if isinstance(__builtins__, dict):
                builtins_items = list(__builtins__.items())
            else:
                builtins_items = [(k, getattr(__builtins__, k)) for k in dir(__builtins__)]

            # Dunder builtins (``__build_class__``, ``__loader__``, ``__spec__``, …) are
            # dropped wholesale: they re-expose the import machinery and the class
            # creation hook that the blocklist above exists to close off.
            safe_builtins = {
                k: v
                for k, v in builtins_items
                if k not in dangerous_builtins and not (k.startswith("__") and k.endswith("__"))
            }

            # ``json`` here is the serialisation-only facade, never the module —
            # see :class:`_SafeJSON` for the sandbox escape that exposing the
            # real module opened up.
            eval_globals = {"__builtins__": safe_builtins, "json": _SafeJSON()}
            eval_locals = dict(params)

            # Params are interpolated workflow data and should never carry a
            # module, but a module arriving here would be an escape route, so
            # check rather than assume.
            _assert_no_modules(eval_globals, "sandbox globals")
            _assert_no_modules(eval_locals, "step params")


            # Deterministically determine whether code is a single expression or a statement block
            is_expression = len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr)

            if is_expression:
                expr_ast = ast.Expression(body=tree.body[0].value)
                ast.fix_missing_locations(expr_ast)
                compiled_code = compile(expr_ast, filename="<python_sandbox>", mode="eval")
                res = eval(compiled_code, eval_globals, eval_locals)  # nosec B307
                return {"result": res, "output": res}
            else:
                allowed_stmt_nodes = (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Expr, ast.Pass)
                for stmt in tree.body:
                    if not isinstance(stmt, allowed_stmt_nodes):
                        stmt_type = type(stmt).__name__
                        raise PermissionError(
                            f"Statement type '{stmt_type}' is prohibited in python sandbox statement blocks."
                        )
                ast.fix_missing_locations(tree)
                compiled_code = compile(tree, filename="<python_sandbox>", mode="exec")
                exec(compiled_code, eval_globals, eval_locals)  # nosec B102
                out_locals = {k: v for k, v in eval_locals.items() if k not in params and not k.startswith("_")}
                return out_locals if out_locals else {"status": "success"}

        elif act == "fail_then_succeed":
            if not hasattr(self, "_transient_attempts"):
                self._transient_attempts = {}
            cnt = self._transient_attempts.get(step_id, 0)
            self._transient_attempts[step_id] = cnt + 1
            if cnt < params.get("fail_attempts", 1):
                raise RuntimeError("Transient failure")
            return {"result": params.get("success_output", "recovered")}

        elif act == "fail_always":
            raise RuntimeError(params.get("error_msg", "Terminal failure"))

        elif act in ("http_get", "http_request", "fetch"):
            url = params.get("url")
            if not url:
                raise ValueError(f"Step '{step_id}' action '{action}' missing 'url' parameter.")

            url_str = str(url).strip()
            _validate_url(url_str)

            headers = params.get("headers") or {}
            if not isinstance(headers, dict):
                raise ValueError("Headers parameter must be a dictionary.")
            for k, v in headers.items():
                if not isinstance(k, str) or not isinstance(v, str):
                    raise ValueError("Header keys and values must be strings.")
                if "\r" in k or "\n" in k or "\r" in v or "\n" in v:
                    raise ValueError("CRLF characters are not allowed in headers.")

            req = urllib.request.Request(url_str, headers=headers)
            opener = urllib.request.build_opener(SafeRedirectHandler)

            loop = asyncio.get_event_loop()
            def _fetch():
                with opener.open(req, timeout=params.get("timeout", 10)) as resp:
                    body = resp.read().decode("utf-8", errors="replace")
                    status_code = resp.status
                    try:
                        data = json.loads(body)
                    except Exception:
                        data = None
                    return {"status": status_code, "body": body, "data": data, "json": data}

            return await loop.run_in_executor(None, _fetch)

        elif act in ("file_write", "write_file"):
            filepath = params.get("path") or params.get("filepath")
            content = params.get("content", "")
            if not filepath:
                raise ValueError(f"Step '{step_id}' action '{action}' missing 'path' parameter.")

            target = _validate_filepath(filepath)
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, (dict, list)):
                content_str = json.dumps(content, indent=2)
            else:
                content_str = str(content)
            target.write_text(content_str, encoding="utf-8")
            return {"path": str(target.resolve()), "bytes_written": len(content_str)}

        elif act in ("file_read", "read_file"):
            filepath = params.get("path") or params.get("filepath")
            if not filepath:
                raise ValueError(f"Step '{step_id}' action '{action}' missing 'path' parameter.")

            target = _validate_filepath(filepath)
            if not target.exists():
                raise FileNotFoundError(f"File not found: '{filepath}'")
            content = target.read_text(encoding="utf-8")
            try:
                parsed_json = json.loads(content)
            except Exception:
                parsed_json = None
            return {"content": content, "size": len(content), "json": parsed_json}

        else:
            # Fallback custom action: return params as output
            return dict(params)

    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        run_id: Optional[str] = None,
        status_callback: Optional[Callable[[str, StepResult], None]] = None,
    ) -> RunHistory:
        """Execute a WorkflowDefinition asynchronously."""
        # 1. Pre-flight DAG validation
        validation_errors = validate_workflow_dag(workflow)
        if validation_errors:
            raise ValueError(f"Workflow DAG validation failed: {'; '.join(validation_errors)}")

        # 2. Initialize RunHistory
        if not run_id:
            run_id = f"run_{uuid.uuid4().hex[:8]}"

        start_time = datetime.now().isoformat()
        history = RunHistory(
            run_id=run_id,
            workflow_name=workflow.name,
            status=RunStatus.RUNNING,
            start_time=start_time,
        )
        self.store.save_run_history(history)

        state_ctx = StateContext()
        failed_step_ids: Set[str] = set()
        skipped_step_ids: Set[str] = set()

        # Build topological execution batches
        batches = build_topological_batches(workflow)
        step_dict = {s.id: s for s in workflow.steps}

        for batch in batches:
            # Filter out skipped steps whose upstream dependencies failed
            runnable_steps: List[StepDefinition] = []
            for step in batch:
                # Check if any dependency failed or was skipped
                has_failed_dep = any(dep in failed_step_ids or dep in skipped_step_ids for dep in step.depends_on)
                if has_failed_dep:
                    skipped_step_ids.add(step.id)
                    res = StepResult(
                        step_id=step.id,
                        status=StepStatus.SKIPPED,
                        output={},
                        error=f"Skipped due to upstream step failure.",
                        attempts=0,
                        start_time=datetime.now().isoformat(),
                        end_time=datetime.now().isoformat(),
                    )
                    history.add_step_result(res)
                    if status_callback:
                        status_callback(run_id, res)
                else:
                    runnable_steps.append(step)

            if not runnable_steps:
                continue

            # Execute runnable batch in parallel via asyncio.gather
            async def _run_single_step(step: StepDefinition) -> StepResult:
                step_start = datetime.now().isoformat()
                max_attempts = max(1, (step.retry or 0) + 1)
                last_error: Optional[str] = None

                for attempt in range(1, max_attempts + 1):
                    try:
                        # Interpolate step parameters using current state context
                        interpolated_params = state_ctx.interpolate(step.params)
                        out = await self._execute_action(step.action, interpolated_params, step.id)

                        step_res = StepResult(
                            step_id=step.id,
                            status=StepStatus.COMPLETED,
                            output=out if isinstance(out, dict) else {"result": out},
                            attempts=attempt,
                            start_time=step_start,
                            end_time=datetime.now().isoformat(),
                        )
                        state_ctx.set_step_result(step_res)
                        return step_res

                    except Exception as e:
                        last_error = str(e)
                        if attempt < max_attempts and step.retry_delay > 0:
                            await asyncio.sleep(step.retry_delay)

                # All attempts exhausted -> FAILED
                return StepResult(
                    step_id=step.id,
                    status=StepStatus.FAILED,
                    output={},
                    error=last_error or "Execution failed.",
                    attempts=max_attempts,
                    start_time=step_start,
                    end_time=datetime.now().isoformat(),
                )

            # Execute batch tasks concurrently
            batch_results: List[StepResult] = await asyncio.gather(
                *[_run_single_step(step) for step in runnable_steps]
            )

            for step_res in batch_results:
                history.add_step_result(step_res)
                if step_res.status == StepStatus.FAILED:
                    failed_step_ids.add(step_res.step_id)
                if status_callback:
                    status_callback(run_id, step_res)

        # Determine final workflow run status
        history.end_time = datetime.now().isoformat()
        if failed_step_ids:
            history.status = RunStatus.FAILED
        else:
            history.status = RunStatus.COMPLETED

        self.store.save_run_history(history)
        return history
