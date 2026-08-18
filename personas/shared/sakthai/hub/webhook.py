"""Webhook event receiver and automated dispatcher for Hugging Face events."""

from __future__ import annotations

import hashlib
import hmac
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class HubWebhookDispatcher:
    """Validates and processes incoming Hugging Face webhook events."""

    def __init__(self, secret: str | None = None) -> None:
        self.secret = secret
        self._handlers: dict[str, list[Callable[[dict[str, Any]], None]]] = {}

    def register_handler(self, event_type: str, handler: Callable[[dict[str, Any]], None]) -> None:
        """Register a callback for a specific event type (e.g. 'repo.update', 'space.build_completed')."""
        self._handlers.setdefault(event_type, []).append(handler)

    def verify_signature(self, payload_bytes: bytes, signature: str) -> bool:
        """Verify HMAC-SHA256 signature from X-Webhook-Signature header."""
        if not self.secret:
            return True
        expected = hmac.new(self.secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def dispatch(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Dispatch event payload to registered callback listeners."""
        handlers = self._handlers.get(event_type, [])
        executed = 0
        errors = []
        for handler in handlers:
            try:
                handler(payload)
                executed += 1
            except Exception as err:
                logger.error("Error executing handler for event %s: %s", event_type, err)
                errors.append(str(err))

        return {
            "event_type": event_type,
            "handlers_executed": executed,
            "success": len(errors) == 0,
            "errors": errors,
        }
