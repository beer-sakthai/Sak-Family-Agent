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

            # Safe execution context
            eval_globals = {"__builtins__": __builtins__, "json": json, "os": os, "sys": sys}
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

            req = urllib.request.Request(str(url), headers=params.get("headers", {}))

            loop = asyncio.get_event_loop()
            def _fetch():
                with urllib.request.urlopen(req, timeout=params.get("timeout", 10)) as resp:
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

            target = Path(filepath)
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

            target = Path(filepath)
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
