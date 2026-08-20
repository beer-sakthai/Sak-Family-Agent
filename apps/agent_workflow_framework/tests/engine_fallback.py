"""
Fallback reference implementation of agent_workflow interfaces for test execution
when agent_workflow package is not yet populated by parallel implementation tracks.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
import os
import sys
import json
import yaml
import asyncio
import time
import uuid
import graphlib
from pathlib import Path
import re


class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class StepDefinition:
    id: str
    action: str = "echo"
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    retry: int = 0
    retry_delay: float = 0.0


@dataclass
class WorkflowDefinition:
    name: str
    description: Optional[str] = None
    steps: List[StepDefinition] = field(default_factory=list)


@dataclass
class StepResult:
    step_id: str
    status: StepStatus
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    attempts: int = 1
    start_time: Optional[str] = None
    end_time: Optional[str] = None


@dataclass
class RunHistory:
    run_id: str
    workflow_name: str
    status: RunStatus
    start_time: str
    end_time: Optional[str] = None
    step_results: Dict[str, StepResult] = field(default_factory=dict)


class StateContext:
    def __init__(self):
        self._outputs: Dict[str, Dict[str, Any]] = {}

    def set_step_output(self, step_id: str, output: Dict[str, Any]) -> None:
        self._outputs[step_id] = output

    def get_step_output(self, step_id: str) -> Dict[str, Any]:
        return self._outputs.get(step_id, {})

    def interpolate(self, template: Any) -> Any:
        if isinstance(template, str):
            # Single expression exact match preserving native type
            match = re.fullmatch(r"\$\{steps\.([a-zA-Z0-9_-]+)\.output(?:\.([a-zA-Z0-9_.-]+))?\}", template.strip())
            if match:
                step_id, key_path = match.groups()
                if step_id not in self._outputs:
                    raise KeyError(f"Step '{step_id}' output not found in state context")
                val = self._outputs[step_id]
                if key_path:
                    keys = key_path.split(".")
                    for k in keys:
                        if isinstance(val, dict) and k in val:
                            val = val[k]
                        else:
                            raise KeyError(f"Key '{k}' not found in step '{step_id}' output")
                return val

            pattern = r"\$\{steps\.([a-zA-Z0-9_-]+)\.output(?:\.([a-zA-Z0-9_.-]+))?\}"
            def replace_match(m):
                step_id, key_path = m.groups()
                if step_id not in self._outputs:
                    raise KeyError(f"Step '{step_id}' output not found in state context")
                val = self._outputs[step_id]
                if key_path:
                    keys = key_path.split(".")
                    for k in keys:
                        if isinstance(val, dict) and k in val:
                            val = val[k]
                        else:
                            raise KeyError(f"Key '{k}' not found in step '{step_id}' output")
                return str(val)

            return re.sub(pattern, replace_match, template)
        elif isinstance(template, dict):
            return {k: self.interpolate(v) for k, v in template.items()}
        elif isinstance(template, list):
            return [self.interpolate(v) for v in template]
        return template


def validate_workflow_dag(workflow: WorkflowDefinition) -> List[str]:
    errors = []
    if not workflow.name:
        errors.append("Workflow name is required.")
    if not workflow.steps:
        errors.append("Workflow must contain at least one step.")
        return errors

    step_ids = set()
    for s in workflow.steps:
        if not s.id:
            errors.append("Step ID is required.")
        elif s.id in step_ids:
            errors.append(f"Duplicate step ID: '{s.id}'.")
        else:
            step_ids.add(s.id)

    graph = {}
    for s in workflow.steps:
        for dep in s.depends_on:
            if dep not in step_ids:
                errors.append(f"Step '{s.id}' depends on undefined step '{dep}'.")
            if dep == s.id:
                errors.append(f"Cyclic dependency detected: Step '{s.id}' depends on itself.")
        graph[s.id] = set(s.depends_on)

    if errors:
        return errors

    try:
        ts = graphlib.TopologicalSorter(graph)
        ts.prepare()
    except graphlib.CycleError as e:
        errors.append(f"Cyclic dependency detected in workflow: {e}")

    return errors


def build_topological_batches(workflow: WorkflowDefinition) -> List[List[StepDefinition]]:
    step_map = {s.id: s for s in workflow.steps}
    graph = {s.id: set(s.depends_on) for s in workflow.steps}
    ts = graphlib.TopologicalSorter(graph)
    ts.prepare()

    batches = []
    while ts.is_active():
        ready = ts.get_ready()
        if not ready:
            break
        batch = [step_map[s_id] for s_id in ready]
        batches.append(batch)
        ts.done(*ready)
    return batches


def parse_workflow_dict(data: dict) -> WorkflowDefinition:
    if not isinstance(data, dict):
        raise ValueError("Invalid workflow definition format.")
    name = data.get("name")
    if not name:
        raise ValueError("Missing required field 'name'")
    description = data.get("description")
    raw_steps = data.get("steps")
    if raw_steps is None:
        raise ValueError("Missing required field 'steps'")
    steps = []
    for s in raw_steps:
        step = StepDefinition(
            id=s["id"],
            action=s.get("action", "echo"),
            params=s.get("params", {}),
            depends_on=s.get("depends_on", []),
            retry=s.get("retry", 0),
            retry_delay=s.get("retry_delay", 0.0),
        )
        steps.append(step)
    return WorkflowDefinition(name=name, description=description, steps=steps)


def parse_workflow_file(filepath: str) -> WorkflowDefinition:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Workflow file not found: {filepath}")
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError("Empty workflow file")
    if path.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(content)
    elif path.suffix == ".json":
        data = json.loads(content)
    else:
        try:
            data = yaml.safe_load(content)
        except Exception:
            data = json.loads(content)
    return parse_workflow_dict(data)


class HistoryStore:
    def __init__(self, storage_dir: str = ".workflow_runs"):
        self.storage_dir = Path(storage_dir)

    def save_run_history(self, history: RunHistory) -> str:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.storage_dir / f"{history.run_id}.json"
        data = {
            "run_id": history.run_id,
            "workflow_name": history.workflow_name,
            "status": history.status.value if isinstance(history.status, Enum) else history.status,
            "start_time": history.start_time,
            "end_time": history.end_time,
            "step_results": {
                sid: {
                    "step_id": res.step_id,
                    "status": res.status.value if isinstance(res.status, Enum) else res.status,
                    "output": res.output,
                    "error": res.error,
                    "attempts": res.attempts,
                    "start_time": res.start_time,
                    "end_time": res.end_time,
                }
                for sid, res in history.step_results.items()
            }
        }
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return str(file_path)

    def load_run_history(self, run_id_or_path: str) -> RunHistory:
        path = Path(run_id_or_path)
        if not path.exists():
            path = self.storage_dir / f"{run_id_or_path}.json"
        if not path.exists():
            raise FileNotFoundError(f"Run history not found: {run_id_or_path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        step_results = {}
        for sid, sdata in data.get("step_results", {}).items():
            step_results[sid] = StepResult(
                step_id=sdata["step_id"],
                status=StepStatus(sdata["status"]),
                output=sdata.get("output", {}),
                error=sdata.get("error"),
                attempts=sdata.get("attempts", 1),
                start_time=sdata.get("start_time"),
                end_time=sdata.get("end_time"),
            )
        return RunHistory(
            run_id=data["run_id"],
            workflow_name=data["workflow_name"],
            status=RunStatus(data["status"]),
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            step_results=step_results,
        )


class WorkflowExecutor:
    def __init__(self, history_store: Optional[HistoryStore] = None, max_workers: int = 4):
        self.history_store = history_store or HistoryStore()
        self.max_workers = max_workers
        self._transient_attempts: Dict[str, int] = {}

    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        run_id: Optional[str] = None,
        status_callback: Optional[Any] = None
    ) -> RunHistory:
        val_errors = validate_workflow_dag(workflow)
        if val_errors:
            raise ValueError(f"Workflow DAG validation failed: {val_errors}")

        run_id = run_id or f"run_{uuid.uuid4().hex[:8]}"
        start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        history = RunHistory(
            run_id=run_id,
            workflow_name=workflow.name,
            status=RunStatus.RUNNING,
            start_time=start_time,
        )
        state_ctx = StateContext()
        failed_steps = set()

        batches = build_topological_batches(workflow)
        semaphore = asyncio.Semaphore(self.max_workers)

        for batch in batches:
            async def run_step(step: StepDefinition):
                async with semaphore:
                    if any(dep in failed_steps for dep in step.depends_on):
                        res = StepResult(
                            step_id=step.id,
                            status=StepStatus.SKIPPED,
                            output={},
                            error="Skipped due to upstream failure",
                            attempts=0,
                        )
                        failed_steps.add(step.id)
                        return res

                    if status_callback:
                        status_callback(step.id, StepStatus.RUNNING)

                    attempts = 0
                    max_attempts = step.retry + 1
                    last_error = None

                    while attempts < max_attempts:
                        attempts += 1
                        step_start = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        try:
                            interpolated_params = state_ctx.interpolate(step.params)
                            output = await self._execute_action(step.id, step.action, interpolated_params)
                            state_ctx.set_step_output(step.id, output)
                            step_end = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                            res = StepResult(
                                step_id=step.id,
                                status=StepStatus.COMPLETED,
                                output=output,
                                attempts=attempts,
                                start_time=step_start,
                                end_time=step_end,
                            )
                            if status_callback:
                                status_callback(step.id, StepStatus.COMPLETED)
                            return res
                        except Exception as e:
                            last_error = str(e)
                            if attempts < max_attempts:
                                if step.retry_delay > 0:
                                    await asyncio.sleep(step.retry_delay)

                    step_end = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    failed_steps.add(step.id)
                    res = StepResult(
                        step_id=step.id,
                        status=StepStatus.FAILED,
                        error=last_error,
                        attempts=attempts,
                        start_time=step_start,
                        end_time=step_end,
                    )
                    if status_callback:
                        status_callback(step.id, StepStatus.FAILED)
                    return res

            results = await asyncio.gather(*(run_step(s) for s in batch))
            for res in results:
                history.step_results[res.step_id] = res

        history.end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if any(r.status == StepStatus.FAILED for r in history.step_results.values()):
            history.status = RunStatus.FAILED
        else:
            history.status = RunStatus.COMPLETED

        self.history_store.save_run_history(history)
        return history

    async def _execute_action(self, step_id: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "echo":
            return dict(params)
        elif action == "transform":
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
        elif action == "python":
            if params.get("always_fail"):
                raise RuntimeError(params.get("error_msg", "Always fails"))
            if "fail_count" in params:
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
            return dict(params)
        elif action == "fail_then_succeed":
            cnt = self._transient_attempts.get(step_id, 0)
            self._transient_attempts[step_id] = cnt + 1
            if cnt < params.get("fail_attempts", 1):
                raise RuntimeError("Transient failure")
            return {"result": params.get("success_output", "recovered")}
        elif action == "fail_always":
            raise RuntimeError(params.get("error_msg", "Terminal failure"))
        else:
            return dict(params)


def cli_main(args: Optional[List[str]] = None) -> int:
    if args is None:
        args = sys.argv[1:]

    if not args:
        print("Usage: python -m agent_workflow.cli <validate|run|inspect> [args]")
        return 1

    cmd = args[0]
    if cmd == "validate":
        if len(args) < 2:
            print("Error: missing file argument for validate", file=sys.stderr)
            return 2
        file_path = args[1]
        try:
            wf = parse_workflow_file(file_path)
            errs = validate_workflow_dag(wf)
            if errs:
                for e in errs:
                    print(f"Validation Error: {e}", file=sys.stderr)
                return 2
            print(f"Workflow '{wf.name}' is valid.")
            return 0
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"Validation Error: {e}", file=sys.stderr)
            return 2

    elif cmd == "run":
        if len(args) < 2:
            print("Error: missing file argument for run", file=sys.stderr)
            return 1
        file_path = args[1]
        try:
            wf = parse_workflow_file(file_path)
            errs = validate_workflow_dag(wf)
            if errs:
                for e in errs:
                    print(f"Validation Error: {e}", file=sys.stderr)
                return 2
            executor = WorkflowExecutor()
            history = asyncio.run(executor.execute_workflow(wf))
            if history.status == RunStatus.COMPLETED:
                print(f"Workflow '{wf.name}' executed successfully (Run ID: {history.run_id}).")
                return 0
            else:
                print(f"Workflow '{wf.name}' failed (Run ID: {history.run_id}).", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"Execution Error: {e}", file=sys.stderr)
            return 1

    elif cmd == "inspect":
        if len(args) < 2:
            print("Error: missing run_id argument for inspect", file=sys.stderr)
            return 1
        run_id = args[1]
        store = HistoryStore()
        try:
            history = store.load_run_history(run_id)
            print(f"Run ID: {history.run_id}")
            print(f"Workflow Name: {history.workflow_name}")
            print(f"Status: {history.status.value}")
            for sid, res in history.step_results.items():
                print(f"  Step '{sid}': {res.status.value} (attempts: {res.attempts})")
            return 0
        except FileNotFoundError:
            print(f"Error: Run history '{run_id}' not found.", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Inspection Error: {e}", file=sys.stderr)
            return 1

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        return 1
