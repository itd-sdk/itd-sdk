from pydantic import BaseModel

from itd.enums import SpanType


class Span(BaseModel):
    length: int
    offset: int
    type: SpanType
    url: str | None = None
