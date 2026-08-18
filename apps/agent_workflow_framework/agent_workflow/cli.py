"""Command-Line Interface (CLI) entry point for agent_workflow.

Provides subcommands:
  - validate: Pre-flight validation of definition files & DAG cycles.
  - run: Asynchronously execute workflow definitions with live output.
  - inspect: Query past run history, step execution logs, and state outputs.
  - list: List all stored workflow runs in .workflow_runs/.

Standard Exit Codes:
  0 = Success
  1 = Runtime / Execution Error
  2 = Validation / Syntax Error
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional

from agent_workflow.dag import validate_workflow_dag
from agent_workflow.executor import WorkflowExecutor
from agent_workflow.models import RunStatus, StepStatus
from agent_workflow.parser import parse_workflow_file, WorkflowParseError
from agent_workflow.persistence import RunHistoryStore, RunNotFoundError


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser for agent_workflow CLI."""
    parser = argparse.ArgumentParser(
        prog="agent-workflow",
        description="Agent Workflow Framework CLI — Validate, Execute, and Inspect DAG Workflows.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # 1. validate
    val_p = subparsers.add_parser("validate", help="Pre-flight validation of workflow definition files.")
    val_p.add_argument("file", help="Path to YAML or JSON workflow definition file.")

    # 2. run
    run_p = subparsers.add_parser("run", help="Execute workflow definition file.")
    run_p.add_argument("file", help="Path to YAML or JSON workflow definition file.")
    run_p.add_argument("--run-id", dest="run_id", help="Optional custom run ID.")

    # 3. inspect
    insp_p = subparsers.add_parser("inspect", help="Inspect past run history by run_id or file.")
    insp_p.add_argument("run_id", help="Run ID or path to run history JSON file.")
    insp_p.add_argument("--step", dest="step_id", help="Optional specific step ID to inspect.")

    # 4. list
    subparsers.add_parser("list", help="List stored workflow runs in .workflow_runs/.")

    return parser


def cmd_validate(filepath: str) -> int:
    """Execute 'validate' subcommand."""
    try:
        wf = parse_workflow_file(filepath)
        errors = validate_workflow_dag(wf)
        if errors:
            print(f"Validation Error: {'; '.join(errors)}", file=sys.stderr)
            return 2
        print(f"Workflow '{wf.name}' is valid.")
        return 0
    except WorkflowParseError as e:
        print(f"Syntax Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


def cmd_run(filepath: str, run_id: Optional[str] = None) -> int:
    """Execute 'run' subcommand."""
    # Pre-flight parse check
    try:
        wf = parse_workflow_file(filepath)
    except Exception as e:
        print(f"Validation Error: Failed to parse workflow file '{filepath}': {e}", file=sys.stderr)
        return 2

    # Pre-flight DAG check
    errors = validate_workflow_dag(wf)
    if errors:
        print(f"Validation Error: {'; '.join(errors)}", file=sys.stderr)
        return 2

    executor = WorkflowExecutor()

    def status_cb(r_id: str, step_res):
        print(f"  Step '{step_res.step_id}': {step_res.status.value} (attempts: {step_res.attempts})")

    try:
        history = asyncio.run(executor.execute_workflow(wf, run_id=run_id, status_callback=status_cb))
        if history.status == RunStatus.COMPLETED:
            print(f"Workflow '{wf.name}' executed successfully (Run ID: {history.run_id}).")
            return 0
        else:
            print(f"Workflow '{wf.name}' failed (Run ID: {history.run_id}).", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Execution Error: {e}", file=sys.stderr)
        return 1


def cmd_inspect(run_id: str, step_id: Optional[str] = None) -> int:
    """Execute 'inspect' subcommand."""
    store = RunHistoryStore()
    try:
        history = store.load_run_history(run_id)
        if step_id:
            step_res = history.get_step_result(step_id)
            if not step_res:
                print(f"Error: Step '{step_id}' not found in run '{run_id}'.", file=sys.stderr)
                return 1
            print(json.dumps(step_res.to_dict(), indent=2))
        else:
            print(f"Run ID: {history.run_id}")
            print(f"Workflow Name: {history.workflow_name}")
            print(f"Status: {history.status.value}")
            for s_id, s_res in history.step_results.items():
                print(f"  Step '{s_id}': {s_res.status.value} (attempts: {s_res.attempts})")
        return 0
    except (RunNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error inspecting run '{run_id}': {e}", file=sys.stderr)
        return 1


def cmd_list() -> int:
    """Execute 'list' subcommand."""
    store = RunHistoryStore()
    try:
        runs = store.list_runs()
        if not runs:
            print("No workflow runs found.")
            return 0

        print(f"{'RUN ID':<20} {'WORKFLOW':<25} {'STATUS':<12} {'START TIME'}")
        print("-" * 75)
        for r in runs:
            print(f"{r.run_id:<20} {r.workflow_name:<25} {r.status.value:<12} {r.start_time}")
        return 0
    except Exception as e:
        print(f"Error listing runs: {e}", file=sys.stderr)
        return 1


def cli_main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point function."""
    parser = build_parser()
    parsed = parser.parse_args(args)

    if not parsed.subcommand:
        parser.print_help()
        return 0

    if parsed.subcommand == "validate":
        return cmd_validate(parsed.file)
    elif parsed.subcommand == "run":
        return cmd_run(parsed.file, run_id=parsed.run_id)
    elif parsed.subcommand == "inspect":
        return cmd_inspect(parsed.run_id, step_id=parsed.step_id)
    elif parsed.subcommand == "list":
        return cmd_list()
    else:
        parser.print_help()
        return 0


def main(args: Optional[List[str]] = None) -> int:
    """Executable console script entry point."""
    return cli_main(args)


if __name__ == "__main__":
    sys.exit(main())
