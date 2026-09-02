from dataclasses import dataclass, field

from app.schemas.chart import ChartArtifact
from app.schemas.source import WebSource


@dataclass
class ChatRunContext:
    charts: list[ChartArtifact] = field(default_factory=list)
    sources: list[WebSource] = field(default_factory=list)
