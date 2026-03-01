# Писал ии, у меня у самого не получилось. Мой код можете найти в комите cd27baa8d65b36cfb1d030bc5a578ac6efb45445 в комментарии
from html.parser import HTMLParser

from itd.models.post import Span
from itd.enums import SpanType


class HTMLSpanParser(HTMLParser):
    """Парсер HTML для извлечения текста и spans с форматированием."""

    TAG_MAP = {
        'b': SpanType.BOLD,
        'i': SpanType.ITALIC,
        's': SpanType.STRIKE,
        'u': SpanType.UNDERLINE,
        'code': SpanType.MONOSPACE,
        'spoiler': SpanType.SPOILER,
        'q': SpanType.QUOTE,
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.spans: list[Span] = []
        self.text_parts: list[str] = []
        self.stack: list[tuple[str, SpanType, int, str | None]] = []  # (tag, type, text_offset, url)
        self.text_offset = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag == 'a':
            href = None
            for attr_name, attr_value in attrs:
                if attr_name == 'href' and attr_value:
                    href = attr_value
                    break
            if href:
                self.stack.append(('a', SpanType.LINK, self.text_offset, href))
                return
        elif tag in self.TAG_MAP:
            self.stack.append((tag, self.TAG_MAP[tag], self.text_offset, None))

    def handle_endtag(self, tag: str):
        # Ищем соответствующий открывающий тег в стеке
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                _, span_type, text_start, url = self.stack.pop(i)
                self.spans.append(Span(
                    length=self.text_offset - text_start,
                    offset=text_start,
                    type=span_type,
                    url=url
                ))
                break

    def handle_data(self, data: str):
        self.text_parts.append(data)
        self.text_offset += len(data)

    def get_text(self) -> str:
        return ''.join(self.text_parts)

    def get_spans(self) -> list[Span]:
        self.spans.sort(key=lambda s: s.offset)
        return self.spans


def parse_html(text: str) -> tuple[str, list[Span]]:
    """
    Парсит HTML-текст, извлекает чистый текст и spans с форматированием.

    Поддерживаемые теги:
    - <b>, <i>, <s>, <u>, <code>, <spoiler>, <q>
    - <a href="..."> (ссылки)

    Args:
        text: HTML-строка для парсинга

    Returns:
        str: чистая строка
        list[Span]: список спанов
    """
    parser = HTMLSpanParser()
    parser.feed(text)
    return parser.get_text(), parser.get_spans()
