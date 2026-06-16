"""Remote memory synchronization."""

from __future__ import annotations

import json
import subprocess

from ..config import sakthai_home
from .store import MemoryStore


def sync_memory_to_git(remote: str | None = None) -> str:
    """Export memory to snapshot.json and sync to a Git remote."""
    home = sakthai_home()
    snapshot_path = home / "snapshot.json"

    with MemoryStore() as store:
        snapshot = store.export_to_dict()

    snapshot_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")

    # Git operations
    if not (home / ".git").exists():
        subprocess.run(["git", "init"], cwd=home, check=True, capture_output=True)
        subprocess.run(["git", "branch", "-M", "main"], cwd=home, check=True, capture_output=True)

    if remote:
        # Check if remote origin exists
        remotes = subprocess.run(
            ["git", "remote"], cwd=home, check=True, capture_output=True, text=True
        ).stdout.splitlines()
        if "origin" not in remotes:
            subprocess.run(
                ["git", "remote", "add", "origin", remote],
                cwd=home,
                check=True,
                capture_output=True,
            )
        else:
            subprocess.run(
                ["git", "remote", "set-url", "origin", remote],
                cwd=home,
                check=True,
                capture_output=True,
            )

    subprocess.run(["git", "add", "snapshot.json"], cwd=home, check=True, capture_output=True)

    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=home, check=True, capture_output=True, text=True
    )
    if not status.stdout.strip():
        return "No changes to sync."

    subprocess.run(
        ["git", "commit", "-m", "chore: memory sync"], cwd=home, check=True, capture_output=True
    )

    if remote:
        subprocess.run(
            ["git", "push", "-u", "origin", "main"], cwd=home, check=True, capture_output=True
        )
        return f"Synced to remote: {remote}"

    return "Synced locally to Git repository."
