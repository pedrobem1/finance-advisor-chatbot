from urllib.parse import urlparse

from agents import Agent, ModelSettings, RunResult, RunResultStreaming, Runner, WebSearchTool

from app.core.run_context import ChatRunContext
from app.schemas.source import WebSource

MAX_WEB_SOURCES = 5


def extract_web_sources(result: RunResult | RunResultStreaming) -> list[WebSource]:
    sources: list[WebSource] = []
    seen_urls: set[str] = set()

    for response in result.raw_responses:
        for item in response.output:
            if getattr(item, "type", None) != "web_search_call":
                continue

            action = getattr(item, "action", None)
            if getattr(action, "type", None) != "search":
                continue

            for source in getattr(action, "sources", None) or []:
                url = getattr(source, "url", None)
                if not isinstance(url, str) or url in seen_urls:
                    continue

                domain = urlparse(url).netloc.removeprefix("www.")
                if not domain:
                    continue

                seen_urls.add(url)
                sources.append(WebSource(url=url, domain=domain))
                if len(sources) == MAX_WEB_SOURCES:
                    return sources

    return sources


async def extract_web_research_output(result: RunResult | RunResultStreaming) -> str:
    context = result.context_wrapper.context
    if isinstance(context, ChatRunContext):
        context.sources.extend(extract_web_sources(result))

    return str(result.final_output or "")


web_agent = Agent[ChatRunContext](
    name="Web Research Agent",
    instructions=(
        "Voce e um pesquisador financeiro. Sempre use uma busca web focada antes de responder. "
        "Faca no maximo uma busca por pergunta, exceto se ela falhar. "
        "Pesquise noticias, fatos e eventos financeiros atuais ou historicos em fontes "
        "confiaveis, priorizando fontes primarias quando existirem. Explique os fatos "
        "encontrados de forma objetiva, deixe incertezas claras e nao invente fontes. "
        "Nao ofereca recomendacoes personalizadas de compra ou venda."
    ),
    model_settings=ModelSettings(
        response_include=["web_search_call.action.sources"],
    ),
    tools=[WebSearchTool(search_context_size="low", external_web_access=True)],
)


async def run_web_agent(message: str) -> str:
    result = await Runner.run(web_agent, message, context=ChatRunContext())
    return result.final_output
