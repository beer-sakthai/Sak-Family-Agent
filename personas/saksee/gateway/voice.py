"""Real-Time Duplex Streaming & Voice Audio Profiles for the SakThai Runtime Gateway.

Provides persona-specific voice synthesis parameters, WebSocket/duplex JSON event
framing, and bidirectional audio/text streaming handlers across all 6 personas.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Generator
from typing import Any

from .router import PERSONA_METADATA, GatewayRouter

logger = logging.getLogger(__name__)

VOICE_PROFILES: dict[str, dict[str, Any]] = {
    "sakthai": {
        "persona": "sakthai",
        "name": "SakThai",
        "voice_id": "sakthai-lead-neutral",
        "pitch": 1.0,
        "rate": 1.0,
        "lang": "en-US",
        "timbre": "Calm, authoritative lead orchestrator",
    },
    "sakking": {
        "persona": "sakking",
        "name": "SakKing",
        "voice_id": "sakking-runner-crisp",
        "pitch": 0.95,
        "rate": 1.08,
        "lang": "en-US",
        "timbre": "Fast, focused engineering specialist",
    },
    "saksee": {
        "persona": "saksee",
        "name": "SakSee",
        "voice_id": "saksee-scout-clear",
        "pitch": 1.05,
        "rate": 1.04,
        "lang": "en-US",
        "timbre": "Sharp, observant web and data scout",
    },
    "sakjules": {
        "persona": "sakjules",
        "name": "SakJules",
        "voice_id": "sakjules-ci-precision",
        "pitch": 0.92,
        "rate": 1.02,
        "lang": "en-US",
        "timbre": "Disciplined, steady automation & CI/CD master",
    },
    "saksit": {
        "persona": "saksit",
        "name": "SakSit",
        "voice_id": "saksit-story-expressive",
        "pitch": 1.08,
        "rate": 0.98,
        "lang": "en-US",
        "timbre": "Warm, articulate content & storytelling voice",
    },
    "saktan": {
        "persona": "saktan",
        "name": "SakTan",
        "voice_id": "saktan-rhythm-grounded",
        "pitch": 0.98,
        "rate": 0.95,
        "lang": "en-US",
        "timbre": "Grounded, steady daily operations steward",
    },
}


class GatewayVoiceHandler:
    """Handles voice profile discovery and duplex streaming sessions."""

    def __init__(self, router: GatewayRouter | None = None) -> None:
        self.router = router

    def list_voice_profiles(self) -> dict[str, Any]:
        """Return voice synthesis profiles for all 6 personas."""
        return {
            "count": len(VOICE_PROFILES),
            "profiles": VOICE_PROFILES,
        }

    def get_voice_profile(self, persona: str) -> dict[str, Any]:
        """Return voice synthesis parameters for a specific persona."""
        key = persona.lower().strip()
        return VOICE_PROFILES.get(key, VOICE_PROFILES["sakthai"])

    def handle_duplex_event(
        self,
        event: dict[str, Any],
        router: GatewayRouter | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Process an incoming duplex/WebSocket event and yield response frames.

        Supported event types:
        - `ping`: yields `{"type": "pong", "timestamp": ...}`
        - `voice_config`: yields `{"type": "voice_profile", "profile": ...}`
        - `audio_chunk`: transcribes/acknowledges audio packet and yields delta frames
        - `message`: streams chat completion delta frames followed by `done`
        """
        active_router = router or self.router or GatewayRouter()
        event_type = str(event.get("type") or "message").lower().strip()
        persona = str(event.get("persona") or active_router.config.default_persona).lower().strip()
        if persona not in PERSONA_METADATA:
            persona = active_router.config.default_persona

        session_id = str(event.get("session_id") or f"ws-{uuid.uuid4().hex[:10]}")
        profile = self.get_voice_profile(persona)

        if event_type == "ping":
            yield {
                "type": "pong",
                "session_id": session_id,
                "timestamp": int(time.time()),
            }
            return

        if event_type == "voice_config":
            yield {
                "type": "voice_profile",
                "session_id": session_id,
                "persona": persona,
                "profile": profile,
            }
            return

        if event_type == "audio_chunk":
            transcript = str(event.get("transcript") or event.get("content") or "").strip()
            audio_b64 = str(event.get("data") or "")
            yield {
                "type": "audio_ack",
                "session_id": session_id,
                "persona": persona,
                "bytes_received": len(audio_b64),
                "transcript": transcript or "[Voice audio frame received]",
            }
            if not transcript:
                return
            prompt = transcript
        else:
            prompt = str(event.get("content") or event.get("prompt") or "").strip()

        if not prompt:
            yield {
                "type": "error",
                "session_id": session_id,
                "error": "Empty message content or transcript in duplex event",
            }
            return

        # Yield start frame with voice profile metadata
        yield {
            "type": "start",
            "session_id": session_id,
            "persona": persona,
            "voice_profile": profile,
        }

        body = {
            "model": persona,
            "stream": True,
            "messages": [{"role": "user", "content": prompt}],
        }
        sse_gen, _ = active_router.handle_chat_completion(body)

        full_text: list[str] = []
        if isinstance(sse_gen, Generator):
            for raw_line in sse_gen:
                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue
                payload_str = line[5:].strip()
                if payload_str == "[DONE]":
                    break
                try:
                    chunk_obj = json.loads(payload_str)
                    delta = chunk_obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        full_text.append(delta)
                        yield {
                            "type": "delta",
                            "session_id": session_id,
                            "persona": persona,
                            "content": delta,
                        }
                except json.JSONDecodeError as exc:
                    logger.debug("Ignoring non-JSON SSE chunk in duplex stream: %s", exc)

        complete_content = "".join(full_text)
        yield {
            "type": "done",
            "session_id": session_id,
            "persona": persona,
            "content": complete_content,
            "voice_profile": profile,
        }
