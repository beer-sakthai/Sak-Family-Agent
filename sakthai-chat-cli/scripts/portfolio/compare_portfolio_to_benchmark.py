import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import sys
import os
from sakthai.finance import get_risk_free_rate

def compare_portfolio_to_benchmark(portfolio_csv: str, benchmark_ticker: str, output_plot: str, risk_free_rate: float | None = None):
    """
    Compares the performance of a portfolio against a benchmark.

    Args:
        portfolio_csv: Path to a CSV file containing the portfolio's historical value.
        benchmark_ticker: Ticker symbol for the benchmark (e.g., 'SPY').
        output_plot: Path to save the comparison plot image.
    """
    try:
        # --- 1. Load Portfolio Data ---
        portfolio_df = pd.read_csv(portfolio_csv, index_col='Date', parse_dates=True)
        if 'Portfolio_Value' not in portfolio_df.columns:
            print(f"Error: '{portfolio_csv}' must contain a 'Portfolio_Value' column.", file=sys.stderr)
            sys.exit(1)

        # Ensure portfolio_df is sorted by date
        portfolio_df = portfolio_df.sort_index()

        # Determine the date range from the portfolio data
        start_date = portfolio_df.index.min().strftime('%Y-%m-%d')
        end_date = portfolio_df.index.max().strftime('%Y-%m-%d')

        # --- Get Dynamic Risk-Free Rate ---
        if risk_free_rate is None:
            risk_free_rate = get_risk_free_rate()

        # --- 2. Fetch Benchmark Data ---
        benchmark_data = yf.download(benchmark_ticker, start=start_date, end=end_date)
        if benchmark_data.empty:
            print(f"Error: No benchmark data found for '{benchmark_ticker}' between {start_date} and {end_date}.", file=sys.stderr)
            sys.exit(1)

        # Use 'Close' price for benchmark
        benchmark_df = benchmark_data[['Close']].copy()
        benchmark_df.rename(columns={'Close': 'Benchmark_Value'}, inplace=True)

        # --- 3. Align Dataframes and Normalize ---
        # Merge on date index, keeping only common dates
        combined_df = pd.merge(portfolio_df[['Portfolio_Value']], benchmark_df, left_index=True, right_index=True, how='inner')

        if combined_df.empty:
            print("Error: No overlapping dates between portfolio and benchmark data. Cannot compare.", file=sys.stderr)
            sys.exit(1)

        # Normalize both to start at 1.0 for easy comparison of growth
        combined_df['Normalized_Portfolio'] = combined_df['Portfolio_Value'] / combined_df['Portfolio_Value'].iloc[0]
        combined_df['Normalized_Benchmark'] = combined_df['Benchmark_Value'] / combined_df['Benchmark_Value'].iloc[0]

        # --- 4. Calculate Performance Metrics ---
        # Portfolio Metrics
        port_total_return = (combined_df['Normalized_Portfolio'].iloc[-1] - 1) * 100
        port_daily_returns = combined_df['Normalized_Portfolio'].pct_change().dropna()
        port_volatility = port_daily_returns.std() * np.sqrt(252) * 100
        port_annualized_return = ((combined_df['Normalized_Portfolio'].iloc[-1]) ** (252 / len(combined_df)) - 1)
        port_sharpe_ratio = (port_annualized_return - risk_free_rate) / (port_volatility / 100) if port_volatility > 0 else 0

        # Benchmark Metrics
        bench_total_return = (combined_df['Normalized_Benchmark'].iloc[-1] - 1) * 100
        bench_daily_returns = combined_df['Normalized_Benchmark'].pct_change().dropna()
        bench_volatility = bench_daily_returns.std() * np.sqrt(252) * 100
        bench_annualized_return = ((combined_df['Normalized_Benchmark'].iloc[-1]) ** (252 / len(combined_df)) - 1)
        bench_sharpe_ratio = (bench_annualized_return - risk_free_rate) / (bench_volatility / 100) if bench_volatility > 0 else 0

        # --- 5. Generate and Save Plot ---
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(12, 7))

        ax.plot(combined_df.index, combined_df['Normalized_Portfolio'], label='Portfolio', color='blue')
        ax.plot(combined_df.index, combined_df['Normalized_Benchmark'], label=benchmark_ticker, color='red', linestyle='--')

        ax.set_title(f'Portfolio vs. {benchmark_ticker} Performance ({start_date} to {end_date})')
        ax.set_xlabel('Date')
        ax.set_ylabel('Normalized Value (Growth)')
        ax.legend()
        ax.grid(True)

        # Ensure output directory exists
        output_dir = os.path.dirname(output_plot)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        plt.savefig(output_plot)
        print(f"Comparison plot saved to: {output_plot}")

        # --- 6. Print Summary Report ---
        print("\n--- Portfolio vs. Benchmark Performance Report ---")
        print(f"Period: {combined_df.index.min().date()} to {combined_df.index.max().date()}")
        print("-" * 60)
        print(f"{'Metric':<25} | {'Portfolio':<15} | {benchmark_ticker:<15}")
        print("-" * 60)
        print(f"{'Total Return (%)':<25} | {port_total_return:<15.2f} | {bench_total_return:<15.2f}")
        print(f"{'Annualized Volatility (%)':<25} | {port_volatility:<15.2f} | {bench_volatility:<15.2f}")
        print(f"{'Sharpe Ratio (Ann.)':<25} | {port_sharpe_ratio:<15.2f} | {bench_sharpe_ratio:<15.2f}")
        print("-" * 60)

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
    parser = argparse.ArgumentParser(description="Compare a portfolio's performance against a benchmark.")
    parser.add_argument("portfolio_csv", type=str, help="Path to the CSV file containing portfolio historical value.")
    parser.add_argument("--benchmark", type=str, default="SPY", help="Ticker symbol for the benchmark (e.g., 'SPY'). Default is 'SPY'.")    
    parser.add_argument("--output-plot", type=str, required=True, help="Path to save the output plot image (e.g., 'portfolio_vs_benchmark.png').")

    args = parser.parse_args()

    compare_portfolio_to_benchmark(args.portfolio_csv, args.benchmark, args.output_plot)