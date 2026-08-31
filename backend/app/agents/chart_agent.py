import json

from agents import Agent, Runner, function_tool
from agents.tool_context import ToolContext

from app.core.run_context import ChatRunContext
from app.tools.charts import build_price_chart
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


chart_agent = Agent[ChatRunContext](
    name="Chart Agent",
    instructions=(
        "Voce e um especialista em graficos financeiros. Sempre use "
        "create_price_chart quando o usuario pedir um grafico, historico ou "
        "evolucao de preco de um ticker. Explique resumidamente qual ativo e "
        "periodo foram usados. Nao ofereca recomendacoes personalizadas."
    ),
    tools=[create_price_chart],
)


async def run_chart_agent(message: str) -> str:
    result = await Runner.run(chart_agent, message, context=ChatRunContext())
    return result.final_output
