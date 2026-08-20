"""Tests for compare_portfolio_to_benchmark script."""

import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

# Ensure scripts directory is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "portfolio"))

from compare_portfolio_to_benchmark import (  # noqa: E402
    align_and_normalize_data,
    calculate_metrics,
    compare_portfolio_to_benchmark,
    fetch_benchmark_data,
    generate_and_save_plot,
    load_portfolio_data,
    print_summary_report,
)


@pytest.fixture
def sample_portfolio_csv(tmp_path):
    csv_path = tmp_path / "portfolio.csv"
    dates = pd.date_range(start="2023-01-01", periods=5, freq="D")
    df = pd.DataFrame({"Portfolio_Value": [100.0, 102.0, 101.0, 105.0, 108.0]}, index=dates)
    df.index.name = "Date"
    df.to_csv(csv_path)
    return str(csv_path)


@pytest.fixture
def sample_invalid_csv(tmp_path):
    csv_path = tmp_path / "invalid.csv"
    dates = pd.date_range(start="2023-01-01", periods=5, freq="D")
    df = pd.DataFrame({"Wrong_Column": [100, 102, 101, 105, 108]}, index=dates)
    df.index.name = "Date"
    df.to_csv(csv_path)
    return str(csv_path)


@pytest.fixture
def sample_benchmark_df():
    dates = pd.date_range(start="2023-01-01", periods=5, freq="D")
    df = pd.DataFrame({"Close": [200.0, 202.0, 204.0, 203.0, 206.0]}, index=dates)
    df.index.name = "Date"
    return df


def test_load_portfolio_data(sample_portfolio_csv):
    df = load_portfolio_data(sample_portfolio_csv)
    assert "Portfolio_Value" in df.columns
    assert len(df) == 5


def test_load_portfolio_data_missing_column(sample_invalid_csv):
    with pytest.raises(SystemExit):
        load_portfolio_data(sample_invalid_csv)


def test_fetch_benchmark_data(sample_benchmark_df):
    with patch("yfinance.download", return_value=sample_benchmark_df):
        bench_df = fetch_benchmark_data("SPY", "2023-01-01", "2023-01-05")
        assert "Benchmark_Value" in bench_df.columns
        assert len(bench_df) == 5


def test_fetch_benchmark_data_empty():
    with patch("yfinance.download", return_value=pd.DataFrame()), pytest.raises(SystemExit):
        fetch_benchmark_data("INVALID", "2023-01-01", "2023-01-05")


def test_align_and_normalize_data():
    dates = pd.date_range(start="2023-01-01", periods=3, freq="D")
    port_df = pd.DataFrame({"Portfolio_Value": [100.0, 110.0, 120.0]}, index=dates)
    bench_df = pd.DataFrame({"Benchmark_Value": [50.0, 55.0, 60.0]}, index=dates)

    combined = align_and_normalize_data(port_df, bench_df)
    assert combined["Normalized_Portfolio"].iloc[0] == 1.0
    assert combined["Normalized_Portfolio"].iloc[-1] == 1.2
    assert combined["Normalized_Benchmark"].iloc[0] == 1.0
    assert combined["Normalized_Benchmark"].iloc[-1] == 1.2


def test_align_and_normalize_data_empty():
    dates1 = pd.date_range(start="2023-01-01", periods=2, freq="D")
    dates2 = pd.date_range(start="2024-01-01", periods=2, freq="D")
    port_df = pd.DataFrame({"Portfolio_Value": [100.0, 110.0]}, index=dates1)
    bench_df = pd.DataFrame({"Benchmark_Value": [50.0, 55.0]}, index=dates2)

    with pytest.raises(SystemExit):
        align_and_normalize_data(port_df, bench_df)


def test_calculate_metrics():
    series = pd.Series([1.0, 1.02, 1.05, 1.10])
    metrics = calculate_metrics(series, risk_free_rate=0.02)
    assert "total_return" in metrics
    assert "volatility" in metrics
    assert "sharpe_ratio" in metrics
    assert metrics["total_return"] == pytest.approx(10.0)


def test_generate_and_save_plot(tmp_path):
    dates = pd.date_range(start="2023-01-01", periods=3, freq="D")
    combined_df = pd.DataFrame(
        {"Normalized_Portfolio": [1.0, 1.1, 1.2], "Normalized_Benchmark": [1.0, 1.05, 1.1]},
        index=dates,
    )
    output_plot = str(tmp_path / "plot.png")
    generate_and_save_plot(combined_df, "SPY", "2023-01-01", "2023-01-03", output_plot)
    assert Path(output_plot).exists()


def test_print_summary_report(capsys):
    port_metrics = {"total_return": 10.0, "volatility": 5.0, "sharpe_ratio": 1.5}
    bench_metrics = {"total_return": 8.0, "volatility": 4.0, "sharpe_ratio": 1.2}
    print_summary_report("2023-01-01", "2023-01-05", "SPY", port_metrics, bench_metrics)
    captured = capsys.readouterr()
    assert "Portfolio vs. Benchmark Performance Report" in captured.out
    assert "SPY" in captured.out


def test_compare_portfolio_to_benchmark_full(sample_portfolio_csv, sample_benchmark_df, tmp_path):
    output_plot = str(tmp_path / "out_plot.png")
    with patch("yfinance.download", return_value=sample_benchmark_df):
        compare_portfolio_to_benchmark(sample_portfolio_csv, "SPY", output_plot)
    assert Path(output_plot).exists()
import ast
import os
import sys

import pytest

# Add scripts/portfolio to sys.path
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "portfolio"))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

SCRIPT_PATH = os.path.join(SCRIPT_DIR, "compare_portfolio_to_benchmark.py")


def test_compare_portfolio_to_benchmark_parses_and_has_expected_functions():
    """Verify that compare_portfolio_to_benchmark.py parses cleanly and defines modular helpers."""
    with open(SCRIPT_PATH, encoding="utf-8") as f:
        source = f.read()

    parsed = ast.parse(source, filename=SCRIPT_PATH)
    func_names = {node.name for node in ast.walk(parsed) if isinstance(node, ast.FunctionDef)}

    expected_functions = {
        "load_portfolio_data",
        "fetch_benchmark_data",
        "align_and_normalize_data",
        "calculate_series_metrics",
        "plot_comparison",
        "print_summary_report",
        "compare_portfolio_to_benchmark",
    }

    assert expected_functions.issubset(func_names)


def test_load_portfolio_data_valid(tmp_path):
    pytest.importorskip("pandas")
    from compare_portfolio_to_benchmark import load_portfolio_data

    csv_file = tmp_path / "portfolio.csv"
    csv_file.write_text("Date,Portfolio_Value\n2023-01-01,100\n2023-01-02,105\n")

    df, start_date, end_date = load_portfolio_data(str(csv_file))

    assert "Portfolio_Value" in df.columns
    assert start_date == "2023-01-01"
    assert end_date == "2023-01-02"


def test_load_portfolio_data_invalid_column(tmp_path):
    pytest.importorskip("pandas")
    from compare_portfolio_to_benchmark import load_portfolio_data

    csv_file = tmp_path / "invalid.csv"
    csv_file.write_text("Date,Wrong_Column\n2023-01-01,100\n")

    with pytest.raises(SystemExit):
        load_portfolio_data(str(csv_file))


def test_align_and_normalize_data():
    pd = pytest.importorskip("pandas")
    from compare_portfolio_to_benchmark import align_and_normalize_data

    dates = pd.date_range("2023-01-01", periods=3)
    portfolio_df = pd.DataFrame({"Portfolio_Value": [100.0, 110.0, 120.0]}, index=dates)
    benchmark_df = pd.DataFrame({"Benchmark_Value": [200.0, 210.0, 220.0]}, index=dates)

    combined = align_and_normalize_data(portfolio_df, benchmark_df)

    assert "Normalized_Portfolio" in combined.columns
    assert "Normalized_Benchmark" in combined.columns
    assert combined["Normalized_Portfolio"].iloc[0] == 1.0
    assert combined["Normalized_Benchmark"].iloc[0] == 1.0
    assert combined["Normalized_Portfolio"].iloc[1] == 1.1


def test_calculate_series_metrics():
    pd = pytest.importorskip("pandas")
    pytest.importorskip("numpy")
    from compare_portfolio_to_benchmark import calculate_series_metrics

    series = pd.Series([1.0, 1.05, 1.10])
    metrics = calculate_series_metrics(series, risk_free_rate=0.02)

    assert "total_return" in metrics
    assert "volatility" in metrics
    assert "sharpe_ratio" in metrics
    assert pytest.approx(metrics["total_return"], 0.01) == 10.0


def test_compare_portfolio_to_benchmark_end_to_end(tmp_path):
    pd = pytest.importorskip("pandas")
    pytest.importorskip("numpy")
    pytest.importorskip("matplotlib")
    pytest.importorskip("yfinance")

    from unittest.mock import patch

    from compare_portfolio_to_benchmark import compare_portfolio_to_benchmark

    csv_file = tmp_path / "portfolio.csv"
    csv_file.write_text("Date,Portfolio_Value\n2023-01-01,100\n2023-01-02,105\n2023-01-03,110\n")
    output_plot = tmp_path / "plot.png"

    dates = pd.date_range("2023-01-01", periods=3)
    fake_benchmark = pd.DataFrame({"Close": [50.0, 52.0, 54.0]}, index=dates)

    with (
        patch("yfinance.download", return_value=fake_benchmark),
        patch("compare_portfolio_to_benchmark.get_risk_free_rate", return_value=0.03),
    ):
        compare_portfolio_to_benchmark(str(csv_file), "SPY", str(output_plot), risk_free_rate=0.03)

    assert output_plot.exists()
