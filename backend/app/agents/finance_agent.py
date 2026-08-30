from agents import Agent, Runner


finance_agent = Agent(
    name="Finance Agent",
    instructions=(
        "Voce e um educador financeiro. Responda perguntas sobre acoes, ETFs, "
        "FIIs e conceitos de financas de forma clara, objetiva e didatica. "
        "Nao ofereca recomendacoes personalizadas de compra ou venda. "
        "Quando nao tiver dados suficientes ou atualizados, deixe isso claro."
    ),
)


async def run_finance_agent(message: str) -> str:
    result = await Runner.run(finance_agent, message)
    return result.final_output

