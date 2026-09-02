from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.chart import ChartArtifact
from app.schemas.source import WebSource


class ConversationMessage(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    tools: list[str] = Field(default_factory=list)
    charts: list[ChartArtifact] = Field(default_factory=list)
    sources: list[WebSource] = Field(default_factory=list)
    created_at: str


class ConversationSummary(BaseModel):
    conversation_id: UUID
    title: str
    created_at: str
    updated_at: str


class ConversationDetail(ConversationSummary):
    messages: list[ConversationMessage] = Field(default_factory=list)
