import pandas as pd

from app.tools import market_data


class FakeTicker:
    info = {"longName": "Empresa Teste", "currency": "BRL"}

    def history(self, **kwargs):
        return pd.DataFrame({"Close": [10.0, 10.5]})


def test_get_ticker_summary_returns_price_and_change(monkeypatch) -> None:
    monkeypatch.setattr(market_data.yf, "Ticker", lambda symbol: FakeTicker())

    result = market_data.get_ticker_summary("teste.sa")

    assert result.symbol == "TESTE.SA"
    assert result.name == "Empresa Teste"
    assert result.currency == "BRL"
    assert result.current_price == 10.5
    assert result.previous_close == 10.0
    assert result.change_percent == 5.0


def test_get_ticker_summary_rejects_invalid_symbol() -> None:
    try:
        market_data.get_ticker_summary("ticker invalido")
    except market_data.MarketDataError as error:
        assert str(error) == "Ticker invalido."
    else:
        raise AssertionError("Expected MarketDataError")

