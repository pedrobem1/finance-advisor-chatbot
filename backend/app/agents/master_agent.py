from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from agents import Agent, RunContextWrapper, Runner
from pydantic import BaseModel, Field

from app.agents.chart_agent import chart_agent
from app.agents.finance_agent import finance_agent
from app.agents.rag_agent import rag_agent
from app.agents.scope_guardrail import finance_scope_guardrail
from app.agents.web_agent import extract_web_research_output, web_agent
from app.core.run_context import ChatRunContext
from app.conversations.sessions import create_conversation_session
from app.schemas.chart import ChartArtifact
from app.schemas.source import WebSource


class MasterAgentOutput(BaseModel):
    answer: str
    suggested_questions: list[str] = Field(min_length=3, max_length=3)


def get_current_brazil_datetime() -> datetime:
    return datetime.now(ZoneInfo("America/Sao_Paulo"))


def master_instructions(
    _: RunContextWrapper[ChatRunContext], __: Agent[ChatRunContext]
) -> str:
    current_datetime = get_current_brazil_datetime().strftime("%d/%m/%Y %H:%M")
    return (
        "Voce e o agente principal de um chatbot financeiro. Mantenha o controle "
        "da conversa e produza a resposta final para o usuario. "
        f"A data e hora atual no horario de Brasilia e {current_datetime}. "
        "Use essa data ao interpretar expressoes relativas, como hoje, ontem e "
        "ultimos tres meses."
        "Nesta versao, voce recebe apenas mensagens de texto: nao consegue ver "
        "imagens, abrir anexos ou analisar arquivos enviados pelo usuario. Se for "
        "perguntado sobre uma imagem ou anexo, informe essa limitacao de forma "
        "direta e nunca diga que viu ou analisou algo que nao recebeu." \
        "Use o "
        "web_research_specialist para noticias, eventos de mercado, resultados "
        "recentes de empresas ou para explicar movimentos de indices e ativos em um "
        "periodo especifico. Nao use pesquisa web para definicoes atemporais ou para "
        "uma cotacao, que devem usar os especialistas apropriados. "
        "Use o finance_specialist para dados de mercado ou analise de um ativo. "
        "Use o rag_specialist para definicoes, conceitos e explicacoes "
        "educacionais baseadas na base de conhecimento. Use o "
        "chart_specialist quando o usuario pedir um grafico, historico ou "
        "evolucao de preco, inclusive comparacoes entre dois ativos.  Combine o "
        "resultado recebido com a pergunta do usuario e seja claro sobre limites e "
        "atualizacao dos dados. Nao ofereca recomendacoes personalizadas de compra "
        "ou venda. Ao finalizar, gere exatamente tres perguntas curtas de continuacao, "
        "em portugues, relevantes para a ultima pergunta e para sua resposta. "
        "As perguntas devem aprofundar a analise sem repetir a pergunta do usuario."
    )


master_agent = Agent[ChatRunContext](
    name="Master Agent",
    instructions=master_instructions,
    output_type=MasterAgentOutput,
    input_guardrails=[finance_scope_guardrail],
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
        web_agent.as_tool(
            tool_name="web_research_specialist",
            tool_description=(
                "Especialista em pesquisa web financeira. Use para noticias, eventos "
                "de mercado e fatos que possam ter mudado ou precisem de fontes atuais."
            ),
            custom_output_extractor=extract_web_research_output,
        ),
    ],
)


@dataclass(frozen=True)
class MasterAgentResponse:
    answer: str
    suggested_questions: list[str]
    tools_used: list[str]
    charts: list[ChartArtifact]
    sources: list[WebSource]


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
        sources=context.sources,
    )
