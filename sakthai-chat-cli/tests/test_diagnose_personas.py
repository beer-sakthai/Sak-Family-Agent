import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.diagnose_personas import persona_mcp_config_path

def test_persona_mcp_config_path():
    path = persona_mcp_config_path("test-persona")
    assert isinstance(path, Path)
    assert path.parts[-3:] == ("test-persona", "config", "mcp.json")
