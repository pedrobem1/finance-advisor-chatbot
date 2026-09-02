import asyncio
from types import SimpleNamespace

from app.agents.web_agent import MAX_WEB_SOURCES, extract_web_research_output, extract_web_sources
from app.core.run_context import ChatRunContext


def test_extract_web_sources_returns_unique_search_urls() -> None:
    result = SimpleNamespace(
        raw_responses=[
            SimpleNamespace(
                output=[
                    SimpleNamespace(
                        type="web_search_call",
                        action=SimpleNamespace(
                            type="search",
                            sources=[
                                SimpleNamespace(url="https://www.bcb.gov.br/decisao"),
                                SimpleNamespace(url="https://www.bcb.gov.br/decisao"),
                                SimpleNamespace(url="https://www.gov.br/fazenda/noticias"),
                                SimpleNamespace(url="https://www.b3.com.br/noticias"),
                                SimpleNamespace(url="https://www.cvm.gov.br/noticias"),
                                SimpleNamespace(url="https://www.ibge.gov.br/noticias"),
                                SimpleNamespace(url="https://www.tesouro.gov.br/noticias"),
                            ],
                        ),
                    )
                ]
            )
        ]
    )

    assert [source.model_dump() for source in extract_web_sources(result)] == [
        {"url": "https://www.bcb.gov.br/decisao", "domain": "bcb.gov.br"},
        {"url": "https://www.gov.br/fazenda/noticias", "domain": "gov.br"},
        {"url": "https://www.b3.com.br/noticias", "domain": "b3.com.br"},
        {"url": "https://www.cvm.gov.br/noticias", "domain": "cvm.gov.br"},
        {"url": "https://www.ibge.gov.br/noticias", "domain": "ibge.gov.br"},
    ]
    assert len(extract_web_sources(result)) == MAX_WEB_SOURCES


def test_extract_web_research_output_adds_sources_to_chat_context() -> None:
    context = ChatRunContext()
    result = SimpleNamespace(
        final_output="Resumo da pesquisa",
        context_wrapper=SimpleNamespace(context=context),
        raw_responses=[
            SimpleNamespace(
                output=[
                    SimpleNamespace(
                        type="web_search_call",
                        action=SimpleNamespace(
                            type="search",
                            sources=[SimpleNamespace(url="https://www.b3.com.br/noticia")],
                        ),
                    )
                ]
            )
        ],
    )

    output = asyncio.run(extract_web_research_output(result))

    assert output == "Resumo da pesquisa"
    assert [source.model_dump() for source in context.sources] == [
        {"url": "https://www.b3.com.br/noticia", "domain": "b3.com.br"}
    ]
