from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.agent_platform.safety import DataLossGuardrail


class AgentEngineMode(StrEnum):
    ANTIGRAVITY = "antigravity"
    ADK = "adk"


@dataclass(frozen=True)
class UnifiedAgentConfig:
    name: str
    engine: AgentEngineMode = AgentEngineMode.ANTIGRAVITY
    model: str = "gemini-2.5-flash"
    max_turns: int = 150
    instruction: str = "You are an autonomous AI pair programming agent."


def _extract_string_values(obj: Any) -> list[str]:
    """Extract all string values from primitive values, dictionaries, or sequences."""
    strings: list[str] = []
    if isinstance(obj, str):
        strings.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            strings.extend(_extract_string_values(v))
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            strings.extend(_extract_string_values(item))
    return strings


class UnifiedAgentRuntime:
    def __init__(self, config: UnifiedAgentConfig, guardrail: DataLossGuardrail | None = None):
        self.config = config
        self.guardrail = guardrail or DataLossGuardrail()
        self._tools: dict[str, Callable[..., Any]] = {}
        self.history: list[dict[str, Any]] = []

    def register_tool(self, name: str, func: Callable[..., Any]) -> None:
        self._tools[name] = func

    def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        approval_token: str | None = None,
    ) -> dict[str, Any]:
        if tool_name not in self._tools:
            return {"status": "error", "error": f"Tool '{tool_name}' not registered"}

        # Pre-execution safety inspection on arguments
        for arg_str in _extract_string_values(arguments):
            pre_check = self.guardrail.verify_or_halt(arg_str, approval_token=approval_token)
            if pre_check.blocked:
                event = {
                    "tool": tool_name,
                    "arguments": dict(arguments),
                    "status": "blocked",
                    "reason": pre_check.reason,
                    "impact": pre_check.impact,
                }
                self.history.append(event)
                return event

        func = self._tools[tool_name]
        try:
            raw_output = func(**arguments)
            output_str = str(raw_output)

            # Post-execution safety inspection for tools generating commands/SQL strings
            post_check = self.guardrail.verify_or_halt(output_str, approval_token=approval_token)
            if post_check.blocked:
                event = {
                    "tool": tool_name,
                    "arguments": dict(arguments),
                    "status": "blocked",
                    "reason": post_check.reason,
                    "impact": post_check.impact,
                }
                self.history.append(event)
                return event

            event = {
                "tool": tool_name,
                "arguments": dict(arguments),
                "status": "success",
                "output": raw_output,
            }
            self.history.append(event)
            return event
        except Exception as exc:
            event = {
                "tool": tool_name,
                "arguments": dict(arguments),
                "status": "error",
                "error": str(exc),
            }
            self.history.append(event)
            return event
