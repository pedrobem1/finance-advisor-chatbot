from pydantic import BaseModel


class WebSource(BaseModel):
    url: str
    domain: str
