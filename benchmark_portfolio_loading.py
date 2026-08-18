import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd


def run_benchmark(num_files=30, num_rows=5000):
    print(f"Generating benchmark dataset with {num_files} CSV files ({num_rows} rows each)...")
    tickers = [f"STOCK_{i}" for i in range(num_files)]

    with tempfile.TemporaryDirectory() as tmpdir:
        files = []
        dates = pd.date_range("2020-01-01", periods=num_rows)
        for i in range(num_files):
            df = pd.DataFrame({"Close": np.random.randn(num_rows) + 100}, index=dates)
            df.index.name = "Date"
            file_path = os.path.join(tmpdir, f"stock_{i}.csv")
            df.to_csv(file_path)
            files.append(file_path)

        # Baseline: Sequential I/O loop
        t0 = time.perf_counter()
        seq_df = pd.DataFrame()
        for i, file in enumerate(files):
            df = pd.read_csv(file, index_col="Date", parse_dates=True)
            seq_df[tickers[i]] = df["Close"]
        t1 = time.perf_counter()
        seq_time = t1 - t0

        # Optimized: ThreadPoolExecutor concurrent loading
        t0 = time.perf_counter()

        def _read_stock_csv(item: tuple[str, str]) -> tuple[str, pd.Series]:
            file_path, ticker = item
            df = pd.read_csv(file_path, index_col="Date", parse_dates=True)
            return ticker, df["Close"]

        with ThreadPoolExecutor() as executor:
            results = list(executor.map(_read_stock_csv, zip(files, tickers, strict=False)))

        conc_df = pd.DataFrame({ticker: series for ticker, series in results})
        t1 = time.perf_counter()
        conc_time = t1 - t0

        data_equal = seq_df.equals(conc_df)
        speedup = seq_time / conc_time if conc_time > 0 else 0.0

        print("\n--- Benchmark Results ---")
        print(f"Sequential I/O (Baseline): {seq_time:.4f} seconds")
        print(f"Concurrent ThreadPool (Optimized): {conc_time:.4f} seconds")
        print(f"Speedup: {speedup:.2f}x faster")
        print(f"Data Equality Verified: {data_equal}")


if __name__ == "__main__":
    run_benchmark()
