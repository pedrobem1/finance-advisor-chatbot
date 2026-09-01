from uuid import UUID

from agents import SQLiteSession

from app.core.config import get_settings


def create_conversation_session(conversation_id: UUID) -> SQLiteSession:
    settings = get_settings()
    settings.conversation_database_path.parent.mkdir(parents=True, exist_ok=True)
    return SQLiteSession(
        session_id=str(conversation_id),
        db_path=settings.conversation_database_path,
        session_settings={"limit": settings.conversation_history_limit},
    )
