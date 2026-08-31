from types import SimpleNamespace

from app.rag.retriever import KnowledgeRetriever


class FakeEmbeddings:
    def create(self, *, model: str, input: list[str]):
        vectors = []
        for index, text in enumerate(input):
            vector = [1.0, 0.0] if "acao" in text.lower() else [0.0, 1.0]
            vectors.append(SimpleNamespace(index=index, embedding=vector))
        return SimpleNamespace(data=vectors)


class FakeOpenAIClient:
    embeddings = FakeEmbeddings()


def test_builds_and_searches_knowledge_index(tmp_path) -> None:
    knowledge_directory = tmp_path / "knowledge"
    knowledge_directory.mkdir()
    (knowledge_directory / "acoes.md").write_text(
        "Uma acao representa participacao em uma empresa.",
        encoding="utf-8",
    )
    (knowledge_directory / "etfs.md").write_text(
        "Um ETF pode reunir varios ativos.",
        encoding="utf-8",
    )

    retriever = KnowledgeRetriever(
        client=FakeOpenAIClient(),
        embedding_model="test-model",
        knowledge_directory=knowledge_directory,
        index_directory=tmp_path / "index",
    )

    assert retriever.build_index() == 2
    results = retriever.search("O que e uma acao?", top_k=1)

    assert results[0].source == "acoes.md"
