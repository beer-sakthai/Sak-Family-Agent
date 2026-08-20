#!/usr/bin/env python3
"""Bridge between Hermes OAuth token and gws CLI.

Refreshes the token if expired by calling out to google_api.py, then executes
gws with the valid access token.
"""
import os
import subprocess
import sys
from pathlib import Path

# Ensure sibling modules (_hermes_home) are importable when run standalone.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from google_api import get_credentials


def get_valid_token() -> str:
    """Return a valid access token, refreshing if needed."""
    try:
        # get_credentials handles the full auth check, refresh, and save logic.
        # We just need the resulting token.
        creds = get_credentials()
        return creds.token
    except Exception as e:
        print(f"ERROR: Failed to get valid credentials: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Refresh token if needed, then exec gws with remaining args."""
    if len(sys.argv) < 2:
        print("Usage: gws_bridge.py <gws args...>", file=sys.stderr)
        sys.exit(1)

    access_token = get_valid_token()
    env = os.environ.copy()
    env["GOOGLE_WORKSPACE_CLI_TOKEN"] = access_token

    result = subprocess.run(["gws"] + sys.argv[1:], env=env)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
