"""Standalone HTML reporting and CSV master history."""

from datetime import datetime
from html import escape
from typing import Any

import pandas as pd

from stock_reviewer.config import MASTER_HISTORY_FILE, OUTPUT_DIR


def update_master_history(
    all_results: pd.DataFrame, criteria: dict[str, Any], run_timestamp: datetime
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    history_df = all_results.copy()
    history_df["run_datetime"] = run_timestamp.strftime("%Y-%m-%d %H:%M:%S")

    for k, v in criteria.items():
        history_df[k] = v

    cols = ["run_datetime", "ticker"] + [
        c for c in history_df.columns if c not in ("ticker", "run_datetime")
    ]
    history_df = history_df[cols]

    if MASTER_HISTORY_FILE.exists():
        existing = pd.read_csv(MASTER_HISTORY_FILE)
        history_df = pd.concat([existing, history_df], ignore_index=True)

    history_df.to_csv(MASTER_HISTORY_FILE, index=False)

    print(f"Master history updated: {MASTER_HISTORY_FILE}")


def write_stock_screen_output(
    passed: pd.DataFrame,
    all_results: pd.DataFrame,
    criteria: dict[str, Any],
    run_timestamp: datetime,
    dev_mode: bool,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    criteria_df = pd.DataFrame([{"criteria": k, "value": v} for k, v in criteria.items()])

    run_info_df = pd.DataFrame(
        {
            "field": ["run_datetime", "dev_mode", "universe_size"],
            "value": [
                run_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                str(dev_mode),
                str(len(all_results)),
            ],
        }
    )

    tables = (
        ("passed", "Passed stocks", passed),
        ("all_results", "All results and failure reasons", all_results),
        ("criteria", "Screening criteria", criteria_df),
        ("run_info", "Run information", run_info_df),
    )
    sections = []
    for name, title, data in tables:
        table = data.to_html(
            index=False,
            escape=True,
            table_id=name,
            border=0,
            max_rows=None,
            max_cols=None,
            float_format=lambda value: repr(float(value)),
        )
        sections.append(
            f'<section id="section-{name}"><h2>{escape(title)}</h2>'
            f'<p>{len(data)} rows</p><div class="table-wrap">{table}</div></section>'
        )
    navigation = " | ".join(
        f'<a href="#section-{name}">{escape(title)}</a>' for name, title, _ in tables
    )
    report = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Stock screen {run_timestamp:%Y-%m-%d %H:%M:%S}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #17212b; background: #f5f7fa; }}
h1, h2 {{ color: #183b56; }}
nav {{ line-height: 2; }}
a {{ color: #005ea8; }}
section {{ background: white; padding: 1.25rem; margin: 1.5rem 0; border-radius: 8px; }}
.table-wrap {{ overflow-x: auto; max-height: 70vh; }}
table {{ border-collapse: collapse; width: 100%; font-size: .9rem; }}
th, td {{ padding: .65rem; border-bottom: 1px solid #dfe5ec; text-align: left; vertical-align: top; }}
th {{ background: #eaf0f6; position: sticky; top: 0; }}
tbody tr:nth-child(even) {{ background: #f7f9fc; }}
td {{ white-space: nowrap; }}
@media print {{ .table-wrap {{ max-height: none; overflow: visible; }} th {{ position: static; }} }}
</style>
</head>
<body>
<h1>Stock screen</h1>
<p>Run: {run_timestamp:%Y-%m-%d %H:%M:%S} · Reviewed: {len(all_results)} · Passed: {len(passed)}</p>
<nav>{navigation}</nav>
{"".join(sections)}
</body>
</html>
"""
    output_file = OUTPUT_DIR / "stock_screen.html"
    with output_file.open("w", encoding="utf-8") as output:
        output.write(report)
    print(f"Results written to {output_file}")
