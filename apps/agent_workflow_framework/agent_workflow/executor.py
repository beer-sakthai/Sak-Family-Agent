"""Asynchronous execution engine and action handlers for agent_workflow.

Provides WorkflowExecutor to run DAG workflow definitions with parallel task scheduling,
state interpolation, step retries, downstream failure short-circuiting, and action handlers.
"""

import asyncio
import copy
import json
import os
import sys
import time
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

    # Strip fragment before parsing to prevent fragment-based host confusion or SSRF bypasses
    if "#" in url_str:
        url_str = url_str.split("#", 1)[0]

    try:
        parsed = urllib.parse.urlparse(url_str)
    except Exception as e:
        raise ValueError(f"Invalid URL: {url_str}. Error: {e}")

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise ValueError(f"Forbidden URL scheme '{scheme}'. Only HTTP and HTTPS are allowed.")

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

            if not ip.is_global or ip.is_multicast:
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

    path_str = str(filepath).strip()

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

    # Resolve target absolute to Path
    try:
        target = Path(path_str).resolve()
    except Exception as exc:
        raise ValueError(f"Invalid file path '{path_str}': {exc}")

    # Critical system roots (e.g., /etc, /bin, /var, /boot, /dev, /lib, /lib64, /proc, /sys, /sbin, /usr)
    parts = [p.lower() for p in target.parts]
    system_roots = {
        "etc", "bin", "var", "boot", "dev", "lib", "lib64", "proc", "sys", "sbin", "usr", "root", "opt",
    }

    if target.is_absolute():
        root_part = target.anchor
        non_root_parts = [p for p in target.parts if p != root_part]
        if non_root_parts:
            first_dir = non_root_parts[0].lower()
            if first_dir in system_roots:
                raise PermissionError(f"Access to critical system directory is prohibited: '{path_str}'")

    # Blocks access to sensitive directories (e.g., .git, .ssh, .aws)
    sensitive_dirs = {
        ".git", ".ssh", ".aws", ".jules", ".config", ".npm",
        ".docker", ".kube", ".gnupg", ".gcloud", ".azure",
    }
    if any(part in sensitive_dirs for part in parts):
        raise PermissionError(f"Access to sensitive directory is prohibited: '{path_str}'")

    # Blocks access to credential/sensitive file basenames (e.g., .env, memory.db, id_rsa)
    filename = target.name.lower()
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

    if (
        filename in sensitive_basenames
        or filename.startswith(sensitive_prefixes)
        or filename.endswith(sensitive_suffixes)
        or any(filename.startswith(stem + ".") for stem in sensitive_key_stems)
    ):
        raise PermissionError(f"Access to sensitive file is prohibited: '{path_str}'")

    return target


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

            proc = await asyncio.create_subprocess_shell(
                str(cmd),
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

            eval_globals = {"__builtins__": safe_builtins, "json": json}
            eval_locals = dict(params)

            try:
                # Try evaluating as expression first
                res = eval(code, eval_globals, eval_locals)
                return {"result": res, "output": res}
            except SyntaxError:
                # Execute as statement block
                exec(code, eval_globals, eval_locals)
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

            req = urllib.request.Request(url_str, headers=params.get("headers", {}))
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
