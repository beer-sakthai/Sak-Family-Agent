"""Multi-Agent REST & Streaming Gateway API Handler.

Exposes REST routing endpoints and Server-Sent Event (SSE) streaming
for web applications, CLI clients, and external webhook integrations.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from sakthai.agent.gateway_router import PERSONA_ROLES
from sakthai.agent.session_gateway import SessionManager


class GatewayApiHandler:
    """Handles HTTP and SSE dispatch requests for the multi-agent gateway."""

    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self.sessions = session_manager or SessionManager()

    def handle_chat_request(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[int, Mapping[str, str], str]:
        """Handle POST /api/gateway/chat.

        Expected JSON payload:
            {
                "session_id": "optional_string",
                "message": "user text query",
                "preferred_persona": "optional_persona_name"
            }
        """
        message = payload.get("message", "")
        if not isinstance(message, str) or not message.strip():
            return (
                400,
                {"Content-Type": "application/json"},
                json.dumps({"error": "Missing or empty 'message' parameter"}),
            )

        session_id = payload.get("session_id") or "default_web_session"
        preferred = payload.get("preferred_persona")
        session = self.sessions.get_or_create(session_id)

        route = session.add_user_message(message.strip())
        if preferred and preferred in PERSONA_ROLES and preferred != route.selected_persona:
            session.handoff(preferred, reason="Explicit preferred_persona in API request")
            persona = preferred
        else:
            persona = route.selected_persona

        role_decl = PERSONA_ROLES.get(persona, PERSONA_ROLES["sakthai"])
        reply_content = (
            f"Successfully routed request to @{persona}.\n\n"
            f"Intent: {route.intent.primary_intent.value} "
            f"(Confidence: {route.intent.confidence:.2f})\n"
            f"Reason: {route.routing_reason}"
        )
        assistant_msg = session.add_assistant_response(reply_content, persona=persona)

        response_data = {
            "success": True,
            "session_id": session_id,
            "persona": persona,
            "role_declaration": role_decl,
            "reply": f"{role_decl}\n\n{reply_content}",
            "intent": {
                "category": route.intent.primary_intent.value,
                "confidence": route.intent.confidence,
                "keywords": list(route.intent.detected_keywords),
            },
            "charge_level": session.charge_levels.get(persona, 100),
            "turn_count": len(session.turns),
            "handoff_count": len(session.handoff_history),
            "timestamp": assistant_msg.timestamp,
        }

        return 200, {"Content-Type": "application/json"}, json.dumps(response_data)

    def handle_sessions_request(self) -> tuple[int, Mapping[str, str], str]:
        """Handle GET /api/gateway/sessions."""
        session_ids = self.sessions.list_sessions()
        summaries = []
        for sid in session_ids:
            s = self.sessions.get(sid)
            if s:
                summaries.append(
                    {
                        "session_id": sid,
                        "active_persona": s.active_persona,
                        "turns": len(s.turns),
                        "handoffs": len(s.handoff_history),
                        "created_at": s.created_at,
                        "updated_at": s.updated_at,
                    }
                )
        return 200, {"Content-Type": "application/json"}, json.dumps({"sessions": summaries})
