import argparse
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

def compare_stock_performance(file1: str, file2: str, ticker1: str, ticker2: str, output_plot: str):
    """
    Compares the performance of two stocks from their historical data CSV files.

    Generates a plot of normalized closing prices and prints key performance metrics.

    Args:
        file1: Path to the first stock's CSV data.
        file2: Path to the second stock's CSV data.
        ticker1: Ticker symbol for the first stock (for labeling).
        ticker2: Ticker symbol for the second stock (for labeling).
        output_plot: Path to save the comparison plot image.
    """
    try:
        # Load data, parsing dates and setting the Date column as the index
        stock1_df = pd.read_csv(file1, index_col='Date', parse_dates=True)
        stock2_df = pd.read_csv(file2, index_col='Date', parse_dates=True)

        # --- 1. Normalize data for performance comparison ---
        # Divide each closing price by the first closing price to see percentage growth
        stock1_df['Normalized'] = stock1_df['Close'] / stock1_df['Close'].iloc[0]
        stock2_df['Normalized'] = stock2_df['Close'] / stock2_df['Close'].iloc[0]

        # --- 2. Calculate Key Performance Metrics ---
        # Total Return
        return1 = (stock1_df['Normalized'].iloc[-1] - 1) * 100
        return2 = (stock2_df['Normalized'].iloc[-1] - 1) * 100

        # Volatility (Annualized Standard Deviation of Daily Returns)
        volatility1 = stock1_df['Close'].pct_change().std() * (252 ** 0.5) * 100
        volatility2 = stock2_df['Close'].pct_change().std() * (252 ** 0.5) * 100

        # --- 3. Generate and Save Plot ---
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(12, 7))

        ax.plot(stock1_df.index, stock1_df['Normalized'], label=ticker1)
        ax.plot(stock2_df.index, stock2_df['Normalized'], label=ticker2)

        ax.set_title(f'Performance Comparison: {ticker1} vs. {ticker2}')
        ax.set_xlabel('Date')
        ax.set_ylabel('Normalized Price (Growth)')
        ax.legend()
        ax.grid(True)

        plt.savefig(output_plot)
        print(f"Comparison plot saved to: {output_plot}")

        # --- 4. Print Summary Report ---
        print("\n--- Stock Performance Comparison Report ---")
        print(f"Period: {stock1_df.index.min().date()} to {stock1_df.index.max().date()}")
        print("-" * 40)
        print(f"Metric              | {ticker1:<10} | {ticker2:<10}")
        print("-" * 40)
        print(f"Total Return (%)    | {return1:<10.2f} | {return2:<10.2f}")
        print(f"Volatility (Ann. %) | {volatility1:<10.2f} | {volatility2:<10.2f}")
        print("-" * 40)

    except FileNotFoundError as e:
        print(f"Error: Input file not found - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare the performance of two stocks from CSV files.")
    parser.add_argument("file1", type=str, help="Path to the first stock CSV file.")
    parser.add_argument("file2", type=str, help="Path to the second stock CSV file.")
    parser.add_argument("--ticker1", type=str, required=True, help="Ticker symbol for the first stock.")
    parser.add_argument("--ticker2", type=str, required=True, help="Ticker symbol for the second stock.")
    parser.add_argument("--output-plot", type=str, required=True, help="Path to save the output plot image (e.g., 'comparison.png').")

    args = parser.parse_args()

    # Ensure the output directory exists
    output_dir = os.path.dirname(args.output_plot)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    compare_stock_performance(args.file1, args.file2, args.ticker1, args.ticker2, args.output_plot)