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

No deploy Lambda, o indice gerado em `data/rag/` e empacotado na imagem. Por isso,
reindexe a base antes de cada build que contenha documentos novos.

## Base do deploy AWS Lambda

O backend sera empacotado como imagem Lambda pelo AWS SAM. A fundacao do deploy
fica no arquivo `../template.yaml` e usa `Dockerfile` neste diretorio.

Antes do primeiro build, gere as dependencias da imagem a partir do lockfile:

```bash
uv export --locked --no-dev --no-emit-project --format requirements.txt -o requirements-lambda.txt
```
