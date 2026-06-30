import pytest
from pathlib import Path
from unittest.mock import patch
from evolution.core.config import get_hermes_agent_path

def test_get_hermes_agent_path_from_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Priority 1: HERMES_AGENT_REPO env var."""
    repo = tmp_path / "env-repo"
    repo.mkdir()
    monkeypatch.setenv("HERMES_AGENT_REPO", str(repo))

    assert get_hermes_agent_path() == repo

def test_get_hermes_agent_path_env_not_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If HERMES_AGENT_REPO is set but path doesn't exist, it should fall through."""
    repo = tmp_path / "non-existent"
    monkeypatch.setenv("HERMES_AGENT_REPO", str(repo))

    # Mocking Path.exists to return False for everything to see it raises
    with patch("evolution.core.config.Path.exists") as mock_exists:
        mock_exists.return_value = False
        with pytest.raises(FileNotFoundError, match="Cannot find hermes-agent repo"):
            get_hermes_agent_path()

def test_get_hermes_agent_path_from_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Priority 2: ~/.hermes/hermes-agent."""
    monkeypatch.delenv("HERMES_AGENT_REPO", raising=False)

    home = tmp_path / "fake-home"
    repo = home / ".hermes" / "hermes-agent"
    repo.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))

    # Path.home() is used in get_hermes_agent_path
    with patch("evolution.core.config.Path.home", return_value=home):
        # We need to make sure the repo exists for the mock to return True
        # But our test_get_hermes_agent_path_from_sibling test will mock exists
        # Here we can just rely on the real Path.exists if we don't mock it globally
        assert get_hermes_agent_path() == repo

def test_get_hermes_agent_path_from_sibling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Priority 3: ../hermes-agent (relative to package root)."""
    monkeypatch.delenv("HERMES_AGENT_REPO", raising=False)

    # Mock home to something non-existent
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))

    with patch("evolution.core.config.Path.home", return_value=tmp_path / "empty-home"):
        # We want to mock exists but it's tricky because it's called on instances
        # Let's mock it at the class level but we need to handle the 'self' if we use autospec or similar
        # Alternatively, we can just create the actual directories in tmp_path and
        # mock the parts that point to them.

        # Sibling path is calculated from evolution.core.config.__file__
        # sibling_path = Path(__file__).parent.parent.parent / "hermes-agent"

        import evolution.core.config as config
        fake_root = tmp_path / "project-root"
        fake_config_file = fake_root / "evolution" / "core" / "config.py"
        fake_config_file.parent.mkdir(parents=True)
        fake_config_file.touch()

        fake_sibling = fake_root / "hermes-agent"
        fake_sibling.mkdir()

        with patch("evolution.core.config.__file__", str(fake_config_file)):
            assert get_hermes_agent_path() == fake_sibling

def test_get_hermes_agent_path_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise FileNotFoundError when no repo is found."""
    monkeypatch.delenv("HERMES_AGENT_REPO", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))

    with patch("evolution.core.config.Path.home", return_value=tmp_path / "empty-home"),          patch("evolution.core.config.Path.exists", return_value=False),          pytest.raises(FileNotFoundError, match="Cannot find hermes-agent repo"):
        get_hermes_agent_path()
