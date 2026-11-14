from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from sakthai.agent_platform.safety import DataLossGuardrail


class AgentEngineMode(StrEnum):
    ANTIGRAVITY = "antigravity"
    ADK = "adk"


class ModelTier(StrEnum):
    FAST = "fast"
    REASONING = "reasoning"
    LOCAL = "local"
    LEAD = "lead"


@dataclass(frozen=True)
class ModelPreset:
    tier: ModelTier
    model_name: str
    temperature: float
    description: str
    provider: str = "google"


MODEL_PRESETS: dict[ModelTier, ModelPreset] = {
    ModelTier.FAST: ModelPreset(
        tier=ModelTier.FAST,
        model_name="gemini-2.5-flash",
        temperature=0.2,
        description="High-speed model for routine tasks, triage, and formatting",
        provider="google",
    ),
    ModelTier.REASONING: ModelPreset(
        tier=ModelTier.REASONING,
        model_name="gemini-3.7-flash",
        temperature=0.0,
        description="Deep reasoning and multi-turn planning model",
        provider="google",
    ),
    ModelTier.LOCAL: ModelPreset(
        tier=ModelTier.LOCAL,
        model_name="gemma-2-9b-it",
        temperature=0.1,
        description="Offline / edge-native model via LiteRT or Ollama",
        provider="local",
    ),
    ModelTier.LEAD: ModelPreset(
        tier=ModelTier.LEAD,
        model_name="deepseek-ai/DeepSeek-V4.1-Flash",
        temperature=0.1,
        description="Primary lead model for architectural synthesis and coordination",
        provider="openrouter",
    ),
}


def resolve_model_preset(tier: ModelTier | str) -> ModelPreset:
    """Resolve a ModelTier enum or string into its configured ModelPreset.

    Args:
        tier: Target tier (fast, reasoning, local, lead).

    Returns:
        Configured ModelPreset instance.

    Raises:
        ValueError: If the tier name is not recognized.
    """
    if isinstance(tier, str):
        try:
            tier_enum = ModelTier(tier.lower().strip())
        except ValueError:
            valid = [t.value for t in ModelTier]
            raise ValueError(f"Unknown model tier: '{tier}'. Choose from {valid}") from None
    else:
        tier_enum = tier

    if tier_enum not in MODEL_PRESETS:
        valid = [t.value for t in ModelTier]
        raise ValueError(f"Unknown model tier: '{tier_enum}'. Choose from {valid}")

    return MODEL_PRESETS[tier_enum]


@dataclass
class UnifiedAgentConfig:
    name: str
    engine: AgentEngineMode = AgentEngineMode.ANTIGRAVITY
    model: str = "gemini-2.5-flash"
    max_turns: int = 150
    instruction: str = "You are an autonomous AI pair programming agent."
    tier: ModelTier | str | None = None

    def __post_init__(self) -> None:
        if self.tier is not None:
            preset = resolve_model_preset(self.tier)
            self.model = preset.model_name


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
