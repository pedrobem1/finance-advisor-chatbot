import re
from datetime import datetime, timezone
from numbers import Real

import yfinance as yf
from pydantic import BaseModel


SUPPORTED_HISTORY_PERIODS = {"1mo", "3mo", "6mo", "1y", "5y"}
TICKER_PATTERN = re.compile(r"[A-Z0-9.\-^]{1,20}")
B3_TICKER_PATTERN = re.compile(r"[A-Z]{4,5}\d{1,2}")


class MarketDataError(ValueError):
    """Raised when market data cannot be retrieved for a ticker."""


class TickerSummary(BaseModel):
    symbol: str
    name: str
    currency: str | None
    current_price: float
    previous_close: float | None
    change_percent: float | None
    market_cap: float | None
    trailing_pe: float | None
    price_to_book: float | None
    dividend_yield_percent: float | None
    trailing_annual_dividend_rate: float | None
    last_dividend_value: float | None
    ex_dividend_date: str | None
    dividends_last_12_months: float
    dividend_history: list["DividendPayment"]


class DividendPayment(BaseModel):
    date: str
    amount: float


class PricePoint(BaseModel):
    date: str
    close: float


class PriceHistory(BaseModel):
    symbol: str
    name: str
    currency: str | None
    period: str
    points: list[PricePoint]


def normalize_symbol(symbol: str) -> str:
    normalized_symbol = symbol.strip().upper()
    if not TICKER_PATTERN.fullmatch(normalized_symbol):
        raise MarketDataError("Ticker invalido.")
    if B3_TICKER_PATTERN.fullmatch(normalized_symbol):
        return f"{normalized_symbol}.SA"
    return normalized_symbol


def _optional_float(value: object) -> float | None:
    return float(value) if isinstance(value, Real) else None


def _percent_from_decimal(value: object) -> float | None:
    numeric_value = _optional_float(value)
    return numeric_value * 100 if numeric_value is not None else None


def _format_market_date(value: object) -> str | None:
    if isinstance(value, Real):
        return datetime.fromtimestamp(value, tz=timezone.utc).date().isoformat()
    if hasattr(value, "date"):
        return value.date().isoformat()
    return None


def _get_dividend_history(ticker: yf.Ticker) -> list[DividendPayment]:
    try:
        history = ticker.history(period="1y", auto_adjust=False, actions=True)
    except Exception:
        return []

    if history.empty or "Dividends" not in history:
        return []

    return [
        DividendPayment(date=index.date().isoformat(), amount=float(amount))
        for index, amount in history["Dividends"].dropna().items()
        if isinstance(amount, Real) and amount != 0
    ]


def get_ticker_summary(symbol: str) -> TickerSummary:
    normalized_symbol = normalize_symbol(symbol)

    try:
        ticker = yf.Ticker(normalized_symbol)
        history = ticker.history(period="5d", auto_adjust=False)
    except Exception as error:
        raise MarketDataError(
            f"Nao foi possivel consultar dados de mercado para {normalized_symbol}."
        ) from error

    if history.empty or "Close" not in history:
        raise MarketDataError(f"Nao foi possivel encontrar dados para {normalized_symbol}.")

    closes = history["Close"].dropna()
    if closes.empty:
        raise MarketDataError(f"Nao foi possivel encontrar preco para {normalized_symbol}.")

    current_price = float(closes.iloc[-1])
    previous_close = float(closes.iloc[-2]) if len(closes) > 1 else None
    change_percent = None
    if previous_close not in (None, 0):
        change_percent = ((current_price - previous_close) / previous_close) * 100

    try:
        info = ticker.info
    except Exception:
        info = {}

    dividend_history = _get_dividend_history(ticker)

    return TickerSummary(
        symbol=normalized_symbol,
        name=info.get("longName") or info.get("shortName") or normalized_symbol,
        currency=info.get("currency"),
        current_price=current_price,
        previous_close=previous_close,
        change_percent=change_percent,
        market_cap=_optional_float(info.get("marketCap")),
        trailing_pe=_optional_float(info.get("trailingPE")),
        price_to_book=_optional_float(info.get("priceToBook")),
        dividend_yield_percent=_percent_from_decimal(info.get("dividendYield")),
        trailing_annual_dividend_rate=_optional_float(
            info.get("trailingAnnualDividendRate")
        ),
        last_dividend_value=_optional_float(info.get("lastDividendValue")),
        ex_dividend_date=_format_market_date(info.get("exDividendDate")),
        dividends_last_12_months=sum(item.amount for item in dividend_history),
        dividend_history=dividend_history,
    )


def get_price_history(symbol: str, period: str = "1mo") -> PriceHistory:
    normalized_symbol = normalize_symbol(symbol)
    if period not in SUPPORTED_HISTORY_PERIODS:
        raise MarketDataError(
            f"Periodo invalido. Use um destes: {', '.join(sorted(SUPPORTED_HISTORY_PERIODS))}."
        )

    try:
        ticker = yf.Ticker(normalized_symbol)
        history = ticker.history(period=period, auto_adjust=False)
    except Exception as error:
        raise MarketDataError(
            f"Nao foi possivel consultar o historico de {normalized_symbol}."
        ) from error

    if history.empty or "Close" not in history:
        raise MarketDataError(f"Nao foi possivel encontrar historico para {normalized_symbol}.")

    closes = history["Close"].dropna()
    if closes.empty:
        raise MarketDataError(f"Nao foi possivel encontrar precos para {normalized_symbol}.")

    try:
        info = ticker.info
    except Exception:
        info = {}

    points = [
        PricePoint(date=index.date().isoformat(), close=float(close))
        for index, close in closes.items()
    ]
    return PriceHistory(
        symbol=normalized_symbol,
        name=info.get("longName") or info.get("shortName") or normalized_symbol,
        currency=info.get("currency"),
        period=period,
        points=points,
    )
