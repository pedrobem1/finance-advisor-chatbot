from collections.abc import Sequence
from pathlib import Path

from openai import OpenAI, OpenAIError

from app.core.config import get_settings
from app.rag.documents import DocumentLoadError, chunk_documents, load_source_documents
from app.rag.vector_store import (
    SearchResult,
    VectorStoreError,
    create_index,
    load_index,
    save_index,
    search_index,
)


EMBEDDING_BATCH_SIZE = 100


class RAGError(ValueError):
    """Raised when the RAG pipeline cannot retrieve knowledge."""


class KnowledgeRetriever:
    def __init__(
        self,
        client: OpenAI | None = None,
        embedding_model: str | None = None,
        knowledge_directory: Path | None = None,
        index_directory: Path | None = None,
    ) -> None:
        settings = get_settings()
        if client is None and not settings.openai_api_key:
            raise RAGError("OPENAI_API_KEY nao configurada para gerar embeddings.")

        self.client = client or OpenAI(api_key=settings.openai_api_key)
        self.embedding_model = embedding_model or settings.rag_embedding_model
        self.knowledge_directory = knowledge_directory or settings.rag_knowledge_directory
        self.index_directory = index_directory or settings.rag_index_directory

    def build_index(self) -> int:
        try:
            documents = load_source_documents(self.knowledge_directory)
            chunks = chunk_documents(documents)
            if not chunks:
                raise RAGError("Nenhum trecho foi gerado a partir dos documentos.")

            embeddings = self._embed_texts([chunk.text for chunk in chunks])
            index = create_index(embeddings, chunks)
            save_index(index, chunks, self.embedding_model, self.index_directory)
            return len(chunks)
        except (DocumentLoadError, VectorStoreError, OpenAIError) as error:
            raise RAGError(str(error)) from error

    def search(self, question: str, top_k: int = 3) -> list[SearchResult]:
        if not question.strip():
            raise RAGError("A pergunta para busca nao pode estar vazia.")

        try:
            index, metadata = load_index(self.index_directory)
            if metadata.embedding_model != self.embedding_model:
                raise RAGError(
                    "O indice foi criado com outro modelo de embedding. Reindexe a base."
                )

            query_embedding = self._embed_texts([question])[0]
            return search_index(index, metadata.chunks, query_embedding, top_k)
        except (VectorStoreError, OpenAIError) as error:
            raise RAGError(str(error)) from error

    def _embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = list(texts[start : start + EMBEDDING_BATCH_SIZE])
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=batch,
            )
            embeddings.extend(item.embedding for item in sorted(response.data, key=lambda item: item.index))
        return embeddings


def search_financial_knowledge(question: str, top_k: int = 3) -> list[SearchResult]:
    return KnowledgeRetriever().search(question, top_k)
