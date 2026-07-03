import yfinance as yf
import sys
import time
import os

_RISK_FREE_RATE_CACHE = {
    "value": None,
    "timestamp": 0,
}

# Read cache TTL from environment variable, with a default of 1 hour.
try:
    # Use SAKTHAI_FINANCE_CACHE_TTL to avoid conflicts with other cache settings.
    CACHE_TTL_SECONDS = int(os.environ.get("SAKTHAI_FINANCE_CACHE_TTL", 3600))
except (ValueError, TypeError):
    CACHE_TTL_SECONDS = 3600

def get_risk_free_rate() -> float:
    """
    Fetches the current 13-week US Treasury Bill yield as the risk-free rate.
    The ticker ^IRX represents the 13-week T-bill yield.
    Returns the rate as a decimal (e.g., 0.05 for 5%).
    The cache duration is configurable via SAKTHAI_FINANCE_CACHE_TTL (in seconds).
    """
    now = time.time()
    if _RISK_FREE_RATE_CACHE["value"] is not None and (now - _RISK_FREE_RATE_CACHE["timestamp"]) < CACHE_TTL_SECONDS:
        # Return cached value
        return _RISK_FREE_RATE_CACHE["value"]

    try:
        irx = yf.Ticker("^IRX")
        # Fetch last 5 days to get the most recent available closing value
        hist = irx.history(period="5d")
        if hist.empty or 'Close' not in hist or hist['Close'].isnull().all():
            print("Warning: Could not fetch risk-free rate (^IRX). Defaulting to a fixed rate of 0.02.", file=sys.stderr)
            return 0.02
        # Get the last valid closing price and convert from percentage to decimal
        last_yield = hist['Close'].dropna().iloc[-1]
        risk_free_rate = last_yield / 100
        print(f"Automatically determined risk-free rate: {risk_free_rate:.4f} (from ^IRX)")

        # Update cache
        _RISK_FREE_RATE_CACHE["value"] = risk_free_rate
        _RISK_FREE_RATE_CACHE["timestamp"] = now

        return risk_free_rate
    except Exception as e:
        print(f"Warning: Failed to fetch risk-free rate (^IRX) due to an error: {e}. Defaulting to 0.02.", file=sys.stderr)
        return 0.02