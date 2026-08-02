"""Timestamped copy of the memory database."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from ..config import memory_db_path


def backup_memory(db_path: Path | None = None) -> Path:
    """Copy DB_PATH (default: the unscoped memory.db) to a timestamped .bak beside it."""
    db = db_path or memory_db_path()
    if not db.is_file():
        raise FileNotFoundError("No memory database exists yet.")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = db.parent / f"memory_{stamp}.db.bak"
    shutil.copy2(db, destination)
    return destination
