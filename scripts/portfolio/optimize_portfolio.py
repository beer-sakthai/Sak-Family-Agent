import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import yfinance as yf
import sys
import os
from sakthai.finance import get_risk_free_rate

def optimize_portfolio(files: list[str], tickers: list[str], output_plot: str | None, risk_free_rate: float | None = None):
    """
    Finds the optimal portfolio weights to maximize the Sharpe Ratio.

    Args:
        files: A list of paths to the stock CSV data.
        tickers: A list of ticker symbols for labeling.
        output_plot: Optional path to save the allocation pie chart.
    """
    if len(files) != len(tickers):
        print("Error: The number of files and tickers must be the same.", file=sys.stderr)
        sys.exit(1)

    try:
        # --- 1. Load and Combine Data ---
        portfolio_df = pd.DataFrame()
        for i, file in enumerate(files):
            df = pd.read_csv(file, index_col='Date', parse_dates=True)
            portfolio_df[tickers[i]] = df['Close']

        # --- 2. Prepare Data for Optimization ---
        daily_returns = portfolio_df.pct_change().dropna()
        mean_returns = daily_returns.mean()
        cov_matrix = daily_returns.cov()
        num_assets = len(tickers)

        # --- Get Dynamic Risk-Free Rate ---
        if risk_free_rate is None:
            risk_free_rate = get_risk_free_rate()

        # --- 3. Define Optimization Functions ---
        def portfolio_performance(weights, mean_returns, cov_matrix):
            returns = np.sum(mean_returns * weights) * 252
            std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
            return returns, std

        def neg_sharpe_ratio(weights, mean_returns, cov_matrix, risk_free_rate):
            p_returns, p_std = portfolio_performance(weights, mean_returns, cov_matrix)
            if p_std == 0:
                return 0
            return -(p_returns - risk_free_rate) / p_std

        # --- 4. Run the Optimization ---
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(num_assets))
        initial_guess = num_assets * [1. / num_assets]

        opt_result = minimize(
            neg_sharpe_ratio,
            initial_guess,
            args=(mean_returns, cov_matrix, risk_free_rate),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        optimal_weights = opt_result.x

        # --- 5. Calculate and Report Results ---
        opt_return, opt_volatility = portfolio_performance(optimal_weights, mean_returns, cov_matrix)
        opt_sharpe = (opt_return - risk_free_rate) / opt_volatility if opt_volatility > 0 else 0

        print("\n--- Optimal Portfolio Allocation (Max Sharpe Ratio) ---")
        print(f"Period: {portfolio_df.index.min().date()} to {portfolio_df.index.max().date()}")
        print("\nOptimal Weights:")
        for i, ticker in enumerate(tickers):
            print(f"- {ticker}: {optimal_weights[i]:.2%}")
        print("-" * 50)
        print("Expected Performance of Optimized Portfolio:")
        print(f"  - Annualized Return:    {opt_return:.2%}")
        print(f"  - Annualized Volatility:  {opt_volatility:.2%}")
        print(f"  - Sharpe Ratio:           {opt_sharpe:.2f}")
        print("-" * 50)

        # --- 6. Generate and Save Plot ---
        if output_plot:
            plt.style.use('seaborn-v0_8-pastel')
            fig, ax = plt.subplots(figsize=(8, 8))
            
            # Filter out very small weights for cleaner plotting
            plot_weights = [w if w > 0.005 else 0 for w in optimal_weights]
            plot_labels = [tickers[i] if plot_weights[i] > 0 else '' for i in range(len(tickers))]

            ax.pie(plot_weights, labels=plot_labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title('Optimal Portfolio Allocation')
            
            plt.savefig(output_plot)
            print(f"Optimal allocation plot saved to: {output_plot}")

    except FileNotFoundError as e:
        print(f"Error: Input file not found - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during optimization: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find the optimal portfolio weights to maximize the Sharpe Ratio.")
    parser.add_argument("--files", type=str, nargs='+', required=True, help="Paths to the stock CSV files.")
    parser.add_argument("--tickers", type=str, nargs='+', required=True, help="Ticker symbols for each stock.")
    parser.add_argument("--output-plot", type=str, help="Optional path to save the output allocation pie chart (e.g., 'allocation.png').")

    args = parser.parse_args()

    if args.output_plot:
        output_dir = os.path.dirname(args.output_plot)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

    optimize_portfolio(args.files, args.tickers, args.output_plot)