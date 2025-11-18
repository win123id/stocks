from datetime import timedelta

import pandas as pd

from data import download_history
from indicators import (
    add_ma20_ma50_for_close,
    add_sma_and_llv_prev,
    add_mode4_indicators,
)


def print_table(headers, rows):
    if not rows:
        return

    col_count = len(headers)
    widths = [len(str(h)) for h in headers]

    for row in rows:
        for i in range(col_count):
            if i >= len(row):
                continue
            value = "" if row[i] is None else str(row[i])
            if len(value) > widths[i]:
                widths[i] = len(value)

    header_line = "  ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print("-" * len(header_line))

    for row in rows:
        cells = []
        for i in range(col_count):
            value = "" if i >= len(row) or row[i] is None else str(row[i])
            num_like = value.replace(",", "").replace(".", "").isdigit()
            if num_like:
                cells.append(value.rjust(widths[i]))
            else:
                cells.append(value.ljust(widths[i]))
        print("  ".join(cells))


def scan_golden_cross_for_tickers(tickers, lookback_days: int = 5, label: str = ""):
    if not tickers:
        print("\nNo tickers to scan.")
        return

    label_text = label or "provided tickers"
    print(f"\nScanning {label_text} for 20/50 MA golden crosses...")
    results = []
    for symbol in tickers:
        # 6 months of data is enough for MA20/MA50
        hist = download_history(symbol, period="1y", interval="1d")
        if hist is None or "Close" not in hist.columns:
            continue

        hist = add_ma20_ma50_for_close(hist)
        valid = hist["MA20"].notna() & hist["MA50"].notna()
        hist_valid = hist.loc[valid]
        if hist_valid.empty:
            continue

        signal = (hist_valid["MA20"] > hist_valid["MA50"]).astype(int)
        cross = signal.diff()
        golden_crosses = hist_valid[cross == 1]
        if golden_crosses.empty:
            continue

        last_gc_date = golden_crosses.index[-1]
        last_date = hist_valid.index[-1]
        if last_gc_date >= last_date - timedelta(days=lookback_days):
            # extract last close as a scalar from the Close column (Series or DataFrame)
            close_array = hist_valid["Close"].tail(1).to_numpy().ravel()
            if close_array.size == 0:
                continue
            last_close = float(close_array[0])
            results.append((symbol, last_close, last_gc_date.date()))

    if not results:
        print("\nNo recent 20/50 MA golden crosses found in the selected lookback window.")
        return

    print("\nStocks with recent 20/50 MA golden crosses:")
    headers = ["Symbol", "Last Price", "GC Date"]
    rows = [
        (symbol, f"{last_close:,.2f}", str(gc_date))
        for symbol, last_close, gc_date in results
    ]
    print_table(headers, rows)



def scan_llv_sma50_value_for_tickers(
    tickers,
    llv_window: int = 5,
    sma_period: int = 50,
    near_low: float = 0.99,
    near_high: float = 1.02,
    min_value: float = 1e9,
    label: str = "",
):
    if not tickers:
        print("\nNo tickers to scan.")
        return

    label_text = label or "provided tickers"
    print(
        f"\nScanning {label_text} for LLV({llv_window}) > SMA{sma_period}, "
        f"close near SMA{sma_period} and value > {min_value:,.0f}..."
    )

    results = []
    for symbol in tickers:
        # Use longer history for larger SMA periods (e.g. SMA200)
        download_period = "1y"
        hist = download_history(symbol, period=download_period, interval="1d")
        if hist is None:
            continue

        required_cols = {"Close", "Low", "Volume"}
        if not required_cols.issubset(hist.columns):
            continue

        # Work on a small DataFrame to avoid multi-index or extra columns issues
        df = hist[["Close", "Low", "Volume"]].copy()
        df = add_sma_and_llv_prev(df, sma_period=sma_period, llv_window=llv_window)

        # Drop rows where any of the required values is NaN
        df = df.dropna(subset=["Close", "Low", "Volume", "SMA", "LLV_prev"])
        if df.empty:
            continue

        last = df.iloc[-1]
        sma = float(last["SMA"])
        llv_prev = float(last["LLV_prev"])
        close = float(last["Close"])
        volume = float(last["Volume"])
        idx = df.index[-1]
        last_date = idx.date() if hasattr(idx, "date") else idx

        # generic LLV/SMA filter using function parameters
        cond_trend = llv_prev > sma
        cond_near = (close >= sma * near_low) and (close <= sma * near_high)
        trading_value = close * volume
        cond_value = trading_value >= min_value

        if cond_trend and cond_near and cond_value:
            results.append((symbol, close, sma, trading_value, last_date))

    if not results:
        print("\nNo stocks matched the LLV/SMA{} + value filter in the selected lookback window.".format(sma_period))
        return

    print("\nStocks matching LLV(5) > SMA{}, close near SMA{}, value > 1B:".format(sma_period, sma_period))
    headers = ["Symbol", "Close", f"SMA{sma_period}", "Value", "Date"]
    rows = [
        (symbol, f"{close:,.2f}", f"{sma:,.2f}", f"{value:,.0f}", str(dt))
        for symbol, close, sma, value, dt in results
    ]
    print_table(headers, rows)



def scan_mode4_combo_for_tickers(tickers, label: str = ""):
    if not tickers:
        print("\nNo tickers to scan.")
        return

    label_text = label or "provided tickers"
    print(
        f"\nScanning {label_text} for mode 4 combo: "
        "Close > SMA50 > SMA150 > SMA200 and traded value >= 1B IDR..."
    )

    results = []
    for symbol in tickers:
        hist = download_history(symbol, period="1y", interval="1d")
        if hist is None:
            continue

        required_cols = {"Close", "Volume"}
        if not required_cols.issubset(hist.columns):
            continue

        df = hist[["Close", "Volume"]].copy()
        df = add_mode4_indicators(df)

        # Require all indicators present
        df = df.dropna(
            subset=[
                "Close",
                "Volume",
                "SMA20",
                "SMA50",
                "SMA150",
                "SMA200",
                "BB_width",
                "MACD_hist",
                "RSI14",
            ]
        )
        if df.empty or len(df) < 20:
            continue

        last = df.iloc[-1]
        close = float(last["Close"])
        sma20 = float(last["SMA20"])
        sma50 = float(last["SMA50"])
        sma150 = float(last["SMA150"])
        sma200 = float(last["SMA200"])
        volume = float(last["Volume"])
        rsi14 = float(last["RSI14"])
        idx = df.index[-1]
        last_date = idx.date() if hasattr(idx, "date") else idx

        # 1) Close above SMA50
        cond_close_sma50 = close > sma50

        # 2) Longer-term stack: SMA50 > SMA150 > SMA200
        cond_sma_stack = sma50 > sma150 > sma200

        # 3) Traded value (close * volume) >= 1B IDR
        trading_value = close * volume
        cond_value = trading_value >= 1e9

        if cond_close_sma50 and cond_sma_stack and cond_value:
            results.append(
                (
                    symbol,
                    close,
                    sma20,
                    sma50,
                    sma150,
                    sma200,
                    trading_value,
                    rsi14,
                    last_date,
                )
            )

    if not results:
        print("\nNo stocks matched the mode 4 combo filter in the selected lookback window.")
        return

    print("\nStocks matching mode 4 combo filter:")
    headers = [
        "Symbol",
        "Close",
        "SMA20",
        "SMA50",
        "SMA150",
        "SMA200",
        "Value",
        "RSI14",
        "Date",
    ]
    rows = []
    for (
        symbol,
        close,
        sma20,
        sma50,
        sma150,
        sma200,
        value,
        rsi14,
        dt,
    ) in results:
        rows.append(
            (
                symbol,
                f"{close:,.2f}",
                f"{sma20:,.2f}",
                f"{sma50:,.2f}",
                f"{sma150:,.2f}",
                f"{sma200:,.2f}",
                f"{value:,.0f}",
                f"{rsi14:.2f}",
                str(dt),
            )
        )
    print_table(headers, rows)
