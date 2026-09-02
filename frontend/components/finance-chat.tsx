"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Activity, ArrowUpRight, Bot, ChartNoAxesCombined, History, Info, Plus, Send, Sparkles, X } from "lucide-react";

import { ConversationList } from "./conversation-list";
import { PriceChart } from "./price-chart";
import type { ChatApiErrorResponse, ChatApiResponse, ChatMessage, ConversationDetail, ConversationSummary } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const EXAMPLE_PROMPTS = [
  "Explique o que é um ETF",
  "Qual o preço atual da PETR4?",
  "Gere um gráfico da PETR4 nos últimos 3 meses"
];

const INITIAL_MESSAGE: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content: "O que você quer analisar hoje?"
};

const SPECIALISTS = [
  { name: "Mercado", dot: "agent-dot--green", description: "Consulta cotações, indicadores e dividendos de ativos." },
  { name: "Conhecimento", dot: "agent-dot--cyan", description: "Busca conceitos financeiros nos documentos indexados." },
  { name: "Gráficos", dot: "agent-dot--amber", description: "Gera históricos e comparações visuais de preços." },
  {
    name: "Pesquisa web",
    dot: "agent-dot--blue",
    description: "Pesquisa notícias e eventos recentes com fontes.",
    notice: "A pesquisa web pode levar alguns instantes."
  }
];

const TOOL_METADATA: Record<string, { label: string; tone: string }> = {
  finance_specialist: { label: "Mercado", tone: "green" },
  rag_specialist: { label: "Conhecimento", tone: "cyan" },
  chart_specialist: { label: "Gráfico", tone: "amber" },
  web_research_specialist: { label: "Pesquisa web", tone: "blue" }
};

function normalizeMarkdown(content: string) {
  return content.replace(/\\([*_])/g, "$1");
}

function labelForTool(tool: string) {
  return TOOL_METADATA[tool]?.label ?? tool;
}

function toolBadgeClass(tool: string) {
  return `tool-badge tool-badge--${TOOL_METADATA[tool]?.tone ?? "default"}`;
}

async function getApiErrorMessage(response: Response) {
  const fallback = "Não foi possível concluir sua pergunta agora. Tente novamente em instantes.";

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
  const [suggestedQuestions, setSuggestedQuestions] = useState(EXAMPLE_PROMPTS);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isConversationPanelOpen, setIsConversationPanelOpen] = useState(false);
  const [isInfoOpen, setIsInfoOpen] = useState(false);
  const [isWebResearchNoticeOpen, setIsWebResearchNoticeOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const chatStreamRef = useRef<HTMLElement>(null);

  useEffect(() => {
    void refreshConversations();
  }, []);

  useEffect(() => {
    const stream = chatStreamRef.current;
    if (stream) stream.scrollTo({ top: stream.scrollHeight, behavior: "smooth" });
  }, [messages, isLoading]);

  async function refreshConversations() {
    try {
      const response = await fetch(`${API_URL}/conversations`);
      if (!response.ok) throw new Error(await getApiErrorMessage(response));
      setConversations((await response.json()) as ConversationSummary[]);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível carregar as conversas.");
    }
  }

  function startNewConversation() {
    setMessages([INITIAL_MESSAGE]);
    setConversationId(null);
    setSuggestedQuestions(EXAMPLE_PROMPTS);
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
      setSuggestedQuestions(EXAMPLE_PROMPTS);
      setError(null);
      setIsConversationPanelOpen(false);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível abrir a conversa.");
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
      setError(error instanceof Error ? error.message : "Não foi possível excluir a conversa.");
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
      setSuggestedQuestions(result.suggested_questions);
      await refreshConversations();
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.answer,
          tools: result.tools_used,
          charts: result.charts,
          sources: result.sources
        }
      ]);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível falar com a API. Confirme se o backend está em execução.");
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
          <div className="brand-mark"><Bot size={18} /></div>
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
          <p className="sidebar-label">Como o MNC responde</p>
          <p className="sidebar-context">O agente mestre aciona especialistas automaticamente.</p>
          <div className="agent-list">
            {SPECIALISTS.map((specialist) => (
              <div className="agent-item" key={specialist.name}>
                <span className="agent-item__name">
                  <i className={`agent-dot ${specialist.dot}`} />
                  {specialist.name}
                  {specialist.notice && (
                    <button
                      className="agent-item__info"
                      type="button"
                      aria-expanded={isWebResearchNoticeOpen}
                      aria-label="Sobre a pesquisa web"
                      title="Sobre a pesquisa web"
                      onClick={() => setIsWebResearchNoticeOpen((isOpen) => !isOpen)}
                    ><Info size={13} /></button>
                  )}
                </span>
                <p>{specialist.description}</p>
                {specialist.notice && isWebResearchNoticeOpen && <p className="agent-item__notice">{specialist.notice}</p>}
              </div>
            ))}
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
            <p className="eyebrow">ANÁLISE FINANCEIRA</p>
            <h1>Conversa com o mercado</h1>
          </div>
          <div className="topbar-actions">
            <button className="info-toggle" type="button" title="Sobre o chatbot" aria-label="Sobre o chatbot" onClick={() => setIsInfoOpen(true)}><Info size={18} /></button>
            <button className="mobile-history-toggle" type="button" title="Conversas" aria-label="Conversas" onClick={() => setIsConversationPanelOpen(true)}><History size={18} /></button>
          </div>
        </header>

        {isInfoOpen && (
          <section className="info-modal" role="dialog" aria-modal="true" aria-labelledby="info-title">
            <div className="info-modal__content">
              <div className="info-modal__header">
                <h2 id="info-title">Sobre o MNC Finance</h2>
                <button type="button" title="Fechar informações" aria-label="Fechar informações" onClick={() => setIsInfoOpen(false)}><X size={18} /></button>
              </div>
              <p>O agente mestre coordena especialistas para responder perguntas financeiras.</p>
              <dl>
                <div><dt>Mercado</dt><dd>Cotações, indicadores e dividendos via yfinance.</dd></div>
                <div><dt>Conhecimento</dt><dd>Conceitos recuperados da base local de documentos.</dd></div>
                <div><dt>Gráficos</dt><dd>Históricos e comparações de preços em Plotly.</dd></div>
                <div><dt>Pesquisa web</dt><dd>Notícias e eventos financeiros com fontes verificáveis.</dd></div>
              </dl>
              <p className="info-modal__scope">Este chat aceita apenas dúvidas sobre finanças, investimentos, mercado e economia.</p>
              <p className="info-modal__notice">Conteúdo educacional. Não constitui recomendação de investimento.</p>
            </div>
          </section>
        )}

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

        <section className="chat-stream" aria-live="polite" ref={chatStreamRef}>
          {messages.map((item) => (
            <article className={`message message--${item.role}`} key={item.id}>
              <div className="message-avatar">
                {item.role === "assistant" ? <Bot size={18} /> : <ArrowUpRight size={18} />}
              </div>
              <div className="message-body">
                <div className="message-role">{item.role === "assistant" ? "MNC Finance" : "Você"}</div>
                {item.role === "assistant" ? (
                  <div className="markdown"><ReactMarkdown>{normalizeMarkdown(item.content)}</ReactMarkdown></div>
                ) : (
                  <p>{item.content}</p>
                )}
                {item.tools && item.tools.length > 0 && (
                  <div className="tool-list">
                    {item.tools.map((tool) => <span className={toolBadgeClass(tool)} key={tool}>{labelForTool(tool)}</span>)}
                  </div>
                )}
                {item.charts?.map((chart, index) => <PriceChart chart={chart} key={`${chart.symbol}-${index}`} />)}
                {item.sources && item.sources.length > 0 && (
                  <div className="source-list" aria-label="Fontes da pesquisa">
                    <span>Fontes</span>
                    {item.sources.map((source) => (
                      <a href={source.url} key={source.url} rel="noreferrer" target="_blank">{source.domain}</a>
                    ))}
                  </div>
                )}
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
            {suggestedQuestions.map((prompt) => (
              <button type="button" key={prompt} onClick={() => void submitMessage(prompt)}>{prompt}</button>
            ))}
          </div>
          <form className="composer" onSubmit={onSubmit}>
            <textarea
              ref={inputRef}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Pergunte sobre ações, indicadores ou mercado..."
              rows={1}
              aria-label="Mensagem"
            />
            <button className="send-button" type="submit" disabled={!message.trim() || isLoading} title="Enviar mensagem">
              <Send size={18} />
            </button>
          </form>
          <p className="disclaimer"><ChartNoAxesCombined size={14} />Conteúdo educacional. Não constitui recomendação de investimento. O MNC Finance pode cometer erros.</p>
        </div>
      </section>
    </main>
  );
}
