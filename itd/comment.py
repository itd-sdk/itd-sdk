from uuid import UUID
from datetime import datetime
from math import ceil

from pydantic import Field, BaseModel, field_validator

from itd.base import ITDBaseModel, ITDList
from itd.client import Client
from itd.enums import CommentSorting, ReportTargetType, ReportReason
from itd.report import Report
from itd.utils import parse_datetime, to_nullable_uuid, format_attachments, ATTACHMENTS
from itd.api.comments import get_comments, add_comment, add_reply_comment, get_replies, like_comment, unlike_comment, delete_comment
from itd.user import User
from itd.file import CommentAttach


class Comment(ITDBaseModel):
    _refreshable = False

    id: UUID
    content: str

    created_at: datetime = Field(alias='createdAt')
    author: User

    likes_count: int = Field(0, alias='likesCount')
    replies_count: int = Field(0, alias='repliesCount')
    is_liked: bool = Field(False, alias='isLiked')

    attachments: list[CommentAttach]
    replies: 'Replies' = Field(default_factory=lambda: Replies())
    reply_to: User | None = None # author of replied comment, if this comment is reply

    _post_id: UUID | None = None
    _comment_id: UUID | None = None # base comment id, if this comment is reply

    def __init__(self, comment: dict, post_id: UUID | None = None, comment_id: UUID | None = None, client: Client | None = None, _skip_init: bool = False) -> None:
        if not _skip_init:
            super().__init__(client)

        for name, value in _CommentValidate.model_validate(comment).__dict__.items():
            setattr(self, name, value)
        self._post_id = post_id
        if comment_id:
            self._comment_id = comment_id
        self.replies._comment = self

    def __str__(self) -> str:
        return self.content

    def report(self, reason: ReportReason, description: str | None = None, client: Client | None = None) -> Report:
        return Report(self.id, ReportTargetType.COMMENT, reason, description, client or self.client)

    def reply(self, content: str | None = None, attachments: ATTACHMENTS = [], user_id: UUID | None = None, client: Client | None = None) -> 'Comment':
        """Ответить на комментарий

        Args:
            content (str | None, optional): Содержимое. Defaults to None.
            attachments (ATTACHMENTS, optional): Вложения. Defaults to [].
            user_id (UUID | None, optional): Пользователь (создатель комментария, на который отвечать), если None то берется автор текущего комментария. Defaults to None.
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            Comment: Комментарий
        """
        return Comment(
            add_reply_comment(
                client or self._client,
                self._comment_id or self.id,
                user_id or self.author.id,
                content,
                format_attachments(attachments)
            ).json(),
            self._post_id,
            client=client or self.client,
            _skip_init=True
        )

    def like(self, client: Client | None = None) -> int:
        """Лайкнуть комментарий

        Args:
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            int: Количество лайков после лайка
        """
        likes = like_comment(client or self._client, self.id).json()['likesCount']
        self.likes_count = likes
        return likes

    def unlike(self, client: Client | None = None) -> int:
        """Убрать лайк с комментария

        Args:
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            int: Количество лайков после убирания лайка
        """
        likes = unlike_comment(client or self._client, self.id).json()['likesCount']
        self.likes_count = likes
        return likes

    def delete(self, client: Client | None = None) -> None:
        """Удалить комментарий

        Args:
            client (Client | None, optional): Клиент. Defaults to None.
        """
        delete_comment(client or self._client, self.id)


    @classmethod
    def new(cls, post_id: UUID, content: str | None = None, attachments: ATTACHMENTS = [], client: Client | None = None):
        instance = cls.__new__(cls)
        super(Comment, instance).__init__(client)
        instance.__init__(
            add_comment(
                client or instance.client,
                post_id,
                content,
                format_attachments(attachments)
            ).json(),
            post_id,
            client=client or instance.client
        )
        return instance



class _CommentValidate(BaseModel, Comment):
    @field_validator('replies', mode='plain')
    @classmethod
    def validate_replies(cls, replies: list[dict]):
        return Replies(replies)

    @field_validator('created_at', mode='plain')
    @classmethod
    def validate_created_at(cls, v: str):
        return parse_datetime(v)

    @field_validator('reply_to', mode='plain')
    @classmethod
    def validate_reply_to(cls, reply_to: dict | None):
        if reply_to is not None:
            return User._from_dict(reply_to, False)

    @field_validator('author', mode='plain')
    @classmethod
    def validate_author(cls, author: dict):
        return User._from_dict(author, False)





class Comments(ITDList, list[Comment]):
    """Список комментариев с функцией дозагрузки"""
    _refreshable = False
    _limit = 500

    _post_id: UUID
    total: int
    _sorting: CommentSorting = CommentSorting.POPULAR

    @property
    def _load_with_parent(self): # pyright: ignore[reportIncompatibleVariableOverride]
        return self.client.config.load_comments_from_post

    def __init__(self, data: list[dict] = []):
        super().__init__()
        self.extend([Comment(comment) for comment in data])

    def _fetch(self, client: Client, limit: int):
        return get_comments(client, self._post_id, len(self), limit).json()['data']

    def _extend(self, objects: list, client: Client):
        self.extend([Comment(comment, self._post_id, client=client) for comment in objects])

    @staticmethod
    def _get_objects(data: dict) -> list[dict]:
        return data['comments']

    @staticmethod
    def _get_has_more(data: dict) -> bool:
        return data['hasMore']

    def _get_total(self, data: dict) -> int:
        return data['total']

    def new(self, content: str | None = None, attachments: ATTACHMENTS = [], client: Client | None = None) -> Comment:
        comment = Comment.new(self._post_id, content, attachments, client=client or self.client)
        self.insert(0, comment)
        return comment

    @property
    def sorting(self) -> CommentSorting:
        return self._sorting

    @sorting.setter
    def sorting(self, value: CommentSorting):
        self._sorting = value
        self.refresh()


    def __setattr__(self, name: str, value) -> None:
        if name == '_client':
            for comment in self.copy():
                comment._client = value
        elif name == '_post_id':
            for comment in self.copy():
                comment._post_id = value
        super().__setattr__(name, value)



class Replies(Comments):
    _limit = 100
    _comment: 'Comment'

    def _fetch(self, client: Client, limit: int):
        return get_replies(
            client or self._client,
            self._comment.id,
            ceil(max(len(self), 1) / limit), # page equals already loaded divide by [LIMIT]
            limit
        ).json()['data']

    @staticmethod
    def _get_has_more(data: dict) -> bool:
        return data['pagination']['hasMore']

    @staticmethod
    def _get_objects(data: dict) -> list[dict]:
        return data['replies']

    def _get_total(self, data: dict) -> int:
        return self._comment.replies_count

    def _extend(self, objects: list, client: Client) -> None:
        self.extend([Comment(comment, comment_id=self._comment.id, client=client) for comment in objects])


    def __setattr__(self, name: str, value) -> None:
        if name == '_comment':
            for comment in self.copy():
                comment._comment_id = value.id

        super().__setattr__(name, value)


    def new(self, content: str | None = None, attachments: ATTACHMENTS = [], client: Client | None = None, *, author_id: str | UUID | None = None) -> 'Comment':
        assert self._comment is not None
        reply = self._comment.reply(content, attachments, to_nullable_uuid(author_id), client)
        self.insert(0, reply)
        return reply