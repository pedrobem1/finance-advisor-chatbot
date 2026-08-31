from pydantic import BaseModel, Field

from app.schemas.chart import ChartArtifact

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    agent: str
    tools_used: list[str] = Field(default_factory=list)
    charts: list[ChartArtifact] = Field(default_factory=list)
