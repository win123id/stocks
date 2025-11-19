import json
import os
from datetime import datetime

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


def _get_cache_path(symbol: str, period: str, interval: str):
    safe_symbol = symbol.replace("/", "_").replace("\\", "_").replace(":", "_")
    cache_dir = os.path.join(os.path.dirname(__file__), "cache")
    return os.path.join(cache_dir, f"{safe_symbol}_{period}_{interval}.csv")


def download_history(symbol: str, period: str, interval: str = "1d"):
    """Download price history for a single symbol using yfinance.

    Returns a pandas DataFrame with flattened column names, or None on error/empty.
    """
    cache_path = _get_cache_path(symbol, period, interval)
    cached = None

    # Try to load existing cache from disk
    if os.path.exists(cache_path):
        try:
            cached = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        except Exception:
            cached = None

    # If we have cached data, try to append only missing days
    if cached is not None and not cached.empty:
        try:
            # Ensure index is a DateTimeIndex
            if not isinstance(cached.index, pd.DatetimeIndex):
                cached.index = pd.to_datetime(cached.index)

            last_timestamp = cached.index.max()
            last_date = last_timestamp.date()
            today = datetime.now().date()

            # If cache already has data for today or later, just use it
            if last_date >= today:
                return cached

            start_date = last_timestamp + pd.Timedelta(days=1)
        except Exception:
            start_date = None

        if start_date is not None:
            try:
                new_hist = yf.download(
                    symbol,
                    start=start_date,
                    interval=interval,
                    auto_adjust=False,
                    progress=False,
                )
            except Exception as e:
                print(f"Failed to download data for {symbol}: {e}")
                return cached

            if new_hist is not None and not new_hist.empty:
                # Flatten MultiIndex columns if needed
                if isinstance(new_hist.columns, pd.MultiIndex):
                    new_hist.columns = new_hist.columns.get_level_values(0)

                updated = pd.concat([cached, new_hist])
                # Drop duplicate index entries, keep the latest
                updated = updated[~updated.index.duplicated(keep="last")]
                updated = updated.sort_index()

                try:
                    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                    updated.to_csv(cache_path)
                except Exception:
                    pass

                return updated

        # If we cannot determine a start_date or there is no new data, fall back to cached
        return cached

    # No valid cache: download a fresh history using the requested period
    try:
        hist = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=False,
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

    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        hist.to_csv(cache_path)
    except Exception:
        pass

    return hist
