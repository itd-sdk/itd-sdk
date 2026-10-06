from __future__ import annotations

from datetime import datetime, timedelta, timezone
from time import sleep
from typing import TYPE_CHECKING, Annotated, Literal, overload
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field, field_validator

from itd.api.hashtags import get_posts_by_hashtag
from itd.api.portal import (
    apply_corrector,
    apply_red_pen,
    cancel_corrector,
    cancel_red_pen,
    get_event_posts_correctors_state,
    get_event_posts_red_pens_state,
    report_corrector,
    report_red_pen
)
from itd.api.posts import (
    create_post,
    delete_post,
    edit_post,
    get_liked_posts,
    get_post,
    get_posts,
    get_stats,
    get_user_posts,
    like_post,
    pin_post,
    repost,
    restore_post,
    unlike_post,
    unpin_post
)
from itd.core.base import ITDBaseModel, ITDdatetime, ITDList
from itd.core.logger import get_logger
from itd.core.utils import parse_datetime, to_uuid
from itd.enums import ALL, LoadStatus, NotebookStyle, ParseMode, PostsTab, ReportReason, ReportTargetType, UserPostSorting, ViewReason, ViewSource
from itd.exceptions import NotFoundError
from itd.models.comment import Comment, Comments
from itd.models.file import PostAttach
from itd.models.hashtag import Hashtag
from itd.models.poll import NewPoll, Poll, PollOption
from itd.models.report import Report
from itd.models.span import Span
from itd.models.user import Me, User, _UserBase
from itd.models.utils import ATTACHMENTS, apply_marks, calc_view_duration, format_attachments, parse_html, parse_md, visible_marks

if TYPE_CHECKING:
    from itd.core.client import Client

l = get_logger('post')  # noqa: E741


def _is_alive(ends_at: datetime | None) -> bool:
    return ends_at is None or ends_at > datetime.now(timezone.utc)


class Corrector(ITDBaseModel):
    """Замазанный текст"""

    _post_id: UUID
    id: UUID
    start: int
    end: int
    event_id: str = Field(alias='eventId')
    actor: User
    created_at: ITDdatetime = Field(alias='createdAt')

    def report(self, reason: str = 'Неприемлимая правка', client: Client | None = None):
        report_corrector(client or self.client, str(self._post_id), str(self.id), reason)


class CorrectorState(ITDBaseModel):
    """Состояние замазки в посте"""

    load_status = LoadStatus.FULL
    _post_id: UUID | None = None

    revision: str  # equals to red pens' revision
    server_time: ITDdatetime | None = Field(None, alias='serverTime')
    correctors: list[Corrector] = Field(default_factory=list, alias='marks')
    event_id: str = Field(alias='events')

    @field_validator('event_id', mode='before')
    @classmethod
    def validate_event_id(cls, events):
        return events[0]['id']

    @property
    def my_corrector(self) -> Corrector | None:
        return next((c for c in self.correctors if c.actor.id == self.client.user_id), None)

    def _refresh(self, client: Client):
        return get_event_posts_correctors_state(client, [self._post_id]).json()['data'][str(self._post_id)]

    def cancel(self, client: Client | None = None):
        if self.my_corrector is None:
            raise ValueError('No own red pen claim in this post')
        cancel_corrector(client or self.client, self._post_id)
        self.refresh()

    def apply(self, start: int, end: int, client: Client | None = None) -> Corrector:
        apply_corrector(client or self.client, str(self._post_id), self.event_id, self.revision, start, end)
        self.refresh()
        assert self.my_corrector
        return self.my_corrector

    def _post_refresh(self, context: dict = {}):
        if self._post_id is None:
            self._post_id = context.get('post_id')
        assert self._post_id
        for c in self.correctors:
            c._post_id = self._post_id


class RedPen(BaseModel):
    """Исправленное красной ручкой слово"""

    id: UUID
    start: int
    end: int
    replacement: str
    created_at: ITDdatetime = Field(alias='createdAt')

    def __str__(self) -> str:
        return self.replacement


class RedPenClaim(ITDBaseModel):
    """Пользователи, исопльзовавшие красную ручку в посте"""

    _post_id: UUID
    id: UUID
    event_id: str = Field(alias='eventId')
    actor: User
    is_owner: bool = Field(False, alias='isOwner')
    used: int = 0  # max 3

    def report(self, reason: str = 'Неприемлимая правка', client: Client | None = None):
        report_red_pen(client or self.client, str(self._post_id), str(self.id), reason)


class RedPenState(ITDBaseModel):
    """Состояние исправлений красной ручкой в посте"""

    _post_id: UUID | None = None
    load_status = LoadStatus.FULL

    revision: str
    server_time: ITDdatetime | None = Field(None, alias='serverTime')
    claims: list[RedPenClaim] = Field(default_factory=list)
    red_pens: list[RedPen] = Field(default_factory=list, alias='corrections')
    event_id: str = Field(alias='events')

    @property
    def my_claim(self) -> RedPenClaim | None:
        return next((claim for claim in self.claims if claim.is_owner), None)

    @field_validator('event_id', mode='before')
    @classmethod
    def validate_event_id(cls, events):
        return events[0]['id']

    def cancel(self, client: Client | None = None):
        claim = self.my_claim
        if claim is None:
            raise ValueError('No own red pen claim in this post')
        cancel_red_pen(client or self.client, self._post_id, claim.id)
        self.refresh()

    def _refresh(self, client: Client):
        return get_event_posts_red_pens_state(client, [self._post_id]).json()['data'][str(self._post_id)]

    def _post_refresh(self, context: dict = {}):
        if self._post_id is None:
            self._post_id = context.get('post_id')
        assert self._post_id
        for c in self.claims:
            c._post_id = self._post_id

    def apply(self, start: int, end: int, replacement: str, client: Client | None = None) -> RedPenClaim:
        apply_red_pen(client or self.client, str(self._post_id), self.event_id, self.revision, start, end, replacement)
        self.refresh()
        assert self.my_claim
        return self.my_claim


class Post(ITDBaseModel):
    _entered_at: datetime | None = None

    id: UUID
    author: User
    created_at: Annotated[datetime, BeforeValidator(parse_datetime)] = Field(alias='createdAt')

    content: str
    spans: list[Span] = []
    attachments: list[PostAttach]
    poll: Poll | None = None
    notebook: NotebookStyle | None = None

    corrector: CorrectorState
    red_pen: RedPenState = Field(alias='redPen')

    comments: Comments = Field(default_factory=lambda: Comments(), alias='definitely_not_comments')
    first_comments: list[Comment] = Field([], alias='comments')

    likes_count: int = Field(0, alias='likesCount')
    comments_count: int = Field(0, alias='commentsCount')  # ! Comments + replies, so len(comments) != comments_count
    reposts_count: int = Field(0, alias='repostsCount')
    views_count: int = Field(0, alias='viewsCount')

    edited_at: Annotated[datetime, BeforeValidator(parse_datetime)] | None = Field(None, alias='editedAt')

    is_liked: bool = Field(False, alias='isLiked')
    is_reposted: bool = Field(False, alias='isReposted')
    is_viewed: bool = Field(False, alias='isViewed')
    is_owner: bool = Field(False, alias='isOwner')
    is_pinned: bool = Field(False, alias='isPinned')

    dominant: str | None = Field(None, alias='dominantEmoji')
    original_post: 'Post | None' = Field(None, alias='originalPost')  # for reposts

    wall_recipient_id: UUID | None = Field(None, alias='wallRecipientId')
    wall_recipient: User | None = Field(None, alias='wallRecipient')
    # vs: ViewerSession
    vs: str = Field('')  # from 13.05 it is string token

    def __init__(self, id: str | UUID, source: ViewSource = ViewSource.POST_PAGE, source_context: str | None = None, client: Client | None = None) -> None:
        super().__init__(client)
        self.id = to_uuid(id)
        self.source = source
        self.source_context = source_context
        self.visible = False
        self.comments = Comments(client=client)
        self.comments._post = self
        self._extra_context = {'source': source, 'source_context': source_context, 'post_id': self.id}
        self._init_refresh()

    def for_client(self, client: Client):
        return Post(self.id, client=client)

    def _post_refresh(self, context: dict = {}):
        self.comments._client = self._client  # comments приходит не из данных, а из default_factory, поэтому про клиент не знает
        self.comments._post = self
        if self.is_loaded('first_comments'):  # в списках постов комментариев нет, обычное обращение сходило бы за ними в апи
            for comment in self.first_comments:
                comment._post = self
        for attachment in self.attachments:
            attachment._post = self

    @classmethod
    def new(
        cls,
        content: str | None = None,
        spans: list[Span] = [],
        attachments: ATTACHMENTS = [],
        poll: NewPoll | None = None,
        wall_recipient: UUID | str | User | None = None,
        client: Client | None = None
    ) -> 'Post':
        """Создать новый пост

        Args:
            content (str | None, optional): Содержимое. Defaults to None.
            spans (list[Span], optional): Спаны. Defaults to [].
            wall_recipient (UUID | str | User | None, optional): Получатель (для постов на чужой стене). Defaults to None.
            attachments (ATTACHMENTS, optional): Вложения. Defaults to [].
            poll (NewPoll | None, optional): Опрос. Defaults to None.
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            Post: Пост
        """
        instance = cls.__new__(cls)
        super(Post, instance).__init__(client)

        if isinstance(wall_recipient, User):
            wall_recipient = wall_recipient.id
        elif wall_recipient is not None:
            wall_recipient = to_uuid(wall_recipient)

        if (client or instance.client).config.parse_mode == ParseMode.HTML and not spans and content:
            content, spans = parse_html(content)
        if (client or instance.client).config.parse_mode == ParseMode.MARKDOWN and not spans and content:
            content, spans = parse_md(content)

        post = create_post(
            instance._client, content, [span.model_dump(mode='json') for span in spans], wall_recipient, format_attachments(attachments), poll
        ).json()

        return cls.from_dict(post, source=ViewSource.PROFILE, client=client)

    @classmethod
    def from_dict(
        cls,
        data: dict,
        source: ViewSource = ViewSource.POST_PAGE,
        source_context: str | None = None,
        *,
        context: dict | None = None,
        client: Client | None = None
    ) -> 'Post':
        context = dict(context or {})
        context.update({'source': source, 'source_context': source_context})
        instance = super().from_dict(data, context=context, client=client)
        instance._extra_context = {'source': source, 'source_context': source_context, 'post_id': instance.id}
        instance.source = source
        instance.source_context = source_context
        instance.visible = False

        return instance

    def vote(self, options: list[str | UUID | PollOption] | str | UUID | PollOption, client: Client | None = None) -> None:
        assert self.poll, 'No poll'
        self.poll.vote(options, client or self.client)

    def _refresh(self, *, client: Client):
        return get_post(client, self.id).json()['data']

    def __str__(self) -> str:
        return self.content

    def __int__(self) -> int:
        return self.likes_count

    def __hash__(self):
        return int(self.id)

    def __eq__(self, other) -> bool:
        if isinstance(other, Post):
            return self.id == other.id
        return False

    def __contains__(self, item) -> bool:
        return item in self.content

    def __lt__(self, other) -> bool:
        if isinstance(other, Post):
            return self.created_at < other.created_at
        return NotImplemented

    def __gt__(self, other) -> bool:
        if isinstance(other, Post):
            return self.created_at > other.created_at
        return NotImplemented

    def __len__(self) -> int:
        return len(self.content)

    def like(self, client: Client | None = None) -> int:
        """Лайкнуть пост

        Args:
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            int: Количество лайков после лайка
        """
        likes = like_post(client or self.client, self.id).json()['likesCount']
        self.likes_count = likes
        if (client or self.client) == self.client:
            self.is_liked = True
        return likes

    def unlike(self, client: Client | None = None) -> int:
        """Убрать лайк с поста

        Args:
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            int: Количество лайков после убирания лайка
        """
        likes = unlike_post(client or self.client, self.id).json()['likesCount']
        self.likes_count = likes
        if (client or self.client) == self.client:
            self.is_liked = False
        return likes

    def repost(self, content: str | None = None, client: Client | None = None) -> 'Post':
        """Репостнуть пост

        Args:
            content (str | None, optional): Содержимое. Defaults to None.
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            Post: Пост
        """
        post = repost(client or self.client, self.id, content).json()
        if 'reposts_count' in self._loaded_attrs:
            self.reposts_count += 1
        if (client or self.client) == self.client:
            self.is_reposted = True

        return Post.from_dict(post, client=client)

    def view(
        self, entered_at: datetime | None = None, exited_at: datetime | None = None, reason: ViewReason = ViewReason.NORMAL, *, client: Client | None = None
    ) -> None:
        """Просмотреть пост

        Args:
            entered_at (datetime | None, optional): Дата открытия поста (когда пользователь увидел верхнюю границу поста). Если None, ставится datetime.now - 5000. Defaults to None.
            exited_at (datetime | None, optional): Дата скрытия поста (когда пост пропал из зоны видимости). Если None, ставится datetime.now. Defaults to None.
            reason (ViewReason, optional): Причина просмотра. Defaults to ViewReason.NORMAL.
            client (Client | None, optional): Клиент. Defaults to None.
        """
        c = client or self.client

        if c.config.dwell_wait_durations:
            sleep(calc_view_duration(c.config, self.content, self.attachments) / 1000)

        entered_at_autofill = entered_at is None
        exited_at_autofill = exited_at is None
        if exited_at_autofill:
            exited_at = datetime.now()
        if entered_at_autofill:
            entered_at = exited_at - timedelta(milliseconds=calc_view_duration(c.config, self.content, self.attachments))

        duration = round((exited_at.timestamp() - entered_at.timestamp()) * 1000)
        l.debug(
            'view post id=%s entered_at=%s%s exited_at=%s%s reason=%s',
            self.id,
            entered_at.strftime('%X.%f'),
            ' (autofill)' if entered_at_autofill else '',
            exited_at.strftime('%X.%f'),
            ' (autofill)' if exited_at_autofill else '',
            reason.name.lower()
        )
        if duration < c.config.dwell_min_duration:
            l.warning('skip post view id=%s duration=%s (min is %s)', self.id, duration, c.config.dwell_min_duration)
            return

        c.dwell_tracker.record_view(self.id, self.vs, duration, entered_at, exited_at, self.source, self.source_context, reason)

        if c == self.client:
            self.is_viewed = True
        if c.config.post_view_increment and 'views_count' in self._loaded_attrs:
            self.views_count += 1

    def pin(self, client: Client | None = None) -> None:
        """Закрепить пост

        Args:
            client (Client | None, optional): Клиент. Defaults to None.
        """
        pin_post(client or self.client, self.id)
        self.is_pinned = True
        (client or self.client).user.pinned_post_id = self.id

    def unpin(self, client: Client | None = None) -> None:
        """Открепить пост

        Args:
            client (Client | None, optional): Клиент. Defaults to None.
        """
        unpin_post(client or self.client, self.id)
        self.is_pinned = False
        (client or self.client).user.pinned_post_id = None

    def delete(self, client: Client | None = None) -> None:
        """Удалить пост

        Args:
            client (Client | None, optional): Клиент. Defaults to None.
        """
        delete_post(client or self.client, self.id)

    # def __del__(self) -> None:
    #     self.delete()

    def restore(self, client: Client | None = None) -> None:
        """Вернуть удаленный пост

        Args:
            client (Client | None, optional): Клиент. Defaults to None.
        """
        restore_post(client or self.client, self.id)

    def edit(self, content: str, spans: list[Span] = [], client: Client | None = None) -> datetime:
        """Редактировать пост

        Args:
            content (str): Содержимое
            spans (list[Span], optional): Спаны. Defaults to [].
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            datetime: Время обновления (updatedAt)
        """
        if (client or self.client).config.parse_mode == ParseMode.HTML and not spans:
            content, spans = parse_html(content)
        if (client or self.client).config.parse_mode == ParseMode.MARKDOWN and not spans:
            content, spans = parse_md(content)

        updated_at = parse_datetime(edit_post(client or self.client, self.id, content, [span.model_dump(mode='json') for span in spans]).json()['updatedAt'])
        self.edited_at = updated_at
        self.content = content
        self.spans = spans
        return updated_at

    def add_comment(self, content: str | None = None, attachments: ATTACHMENTS = [], client: Client | None = None) -> Comment:
        """Создать комментарий

        Args:
            content (str | None, optional): Содержимое. Defaults to None.
            attachments (list[UUID | str], optional): Вложения. Defaults to [].
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            Comment: Комментарий
        """
        comment = self.comments.new(content, attachments, client or self.client)
        if 'comments_count' in self._loaded_attrs:
            self.comments_count += 1
        return comment

    def report(self, reason: ReportReason, description: str | None = None, client: Client | None = None) -> Report:
        return Report(self.id, ReportTargetType.POST, reason, description, client or self.client)

    def mask_content(self, mark_char: str = '■') -> str:
        if not self.correctors:
            return self.content
        return apply_marks(self.content, visible_marks(self.correctors, self.red_pens), mark_char)

    @property
    def correctors(self) -> list[Corrector]:
        return self.corrector.correctors

    @property
    def red_pens(self) -> list[RedPen]:
        return self.red_pen.red_pens

    @property
    def event_revision(self) -> str:
        return self.red_pen.revision  # or corrector.revision

    def apply_corrector(self, start: int, end: int, client: Client | None = None) -> None:
        """Замазать фрагмент текста корректором (только в чужом посте)

        Args:
            start (int): Начало фрагмента
            end (int): Конец фрагмента
            client (Client | None, optional): Клиент. Defaults to None.
        """
        self.corrector.apply(start, end, client=client or self.client)

    def apply_red_pen(self, start: int, end: int, replacement: str, client: Client | None = None) -> None:
        """Исправить слово красной ручкой (только в чужом посте)

        Args:
            start (int): Начало слова
            end (int): Конец слова
            replacement (str): Новое слово
            client (Client | None, optional): Клиент. Defaults to None.
        """
        self.red_pen.apply(start, end, replacement, client=client or self.client)

    def cancel_corrector(self, client: Client | None = None) -> None:
        """Убрать свои замазки корректором с поста"""
        self.corrector.cancel(client or self.client)

    def cancel_red_pen(self, client: Client | None = None) -> None:
        """Убрать свои правки красной ручкой"""
        self.red_pen.cancel(client or self.client)

    def report_corrector(self, mark: Corrector | str | UUID, reason: str = 'Неприемлемая правка', client: Client | None = None) -> None:
        """Пожаловаться на замазку корректором"""
        report_corrector(client or self.client, self.id, mark.id if isinstance(mark, Corrector) else mark, reason)

    def report_red_pen(self, claim: RedPenClaim | str | UUID, reason: str = 'Неприемлемая правка', client: Client | None = None) -> None:
        """Пожаловаться на правки красной ручкой"""
        report_red_pen(client or self.client, self.id, claim.id if isinstance(claim, RedPenClaim) else claim, reason)

    def set_visible(self, client: Client | None = None):
        if not self.visible:
            l.debug('set visible id=%s', self.id)
            self.visible = True

            self._entered_at = datetime.now()
            (client or self.client).visible_posts.append(self)
        else:
            l.warning('set_visible called on already visible post')

    def set_invisible(self, reason: ViewReason = ViewReason.NORMAL, client: Client | None = None):
        if self.visible:
            l.debug('set invisible id=%s reason=%s', self.id, reason.name.lower())
            self.visible = False

            (client or self.client).visible_posts.remove(self)
            if self._entered_at and (client or self.client).config.post_auto_view:
                self.view(self._entered_at, reason=reason, client=client or self.client)
        else:
            l.warning('set_invisible called on already invisible post')

    def on_stats_update(self):
        pass  # override this

    def update_stats(self, client: Client | None = None):
        stats = get_stats(client or self.client, [self.id]).json().get('posts', [])
        if not stats:
            raise NotFoundError('Post')
        self._set_stats(stats[0])

    def _set_stats(self, stats: dict):
        fields = {value.alias or name: name for name, value in self._pydantic_model.model_fields.items()}
        for name, value in stats.items():
            if name in fields:
                setattr(self, fields[name], value)
        self.on_stats_update()

    @property
    def url(self) -> str:
        return f'https://xn--d1ah4a.com/@{self.author.username}/post/{self.id}'

    @property
    def link(self) -> str:
        return self.url

    @field_validator('notebook', mode='before')
    @classmethod
    def validate_notebook(cls, notebook: dict | None):
        if notebook:
            return notebook.get('style')


class _BasePosts(ITDList[Post]):
    source: ViewSource
    source_context: str | None = None

    @staticmethod
    def _get_cursor(data: dict):
        return data['pagination']['nextCursor']

    @staticmethod
    def _get_has_more(data: dict):
        return data['pagination']['hasMore']

    @staticmethod
    def _get_objects(data: dict) -> list[dict]:
        return data['posts']

    def _to_models(self, objects: list, client: Client):
        return [Post.from_dict(post, self.source, self.source_context, client=client) for post in objects]

    def __setattr__(self, name: str, value) -> None:
        if name == '_client':
            for post in self.copy():
                post._client = value
        super().__setattr__(name, value)


class Posts(_BasePosts):
    cursor: str | datetime | None = None

    def __init__(self, tab: PostsTab = PostsTab.POPULAR, client: Client | None = None) -> None:
        super().__init__(client)
        self.tab = tab
        match tab:
            case PostsTab.POPULAR:
                self.source = ViewSource.FEED_GLOBAL
            case PostsTab.FOLLOWING:
                self.source = ViewSource.FEED_FOLLOWING
            case PostsTab.CLAN:
                self.source = ViewSource.FEED_CLAN

    def _fetch(self, client: Client, limit: int) -> dict:
        return get_posts(client, self.cursor, limit, self.tab).json()['data']

    @classmethod
    def popular(cls, client: Client | None = None):  # i think no one will use it (cuz it is equals just to "Posts()") but why not
        return cls(PostsTab.POPULAR, client)

    @classmethod
    def trending(cls, client: Client | None = None):  # same as "popular"
        return cls.popular(client)

    @classmethod
    def following(cls, client: Client | None = None):
        return cls(PostsTab.FOLLOWING, client)

    @classmethod
    def clan(cls, client: Client | None = None):
        return cls(PostsTab.CLAN, client)


class UserPosts(_BasePosts):
    _load_with_parent = False
    cursor: datetime | None = None
    source = ViewSource.PROFILE

    # ! not includes posts from other users (wall posts)
    # def _get_total(self, data: dict):
    #     return self.user.posts_count

    def __init__(self, user: str | UUID | _UserBase, sorting: UserPostSorting = UserPostSorting.NEW, client: Client | None = None) -> None:
        super().__init__(client)
        if isinstance(user, Me):
            self.user = user.to_user()
        elif isinstance(user, User):
            self.user = user
        elif isinstance(user, str | UUID):
            self.user = User(user, client)
        else:
            raise ValueError('User must be instance of User or Me class')

        self.sorting = sorting  # sort is busy
        self._force_remove_pinned_post: bool = False

    @property
    def source_context(self):
        return str(self.user.id)

    def _fetch(self, client: Client, limit: int) -> dict:
        if self.sorting == UserPostSorting.NEW and client.config.userposts_add_pinned_post and not self._force_remove_pinned_post:
            return get_user_posts(client, self.user._identifier, self.cursor, limit, self.user.pinned_post_id, self.sorting).json()['data']
        return get_user_posts(client, self.user._identifier, self.cursor, limit, sort=self.sorting).json()['data']  # you dont need pinned post for popular

    @classmethod
    def popular(cls, user: str | UUID | _UserBase, client: Client | None = None):
        return cls(user, UserPostSorting.POPULAR, client)

    @classmethod
    def new(cls, user: str | UUID | _UserBase, client: Client | None = None):
        return cls(user, UserPostSorting.NEW, client)

    def wait_for_post(self, delay: float = 5, include_pinned_post: bool = False) -> Post:
        self._force_remove_pinned_post = not include_pinned_post
        post = self[0] if self else None
        l.info('userposts wait_for_post init')
        while True:
            sleep(delay)
            l.debug('userposts wait_for_post check for new posts')
            self.refresh(1)
            if (self[0].id if self else None) != (post.id if post is not None else None):
                l.debug('userposts wait_for_post found diff old=%s new=%s', (post.id if post is not None else None), self[0].id)
                self._force_remove_pinned_post = include_pinned_post
                return self[0]


class LikedPosts(_BasePosts):  # [] if forbidden
    _load_with_parent = False
    cursor: datetime | None = None  # actually datetime but in runtime its string
    source = ViewSource.PROFILE

    def __init__(self, user: str | UUID | _UserBase, client: Client | None = None) -> None:
        super().__init__(client)
        if isinstance(user, _UserBase):
            self.user = user
        else:
            self.user = User(user)

    def _fetch(self, client: Client, limit: int) -> dict:
        return get_liked_posts(client, self.user._identifier, self.cursor, limit).json()['data']

    @staticmethod
    def _get_has_more(data: dict):
        return data['pagination']['hasMore']

    def wait_for_post(self, delay: float = 5) -> Post:
        post = self[0] if self else None
        l.info('likedposts wait_for_post init')
        while True:
            sleep(delay)
            l.debug('likedposts wait_for_post check for new posts')
            self.refresh(1)
            if (self[0].id if self else None) != (post.id if post is not None else None):
                l.debug('likedposts wait_for_post found diff old=%s new=%s', (post.id if post is not None else None), self[0].id)
                return self[0]


class HashtagPosts(_BasePosts):
    hashtag: Hashtag
    cursor: UUID | None = None
    source = ViewSource.HASHTAG

    def __init__(self, hashtag: Hashtag | str, client: Client | None = None) -> None:
        super().__init__(client)

        if isinstance(hashtag, str):
            hashtag = Hashtag(hashtag, self.client)
        self.hashtag = hashtag
        self.source_context = self.hashtag.name

    def _fetch(self, client: Client, limit: int) -> dict:
        return get_posts_by_hashtag(client, self.hashtag.name, self.cursor, limit).json()['data']

    def _to_models(self, objects: list, client: Client):
        return [Post.from_dict(post, self.source, self.source_context, client=client) for post in objects]

    def _get_total(self, data: dict):
        return data['hashtag']['postsCount']

    @staticmethod
    def _get_has_more(data: dict):
        return data['pagination']['hasMore']

    @overload
    def wait_for_posts(self, delay: float, *, client: Client | None) -> list[Post]: ...

    @overload
    def wait_for_posts(self, delay: float, find_post: Literal[True], client: Client | None) -> list[Post]: ...

    @overload
    def wait_for_posts(self, delay: float, find_post: Literal[False], client: Client | None) -> None: ...

    def wait_for_posts(self, delay: float = 5, find_post: bool = True, client: Client | None = None) -> list[Post] | None:
        count = self.hashtag.posts_count

        posts = set([post.id for post in self]) if find_post else ()

        l.info('hashtagposts wait_for_post init')
        while True:
            sleep(delay)
            l.debug('hashtagposts wait_for_post check for new posts')
            self.hashtag.refresh(client=client)
            if count < self.hashtag.posts_count:
                l.info('hashtagposts wait_for_post found diff old=%s new=%s', count, self.hashtag.posts_count)
                if find_post:
                    self.refresh(ALL, client=client)
                    l.debug('%s %s', [post.id for post in self], posts)
                    return [post for post in self if post.id not in posts]
                return
            count = self.hashtag.posts_count

    def wait_for_post(self, delay: float = 5, client: Client | None = None) -> Post | None:
        return self.wait_for_posts(delay, client=client)[0]
