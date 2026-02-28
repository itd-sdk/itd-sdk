# новая версия от чат гпт. у меня самого не получилось сделать
import re
from itd.models.post import Span
from itd.enums import SpanType


class Tag:
    def __init__(self, open: str, close: str, type: SpanType, url: str | None = None):
        self.open = open
        self.close = close
        self.type = type
        self.url = url


def _parse_spans(text: str, tags: list[Tag]) -> tuple[str, list[Span]]:
    spans: list[Span] = []
    stack: list[tuple[int, SpanType, int, int]] = []
    clean_chars: list[str] = []
    i = 0

    while i < len(text):
        closed = False
        for idx, tag in enumerate(tags):
            if text.startswith(tag.close, i) and stack and stack[-1][0] == idx:
                _, span_type, offset, _ = stack.pop()
                spans.append(Span(length=len(clean_chars) - offset, offset=offset, type=span_type))
                i += len(tag.close)
                closed = True
                break
        if closed:
            continue

        opened = False
        for idx, tag in enumerate(tags):
            if text.startswith(tag.open, i):
                stack.append((idx, tag.type, len(clean_chars), i))
                i += len(tag.open)
                opened = True
                break
        if opened:
            continue

        clean_chars.append(text[i])
        i += 1

    if stack:
        _, last_type, _, raw_pos = stack[-1]
        raise ValueError(f'No closing tag for {last_type.value} at pos {raw_pos}')

    spans.sort(key=lambda span: span.offset)
    return ''.join(clean_chars), spans


def parse_html(text: str) -> tuple[str, list[Span]]:
    return _parse_spans(
        text,
        [
            Tag('<b>', '</b>', SpanType.BOLD),
            Tag('<i>', '</i>', SpanType.ITALIC),
            Tag('<s>', '</s>', SpanType.STRIKE),
            Tag('<u>', '</u>', SpanType.UNDERLINE),
            Tag('<code>', '</code>', SpanType.MONOSPACE),
            Tag('<spoiler>', '</spoiler>', SpanType.SPOILER),
        ],
    )


# версия от человека (не работает с вложенными тэгами)
# from re import finditer, Match

# from itd.models.post import Span
# from itd.enums import SpanType


# class Tag:
#     def __init__(self, open: str, close: str, type: SpanType):
#         self.open = open
#         self.close = close
#         self.type = type

#     def raise_error(self, pos: int):
#         raise ValueError(f'No closing tag for {self.type.value} at pos {pos - len(self.open)}')

#     def to_span(self, start: int, end: int) -> Span:
#         return Span(length=end - (start - len(self.open)), offset=start - len(self.open), type=self.type)

#     def get_pos(self, match: Match[str], text: str, offset: int) -> tuple[int, int, str]:
#         start = match.end() - offset
#         text = text[:match.start() - offset] + text[start:]
#         end = text.find(self.close, start)
#         if end == -1:
#             self.raise_error(start)

#         return start - len(self.open), end, text[:end] + text[end + len(self.close):]


# def parse_html(text: str) -> tuple[str, list[Span]]:
#     spans = []

#     for tag in [
#         Tag('<b>', '</b>', SpanType.BOLD),
#         Tag('<i>', '</i>', SpanType.ITALIC),
#         Tag('<s>', '</s>', SpanType.STRIKE),
#         Tag('<u>', '</u>', SpanType.UNDERLINE),
#         Tag('<code>', '</code>', SpanType.MONOSPACE),
#         Tag('<spoiler>', '</spoiler>', SpanType.SPOILER),
#     ]:

#         offset = 0
#         full_text = text
#         for match in finditer(tag.open, full_text):
#             start, end, text = tag.get_pos(match, text, offset)
#             spans.append(tag.to_span(start, end))
#             offset += len(tag.open) + len(tag.close)

#     return text, spans
