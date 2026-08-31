import json

from agents import Agent, Runner, function_tool

from app.rag.retriever import RAGError, search_financial_knowledge


@function_tool
def search_knowledge_base(question: str) -> str:
    """Busca trechos relevantes da base de conhecimento financeiro."""
    try:
        results = search_financial_knowledge(question)
    except RAGError as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)

    return json.dumps(
        {"results": [result.model_dump() for result in results]},
        ensure_ascii=False,
    )


rag_agent = Agent(
    name="RAG Agent",
    instructions=(
        "Voce e um especialista em responder conceitos financeiros com base na "
        "base de conhecimento do projeto. Sempre chame search_knowledge_base "
        "antes de responder uma pergunta conceitual. Use apenas os trechos "
        "recuperados como base factual, explique de forma didatica e informe "
        "as fontes no formato [Fonte: caminho do arquivo, pagina N] quando "
        "uma pagina estiver disponivel. Nao ofereca recomendacoes personalizadas."
    ),
    tools=[search_knowledge_base],
)


async def run_rag_agent(message: str) -> str:
    result = await Runner.run(rag_agent, message)
    return result.final_output

