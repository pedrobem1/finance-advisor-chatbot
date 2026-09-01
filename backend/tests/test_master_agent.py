import asyncio
from types import SimpleNamespace
from uuid import UUID

from agents import SQLiteSession
from app.agents import master_agent
from app.agents.master_agent import extract_tools_used


def test_extract_tools_used_preserves_unique_tool_order() -> None:
    run_result = SimpleNamespace(
        new_items=[
            SimpleNamespace(type="message_output_item"),
            SimpleNamespace(type="tool_call_item", tool_name="rag_specialist"),
            SimpleNamespace(type="tool_call_item", tool_name="rag_specialist"),
            SimpleNamespace(type="tool_call_item", tool_name="finance_specialist"),
        ]
    )

    assert extract_tools_used(run_result) == [
        "rag_specialist",
        "finance_specialist",
    ]


def test_run_master_agent_uses_sqlite_session(monkeypatch, tmp_path) -> None:
    captured_session = None

    async def fake_runner_run(agent, message, *, context, session):
        nonlocal captured_session
        captured_session = session
        return SimpleNamespace(final_output="Resposta", new_items=[])

    def fake_create_session(received_id: UUID) -> SQLiteSession:
        return SQLiteSession(
            session_id=str(received_id),
            db_path=tmp_path / "conversations.db",
            session_settings={"limit": 12},
        )

    monkeypatch.setattr(master_agent, "create_conversation_session", fake_create_session)
    monkeypatch.setattr(master_agent.Runner, "run", fake_runner_run)

    conversation_id = UUID("a2eb2b69-9a4b-4e76-9090-5936f73bc117")
    result = asyncio.run(master_agent.run_master_agent("Ola", conversation_id))

    assert result.answer == "Resposta"
    assert captured_session is not None
    assert captured_session.session_id == str(conversation_id)
    assert captured_session.db_path == tmp_path / "conversations.db"
    assert captured_session.session_settings.limit == 12
    assert captured_session._closed is True
