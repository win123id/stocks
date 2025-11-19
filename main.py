import os
from data import load_tickers_from_json, download_history
from scanners import (
    scan_golden_cross_for_tickers,
    scan_llv_sma50_value_for_tickers,
    scan_mode4_combo_for_tickers,
    scan_lower_low_3days_for_tickers,
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
    print("5 - 3 consecutive lower daily lows")
    mode = input("Enter 1, 2, 3, 4 or 5 (default: 1): ").strip()

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
    elif mode == "5":
        scan_lower_low_3days_for_tickers(tickers, label=label)
    else:
        scan_golden_cross_for_tickers(tickers, label=label)


if __name__ == "__main__":
    main()
