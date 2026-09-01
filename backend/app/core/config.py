from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
PROJECT_DIRECTORY = BACKEND_DIRECTORY.parent


class Settings(BaseSettings):
    app_name: str = "MNC Finance Chatbot API"
    environment: str = "development"
    openai_api_key: str | None = None
    rag_embedding_model: str = "text-embedding-3-small"
    rag_knowledge_directory: Path = PROJECT_DIRECTORY / "knowledge"
    rag_index_directory: Path = BACKEND_DIRECTORY / "data" / "rag"
    conversation_database_path: Path = BACKEND_DIRECTORY / "data" / "conversations.db"
    conversation_history_limit: int = 40

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
