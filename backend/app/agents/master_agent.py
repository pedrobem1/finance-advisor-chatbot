from dataclasses import dataclass

from agents import Agent, Runner

from app.agents.finance_agent import finance_agent
from app.agents.rag_agent import rag_agent


master_agent = Agent(
    name="Master Agent",
    instructions=(
        "Voce e o agente principal de um chatbot financeiro. Mantenha o controle "
        "da conversa e produza a resposta final para o usuario. "
        "Use o finance_specialist para dados de mercado ou analise de um ativo. "
        "Use o rag_specialist para definicoes, conceitos e explicacoes "
        "educacionais baseadas na base de conhecimento. Preserve as fontes "
        "informadas pelo especialista quando elas existirem. Combine o resultado "
        "recebido com a pergunta do usuario e seja claro sobre limites e "
        "atualizacao dos dados. "
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
        ),
        rag_agent.as_tool(
            tool_name="rag_specialist",
            tool_description=(
                "Especialista em conceitos financeiros baseado nos documentos "
                "indexados localmente. Use para perguntas educacionais e "
                "explicacoes de termos financeiros."
            ),
        ),
    ],
)


@dataclass(frozen=True)
class MasterAgentResponse:
    answer: str
    tools_used: list[str]


def extract_tools_used(run_result) -> list[str]:
    tools_used: list[str] = []
    for item in run_result.new_items:
        if getattr(item, "type", None) != "tool_call_item":
            continue

        tool_name = getattr(item, "tool_name", None)
        if tool_name and tool_name not in tools_used:
            tools_used.append(tool_name)
    return tools_used


async def run_master_agent(message: str) -> MasterAgentResponse:
    result = await Runner.run(master_agent, message)
    return MasterAgentResponse(
        answer=str(result.final_output),
        tools_used=extract_tools_used(result),
    )
