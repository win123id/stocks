import json

import pandas as pd
import yfinance as yf


def load_tickers_from_json(path: str):
    """Load a list of tickers from a JSON file.

    The JSON file must contain a simple list of ticker strings.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"\nFile not found: {path}")
        return []
    except json.JSONDecodeError as e:
        print(f"\nInvalid JSON in {path}: {e}")
        return []

    if not isinstance(data, list):
        print(f"\nJSON file must contain a list of tickers (list), got {type(data).__name__}")
        return []

    tickers = [str(x).strip() for x in data if str(x).strip()]
    if not tickers:
        print(f"\nNo valid tickers found in {path}")
    return tickers


def download_history(symbol: str, period: str, interval: str = "1d"):
    """Download price history for a single symbol using yfinance.

    Returns a pandas DataFrame with flattened column names, or None on error/empty.
    """
    try:
        hist = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
        )
    except Exception as e:
        print(f"Failed to download data for {symbol}: {e}")
        return None

    if hist is None or hist.empty:
        return None

    # Some yfinance versions return MultiIndex columns even for a single ticker.
    # Flatten to the first level so we have simple 'Open','High','Low','Close','Volume' names.
    if isinstance(hist.columns, pd.MultiIndex):
        hist.columns = hist.columns.get_level_values(0)

    return hist
