"""Data models for Multi-Agent Self-Evolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class TrajectoryFeedback:
    """Feedback telemetry from an agent execution trajectory."""

    feedback_id: str
    persona: str
    task_type: str
    success: bool
    tool_errors: int
    duration_sec: float
    user_rating: float | None = None  # 1.0 - 5.0 or None
    error_summary: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, object]:
        return {
            "feedback_id": self.feedback_id,
            "persona": self.persona,
            "task_type": self.task_type,
            "success": self.success,
            "tool_errors": self.tool_errors,
            "duration_sec": self.duration_sec,
            "user_rating": self.user_rating,
            "error_summary": self.error_summary,
            "timestamp": self.timestamp,
        }


@dataclass
class MutationScore:
    """Benchmark evaluation scores for a prompt mutation."""

    accuracy_score: float  # 0.0 - 1.0
    tool_discipline_score: float  # 0.0 - 1.0
    conciseness_score: float  # 0.0 - 1.0
    composite_score: float  # Weighted combination
    passed_safety_gate: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "accuracy_score": round(self.accuracy_score, 4),
            "tool_discipline_score": round(self.tool_discipline_score, 4),
            "conciseness_score": round(self.conciseness_score, 4),
            "composite_score": round(self.composite_score, 4),
            "passed_safety_gate": self.passed_safety_gate,
        }


@dataclass
class EvolutionVariant:
    """A generated candidate prompt mutation for an agent persona."""

    variant_id: str
    persona: str
    generation: int
    parent_checkpoint_id: str
    prompt_diff: str
    mutated_prompt: str
    mutation_rationale: str
    score: MutationScore | None = None
    status: str = "evaluated"  # "draft", "evaluated", "promoted", "rejected"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, object]:
        return {
            "variant_id": self.variant_id,
            "persona": self.persona,
            "generation": self.generation,
            "parent_checkpoint_id": self.parent_checkpoint_id,
            "prompt_diff": self.prompt_diff,
            "mutated_prompt": self.mutated_prompt,
            "mutation_rationale": self.mutation_rationale,
            "score": self.score.to_dict() if self.score else None,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class EvolutionCheckpoint:
    """An active or archived prompt version checkpoint for a persona."""

    checkpoint_id: str
    persona: str
    generation: int
    active_prompt: str
    composite_score: float
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, object]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "persona": self.persona,
            "generation": self.generation,
            "active_prompt": self.active_prompt,
            "composite_score": round(self.composite_score, 4),
            "is_active": self.is_active,
            "created_at": self.created_at,
        }
