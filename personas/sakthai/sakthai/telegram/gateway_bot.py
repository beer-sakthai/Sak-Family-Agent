"""Multi-Agent Telegram Gateway Bot.

Dispatches Telegram messages across all 6 Sak-Family personas with intent routing,
persona switching commands, charge inspection, and session memory.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sakthai.agent.gateway_router import PERSONA_ROLES
from sakthai.agent.session_gateway import GatewaySession, SessionManager


class TelegramGatewayDispatcher:
    """Handles Telegram incoming updates and delegates to the routed persona."""

    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self.sessions = session_manager or SessionManager()

    def handle_message(
        self,
        chat_id: int | str,
        text: str,
        user_info: Mapping[str, Any] | None = None,
    ) -> tuple[str, str, Mapping[str, Any]]:
        """Process incoming chat message and generate response with persona header.

        Returns:
            tuple of (response_text, responding_persona, metadata)
        """
        session_id = f"telegram_{chat_id}"
        session = self.sessions.get_or_create(session_id)
        stripped = text.strip()

        # Handle built-in Telegram gateway commands
        if stripped == "/start":
            return self._handle_start()
        if stripped.startswith("/persona"):
            return self._handle_persona_cmd(session, stripped)
        if stripped in ("/charge", "/status"):
            return self._handle_status(session)
        if stripped == "/reset":
            return self._handle_reset(session_id)
        if stripped == "/help":
            return self._handle_help()

        # Route regular message
        route = session.add_user_message(stripped)
        persona = route.selected_persona
        role_header = route.role_declaration

        # Generate contextual persona response body
        response_body = (
            f"Received your request regarding '{route.intent.primary_intent.value}'. "
            f"Processing with specialized capabilities of @{persona}."
        )

        full_response = f"{role_header}\n\n{response_body}"
        session.add_assistant_response(response_body, persona=persona)

        metadata = {
            "session_id": session_id,
            "persona": persona,
            "intent": route.intent.primary_intent.value,
            "confidence": f"{route.intent.confidence:.2f}",
            "charge_level": str(session.charge_levels.get(persona, 100)),
        }
        return full_response, persona, metadata

    def _handle_start(self) -> tuple[str, str, Mapping[str, Any]]:
        body = (
            "**Sak-Family Multi-Agent Gateway · Active**\n\n"
            "Welcome! I intelligently route your requests to the 6 specialized personas:\n"
            "- 🧠 **SakThai**: Core Reasoning & Adaptive Coding\n"
            "- 🏛️ **SakKing**: Architectural Vision & Strategic Design\n"
            "- 🔍 **SakSee**: Deep Research & Visual Intelligence\n"
            "- ✍️ **SakSit**: Creative Copywriting & Narrative Content\n"
            "- 🛠️ **SakJules**: Master of Automation & CI/CD\n"
            "- 📅 **SakTan**: Daily Operations & Triage Master\n\n"
            "Use `/persona <name>` to pin a persona, `/charge` to check charge status, or simply ask anything!"
        )
        return body, "gateway", {"command": "/start"}

    def _handle_persona_cmd(
        self, session: GatewaySession, text: str
    ) -> tuple[str, str, Mapping[str, Any]]:
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            current = session.active_persona
            return (
                f"Active persona: @{current} ({PERSONA_ROLES.get(current)})\n"
                f"Usage: `/persona <sakthai|sakking|saksee|saksit|sakjules|saktan>`",
                current,
                {"active_persona": current},
            )

        target = parts[1].strip().lower().lstrip("@")
        if target not in PERSONA_ROLES:
            return (
                f"Unknown persona '@{target}'. Available: {', '.join(PERSONA_ROLES.keys())}",
                session.active_persona,
                {"error": "unknown_persona"},
            )

        session.handoff(target, reason="Explicit /persona command")
        role = PERSONA_ROLES[target]
        return (
            f"Switched active persona to @{target}.\n\n{role}",
            target,
            {"active_persona": target},
        )

    def _handle_status(self, session: GatewaySession) -> tuple[str, str, Mapping[str, Any]]:
        lines = ["**Sak-Family Persona Charge Status**\n"]
        for p in PERSONA_ROLES:
            lvl = session.charge_levels.get(p, 100)
            status_icon = "🟢" if lvl >= 50 else ("🟡" if lvl >= 20 else "🔴")
            active_marker = " *(Active)*" if p == session.active_persona else ""
            lines.append(f"{status_icon} **@{p}**: {lvl}%{active_marker}")

        lines.append(f"\nTotal conversation turns: {len(session.turns)}")
        lines.append(f"Handoff events: {len(session.handoff_history)}")
        return "\n".join(lines), session.active_persona, {"turns": str(len(session.turns))}

    def _handle_reset(self, session_id: str) -> tuple[str, str, Mapping[str, Any]]:
        self.sessions.delete(session_id)
        return "Session memory reset. Starting fresh with @sakthai.", "sakthai", {"action": "reset"}

    def _handle_help(self) -> tuple[str, str, Mapping[str, Any]]:
        help_text = (
            "**Gateway Commands:**\n"
            "- `/start` - Introduction & persona overview\n"
            "- `/persona <name>` - Switch active persona explicitly\n"
            "- `/charge` - View charge levels and active turn counts\n"
            "- `/reset` - Clear conversation history and reset charge\n"
            "- `@persona_name query` - Direct a single query to a specific persona"
        )
        return help_text, "gateway", {"command": "/help"}
