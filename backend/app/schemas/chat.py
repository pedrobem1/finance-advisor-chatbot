from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.chart import ChartArtifact

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None


class ChatResponse(BaseModel):
    answer: str
    agent: str
    conversation_id: UUID
    tools_used: list[str] = Field(default_factory=list)
    charts: list[ChartArtifact] = Field(default_factory=list)
