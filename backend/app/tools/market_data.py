import re

import yfinance as yf
from pydantic import BaseModel


class MarketDataError(ValueError):
    """Raised when market data cannot be retrieved for a ticker."""


class TickerSummary(BaseModel):
    symbol: str
    name: str
    currency: str | None
    current_price: float
    previous_close: float | None
    change_percent: float | None


def get_ticker_summary(symbol: str) -> TickerSummary:
    normalized_symbol = symbol.strip().upper()
    if not re.fullmatch(r"[A-Z0-9.\-^]{1,20}", normalized_symbol):
        raise MarketDataError("Ticker invalido.")

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

