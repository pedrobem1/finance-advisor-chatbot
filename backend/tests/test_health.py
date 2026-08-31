from agents.exceptions import MaxTurnsExceeded, ModelTimeoutError
from fastapi.testclient import TestClient

from app.agents.master_agent import MasterAgentResponse
from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "environment": "development",
    }


def test_chat_returns_agent_answer(monkeypatch) -> None:
    async def fake_run_master_agent(message: str) -> MasterAgentResponse:
        return MasterAgentResponse(
            answer=f"Resposta simulada para: {message}",
            tools_used=["finance_specialist"],
            charts=[],
        )

    monkeypatch.setattr(
        "app.api.routes.chat.run_master_agent",
        fake_run_master_agent,
    )

    response = client.post(
        "/chat",
        json={"message": "O que e uma acao?"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Resposta simulada para: O que e uma acao?",
        "agent": "master_agent",
        "tools_used": ["finance_specialist"],
        "charts": [],
    }


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
    async def fake_run_master_agent(message: str) -> MasterAgentResponse:
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
    async def fake_run_master_agent(message: str) -> MasterAgentResponse:
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
