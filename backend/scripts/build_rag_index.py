from app.rag.retriever import KnowledgeRetriever


def main() -> None:
    retriever = KnowledgeRetriever()
    chunk_count = retriever.build_index()
    print(f"Indice RAG criado com {chunk_count} trechos.")


if __name__ == "__main__":
    main()

