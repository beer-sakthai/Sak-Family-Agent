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
