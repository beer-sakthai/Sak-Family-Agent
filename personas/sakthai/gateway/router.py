"""Routing logic and request dispatch for the SakThai Runtime Gateway."""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Callable, Generator
from datetime import UTC, datetime
from typing import Any

from .. import __version__
from ..agent.guardrails import DEFAULT_POLICY, GuardrailAction, GuardrailPolicy
from ..agent.tools import BUILTIN_TOOLS
from ..agent_platform.agent_engine import MODEL_PRESETS
from ..agent_platform.safety import DataLossGuardrail
from ..config import redact_secrets
from .config import GatewayConfig
from .memory import GatewayMemoryManager

logger = logging.getLogger(__name__)

PERSONA_METADATA: dict[str, dict[str, Any]] = {
    "sakthai": {
        "name": "SakThai",
        "role": "Main Lead, HF Master, Orchestrator",
        "handle": "@sakthai_agent_bot",
        "default_model": "gpt-4o-mini",
        "charge_state": "Optimal",
        "primary_skills": ["SakThai-hf-ecosystem-maintenance", "Sak-ocr-and-documents"],
    },
    "sakking": {
        "name": "SakKing",
        "role": "General Assistant & Runner · Deputy 1",
        "handle": "@sakking_agent_bot",
        "default_model": "model-router",
        "charge_state": "Optimal",
        "primary_skills": ["SakKing-coding-tdd", "SakKing-coding-python-mastery"],
    },
    "saksee": {
        "name": "SakSee",
        "role": "Web / Browser Specialist · Deputy 3",
        "handle": "@saksee_agent_bot",
        "default_model": "gpt-5.4-mini",
        "charge_state": "Optimal",
        "primary_skills": ["SakSee-playwright-automation", "SakSee-web-scraping"],
    },
    "sakjules": {
        "name": "SakJules",
        "role": "GitHub, CI/CD & Automation",
        "handle": "@sakjules_agent_bot",
        "default_model": "deepseek-ai/DeepSeek-V4.1-Flash",
        "charge_state": "Optimal",
        "primary_skills": ["SakJules-github-actions-ci-cd", "SakJules-pr-workflow"],
    },
    "saksit": {
        "name": "SakSit",
        "role": "Social / Content Specialist",
        "handle": "@saksit_agent_bot",
        "default_model": "Phi-4-mini-reasoning",
        "charge_state": "Optimal",
        "primary_skills": ["SakSit-content-strategy", "SakSit-hf-model-cards"],
    },
    "saktan": {
        "name": "SakTan",
        "role": "Daily Ops · Deputy 2",
        "handle": "@saktan_agent_bot",
        "default_model": "gpt-4o-mini",
        "charge_state": "Optimal",
        "primary_skills": ["SakTan-ops-daily-rhythm", "SakTan-memory-healthcheck"],
    },
}


class GatewayRouter:
    """Dispatches HTTP requests to runtime components."""

    def __init__(
        self,
        config: GatewayConfig | None = None,
        chat_executor: Callable[..., Any] | None = None,
        guardrail: DataLossGuardrail | None = None,
        policy: GuardrailPolicy = DEFAULT_POLICY,
        memory_manager: GatewayMemoryManager | None = None,
    ) -> None:
        self.config = config or GatewayConfig()
        self.chat_executor = chat_executor
        self.guardrail = guardrail or DataLossGuardrail()
        self.policy = policy
        self.memory_manager = memory_manager or GatewayMemoryManager()
        self._start_time = time.time()

    def handle_models(self) -> dict[str, Any]:
        """Return available models in OpenAI standard format."""
        data: list[dict[str, Any]] = []
        created = 1700000000

        # Register 6 personas as first-class models
        for persona_id, meta in PERSONA_METADATA.items():
            data.append(
                {
                    "id": persona_id,
                    "object": "model",
                    "created": created,
                    "owned_by": "house-of-sak",
                    "root": persona_id,
                    "description": meta["role"],
                    "permission": [],
                    "parent": None,
                }
            )

        # Register model tier presets
        for tier, preset in MODEL_PRESETS.items():
            data.append(
                {
                    "id": preset.model_name,
                    "object": "model",
                    "created": created,
                    "owned_by": preset.provider,
                    "root": preset.model_name,
                    "description": f"[{tier.value.upper()}] {preset.description}",
                    "permission": [],
                    "parent": None,
                }
            )

        # Register legacy model aliases for backward compatibility
        legacy_aliases = [
            ("gemini-2.5-flash", "Legacy Google Gemini Flash (auto-routes to gemini-4-hydrogen)"),
            (
                "gemini-3.7-flash",
                "Legacy Google Gemini Flash Reasoning (auto-routes to gemini-4-carbon)",
            ),
        ]
        registered_ids = {item["id"] for item in data}
        for alias_id, alias_desc in legacy_aliases:
            if alias_id not in registered_ids:
                data.append(
                    {
                        "id": alias_id,
                        "object": "model",
                        "created": created,
                        "owned_by": "google",
                        "root": alias_id,
                        "description": alias_desc,
                        "permission": [],
                        "parent": None,
                    }
                )

        return {"object": "list", "data": data}

    def handle_personas(self) -> dict[str, Any]:
        """Return registered persona metadata."""
        return {
            "count": len(PERSONA_METADATA),
            "personas": PERSONA_METADATA,
        }

    def handle_persona_detail(self, persona_name: str) -> dict[str, Any] | None:
        """Return detail for single persona, or None if unknown."""
        key = persona_name.lower().strip()
        return PERSONA_METADATA.get(key)

    def handle_persona_memory(self, persona_name: str, limit: int = 10) -> dict[str, Any]:
        """Return memory statistics and recent facts for a persona."""
        key = persona_name.lower().strip()
        if key not in PERSONA_METADATA and key != "default":
            return {"ok": False, "error": f"Unknown persona '{persona_name}'"}
        target = key if key in PERSONA_METADATA else self.config.default_persona
        return self.memory_manager.get_memory_stats(target, limit=limit)

    def handle_tools(self) -> dict[str, Any]:
        """Return registered tools formatted as OpenAI functions."""
        tool_entries: list[dict[str, Any]] = []
        for tool in BUILTIN_TOOLS:
            tool_entries.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
            )
        return {"tools": tool_entries}

    def handle_tools_execute(self, body: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool with safety verification."""
        tool_name = body.get("tool") or body.get("name")
        if not tool_name or not isinstance(tool_name, str):
            return {"status": "error", "error": "Missing required field 'tool'"}

        arguments = body.get("arguments") or {}
        if not isinstance(arguments, dict):
            return {"status": "error", "error": "'arguments' must be a dictionary"}

        # Find tool
        target_tool = next((t for t in BUILTIN_TOOLS if t.name == tool_name), None)
        if target_tool is None:
            return {"status": "error", "error": f"Unknown tool '{tool_name}'"}

        # Destructive-input check. A block is final: the gateway never issues a
        # token that lets the same caller approve its own blocked request.
        for val in arguments.values():
            if isinstance(val, str):
                check = self.guardrail.verify_or_halt(val)
                if check.blocked:
                    return {
                        "status": "blocked",
                        "tool": tool_name,
                        "reason": check.reason,
                        "impact": check.impact,
                    }

        try:
            from ..memory.store import MemoryStore

            with MemoryStore() as store:
                # The same pre/post GuardrailPolicy the agent loop and MCP server enforce.
                pre_check = self.policy.check_pre_execution(target_tool, dict(arguments), store)
                if pre_check.action == GuardrailAction.DENY:
                    return {"status": "blocked", "tool": tool_name, "reason": pre_check.reason}
                final_args = (
                    pre_check.modified_args
                    if pre_check.modified_args is not None
                    else dict(arguments)
                )

                result_str = redact_secrets(target_tool.handler(final_args, store))

                post_check = self.policy.check_post_execution(
                    target_tool, final_args, result_str, False, store
                )
                if post_check.action == GuardrailAction.DENY:
                    return {"status": "blocked", "tool": tool_name, "reason": post_check.reason}

            # Output safety check
            output_check = self.guardrail.verify_or_halt(result_str)
            if output_check.blocked:
                return {
                    "status": "blocked",
                    "tool": tool_name,
                    "reason": output_check.reason,
                    "impact": output_check.impact,
                }

            return {
                "status": "success",
                "tool": tool_name,
                "output": result_str,
            }
        except Exception as exc:
            logger.exception("Failed to execute tool %s", tool_name)
            return {"status": "error", "tool": tool_name, "error": redact_secrets(str(exc))}

    def handle_chat_completion(
        self, body: dict[str, Any], headers: dict[str, str] | None = None
    ) -> tuple[dict[str, Any] | Generator[str, None, None], bool]:
        """Handle OpenAI-compatible chat completion.

        Returns (response_data_or_generator, is_stream).
        """
        messages = body.get("messages")
        if not messages or not isinstance(messages, list):
            raise ValueError("Field 'messages' is required and must be a non-empty list.")

        model = str(body.get("model") or self.config.default_persona)
        stream = bool(body.get("stream", False))

        # Extract persona
        clean_model = model.lower().strip()
        if clean_model.startswith("gateway/"):
            clean_model = clean_model.split("/", 1)[1]

        target_persona = (
            clean_model if clean_model in PERSONA_METADATA else self.config.default_persona
        )

        # Extract last user message as prompt
        prompt = ""
        for m in reversed(messages):
            if isinstance(m, dict) and m.get("role") == "user":
                prompt = str(m.get("content", ""))
                break
        if not prompt and messages:
            last = messages[-1]
            if isinstance(last, dict):
                prompt = str(last.get("content", ""))

        # Check memory control flags
        hdr = headers or {}
        disable_mem = hdr.get("x-sakthai-disable-memory", "").lower() in ("true", "1") or bool(
            body.get("disable_memory", False)
        )
        try:
            mem_limit = int(hdr.get("x-sakthai-memory-limit") or body.get("memory_limit", 5))
        except (ValueError, TypeError):
            mem_limit = 5

        # Memory context injection
        messages_to_use = [dict(m) for m in messages if isinstance(m, dict)]
        if not disable_mem:
            mem_ctx = self.memory_manager.get_memory_context(
                target_persona, query=prompt, limit=mem_limit
            )
            if mem_ctx:
                if messages_to_use and messages_to_use[0].get("role") == "system":
                    messages_to_use[0]["content"] = (
                        str(messages_to_use[0].get("content", "")) + f"\n\n{mem_ctx}"
                    )
                else:
                    messages_to_use.insert(0, {"role": "system", "content": mem_ctx})

        completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())

        def _on_finish(text: str) -> None:
            if not disable_mem and text.strip():
                self.memory_manager.record_turn(target_persona, prompt, text)

        if self.chat_executor is not None:
            raw_output = self.chat_executor(
                prompt=prompt,
                persona=target_persona,
                model=model,
                messages=messages_to_use,
                stream=stream,
            )
            if stream and isinstance(raw_output, Generator):
                return self._stream_sse(
                    completion_id, created, model, raw_output, on_done=_on_finish
                ), True
            response_text = str(raw_output)
        else:
            # Fallback simulated response acknowledging persona and request
            response_text = (
                f"[{PERSONA_METADATA.get(target_persona, {}).get('name', 'SakThai')}] "
                f"Received request for '{model}': {prompt}"
            )

        if stream:
            # Emit token stream
            def _token_gen() -> Generator[str, None, None]:
                words = response_text.split(" ")
                for i, w in enumerate(words):
                    yield w + (" " if i < len(words) - 1 else "")

            return self._stream_sse(
                completion_id, created, model, _token_gen(), on_done=_on_finish
            ), True

        # Non-streaming response
        _on_finish(response_text)
        result = {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": max(1, len(prompt.split())),
                "completion_tokens": max(1, len(response_text.split())),
                "total_tokens": max(1, len(prompt.split())) + max(1, len(response_text.split())),
            },
        }
        return result, False

    def _stream_sse(
        self,
        completion_id: str,
        created: int,
        model: str,
        tokens: Generator[str, None, None],
        on_done: Callable[[str], None] | None = None,
    ) -> Generator[str, None, None]:
        """Format tokens as Server-Sent Events (SSE)."""
        accumulated: list[str] = []
        for token in tokens:
            accumulated.append(token)
            chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": token},
                        "finish_reason": None,
                    }
                ],
            }
            yield f"data: {json.dumps(chunk)}\n\n"

        if on_done:
            try:
                on_done("".join(accumulated))
            except Exception as exc:
                logger.warning("Error in on_done stream callback: %s", exc)

        # Final stop chunk
        final_chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }
            ],
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"

    def handle_health(self) -> dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "gateway": "running",
            "version": __version__,
            "uptime_seconds": round(time.time() - self._start_time, 2),
            "timestamp": datetime.now(UTC).isoformat(),
            "personas": list(PERSONA_METADATA.keys()),
            "models_count": len(self.handle_models()["data"]),
            "tools_count": len(self.handle_tools()["tools"]),
        }

    def handle_status(self) -> dict[str, Any]:
        """System status check."""
        return {
            "status": "ok",
            "gateway": "running",
            "uptime_seconds": round(time.time() - self._start_time, 2),
        }

    def handle_saksee_status(self) -> dict[str, Any]:
        """SakSee dashboard status check."""
        return {
            "gateway": "running",
            "telegram": "connected",
            "model": "0.5B",
            "skills": 106,
        }

    def handle_model_chat(self, body: dict[str, Any]) -> dict[str, Any]:
        """Quick chat interface endpoint."""
        prompt = str(body.get("prompt", ""))
        return {
            "response": f"[SakSee] Processed: {prompt}",
            "speed": "48.2 tok/s",
            "debug": "Inference completed via Runtime Gateway",
        }

    def handle_voice_profiles(self) -> dict[str, Any]:
        """Return voice synthesis profiles across all 6 personas."""
        from .voice import GatewayVoiceHandler

        return GatewayVoiceHandler(router=self).list_voice_profiles()

    def handle_duplex_event(self, body: dict[str, Any]) -> list[dict[str, Any]]:
        """Process a duplex/WebSocket JSON event and return frame list."""
        from .voice import GatewayVoiceHandler

        handler = GatewayVoiceHandler(router=self)
        return list(handler.handle_duplex_event(body, router=self))

    def handle_team_pipelines(self) -> dict[str, Any]:
        """Return registered multi-agent team pipelines."""
        from ..team.gateway import GatewayTeamOrchestrator

        return GatewayTeamOrchestrator(router=self).list_pipelines()

    def handle_team_run(self, body: dict[str, Any]) -> dict[str, Any]:
        """Execute a multi-agent team pipeline."""
        from ..team.gateway import GatewayTeamOrchestrator

        pipeline_name = str(body.get("pipeline") or body.get("name") or "")
        task = str(body.get("task") or body.get("prompt") or "")
        gateway_url = body.get("gateway_url")
        return GatewayTeamOrchestrator(router=self).execute_pipeline(
            pipeline_name=pipeline_name,
            task=task,
            gateway_url=str(gateway_url) if gateway_url else None,
        )

    def handle_benchmark(self, body: dict[str, Any]) -> dict[str, Any]:
        """Execute a high-concurrency gateway benchmark."""
        from .bench import run_gateway_benchmark

        concurrency = int(body.get("concurrency", 10))
        num_requests = int(body.get("requests", 50))
        persona = str(body.get("persona") or self.config.default_persona)
        stream = bool(body.get("stream", True))
        return run_gateway_benchmark(
            router=self,
            concurrency=concurrency,
            num_requests=num_requests,
            persona=persona,
            stream=stream,
        )
