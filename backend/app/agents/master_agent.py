from agents import Agent, Runner

from app.agents.finance_agent import finance_agent


master_agent = Agent(
    name="Master Agent",
    instructions=(
        "Voce e o agente principal de um chatbot financeiro. Mantenha o controle "
        "da conversa e produza a resposta final para o usuario. "
        "Use o finance_specialist quando precisar de explicacoes financeiras "
        "ou dados de um ativo. Combine o resultado recebido com a pergunta do "
        "usuario e seja claro sobre limites e atualizacao dos dados. "
        "Nao ofereca recomendacoes personalizadas de compra ou venda."
    ),
    tools=[
        finance_agent.as_tool(
            tool_name="finance_specialist",
            tool_description=(
                "Especialista em conceitos financeiros e dados de mercado. "
                "Use quando a pergunta exigir analise financeira ou consulta "
                "de um ticker."
            ),
        )
    ],
)


async def run_master_agent(message: str) -> str:
    result = await Runner.run(master_agent, message)
    return result.final_output

