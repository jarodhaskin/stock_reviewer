import pandas as pd
import pytest

from stock_reviewer import config, criteria, screening


def prices(values, volume=2_000_000):
    return pd.DataFrame({"Close": values, "Volume": volume})


@pytest.fixture
def passing_data():
    # Mean 100, final 200 mean 100, peak 125, last 100 => drawdown 20%.
    return prices([75.0, 125.0] + [100.0] * 200)


def test_formulas_and_combined_result(monkeypatch, passing_data):
    raw = pd.concat(
        {"A": passing_data, "B": passing_data.assign(Volume=3e6), "SPY": passing_data}, axis=1
    )
    requests = []

    def download(tickers, settings):
        requests.append(tickers)
        return raw

    monkeypatch.setattr(screening, "bulk_download", download)
    monkeypatch.setattr(screening, "download_financial_metrics", lambda ticker: {})
    passed, all_results = screening.screen_stocks(["A", "B", "MISSING", "SPY"], config.CRITERIA)
    assert requests == [["A", "B", "MISSING", "SPY"]]
    assert list(passed.ticker) == ["B", "A"]
    assert "failed_reason" not in passed
    row = all_results.iloc[0]
    assert row.avg_dollar_volume == 200_000_000
    assert row.avg_price == 100
    assert row.ma_200 == 100
    assert row.drawdown_pct == 20
    assert row.stock_return_pct == pytest.approx(100 / 3)
    assert row.market_return_pct == pytest.approx(100 / 3)
    assert row.rel_return_pct == 0
    assert row.status == "ok"
    assert all_results.iloc[2].failed_reason == "ticker not pulled (no data in bulk download)"


def test_all_failures_collected(monkeypatch):
    monkeypatch.setattr(
        screening, "bulk_download", lambda *args: pd.concat({"A": prices([1, 1], 1)}, axis=1)
    )
    monkeypatch.setattr(screening, "download_financial_metrics", lambda ticker: {})
    passed, results = screening.screen_stocks(["A"], config.CRITERIA)
    assert passed.empty
    assert results.iloc[0].failed_reason == (
        "entry_liquidity 1 < min_entry_dollar_volume 100,000,000; "
        "exit_liquidity 1 < min_exit_dollar_volume 50,000,000; "
        "avg_price 1.00 < min_avg_price 10; not enough data for long-term trend; "
        "drawdown 0.0% < min_drawdown 10%; market reference data missing"
    )


@pytest.mark.parametrize("value,ok", [(9.99, False), (10, True), (10.01, True)])
def test_price_boundary(value, ok):
    result = criteria.check_price_floor(prices([value, float("nan")]), config.CRITERIA)
    assert result[0] == ok
    assert result[2] == {"avg_price": value}


@pytest.mark.parametrize("last,ok", [(90, True), (65, True), (91, False), (64, False)])
def test_drawdown_boundary(last, ok):
    assert criteria.check_drawdown_from_high(prices([100, last]), config.CRITERIA)[0] == ok


def test_liquidity_and_trend_equality():
    frame = prices([10] * 200, 10_000_000)
    assert criteria.check_dollar_liquidity(frame, config.CRITERIA) == (
        True,
        None,
        {"avg_dollar_volume": 100e6},
    )
    assert criteria.check_long_term_trend(frame, config.CRITERIA) == (True, None, {"ma_200": 10})
    assert not criteria.check_long_term_trend(frame.iloc[:199], config.CRITERIA)[0]
    settings = {
        **config.CRITERIA,
        "min_entry_dollar_volume": 50e6,
        "min_exit_dollar_volume": 100e6 + 1,
    }
    assert not criteria.check_dollar_liquidity(frame, settings)[0]


def test_missing_observations():
    frame = prices([float("nan")])
    for check in criteria.CRITERION_FUNCTIONS[:-1]:
        assert check(frame, config.CRITERIA)[0] is False
    assert criteria.check_market_relative_performance(frame, config.CRITERIA) == (
        False,
        "market reference data missing",
        {},
    )
    assert criteria.check_market_relative_performance(
        frame, {**config.CRITERIA, "market_df": frame}
    ) == (False, "insufficient data for relative performance", {})


def test_relative_dates_and_boundary():
    stock = prices([100, 95])
    market = prices([100, 100])
    stock.index = pd.date_range("2020-01-01", periods=2)
    market.index = pd.date_range("2021-01-01", periods=2)
    settings = {**config.CRITERIA, "market_df": market}
    ok, reason, metrics = criteria.check_market_relative_performance(stock, settings)
    # Retain unaligned dates and legacy floating-point comparison behavior.
    assert ok is False
    assert reason == "underperformed market by 5.0%"
    assert metrics["rel_return_pct"] == pytest.approx(-5)
    settings["max_underperformance_pct"] = abs((95 / 100 - 1) * 100)
    assert criteria.check_market_relative_performance(stock, settings)[0]


def test_universe_and_registry():
    assert len(config.NASDAQ_100_TICKERS) == 77
    assert "ANSS" not in config.NASDAQ_100_TICKERS
    assert config.DEV_TICKERS == ["AAPL", "MSFT", "NVDA", "PLTR", "SOFI"]
    assert [check.__name__ for check in criteria.CRITERION_FUNCTIONS] == config.ACTIVE_CRITERIA
