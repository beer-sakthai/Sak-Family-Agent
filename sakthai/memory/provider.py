"""Adapter that surfaces persistent memory as a system-prompt block.

Kept as a plain class so the standalone agent (and any host runtime) can pull a
ready-made memory block without importing the store directly.
"""

from __future__ import annotations

import logging
from typing import Any

from .store import MemoryStore

logger = logging.getLogger(__name__)


class SakThaiMemoryProvider:
    """Lazily open a :class:`MemoryStore` and expose it as a prompt block."""

    def __init__(self) -> None:
        self._store: MemoryStore | None = None

    @property
    def name(self) -> str:
        return "sakthai"

    def is_available(self) -> bool:
        return True

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return []

    def initialize(self, session_id: str = "", **kwargs: Any) -> None:
        try:
            self._store = MemoryStore()
        except (
            Exception
        ) as exc:  # noqa: BLE001 — degrade gracefully if the DB is unusable
            logger.warning("SakThai memory could not initialize: %s", exc)

    def system_prompt_block(self) -> str:
        if self._store is None:
            return ""
        return self._store.render_prompt_block()

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        return self.system_prompt_block()

    def shutdown(self) -> None:
        if self._store is not None:
            self._store.close()
            self._store = None
