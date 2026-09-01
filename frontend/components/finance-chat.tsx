"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Activity, ArrowUpRight, Bot, ChartNoAxesCombined, History, Plus, Send, Sparkles, X } from "lucide-react";

import { ConversationList } from "./conversation-list";
import { PriceChart } from "./price-chart";
import type { ChatApiErrorResponse, ChatApiResponse, ChatMessage, ConversationDetail, ConversationSummary } from "./types";

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

async function getApiErrorMessage(response: Response) {
  const fallback = "Nao foi possivel concluir sua pergunta agora. Tente novamente em instantes.";

  try {
    const payload = (await response.json()) as ChatApiErrorResponse;
    if (typeof payload.detail === "string") return payload.detail;
    return payload.detail?.message ?? fallback;
  } catch {
    return fallback;
  }
}

export function FinanceChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_MESSAGE]);
  const [message, setMessage] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isConversationPanelOpen, setIsConversationPanelOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    void refreshConversations();
  }, []);

  async function refreshConversations() {
    try {
      const response = await fetch(`${API_URL}/conversations`);
      if (!response.ok) throw new Error(await getApiErrorMessage(response));
      setConversations((await response.json()) as ConversationSummary[]);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Nao foi possivel carregar as conversas.");
    }
  }

  function startNewConversation() {
    setMessages([INITIAL_MESSAGE]);
    setConversationId(null);
    setError(null);
    setIsConversationPanelOpen(false);
    inputRef.current?.focus();
  }

  async function openConversation(id: string) {
    if (isLoading) return;

    try {
      const response = await fetch(`${API_URL}/conversations/${id}`);
      if (!response.ok) throw new Error(await getApiErrorMessage(response));
      const conversation = (await response.json()) as ConversationDetail;
      setMessages(conversation.messages);
      setConversationId(conversation.conversation_id);
      setError(null);
      setIsConversationPanelOpen(false);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Nao foi possivel abrir a conversa.");
    }
  }

  async function deleteConversation(id: string) {
    if (isLoading || !window.confirm("Excluir esta conversa?")) return;

    try {
      const response = await fetch(`${API_URL}/conversations/${id}`, { method: "DELETE" });
      if (!response.ok) throw new Error(await getApiErrorMessage(response));
      if (conversationId === id) startNewConversation();
      await refreshConversations();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Nao foi possivel excluir a conversa.");
    }
  }

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
        body: JSON.stringify({ message: question, conversation_id: conversationId })
      });
      if (!response.ok) throw new Error(await getApiErrorMessage(response));

      const result = (await response.json()) as ChatApiResponse;
      setConversationId(result.conversation_id);
      await refreshConversations();
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
    } catch (error) {
      setError(error instanceof Error ? error.message : "Nao foi possivel falar com a API. Confirme se o backend esta em execucao.");
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

        <button className="new-chat" type="button" title="Nova conversa" onClick={startNewConversation}>
          <Plus size={18} />
          <span>Nova conversa</span>
        </button>

        <div className="sidebar-section sidebar-section--conversations">
          <p className="sidebar-label">Conversas</p>
          <ConversationList activeConversationId={conversationId} conversations={conversations} disabled={isLoading} onOpen={(id) => void openConversation(id)} onDelete={(id) => void deleteConversation(id)} />
        </div>

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
          <div className="topbar-actions">
            <button className="mobile-history-toggle" type="button" title="Conversas" aria-label="Conversas" onClick={() => setIsConversationPanelOpen(true)}><History size={18} /></button>
            <div className="status"><span />Sistema ativo</div>
          </div>
        </header>

        {isConversationPanelOpen && (
          <section className="mobile-conversation-panel" aria-label="Conversas salvas">
            <div className="mobile-conversation-panel__header">
              <span>Conversas</span>
              <button type="button" title="Fechar conversas" aria-label="Fechar conversas" onClick={() => setIsConversationPanelOpen(false)}><X size={18} /></button>
            </div>
            <button className="new-chat mobile-new-chat" type="button" onClick={startNewConversation}>
              <Plus size={18} />
              <span>Nova conversa</span>
            </button>
            <ConversationList activeConversationId={conversationId} conversations={conversations} disabled={isLoading} onOpen={(id) => void openConversation(id)} onDelete={(id) => void deleteConversation(id)} />
          </section>
        )}

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
