"""Yahoo acquisition and ticker extraction."""

from typing import Any, Optional, cast

import pandas as pd
import yfinance as yf


def bulk_download(tickers: list[str], criteria: dict[str, Any]) -> pd.DataFrame:
    """
    One Yahoo/yfinance call for all tickers.
    Returns a DataFrame with MultiIndex columns: (Ticker, Field).
    """
    tickers_str = " ".join([t.upper().strip() for t in tickers])
    raw = yf.download(
        tickers_str,
        period=f"{criteria['lookback_days']}d",
        interval="1d",
        group_by="ticker",
        progress=False,
        threads=True,
    )
    return raw


def extract_ticker_frame(raw: pd.DataFrame, ticker: str) -> Optional[pd.DataFrame]:
    """
    Given bulk-downloaded 'raw', return a single-ticker OHLCV df with columns
    like ['Open','High','Low','Close','Adj Close','Volume'] or None if missing.
    """
    if raw is None or raw.empty:
        return None

    df: pd.DataFrame
    # Multi-ticker format uses MultiIndex columns: (ticker, field)
    if isinstance(raw.columns, pd.MultiIndex):
        top_level = raw.columns.get_level_values(0)
        if ticker not in set(top_level):
            return None
        df = cast(pd.DataFrame, raw[ticker])
        df = df.dropna(how="all")
        return None if df.empty else df

    # Single ticker case fallback (shouldn't happen with multi tickers, but safe)
    df = raw.dropna(how="all")
    return None if df.empty else df
