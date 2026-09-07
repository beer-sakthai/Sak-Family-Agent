"""Check that both HTTP servers emit the expected security response headers.

Run directly; it is not wired into CI:

    uv run python3 scripts/verify_headers.py

Two servers are checked, each on the fixed port it defaults to:

- ``sakthai.web.server`` (3001) -- the maintained API server.
- ``scripts/serve_api.py`` (3002) -- the standalone dashboard/API server.

Both require a bearer token on every path except ``/health``, so the request
below comes back 401. That is fine and deliberate: the headers are attached in
``end_headers`` and so are present on the rejection too, which is exactly the
case worth guarding.

Exits non-zero if any expected header is missing from any server.
"""

from __future__ import annotations

import http.client
import os
import shlex
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_HEADERS = (
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "content-security-policy",
)


def check_server(cmd: str, port: int) -> list[str]:
    """Start ``cmd``, request ``/``, and return the expected headers it omitted."""
    print(f"\n=== {cmd} (port {port}) ===")
    proc = subprocess.Popen(  # noqa: S603
        shlex.split(cmd), shell=False, cwd=REPO_ROOT, preexec_fn=os.setsid
    )
    try:
        # Poll rather than sleeping a fixed interval: a slow import should not
        # be reported as a missing header.
        deadline = time.monotonic() + 20
        resp = None
        while time.monotonic() < deadline:
            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
                conn.request("GET", "/")
                resp = conn.getresponse()
                break
            except OSError:
                time.sleep(0.25)

        if resp is None:
            print(f"FAILED to reach the server on port {port}")
            return list(EXPECTED_HEADERS)

        headers = {k.lower(): v for k, v in resp.getheaders()}
        print(f"Status: {resp.status}")

        missing = []
        for name in EXPECTED_HEADERS:
            if name in headers:
                print(f"  ok      {name}: {headers[name]}")
            else:
                print(f"  MISSING {name}")
                missing.append(name)
        return missing
    finally:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=10)


def main() -> int:
    # serve_api.py chdirs into this directory on startup, so it has to exist.
    # It is the build output of a frontend that no longer lives in this repo
    # (the dashboard is now apps/sak_agent_dashboard), hence the placeholder.
    static_dir = REPO_ROOT / "dashboard" / "dist"
    created = not static_dir.exists()
    static_dir.mkdir(parents=True, exist_ok=True)

    try:
        missing = {
            "sakthai.web.server": check_server("uv run python3 -m sakthai.web.server", 3001),
            "scripts/serve_api.py": check_server("uv run python3 scripts/serve_api.py", 3002),
        }
    finally:
        if created:
            for leftover in sorted(static_dir.rglob("*"), reverse=True):
                leftover.unlink() if leftover.is_file() else leftover.rmdir()
            static_dir.rmdir()
            static_dir.parent.rmdir()

    failed = {name: names for name, names in missing.items() if names}
    print()
    if failed:
        for name, names in failed.items():
            print(f"FAIL {name}: missing {', '.join(names)}")
        return 1
    print("All expected security headers present on both servers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
