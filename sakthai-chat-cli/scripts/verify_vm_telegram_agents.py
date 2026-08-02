#!/usr/bin/env python3
"""Verify the status of the six Sak Family Telegram agents running as systemd services."""

from __future__ import annotations

import subprocess
import sys

AGENTS = ("sakking", "sakthai", "saksee", "saksit", "saktan", "sakjules")


def check_service_status(service_name: str) -> tuple[bool, str]:
    """Check if a systemd user service is active and return its status and recent logs."""
    try:
        # Check if the service is active
        is_active_proc = subprocess.run(
            ["systemctl", "--user", "is-active", service_name],
            capture_output=True,
            text=True,
            check=False,  # We check the status manually
        )
        status = is_active_proc.stdout.strip()

        if is_active_proc.returncode != 0 or status != "active":
            return False, f"Service is not active. Status: {status}"

        # Get the last 5 log lines
        logs_proc = subprocess.run(
            ["journalctl", "--user", "-u", service_name, "-n", "5", "--no-pager"],
            capture_output=True,
            text=True,
            check=False,
        )
        logs = logs_proc.stdout.strip()
        return True, f"Service is active.\nRecent logs:\n{logs}"

    except FileNotFoundError:
        return False, "Command 'systemctl' not found. Are you on the Linux VM?"
    except Exception as e:
        return False, f"An unexpected error occurred: {e}"


def main() -> int:
    """Iterate through agents, check their service status, and report results."""
    print("Verifying Sak Family VM agent services...")
    all_ok = True
    for agent in AGENTS:
        service_name = f"sakthai-telegram@{agent}.service"
        print(f"\n--- Checking: {service_name} ---")
        is_active, details = check_service_status(service_name)
        print(details)
        if not is_active:
            all_ok = False

    print("\n--- Summary ---")
    if all_ok:
        print("✅ All agent services are active and running.")
        return 0
    print("❌ One or more agent services are not active. Please review the logs above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())