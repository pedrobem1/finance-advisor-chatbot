from fastapi.testclient import TestClient

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
    async def fake_run_master_agent(message: str) -> str:
        return f"Resposta simulada para: {message}"

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
    }


def test_chat_rejects_empty_message() -> None:
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422
