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


def test_chat_returns_placeholder_answer() -> None:
    response = client.post(
        "/chat",
        json={"message": "O que e uma acao?"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Recebi sua pergunta: O que e uma acao?",
        "agent": "placeholder",
    }


def test_chat_rejects_empty_message() -> None:
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422
