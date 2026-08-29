# MNC Finance Chatbot

Chatbot financeiro com arquitetura baseada em agentes de IA, RAG, dados de mercado via `yfinance` e geracao de graficos.

## Objetivo

Criar uma interface moderna onde o usuario possa fazer perguntas sobre acoes, ETFs, FIIs, indices e conceitos de financas. O sistema deve buscar dados de mercado, explicar conceitos, gerar graficos e deixar claro quais fontes e ferramentas foram usadas.

Este projeto nao tem como objetivo fornecer recomendacao financeira personalizada. As respostas devem ser educacionais, informativas e acompanhadas de ressalvas quando necessario.

## Plano

O planejamento completo esta em [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md).

## Stack Inicial

- Backend: Python, FastAPI, OpenAI Agents SDK
- Dados de mercado: yfinance
- RAG: ChromaDB ou FAISS
- Analise de dados: pandas
- Graficos: Plotly
- Frontend: Next.js, TypeScript, Tailwind, shadcn/ui
- Deploy: Vercel para frontend e Render/Railway/Fly.io para backend

