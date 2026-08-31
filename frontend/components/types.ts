export type ChartArtifact = {
  chart_type: string;
  symbol: string;
  period: string;
  figure: {
    data: Record<string, unknown>[];
    layout: Record<string, unknown>;
  };
};

export type ChatApiResponse = {
  answer: string;
  agent: string;
  tools_used: string[];
  charts: ChartArtifact[];
};

export type ChatMessage = {
  id: string;
  role: "assistant" | "user";
  content: string;
  tools?: string[];
  charts?: ChartArtifact[];
};
