import json
from pathlib import Path

import faiss
import numpy as np
from pydantic import BaseModel

from app.rag.documents import DocumentChunk


INDEX_FILENAME = "index.faiss"
METADATA_FILENAME = "metadata.json"


class SearchResult(DocumentChunk):
    score: float


class PersistedIndex(BaseModel):
    embedding_model: str
    chunks: list[DocumentChunk]


class VectorStoreError(ValueError):
    """Raised when the local vector index is invalid or unavailable."""


def create_index(embeddings: list[list[float]], chunks: list[DocumentChunk]) -> faiss.Index:
    if not embeddings or not chunks:
        raise VectorStoreError("Nao e possivel criar um indice vazio.")
    if len(embeddings) != len(chunks):
        raise VectorStoreError("A quantidade de embeddings nao corresponde aos trechos.")

    vectors = np.asarray(embeddings, dtype="float32")
    if vectors.ndim != 2:
        raise VectorStoreError("Os embeddings devem formar uma matriz bidimensional.")

    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    return index


def save_index(
    index: faiss.Index,
    chunks: list[DocumentChunk],
    embedding_model: str,
    index_directory: Path,
) -> None:
    index_directory.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_directory / INDEX_FILENAME))
    metadata = PersistedIndex(embedding_model=embedding_model, chunks=chunks)
    (index_directory / METADATA_FILENAME).write_text(
        metadata.model_dump_json(),
        encoding="utf-8",
    )


def load_index(index_directory: Path) -> tuple[faiss.Index, PersistedIndex]:
    index_path = index_directory / INDEX_FILENAME
    metadata_path = index_directory / METADATA_FILENAME
    if not index_path.exists() or not metadata_path.exists():
        raise VectorStoreError(
            "Indice RAG nao encontrado. Execute o script de indexacao primeiro."
        )

    try:
        index = faiss.read_index(str(index_path))
        metadata = PersistedIndex.model_validate_json(metadata_path.read_text(encoding="utf-8"))
    except (RuntimeError, ValueError, json.JSONDecodeError) as error:
        raise VectorStoreError("Indice RAG invalido.") from error

    if index.ntotal != len(metadata.chunks):
        raise VectorStoreError("Indice e metadados RAG estao inconsistentes.")
    return index, metadata


def search_index(
    index: faiss.Index,
    chunks: list[DocumentChunk],
    query_embedding: list[float],
    top_k: int = 3,
) -> list[SearchResult]:
    if not query_embedding:
        raise VectorStoreError("Embedding da consulta esta vazio.")

    query = np.asarray([query_embedding], dtype="float32")
    if query.shape[1] != index.d:
        raise VectorStoreError("Dimensao do embedding da consulta nao corresponde ao indice.")

    faiss.normalize_L2(query)
    scores, indices = index.search(query, min(top_k, len(chunks)))
    results = []
    for score, index_position in zip(scores[0], indices[0], strict=True):
        if index_position < 0:
            continue
        chunk = chunks[index_position]
        results.append(
            SearchResult(
                id=chunk.id,
                source=chunk.source,
                text=chunk.text,
                page=chunk.page,
                score=float(score),
            )
        )
    return results

