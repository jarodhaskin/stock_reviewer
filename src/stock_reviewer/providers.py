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
        auto_adjust=True,
        group_by="ticker",
        progress=False,
        threads=True,
    )
    return raw


def download_financial_metrics(ticker: str) -> dict[str, Any]:
    """Return the latest annual net income, D&A, and capital expenditure."""
    company = yf.Ticker(ticker)
    income_stmt = company.get_income_stmt(freq="yearly", pretty=True)
    cash_flow = company.get_cash_flow(freq="yearly", pretty=True)
    info = company.get_info()
    market_cap_value = info.get("marketCap")
    market_cap = (
        float(market_cap_value)
        if market_cap_value is not None and pd.notna(market_cap_value)
        else None
    )

    def latest_value(statement: pd.DataFrame, row_name: str) -> tuple[Any, Any]:
        if row_name not in statement.index or statement.empty:
            return None, None
        periods = sorted(statement.columns, reverse=True)
        for period in periods:
            value = statement.at[row_name, period]
            if pd.notna(value):
                return float(value), period
        return None, None

    net_income, income_period = latest_value(income_stmt, "Net Income")
    depreciation, cash_flow_period = latest_value(cash_flow, "Depreciation And Amortization")
    capex, _ = latest_value(cash_flow, "Capital Expenditure")
    owner_earnings = (
        net_income + depreciation - abs(capex)
        if net_income is not None and depreciation is not None and capex is not None
        else None
    )
    owner_earnings_yield_pct = (
        owner_earnings / market_cap * 100
        if owner_earnings is not None and market_cap not in (None, 0)
        else None
    )
    return {
        "market_cap": market_cap,
        "net_income": net_income,
        "net_income_period": str(income_period.date()) if income_period is not None else None,
        "depreciation_and_amortization": depreciation,
        "capital_expenditure": capex,
        "owner_earnings": owner_earnings,
        "owner_earnings_yield_pct": owner_earnings_yield_pct,
        "cash_flow_period": (
            str(cash_flow_period.date()) if cash_flow_period is not None else None
        ),
    }


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
