import dataclasses
from pathlib import Path

import pytest

from app.agent_platform.dep_manager import detect_dependency_manager


def test_detect_uv_from_uv_lock(tmp_path: Path):
    (tmp_path / "uv.lock").write_text("# uv lockfile")
    config = detect_dependency_manager(tmp_path, package="requests")
    assert config.manager == "uv"
    assert config.install_cmd == "uv add requests"
    assert config.sync_cmd == "uv sync"
    assert config.isolated_exec == "uv run python"


def test_detect_uv_from_pyproject(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[tool.uv]\ndev-dependencies = []")
    config = detect_dependency_manager(tmp_path, package="ruff")
    assert config.manager == "uv"
    assert config.install_cmd == "uv add ruff"
    assert config.sync_cmd == "uv sync"
    assert config.isolated_exec == "uv run python"


def test_detect_poetry_from_pyproject(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'demo'")
    config = detect_dependency_manager(tmp_path, package="httpx")
    assert config.manager == "poetry"
    assert config.install_cmd == "poetry add httpx"
    assert config.sync_cmd == "poetry install"
    assert config.isolated_exec == "poetry run python"


def test_detect_pipenv_from_pipfile(tmp_path: Path):
    (tmp_path / "Pipfile").write_text("[packages]")
    config = detect_dependency_manager(tmp_path, package="flask")
    assert config.manager == "pipenv"
    assert config.install_cmd == "pipenv install flask"
    assert config.sync_cmd == "pipenv install"
    assert config.isolated_exec == "pipenv run python"


def test_detect_conda_from_environment_yml(tmp_path: Path):
    (tmp_path / "environment.yml").write_text("name: myenv")
    config = detect_dependency_manager(tmp_path, package="numpy")
    assert config.manager == "conda"
    assert config.install_cmd == "conda install numpy"
    assert config.sync_cmd == "conda env create -f environment.yml"
    assert config.isolated_exec == "conda run python"


def test_detect_conda_from_environment_yaml(tmp_path: Path):
    (tmp_path / "environment.yaml").write_text("name: myenv")
    config = detect_dependency_manager(tmp_path, package="scipy")
    assert config.manager == "conda"
    assert config.install_cmd == "conda install scipy"
    assert config.sync_cmd == "conda env create -f environment.yaml"
    assert config.isolated_exec == "conda run python"


def test_fallback_to_isolated_venv(tmp_path: Path):
    config = detect_dependency_manager(tmp_path, package="pydantic")
    assert config.manager == "venv"
    assert config.install_cmd == ".venv/bin/pip install pydantic"
    assert config.sync_cmd == ".venv/bin/pip install -r requirements.txt"
    assert "pip install" not in config.isolated_exec or ".venv/bin" in config.isolated_exec
    assert config.isolated_exec == ".venv/bin/python"


def test_fallback_with_generic_pyproject(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'generic-lib'")
    config = detect_dependency_manager(tmp_path, package="requests")
    assert config.manager == "venv"
    assert config.install_cmd == ".venv/bin/pip install requests"


def test_default_package_placeholder(tmp_path: Path):
    config = detect_dependency_manager(tmp_path)
    assert config.install_cmd == ".venv/bin/pip install <package>"


def test_package_as_list(tmp_path: Path):
    config = detect_dependency_manager(tmp_path, package=["requests", "pytest"])
    assert config.install_cmd == ".venv/bin/pip install requests pytest"


def test_dependency_config_immutability(tmp_path: Path):
    config = detect_dependency_manager(tmp_path)
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.manager = "other"  # type: ignore


def test_detect_dependency_manager_string_path(tmp_path: Path):
    (tmp_path / "uv.lock").write_text("# uv lockfile")
    config = detect_dependency_manager(str(tmp_path), package="black")
    assert config.manager == "uv"
    assert config.install_cmd == "uv add black"
