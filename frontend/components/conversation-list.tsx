import { MessageSquare, Trash2 } from "lucide-react";

import type { ConversationSummary } from "./types";

type ConversationListProps = {
  activeConversationId: string | null;
  conversations: ConversationSummary[];
  disabled?: boolean;
  onDelete: (conversationId: string) => void;
  onOpen: (conversationId: string) => void;
};

export function ConversationList({
  activeConversationId,
  conversations,
  disabled = false,
  onDelete,
  onOpen
}: ConversationListProps) {
  if (conversations.length === 0) {
    return <p className="empty-conversations">Nenhuma conversa salva</p>;
  }

  return (
    <div className="conversation-list">
      {conversations.map((conversation) => (
        <div className={`conversation-row ${conversation.conversation_id === activeConversationId ? "conversation-row--active" : ""}`} key={conversation.conversation_id}>
          <button className="conversation-open" type="button" onClick={() => onOpen(conversation.conversation_id)} disabled={disabled}>
            <MessageSquare size={14} />
            <span>{conversation.title}</span>
          </button>
          <button className="conversation-delete" type="button" title="Excluir conversa" aria-label={`Excluir conversa: ${conversation.title}`} onClick={() => onDelete(conversation.conversation_id)} disabled={disabled}>
            <Trash2 size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}
