# tests/test_agent_platform_dep_manager.py
from pathlib import Path

from sakthai.agent_platform.dep_manager import detect_dependency_manager


def test_detect_uv_from_uv_lock(tmp_path: Path):
    (tmp_path / "uv.lock").write_text("# uv lockfile")
    config = detect_dependency_manager(tmp_path, package="requests")
    assert config.manager == "uv"
    assert config.install_cmd == "uv add requests"
    assert config.sync_cmd == "uv sync"


def test_detect_poetry_from_pyproject(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'demo'")
    config = detect_dependency_manager(tmp_path, package="httpx")
    assert config.manager == "poetry"
    assert config.install_cmd == "poetry add httpx"
    assert config.sync_cmd == "poetry install"


def test_detect_pipenv_from_pipfile(tmp_path: Path):
    (tmp_path / "Pipfile").write_text("[packages]")
    config = detect_dependency_manager(tmp_path, package="flask")
    assert config.manager == "pipenv"
    assert config.install_cmd == "pipenv install flask"


def test_detect_conda_from_environment_yml(tmp_path: Path):
    (tmp_path / "environment.yml").write_text("name: myenv")
    config = detect_dependency_manager(tmp_path, package="numpy")
    assert config.manager == "conda"
    assert config.install_cmd == "conda install numpy"


def test_fallback_to_isolated_venv(tmp_path: Path):
    config = detect_dependency_manager(tmp_path, package="pydantic")
    assert config.manager == "venv"
    assert config.install_cmd == ".venv/bin/pip install pydantic"
    assert config.sync_cmd == ".venv/bin/pip install -r requirements.txt"
    assert "pip install" not in config.isolated_exec or ".venv/bin" in config.isolated_exec
