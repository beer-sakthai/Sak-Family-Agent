"""Remote memory synchronization."""

from __future__ import annotations

import json
import subprocess

from ..config import sakthai_home
from .store import MemoryStore


def sync_memory_to_git(remote: str | None = None) -> str:
    """Export memory to JSONL and sync to a Git remote."""
    home = sakthai_home()
    facts_path = home / "facts.jsonl"
    obs_path = home / "observations.jsonl"

    with MemoryStore() as store:
        snapshot = store.export_to_dict()

    # Write facts
    facts_lines = [json.dumps(f, ensure_ascii=False) for f in snapshot.get("facts", [])]
    facts_path.write_text("\n".join(facts_lines) + ("\n" if facts_lines else ""), encoding="utf-8")

    # Write observations
    obs_lines = [json.dumps(o, ensure_ascii=False) for o in snapshot.get("observations", [])]
    obs_path.write_text("\n".join(obs_lines) + ("\n" if obs_lines else ""), encoding="utf-8")

    # Clean up legacy snapshot
    legacy_snapshot = home / "snapshot.json"
    if legacy_snapshot.exists():
        legacy_snapshot.unlink()

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

    subprocess.run(
        ["git", "rm", "-q", "--ignore-unmatch", "snapshot.json"],
        cwd=home,
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["git", "add", "facts.jsonl", "observations.jsonl"],
        cwd=home,
        check=True,
        capture_output=True,
    )

    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=home, check=True, capture_output=True, text=True
    )
    if not status.stdout.strip():
        return "No changes to sync."

    subprocess.run(
        [
            "git",
            "-c",
            "user.name=SakThai Agent",
            "-c",
            "user.email=agent@sakthai.local",
            "commit",
            "-m",
            "chore: memory sync",
        ],
        cwd=home,
        check=True,
        capture_output=True,
    )

    if remote:
        subprocess.run(
            ["git", "push", "-u", "origin", "main"], cwd=home, check=True, capture_output=True
        )
        return f"Synced to remote: {remote}"

    return "Synced locally to Git repository."
