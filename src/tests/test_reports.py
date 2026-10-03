from datetime import datetime, timedelta
from html.parser import HTMLParser

import pandas as pd
import pytest

from stock_reviewer import config, reports


class TableReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = {}
        self.current = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.current = dict(attrs)["id"]
            self.tables[self.current] = []
        elif tag == "tr" and self.current:
            self.row = []
        elif tag in ("td", "th") and self.current:
            self.cell = ""

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.current:
            self.tables[self.current].append(self.row)
        elif tag == "table":
            self.current = None


def test_html_complete_and_history_append(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    timestamp = datetime(2026, 1, 2, 3, 4, 5)
    reason = '<script>alert("x")</script> & missing data'
    results = pd.DataFrame(
        [
            {"ticker": "A", "status": "ok", "failed_reason": "", "avg_price": 12.345678901234567},
            {"ticker": "B", "status": "failed", "failed_reason": reason, "avg_price": 9.0},
        ]
    )
    passed = results.iloc[:1].drop(columns="failed_reason")
    reports.write_stock_screen_output(passed, results, config.CRITERIA, timestamp, True)
    path = tmp_path / "outputs" / "stock_screen_2026-01-02_03-04-05.html"
    text = path.read_text()
    assert "<script>" not in text
    reader = TableReader()
    reader.feed(text)
    assert set(reader.tables) == {"passed", "all_results", "criteria", "run_info"}
    for name, frame in [("passed", passed), ("all_results", results)]:
        assert reader.tables[name] == [list(frame.columns)] + [
            [str(value) for value in row] for row in frame.itertuples(index=False, name=None)
        ]
    assert reader.tables["criteria"][1:] == [
        [key, str(value)] for key, value in config.CRITERIA.items()
    ]
    assert reader.tables["run_info"][1:] == [
        ["run_datetime", "2026-01-02 03:04:05"],
        ["dev_mode", "True"],
        ["universe_size", "2"],
    ]
    reports.update_master_history(results, config.CRITERIA, timestamp)
    reports.update_master_history(results, config.CRITERIA, timestamp + timedelta(seconds=1))
    history = pd.read_csv(tmp_path / "outputs" / "master_stock_history.csv", keep_default_na=False)
    assert len(history) == 4
    assert history.failed_reason.tolist() == ["", reason, "", reason]
    assert history.lookback_days.eq(260).all()
    assert (
        history.run_datetime.tolist() == ["2026-01-02 03:04:05"] * 2 + ["2026-01-02 03:04:06"] * 2
    )
    with pytest.raises(FileExistsError):
        reports.write_stock_screen_output(passed, results, config.CRITERIA, timestamp, True)
    assert path.read_text() == text


def test_empty_passed_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    frame = pd.DataFrame(columns=["ticker", "status"])
    reports.write_stock_screen_output(frame, frame, config.CRITERIA, datetime(2026, 1, 1), False)
    reader = TableReader()
    reader.feed((tmp_path / "outputs" / "stock_screen_2026-01-01_00-00-00.html").read_text())
    assert reader.tables["passed"] == [["ticker", "status"]]
