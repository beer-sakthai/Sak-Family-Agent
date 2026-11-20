"""Unit tests for the training and serving subsystem."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock heavy ML dependencies not required for metadata/structure testing
for mod_name in (
    "torch",
    "peft",
    "transformers",
    "accelerate",
    "huggingface_hub",
    "datasets",
    "trl",
    "bitsandbytes",
):
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_build_toolcalling_dataset_schema() -> None:
    """Verify synthetic tool-calling dataset generation and schema integrity."""
    script_path = Path("training/hf-jobs/build_toolcalling_dataset.py")
    mod = _load_module(script_path, "build_toolcalling_dataset")

    assert hasattr(mod, "TOOLS")
    assert hasattr(mod, "SYSTEM_PROMPT")
    assert hasattr(mod, "build")

    tools = mod.TOOLS
    assert len(tools) == 8
    tool_names = {t["function"]["name"] for t in tools}
    expected_tools = {
        "learn",
        "recall",
        "search",
        "forget",
        "read_file",
        "run_command",
        "send_telegram_message",
        "run_agent_loop",
    }
    assert tool_names == expected_tools

    rows = mod.build()
    assert len(rows) > 50

    # Test sample rows
    has_tool_call = False
    has_negative = False
    for row in rows:
        assert "tools" in row
        assert "messages" in row
        assert len(row["messages"]) == 3
        sys_msg, user_msg, asst_msg = row["messages"]
        assert sys_msg["role"] == "system"
        assert sys_msg["content"] == mod.SYSTEM_PROMPT
        assert user_msg["role"] == "user"
        assert asst_msg["role"] == "assistant"
        if asst_msg.get("tool_calls"):
            has_tool_call = True
            call = asst_msg["tool_calls"][0]
            assert call["type"] == "function"
            assert call["function"]["name"] in expected_tools
        else:
            has_negative = True
            assert asst_msg["content"] != ""

    assert has_tool_call, "Dataset must include positive tool-call examples"
    assert has_negative, "Dataset must include negative no-tool examples"


def test_export_ollama_modelfile_format() -> None:
    """Verify Ollama Modelfile format and system prompt interpolation."""
    script_path = Path("training/serving/export_ollama.py")
    hf_jobs_dir = str(Path("training/hf-jobs").resolve())
    if hf_jobs_dir not in sys.path:
        sys.path.insert(0, hf_jobs_dir)

    mod = _load_module(script_path, "export_ollama")
    assert hasattr(mod, "MODELFILE")
    assert hasattr(mod, "SYSTEM_PROMPT")

    rendered = mod.MODELFILE.format(system=mod.SYSTEM_PROMPT)
    assert "FROM ./sakthai-merged.gguf" in rendered
    assert 'SYSTEM """' in rendered
    assert mod.SYSTEM_PROMPT in rendered
    assert "PARAMETER temperature 0.2" in rendered
    assert 'PARAMETER stop "<|im_end|>"' in rendered


def test_eval_toolcalling_probes() -> None:
    """Verify tool-calling probe prompts and expectations."""
    script_path = Path("training/serving/eval_toolcalling.py")
    hf_jobs_dir = str(Path("training/hf-jobs").resolve())
    if hf_jobs_dir not in sys.path:
        sys.path.insert(0, hf_jobs_dir)

    mod = _load_module(script_path, "eval_toolcalling")
    assert hasattr(mod, "PROBES")
    assert len(mod.PROBES) >= 5

    for prompt, hint in mod.PROBES:
        assert isinstance(prompt, str) and len(prompt) > 0
        assert isinstance(hint, str) and len(hint) > 0


def test_submit_job_dry_run(capsys) -> None:
    """Verify that 7b submit_job.py --dry-run produces a clean plan without network calls."""
    script_path = Path("training/sakthai-7b-lora/submit_job.py")
    mod = _load_module(script_path, "submit_job_7b")

    test_args = ["submit_job.py", "--dry-run"]
    orig_argv = sys.argv
    try:
        sys.argv = test_args
        mod.main()
    finally:
        sys.argv = orig_argv

    captured = capsys.readouterr()
    assert "[dry-run]" in captured.out
    assert "HF Jobs 7B Training Submission Plan" in captured.out
    assert "train.py" in captured.out
