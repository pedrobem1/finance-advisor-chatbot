from pathlib import Path

from pydantic import BaseModel
from pypdf import PdfReader


SKIPPED_MARKDOWN_FILENAMES = {"README.md", "sources.md"}


class SourceDocument(BaseModel):
    source: str
    text: str
    page: int | None = None


class DocumentChunk(BaseModel):
    id: str
    source: str
    text: str
    page: int | None = None


class DocumentLoadError(ValueError):
    """Raised when the knowledge base cannot be read."""


def load_source_documents(knowledge_directory: Path) -> list[SourceDocument]:
    if not knowledge_directory.exists():
        raise DocumentLoadError(
            f"Diretorio de conhecimento nao encontrado: {knowledge_directory}"
        )

    documents: list[SourceDocument] = []
    for path in sorted(knowledge_directory.rglob("*")):
        if not path.is_file():
            continue

        relative_path = str(path.relative_to(knowledge_directory))
        if path.suffix.lower() == ".md" and path.name not in SKIPPED_MARKDOWN_FILENAMES:
            text = path.read_text(encoding="utf-8").strip()
            if text:
                documents.append(SourceDocument(source=relative_path, text=text))
        elif path.suffix.lower() == ".pdf":
            documents.extend(_load_pdf(path, relative_path))

    if not documents:
        raise DocumentLoadError("Nenhum documento Markdown ou PDF com texto foi encontrado.")

    return documents


def _load_pdf(path: Path, relative_path: str) -> list[SourceDocument]:
    try:
        reader = PdfReader(path)
    except Exception as error:
        raise DocumentLoadError(f"Nao foi possivel ler o PDF {relative_path}.") from error

    documents = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            documents.append(
                SourceDocument(source=relative_path, text=text, page=page_number)
            )
    return documents


def chunk_documents(
    documents: list[SourceDocument],
    chunk_size: int = 1_200,
    overlap: int = 200,
) -> list[DocumentChunk]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size deve ser maior que overlap.")

    chunks: list[DocumentChunk] = []
    for document in documents:
        for index, text in enumerate(split_text(document.text, chunk_size, overlap)):
            chunks.append(
                DocumentChunk(
                    id=f"{document.source}:{document.page or 0}:{index}",
                    source=document.source,
                    text=text,
                    page=document.page,
                )
            )
    return chunks


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    normalized_text = " ".join(text.split())
    if not normalized_text:
        return []

    chunks = []
    start = 0
    while start < len(normalized_text):
        end = min(start + chunk_size, len(normalized_text))
        if end < len(normalized_text):
            boundary = normalized_text.rfind(" ", start, end)
            if boundary > start + (chunk_size // 2):
                end = boundary

        chunk = normalized_text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(normalized_text):
            break
        start = end - overlap

    return chunks
