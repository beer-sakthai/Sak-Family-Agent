"""Distributed Multi-Agent Team Orchestration via the SakThai Runtime Gateway.

Enables multi-step and parallel pipelines (`BUILTIN_PIPELINES`) to execute across
local or remote networked Gateway instances with DAG execution traces.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Generator
from typing import Any

from ..client.gateway import GatewayClient
from ..gateway.router import GatewayRouter
from .builtin_pipelines import BUILTIN_PIPELINES
from .models import PipelineDefinition

logger = logging.getLogger(__name__)


class GatewayTeamOrchestrator:
    """Executes multi-agent team pipelines via local GatewayRouter or remote GatewayClient."""

    def __init__(
        self,
        router: GatewayRouter | None = None,
        client: GatewayClient | None = None,
    ) -> None:
        self.router = router
        self.client = client

    def list_pipelines(self) -> dict[str, Any]:
        """Return metadata and DAG structure for all registered team pipelines."""
        pipelines_list: list[dict[str, Any]] = []
        for name, p in BUILTIN_PIPELINES.items():
            steps_meta = [
                {
                    "index": idx,
                    "name": s.name,
                    "persona": s.persona,
                    "output_key": s.output_key,
                    "parallel_group": s.parallel_group,
                }
                for idx, s in enumerate(p.steps)
            ]
            pipelines_list.append(
                {
                    "name": name,
                    "description": p.description,
                    "steps_count": len(p.steps),
                    "steps": steps_meta,
                }
            )
        return {
            "count": len(pipelines_list),
            "pipelines": pipelines_list,
        }

    def execute_pipeline(
        self,
        pipeline_name: str,
        task: str,
        *,
        gateway_url: str | None = None,
        api_token: str | None = None,
    ) -> dict[str, Any]:
        """Run a team pipeline end-to-end across local or remote Gateway steps."""
        clean_name = pipeline_name.lower().strip()
        pipeline: PipelineDefinition | None = BUILTIN_PIPELINES.get(clean_name)
        if pipeline is None:
            return {
                "ok": False,
                "status": "error",
                "error": f"Unknown pipeline '{pipeline_name}'. Available: {list(BUILTIN_PIPELINES.keys())}",
            }

        if not task or not task.strip():
            return {
                "ok": False,
                "status": "error",
                "error": "Field 'task' is required and must be a non-empty string.",
            }

        run_id = f"teamrun-{uuid.uuid4().hex[:10]}"
        start_ts = time.perf_counter()
        context: dict[str, str] = {"task": task.strip()}
        step_results: list[dict[str, Any]] = []

        remote_client = self.client
        if gateway_url and remote_client is None:
            remote_client = GatewayClient(base_url=gateway_url, api_token=api_token)

        active_router = self.router or GatewayRouter()

        for idx, step in enumerate(pipeline.steps):
            step_start = time.perf_counter()
            try:
                formatted_prompt = step.prompt_template.format(**context)
            except KeyError:
                formatted_prompt = f"{step.prompt_template}\n\nTask: {task}"

            try:
                if remote_client is not None:
                    resp = remote_client.chat_completions(
                        messages=[{"role": "user", "content": formatted_prompt}],
                        model=step.persona,
                    )
                    output_text = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
                    dispatch_mode = f"remote:{remote_client.base_url}"
                else:
                    res, _ = active_router.handle_chat_completion(
                        {
                            "model": step.persona,
                            "stream": False,
                            "messages": [{"role": "user", "content": formatted_prompt}],
                        }
                    )
                    if isinstance(res, dict):
                        output_text = (
                            res.get("choices", [{}])[0].get("message", {}).get("content", "")
                        )
                    else:
                        output_text = str(res)
                    dispatch_mode = "local-gateway"

                elapsed_ms = round((time.perf_counter() - step_start) * 1000.0, 2)
                context[step.output_key] = output_text
                step_results.append(
                    {
                        "index": idx,
                        "step": step.name,
                        "persona": step.persona,
                        "output_key": step.output_key,
                        "parallel_group": step.parallel_group,
                        "status": "completed",
                        "dispatch_mode": dispatch_mode,
                        "duration_ms": elapsed_ms,
                        "output": output_text,
                    }
                )
            except Exception as exc:
                elapsed_ms = round((time.perf_counter() - step_start) * 1000.0, 2)
                logger.warning("Pipeline %s step %s failed: %s", clean_name, step.name, exc)
                step_results.append(
                    {
                        "index": idx,
                        "step": step.name,
                        "persona": step.persona,
                        "output_key": step.output_key,
                        "parallel_group": step.parallel_group,
                        "status": "failed",
                        "duration_ms": elapsed_ms,
                        "error": str(exc),
                    }
                )
                return {
                    "ok": False,
                    "run_id": run_id,
                    "pipeline": clean_name,
                    "task": task,
                    "status": "failed",
                    "failed_step": step.name,
                    "steps": step_results,
                    "total_duration_ms": round((time.perf_counter() - start_ts) * 1000.0, 2),
                }

        total_ms = round((time.perf_counter() - start_ts) * 1000.0, 2)
        final_output = step_results[-1]["output"] if step_results else ""
        return {
            "ok": True,
            "run_id": run_id,
            "pipeline": clean_name,
            "description": pipeline.description,
            "task": task,
            "status": "completed",
            "steps_completed": len(step_results),
            "steps": step_results,
            "final_output": final_output,
            "total_duration_ms": total_ms,
        }

    def stream_pipeline(
        self,
        pipeline_name: str,
        task: str,
        *,
        gateway_url: str | None = None,
        api_token: str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Stream a team pipeline step-by-step with real-time lifecycle and token events."""
        clean_name = pipeline_name.lower().strip()
        pipeline: PipelineDefinition | None = BUILTIN_PIPELINES.get(clean_name)
        if pipeline is None:
            yield {
                "event": "pipeline_error",
                "ok": False,
                "status": "error",
                "error": (
                    f"Unknown pipeline '{pipeline_name}'. "
                    f"Available: {list(BUILTIN_PIPELINES.keys())}"
                ),
            }
            return

        if not task or not task.strip():
            yield {
                "event": "pipeline_error",
                "ok": False,
                "status": "error",
                "error": "Field 'task' is required and must be a non-empty string.",
            }
            return

        run_id = f"teamrun-{uuid.uuid4().hex[:10]}"
        start_ts = time.perf_counter()
        context: dict[str, str] = {"task": task.strip()}
        step_results: list[dict[str, Any]] = []

        remote_client = self.client
        if gateway_url and remote_client is None:
            remote_client = GatewayClient(base_url=gateway_url, api_token=api_token)

        active_router = self.router or GatewayRouter()

        steps_meta = [
            {
                "index": idx,
                "name": s.name,
                "persona": s.persona,
                "output_key": s.output_key,
                "parallel_group": s.parallel_group,
            }
            for idx, s in enumerate(pipeline.steps)
        ]

        yield {
            "event": "pipeline_start",
            "ok": True,
            "run_id": run_id,
            "pipeline": clean_name,
            "description": pipeline.description,
            "task": task.strip(),
            "total_steps": len(pipeline.steps),
            "steps": steps_meta,
        }

        for idx, step in enumerate(pipeline.steps):
            step_start = time.perf_counter()
            try:
                formatted_prompt = step.prompt_template.format(**context)
            except KeyError:
                formatted_prompt = f"{step.prompt_template}\n\nTask: {task}"

            yield {
                "event": "step_start",
                "run_id": run_id,
                "step_index": idx,
                "step_name": step.name,
                "persona": step.persona,
                "output_key": step.output_key,
                "parallel_group": step.parallel_group,
                "input_prompt": formatted_prompt,
            }

            try:
                if remote_client is not None:
                    resp = remote_client.chat_completions(
                        messages=[{"role": "user", "content": formatted_prompt}],
                        model=step.persona,
                    )
                    output_text = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
                    dispatch_mode = f"remote:{remote_client.base_url}"
                    words = output_text.split(" ")
                    for i, w in enumerate(words):
                        piece = w + (" " if i < len(words) - 1 else "")
                        yield {
                            "event": "step_token",
                            "run_id": run_id,
                            "step_index": idx,
                            "step_name": step.name,
                            "token": piece,
                        }
                else:
                    res, is_stream = active_router.handle_chat_completion(
                        {
                            "model": step.persona,
                            "stream": True,
                            "messages": [{"role": "user", "content": formatted_prompt}],
                        }
                    )
                    dispatch_mode = "local-gateway"
                    if is_stream and hasattr(res, "__iter__"):
                        accumulated: list[str] = []
                        for chunk_str in res:
                            for line in str(chunk_str).split("\n"):
                                line = line.strip()
                                if line.startswith("data: ") and not line.startswith(
                                    "data: [DONE]"
                                ):
                                    try:
                                        data = json.loads(line[6:])
                                        delta = data.get("choices", [{}])[0].get("delta", {})
                                        content_tok = delta.get("content", "")
                                        if content_tok:
                                            accumulated.append(content_tok)
                                            yield {
                                                "event": "step_token",
                                                "run_id": run_id,
                                                "step_index": idx,
                                                "step_name": step.name,
                                                "token": content_tok,
                                            }
                                    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                                        continue
                        output_text = "".join(accumulated)
                    elif isinstance(res, dict):
                        output_text = (
                            res.get("choices", [{}])[0].get("message", {}).get("content", "")
                        )
                    else:
                        output_text = str(res)

                elapsed_ms = round((time.perf_counter() - step_start) * 1000.0, 2)
                context[step.output_key] = output_text
                step_result = {
                    "index": idx,
                    "step": step.name,
                    "persona": step.persona,
                    "output_key": step.output_key,
                    "parallel_group": step.parallel_group,
                    "status": "completed",
                    "dispatch_mode": dispatch_mode,
                    "duration_ms": elapsed_ms,
                    "output": output_text,
                }
                step_results.append(step_result)
                yield {
                    "event": "step_complete",
                    "run_id": run_id,
                    "step_index": idx,
                    "step_name": step.name,
                    "persona": step.persona,
                    "output_key": step.output_key,
                    "duration_ms": elapsed_ms,
                    "output": output_text,
                }
            except Exception as exc:
                elapsed_ms = round((time.perf_counter() - step_start) * 1000.0, 2)
                logger.warning(
                    "Pipeline %s step %s failed in stream: %s",
                    clean_name,
                    step.name,
                    exc,
                )
                yield {
                    "event": "step_failed",
                    "run_id": run_id,
                    "step_index": idx,
                    "step_name": step.name,
                    "persona": step.persona,
                    "duration_ms": elapsed_ms,
                    "error": str(exc),
                }
                yield {
                    "event": "pipeline_complete",
                    "ok": False,
                    "run_id": run_id,
                    "pipeline": clean_name,
                    "status": "failed",
                    "failed_step": step.name,
                    "error": str(exc),
                    "steps_completed": len(step_results),
                    "total_duration_ms": round((time.perf_counter() - start_ts) * 1000.0, 2),
                }
                return

        total_ms = round((time.perf_counter() - start_ts) * 1000.0, 2)
        final_output = step_results[-1]["output"] if step_results else ""
        yield {
            "event": "pipeline_complete",
            "ok": True,
            "run_id": run_id,
            "pipeline": clean_name,
            "description": pipeline.description,
            "task": task,
            "status": "completed",
            "steps_completed": len(step_results),
            "steps": step_results,
            "final_output": final_output,
            "total_duration_ms": total_ms,
        }
