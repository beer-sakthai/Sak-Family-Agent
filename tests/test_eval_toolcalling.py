"""Tests for the toolcalling evaluation script."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# Ensure training/serving directory is in python path for importing eval_toolcalling
SERVING_DIR = Path(__file__).resolve().parent.parent / "training" / "serving"
if str(SERVING_DIR) not in sys.path:
    sys.path.insert(0, str(SERVING_DIR))


def _setup_mock_modules(monkeypatch: pytest.MonkeyPatch, cuda_available: bool = False):
    """Setup mock modules in sys.modules for torch, peft, and transformers."""
    mock_torch = ModuleType("torch")
    mock_torch.bfloat16 = "bfloat16"
    mock_torch.float32 = "float32"
    mock_torch.no_grad = MagicMock

    mock_cuda = MagicMock()
    mock_cuda.is_available.return_value = cuda_available
    mock_torch.cuda = mock_cuda

    mock_tokenizer = MagicMock()
    mock_inputs = MagicMock()
    mock_inputs.shape = [1, 5]
    mock_tokenizer.apply_chat_template.return_value.to.return_value = mock_inputs
    mock_tokenizer.pad_token_id = 0
    mock_tokenizer.eos_token_id = 2
    mock_tokenizer.decode.return_value = "<tool_call>...</tool_call>"

    mock_base_model = MagicMock()
    mock_peft_model_instance = MagicMock()
    mock_peft_model_instance.device = "cpu" if not cuda_available else "cuda"
    mock_peft_model_instance.generate.return_value = MagicMock()

    mock_auto_tokenizer = MagicMock()
    mock_auto_tokenizer.from_pretrained.return_value = mock_tokenizer

    mock_auto_model = MagicMock()
    mock_auto_model.from_pretrained.return_value = mock_base_model

    mock_peft_model_cls = MagicMock()
    mock_peft_model_cls.from_pretrained.return_value = mock_peft_model_instance

    mock_transformers = ModuleType("transformers")
    mock_transformers.AutoTokenizer = mock_auto_tokenizer
    mock_transformers.AutoModelForCausalLM = mock_auto_model

    mock_peft = ModuleType("peft")
    mock_peft.PeftModel = mock_peft_model_cls

    monkeypatch.setitem(sys.modules, "torch", mock_torch)
    monkeypatch.setitem(sys.modules, "transformers", mock_transformers)
    monkeypatch.setitem(sys.modules, "peft", mock_peft)

    return {
        "tokenizer": mock_tokenizer,
        "base_model": mock_base_model,
        "peft_model": mock_peft_model_instance,
        "auto_tokenizer": mock_auto_tokenizer,
        "auto_model": mock_auto_model,
        "peft_model_cls": mock_peft_model_cls,
    }


def test_eval_toolcalling_main_cpu(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test main execution path when CUDA is not available (CPU path)."""
    deps = _setup_mock_modules(monkeypatch, cuda_available=False)

    import eval_toolcalling

    importlib.reload(eval_toolcalling)
    eval_toolcalling.main()

    captured = capsys.readouterr().out
    assert (
        "Loading base Qwen/Qwen2.5-1.5B-Instruct + adapter Nanthasit/sakthai-toolcalling-1.5b-lora"
        in captured
    )
    assert "USER: Remember that I prefer dark mode in all my apps." in captured
    assert "MODEL: <tool_call>...</tool_call>" in captured

    deps["auto_tokenizer"].from_pretrained.assert_called_once_with(
        "Nanthasit/sakthai-toolcalling-1.5b-lora"
    )
    deps["auto_model"].from_pretrained.assert_called_once()
    assert deps["auto_model"].from_pretrained.call_args.kwargs["torch_dtype"] == "float32"
    assert deps["auto_model"].from_pretrained.call_args.kwargs["device_map"] is None

    deps["peft_model_cls"].from_pretrained.assert_called_once_with(
        deps["base_model"], "Nanthasit/sakthai-toolcalling-1.5b-lora"
    )
    deps["peft_model"].eval.assert_called_once()


def test_eval_toolcalling_main_gpu(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test main execution path when CUDA is available (GPU path)."""
    deps = _setup_mock_modules(monkeypatch, cuda_available=True)

    import eval_toolcalling

    importlib.reload(eval_toolcalling)
    eval_toolcalling.main()

    captured = capsys.readouterr().out
    assert "Loading base Qwen/Qwen2.5-1.5B-Instruct" in captured
    assert "USER: What does the Dream stage mean?" in captured

    deps["auto_tokenizer"].from_pretrained.assert_called_once()
    deps["auto_model"].from_pretrained.assert_called_once()
    assert deps["auto_model"].from_pretrained.call_args.kwargs["torch_dtype"] == "bfloat16"
    assert deps["auto_model"].from_pretrained.call_args.kwargs["device_map"] == "auto"

    deps["peft_model_cls"].from_pretrained.assert_called_once()


def test_eval_toolcalling_custom_env_vars(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that custom environment variables BASE_MODEL and ADAPTER_REPO are respected."""
    monkeypatch.setenv("BASE_MODEL", "custom/base-model")
    monkeypatch.setenv("ADAPTER_REPO", "custom/adapter-repo")

    deps = _setup_mock_modules(monkeypatch, cuda_available=False)

    import eval_toolcalling

    importlib.reload(eval_toolcalling)
    eval_toolcalling.main()

    captured = capsys.readouterr().out
    assert "Loading base custom/base-model + adapter custom/adapter-repo" in captured

    deps["auto_tokenizer"].from_pretrained.assert_called_once_with("custom/adapter-repo")
    deps["peft_model_cls"].from_pretrained.assert_called_once_with(
        deps["base_model"], "custom/adapter-repo"
    )
