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
