"""Remote memory synchronization."""

from __future__ import annotations

import contextlib
import ipaddress
import json
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from ..config import sakthai_home
from ..giturl import validate_git_url
from .store import SNAPSHOT_VERSION, MemoryStore

# Ceiling on the HTTP backup POST so a dead endpoint fails instead of hanging.
_HTTP_SYNC_TIMEOUT = 30.0


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Block HTTP redirects so a 3xx can't bounce a POST to an internal host."""

    def redirect_request(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        raise RuntimeError(
            "HTTP redirect refused: the sync endpoint must be a direct, "
            "pre-validated URL (redirects could target an internal host)."
        )


def _assert_safe_sync_endpoint(endpoint_url: str, *, has_secret: bool) -> None:
    """Validate an HTTP(S) sync endpoint against SSRF and cleartext exposure.

    Rejects non-http(s) schemes, plaintext ``http://`` when a bearer token
    would be sent, and any host that resolves to a private, loopback,
    link-local, or otherwise non-global address.
    """
    parsed = urllib.parse.urlparse(endpoint_url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("endpoint_url must start with http:// or https://")
    host = parsed.hostname
    if not host:
        raise ValueError("endpoint_url has no host.")
    if has_secret and parsed.scheme != "https":
        raise ValueError(
            "Refusing to send an Authorization token over plaintext http://; "
            "use https:// for the sync endpoint."
        )
    try:
        addrinfos = socket.getaddrinfo(host, parsed.port, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        raise ValueError(f"Could not resolve sync endpoint host {host!r}: {exc}") from exc
    for _family, _type, _proto, _canon, sockaddr in addrinfos:
        ip = ipaddress.ip_address(sockaddr[0])
        if not ip.is_global or ip.is_multicast:
            raise ValueError(
                f"Refusing to sync to non-public address {ip} (resolved from "
                f"{host!r}); private/loopback/link-local endpoints are blocked."
            )


def _run_git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
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

    _assert_safe_sync_endpoint(endpoint_url, has_secret=bool(api_key))

    payload = json.dumps(snapshot, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(endpoint_url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")

    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=_HTTP_SYNC_TIMEOUT) as response:  # nosec B310
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
    if remote is not None:
        remote = validate_git_url(remote)
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
    # If summary generation fails, proceed with a generic message.
    with contextlib.suppress(Exception):
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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a facts/observations JSONL export, tolerating a missing file."""
    if not path.exists():
        return []
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [json.dumps(row, ensure_ascii=False) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _merge_remote_into_store(home: Path) -> tuple[int, int]:
    """Merge facts.jsonl/observations.jsonl (as currently checked out) into the
    local store, then re-export the merged result back over those two files.

    Returns the (facts, observations) counts read from the checked-out
    snapshot and merged in (merge has no content-level dedup — that's what
    `sakthai memory deduplicate` is for).
    """
    facts_path = home / "facts.jsonl"
    obs_path = home / "observations.jsonl"

    snapshot = {
        "version": SNAPSHOT_VERSION,
        "facts": _read_jsonl(facts_path),
        "observations": _read_jsonl(obs_path),
    }

    with MemoryStore() as store:
        merged_facts, merged_obs = store.import_from_dict(snapshot, mode="merge")
        merged_snapshot = store.export_to_dict()

    _write_jsonl(facts_path, merged_snapshot.get("facts", []))
    _write_jsonl(obs_path, merged_snapshot.get("observations", []))
    return merged_facts, merged_obs


def pull_memory_from_git(remote: str | None = None) -> str:
    """Fetch a Git remote and merge its facts/observations into the local store.

    ``facts.jsonl``/``observations.jsonl`` are pure exports of the DB, always
    regenerated fresh before every sync — so fast-forwarding the local
    checkout to match the remote (``reset --hard origin/main``) loses nothing
    that isn't already durably stored in ``memory.db``. Doing that reset here
    (rather than only reactively on a push conflict) means a later `sync`
    starts from an up-to-date HEAD and won't re-merge the same remote rows.
    """
    if remote is not None:
        remote = validate_git_url(remote)
    home = sakthai_home()
    if not (home / ".git").exists():
        raise RuntimeError(
            "no local Git repository found; run `sakthai memory sync` once to initialize it"
        )

    if remote:
        remotes_proc = _run_git(["remote"], cwd=home)
        remotes = remotes_proc.stdout.splitlines()
        if "origin" not in remotes:
            _run_git(["remote", "add", "origin", remote], cwd=home)
        else:
            _run_git(["remote", "set-url", "origin", remote], cwd=home)

    _run_git(["fetch", "origin", "main"], cwd=home)
    _run_git(["reset", "--hard", "origin/main"], cwd=home)

    merged_facts, merged_obs = _merge_remote_into_store(home)
    if merged_facts == 0 and merged_obs == 0:
        return f"Pulled from {remote or 'origin'}: already up to date."
    return f"Pulled from {remote or 'origin'}: merged {merged_facts} fact(s), {merged_obs} observation(s)."


def _handle_git_conflict_and_push(home: Path, remote: str) -> str:
    """Resolve a rejected push by treating the database as the merge engine."""
    _run_git(["fetch", "origin", "main"], cwd=home)
    _run_git(["reset", "--hard", "origin/main"], cwd=home)

    _merge_remote_into_store(home)

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
