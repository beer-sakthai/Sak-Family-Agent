"""Timestamped copy of the memory database."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from ..config import memory_db_path


def backup_memory() -> Path:
    """Copy the memory DB to ``memory_<timestamp>.db.bak`` beside it."""
    db = memory_db_path()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = db.parent / f"memory_{stamp}.db.bak"
    shutil.copy2(db, destination)
    return destination
