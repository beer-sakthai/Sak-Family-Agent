"""Reactive Python Dependency Manager Detection.

Detects project-level dependency managers (uv, poetry, pipenv, conda, or venv fallback)
and generates standardized package installation, project synchronization, and isolated
execution commands.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DependencyConfig:
    """Configuration and execution primitives for a detected dependency manager."""

    manager: str
    install_cmd: str
    sync_cmd: str
    isolated_exec: str


def detect_dependency_manager(
    workspace: Path | str, package: str | Sequence[str] | None = None
) -> DependencyConfig:
    """Inspect a workspace directory and return the appropriate dependency manager configuration.

    Detection precedence:
    1. uv: Detected if `uv.lock` exists or `pyproject.toml` contains `[tool.uv]`.
    2. poetry: Detected if `pyproject.toml` contains `[tool.poetry]`.
    3. pipenv: Detected if `Pipfile` exists.
    4. conda: Detected if `environment.yml` or `environment.yaml` exists.
    5. venv (default): Fallback to isolated `.venv` with `pip`.

    Args:
        workspace: Path or string path to workspace root directory.
        package: Optional package name or sequence of package names to install.

    Returns:
        DependencyConfig containing manager name, install command, sync command,
        and isolated execution binary command.
    """
    workspace = Path(workspace)
    if package is None:
        pkg = "<package>"
    elif isinstance(package, (list, tuple)):
        pkg = " ".join(package).strip() or "<package>"
    else:
        pkg = str(package).strip() or "<package>"

    uv_lock = workspace / "uv.lock"
    pyproject = workspace / "pyproject.toml"
    pipfile = workspace / "Pipfile"
    conda_env_yml = workspace / "environment.yml"
    conda_env_yaml = workspace / "environment.yaml"

    pyproject_content = ""
    if pyproject.exists():
        try:
            pyproject_content = pyproject.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            pyproject_content = ""

    # 1. uv check
    if uv_lock.exists() or "[tool.uv]" in pyproject_content:
        return DependencyConfig(
            manager="uv",
            install_cmd=f"uv add {pkg}",
            sync_cmd="uv sync",
            isolated_exec="uv run python",
        )

    # 2. poetry check
    if "[tool.poetry]" in pyproject_content:
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
    if conda_env_yml.exists() or conda_env_yaml.exists():
        env_file = "environment.yml" if conda_env_yml.exists() else "environment.yaml"
        return DependencyConfig(
            manager="conda",
            install_cmd=f"conda install {pkg}",
            sync_cmd=f"conda env create -f {env_file}",
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
