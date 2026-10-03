"""Entry point; execution writes reports in the working directory."""

from datetime import datetime

from stock_reviewer.config import CRITERIA, DEV_MODE, DEV_TICKERS, MARKET_TICKER, NASDAQ_100_TICKERS
from stock_reviewer.reports import update_master_history, write_stock_screen_output
from stock_reviewer.screening import screen_stocks


def main() -> None:
    timestamp = datetime.now()
    tickers = DEV_TICKERS if DEV_MODE else NASDAQ_100_TICKERS
    if MARKET_TICKER not in tickers:
        tickers = tickers + [MARKET_TICKER]
    passed, all_results = screen_stocks(tickers, CRITERIA)
    update_master_history(all_results, CRITERIA, timestamp)
    write_stock_screen_output(passed, all_results, CRITERIA, timestamp, DEV_MODE)
