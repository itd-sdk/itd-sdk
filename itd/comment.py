from uuid import UUID
from datetime import datetime
from math import ceil

from pydantic import Field, BaseModel, field_validator

from itd.base import ITDBaseModel
from itd.client import Client
from itd.enums import CommentSorting, All, ALL, ReportTargetType, ReportReason
from itd.report import Report
from itd.utils import parse_datetime, to_uuid, to_nullable_uuid, format_attachments, ATTACHMENTS
from itd.routes.comments import get_comments, add_comment, add_reply_comment, get_replies, like_comment, unlike_comment, delete_comment
from itd.models.user import UserPost
from itd.file import CommentAttach, File

class Comment(ITDBaseModel):
    _refreshable = False

    id: UUID
    content: str

    created_at: datetime = Field(alias='createdAt')
    author: UserPost

    likes_count: int = Field(0, alias='likesCount')
    replies_count: int = Field(0, alias='repliesCount')
    is_liked: bool = Field(False, alias='isLiked')

    attachments: list[CommentAttach]
    replies: 'Replies' = Field(default_factory=lambda: Replies(_empty=True))
    reply_to: UserPost | None = None # author of replied comment, if this comment is reply

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
        # print(self.id, self.reply_to)
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
                self.id,
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



class Comments(ITDBaseModel, list[Comment]):
    """Список комментариев с функцией дозагрузки"""
    _refreshable = False

    _post_id: UUID
    has_more: bool = True
    total: int
    _sorting: CommentSorting = CommentSorting.POPULAR

    def __init__(self, data: list[dict] = [], _empty: bool = False):
        if _empty: # only for default value
            return

        super().__init__()
        self.extend([Comment(comment) for comment in data])


    def load(self, count: int | All = 100, limit: int = 500, client: Client | None = None) -> 'Comments':
        """Загрузить комментарии

        Args:
            count (int | None, optional): Количество (None - все). Defaults to 100.
            limit (int, optional): Лимит загрузки за раз (1 >= limit >= 500). Defaults to 500.
            client (Client | None, optional): Клиент. Defaults to None.
        """
        if isinstance(count, All):
            ncount = None
        else:
            ncount = count

        left = ncount or limit # if None get [LIMIT] firstly

        while left > 0: # can be !=, but what if something went wrong
            data = get_comments(
                client or self._client,
                self._post_id,
                len(self), # cursor equals already loaded
                min(limit, left) # not always [LIMIT] to not overflow (if left < [LIMIT], use left, [LIMIT] otherwise)
            ).json()['data']

            self.has_more = data['hasMore']
            self.total = data['total']

            if ncount is None:
                left = self.total - len(self)
            elif self.total < ncount:
                left = 0

            comments = data['comments']
            left -= len(comments)
            if not comments or not self.has_more:
                break

            print(f'fetched {len(comments)} left={left} (was {len(self)})')
            self.extend([Comment(comment, self._post_id, client=client or self.client) for comment in comments])
        return self


    def load_all(self, limit: int = 500, client: Client | None = None) -> 'Comments': # dont know why you should change client to load comments but
        """Загрузить все комментарии

        Args:
            limit (int, optional): Лимит загрузки за раз (1 >= limit >= 500). Defaults to 500.
            client (Client | None, optional): Клиент. Defaults to None.
        """
        return self.load(ALL, limit, client)

    def refresh(self, count: int | None = None, client: Client | None = None, limit: int = 500) -> 'Comments': # "None" count means already loaded count
        count = count or len(self)
        self.clear()
        return self.load(count, limit, client)


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

    @property
    def all(self) -> 'Comments':
        return self.load_all()


    def __setattr__(self, name: str, value) -> None:
        if name == '_client':
            for comment in self:
                comment._client = value
        elif name == '_post_id':
            for comment in self:
                comment._post_id = value
        super().__setattr__(name, value)



class Replies(Comments):
    _comment: 'Comment'

    def load(self, count: int | All = 100, limit: int = 100, client: Client | None = None) -> 'Replies':
        """Загрузить ответы

        Args:
            count (int | None, optional): Количество (None - все). Defaults to 100.
            limit (int, optional): Лимит загрузки за раз (1 >= limit >= 100). Defaults to 100.
            client (Client | None, optional): Клиент. Defaults to None.
        """
        if isinstance(count, All):
            ncount = None
        else:
            ncount = count

        left = ncount or limit # if None get [LIMIT] firstly

        while left > 0: # can be !=, but what if something went wrong
            data = get_replies(
                client or self._client,
                self._comment.id,
                ceil(len(self) / min(limit, left)), # page equals already loaded divide by [LIMIT]
                min(limit, left), # not always [LIMIT] to not overflow (if left < [LIMIT], use left, [LIMIT] otherwise)
            ).json()['data']
            self.has_more = data['pagination']['hasMore']
            self.total = data['pagination']['total']

            if ncount is None:
                left = self.total - len(self)

            replies = data['replies']
            left -= len(replies)

            if not replies or not self.has_more:
                break

            if left < 0: # um what
                replies = replies[:len(replies) + left] # cut extra (stupid api)

            print(f'loaded {len(replies)} left={left} was={len(self)}')
            self.extend([Comment(comment, comment_id=self._comment.id, client=client or self.client) for comment in replies])
        return self

    def load_all(self, limit: int = 100, client: Client | None = None) -> 'Replies':
        """Загрузить все ответы

        Args:
            limit (int, optional): Лимит загрузки за раз (1 >= limit >= 100). Defaults to 100.
            client (Client | None, optional): Клиент. Defaults to None.
        """
        return self.load(ALL, limit, client)


    def __setattr__(self, name: str, value) -> None:
        if name == '_comment':
            for comment in self:
                comment._comment_id = value.id

        super().__setattr__(name, value)


    def new(self, content: str | None = None, attachments: ATTACHMENTS = [], client: Client | None = None, *, author_id: str | UUID | None = None) -> 'Comment':
        assert self._comment is not None
        reply = self._comment.reply(content, attachments, to_nullable_uuid(author_id), client)
        self.insert(0, reply)
        return reply