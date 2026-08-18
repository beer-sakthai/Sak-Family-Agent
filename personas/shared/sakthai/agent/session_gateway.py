"""Multi-Agent Session & State Memory Bridge.

Coordinates conversation state, dynamic persona delegation/handoffs,
sliding window memory, and persona charge depletion/replenishment across sessions.
"""

from __future__ import annotations

import datetime
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from sakthai.agent.gateway_router import (
    PERSONA_ROLES,
    PersonaRouteResult,
    route_to_persona,
)


@dataclass(frozen=True)
class HandoffRecord:
    """Audit record when conversation is delegated from one persona to another."""

    from_persona: str
    to_persona: str
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


@dataclass(frozen=True)
class GatewayMessage:
    """A single turn inside a multi-agent gateway session."""

    role: str  # "user" | "assistant" | "system"
    content: str
    persona: str | None = None
    role_declaration: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    metadata: Mapping[str, str] = field(default_factory=dict)


class GatewaySession:
    """Active multi-turn session tracking persona assignments and memory."""

    def __init__(
        self,
        session_id: str,
        initial_persona: str = "sakthai",
        max_turns: int = 50,
    ) -> None:
        self.session_id = session_id
        self.active_persona = initial_persona if initial_persona in PERSONA_ROLES else "sakthai"
        self.max_turns = max_turns
        self.created_at = datetime.datetime.now(datetime.UTC).isoformat()
        self.updated_at = self.created_at
        self.turns: list[GatewayMessage] = []
        self.handoff_history: list[HandoffRecord] = []
        self.charge_levels: dict[str, int] = {p: 100 for p in PERSONA_ROLES}

    def add_user_message(self, content: str) -> PersonaRouteResult:
        """Add a user message, check for dynamic routing or handoff, and return route."""
        route = route_to_persona(content, charge_state=self.charge_levels)
        if route.selected_persona != self.active_persona:
            self.handoff(
                to_persona=route.selected_persona,
                reason=f"Auto-handoff: {route.routing_reason}",
            )

        msg = GatewayMessage(
            role="user",
            content=content,
            persona=None,
        )
        self.turns.append(msg)
        self._trim_window()
        self.updated_at = datetime.datetime.now(datetime.UTC).isoformat()
        return route

    def add_assistant_response(
        self,
        content: str,
        persona: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> GatewayMessage:
        """Record the persona's response and deduct nominal charge."""
        responding_persona = persona or self.active_persona
        role_decl = PERSONA_ROLES.get(responding_persona, PERSONA_ROLES["sakthai"])

        # Deduct nominal charge (recovers on recharge)
        current_charge = self.charge_levels.get(responding_persona, 100)
        self.charge_levels[responding_persona] = max(10, current_charge - 5)

        msg = GatewayMessage(
            role="assistant",
            content=content,
            persona=responding_persona,
            role_declaration=role_decl,
            metadata=metadata or {},
        )
        self.turns.append(msg)
        self._trim_window()
        self.updated_at = datetime.datetime.now(datetime.UTC).isoformat()
        return msg

    def handoff(self, to_persona: str, reason: str) -> HandoffRecord:
        """Explicitly transfer session control to a different persona."""
        if to_persona not in PERSONA_ROLES:
            raise ValueError(f"Invalid target persona '{to_persona}'")

        from_p = self.active_persona
        self.active_persona = to_persona
        record = HandoffRecord(from_persona=from_p, to_persona=to_persona, reason=reason)
        self.handoff_history.append(record)
        return record

    def recharge_all(self, amount: int = 100) -> None:
        """Restore all persona charge states."""
        for p in self.charge_levels:
            self.charge_levels[p] = min(100, self.charge_levels[p] + amount)

    def _trim_window(self) -> None:
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns :]


class SessionManager:
    """Thread-safe multi-agent session store."""

    def __init__(self, ttl_seconds: int = 86400) -> None:
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, GatewaySession] = {}
        self._access_times: dict[str, float] = {}
        self._lock = threading.Lock()

    def get_or_create(
        self,
        session_id: str,
        initial_persona: str = "sakthai",
    ) -> GatewaySession:
        """Retrieve an existing session or initialize a fresh one."""
        with self._lock:
            self._purge_expired()
            if session_id not in self._sessions:
                session = GatewaySession(session_id, initial_persona=initial_persona)
                self._sessions[session_id] = session
            self._access_times[session_id] = time.time()
            return self._sessions[session_id]

    def get(self, session_id: str) -> GatewaySession | None:
        """Retrieve session without auto-creation."""
        with self._lock:
            self._purge_expired()
            if session_id in self._sessions:
                self._access_times[session_id] = time.time()
                return self._sessions[session_id]
            return None

    def list_sessions(self) -> Sequence[str]:
        """Return all active session IDs."""
        with self._lock:
            self._purge_expired()
            return tuple(self._sessions.keys())

    def delete(self, session_id: str) -> bool:
        """Remove a session."""
        with self._lock:
            self._access_times.pop(session_id, None)
            return self._sessions.pop(session_id, None) is not None

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [
            sid
            for sid, last_active in self._access_times.items()
            if now - last_active > self.ttl_seconds
        ]
        for sid in expired:
            self._sessions.pop(sid, None)
            self._access_times.pop(sid, None)
