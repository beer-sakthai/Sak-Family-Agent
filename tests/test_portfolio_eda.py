from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

pytest.importorskip("pandas")

# Ensure repository root is on sys.path so scripts.portfolio resolves
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.portfolio.perform_eda import perform_eda  # noqa: E402


def test_perform_eda_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,name,value\n1,Alice,10.5\n2,Bob,20.0", encoding="utf-8")

    perform_eda(str(csv_file))
    captured = capsys.readouterr()

    assert "Exploratory Data Analysis Report for:" in captured.out
    assert "1. Basic Information" in captured.out
    assert "2. First 5 Rows" in captured.out
    assert "3. Descriptive Statistics (Numerical Columns)" in captured.out
    assert "4. Value Counts (Categorical Columns)" in captured.out


def test_perform_eda_no_numerical(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("name,category\nAlice,A\nBob,B", encoding="utf-8")

    perform_eda(str(csv_file))
    captured = capsys.readouterr()

    assert "3. No numerical columns found for descriptive statistics." in captured.out
    assert "4. Value Counts (Categorical Columns)" in captured.out


def test_perform_eda_no_categorical(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,value\n1,10.5\n2,20.0", encoding="utf-8")

    perform_eda(str(csv_file))
    captured = capsys.readouterr()

    assert "3. Descriptive Statistics (Numerical Columns)" in captured.out
    assert "4. No categorical columns found for value counts." in captured.out


def test_perform_eda_file_not_found(capsys: pytest.CaptureFixture[str]) -> None:
    perform_eda("non_existent_file.csv")
    captured = capsys.readouterr()

    assert "Error: The file at 'non_existent_file.csv' was not found." in captured.out


@patch("pandas.read_csv")
def test_perform_eda_read_error(mock_read_csv: Any, capsys: pytest.CaptureFixture[str]) -> None:
    mock_read_csv.side_effect = Exception("Mocked read error")

    perform_eda("dummy.csv")
    captured = capsys.readouterr()

    assert "An error occurred while reading the CSV file: Mocked read error" in captured.out
