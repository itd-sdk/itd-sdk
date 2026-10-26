from __future__ import annotations

from datetime import datetime
from json import loads
from threading import Thread
from typing import TYPE_CHECKING, Annotated, Any, Callable, Iterator, Literal, cast
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field
from sseclient import SSEClient

from itd.api.notifications import (
    get_notifications,
    get_notifications_settings,
    get_unread_notifications_count,
    mark_all_as_read,
    mark_as_read,
    stream_notifications,
    update_notifications_settings
)
from itd.core.base import ITDBaseModel, ITDList
from itd.core.client import Client
from itd.core.logger import get_logger
from itd.core.utils import parse_datetime
from itd.enums import DebugResponseMode, LoadStatus, NotificationSubjectType, NotificationTargetType, NotificationType
from itd.models.user import User

if TYPE_CHECKING:
    from itd.core.client import Client


l = get_logger('notifications')  # noqa: E741


class NotificationsSettings(ITDBaseModel):
    enabled: bool
    web_enabled: bool = Field(True, alias='webEnabled')
    sound: bool = Field(alias='sound')
    follows: bool
    wall_posts: bool = Field(alias='wallPosts')
    likes: bool
    comments: bool
    replies: bool = True
    mentions: bool

    def _refresh(self, *, client: Client):
        return get_notifications_settings(client).json()

    def update(
        self,
        enabled: bool | None = None,
        web_enabled: bool | None = None,
        sound: bool | None = None,
        follows: bool | None = None,
        wall_posts: bool | None = None,
        likes: bool | None = None,
        comments: bool | None = None,
        replies: bool | None = None,
        mentions: bool | None = None,
        client: Client | None = None,
        old: bool = True,
        new: bool = True
    ):
        if self.load_status != LoadStatus.FULL:
            self.refresh()
        if enabled is not None:
            self.enabled = enabled
        if web_enabled is not None:
            self.web_enabled = web_enabled
        if sound is not None:
            self.sound = sound
        if follows is not None:
            self.follows = follows
        if wall_posts is not None:
            self.wall_posts = wall_posts
        if likes is not None:
            self.likes = likes
        if comments is not None:
            self.comments = comments
        if replies is not None:
            self.replies = replies
        if mentions is not None:
            self.mentions = mentions
        self.update_from_fields(client, old=old, new=new)

    def _dump(self, *, old: bool = True, new: bool = True) -> dict:
        """Собрать тело запроса: апи какое то время принимает и старый, и новый формат"""
        data = {}
        if old:
            data.update(_NotificationsSettingsOld.model_validate(self, from_attributes=True).model_dump(mode='json', by_alias=True))

        if new:
            data.update(
                _NotificationsSettingsNew(
                    web_enabled=self.web_enabled,
                    sound_enabled=self.sound,
                    preferences=_NotificationsSettingsNewPreferences.model_validate(self, from_attributes=True),
                    enabled=self.enabled
                ).model_dump(mode='json', by_alias=True)
            )

        return data

    def update_from_fields(self, client: Client | None = None, *, old: bool = True, new: bool = True):
        update_notifications_settings(client or self.client, self._dump(old=old, new=new))


class _NotificationsSettingsOld(BaseModel):
    enabled: bool
    sound: bool
    follows: bool
    wall_posts: bool = Field(serialization_alias='wallPosts')
    likes: bool
    comments: bool
    mentions: bool


class _NotificationsSettingsNewPreferences(BaseModel):
    follows: bool
    reactions: bool = Field(validation_alias='likes')
    comments: bool
    replies: bool
    mentions: bool
    wall_posts: bool = Field(serialization_alias='wallPosts')


class _NotificationsSettingsNew(BaseModel):
    web_enabled: bool = Field(serialization_alias='webEnabled')
    sound_enabled: bool = Field(serialization_alias='soundEnabled')
    preferences: _NotificationsSettingsNewPreferences
    enabled: bool


class Notification(ITDBaseModel):
    _refreshable = False
    _notifications: Notifications

    id: UUID
    type: NotificationType

    target_type: NotificationTargetType | None = Field(None, alias='targetType')  # none if follow, NotificationTargetType.POST otherwise
    target_id: UUID | None = Field(None, alias='targetId')  # none - follows
    subject_type: NotificationSubjectType | None = Field(
        None, alias='subjectType'
    )  # NotificationSubjectType.COMMENT if comment_like or reply follows, other - NotificationTragetType.POST, none otherwise
    subject_id: UUID | None = Field(None, alias='subjectId')

    preview: str | None = (
        None  # follow - none, comment/reply - content, repost - original post content, like - post/comment content, wall_post - wall post content
    )
    title: str | None = None

    is_read: bool = Field(False, alias='read')
    read_at: Annotated[datetime, BeforeValidator(parse_datetime)] | None = Field(None, alias='readAt')
    created_at: Annotated[datetime, BeforeValidator(parse_datetime)] = Field(alias='createdAt')

    actor: User | None = None
    sound: bool = False  # for notifications from stream

    def __hash__(self):
        return int(self.id)

    @classmethod
    def from_dict(cls, data: dict, notifications: Notifications, *, client: Client | None = None):  # ty: ignore # who asked
        instance = super().from_dict(data, client=client)
        instance._notifications = notifications
        return instance

    def read(self, client: Client | None = None) -> None:
        mark_as_read(client or self.client, self.id)

        if not self.is_read and self._notifications._unread:  # check if already read and has notifications and unread loaded
            self._notifications._unread -= 1

        self.is_read = True
        self.read_at = datetime.now()

    def get_text(self, actor: bool = True, avatar: bool = False) -> str:
        text = ''
        if self.title:
            return self.title
        assert self.actor
        if avatar:
            text += self.actor.avatar + ' '
        if actor:
            text += self.actor.display_name + ' '

        match self.type:
            case NotificationType.FOLLOW:
                text += 'подписался(-ась) на вас'
            case NotificationType.FOLLOW_REQUEST:
                text += 'хочет подписаться на вас'
            case NotificationType.FOLLOW_ACCEPTED:
                text += 'принял(а) вашу заявку на подписку'
            case NotificationType.LIKE:
                text += 'оценил(а) ваш пост'
            case NotificationType.COMMENT:
                text += 'прокомментировал(а) ваш пост'
            case NotificationType.REPOST:
                text += 'сделал(а) репост вашего поста'
            case NotificationType.COMMENT_LIKE:
                text += 'оценил(а) ваш комментарий'
            case NotificationType.REPLY:
                text += 'ответил(а) на ваш комментарий'
            case NotificationType.MENTION:
                text += 'упомянул(а) вас в посте'
            case NotificationType.COMMENT_MENTION:
                text += 'упомянул(а) вас в комментарии'
            case NotificationType.WALL_POST:
                text += 'написал(а) на вашей стене'

        return text

    def get_color(self) -> Literal['blue'] | Literal['green'] | Literal['red'] | Literal['purple']:
        match self.type:
            case NotificationType.FOLLOW | NotificationType.FOLLOW_REQUEST | NotificationType.REPOST | NotificationType.WALL_POST:
                return 'blue'

            case NotificationType.FOLLOW_ACCEPTED | NotificationType.COMMENT | NotificationType.REPLY:
                return 'green'

            case NotificationType.LIKE | NotificationType.COMMENT_LIKE:
                return 'red'

            case NotificationType.MENTION | NotificationType.COMMENT_MENTION | NotificationType.EVENT_REMINDER:
                return 'purple'

    def __str__(self):
        return self.get_text()


class Notifications(ITDList[Notification]):
    cursor: int = 0

    def __init__(self, client: Client | None = None):
        super().__init__(client=client)
        self._unread: int | None = None
        self.settings = NotificationsSettings(client=client)

        self._callbacks: dict[NotificationType | None, list[Callable[[Notification], Any]]] = {}
        for type in NotificationType:
            self._callbacks[type] = []
        self._callbacks[None] = []

    def _fetch(self, client: Client, limit: int) -> dict:
        return get_notifications(client, limit, len(self)).json()

    def _get_cursor(self, data: dict) -> int:
        return len(self)

    @staticmethod
    def _get_objects(data: dict) -> list[dict]:
        return data['notifications']

    @staticmethod
    def _get_has_more(data: dict) -> bool:
        return data['hasMore']

    def _to_models(self, objects: list, client: Client):
        return [Notification.from_dict(notification, self, client=client) for notification in objects]

    def read_all(self):
        mark_all_as_read(self.client)
        self._unread = 0

    @property
    def unread_count(self):
        if self._unread is None:
            self._unread = get_unread_notifications_count(self.client).json()['count']
        return self._unread

    def stream(self) -> Iterator[Notification]:
        self._stream = stream_notifications(self.client)
        l.info('start stream')

        for event in SSEClient(cast(Iterator[bytes], self._stream)).events():
            data = loads(event.data)
            if self.client.config.debug_response != DebugResponseMode.NO:
                l.debug('< %s', data)

            if 'userId' in data and 'timestamp' in data and 'type' not in data:
                l.info('received init message', data)
                continue  # initial message

            notification: Notification = Notification.from_dict(data, self, client=self.client)
            self.insert(0, notification)
            if self._unread is not None:
                self._unread += 1

            l.info('new notification type=%s', notification.type.value)
            exec(f'self.on_{notification.type.value}(notification)')
            self.on_notification(notification)
            for callback in self._callbacks[notification.type] + self._callbacks[None]:
                callback(notification)

            yield notification

        l.info('stop stream')

    def stream_bg(self, daemon: bool = False) -> Thread:
        def _stream():
            for _ in self.stream():
                continue

        thread = Thread(target=_stream, daemon=daemon)
        thread.start()
        return thread

    def stop_stream(self) -> None:
        if getattr(self, '_stream', None) is not None:
            assert self._stream
            self._stream.close()
            self._stream = None

    # redefine this for your needs (eg notifications.on_like = my_function)
    def on_like(self, notification: Notification, /) -> None: ...

    def on_comment(self, notification: Notification, /) -> None: ...

    def on_reply(self, notification: Notification, /) -> None: ...

    def on_repost(self, notification: Notification, /) -> None: ...

    def on_mention(self, notification: Notification, /) -> None: ...

    def on_follow(self, notification: Notification, /) -> None: ...

    def on_follow_request(self, notification: Notification, /) -> None: ...

    def on_follow_accepted(self, notification: Notification, /) -> None: ...

    def on_comment_like(self, notification: Notification, /) -> None: ...

    def on_comment_mention(self, notification: Notification, /) -> None: ...

    def on_wall_post(self, notification: Notification, /) -> None: ...

    def on_notification(self, notification: Notification, /) -> None: ...

    def on(self, type: NotificationType | None = None):
        def decorator(func: Callable[[Notification], Any]):
            self._callbacks[type].append(func)
            return func

        return decorator


Ntfs = Notifications  # short alias
Ntf = Notification
