"""Run all criteria and sort passing results."""

from typing import Any

import pandas as pd

from stock_reviewer.config import MARKET_TICKER
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

    criteria = criteria.copy()
    criteria["market_df"] = market_df

    for ticker in tickers:
        ticker = ticker.upper().strip()

        if ticker == MARKET_TICKER:
            continue

        failed_reasons = []
        metrics = {}

        df = extract_ticker_frame(raw_data, ticker)

        # Explicitly mark tickers that weren't pulled
        if df is None:
            results.append(
                {
                    "ticker": ticker,
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
