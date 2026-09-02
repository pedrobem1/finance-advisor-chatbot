import sqlite3
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.routes import conversations as conversation_routes
from app.conversations.repository import ConversationStore
from app.main import app
from app.schemas.source import WebSource


CLIENT_ID = UUID("054b7140-516a-456c-a5f6-3cc2f2a0a9a5")
OTHER_CLIENT_ID = UUID("a4e6aa9e-bf42-48f8-930d-8d94a6f38814")
client = TestClient(app, headers={"X-Client-Id": str(CLIENT_ID)})


def test_conversation_store_migrates_existing_database_for_sources(tmp_path) -> None:
    database_path = tmp_path / "conversations.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tools_json TEXT NOT NULL,
                charts_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    store = ConversationStore(database_path)
    store.list_conversations(CLIENT_ID)

    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(conversation_messages)")
        }

    assert "sources_json" in columns


def test_conversation_store_saves_and_loads_exchanges(tmp_path) -> None:
    store = ConversationStore(tmp_path / "conversations.db")
    conversation_id = UUID("a2eb2b69-9a4b-4e76-9090-5936f73bc117")

    store.save_exchange(
        client_id=CLIENT_ID,
        conversation_id=conversation_id,
        user_message="Explique o P/L da PETR4",
        answer="P/L compara preco e lucro.",
        tools_used=["finance_specialist"],
        charts=[],
        sources=[WebSource(url="https://b3.com.br/noticia", domain="b3.com.br")],
    )

    summaries = store.list_conversations(CLIENT_ID)
    detail = store.get_conversation(CLIENT_ID, conversation_id)

    assert summaries[0].conversation_id == conversation_id
    assert summaries[0].title == "Explique o P/L da PETR4"
    assert detail is not None
    assert [message.role for message in detail.messages] == ["user", "assistant"]
    assert detail.messages[1].tools == ["finance_specialist"]
    assert detail.messages[1].sources[0].domain == "b3.com.br"
    assert store.list_conversations(OTHER_CLIENT_ID) == []
    assert store.get_conversation(OTHER_CLIENT_ID, conversation_id) is None


def test_conversation_routes_list_open_and_delete(monkeypatch, tmp_path) -> None:
    store = ConversationStore(tmp_path / "conversations.db")
    conversation_id = UUID("a2eb2b69-9a4b-4e76-9090-5936f73bc117")
    store.save_exchange(
        client_id=CLIENT_ID,
        conversation_id=conversation_id,
        user_message="Fale sobre ETFs",
        answer="ETFs sao fundos negociados em bolsa.",
        tools_used=[],
        charts=[],
        sources=[],
    )

    class FakeSession:
        cleared = False
        closed = False

        async def clear_session(self) -> None:
            self.cleared = True

        def close(self) -> None:
            self.closed = True

    session = FakeSession()
    monkeypatch.setattr(conversation_routes, "get_conversation_store", lambda: store)
    monkeypatch.setattr(conversation_routes, "create_conversation_session", lambda _: session)

    list_response = client.get("/conversations")
    detail_response = client.get(f"/conversations/{conversation_id}")
    delete_response = client.delete(f"/conversations/{conversation_id}")

    assert list_response.status_code == 200
    assert list_response.json()[0]["conversation_id"] == str(conversation_id)
    assert detail_response.status_code == 200
    assert detail_response.json()["messages"][0]["content"] == "Fale sobre ETFs"
    assert delete_response.status_code == 204
    assert session.cleared is True
    assert session.closed is True
    assert store.get_conversation(CLIENT_ID, conversation_id) is None
