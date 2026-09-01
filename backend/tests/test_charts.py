from types import SimpleNamespace

from app.agents.chart_agent import create_comparison_chart, create_price_chart
from app.core.run_context import ChatRunContext
from app.schemas.chart import ChartArtifact
from app.tools.charts import build_comparison_chart, build_price_chart
from app.tools.market_data import PriceHistory, PricePoint


def test_build_price_chart_returns_plotly_figure(monkeypatch) -> None:
    history = PriceHistory(
        symbol="TESTE.SA",
        name="Empresa Teste",
        currency="BRL",
        period="1mo",
        points=[
            PricePoint(date="2026-01-02", close=10.0),
            PricePoint(date="2026-01-05", close=10.5),
        ],
    )
    monkeypatch.setattr("app.tools.charts.get_price_history", lambda symbol, period: history)

    chart = build_price_chart("TESTE.SA")

    assert chart.symbol == "TESTE.SA"
    assert chart.figure["data"][0]["x"] == ["2026-01-02", "2026-01-05"]
    assert chart.figure["data"][0]["y"] == [10.0, 10.5]


def test_chart_tool_adds_artifact_to_run_context(monkeypatch) -> None:
    chart = ChartArtifact(
        symbol="TESTE.SA",
        period="1mo",
        figure={"data": [], "layout": {}},
    )
    monkeypatch.setattr("app.agents.chart_agent.build_price_chart", lambda symbol, period: chart)
    context = ChatRunContext()

    create_price_chart.__wrapped__(
        SimpleNamespace(context=context),
        symbol="TESTE.SA",
        period="1mo",
    )

    assert context.charts == [chart]


def test_build_comparison_chart_returns_two_series(monkeypatch) -> None:
    histories = {
        "PETR4.SA": PriceHistory(
            symbol="PETR4.SA", name="Petrobras", currency="BRL", period="3mo",
            points=[PricePoint(date="2026-06-01", close=30.0)],
        ),
        "VALE3.SA": PriceHistory(
            symbol="VALE3.SA", name="Vale", currency="BRL", period="3mo",
            points=[PricePoint(date="2026-06-01", close=50.0)],
        ),
    }
    monkeypatch.setattr("app.tools.charts.get_price_history", lambda symbol, period: histories[symbol])

    chart = build_comparison_chart(["PETR4.SA", "VALE3.SA"], "3mo")

    assert chart.chart_type == "comparison_line"
    assert chart.symbol == "PETR4.SA vs VALE3.SA"
    assert [series["name"] for series in chart.figure["data"]] == ["PETR4.SA", "VALE3.SA"]


def test_comparison_chart_tool_adds_artifact_to_run_context(monkeypatch) -> None:
    chart = ChartArtifact(symbol="PETR4.SA vs VALE3.SA", period="3mo", figure={"data": [], "layout": {}})
    monkeypatch.setattr("app.agents.chart_agent.build_comparison_chart", lambda symbols, period: chart)
    context = ChatRunContext()

    create_comparison_chart.__wrapped__(
        SimpleNamespace(context=context), symbols=["PETR4", "VALE3"], period="3mo"
    )

    assert context.charts == [chart]
