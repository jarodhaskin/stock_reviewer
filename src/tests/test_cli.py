from stock_reviewer import cli, config


def test_main_workflow(monkeypatch):
    events = []
    monkeypatch.setattr(cli, "DEV_MODE", True)

    def screen(tickers, settings):
        events.append(("screen", tickers, settings))
        return "passed", "all"

    monkeypatch.setattr(cli, "screen_stocks", screen)
    monkeypatch.setattr(
        cli, "update_master_history", lambda *args: events.append(("history", args))
    )
    monkeypatch.setattr(
        cli, "write_stock_screen_output", lambda *args: events.append(("report", args))
    )
    cli.main()
    assert events[0] == ("screen", config.DEV_TICKERS + ["SPY"], config.CRITERIA)
    assert [event[0] for event in events] == ["screen", "history", "report"]
    assert events[1][1][0] == "all"
    assert events[2][1][:3] == ("passed", "all", config.CRITERIA)
    assert events[2][1][-1] is True
