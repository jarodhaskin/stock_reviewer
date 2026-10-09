import pandas as pd
import pytest

from stock_reviewer import config, providers


def test_download_contract(monkeypatch):
    calls = []
    frame = pd.DataFrame({"Close": [100], "Volume": [1e6]})

    def download(*args, **kwargs):
        calls.append((args, kwargs))
        return frame

    monkeypatch.setattr(providers.yf, "download", download)
    assert providers.bulk_download([" aapl ", "spy"], config.CRITERIA) is frame
    assert calls == [
        (
            ("AAPL SPY",),
            {
                "period": "260d",
                "interval": "1d",
                "auto_adjust": True,
                "group_by": "ticker",
                "progress": False,
                "threads": True,
            },
        )
    ]


def test_extraction():
    frame = pd.DataFrame({"Close": [100.0, float("nan")], "Volume": [1e6, float("nan")]})
    bulk = pd.concat({"A": frame}, axis=1)
    pd.testing.assert_frame_equal(providers.extract_ticker_frame(bulk, "A"), frame.iloc[:1])
    pd.testing.assert_frame_equal(providers.extract_ticker_frame(frame, "A"), frame.iloc[:1])
    assert providers.extract_ticker_frame(bulk, "MISSING") is None
    assert providers.extract_ticker_frame(pd.DataFrame(), "A") is None


@pytest.mark.live
def test_live_yahoo_contract():
    raw = providers.bulk_download(["AAPL", "SPY"], config.CRITERIA)
    for ticker in ("AAPL", "SPY"):
        frame = providers.extract_ticker_frame(raw, ticker)
        assert frame is not None and len(frame) >= 2
        assert {"Close", "Volume"}.issubset(frame.columns)
        assert frame.Close.dropna().gt(0).all()
