"use client";

import { FormEvent, KeyboardEvent, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Activity, ArrowUpRight, Bot, ChartNoAxesCombined, Plus, Send, Sparkles } from "lucide-react";

import { PriceChart } from "./price-chart";
import type { ChatApiResponse, ChatMessage } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const EXAMPLE_PROMPTS = [
  "Explique o que e um ETF",
  "Qual o preco atual da PETR4?",
  "Gere um grafico da PETR4 nos ultimos 3 meses"
];

const INITIAL_MESSAGE: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content: "O que voce quer analisar hoje?"
};

function normalizeMarkdown(content: string) {
  return content.replace(/\\([*_])/g, "$1");
}

function labelForTool(tool: string) {
  const labels: Record<string, string> = {
    finance_specialist: "Mercado",
    rag_specialist: "Conhecimento",
    chart_specialist: "Grafico"
  };
  return labels[tool] ?? tool;
}

export function FinanceChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_MESSAGE]);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  async function submitMessage(content = message) {
    const question = content.trim();
    if (!question || isLoading) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question
    };
    setMessages((current) => [...current, userMessage]);
    setMessage("");
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question })
      });
      if (!response.ok) throw new Error("A API nao respondeu como esperado.");

      const result = (await response.json()) as ChatApiResponse;
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.answer,
          tools: result.tools_used,
          charts: result.charts
        }
      ]);
    } catch {
      setError("Nao foi possivel falar com a API. Confirme se o backend esta em execucao.");
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitMessage();
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submitMessage();
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Activity size={18} /></div>
          <span>MNC Finance</span>
        </div>

        <button className="new-chat" type="button" title="Nova conversa" onClick={() => setMessages([INITIAL_MESSAGE])}>
          <Plus size={18} />
          <span>Nova conversa</span>
        </button>

        <div className="sidebar-section">
          <p className="sidebar-label">Especialistas</p>
          <div className="agent-list">
            <div><span className="agent-dot agent-dot--green" />Mercado</div>
            <div><span className="agent-dot agent-dot--cyan" />Conhecimento</div>
            <div><span className="agent-dot agent-dot--amber" />Graficos</div>
          </div>
        </div>

        <div className="sidebar-footer">
          <Sparkles size={15} />
          <span>Respostas educacionais</span>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">ANALISE FINANCEIRA</p>
            <h1>Conversa com o mercado</h1>
          </div>
          <div className="status"><span />Sistema ativo</div>
        </header>

        <section className="chat-stream" aria-live="polite">
          {messages.map((item) => (
            <article className={`message message--${item.role}`} key={item.id}>
              <div className="message-avatar">
                {item.role === "assistant" ? <Bot size={18} /> : <ArrowUpRight size={18} />}
              </div>
              <div className="message-body">
                <div className="message-role">{item.role === "assistant" ? "MNC Finance" : "Voce"}</div>
                {item.role === "assistant" ? (
                  <div className="markdown"><ReactMarkdown>{normalizeMarkdown(item.content)}</ReactMarkdown></div>
                ) : (
                  <p>{item.content}</p>
                )}
                {item.tools && item.tools.length > 0 && (
                  <div className="tool-list">
                    {item.tools.map((tool) => <span className="tool-badge" key={tool}>{labelForTool(tool)}</span>)}
                  </div>
                )}
                {item.charts?.map((chart, index) => <PriceChart chart={chart} key={`${chart.symbol}-${index}`} />)}
              </div>
            </article>
          ))}
          {isLoading && (
            <article className="message message--assistant">
              <div className="message-avatar"><Bot size={18} /></div>
              <div className="loading-copy"><span /><span /><span /></div>
            </article>
          )}
        </section>

        <div className="composer-wrap">
          {error && <p className="error-message">{error}</p>}
          <div className="examples" aria-label="Perguntas sugeridas">
            {EXAMPLE_PROMPTS.map((prompt) => (
              <button type="button" key={prompt} onClick={() => void submitMessage(prompt)}>{prompt}</button>
            ))}
          </div>
          <form className="composer" onSubmit={onSubmit}>
            <textarea
              ref={inputRef}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Pergunte sobre acoes, indicadores ou mercado..."
              rows={1}
              aria-label="Mensagem"
            />
            <button className="send-button" type="submit" disabled={!message.trim() || isLoading} title="Enviar mensagem">
              <Send size={18} />
            </button>
          </form>
          <p className="disclaimer"><ChartNoAxesCombined size={14} />Conteudo educacional. Nao constitui recomendacao de investimento.</p>
        </div>
      </section>
    </main>
  );
}
