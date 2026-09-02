from uuid import UUID

from agents import SQLiteSession

from app.core.config import get_settings


def create_conversation_session(conversation_id: UUID) -> SQLiteSession:
    settings = get_settings()
    if settings.conversation_store == "dynamodb":
        if not settings.dynamodb_conversations_table:
            raise RuntimeError("A tabela de conversas nao foi configurada.")
        from app.conversations.dynamodb import DynamoDBSession

        return DynamoDBSession(  # type: ignore[return-value]
            session_id=str(conversation_id),
            table_name=settings.dynamodb_conversations_table,
            history_limit=settings.conversation_history_limit,
        )
    settings.conversation_database_path.parent.mkdir(parents=True, exist_ok=True)
    return SQLiteSession(
        session_id=str(conversation_id),
        db_path=settings.conversation_database_path,
        session_settings={"limit": settings.conversation_history_limit},
    )
