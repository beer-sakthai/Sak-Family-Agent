import sys
from pathlib import Path
import pytest
from unittest.mock import patch

# Modify sys.path to allow importing the script as a module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.portfolio.perform_eda import perform_eda


def test_perform_eda_success(tmp_path, capsys):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,name,value\n1,Alice,10.5\n2,Bob,20.0")

    perform_eda(str(csv_file))
    captured = capsys.readouterr()

    assert "Exploratory Data Analysis Report for:" in captured.out
    assert "1. Basic Information" in captured.out
    assert "2. First 5 Rows" in captured.out
    assert "3. Descriptive Statistics (Numerical Columns)" in captured.out
    assert "4. Value Counts (Categorical Columns)" in captured.out


def test_perform_eda_no_numerical(tmp_path, capsys):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("name,category\nAlice,A\nBob,B")

    perform_eda(str(csv_file))
    captured = capsys.readouterr()

    assert "3. No numerical columns found for descriptive statistics." in captured.out
    assert "4. Value Counts (Categorical Columns)" in captured.out


def test_perform_eda_no_categorical(tmp_path, capsys):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,value\n1,10.5\n2,20.0")

    perform_eda(str(csv_file))
    captured = capsys.readouterr()

    assert "3. Descriptive Statistics (Numerical Columns)" in captured.out
    assert "4. No categorical columns found for value counts." in captured.out


def test_perform_eda_file_not_found(capsys):
    perform_eda("non_existent_file.csv")
    captured = capsys.readouterr()

    assert "Error: The file at 'non_existent_file.csv' was not found." in captured.out


@patch("pandas.read_csv")
def test_perform_eda_read_error(mock_read_csv, capsys):
    mock_read_csv.side_effect = Exception("Mocked read error")

    perform_eda("dummy.csv")
    captured = capsys.readouterr()

    assert "An error occurred while reading the CSV file: Mocked read error" in captured.out
