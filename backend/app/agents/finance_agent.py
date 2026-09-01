import json

from agents import Agent, Runner, function_tool

from app.core.run_context import ChatRunContext
from app.tools.market_data import MarketDataError, get_ticker_summary


@function_tool
def get_market_summary(symbol: str) -> str:
    """Busca o resumo mais recente de mercado para um ticker."""
    try:
        summary = get_ticker_summary(symbol)
    except MarketDataError as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)

    return summary.model_dump_json()


finance_agent = Agent[ChatRunContext](
    name="Finance Agent",
    instructions=(
        "Voce e um educador financeiro. Responda perguntas sobre acoes, ETFs, "
        "FIIs e conceitos de financas de forma clara, objetiva e didatica. "
        "Nao ofereca recomendacoes personalizadas de compra ou venda. "
        "Quando nao tiver dados suficientes ou atualizados, deixe isso claro. "
        "Use a tool get_market_summary sempre que considerar que dados atuais "
        "ou especificos de um ticker, inclusive indicadores e dividendos, possam "
        "tornar sua resposta mais precisa. Para perguntas sobre proventos, use o "
        "historico de dividendos dos ultimos 12 meses retornado pela tool. "
        "Voce nao precisa usar a tool em perguntas puramente conceituais."
    ),
    tools=[get_market_summary],
)


async def run_finance_agent(message: str) -> str:
    result = await Runner.run(finance_agent, message, context=ChatRunContext())
    return result.final_output
