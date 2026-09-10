"""Хелперы, которым нужны модели (вложения, спаны, разметка)"""

from typing import TYPE_CHECKING
from uuid import UUID

import pyromark
from lxml import html
from telegramify_markdown import convert, converter

from itd.core.utils import to_uuid
from itd.enums import AttachType, SpanType
from itd.models.file import File, PostAttach
from itd.models.span import Span

if TYPE_CHECKING:
    from itd.core.config import Config

converter.STANDARD_OPTIONS = pyromark.Options.ENABLE_STRIKETHROUGH  # ty: ignore[invalid-assignment]

ATTACHMENTS = File | UUID | str | list[File | UUID | str]


def format_attachments(attachments: ATTACHMENTS = []) -> list[UUID]:
    if isinstance(attachments, list):
        formatted = []
        for attachment in attachments:
            if isinstance(attachment, File):
                formatted.append(attachment.id)
            else:
                formatted.append(to_uuid(attachment))  # ty: ignore[invalid-argument-type]
        return formatted
    else:
        if isinstance(attachments, File):
            return [attachments.id]
        return [to_uuid(attachments)]


def calc_view_duration(config: 'Config', text: str, attachments: list[PostAttach] = []):
    text_reading = round(len(text.split()) / config.view_read_speed * 60_000)
    image_reading = sum([config.view_images_speed for attachment in attachments if attachment.type == AttachType.IMAGE])
    # video_watching = sum([attachment.duration for attachment in attachments if attachment.type == AttachType.VIDEO]) # TODO
    return max(config.dwell_min_duration, min(config.dwell_max_duration, text_reading + image_reading))


TAG_MAP = {
    'b': SpanType.BOLD,
    'i': SpanType.ITALIC,
    's': SpanType.STRIKE,
    'u': SpanType.UNDERLINE,
    'code': SpanType.MONOSPACE,
    'spoiler': SpanType.SPOILER,
    'q': SpanType.QUOTE,
    'a': SpanType.LINK
}


def parse_html(text: str) -> tuple[str, list[Span]]:
    """Спарсить HTML

    Поддерживаемые теги:
    - `<b>, <i>, <s>, <u>, <code>, <spoiler>, <q>`
    - `<a href="url">text</a>` или `<а>url</а>` (ссылки)

    Args:
        text (str): HTML-строка для парсинга

    Returns:
        str: чистая строка
        list[Span]: список спанов
    """
    if not text:
        return text, []

    root = html.document_fromstring(text)

    # https://stackoverflow.com/questions/67434754/extract-inline-nodes-from-html-string-with-offset-and-length
    spans = []
    for element in root.xpath('.//*'):
        if element.tag not in TAG_MAP:
            continue

        length = len(element.text_content())
        offset = len(''.join(element.xpath('./preceding::text()')))
        spans.append(Span(length=length, offset=offset, type=TAG_MAP[element.tag], url=None if element.tag != 'a' else element.get('href', element.text)))
    return root.text_content(), spans


def parse_md(text: str) -> tuple[str, list[Span]]:
    """Спарсить markdown

    Поддерживаемые теги:
    - *, _, **, __, ~, ~~, `, ||, \\[text](url)

    Args:
        text (str): строка для парсинга

    Returns:
        str: чистая строка
        list[Span]: список спанов
    """
    text, spans = convert(text, latex_escape=False)
    return text, [Span.model_validate(span, from_attributes=True) for span in spans]
