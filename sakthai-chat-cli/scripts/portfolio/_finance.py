"""Shared finance helpers for the portfolio scripts.

`optimize_portfolio.py` and `compare_portfolio_to_benchmark.py` both imported
``get_risk_free_rate`` from ``sakthai.finance`` — a module that has never
existed in this repository at any commit. Both scripts therefore failed at
import with ``ModuleNotFoundError`` and could not run at all.

The helper lives here rather than in the installed package because it is only
ever used by these two CLI scripts, and `scripts/` is deliberately outside the
`sakthai` package (see CLAUDE.md). Both callers already depend on `yfinance`,
so this adds no new dependency.
"""

from __future__ import annotations

import sys

# 13-week US Treasury bill yield — the conventional short-term risk-free proxy
# for Sharpe-ratio work. Quoted by Yahoo in percent (5.25 == 5.25%).
RISK_FREE_TICKER = "^IRX"

# Used when the quote cannot be fetched (offline, rate-limited, delisted).
# Returning a documented constant keeps the Sharpe calculation running with a
# plausible rate instead of aborting the whole analysis.
DEFAULT_RISK_FREE_RATE = 0.04


def get_risk_free_rate(ticker: str = RISK_FREE_TICKER, default: float = DEFAULT_RISK_FREE_RATE) -> float:
    """Return the current annualised risk-free rate as a decimal (0.04 == 4%).

    Falls back to ``default`` and warns on stderr if the quote is unavailable,
    so a transient network failure degrades the result rather than killing the
    run.
    """
    try:
        import yfinance as yf

        history = yf.Ticker(ticker).history(period="5d")
        if history.empty or "Close" not in history:
            raise ValueError(f"no recent closes for {ticker}")
        # Yahoo quotes ^IRX in percent; convert to the decimal the Sharpe
        # formulas expect.
        rate = float(history["Close"].dropna().iloc[-1]) / 100.0
    except Exception as exc:  # noqa: BLE001 - any failure degrades to the default
        print(
            f"Warning: could not fetch risk-free rate from {ticker} ({exc}); "
            f"falling back to {default:.2%}.",
            file=sys.stderr,
        )
        return default

    if not 0.0 <= rate < 0.25:
        print(
            f"Warning: implausible risk-free rate {rate:.2%} from {ticker}; "
            f"falling back to {default:.2%}.",
            file=sys.stderr,
        )
        return default

    return rate
