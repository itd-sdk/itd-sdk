from pydantic import BaseModel, field_validator

from itd.enums import SpanType


class Span(BaseModel):
    length: int
    offset: int
    type: SpanType
    url: str | None = None
    tag: str | None = None

    @field_validator('type', mode='before')
    @classmethod
    def validate_type(cls, type: str):
        if type == 'text_link':
            return 'link'
        if type == 'strikethrough':
            return 'strike'
        if type in ('code', 'pre'):
            return 'monospace'
        return type

    def _fix_utf16(self, content: str):
        self.length -= (len(content[self.offset : self.offset + self.length].encode('utf-16le')) // 2) - len(content[self.offset : self.offset + self.length])
        self.offset -= (len(content[: self.offset].encode('utf-16le')) // 2) - len(content[: self.offset])
