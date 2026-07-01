"""Token usage tracking for agent provider calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class UsageTracker:
    """Accumulates input/output token counts across one or more API calls."""

    input_tokens: int = 0
    output_tokens: int = 0

    def record(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        self.input_tokens += int(input_tokens or 0)
        self.output_tokens += int(output_tokens or 0)

    def total(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total(),
        }


def extract_usage(response: Any) -> dict[str, int]:
    """Pull token usage from an Anthropic/Gemini/OpenAI-compatible response."""
    usage: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}

    # Anthropic SDK response object
    usage_obj = getattr(response, "usage", None)
    if usage_obj is not None:
        usage["input_tokens"] = int(getattr(usage_obj, "input_tokens", 0) or 0)
        usage["output_tokens"] = int(getattr(usage_obj, "output_tokens", 0) or 0)
        return usage

    # Google genai response usage_metadata
    usage_meta = getattr(response, "usage_metadata", None)
    if usage_meta is not None:
        usage["input_tokens"] = int(getattr(usage_meta, "prompt_token_count", 0) or 0)
        usage["output_tokens"] = int(
            getattr(usage_meta, "candidates_token_count", 0) or 0
        )
        return usage

    # OpenAI-compatible dict or SDK object
    raw: Any = response
    if hasattr(response, "model_dump"):
        raw = response.model_dump()
    raw_usage = raw.get("usage") if isinstance(raw, dict) else None
    if isinstance(raw_usage, dict):
        usage["input_tokens"] = int(
            raw_usage.get("prompt_tokens") or raw_usage.get("input_tokens") or 0
        )
        usage["output_tokens"] = int(
            raw_usage.get("completion_tokens") or raw_usage.get("output_tokens") or 0
        )
        return usage

    return usage
