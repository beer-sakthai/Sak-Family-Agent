---
name: optimize-portfolio
description: "Finds the optimal portfolio weights for a set of stocks to maximize the Sharpe Ratio using modern portfolio theory."
version: 1.1.0
author: Gemini Code Assist
license: MIT
tags: [finance, portfolio-optimization, scipy, sharpe-ratio, risk-management, productivity]
platforms: [linux, macos, windows]
triggers:
  - optimize this portfolio
  - find optimal weights for these stocks
  - maximize the sharpe ratio for this portfolio
---

# Optimize Portfolio for Maximum Sharpe Ratio

This skill elevates SakFin's capabilities from analysis to optimization. It uses modern portfolio theory to determine the ideal allocation of assets in a portfolio to achieve the highest possible risk-adjusted return (Sharpe Ratio).

The script performs the following actions:

1. Loads historical data for multiple stocks from CSV files.
2. Automatically determines the current risk-free rate by fetching the 13-week US Treasury Bill yield (`^IRX`).
3. Calculates daily returns and the covariance matrix for the assets.
4. Uses `scipy.optimize.minimize` to find the set of weights that maximizes the portfolio's Sharpe Ratio.
5. The optimization is constrained to ensure weights sum to 1 and no short-selling is allowed (weights are between 0 and 1).
6. Prints a detailed report showing the optimal weights and the expected performance (return, volatility, Sharpe Ratio) of the resulting portfolio.
7. Optionally generates and saves a pie chart visualizing the optimal asset allocation.

## How to Use

The agent should first use the `fetch-stock-data` skill to download data for all desired portfolio components. Then, it should execute the `optimize_portfolio.py` script, providing the list of file paths and corresponding tickers.

### Example Workflow

```bash
# Step 1: Fetch data for all potential portfolio components.
run_command("python personas/sakfin/skills/fetch-stock-data/fetch_stock_data.py GOOGL --period 2y --output /path/to/data/googl_2y.csv")
run_command("python personas/sakfin/skills/fetch-stock-data/fetch_stock_data.py MSFT --period 2y --output /path/to/data/msft_2y.csv")
run_command("python personas/sakfin/skills/fetch-stock-data/fetch_stock_data.py AAPL --period 2y --output /path/to/data/aapl_2y.csv")

# Step 2: Run the portfolio optimization skill on the downloaded data.
run_command("python personas/sakfin/skills/optimize-portfolio/optimize_portfolio.py --files /path/to/data/googl_2y.csv /path/to/data/msft_2y.csv /path/to/data/aapl_2y.csv --tickers GOOGL MSFT AAPL --output-plot /path/to/plots/optimal_allocation.png")
```

**Dependencies:** This skill requires `pandas`, `numpy`, `scipy`, `matplotlib`, and `yfinance`.

```bash
uv pip install pandas numpy scipy matplotlib yfinance
```
