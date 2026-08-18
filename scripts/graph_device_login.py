#!/usr/bin/env python3
"""One-time Microsoft Graph device-code sign-in for the Outlook/Calendar tools.

Run this once (interactively) to authorize SakThai against your Microsoft
account. It performs the OAuth2 device-code flow — no client secret needed —
and caches the resulting refresh token at ~/.sakthai/graph_token.json (mode
0600), the same file `_graph_access_token()` in `agent/tools.py` reads from.
After a successful run the send_outlook_mail / read_outlook_mail /
list_calendar_events / create_calendar_event tools work with no further setup
beyond MS_GRAPH_CLIENT_ID being set.

Prerequisite: register a free app at https://entra.microsoft.com
(Entra ID -> App registrations -> New registration), then under
Authentication enable "Allow public client flows". Copy the Application
(client) ID into MS_GRAPH_CLIENT_ID (env or .env).

Usage:
    python scripts/graph_device_login.py
"""

from __future__ import annotations

import contextlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.error import HTTPError

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"

_GRAPH_SCOPES = "Mail.Send Mail.Read Calendars.ReadWrite offline_access"


def load_env_file(path: Path) -> None:
    """Populate os.environ from KEY=VALUE lines in .env (existing vars win)."""
    if not path.is_file():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def sakthai_home() -> Path:
    override = os.environ.get("SAKTHAI_HOME")
    return Path(override) if override else Path.home() / ".sakthai"


def write_token_cache(refresh_token: str) -> Path:
    path = sakthai_home() / "graph_token.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        os.chmod(str(path.parent), 0o700)
    payload = json.dumps({"refresh_token": refresh_token}).encode("utf-8")
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, payload)
    finally:
        os.close(fd)
    with contextlib.suppress(OSError):
        os.chmod(str(path), 0o600)
    return path


def post_form(url: str, fields: dict[str, str]) -> dict:
    data = urllib.parse.urlencode(fields).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request, timeout=15) as response:  # nosec B310
        return json.loads(response.read().decode("utf-8"))


def main(argv: list[str]) -> int:
    load_env_file(ENV_FILE)

    client_id = os.environ.get("MS_GRAPH_CLIENT_ID")
    tenant = os.environ.get("MS_GRAPH_TENANT_ID", "consumers")
    if not client_id:
        print(
            "MS_GRAPH_CLIENT_ID is not set (checked env and .env).\n"
            "Register a free app at https://entra.microsoft.com first — see this "
            "script's docstring.",
            file=sys.stderr,
        )
        return 2

    devicecode_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/devicecode"
    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    try:
        dc = post_form(devicecode_url, {"client_id": client_id, "scope": _GRAPH_SCOPES})
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"Failed to start device-code flow ({exc.code}): {body}", file=sys.stderr)
        return 1

    print(dc["message"])
    interval = dc.get("interval", 5)
    expires_at = time.time() + dc.get("expires_in", 900)

    while time.time() < expires_at:
        time.sleep(interval)
        try:
            tok = post_form(
                token_url,
                {
                    "client_id": client_id,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": dc["device_code"],
                },
            )
        except HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            error = body.get("error")
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                interval += 5
                continue
            print(f"Sign-in failed: {body.get('error_description', error)}", file=sys.stderr)
            return 1

        refresh_token = tok.get("refresh_token")
        if not refresh_token:
            print("No refresh_token in response — check the app's public client flow setting.",
                  file=sys.stderr)
            return 1
        path = write_token_cache(refresh_token)
        print(f"Signed in. Refresh token cached at {path}.")
        print("The Outlook/Calendar tools are ready to use.")
        return 0

    print("Device code expired before sign-in completed. Re-run and try again.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
