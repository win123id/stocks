from datetime import timedelta
import json
import os

import pandas as pd
import yfinance as yf


def load_tickers_from_json(path: str):
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


def scan_golden_cross_for_tickers(tickers, lookback_days: int = 5, label: str = ""):
    if not tickers:
        print("\nNo tickers to scan.")
        return

    label_text = label or "provided tickers"
    print(f"\nScanning {label_text} for 20/50 MA golden crosses...")
    results = []
    debug_rows = []
    for symbol in tickers:
        try:
            # 6 months of data is enough for MA20/MA50
            hist = yf.download(
                symbol,
                period="6mo",
                interval="1d",
                auto_adjust=True,
                progress=False,
            )
        except Exception as e:
            print(f"Failed to download data for {symbol}: {e}")
            continue

        if hist is None or hist.empty or "Close" not in hist.columns:
            continue

        hist["MA20"] = hist["Close"].rolling(20).mean()
        hist["MA50"] = hist["Close"].rolling(50).mean()
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
    header = f"{'Symbol':<10} {'Last Price':>12} {'GC Date':>12}"
    print(header)
    print("-" * len(header))
    for symbol, last_close, gc_date in results:
        print(f"{symbol:<10} {last_close:>12,.2f} {str(gc_date):>12}")


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
        try:
            # Use longer history for larger SMA periods (e.g. SMA200)
            download_period = "1y" if sma_period >= 150 else "6mo"
            hist = yf.download(
                symbol,
                period=download_period,
                interval="1d",
                auto_adjust=True,
                progress=False,
            )
        except Exception as e:
            print(f"Failed to download data for {symbol}: {e}")
            continue

        if hist is None or hist.empty:
            continue

        # Some yfinance versions return MultiIndex columns even for a single ticker.
        # Flatten to the first level so we have simple 'Open','High','Low','Close','Volume' names.
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)

        required_cols = {"Close", "Low", "Volume"}
        if not required_cols.issubset(hist.columns):
            continue

        # Work on a small DataFrame to avoid multi-index or extra columns issues
        df = hist[["Close", "Low", "Volume"]].copy()
        df["SMA"] = df["Close"].rolling(sma_period).mean()
        df["LLV_prev"] = df["Low"].rolling(llv_window).min().shift(1)

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
    header = f"{'Symbol':<10} {'Close':>12} {'SMA%s' % sma_period:>12} {'Value':>16} {'Date':>12}"
    print(header)
    print("-" * len(header))
    for symbol, close, sma, value, dt in results:
        print(f"{symbol:<10} {close:>12,.2f} {sma:>12,.2f} {value:>16,.0f} {str(dt):>12}")


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
        try:
            hist = yf.download(
                symbol,
                period="1y",
                interval="1d",
                auto_adjust=True,
                progress=False,
            )
        except Exception as e:
            print(f"Failed to download data for {symbol}: {e}")
            continue

        if hist is None or hist.empty:
            continue

        # Flatten possible MultiIndex columns
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)

        required_cols = {"Close", "Volume"}
        if not required_cols.issubset(hist.columns):
            continue

        df = hist[["Close", "Volume"]].copy()

        # Moving averages
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["SMA50"] = df["Close"].rolling(50).mean()
        df["SMA150"] = df["Close"].rolling(150).mean()
        df["SMA200"] = df["Close"].rolling(200).mean()

        # Bollinger Band width (20 period, 2 std)
        rolling20 = df["Close"].rolling(20)
        bb_std = rolling20.std()
        df["BB_width"] = 4 * bb_std  # upper - lower = 4 * std (±2 std)

        # MACD (12,26,9)
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema12 - ema26
        df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

        # RSI(14) using simple moving averages
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss.replace(0, pd.NA)
        df["RSI14"] = 100 - (100 / (1 + rs))

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
    header = f"{'Symbol':<10} {'Close':>10} {'SMA20':>10} {'SMA50':>10} {'SMA150':>10} {'SMA200':>10} {'Value':>16} {'RSI14':>8} {'Date':>12}"
    print(header)
    print("-" * len(header))
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
        print(
            f"{symbol:<10} {close:>10,.2f} {sma20:>10,.2f} {sma50:>10,.2f} "
            f"{sma150:>10,.2f} {sma200:>10,.2f} {value:>16,.0f} {rsi14:>8.2f} {str(dt):>12}"
        )


def main():
    default_file = "idx80.json"
    path = input(f"Enter JSON file path with tickers (default: {default_file}): ").strip()
    if not path:
        path = default_file

    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(__file__), path)

    tickers = load_tickers_from_json(path)
    if not tickers:
        return

    label = os.path.basename(path)

    print("\nChoose scan mode:")
    print("1 - Golden cross 20/50 MA")
    print("2 - LLV(5) > SMA50, close near SMA50 (0.99-1.02), value > 1B")
    print("3 - LLV(5) > SMA200, close near SMA200 (0.99-1.02), value > 1B")
    print("4 - Trend + squeeze + MACD + RSI combo filter")
    mode = input("Enter 1, 2, 3 or 4 (default: 1): ").strip()

    if mode == "2":
        # Filter around SMA50: LLV(5) > SMA50, close ~ SMA50, value > 1B
        scan_llv_sma50_value_for_tickers(
            tickers,
            llv_window=5,
            sma_period=50,
            near_low=0.99,
            near_high=1.02,
            min_value=1e9,
            label=label,
        )
    elif mode == "3":
        # Filter around SMA200: LLV(5) > SMA200, close ~ SMA200, value > 1B
        scan_llv_sma50_value_for_tickers(
            tickers,
            llv_window=5,
            sma_period=200,
            near_low=0.99,
            near_high=1.02,
            min_value=1e9,
            label=label,
        )
    elif mode == "4":
        scan_mode4_combo_for_tickers(tickers, label=label)
    else:
        scan_golden_cross_for_tickers(tickers, label=label)


if __name__ == "__main__":
    main()
