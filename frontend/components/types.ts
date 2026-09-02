export type ChartArtifact = {
  chart_type: string;
  symbol: string;
  period: string;
  figure: {
    data: Record<string, unknown>[];
    layout: Record<string, unknown>;
  };
};

export type WebSource = {
  url: string;
  domain: string;
};

export type ChatApiResponse = {
  answer: string;
  agent: string;
  conversation_id: string;
  suggested_questions: string[];
  tools_used: string[];
  charts: ChartArtifact[];
  sources: WebSource[];
};

export type ChatApiErrorResponse = {
  detail?: {
    code?: string;
    message?: string;
  } | string;
};

export type ConversationSummary = {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ConversationDetail = ConversationSummary & {
  messages: ChatMessage[];
};

export type ChatMessage = {
  id: string;
  role: "assistant" | "user";
  content: string;
  created_at?: string;
  tools?: string[];
  charts?: ChartArtifact[];
  sources?: WebSource[];
};
