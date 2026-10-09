"""Run all criteria and sort passing results."""

from typing import Any

import pandas as pd

from stock_reviewer.config import MARKET_TICKER, TREASURY_TICKER
from stock_reviewer.criteria import CRITERION_FUNCTIONS
from stock_reviewer.providers import (
    bulk_download,
    download_financial_metrics,
    extract_ticker_frame,
)


def screen_stocks(
    tickers: list[str], criteria: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    results = []

    raw_data = bulk_download(tickers, criteria)

    market_df = extract_ticker_frame(raw_data, MARKET_TICKER)
    treasury_df = extract_ticker_frame(raw_data, TREASURY_TICKER)
    treasury_close = (
        treasury_df["Close"].dropna() if treasury_df is not None else pd.Series(dtype=float)
    )
    treasury_10y_yield_pct = float(treasury_close.iloc[-1]) if not treasury_close.empty else None

    criteria = criteria.copy()
    criteria["market_df"] = market_df

    for ticker in tickers:
        ticker = ticker.upper().strip()

        if ticker in (MARKET_TICKER, TREASURY_TICKER):
            continue

        failed_reasons = []
        metrics = {}

        df = extract_ticker_frame(raw_data, ticker)

        # Explicitly mark tickers that weren't pulled
        if df is None:
            results.append(
                {
                    "ticker": ticker,
                    "treasury_10y_yield_pct": treasury_10y_yield_pct,
                    "risk_premium_pct": None,
                    "status": "failed",
                    "failed_reason": "ticker not pulled (no data in bulk download)",
                }
            )
            continue

        # Run all active criteria
        for check_fn in CRITERION_FUNCTIONS:
            check_passed, reason, metric_updates = check_fn(df, criteria)
            metrics.update(metric_updates)
            if not check_passed and reason:
                failed_reasons.append(reason)

        metrics.update(download_financial_metrics(ticker))
        metrics["treasury_10y_yield_pct"] = treasury_10y_yield_pct
        owner_earnings_yield_pct = metrics.get("owner_earnings_yield_pct")
        metrics["risk_premium_pct"] = (
            owner_earnings_yield_pct - treasury_10y_yield_pct
            if owner_earnings_yield_pct is not None and treasury_10y_yield_pct is not None
            else None
        )

        status = "ok" if not failed_reasons else "failed"

        results.append(
            {
                "ticker": ticker,
                **metrics,
                "status": status,
                "failed_reason": "; ".join(failed_reasons),
            }
        )

    all_results = pd.DataFrame(results)

    # Sort PASSED by whatever metric columns exist (if any)
    metric_cols = [
        column
        for column in (
            "avg_dollar_volume",
            "avg_price",
            "ma_200",
            "drawdown_pct",
            "stock_return_pct",
            "market_return_pct",
            "rel_return_pct",
        )
        if column in all_results.columns
    ]
    passed = (
        all_results[all_results["status"] == "ok"]
        .drop(columns=["failed_reason"])
        .sort_values(
            by=metric_cols if metric_cols else ["ticker"], ascending=False if metric_cols else True
        )
        .reset_index(drop=True)
    )

    return passed, all_results
