from __future__ import annotations

from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from pydantic import BeforeValidator, Field

from itd.api.comments import add_comment, add_reply_comment, delete_comment, edit_comment, get_comments, get_replies, like_comment, unlike_comment
from itd.core.base import ITDBaseModel, ITDList
from itd.core.utils import parse_datetime, to_nullable_uuid, to_uuid
from itd.enums import CommentSorting, LoadStatus, ReportReason, ReportTargetType
from itd.models.file import CommentAttach
from itd.models.report import Report
from itd.models.user import User
from itd.models.utils import ATTACHMENTS, format_attachments

if TYPE_CHECKING:
    from itd.core.client import Client
    from itd.models.post import Post


class Comment(ITDBaseModel):
    _refreshable = True

    id: UUID
    content: str

    created_at: Annotated[datetime, BeforeValidator(parse_datetime)] = Field(alias='createdAt')
    author: User

    likes_count: int = Field(0, alias='likesCount')
    replies_count: int = Field(0, alias='repliesCount')
    is_liked: bool = Field(False, alias='isLiked')

    attachments: list[CommentAttach] = Field(default_factory=list)
    first_replies: list[Comment] = Field(default_factory=list, alias='replies')
    reply_to: User | None = Field(None, alias='replyTo')  # author of replied comment, if this comment is reply

    _post: Post | None = None
    _base_comment: Comment | None = None
    _init_from_id: bool = False

    def __init__(self, id: UUID | str, *, client: Client | None = None) -> None:
        super().__init__(client=client)
        self.id = to_uuid(id)
        self._init_from_id = True

    @classmethod
    def from_dict(
        cls, data: dict, post: Post | None = None, base_comment: Comment | None = None, *, context: dict | None = None, client: Client | None = None
    ) -> Comment:
        context = dict(context or {})
        if post is not None:
            context['post'] = post
        if base_comment is not None:
            context['base_comment'] = base_comment
        return super().from_dict(data, client=client, context=context)

    def _refresh(self, *, client: Client):
        if self._init_from_id:
            raise RuntimeError('Unable to refresh comment that initialized by id. Please load comment from post')
        else:
            super()._refresh(client=client)

    @cached_property
    def replies(self) -> Replies:
        assert self._post is not None, 'post not set'
        replies = Replies(client=self.client)
        replies._post = self._post
        replies._base_comment = self
        return replies

    def __hash__(self):
        return int(self.id)

    def __str__(self) -> str:
        return self.content

    def report(self, reason: ReportReason, description: str | None = None, client: Client | None = None) -> Report:
        return Report(self.id, ReportTargetType.COMMENT, reason, description, client or self.client)

    def reply(self, content: str | None = None, attachments: ATTACHMENTS = [], user_id: UUID | None = None, client: Client | None = None) -> Comment:
        """Ответить на комментарий

        Args:
            content (str | None, optional): Содержимое. Defaults to None.
            attachments (ATTACHMENTS, optional): Вложения. Defaults to [].
            user_id (UUID | None, optional): Автор комментария, на который отвечать. Если None, берется автор текущего комментария. Defaults to None.
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            Comment: Комментарий
        """
        comment = Comment.from_dict(
            add_reply_comment(
                client or self._client,
                self._base_comment.id if self.is_reply and self._base_comment is not None else self.id,
                user_id or self.author.id,
                content,
                format_attachments(attachments)
            ).json(),
            post=self._post,
            base_comment=self._base_comment if self.is_reply else self,
            client=client or self.client
        )
        comment.reply_to = User(user_id) if user_id else self.author  # manual patch stupid api
        if self.is_reply:
            assert self._base_comment is not None
            self._base_comment.replies.append(comment)
            self._base_comment.replies.total += 1
            self._base_comment.replies_count += 1
        else:
            self.replies.append(comment)
            self.replies.total += 1
            self.replies_count += 1

        if self._post is not None:
            self._post.comments_count += 1
        return comment

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

    def edit(self, content: str, *, client: Client | None = None) -> datetime:
        """Изменить комментарий

        Args:
            content (str): Новое содержимое
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            datetime: Дата изменения
        """
        edited_at = edit_comment(client or self.client, self.id, content).json()['editedAt']
        self.content = content
        return parse_datetime(edited_at)

    @classmethod
    def new(cls, post: Post, content: str | None = None, attachments: ATTACHMENTS = [], client: Client | None = None) -> Comment:
        instance = cls.__new__(cls)
        super(Comment, instance).__init__(client)
        comment = cls.from_dict(
            add_comment(client or instance.client, post.id, content, format_attachments(attachments)).json(), post, client=client or instance.client
        )
        if post.is_loaded('comments_count'):
            post.comments_count += 1
        post.comments.insert(0, comment)
        return comment

    @property
    def url(self) -> str:
        assert self._post is not None, 'post not set'
        return f'https://xn--d1ah4a.com/@{self._post.author.username}/post/{self._post.id}?comment={self.id}'

    @property
    def link(self) -> str:
        return self.url

    @property
    def is_reply(self) -> bool:
        return self.reply_to is not None

    @property
    def is_owner(self) -> bool:
        return self.client.user_id == self.author.id

    @property
    def can_delete(self) -> bool:
        assert self._post is not None, 'post not set'
        return self.is_owner or self._post.is_owner

    @property
    def can_edit(self) -> bool:
        return self.is_owner

    @property
    def can_report(self) -> bool:
        return not self.is_owner

    def _post_refresh(self, context: dict = {}):
        self.load_status = LoadStatus.FULL
        self._base_comment = context.get('base_comment')
        self._post = context.get('post')
        for reply in self.first_replies:
            reply._base_comment = self


class Comments(ITDList[Comment]):
    """Список комментариев с функцией дозагрузки"""

    _load_with_parent = False
    _post: Post
    total: int
    cursor: int = 0
    _sorting: CommentSorting = CommentSorting.POPULAR

    def _fetch(self, client: Client, limit: int):
        return get_comments(client, self._post.id, self.cursor, limit).json()['data']

    def _to_models(self, objects: list, client: Client):
        return [Comment.from_dict(comment, self._post, client=client) for comment in objects]

    @staticmethod
    def _get_objects(data: dict) -> list[dict]:
        return data['comments']

    @staticmethod
    def _get_has_more(data: dict) -> bool:
        return data['hasMore']

    @staticmethod
    def _get_total(data: dict) -> int:
        return data['total']

    @staticmethod
    def _get_cursor(data: dict):
        return data['nextCursor']

    def new(self, content: str | None = None, attachments: ATTACHMENTS = [], client: Client | None = None) -> Comment:
        comment = Comment.new(self._post, content, attachments, client=client or self.client)
        if hasattr(self, 'total'):
            self.total += 1
        return comment

    @property
    def sorting(self) -> CommentSorting:
        return self._sorting

    @sorting.setter
    def sorting(self, value: CommentSorting):
        self._sorting = value
        self.refresh()

    def __str__(self):
        return str([str(c) for c in self.copy()])


class Replies(ITDList[Comment]):
    _base_comment: 'Comment'

    _post: Post
    total: int = 0
    cursor: int = 1
    _is_page_pagination = True

    def _fetch(self, client: Client, limit: int):
        return get_replies(client or self._client, self._base_comment.id, self.cursor, limit).json()['data']

    @staticmethod
    def _get_has_more(data: dict) -> bool:
        return data['pagination']['hasMore']

    @staticmethod
    def _get_objects(data: dict) -> list[dict]:
        return data['replies']

    @staticmethod
    def _get_cursor(data: dict):
        return data['pagination']['page'] + 1

    @staticmethod
    def _get_total(data: dict) -> int:
        return data['pagination']['total']

    def _to_models(self, objects: list, client: Client):
        return [Comment.from_dict(comment, self._post, self._base_comment, client=client) for comment in objects]

    def new(self, content: str | None = None, attachments: ATTACHMENTS = [], client: Client | None = None, *, author_id: str | UUID | None = None) -> 'Comment':
        return self._base_comment.reply(content, attachments, to_nullable_uuid(author_id), client)
