import json

from agents import Agent, Runner, function_tool
from agents.tool_context import ToolContext

from app.core.run_context import ChatRunContext
from app.tools.charts import build_comparison_chart, build_price_chart
from app.tools.market_data import MarketDataError


@function_tool
def create_price_chart(
    ctx: ToolContext[ChatRunContext],
    symbol: str,
    period: str = "1mo",
) -> str:
    """Cria uma especificacao Plotly de historico de precos para um ticker."""
    try:
        chart = build_price_chart(symbol, period)
    except MarketDataError as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)

    ctx.context.charts.append(chart)
    return chart.model_dump_json()


@function_tool
def create_comparison_chart(
    ctx: ToolContext[ChatRunContext],
    symbols: list[str],
    period: str = "1mo",
) -> str:
    """Cria um unico grafico Plotly comparando os precos de exatamente dois tickers."""
    try:
        chart = build_comparison_chart(symbols, period)
    except (MarketDataError, ValueError) as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)

    ctx.context.charts.append(chart)
    return chart.model_dump_json()


chart_agent = Agent[ChatRunContext](
    name="Chart Agent",
    instructions=(
        "Voce e um especialista em graficos financeiros. Sempre use "
        "create_price_chart quando o usuario pedir um grafico, historico ou "
        "evolucao de preco de um ticker. Quando pedir uma comparacao entre dois "
        "ativos, use create_comparison_chart uma unica vez com os dois tickers. "
        "Explique resumidamente quais ativos e periodo foram usados. Nao ofereca "
        "recomendacoes personalizadas."
    ),
    tools=[create_price_chart, create_comparison_chart],
)


async def run_chart_agent(message: str) -> str:
    result = await Runner.run(chart_agent, message, context=ChatRunContext())
    return result.final_output
