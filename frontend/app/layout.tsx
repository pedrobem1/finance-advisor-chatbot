import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "MNC Finance",
  description: "Chatbot financeiro orientado por agentes"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
