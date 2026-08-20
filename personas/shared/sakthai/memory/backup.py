"""Timestamped copy of the memory database."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from ..config import memory_db_path


def backup_memory(db_path: Path | None = None) -> Path:
    """Copy the memory DB to ``memory_<timestamp>.db.bak`` beside it.

    ``db_path``, when given, backs up that database instead of the default
    unscoped ``memory.db`` (used to back up a persona's own shard).
    """
    db = db_path if db_path is not None else memory_db_path()
    if not db.is_file():
        raise FileNotFoundError("No memory database exists yet.")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = db.parent / f"memory_{stamp}.db.bak"
    shutil.copy2(db, destination)
    return destination
