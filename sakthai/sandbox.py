"""Docker sandbox for ``sakthai run --sandbox``.

Builds a minimal image from Dockerfile.sandbox (layer-cached after the first
run) and re-executes the task inside an isolated container. Only the SQLite
memory database is bind-mounted from the host; nothing else is shared.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .config import REPO_ROOT, memory_db_path

SANDBOX_IMAGE = "sakthai-sandbox:latest"
_DOCKERFILE = "Dockerfile.sandbox"


class SandboxError(RuntimeError):
    """Raised when the sandbox cannot be started."""


def _docker() -> str:
    path = shutil.which("docker")
    if path is None:
        raise SandboxError(
            "Docker is not installed or not on PATH. "
            "Install Docker Desktop (https://docs.docker.com/get-docker/) then retry."
        )
    return path


def build_image(*, force: bool = False) -> None:
    """Build (or rebuild) the sandbox image from Dockerfile.sandbox."""
    docker = _docker()
    cmd = [docker, "build", "-f", _DOCKERFILE, "-t", SANDBOX_IMAGE, "."]
    if force:
        cmd.insert(2, "--no-cache")
    result = subprocess.run(  # noqa: S603
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SandboxError(
            f"Docker build failed (exit {result.returncode}):\n{result.stderr.strip()}"
        )


def run_in_sandbox(
    task: str,
    *,
    model: str,
    max_tokens: int,
    max_iterations: int,
    max_seconds: float | None,
    provider: str | None = None,
    verbose: bool,
    no_mcp: bool = False,
    with_skills: tuple[str, ...] = (),
    fast: bool = False,
    stateless: bool = False,
    caveman: str | None = None,
    dry_run: bool = False,
    stream: bool = False,
) -> int:
    """Run the agent task inside an isolated Docker container.

    The host's memory.db is bind-mounted read-write so facts persist across
    sandbox runs. Everything else is ephemeral. Returns the container exit code.
    """
    docker = _docker()
    build_image()

    # Ensure memory.db exists — Docker would create it as a directory otherwise
    db: Path = memory_db_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    if not db.exists():
        db.touch()

    cmd: list[str] = [
        docker,
        "run",
        "--rm",
        # Pass API keys from current env
        "-e",
        "ANTHROPIC_API_KEY",
        "-e",
        "GEMINI_API_KEY",
        "-e",
        "GOOGLE_API_KEY",
        "-e",
        "OPENAI_API_KEY",
        "-e",
        "OPENAI_API_BASE",
        "-e",
        "OPENAI_BASE_URL",
        "-e",
        "OLLAMA_HOST",
        # SAKTHAI_SHELL_ALLOW is baked into the image; pass it explicitly too
        "-e",
        "SAKTHAI_SHELL_ALLOW=1",
        # Memory persistence: only the DB file, nothing else from the host
        "-v",
        f"{db}:/root/.sakthai/memory.db",
        # Hard resource limits — prevent runaway commands from starving the host
        "--memory",
        "512m",
        "--cpus",
        "1",
        # No privilege escalation inside the container
        "--security-opt",
        "no-new-privileges",
        SANDBOX_IMAGE,
        # Forward all agent flags
        "run",
        task,
        "--model",
        model,
        "--max-tokens",
        str(max_tokens),
        "--max-iterations",
        str(max_iterations),
    ]
    if provider:
        cmd.extend(["--provider", provider])
    if max_seconds is not None:
        cmd.extend(["--max-seconds", str(max_seconds)])
    if verbose:
        cmd.append("-v")
    if no_mcp:
        cmd.append("--no-mcp")
    for skill in with_skills:
        cmd.extend(["--with-skills", skill])
    if fast:
        cmd.append("--fast")
    if stateless:
        cmd.append("--stateless")
    if caveman:
        cmd.extend(["--caveman", caveman])
    if dry_run:
        cmd.append("--dry-run")
    if stream:
        cmd.append("--stream")

    proc = subprocess.run(cmd)  # noqa: S603
    return proc.returncode
