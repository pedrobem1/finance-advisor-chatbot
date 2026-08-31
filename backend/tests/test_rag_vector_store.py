from app.rag.documents import DocumentChunk
from app.rag.vector_store import create_index, load_index, save_index, search_index


def test_persists_and_searches_vector_index(tmp_path) -> None:
    chunks = [
        DocumentChunk(id="acoes:0:0", source="acoes.md", text="acoes", page=None),
        DocumentChunk(id="etfs:0:0", source="etfs.md", text="etfs", page=None),
    ]
    index = create_index([[1.0, 0.0], [0.0, 1.0]], chunks)

    save_index(index, chunks, "test-model", tmp_path)
    loaded_index, metadata = load_index(tmp_path)
    results = search_index(loaded_index, metadata.chunks, [0.9, 0.1], top_k=1)

    assert metadata.embedding_model == "test-model"
    assert results[0].source == "acoes.md"
    assert results[0].score > 0.9

