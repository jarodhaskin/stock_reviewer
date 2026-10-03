# Stock reviewer

A Python stock screener that downloads daily Yahoo Finance data, applies five
configurable criteria, and produces a standalone HTML report plus CSV history.
The application uses cross-platform Python libraries.

## Layout

```text
src/stock_reviewer/
    config.py       # Thresholds, universes, and runtime defaults
    criteria.py     # Individual checks and explicit criterion registry
    providers.py    # Yahoo download and ticker extraction
    screening.py    # Combined decisions and result ordering
    reports.py      # HTML report and CSV history
    cli.py          # Run workflow
    __main__.py     # python -m stock_reviewer
src/tests/         # Offline unit/workflow tests and opt-in live check
docs/README.md     # Project documentation
.github/workflows/ci.yml
pyproject.toml
requirements-dev.lock
```

## Install and run

Python 3.9 or later is required for compatibility; use a maintained Python
release for new installations and validate dependency compatibility. The locked
development environment and CI target Python 3.9. Runtime dependencies are
pandas, yfinance, and a compatible peewee version. No Yahoo API key is needed.

From the repository directory on macOS or Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/stock-reviewer
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\stock-reviewer.exe
```

After installation, `python -m stock_reviewer` or the `stock-reviewer` command
works using the virtual environment's interpreter. An internet connection is
required to screen live stocks. Reports and history are written to the `outputs/`
directory, which the program creates automatically. Run from the repository
directory for predictable paths.

## Configuration and screening

Settings are edited in `src/stock_reviewer/config.py`; there are no command-line
options, external configuration files, or environment-variable settings.

- `DEV_MODE=False` selects the hardcoded 78-symbol `NASDAQ_100_TICKERS` list.
  Despite its name, this is a legacy universe, not verified current index membership.
- `DEV_MODE=True` selects AAPL, MSFT, NVDA, PLTR, and SOFI.
- `MARKET_TICKER` is SPY. The main block adds it to the download list if absent,
  and the engine excludes it from screened results.
- `CRITERIA` holds thresholds; `ACTIVE_CRITERIA` lists the active check functions.
  The explicit registry in `criteria.py` maps active names to check functions.

All five checks run for each available stock. Every check must pass; failures
are collected and joined with `; `. Missing tickers receive an explicit failed
no-data result. There is no weighted score or automatic trading.

| Criterion | Formula and default passing condition |
| --- | --- |
| Dollar liquidity | Mean of nonmissing daily `Close × Volume`; at least $100M entry and $50M exit liquidity |
| Price floor | Mean of nonmissing closing prices; at least $10 |
| Long-term trend | Latest nonmissing close at least the mean of the last 200 valid closes; requires 200 observations |
| Drawdown | `(highest close − latest close) / highest close × 100`; between 10% and 35%, inclusive |
| Market-relative performance | Stock return minus SPY return at least −5 percentage points; each return is `(last valid close / first valid close − 1) × 100` |

The default history request is `period="260d"`, `interval="1d"`. It does not
guarantee 260 trading observations or enough observations for the moving average.
Missing closes are removed before calculations. Drawdown uses the highest close
in the downloaded period, not an intraday high. Both liquidity thresholds are
retained, although the higher entry threshold makes the exit threshold redundant
at the defaults.

Passing results omit `failed_reason` and sort descending by available metrics in
insertion order: average dollar volume, average price, moving average, drawdown,
stock return, market return, relative return. This is a multi-column sort, not
an investment score. If no metric columns exist, ticker sorts ascending.

## Reports and history

Each run creates `stock_screen_YYYY-MM-DD_HH-MM-SS.html` with four complete tables:
passed stocks, all results and failure reasons, criteria, and run information.
Run information records the host's local timestamp, development mode, and
screened universe size. The report embeds its CSS and needs no external assets.
It escapes HTML values and retains floating-point metric precision. A filename
collision raises an error rather than overwriting an existing HTML report.

Open the report in a browser or use Microsoft's Live Preview extension in
VS Code to show the rendered HTML. Reports can be copied between computers.

`outputs/master_stock_history.csv` accumulates all results, run timestamps, and criteria.
Each run reads and rewrites history before writing the HTML report. Use one
writer at a time; history writes are not atomic, and a failed HTML write does
not roll back history. Generated reports/history are ignored by Git. Existing
sample outputs were removed during repository preparation; new runs recreate them.

## Development checks

Install the reproducible Python 3.9 development environment:

```sh
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/python -m pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
.venv/bin/python -m pip check
```

On Windows, replace `.venv/bin/` with `.venv\Scripts\` and use the corresponding
executable names. Default tests use controlled data and mocked acquisition;
HTML output is parsed to verify all tables and CSV history is checked for append
behavior. CI runs offline tests, lint, formatting, and types.

To opt into live Yahoo connectivity and schema verification:

```sh
.venv/bin/python -m pytest -m live
```

Live checks assert usable data contracts rather than changing market prices.

## GitHub preparation

Source, tests, documentation, dependency metadata, and CI are ready for GitHub.
Local `AGENTS.md`, virtual environments, credentials, caches, and generated
reports/history are excluded. No remote has been created and nothing has been
uploaded. Configure Git author identity before the first commit; review the
initial baseline before establishing permanent `main` and `dev` branches.
