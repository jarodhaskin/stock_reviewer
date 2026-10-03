"""Pure price/volume screening checks; formulas retained from the original script."""

from typing import Any, Callable, Optional

import pandas as pd

from stock_reviewer.config import ACTIVE_CRITERIA

CheckResult = tuple[bool, Optional[str], dict[str, Any]]
Criterion = Callable[[pd.DataFrame, dict[str, Any]], CheckResult]


def check_dollar_liquidity(df: pd.DataFrame, criteria: dict[str, Any]) -> CheckResult:
    dollar_volume = (df["Close"] * df["Volume"]).dropna()
    if dollar_volume.empty:
        return (
            False,
            "insufficient data for dollar volume (Close/Volume missing)",
            {"avg_dollar_volume": None},
        )

    avg_dollar_volume = float(dollar_volume.mean())
    failed = []

    if avg_dollar_volume < criteria["min_entry_dollar_volume"]:
        failed.append(
            f"entry_liquidity {avg_dollar_volume:,.0f} < "
            f"min_entry_dollar_volume {criteria['min_entry_dollar_volume']:,.0f}"
        )

    if avg_dollar_volume < criteria["min_exit_dollar_volume"]:
        failed.append(
            f"exit_liquidity {avg_dollar_volume:,.0f} < "
            f"min_exit_dollar_volume {criteria['min_exit_dollar_volume']:,.0f}"
        )

    if failed:
        return False, "; ".join(failed), {"avg_dollar_volume": avg_dollar_volume}

    return True, None, {"avg_dollar_volume": avg_dollar_volume}


def check_price_floor(df: pd.DataFrame, criteria: dict[str, Any]) -> CheckResult:
    avg_price_series = df["Close"].dropna()
    if avg_price_series.empty:
        return (
            False,
            "no price data available",
            {"avg_price": None},
        )

    avg_price = float(avg_price_series.mean())

    if avg_price < criteria["min_avg_price"]:
        return (
            False,
            f"avg_price {avg_price:.2f} < min_avg_price {criteria['min_avg_price']}",
            {"avg_price": avg_price},
        )

    return True, None, {"avg_price": avg_price}


def check_long_term_trend(df: pd.DataFrame, criteria: dict[str, Any]) -> CheckResult:
    close = df["Close"].dropna()

    if len(close) < criteria["ma_long_window"]:
        return (
            False,
            "not enough data for long-term trend",
            {"ma_200": None},
        )

    ma_200 = close.rolling(criteria["ma_long_window"]).mean().iloc[-1]
    current_price = close.iloc[-1]

    if current_price < ma_200:
        return (
            False,
            f"price {current_price:.2f} < 200d MA {ma_200:.2f}",
            {"ma_200": ma_200},
        )

    return True, None, {"ma_200": ma_200}


def check_drawdown_from_high(df: pd.DataFrame, criteria: dict[str, Any]) -> CheckResult:
    close = df["Close"].dropna()

    if close.empty:
        return (
            False,
            "no price data for drawdown",
            {"drawdown_pct": None},
        )

    recent_high = close.max()
    current_price = close.iloc[-1]

    drawdown_pct = (recent_high - current_price) / recent_high * 100

    if drawdown_pct < criteria["min_drawdown_pct"]:
        return (
            False,
            f"drawdown {drawdown_pct:.1f}% < min_drawdown {criteria['min_drawdown_pct']}%",
            {"drawdown_pct": drawdown_pct},
        )

    if drawdown_pct > criteria["max_drawdown_pct"]:
        return (
            False,
            f"drawdown {drawdown_pct:.1f}% > max_drawdown {criteria['max_drawdown_pct']}%",
            {"drawdown_pct": drawdown_pct},
        )

    return True, None, {"drawdown_pct": drawdown_pct}


def check_market_relative_performance(df: pd.DataFrame, criteria: dict[str, Any]) -> CheckResult:
    if "market_df" not in criteria or criteria["market_df"] is None:
        return False, "market reference data missing", {}

    market_df = criteria["market_df"]

    stock_close = df["Close"].dropna()
    market_close = market_df["Close"].dropna()

    if len(stock_close) < 2 or len(market_close) < 2:
        return False, "insufficient data for relative performance", {}

    stock_return = (stock_close.iloc[-1] / stock_close.iloc[0] - 1) * 100
    market_return = (market_close.iloc[-1] / market_close.iloc[0] - 1) * 100

    rel_perf = stock_return - market_return

    if rel_perf < -criteria["max_underperformance_pct"]:
        return (
            False,
            f"underperformed market by {abs(rel_perf):.1f}%",
            {
                "stock_return_pct": stock_return,
                "market_return_pct": market_return,
                "rel_return_pct": rel_perf,
            },
        )

    return (
        True,
        None,
        {
            "stock_return_pct": stock_return,
            "market_return_pct": market_return,
            "rel_return_pct": rel_perf,
        },
    )


CRITERION_REGISTRY: dict[str, Criterion] = {
    "check_dollar_liquidity": check_dollar_liquidity,
    "check_price_floor": check_price_floor,
    "check_long_term_trend": check_long_term_trend,
    "check_drawdown_from_high": check_drawdown_from_high,
    "check_market_relative_performance": check_market_relative_performance,
}

CRITERION_FUNCTIONS = tuple(CRITERION_REGISTRY[name] for name in ACTIVE_CRITERIA)
