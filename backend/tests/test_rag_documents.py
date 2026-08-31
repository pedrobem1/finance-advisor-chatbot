from app.rag import documents


def test_loads_markdown_and_pdf_documents(tmp_path, monkeypatch) -> None:
    (tmp_path / "conceito.md").write_text("Conteudo de acao.", encoding="utf-8")
    (tmp_path / "livro.pdf").write_bytes(b"pdf")

    class FakePage:
        def extract_text(self) -> str:
            return "Conteudo do PDF."

    class FakeReader:
        pages = [FakePage()]

    monkeypatch.setattr(documents, "PdfReader", lambda path: FakeReader())

    result = documents.load_source_documents(tmp_path)

    assert [(document.source, document.page) for document in result] == [
        ("conceito.md", None),
        ("livro.pdf", 1),
    ]


def test_chunks_documents_with_overlap() -> None:
    source = documents.SourceDocument(source="acoes.md", text="palavra " * 80)

    chunks = documents.chunk_documents([source], chunk_size=100, overlap=20)

    assert len(chunks) > 1
    assert chunks[0].source == "acoes.md"
    assert chunks[0].id == "acoes.md:0:0"
    assert chunks[1].text.split()[0] in chunks[0].text

