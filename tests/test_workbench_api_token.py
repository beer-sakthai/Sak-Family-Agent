"""Test token resolution for workbench-1.5b-api.py script."""
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch


def test_workbench_1_5b_api_uses_env_hf_token():
    script_path = Path(__file__).parent.parent / "scripts" / "workbench" / "workbench-1.5b-api.py"
    assert script_path.exists(), f"Script not found at {script_path}"

    mock_hf_hub = MagicMock()
    mock_login = mock_hf_hub.login
    mock_hf_api = mock_hf_hub.HfApi
    mock_client = mock_hf_hub.InferenceClient

    mock_api_instance = MagicMock()
    mock_api_instance.model_info.return_value = MagicMock(
        pipeline_tag="text-generation",
        downloads=100,
        likes=10,
        id="Nanthasit/sakthai-context-1.5b-merged"
    )
    mock_hf_api.return_value = mock_api_instance

    mock_client_instance = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Test response"
    mock_choice.finish_reason = "stop"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5)
    mock_client_instance.chat_completion.return_value = mock_response
    mock_client.return_value = mock_client_instance

    with patch.dict("sys.modules", {"huggingface_hub": mock_hf_hub}), \
         patch.dict("os.environ", {"HF_TOKEN": "test_token_12345"}), \
         patch("builtins.open", MagicMock()):

        spec = importlib.util.spec_from_file_location("workbench_1_5b_api", script_path)
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)

    mock_login.assert_called_once_with(token="test_token_12345")
    mock_client.assert_called_with("Nanthasit/sakthai-context-1.5b-merged", token="test_token_12345")
