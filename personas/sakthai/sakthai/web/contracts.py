"""The single definition of every payload the read-only web API returns.

This module is the **source of truth** for the shapes the Next.js dashboard in
``apps/sak_agent_dashboard/`` consumes. The TypeScript equivalents are generated
from it by ``scripts/gen_dashboard_types.py`` into
``apps/sak_agent_dashboard/src/lib/contracts.generated.ts``, and CI fails if the
committed file is stale — so the two runtimes cannot drift apart.

Deliberately types only: no logic, no imports beyond ``typing``. Keep it that
way. ``web/api.py`` builds values of these shapes; ``web/server.py`` serves them.

Two conventions the generator depends on:

* ``__all__`` fixes the emission order, so regenerating produces a byte-identical
  file and ``git diff --exit-code`` is a valid staleness check.
* The type vocabulary is small on purpose — ``str``, ``int``, ``float``,
  ``bool``, ``X | None``, ``list[X]``, ``dict[str, X]``, ``Literal[...]``, other
  ``TypedDict``s, and ``object`` (rendered ``unknown``). Anything outside it
  raises in the generator rather than emitting a silently wrong TS type.
"""

from __future__ import annotations

from typing import Generic, Literal, TypedDict, TypeVar

__all__ = [
    "DataSource",
    "UNATTRIBUTED",
    "TokenStats",
    "TrendPoint",
    "ModelUsage",
    "PersonaSummary",
    "PersonasPayload",
    "MetricsPayload",
    "SessionMessage",
    "ToolCallRecord",
    "SessionSummary",
    "SessionDetail",
    "SessionsPayload",
    "FactRecord",
    "ObservationRecord",
    "GrowthSeries",
    "MemoryPayload",
    "AuditEvent",
    "AuditPayload",
    "WorkflowStepResult",
    "WorkflowRunSummary",
    "WorkflowRunDetail",
    "WorkflowsPayload",
    "ApiEnvelope",
]

T = TypeVar("T")

#: Where a payload actually came from. Carried on every envelope and surfaced in
#: the UI, so demo data can never be mistaken for live data.
DataSource = Literal["local", "api", "demo"]

#: The bucket for runs recorded before ``persona`` was written to the eval log
#: and session files. An honest "we don't know", not a guess.
UNATTRIBUTED = "unattributed"


class TokenStats(TypedDict):
    """Token counts, matching the ``usage`` block of a session log."""

    input_tokens: int
    output_tokens: int
    total_tokens: int


class TrendPoint(TypedDict):
    """One day's aggregate, derived from ``eval.jsonl`` timestamps."""

    date: str  # YYYY-MM-DD, UTC
    runs: int
    errors: int
    avg_latency_ms: float
    input_tokens: int
    output_tokens: int


class ModelUsage(TypedDict):
    """Per-model rollup, mirroring ``summarize_evals()["per_model"]``."""

    count: int
    input_tokens: int
    output_tokens: int
    avg_latency_s: float


class PersonaSummary(TypedDict):
    """One agent persona.

    ``name`` is a member of ``config.PERSONA_NAMES`` or the literal
    ``"unattributed"``. ``has_shard`` is False for a persona that has never been
    written to — its memory shard only comes into existence on first write, so
    an absent shard is a normal state, not an error.
    """

    name: str
    display_name: str
    provider: str
    model: str
    has_shard: bool
    fact_count: int
    observation_count: int
    runs: int
    errors: int
    avg_latency_ms: float
    input_tokens: int
    output_tokens: int
    last_run_at: int | None


class PersonasPayload(TypedDict):
    personas: list[PersonaSummary]
    unattributed_runs: int


class MetricsPayload(TypedDict):
    total_runs: int
    error_rate: float
    avg_latency_ms: float
    tokens: TokenStats
    stop_reasons: dict[str, int]
    per_model: dict[str, ModelUsage]
    trends: list[TrendPoint]


class SessionMessage(TypedDict):
    role: str
    content: str


class ToolCallRecord(TypedDict):
    name: str
    is_error: bool


class SessionSummary(TypedDict):
    """A session log's metadata, without its message bodies.

    ``id`` is the session filename stem (``<unix_seconds>_<32 hex>``).
    ``persona`` is None for sessions written before persona attribution existed.
    """

    id: str
    timestamp: int
    persona: str | None
    task: str
    model: str
    iterations: int
    stop_reason: str
    tokens: TokenStats
    message_count: int
    tool_call_count: int
    had_error: bool


class SessionDetail(TypedDict):
    summary: SessionSummary
    messages: list[SessionMessage]
    result_text: str
    tool_calls: list[ToolCallRecord]


class SessionsPayload(TypedDict):
    """``detail`` is populated only when a specific session id was requested."""

    sessions: list[SessionSummary]
    total: int
    detail: SessionDetail | None


class FactRecord(TypedDict):
    """A row from the ``facts`` table, tagged with the shard it came from."""

    id: int
    persona: str
    kind: str
    key: str | None
    value: str
    tags: list[str]
    created_at: int
    updated_at: int


class ObservationRecord(TypedDict):
    """A row from the ``observations`` table, tagged with its shard."""

    id: int
    persona: str
    summary: str
    weight: float
    confidence: float
    created_at: int


class GrowthSeries(TypedDict):
    """A binned time series, from ``MemoryStore.get_dashboard_aggregates``."""

    labels: list[str]
    values: list[int]


class MemoryPayload(TypedDict):
    facts: list[FactRecord]
    observations: list[ObservationRecord]
    total_facts: int
    total_observations: int
    facts_this_week: int
    observations_this_week: int
    fact_growth: GrowthSeries
    observation_growth: GrowthSeries
    kind_counts: dict[str, int]


class AuditEvent(TypedDict):
    """One line of ``~/.sakthai/audit.log``, written by ``AuditLogger``.

    ``severity`` is one of ``critical``/``high``/``medium``/``low`` as written,
    not normalised — the dashboard maps it for display.
    """

    timestamp: float
    type: str
    severity: str
    message: str
    details: dict[str, object]


class AuditPayload(TypedDict):
    events: list[AuditEvent]
    severity_counts: dict[str, int]
    total: int


class WorkflowStepResult(TypedDict):
    step_id: str
    status: str
    attempts: int
    error: str | None
    started_at: float | None
    finished_at: float | None


class WorkflowRunSummary(TypedDict):
    run_id: str
    workflow_name: str
    status: str
    started_at: float | None
    finished_at: float | None
    step_count: int
    failed_steps: int


class WorkflowRunDetail(TypedDict):
    summary: WorkflowRunSummary
    steps: list[WorkflowStepResult]


class WorkflowsPayload(TypedDict):
    runs: list[WorkflowRunSummary]


class ApiEnvelope(TypedDict, Generic[T]):
    """What every endpoint returns.

    ``source`` is the point of the whole envelope: a client can always tell
    whether it is looking at live state, a remote API, or demo data.
    """

    ok: bool
    source: DataSource
    generated_at: str  # ISO-8601 UTC
    data: T
