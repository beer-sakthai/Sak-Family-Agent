#!/usr/bin/env python3
"""Container healthcheck script for ServiceQuoteBot."""

from __future__ import annotations

import os
from pathlib import Path
import sys

def main() -> int:
    sakthai_home = os.getenv("SAKTHAI_HOME", "/app/data")
    data_dir = Path(sakthai_home)
    
    # Verify data directory is writable and accessible
    if not data_dir.exists():
        sys.stderr.write(f"Healthcheck failed: SAKTHAI_HOME ({data_dir}) does not exist.\n")
        return 1
        
    db_file = data_dir / "memory.db"
    # If DB exists, check readability
    if db_file.exists() and not os.access(db_file, os.R_OK):
        sys.stderr.write(f"Healthcheck failed: DB file ({db_file}) is not readable.\n")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
