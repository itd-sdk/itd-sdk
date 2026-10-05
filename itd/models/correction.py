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


def apply_corrections(text: str, marks: list[CorrectorMark] = [], corrections: list[RedPenCorrection] = [], mark_char: str = '■') -> str:
    """Текст поста так, как его видно на сайте: замазанное заменено на `mark_char`, исправленное - на правку

    Если замазка и правка попали на один фрагмент, остается более поздняя (как на сайте).

    Args:
        text (str): Исходный текст
        marks (list[CorrectorMark], optional): Замазки. Defaults to [].
        corrections (list[RedPenCorrection], optional): Правки красной ручкой. Defaults to [].
        mark_char (str, optional): Чем заменять замазанные символы (пробелы остаются). Defaults to '■'.

    Returns:
        str: Текст с правками
    """
    latest: dict[tuple[int, int], CorrectorMark | RedPenCorrection] = {}
    for item in [*marks, *corrections]:
        key = (item.start, item.end)
        current = latest.get(key)
        stamp = item.created_at.timestamp() if item.created_at else 0
        if current is None or stamp >= (current.created_at.timestamp() if current.created_at else 0):
            latest[key] = item

    length = len(text.encode('utf-16-le')) // 2
    result = []
    position = 0
    for (start, end), item in sorted(latest.items()):
        if start < position:  # пересекается с уже примененной правкой
            continue
        result.append(_utf16_slice(text, position, start))
        original = _utf16_slice(text, start, end)
        if isinstance(item, RedPenCorrection):
            result.append(item.replacement)
        else:
            result.append(''.join(char if char.isspace() else mark_char for char in original))
        position = end
    result.append(_utf16_slice(text, position, length))
    return ''.join(result)
