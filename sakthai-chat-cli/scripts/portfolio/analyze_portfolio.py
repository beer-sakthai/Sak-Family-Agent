import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

def analyze_portfolio(files: list[str], tickers: list[str], weights: list[float], output_plot: str):
    """
    Analyzes the performance of a portfolio constructed from multiple stock CSVs.

    Args:
        files: A list of paths to the stock CSV data.
        tickers: A list of ticker symbols for labeling.
        weights: A list of weights for each stock in the portfolio.
        output_plot: Path to save the portfolio performance plot.
        output_csv: Optional path to save the portfolio's historical value to a CSV.
    """
    # --- 1. Validate Inputs ---
    if not (len(files) == len(tickers) == len(weights)):
        print("Error: The number of files, tickers, and weights must be the same.", file=sys.stderr)
        sys.exit(1)

    if not np.isclose(sum(weights), 1.0):
        print(f"Warning: Portfolio weights sum to {sum(weights):.2f}, not 1.0. Normalizing weights.", file=sys.stderr)
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

    try:
        # --- 2. Load and Combine Data ---
        portfolio_df = pd.DataFrame()
        for i, file in enumerate(files):
            df = pd.read_csv(file, index_col='Date', parse_dates=True)
            # Use a unique column name for each stock's close price
            portfolio_df[tickers[i]] = df['Close']

        # --- 3. Calculate Portfolio Performance ---
        # Normalize prices to see growth from day 1
        normalized_df = portfolio_df / portfolio_df.iloc[0]

        # Apply weights to normalized prices
        weighted_df = normalized_df * weights

        # Sum to get total portfolio value over time
        portfolio_df['Portfolio_Value'] = weighted_df.sum(axis=1)

        # Calculate daily returns
        portfolio_df['Daily_Return'] = portfolio_df['Portfolio_Value'].pct_change()

        # --- 4. Calculate Key Performance Metrics ---
        # Total Return
        total_return = (portfolio_df['Portfolio_Value'].iloc[-1] - 1) * 100

        # Annualized Volatility
        volatility = portfolio_df['Daily_Return'].std() * np.sqrt(252) * 100

        # Sharpe Ratio (assuming 0% risk-free rate)
        # Annualized return for Sharpe calculation
        annualized_return = ((portfolio_df['Portfolio_Value'].iloc[-1]) ** (252 / len(portfolio_df)) - 1)
        sharpe_ratio = (annualized_return * 100) / volatility if volatility > 0 else 0

        # --- 5. Generate and Save Plot ---
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(12, 7))

        ax.plot(portfolio_df.index, portfolio_df['Portfolio_Value'], label='Portfolio Value', color='navy')

        ax.set_title('Portfolio Performance Over Time')
        ax.set_xlabel('Date')
        ax.set_ylabel('Normalized Portfolio Value (Growth)')
        ax.legend()
        ax.grid(True)

        plt.savefig(output_plot)
        print(f"Portfolio performance plot saved to: {output_plot}")

        if output_csv:
            # Save the portfolio value to a CSV for further analysis (e.g., benchmarking)
            portfolio_df[['Portfolio_Value']].to_csv(output_csv)
            print(f"Portfolio historical value saved to: {output_csv}")

        # --- 6. Print Summary Report ---
        print("\n--- Portfolio Performance Analysis Report ---")
        print(f"Period: {portfolio_df.index.min().date()} to {portfolio_df.index.max().date()}")
        print("\nPortfolio Composition:")
        for ticker, weight in zip(tickers, weights):
            print(f"- {ticker}: {weight:.2%}")
        print("-" * 45)
        print("Key Performance Metrics:")
        print(f"  - Total Return:        {total_return:.2f}%")
        print(f"  - Annualized Volatility: {volatility:.2f}%")
        print(f"  - Sharpe Ratio:        {sharpe_ratio:.2f}")
        print("-" * 45)

    except FileNotFoundError as e:
        print(f"Error: Input file not found - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze the performance of a stock portfolio from CSV files.")
    parser.add_argument("--files", type=str, nargs='+', required=True, help="Paths to the stock CSV files.")
    parser.add_argument("--tickers", type=str, nargs='+', required=True, help="Ticker symbols for each stock.")
    parser.add_argument("--weights", type=float, nargs='+', required=True, help="Weight for each stock in the portfolio (e.g., 0.6 0.4).")
    parser.add_argument("--output-plot", type=str, help="Path to save the output plot image (e.g., 'portfolio.png').")
    parser.add_argument("--output-csv", type=str, help="Optional. Path to save the portfolio's historical value to a CSV (e.g., 'portfolio_value.csv').")

    args = parser.parse_args()

    output_dir = os.path.dirname(args.output_plot)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    if args.output_csv:
        os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)

    analyze_portfolio(args.files, args.tickers, args.weights, args.output_plot, args.output_csv)