# MNC Finance Chatbot Backend

API do chatbot financeiro, construída com FastAPI.

## Executar localmente

Com `uv` instalado:

```bash
uv sync --dev
uv run fastapi dev app/main.py
```

A API ficará disponível em `http://127.0.0.1:8000`.

## Verificar saúde da API

```bash
curl http://127.0.0.1:8000/health
```

## Executar testes

```bash
uv run pytest
```

