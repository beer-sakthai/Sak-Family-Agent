"""Remote memory synchronization."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from ..config import sakthai_home
from .store import MemoryStore


def _run_git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """Run a Git command and raise a detailed error on failure."""
    try:
        return subprocess.run(
            ["git", *args], cwd=cwd, check=check, capture_output=True, text=True, shell=False
        )
    except subprocess.CalledProcessError as e:
        # Provide more context on failure
        print(f"Git command failed: {' '.join(e.cmd)}", file=sys.stderr)
        print(f"  Exit code: {e.returncode}", file=sys.stderr)
        print(f"  Stdout: {e.stdout.strip()}", file=sys.stderr)
        print(f"  Stderr: {e.stderr.strip()}", file=sys.stderr)
        raise


def sync_memory_via_http(endpoint_url: str, api_key: str | None = None) -> str:
    """Export memory to JSON and POST it to a remote HTTP endpoint."""
    with MemoryStore() as store:
        snapshot = store.export_to_dict()

    if not endpoint_url.startswith(("http://", "https://")):
        raise ValueError("endpoint_url must start with http:// or https://")

    payload = json.dumps(snapshot, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(endpoint_url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(req) as response:  # nosec B310
            if response.status not in (200, 201, 202, 204):
                raise RuntimeError(
                    f"HTTP Error {response.status}: {response.read().decode('utf-8', errors='ignore')}"
                )
            return f"Synced to HTTP endpoint: {endpoint_url}"
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to sync to {endpoint_url}: {e.reason}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to sync to {endpoint_url}: {e}") from e


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
        _run_git(["init"], cwd=home)
        _run_git(["branch", "-M", "main"], cwd=home)

    if remote:
        # Check if remote origin exists
        remotes_proc = _run_git(["remote"], cwd=home)
        remotes = remotes_proc.stdout.splitlines()
        if "origin" not in remotes:
            _run_git(["remote", "add", "origin", remote], cwd=home)
        else:
            _run_git(["remote", "set-url", "origin", remote], cwd=home)

    _run_git(["rm", "-q", "--ignore-unmatch", "snapshot.json"], cwd=home, check=False)
    _run_git(["add", "facts.jsonl", "observations.jsonl"], cwd=home)

    # Scope the change check to the synced artifacts: the live ``memory.db``
    # (and its WAL/SHM siblings) sit untracked in the same directory, so an
    # unscoped ``git status`` would always look dirty and push us into an empty
    # commit that aborts with a non-zero exit.
    status = _run_git(
        ["status", "--porcelain", "--", "facts.jsonl", "observations.jsonl"], cwd=home
    )
    if not status.stdout.strip():
        return "No changes to sync."

    commit_body = ""
    try:
        diff_proc = _run_git(["diff", "--", "facts.jsonl", "observations.jsonl"], cwd=home)
        added_lines = [line[1:] for line in diff_proc.stdout.splitlines() if line.startswith("+")]
        num_facts_added = sum(1 for line in added_lines if '"kind":' in line)
        num_obs_added = sum(1 for line in added_lines if '"summary":' in line)

        summary_parts = []
        if num_facts_added > 0:
            summary_parts.append(f"{num_facts_added} fact(s)")
        if num_obs_added > 0:
            summary_parts.append(f"{num_obs_added} observation(s)")

        if summary_parts:
            commit_body = f"Learned {', '.join(summary_parts)}."
    except Exception:
        # If summary generation fails, proceed with a generic message.
        pass

    commit_args = [
        "-c",
        "user.name=SakThai Agent",
        "-c",
        "user.email=agent@sakthai.local",
        "commit",
        "-m",
        "chore: memory sync",
    ]
    if commit_body:
        commit_args.extend(["-m", commit_body])
    _run_git(commit_args, cwd=home)

    if remote:
        push_status = _run_git(["push", "-u", "origin", "main"], cwd=home, check=False)
        if push_status.returncode != 0:
            return _handle_git_conflict_and_push(home, remote)
        return f"Synced to remote: {remote}"

    return "Synced locally to Git repository."


def _handle_git_conflict_and_push(home: Path, remote: str) -> str:
    """Resolve a rejected push by treating the database as the merge engine."""
    _run_git(["fetch", "origin", "main"], cwd=home)
    _run_git(["reset", "--hard", "origin/main"], cwd=home)

    facts_path = home / "facts.jsonl"
    obs_path = home / "observations.jsonl"

    remote_facts = []
    if facts_path.exists():
        for line in facts_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                remote_facts.append(json.loads(line))

    remote_obs = []
    if obs_path.exists():
        for line in obs_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                remote_obs.append(json.loads(line))

    # SNAPSHOT_VERSION is 1 (hardcoded to avoid import loops if not easily accessible)
    snapshot = {"version": 1, "facts": remote_facts, "observations": remote_obs}

    from .store import MemoryStore

    with MemoryStore() as store:
        store.import_from_dict(snapshot, mode="merge")
        merged_snapshot = store.export_to_dict()

    facts_lines = [json.dumps(f, ensure_ascii=False) for f in merged_snapshot.get("facts", [])]
    facts_path.write_text("\n".join(facts_lines) + ("\n" if facts_lines else ""), encoding="utf-8")

    obs_lines = [json.dumps(o, ensure_ascii=False) for o in merged_snapshot.get("observations", [])]
    obs_path.write_text("\n".join(obs_lines) + ("\n" if obs_lines else ""), encoding="utf-8")

    _run_git(["add", "facts.jsonl", "observations.jsonl"], cwd=home)

    status = _run_git(
        ["status", "--porcelain", "--", "facts.jsonl", "observations.jsonl"], cwd=home
    )
    if not status.stdout.strip():
        return f"Merged remote {remote} but no changes to push."

    _run_git(
        [
            "-c",
            "user.name=SakThai Agent",
            "-c",
            "user.email=agent@sakthai.local",
            "commit",
            "-m",
            "chore: memory sync auto-merge",
        ],
        cwd=home,
    )
    _run_git(["push", "-u", "origin", "main"], cwd=home)

    return f"Auto-merged remote changes and synced to remote: {remote}"
