from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from sakthai.agent_platform.safety import DataLossGuardrail


class AgentEngineMode(StrEnum):
    ANTIGRAVITY = "antigravity"
    ADK = "adk"


@dataclass
class UnifiedAgentConfig:
    name: str
    engine: AgentEngineMode = AgentEngineMode.ANTIGRAVITY
    model: str = "gemini-2.5-flash"
    max_turns: int = 150
    instruction: str = "You are an autonomous AI pair programming agent."


class UnifiedAgentRuntime:
    def __init__(self, config: UnifiedAgentConfig, guardrail: DataLossGuardrail | None = None):
        self.config = config
        self.guardrail = guardrail or DataLossGuardrail()
        self._tools: dict[str, Callable[..., Any]] = {}
        self.history: list[dict[str, Any]] = []

    def register_tool(self, name: str, func: Callable[..., Any]) -> None:
        self._tools[name] = func

    def execute_tool(
        self, tool_name: str, arguments: dict[str, Any], approval_token: str | None = None
    ) -> dict[str, Any]:
        if tool_name not in self._tools:
            return {"status": "error", "error": f"Tool '{tool_name}' not registered"}

        func = self._tools[tool_name]
        try:
            raw_output = func(**arguments)
            output_str = str(raw_output)

            # Safety interceptor
            safety_check = self.guardrail.verify_or_halt(output_str, approval_token=approval_token)
            if safety_check.blocked:
                event = {
                    "tool": tool_name,
                    "arguments": arguments,
                    "status": "blocked",
                    "reason": safety_check.reason,
                    "impact": safety_check.impact,
                }
                self.history.append(event)
                return event

            event = {
                "tool": tool_name,
                "arguments": arguments,
                "status": "success",
                "output": raw_output,
            }
            self.history.append(event)
            return event
        except Exception as exc:
            event = {
                "tool": tool_name,
                "arguments": arguments,
                "status": "error",
                "error": str(exc),
            }
            self.history.append(event)
            return event
