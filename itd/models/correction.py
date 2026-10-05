"""Тетрадка, корректор (замазка) и красная ручка в постах

Корректор и красная ручка временные: дежурный замазывает или исправляет текст чужого поста,
и правка видна до `ends_at`. Сайт показывает только еще не истекшие правки, для этого есть свойства `active_*`.
"""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field, model_validator

from itd.core.utils import parse_datetime
from itd.enums import NotebookStyle

_Datetime = Annotated[datetime, BeforeValidator(parse_datetime)]


def _is_alive(ends_at: datetime | None) -> bool:
    return ends_at is None or ends_at > datetime.now(timezone.utc)


class Notebook(BaseModel):
    """Оформление поста как страницы тетради (покупается в магазине)"""

    style: NotebookStyle


class EventActor(BaseModel):
    """Пользователь, который применил корректор или красную ручку"""

    id: UUID | str
    username: str | None = None
    display_name: str | None = Field(None, alias='displayName')

    def __str__(self) -> str:
        return f'@{self.username}' if self.username else self.display_name or str(self.id)


class ToolEvent(BaseModel):
    """Ивент, в рамках которого работает корректор или красная ручка"""

    id: str
    ends_at: _Datetime | None = Field(None, alias='endsAt')
    applications_enabled: bool = Field(True, alias='applicationsEnabled')

    @property
    def is_active(self) -> bool:
        return _is_alive(self.ends_at)


class CorrectorMark(BaseModel):
    """Замазанный фрагмент текста. `start` и `end` - смещения в UTF-16, как у спанов"""

    id: UUID | str
    start: int
    end: int
    event_id: str | None = Field(None, alias='eventId')
    actor: EventActor | None = None
    created_at: _Datetime | None = Field(None, alias='createdAt')
    ends_at: _Datetime | None = Field(None, alias='endsAt')

    @property
    def is_active(self) -> bool:
        return _is_alive(self.ends_at)


class CorrectorState(BaseModel):
    """Состояние корректора поста (`post.corrector`)"""

    revision: str | int | None = None
    server_time: _Datetime | None = Field(None, alias='serverTime')
    events: list[ToolEvent] = []
    marks: list[CorrectorMark] = []

    @property
    def active_marks(self) -> list[CorrectorMark]:
        """Замазки, которые еще видны на сайте"""
        return [mark for mark in self.marks if mark.is_active]

    @property
    def active_event(self) -> ToolEvent | None:
        return next((event for event in self.events if event.is_active and event.applications_enabled), None) or next(
            (event for event in self.events if event.is_active), None
        )


class RedPenCorrection(BaseModel):
    """Исправленное красной ручкой слово. `start` и `end` - смещения в UTF-16, как у спанов"""

    id: UUID | str
    start: int
    end: int
    replacement: str
    created_at: _Datetime | None = Field(None, alias='createdAt')

    def __str__(self) -> str:
        return self.replacement


class RedPenClaim(BaseModel):
    """Право пользователя на правки красной ручкой в посте"""

    id: UUID | str
    event_id: str | None = Field(None, alias='eventId')
    actor: EventActor | None = None
    is_owner: bool = Field(False, alias='isOwner')  # это правки текущего пользователя
    used: int = 0
    ends_at: _Datetime | None = Field(None, alias='endsAt')

    @property
    def is_active(self) -> bool:
        return _is_alive(self.ends_at)


class RedPenState(BaseModel):
    """Состояние красной ручки поста (`post.red_pen`)"""

    revision: str | int | None = None
    server_time: _Datetime | None = Field(None, alias='serverTime')
    events: list[ToolEvent] = []
    claims: list[RedPenClaim] = []
    corrections: list[RedPenCorrection] = []

    @model_validator(mode='before')
    @classmethod
    def single_claim(cls, data):
        # иногда апи присылает одну заявку в `claim` вместо списка `claims`
        if isinstance(data, dict) and 'claims' not in data and data.get('claim'):
            data = {**data, 'claims': [data['claim']]}
        return data

    @property
    def active_claims(self) -> list[RedPenClaim]:
        return [claim for claim in self.claims if claim.is_active]

    @property
    def active_corrections(self) -> list[RedPenCorrection]:
        """Правки, которые еще видны на сайте (пропадают вместе с заявками)"""
        return self.corrections if self.active_claims else []

    @property
    def own_claim(self) -> RedPenClaim | None:
        return next((claim for claim in self.active_claims if claim.is_owner), None)

    @property
    def active_event(self) -> ToolEvent | None:
        return next((event for event in self.events if event.is_active and event.applications_enabled), None) or next(
            (event for event in self.events if event.is_active), None
        )


def _utf16_slice(text: str, start: int, end: int) -> str:
    encoded = text.encode('utf-16-le')
    return encoded[start * 2 : end * 2].decode('utf-16-le', errors='replace')


def _stamp(item: CorrectorMark | RedPenCorrection) -> float:
    return item.created_at.timestamp() if item.created_at else 0


def visible_marks(marks: list[CorrectorMark], corrections: list[RedPenCorrection] = []) -> list[CorrectorMark]:
    """Замазки, которые видно на сайте

    Если на тот же фрагмент позже легла правка красной ручкой, сайт показывает правку, а не замазку.

    Args:
        marks (list[CorrectorMark]): Замазки
        corrections (list[RedPenCorrection], optional): Правки красной ручкой. Defaults to [].

    Returns:
        list[CorrectorMark]: Видимые замазки
    """
    newest_pen = {}
    for correction in corrections:
        key = (correction.start, correction.end)
        newest_pen[key] = max(newest_pen.get(key, 0), _stamp(correction))
    return [mark for mark in marks if (mark.start, mark.end) not in newest_pen or _stamp(mark) > newest_pen[(mark.start, mark.end)]]


def apply_marks(text: str, marks: list[CorrectorMark], mark_char: str = '■') -> str:
    """Текст с замазками: замазанные символы заменены на `mark_char` (пробелы остаются), как при копировании с сайта

    Правки красной ручкой сюда не входят: на сайте исходное слово остается зачеркнутым, а правка пишется поверх,
    в строку это без потерь не превратить. Они доступны через `RedPenState.active_corrections`.

    Args:
        text (str): Исходный текст
        marks (list[CorrectorMark]): Замазки
        mark_char (str, optional): Чем заменять замазанные символы. Defaults to '■'.

    Returns:
        str: Текст с замазками
    """
    length = len(text.encode('utf-16-le')) // 2
    result = []
    position = 0
    for mark in sorted(marks, key=lambda mark: (mark.start, mark.end)):
        start = max(mark.start, position)  # замазки могут пересекаться
        if start >= mark.end:
            continue
        result.append(_utf16_slice(text, position, start))
        result.append(''.join(char if char.isspace() else mark_char for char in _utf16_slice(text, start, mark.end)))
        position = mark.end
    result.append(_utf16_slice(text, position, length))
    return ''.join(result)
