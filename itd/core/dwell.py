from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_serializer

from itd.api.dwell import send_interactions, send_views
from itd.core.base import ITDBaseModel
from itd.core.logger import get_logger
from itd.core.timer import Timer
from itd.enums import InteractionType, ViewReason, ViewSource

if TYPE_CHECKING:
    from itd.core.client import Client

l = get_logger('dwell')  # noqa: E741


class DwellEvent(BaseModel):
    vs: str = Field(alias='v')
    source: ViewSource = Field(alias='s')


class InteractionEvent(DwellEvent):
    type: InteractionType = Field(alias='t')
    attachment_id: UUID = Field(alias='ai')


class PhotoOpenEvent(InteractionEvent):
    index: int | None = Field(None, alias='mi')


class VideoProgressEvent(InteractionEvent):
    played: int = Field(alias='pm')
    duration: int = Field(alias='dm')


class ViewEvent(DwellEvent):
    duration: int = Field(alias='md')
    entered_at: int = Field(alias='et')
    exited_at: int = Field(alias='xt')
    reason: ViewReason = Field(alias='r')
    source_context: str | None = Field(None, alias='sc')
    has_seen: bool = Field(False, alias='b')

    @field_serializer('has_seen', mode='plain')
    @classmethod
    def serialize_has_seen(cls, value: bool):
        return int(value)


class DwellTracker(ITDBaseModel):
    _refreshable = False

    def __init__(self, client: Client | None = None) -> None:
        super().__init__(client)
        self.views: list[ViewEvent] = []
        self.interactions: list[InteractionEvent] = []
        self.seen_posts: set[UUID] = set()
        self.sid = uuid4()
        self.timer = Timer('dwell', self.client.config.dwell_send_interval, self.send, on_exit=self.send if self.client.config.dwell_save_on_quit else None)

    def send_views(self) -> bool:  # call on app visibilitychange
        """Отправить просмотры (api/v1/i) и очистить буффер

        Returns:
            bool: Статус (False если буффер пустой и ничего не было отправлено)
        """
        if not self.views:
            return False
        l.info('dwell send view batch')
        send_views(
            self.client,
            [
                event.model_dump(
                    mode='json', by_alias=True, exclude_none=True, exclude={'source'} if event.source not in (ViewSource.POST_PAGE, ViewSource.LINK) else {}
                )  # хз зачем убирать сурс но в оф клиенте так написано
                for event in self.views
            ],
            self.sid
        )
        self.views.clear()
        return True

    def send_interactions(self) -> bool:  # call on app visibilitychange
        """Отправить события взаимодействий с вложениями (api/v1/x) и очистить буффер

        Returns:
            bool: Статус (False если буффер пустой и ничего не было отправлено)
        """
        if not self.interactions:
            return False
        l.info('dwell send interactions batch')
        send_interactions(self.client, [event.model_dump(mode='json', by_alias=True) for event in self.interactions], self.sid)
        self.interactions.clear()
        return True

    def record_view(
        self,
        id: UUID,
        vs: str,
        duration: int,
        entered_at: datetime,
        exited_at: datetime,
        source: ViewSource,
        source_context: str | None = None,
        reason: ViewReason = ViewReason.NORMAL
    ):
        """Записать событие просмотра

        Args:
            id (UUID): ID поста
            vs (str): VS
            duration (int): Время на просмотр (сколько времени пользователь читал пост) (мс). Желательно должно быть 250+
            entered_at (datetime): Дата открытия поста (когда пользователь увидел пост)
            exited_at (datetime): Дата скрытия поста (когда пост пропал из зоны видимости)
            source (ViewSource): Страница, с которой произошел просмотр
            source_context (str | None, optional): Контекст страницы, с которой произошел просмотр. Defaults to None.
            reason (ViewReason, optional): Причина просмотра. Defaults to ViewReason.NORMAL.
        """
        l.info(
            'dwell add view record id=%s vs=%s duration=%s entered_at=%s exited_at=%s source=%s source_context=%s reason=%s',
            id,
            vs,
            duration,
            entered_at.strftime('%X.%f'),
            exited_at.strftime('%X.%f'),
            source.name.lower(),
            source_context,
            reason.name.lower()
        )

        self.views.append(
            ViewEvent(  # stupid pydantic i want validate by name
                v=vs,
                md=duration,
                et=round(entered_at.timestamp() * 1000),
                xt=round(exited_at.timestamp() * 1000),
                r=reason,
                s=source,
                sc=source_context,
                b=id in self.seen_posts
            )
        )
        self.seen_posts.add(id)
        if len(self.views) >= self.client.config.dwell_max_buffer:
            self.send_views()

    def record_photo_open(self, vs: str, source: ViewSource, attachment_id: UUID, index: int):
        """Записать событие просмотра фото

        Args:
            vs (str): VS
            source (ViewSource): Страница, с которой проищошел просмотр
            attachment_id (UUID): ID вложения
            index (int): Индекс вложения
        """
        l.info('dwell add photo open record vs=%s source=%s id=%s index=%s', vs, source.value, attachment_id, index)

        self.interactions.append(PhotoOpenEvent(v=vs, s=source, t=InteractionType.PHOTO_OPEN, ai=attachment_id, mi=index))
        if len(self.interactions) >= self.client.config.dwell_max_buffer:
            self.send_interactions()

    def record_video_progress(self, vs: str, source: ViewSource, attachment_id: UUID, played: int, duration: int):
        """Записать событие просмотра видео (отправлять каждые 2-3 сек пока запущено видео)

        Args:
            vs (str): VS
            source (ViewSource): Страница, с которой произошел просмотр
            attachment_id (UUID): ID просмотренного вложения
            played (int): Сколько было просмотренно (мс) с учетом перепросмотров
            duration (int): Общая длительность видео (константа) (мс)
        """
        l.info('dwell add video progress record vs=%s source=%s id=%s played=%s duration=%s', vs, source, attachment_id, played, duration)

        self.interactions.append(VideoProgressEvent(v=vs, s=source, t=InteractionType.VIDEO_PROGRESS, ai=attachment_id, pm=played, dm=duration))
        if len(self.interactions) >= self.client.config.dwell_max_buffer:
            self.send_interactions()

    def send(self):
        self.send_views()
        self.send_interactions()

    def start(self):
        if self.client.config.dwell_enabled:
            self.timer.start()

    def stop(self):
        self.timer.stop(run_on_exit=self.client.config.dwell_save_on_quit)
