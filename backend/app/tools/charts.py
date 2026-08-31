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
