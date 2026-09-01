from uuid import UUID

from agents import GuardrailFunctionOutput, InputGuardrailResult
from agents.exceptions import InputGuardrailTripwireTriggered, MaxTurnsExceeded, ModelTimeoutError
from fastapi.testclient import TestClient

from app.agents.master_agent import MasterAgentResponse
from app.main import app


client = TestClient(app)


class FakeConversationStore:
    def __init__(self) -> None:
        self.exchanges: list[dict] = []

    def save_exchange(self, **exchange) -> None:
        self.exchanges.append(exchange)


def mock_openai_key(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.chat.get_settings",
        lambda: type("Settings", (), {"openai_api_key": "test-key"})(),
    )


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "environment": "development",
    }


def test_chat_returns_agent_answer(monkeypatch) -> None:
    captured_conversation_ids: list[UUID] = []
    store = FakeConversationStore()
    mock_openai_key(monkeypatch)

    async def fake_run_master_agent(message: str, conversation_id: UUID) -> MasterAgentResponse:
        captured_conversation_ids.append(conversation_id)
        return MasterAgentResponse(
            answer=f"Resposta simulada para: {message}",
            suggested_questions=["Pergunta um", "Pergunta dois", "Pergunta tres"],
            tools_used=["finance_specialist"],
            charts=[],
        )

    monkeypatch.setattr(
        "app.api.routes.chat.run_master_agent",
        fake_run_master_agent,
    )
    monkeypatch.setattr("app.api.routes.chat.get_conversation_store", lambda: store)

    response = client.post(
        "/chat",
        json={"message": "O que e uma acao?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "answer": "Resposta simulada para: O que e uma acao?",
        "agent": "master_agent",
        "conversation_id": str(captured_conversation_ids[0]),
        "suggested_questions": ["Pergunta um", "Pergunta dois", "Pergunta tres"],
        "tools_used": ["finance_specialist"],
        "charts": [],
    }
    assert store.exchanges[0]["user_message"] == "O que e uma acao?"


def test_chat_reuses_conversation_id(monkeypatch) -> None:
    conversation_id = UUID("a2eb2b69-9a4b-4e76-9090-5936f73bc117")
    captured_conversation_ids: list[UUID] = []
    store = FakeConversationStore()
    mock_openai_key(monkeypatch)

    async def fake_run_master_agent(message: str, received_id: UUID) -> MasterAgentResponse:
        captured_conversation_ids.append(received_id)
        return MasterAgentResponse(
            answer="Resposta simulada",
            suggested_questions=["Pergunta um", "Pergunta dois", "Pergunta tres"],
            tools_used=[],
            charts=[],
        )

    monkeypatch.setattr(
        "app.api.routes.chat.run_master_agent",
        fake_run_master_agent,
    )
    monkeypatch.setattr("app.api.routes.chat.get_conversation_store", lambda: store)

    response = client.post(
        "/chat",
        json={"message": "Compare com a VALE3", "conversation_id": str(conversation_id)},
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == str(conversation_id)
    assert captured_conversation_ids == [conversation_id]


def test_chat_rejects_empty_message() -> None:
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_returns_friendly_configuration_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.chat.get_settings",
        lambda: type("Settings", (), {"openai_api_key": None})(),
    )

    response = client.post("/chat", json={"message": "O que e uma acao?"})

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "code": "ai_configuration_error",
            "message": "O servico de IA nao esta configurado corretamente.",
        }
    }


def test_chat_returns_friendly_timeout_error(monkeypatch) -> None:
    mock_openai_key(monkeypatch)

    async def fake_run_master_agent(message: str, conversation_id: UUID) -> MasterAgentResponse:
        raise ModelTimeoutError(30)

    monkeypatch.setattr(
        "app.api.routes.chat.run_master_agent",
        fake_run_master_agent,
    )

    response = client.post("/chat", json={"message": "Analise PETR4"})

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "code": "ai_unavailable",
            "message": "O servico de IA esta indisponivel no momento. Tente novamente em instantes.",
        }
    }


def test_chat_returns_friendly_agent_limit_error(monkeypatch) -> None:
    mock_openai_key(monkeypatch)

    async def fake_run_master_agent(message: str, conversation_id: UUID) -> MasterAgentResponse:
        raise MaxTurnsExceeded("limit reached")

    monkeypatch.setattr(
        "app.api.routes.chat.run_master_agent",
        fake_run_master_agent,
    )

    response = client.post("/chat", json={"message": "Analise detalhada"})

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "code": "agent_limit_reached",
            "message": "Nao consegui concluir essa analise agora. Tente reformular a pergunta.",
        }
    }


def test_chat_returns_scope_error(monkeypatch) -> None:
    mock_openai_key(monkeypatch)

    async def fake_run_master_agent(message: str, conversation_id: UUID) -> MasterAgentResponse:
        from app.agents.scope_guardrail import finance_scope_guardrail

        raise InputGuardrailTripwireTriggered(
            InputGuardrailResult(
                guardrail=finance_scope_guardrail,
                output=GuardrailFunctionOutput(output_info=None, tripwire_triggered=True),
            )
        )

    monkeypatch.setattr("app.api.routes.chat.run_master_agent", fake_run_master_agent)

    response = client.post("/chat", json={"message": "Gere um codigo DFS em Python"})

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "code": "out_of_scope",
            "message": "Posso ajudar com finanças, investimentos, mercado e economia.",
        }
    }
