from dataclasses import dataclass
from uuid import UUID

from agents import Agent, Runner
from pydantic import BaseModel, Field

from app.agents.chart_agent import chart_agent
from app.agents.finance_agent import finance_agent
from app.agents.rag_agent import rag_agent
from app.core.run_context import ChatRunContext
from app.conversations.sessions import create_conversation_session
from app.schemas.chart import ChartArtifact


class MasterAgentOutput(BaseModel):
    answer: str
    suggested_questions: list[str] = Field(min_length=3, max_length=3)


master_agent = Agent[ChatRunContext](
    name="Master Agent",
    instructions=(
        "Voce e o agente principal de um chatbot financeiro. Mantenha o controle "
        "da conversa e produza a resposta final para o usuario. "
        "Use o finance_specialist para dados de mercado ou analise de um ativo. "
        "Use o rag_specialist para definicoes, conceitos e explicacoes "
        "educacionais baseadas na base de conhecimento. Preserve as fontes "
        "informadas pelo especialista quando elas existirem. Use o "
        "chart_specialist quando o usuario pedir um grafico, historico ou "
        "evolucao de preco. Combine o resultado recebido com a pergunta do "
        "usuario e seja claro sobre limites e "
        "atualizacao dos dados. "
        "Nao ofereca recomendacoes personalizadas de compra ou venda. "
        "Ao finalizar, gere exatamente tres perguntas curtas de continuacao, "
        "em portugues, relevantes para a ultima pergunta e para sua resposta. "
        "As perguntas devem aprofundar a analise sem repetir a pergunta do usuario."
    ),
    output_type=MasterAgentOutput,
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
        chart_agent.as_tool(
            tool_name="chart_specialist",
            tool_description=(
                "Especialista em graficos de historico de precos. Use quando o "
                "usuario pedir um grafico ou uma serie historica de um ticker."
            ),
        ),
    ],
)


@dataclass(frozen=True)
class MasterAgentResponse:
    answer: str
    suggested_questions: list[str]
    tools_used: list[str]
    charts: list[ChartArtifact]


def extract_tools_used(run_result) -> list[str]:
    tools_used: list[str] = []
    for item in run_result.new_items:
        if getattr(item, "type", None) != "tool_call_item":
            continue

        tool_name = getattr(item, "tool_name", None)
        if tool_name and tool_name not in tools_used:
            tools_used.append(tool_name)
    return tools_used


async def run_master_agent(message: str, conversation_id: UUID) -> MasterAgentResponse:
    session = create_conversation_session(conversation_id)
    context = ChatRunContext()
    try:
        result = await Runner.run(master_agent, message, context=context, session=session)
    finally:
        session.close()

    return MasterAgentResponse(
        answer=result.final_output.answer,
        suggested_questions=result.final_output.suggested_questions,
        tools_used=extract_tools_used(result),
        charts=context.charts,
    )
