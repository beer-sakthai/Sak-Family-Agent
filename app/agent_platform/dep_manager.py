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
        except Exception:
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

    # 5. Fallback: venv + pip
    return DependencyConfig(
        manager="venv",
        install_cmd=f".venv/bin/pip install {pkg}",
        sync_cmd=".venv/bin/pip install -r requirements.txt",
        isolated_exec=".venv/bin/python",
    )
