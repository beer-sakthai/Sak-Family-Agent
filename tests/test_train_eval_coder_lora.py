"""Unit tests for dependency-free coder training helpers."""

import ast
from pathlib import Path

SCRIPT = Path("training/hf-jobs/train_eval_coder_lora.py")


def _helper(name: str):
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    node = next(
        item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name
    )
    module = ast.Module(body=[node], type_ignores=[])
    namespace = {"ast": ast, "re": __import__("re")}
    exec(compile(module, str(SCRIPT), "exec"), namespace)  # noqa: S102
    return namespace[name]


def test_extract_python_prefers_fenced_code() -> None:
    extract_python = _helper("_extract_python")

    assert extract_python("Explanation\n```python\ndef answer():\n    return 42\n```") == (
        "def answer():\n    return 42"
    )


def test_python_compiles_accepts_valid_fenced_code() -> None:
    extract_python = _helper("_extract_python")
    python_compiles = _helper("_python_compiles")
    python_compiles.__globals__["_extract_python"] = extract_python

    assert python_compiles("```python\ndef add(a, b):\n    return a + b\n```") is True
    assert python_compiles("def broken(:\n    pass") is False
