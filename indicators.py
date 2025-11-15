import pandas as pd


def add_ma20_ma50_for_close(df):
    """Add MA20 and MA50 columns based on the Close price."""
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    return df


def add_sma_and_llv_prev(df, sma_period: int, llv_window: int):
    """Add SMA and LLV_prev columns used by the LLV/SMA scanners."""
    df["SMA"] = df["Close"].rolling(sma_period).mean()
    df["LLV_prev"] = df["Low"].rolling(llv_window).min().shift(1)
    return df


def add_mode4_indicators(df):
    """Add all indicators required by the mode 4 combo scanner.

    This includes SMA20/50/150/200, Bollinger Band width, MACD and RSI14.
    """
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

    return df
