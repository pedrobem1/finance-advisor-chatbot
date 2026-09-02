from functools import lru_cache
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
PROJECT_DIRECTORY = BACKEND_DIRECTORY.parent


class Settings(BaseSettings):
    app_name: str = "MNC Finance Chatbot API"
    environment: str = "development"
    openai_api_key: str | None = None
    openai_api_key_parameter: str | None = None
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    rag_embedding_model: str = "text-embedding-3-small"
    rag_knowledge_directory: Path = PROJECT_DIRECTORY / "knowledge"
    rag_index_directory: Path = BACKEND_DIRECTORY / "data" / "rag"
    conversation_database_path: Path = BACKEND_DIRECTORY / "data" / "conversations.db"
    conversation_store: str = "sqlite"
    dynamodb_conversations_table: str | None = None
    conversation_history_limit: int = 40
    chat_rate_limit_requests: int = 10
    chat_rate_limit_window_seconds: int = 300

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_openai_api_key() -> str | None:
    settings = get_settings()
    if settings.openai_api_key:
        return settings.openai_api_key
    if not settings.openai_api_key_parameter:
        return None

    try:
        response = boto3.client("ssm").get_parameter(
            Name=settings.openai_api_key_parameter,
            WithDecryption=True,
        )
    except (BotoCoreError, ClientError):
        return None

    value = response.get("Parameter", {}).get("Value")
    return value if isinstance(value, str) and value else None
