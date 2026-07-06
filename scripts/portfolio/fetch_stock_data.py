import argparse
import yfinance as yf
import pandas as pd
import sys

def fetch_stock_data(ticker: str, period: str, output_path: str | None):
    """
    Fetches historical stock data for a given ticker and saves it to a CSV file.

    Args:
        ticker: The stock ticker symbol (e.g., 'GOOGL', 'MSFT').
        period: The time period for the data (e.g., '1d', '5d', '1mo', '1y', 'max').
        output_path: Optional. The file path to save the CSV data. If not provided,
                     prints a summary to stdout.
    """
    try:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period=period)

        if hist_data.empty:
            print(f"Error: No data found for ticker '{ticker}' for the period '{period}'. It might be an invalid ticker.", file=sys.stderr)
            sys.exit(1)

        if output_path:
            hist_data.to_csv(output_path)
            print(f"Successfully fetched {len(hist_data)} rows of data for '{ticker}' and saved to '{output_path}'.")
        else:
            print(f"--- Summary for {ticker} (Period: {period}) ---")
            print(f"Date Range: {hist_data.index.min().date()} to {hist_data.index.max().date()}")
            print(f"Latest Close: ${hist_data['Close'][-1]:.2f}")
            print("\nFirst 5 rows:")
            print(hist_data.head().to_string())

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch historical stock market data using yfinance."
    )
    parser.add_argument("ticker", type=str, help="Stock ticker symbol (e.g., 'GOOGL').")
    parser.add_argument(
        "--period", type=str, default="1y",
        help="The period for which to fetch data (e.g., '1d', '5d', '1mo', '1y', 'max'). Default is '1y'."
    )
    parser.add_argument(
        "--output", type=str, help="Optional. Path to save the output CSV file."
    )
    args = parser.parse_args()

    fetch_stock_data(args.ticker, args.period, args.output)