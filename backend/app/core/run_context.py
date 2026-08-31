from dataclasses import dataclass, field

from app.schemas.chart import ChartArtifact


@dataclass
class ChatRunContext:
    charts: list[ChartArtifact] = field(default_factory=list)
