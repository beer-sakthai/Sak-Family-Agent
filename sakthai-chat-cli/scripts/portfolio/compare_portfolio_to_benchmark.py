import argparse
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf

from sakthai.finance import get_risk_free_rate


def load_portfolio_data(portfolio_csv: str) -> pd.DataFrame:
    """Load and prepare historical portfolio CSV data."""
    portfolio_df = pd.read_csv(portfolio_csv, index_col="Date", parse_dates=True)
    if "Portfolio_Value" not in portfolio_df.columns:
        print(f"Error: '{portfolio_csv}' must contain a 'Portfolio_Value' column.", file=sys.stderr)
        sys.exit(1)
    return portfolio_df.sort_index()


def fetch_benchmark_data(benchmark_ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch benchmark historical data from yfinance."""
    benchmark_data = yf.download(benchmark_ticker, start=start_date, end=end_date)
    if benchmark_data.empty:
        print(
            f"Error: No benchmark data found for '{benchmark_ticker}' between {start_date} and {end_date}.",
            file=sys.stderr,
        )
        sys.exit(1)
    benchmark_df = benchmark_data[["Close"]].copy()
    benchmark_df.rename(columns={"Close": "Benchmark_Value"}, inplace=True)
    return benchmark_df


def align_and_normalize_data(
    portfolio_df: pd.DataFrame, benchmark_df: pd.DataFrame
) -> pd.DataFrame:
    """Align portfolio and benchmark dataframes and normalize starting values to 1.0."""
    combined_df = pd.merge(
        portfolio_df[["Portfolio_Value"]],
        benchmark_df,
        left_index=True,
        right_index=True,
        how="inner",
    )

    if combined_df.empty:
        print(
            "Error: No overlapping dates between portfolio and benchmark data. Cannot compare.",
            file=sys.stderr,
        )
        sys.exit(1)

    combined_df["Normalized_Portfolio"] = (
        combined_df["Portfolio_Value"] / combined_df["Portfolio_Value"].iloc[0]
    )
    combined_df["Normalized_Benchmark"] = (
        combined_df["Benchmark_Value"] / combined_df["Benchmark_Value"].iloc[0]
    )
    return combined_df


def calculate_metrics(normalized_series: pd.Series, risk_free_rate: float) -> dict[str, float]:
    """Calculate performance metrics for a normalized asset growth series."""
    total_return = (normalized_series.iloc[-1] - 1) * 100
    daily_returns = normalized_series.pct_change().dropna()
    volatility = daily_returns.std() * np.sqrt(252) * 100
    annualized_return = (normalized_series.iloc[-1]) ** (252 / len(normalized_series)) - 1
    sharpe_ratio = (
        (annualized_return - risk_free_rate) / (volatility / 100) if volatility > 0 else 0.0
    )

    return {
        "total_return": float(total_return),
        "volatility": float(volatility),
        "annualized_return": float(annualized_return),
        "sharpe_ratio": float(sharpe_ratio),
    }


def generate_and_save_plot(
    combined_df: pd.DataFrame,
    benchmark_ticker: str,
    start_date: str,
    end_date: str,
    output_plot: str,
) -> None:
    """Generate and save the performance comparison plot."""
    plt.style.use("seaborn-v0_8-darkgrid")
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(combined_df.index, combined_df["Normalized_Portfolio"], label="Portfolio", color="blue")
    ax.plot(
        combined_df.index,
        combined_df["Normalized_Benchmark"],
        label=benchmark_ticker,
        color="red",
        linestyle="--",
    )

    ax.set_title(f"Portfolio vs. {benchmark_ticker} Performance ({start_date} to {end_date})")
    ax.set_xlabel("Date")
    ax.set_ylabel("Normalized Value (Growth)")
    ax.legend()
    ax.grid(True)

    output_dir = os.path.dirname(output_plot)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    plt.savefig(output_plot)
    plt.close(fig)
    print(f"Comparison plot saved to: {output_plot}")


def print_summary_report(
    start_date: str,
    end_date: str,
    benchmark_ticker: str,
    port_metrics: dict[str, float],
    bench_metrics: dict[str, float],
) -> None:
    """Print performance summary report to standard output."""
    print("\n--- Portfolio vs. Benchmark Performance Report ---")
    print(f"Period: {start_date} to {end_date}")
    print("-" * 60)
    print(f"{'Metric':<25} | {'Portfolio':<15} | {benchmark_ticker:<15}")
    print("-" * 60)
    print(
        f"{'Total Return (%)':<25} | {port_metrics['total_return']:<15.2f} | {bench_metrics['total_return']:<15.2f}"
    )
    print(
        f"{'Annualized Volatility (%)':<25} | {port_metrics['volatility']:<15.2f} | {bench_metrics['volatility']:<15.2f}"
    )
    print(
        f"{'Sharpe Ratio (Ann.)':<25} | {port_metrics['sharpe_ratio']:<15.2f} | {bench_metrics['sharpe_ratio']:<15.2f}"
    )
    print("-" * 60)


def compare_portfolio_to_benchmark(
    portfolio_csv: str,
    benchmark_ticker: str,
    output_plot: str,
    risk_free_rate: float | None = None,
) -> None:
    """Compares the performance of a portfolio against a benchmark."""
    try:
        portfolio_df = load_portfolio_data(portfolio_csv)

        start_date = portfolio_df.index.min().strftime("%Y-%m-%d")
        end_date = portfolio_df.index.max().strftime("%Y-%m-%d")

# Local helper: sys.path[0] is this script's directory when run directly.
from _finance import get_risk_free_rate


def load_portfolio_data(portfolio_csv: str) -> tuple[pd.DataFrame, str, str]:
    """Loads portfolio historical value CSV data and extracts the date range."""
    portfolio_df = pd.read_csv(portfolio_csv, index_col="Date", parse_dates=True)
    if "Portfolio_Value" not in portfolio_df.columns:
        print(f"Error: '{portfolio_csv}' must contain a 'Portfolio_Value' column.", file=sys.stderr)
        sys.exit(1)

    portfolio_df = portfolio_df.sort_index()
    start_date = portfolio_df.index.min().strftime("%Y-%m-%d")
    end_date = portfolio_df.index.max().strftime("%Y-%m-%d")

    return portfolio_df, start_date, end_date


def fetch_benchmark_data(benchmark_ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetches historical benchmark price data from yfinance."""
    benchmark_data = yf.download(benchmark_ticker, start=start_date, end=end_date)
    if benchmark_data.empty:
        print(
            f"Error: No benchmark data found for '{benchmark_ticker}' between {start_date} and {end_date}.",
            file=sys.stderr,
        )
        sys.exit(1)

    benchmark_df = benchmark_data[["Close"]].copy()
    benchmark_df.rename(columns={"Close": "Benchmark_Value"}, inplace=True)
    return benchmark_df


def align_and_normalize_data(
    portfolio_df: pd.DataFrame, benchmark_df: pd.DataFrame
) -> pd.DataFrame:
    """Merges portfolio and benchmark data on common dates and normalizes values to 1.0."""
    combined_df = pd.merge(
        portfolio_df[["Portfolio_Value"]],
        benchmark_df,
        left_index=True,
        right_index=True,
        how="inner",
    )

    if combined_df.empty:
        print(
            "Error: No overlapping dates between portfolio and benchmark data. Cannot compare.",
            file=sys.stderr,
        )
        sys.exit(1)

    combined_df["Normalized_Portfolio"] = (
        combined_df["Portfolio_Value"] / combined_df["Portfolio_Value"].iloc[0]
    )
    combined_df["Normalized_Benchmark"] = (
        combined_df["Benchmark_Value"] / combined_df["Benchmark_Value"].iloc[0]
    )
    return combined_df


def calculate_series_metrics(
    normalized_series: pd.Series, risk_free_rate: float
) -> dict[str, float]:
    """Calculates performance metrics for a normalized price series starting at 1.0."""
    total_return = (normalized_series.iloc[-1] - 1) * 100
    daily_returns = normalized_series.pct_change().dropna()
    volatility = daily_returns.std() * np.sqrt(252) * 100
    annualized_return = (normalized_series.iloc[-1]) ** (252 / len(normalized_series)) - 1
    sharpe_ratio = (
        (annualized_return - risk_free_rate) / (volatility / 100) if volatility > 0 else 0.0
    )

    return {
        "total_return": total_return,
        "volatility": volatility,
        "sharpe_ratio": sharpe_ratio,
    }


def plot_comparison(
    combined_df: pd.DataFrame,
    benchmark_ticker: str,
    start_date: str,
    end_date: str,
    output_plot: str,
) -> None:
    """Generates and saves comparison plot of portfolio vs benchmark."""
    plt.style.use("seaborn-v0_8-darkgrid")
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(combined_df.index, combined_df["Normalized_Portfolio"], label="Portfolio", color="blue")
    ax.plot(
        combined_df.index,
        combined_df["Normalized_Benchmark"],
        label=benchmark_ticker,
        color="red",
        linestyle="--",
    )

    ax.set_title(f"Portfolio vs. {benchmark_ticker} Performance ({start_date} to {end_date})")
    ax.set_xlabel("Date")
    ax.set_ylabel("Normalized Value (Growth)")
    ax.legend()
    ax.grid(True)

    output_dir = os.path.dirname(output_plot)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    plt.savefig(output_plot)
    plt.close(fig)
    print(f"Comparison plot saved to: {output_plot}")


def print_summary_report(
    combined_df: pd.DataFrame,
    benchmark_ticker: str,
    port_metrics: dict[str, float],
    bench_metrics: dict[str, float],
) -> None:
    """Prints performance comparison summary table to stdout."""
    print("\n--- Portfolio vs. Benchmark Performance Report ---")
    print(f"Period: {combined_df.index.min().date()} to {combined_df.index.max().date()}")
    print("-" * 60)
    print(f"{'Metric':<25} | {'Portfolio':<15} | {benchmark_ticker:<15}")
    print("-" * 60)
    print(
        f"{'Total Return (%)':<25} | {port_metrics['total_return']:<15.2f} | {bench_metrics['total_return']:<15.2f}"
    )
    print(
        f"{'Annualized Volatility (%)':<25} | {port_metrics['volatility']:<15.2f} | {bench_metrics['volatility']:<15.2f}"
    )
    print(
        f"{'Sharpe Ratio (Ann.)':<25} | {port_metrics['sharpe_ratio']:<15.2f} | {bench_metrics['sharpe_ratio']:<15.2f}"
    )
    print("-" * 60)


def compare_portfolio_to_benchmark(
    portfolio_csv: str, benchmark_ticker: str, output_plot: str, risk_free_rate: float | None = None
):
    """
    Compares the performance of a portfolio against a benchmark.

    Args:
        portfolio_csv: Path to a CSV file containing the portfolio's historical value.
        benchmark_ticker: Ticker symbol for the benchmark (e.g., 'SPY').
        output_plot: Path to save the comparison plot image.
        risk_free_rate: Optional annual risk-free rate override.
    """
    try:
        portfolio_df, start_date, end_date = load_portfolio_data(portfolio_csv)

        if risk_free_rate is None:
            risk_free_rate = get_risk_free_rate()

        benchmark_df = fetch_benchmark_data(benchmark_ticker, start_date, end_date)
        combined_df = align_and_normalize_data(portfolio_df, benchmark_df)

        port_metrics = calculate_metrics(combined_df["Normalized_Portfolio"], risk_free_rate)
        bench_metrics = calculate_metrics(combined_df["Normalized_Benchmark"], risk_free_rate)

        generate_and_save_plot(
            combined_df, benchmark_ticker, start_date, end_date, output_plot
        )

        print_summary_report(
            portfolio_df.index.min().date().strftime("%Y-%m-%d"),
            portfolio_df.index.max().date().strftime("%Y-%m-%d"),
            benchmark_ticker,
            port_metrics,
            bench_metrics,
        )
        port_metrics = calculate_series_metrics(combined_df["Normalized_Portfolio"], risk_free_rate)
        bench_metrics = calculate_series_metrics(
            combined_df["Normalized_Benchmark"], risk_free_rate
        )

        plot_comparison(combined_df, benchmark_ticker, start_date, end_date, output_plot)
        print_summary_report(combined_df, benchmark_ticker, port_metrics, bench_metrics)

    except FileNotFoundError as e:
        print(f"Error: Input file not found - {e}", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing expected column in CSV or yfinance data - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare a portfolio's performance against a benchmark."
    )
    parser.add_argument(
        "portfolio_csv",
        type=str,
        help="Path to the CSV file containing portfolio historical value.",
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        default="SPY",
        help="Ticker symbol for the benchmark (e.g., 'SPY'). Default is 'SPY'.",
    )
    parser.add_argument(
        "--output-plot",
        type=str,
        required=True,
        help="Path to save the output plot image (e.g., 'portfolio_vs_benchmark.png').",
    )

    args = parser.parse_args()

    compare_portfolio_to_benchmark(args.portfolio_csv, args.benchmark, args.output_plot)
