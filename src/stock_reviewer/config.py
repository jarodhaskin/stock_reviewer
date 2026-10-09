"""Screening defaults and legacy universes."""

from pathlib import Path

NASDAQ_100_TICKERS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "GOOG",
    "TSLA",
    "AVGO",
    "COST",
    "PEP",
    "ADBE",
    "NFLX",
    "AMD",
    "INTC",
    "CSCO",
    "TXN",
    "QCOM",
    "AMGN",
    "HON",
    "INTU",
    "ISRG",
    "BKNG",
    "SBUX",
    "ADI",
    "GILD",
    "MDLZ",
    "REGN",
    "VRTX",
    "LRCX",
    "MU",
    "KLAC",
    "SNPS",
    "CDNS",
    "ASML",
    "PANW",
    "MAR",
    "ABNB",
    "ORLY",
    "CTAS",
    "ADP",
    "MELI",
    "PAYX",
    "WDAY",
    "BIIB",
    "KDP",
    "AEP",
    "DXCM",
    "ROST",
    "FAST",
    "PCAR",
    "ODFL",
    "EXC",
    "CSX",
    "IDXX",
    "MRNA",
    "ILMN",
    "EA",
    "XEL",
    "DLTR",
    "BKR",
    "CTSH",
    "WBD",
    "FANG",
    "CEG",
    "GEHC",
    "FTNT",
    "DDOG",
    "ZS",
    "TEAM",
    "MDB",
    "PYPL",
    "CHTR",
    "TTD",
    "PDD",
    "JD",
    "BIDU",
]

MARKET_TICKER = "SPY"

DEV_TICKERS = ["AAPL", "MSFT", "NVDA", "PLTR", "SOFI"]

CRITERIA = {
    "lookback_days": 260,
    "min_entry_dollar_volume": 100_000_000,  # $100M/day
    "min_exit_dollar_volume": 50_000_000,  # $50M/day
    "min_avg_price": 10,  # $10 minimum average price
    "ma_long_window": 200,  # 200 moving day average
    "min_drawdown_pct": 10,  # % drawdown minimum
    "max_drawdown_pct": 35,  # % drawdown maximum
    "market_ticker": "SPY",  # market benchmark
    "max_underperformance_pct": 5,  # market underperformance accepted
}

ACTIVE_CRITERIA = [
    "check_dollar_liquidity",
    "check_price_floor",
    "check_long_term_trend",
    "check_drawdown_from_high",
    "check_market_relative_performance",
]

OUTPUT_DIR = Path("outputs")
MASTER_HISTORY_FILE = OUTPUT_DIR / "master_stock_history.csv"

DEV_MODE = False
