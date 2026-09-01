import pandas as pd

from app.tools import market_data


class FakeTicker:
    info = {
        "longName": "Empresa Teste",
        "currency": "BRL",
        "marketCap": 1_000_000.0,
        "trailingPE": 8.5,
        "priceToBook": 1.2,
        "dividendYield": 0.08,
        "trailingAnnualDividendRate": 1.1,
        "lastDividendValue": 0.3,
        "exDividendDate": 1_788_220_800,
    }

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
    assert result.market_cap == 1_000_000.0
    assert result.trailing_pe == 8.5
    assert result.price_to_book == 1.2
    assert result.dividend_yield_percent == 8.0
    assert result.trailing_annual_dividend_rate == 1.1
    assert result.last_dividend_value == 0.3
    assert result.ex_dividend_date == "2026-09-01"
    assert result.dividends_last_12_months == 0
    assert result.dividend_history == []


def test_get_ticker_summary_returns_dividend_history_for_last_12_months(monkeypatch) -> None:
    class DividendHistoryTicker:
        info = {}

        def history(self, **kwargs):
            if kwargs["period"] == "1y":
                return pd.DataFrame(
                    {"Close": [10.0, 10.5], "Dividends": [0.25, 0.35]},
                    index=pd.to_datetime(["2026-03-15", "2026-08-15"]),
                )
            return pd.DataFrame({"Close": [10.0, 10.5]})

    monkeypatch.setattr(market_data.yf, "Ticker", lambda symbol: DividendHistoryTicker())

    result = market_data.get_ticker_summary("TESTE")

    assert result.dividends_last_12_months == 0.6
    assert [item.model_dump() for item in result.dividend_history] == [
        {"date": "2026-03-15", "amount": 0.25},
        {"date": "2026-08-15", "amount": 0.35},
    ]


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
