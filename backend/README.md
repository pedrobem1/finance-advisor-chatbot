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

## Criar o indice RAG

Depois de adicionar ou alterar documentos em `../knowledge/`, execute:

```bash
uv run python -m scripts.build_rag_index
```
