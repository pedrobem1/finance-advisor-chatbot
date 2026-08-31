from typing import Any

from pydantic import BaseModel


class ChartArtifact(BaseModel):
    chart_type: str = "line"
    symbol: str
    period: str
    figure: dict[str, Any]
