import re

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


def get_ticker_summary(symbol: str) -> TickerSummary:
    normalized_symbol = normalize_symbol(symbol)

    ticker = yf.Ticker(normalized_symbol)
    history = ticker.history(period="5d", auto_adjust=False)
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

    return TickerSummary(
        symbol=normalized_symbol,
        name=info.get("longName") or info.get("shortName") or normalized_symbol,
        currency=info.get("currency"),
        current_price=current_price,
        previous_close=previous_close,
        change_percent=change_percent,
    )


def get_price_history(symbol: str, period: str = "1mo") -> PriceHistory:
    normalized_symbol = normalize_symbol(symbol)
    if period not in SUPPORTED_HISTORY_PERIODS:
        raise MarketDataError(
            f"Periodo invalido. Use um destes: {', '.join(sorted(SUPPORTED_HISTORY_PERIODS))}."
        )

    ticker = yf.Ticker(normalized_symbol)
    history = ticker.history(period=period, auto_adjust=False)
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
