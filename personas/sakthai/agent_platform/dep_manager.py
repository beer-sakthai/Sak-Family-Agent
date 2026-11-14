from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DependencyConfig:
    manager: str
    install_cmd: str
    sync_cmd: str
    isolated_exec: str


def detect_dependency_manager(workspace: Path, package: str | None = None) -> DependencyConfig:
    pkg = package or "<package>"
    uv_lock = workspace / "uv.lock"
    pyproject = workspace / "pyproject.toml"
    pipfile = workspace / "Pipfile"
    conda_env = workspace / "environment.yml"
    requirements = workspace / "requirements.txt"

    # 1. uv check
    if uv_lock.exists() or (pyproject.exists() and "[tool.uv]" in pyproject.read_text()):
        return DependencyConfig(
            manager="uv",
            install_cmd=f"uv add {pkg}",
            sync_cmd="uv sync",
            isolated_exec="uv run python",
        )

    # 2. poetry check
    if pyproject.exists() and "[tool.poetry]" in pyproject.read_text():
        return DependencyConfig(
            manager="poetry",
            install_cmd=f"poetry add {pkg}",
            sync_cmd="poetry install",
            isolated_exec="poetry run python",
        )

    # 3. pipenv check
    if pipfile.exists():
        return DependencyConfig(
            manager="pipenv",
            install_cmd=f"pipenv install {pkg}",
            sync_cmd="pipenv install",
            isolated_exec="pipenv run python",
        )

    # 4. conda check
    if conda_env.exists():
        return DependencyConfig(
            manager="conda",
            install_cmd=f"conda install {pkg}",
            sync_cmd="conda env create -f environment.yml",
            isolated_exec="conda run python",
        )

    # 5. requirements.txt or default venv + pip
    return DependencyConfig(
        manager="venv",
        install_cmd=f".venv/bin/pip install {pkg}",
        sync_cmd=".venv/bin/pip install -r requirements.txt",
        isolated_exec=".venv/bin/python",
    )


PYTHON_ENV_COMMANDS: frozenset[str] = frozenset(
    {
        "python",
        "python3",
        "py",
        "pip",
        "pytest",
        "mypy",
        "ruff",
        "bandit",
        "flake8",
        "black",
        "isort",
        "pylint",
        "coverage",
        "flit",
        "hatch",
        "sphinx-build",
    }
)


def wrap_with_isolated_runner(
    command: str,
    workspace: Path | None = None,
    *,
    force: bool = False,
) -> str:
    """Wrap a command with the appropriate isolated environment runner.

    Detects the active dependency manager (uv, poetry, pipenv, conda, venv)
    and prefixes the command to ensure execution occurs inside the isolated virtual environment.

    Args:
        command: Shell command string to execute.
        workspace: Optional workspace directory. Defaults to Path.cwd().
        force: If True, wrap the command regardless of whether the base binary
            is recognized as a Python tool.

    Returns:
        The wrapped command string.
    """
    cmd = command.strip()
    if not cmd:
        return ""

    # Avoid double-wrapping
    if cmd.startswith(("uv run ", "poetry run ", "pipenv run ", "conda run ", ".venv/bin/")):
        return cmd

    # Parse primary executable token
    parts = cmd.split(maxsplit=1)
    base_exe = parts[0]
    rest = f" {parts[1]}" if len(parts) > 1 else ""

    is_py_file = base_exe.endswith(".py")
    is_py_tool = base_exe in PYTHON_ENV_COMMANDS or is_py_file

    if not force and not is_py_tool:
        return cmd

    ws = workspace or Path.cwd()
    cfg = detect_dependency_manager(ws)

    if cfg.manager in ("uv", "poetry", "pipenv", "conda"):
        runner = f"{cfg.manager} run"
        if is_py_file:
            return f"{runner} python {cmd}"
        return f"{runner} {cmd}"

    # Venv fallback
    if is_py_file:
        return f".venv/bin/python {cmd}"
    if base_exe in ("python", "python3"):
        return f".venv/bin/{base_exe}{rest}"
    return f".venv/bin/{base_exe}{rest}"
