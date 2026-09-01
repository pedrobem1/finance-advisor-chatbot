import plotly.graph_objects as go

from app.schemas.chart import ChartArtifact
from app.tools.market_data import PriceHistory, get_price_history


def build_price_chart(symbol: str, period: str = "1mo") -> ChartArtifact:
    history = get_price_history(symbol, period)
    figure = go.Figure(
        data=[
            go.Scatter(
                x=[point.date for point in history.points],
                y=[point.close for point in history.points],
                mode="lines",
                name=history.symbol,
            )
        ]
    )
    figure.update_layout(
        title=f"Historico de preco: {history.name} ({history.period})",
        xaxis_title="Data",
        yaxis_title=f"Preco ({history.currency or 'N/A'})",
        template="plotly_white",
    )

    return ChartArtifact(
        symbol=history.symbol,
        period=history.period,
        figure=figure.to_plotly_json(),
    )


def build_comparison_chart(symbols: list[str], period: str = "1mo") -> ChartArtifact:
    if len(symbols) != 2:
        raise ValueError("Informe exatamente dois tickers para comparar.")

    histories = [get_price_history(symbol, period) for symbol in symbols]
    if histories[0].symbol == histories[1].symbol:
        raise ValueError("Use dois tickers diferentes para comparar.")
    if histories[0].currency != histories[1].currency:
        raise ValueError("Os ativos devem usar a mesma moeda para comparar precos.")

    figure = go.Figure(
        data=[
            go.Scatter(
                x=[point.date for point in history.points],
                y=[point.close for point in history.points],
                mode="lines",
                name=history.symbol,
            )
            for history in histories
        ]
    )
    figure.update_layout(
        title=f"Comparacao de precos: {histories[0].name} e {histories[1].name} ({period})",
        xaxis_title="Data",
        yaxis_title=f"Preco ({histories[0].currency or 'N/A'})",
        template="plotly_white",
    )

    return ChartArtifact(
        chart_type="comparison_line",
        symbol=f"{histories[0].symbol} vs {histories[1].symbol}",
        period=period,
        figure=figure.to_plotly_json(),
    )
