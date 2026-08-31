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


def test_normalize_symbol_adds_b3_suffix() -> None:
    assert market_data.normalize_symbol("petr4") == "PETR4.SA"
    assert market_data.normalize_symbol("hglg11") == "HGLG11.SA"
    assert market_data.normalize_symbol("AAPL") == "AAPL"


def test_get_ticker_summary_rejects_invalid_symbol() -> None:
    try:
        market_data.get_ticker_summary("ticker invalido")
    except market_data.MarketDataError as error:
        assert str(error) == "Ticker invalido."
    else:
        raise AssertionError("Expected MarketDataError")


def test_get_ticker_summary_converts_provider_failure_to_market_data_error(monkeypatch) -> None:
    class UnavailableTicker:
        def history(self, **kwargs):
            raise ConnectionError("provider unavailable")

    monkeypatch.setattr(market_data.yf, "Ticker", lambda symbol: UnavailableTicker())

    try:
        market_data.get_ticker_summary("PETR4")
    except market_data.MarketDataError as error:
        assert str(error) == "Nao foi possivel consultar dados de mercado para PETR4.SA."
    else:
        raise AssertionError("Expected MarketDataError")


def test_get_price_history_returns_points(monkeypatch) -> None:
    class HistoryTicker:
        info = {"shortName": "Empresa Teste", "currency": "BRL"}

        def history(self, **kwargs):
            return pd.DataFrame(
                {"Close": [10.0, 10.5]},
                index=pd.to_datetime(["2026-01-02", "2026-01-05"]),
            )

    monkeypatch.setattr(market_data.yf, "Ticker", lambda symbol: HistoryTicker())

    result = market_data.get_price_history("teste.sa", "1mo")

    assert result.symbol == "TESTE.SA"
    assert result.period == "1mo"
    assert result.points[0].date == "2026-01-02"
    assert result.points[1].close == 10.5


def test_get_price_history_rejects_invalid_period() -> None:
    try:
        market_data.get_price_history("PETR4.SA", "2d")
    except market_data.MarketDataError as error:
        assert "Periodo invalido" in str(error)
    else:
        raise AssertionError("Expected MarketDataError")
