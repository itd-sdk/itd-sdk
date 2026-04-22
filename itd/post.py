from uuid import UUID
from datetime import datetime

from pydantic import Field, BaseModel, field_validator

from itd.base import ITDBaseModel, refresh_wrapper, ITDList
from itd.client import Client
from itd.comment import Comment, Comments
from itd.enums import PostsTab, UserPostSorting, ReportReason, ReportTargetType
from itd.file import PostAttach
from itd.hashtag import Hashtag
from itd.poll import Poll, NewPoll, PollOption
from itd.report import Report
from itd.span import Span
from itd.user import User, _UserBase
from itd.utils import to_uuid, parse_datetime, format_attachments, ATTACHMENTS
from itd.routes.posts import (
    get_post, create_post, like_post, unlike_post, repost, view_post, pin_post, unpin_post,
    delete_post, restore_post, edit_post, get_posts, get_user_posts, get_liked_posts
)
from itd.routes.hashtags import get_posts_by_hashtag



class _BasePost(ITDBaseModel):
    id: UUID
    author: User
    created_at: datetime = Field(alias='createdAt')

    content: str
    spans: list[Span] = []
    attachments: list[PostAttach]
    comments: Comments = Field(default_factory=lambda: Comments())

    likes_count: int = Field(0, alias='likesCount')
    comments_count: int = Field(0, alias='commentsCount') # ! Comments + replies, so len(comments) != comments_count
    reposts_count: int = Field(0, alias='repostsCount')
    views_count: int = Field(0, alias='viewsCount')


    @refresh_wrapper
    def refresh(self, client: Client | None = None):
        return get_post(client or self.client, self.id).json()['data']


    def __str__(self) -> str:
        return self.content

    def __int__(self) -> int:
        return self.likes_count

    def __eq__(self, other) -> bool:
        if isinstance(other, _BasePost):
            return self.id == other.id
        return False

    def __ne__(self, other) -> bool:
        if isinstance(other, _BasePost):
            return self.id != other.id
        return True

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
        post['author'] = None
        self.reposts_count += 1

        return Post._from_dict(post, client=client)

    def view(self, client: Client | None = None) -> None:
        """Просмотреть пост

        Args:
            client (Client | None, optional): Клиент. Defaults to None.
        """
        view_post(client or self.client, self.id)
        # post can be already viewed, so view will not add; thats why do not change views_count

    def pin(self, client: Client | None = None) -> None:
        """Закрепить пост

        Args:
            client (Client | None, optional): Клиент. Defaults to None.
        """
        pin_post(client or self.client, self.id)

    def unpin(self, client: Client | None = None) -> None:
        """Открепить пост

        Args:
            client (Client | None, optional): Клиент. Defaults to None.
        """
        unpin_post(client or self.client, self.id)

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
        updated_at = parse_datetime(edit_post(client or self.client, self.id, content, [span.model_dump(mode="json") for span in spans]).json()['updatedAt'])
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
        self.comments_count += 1
        return comment

    def report(self, reason: ReportReason, description: str | None = None, client: Client | None = None) -> Report:
        return Report(self.id, ReportTargetType.POST, reason, description, client or self.client)

    @property
    def url(self) -> str:
        return f'https://xn--d1ah4a.com/@{self.author.username}/post/{self.id}'



class Post(_BasePost):
    _validator = lambda _: _PostValidate

    id: UUID

    poll: Poll | None = None
    edited_at: datetime | None = Field(None, alias='editedAt')

    is_liked: bool = Field(False, alias='isLiked')
    is_reposted: bool = Field(False, alias='isReposted')
    is_viewed: bool = Field(False, alias='isViewed')
    is_owner: bool = Field(False, alias='isOwner')
    is_pinned: bool | None = Field(None, alias='isPinned')  # only for user wall

    dominant: str | None = Field(None, alias='dominantEmoji')
    original_post: 'OriginalPost | None' = Field(None, alias='originalPost')  # for reposts

    wall_recipient_id: UUID | None = Field(None, alias='wallRecipientId')
    wall_recipient: User | None = Field(None, alias='wallRecipient')


    def __init__(self, id: str | UUID, client: Client | None = None) -> None:
        self.id = to_uuid(id)
        super().__init__(client)


    @classmethod
    def new(
        cls,
        content: str | None = None,
        spans: list[Span] = [],
        wall_recipient: UUID | str | User | None = None,
        attachments: ATTACHMENTS = [],
        poll: NewPoll | None = None,
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

        post = create_post(
            instance._client,
            content, [span.model_dump(mode="json") for span in spans],
            wall_recipient,
            format_attachments(attachments),
            poll
        ).json()

        post['author'] = None # author is loaded lazily on access via __getattribute__

        validated = _PostValidate.model_validate(post)
        instance._fields_from_data = validated.model_fields_set
        for name, value in validated.__dict__.items():
            setattr(instance, name, value)

        instance._loaded = True

        return instance

    @classmethod
    def _from_dict(cls, data: dict, set_loaded: bool = True, client: Client | None = None) -> 'Post':
        instance = cls.__new__(cls)
        super(Post, instance).__init__(client)

        validated = _PostValidate.model_validate(data)
        instance._fields_from_data = validated.model_fields_set
        for name, value in validated.__dict__.items():
            setattr(instance, name, value)

        instance._loaded = set_loaded
        return instance


    def like(self, client: Client | None = None) -> int:
        count = super().like(client)
        self.is_liked = True
        return count

    def unlike(self, client: Client | None = None) -> int:
        count = super().unlike(client)
        self.is_liked = False
        return count

    def repost(self, content: str | None = None, client: Client | None = None) -> 'Post':
        post = super().repost(content, client)
        self.is_reposted = True
        return post

    def pin(self, client: Client | None = None) -> None:
        super().pin(client)
        self.is_pinned = True
        self.client.user.pinned_post_id = self.id # TODO

    def unpin(self, client: Client | None = None) -> None:
        super().unpin(client)
        self.is_pinned = False
        self.client.user.pinned_post_id = None # TODO

    def edit(self, content: str, spans: list[Span] = [], client: Client | None = None) -> datetime:
        updated_at = super().edit(content, spans, client)
        self.edited_at = updated_at
        return updated_at

    def vote(self, options: list[str | UUID | PollOption] | str | UUID | PollOption, client: Client | None = None) -> None:
        assert self.poll, 'No poll'
        self.poll.vote(options, client or self.client)


    def __getattribute__(self, name: str):
        if name == 'author':
            try:
                author = object.__getattribute__(self, 'author')
            except AttributeError:
                author = None
            if author is None:
                client = object.__getattribute__(self, '_client')
                if client is not None:
                    object.__setattr__(self, 'author', client.user)

        value = super().__getattribute__(name)
        if name == 'comments' and getattr(value, '_post_id', None) is None:
            value._post_id = self.id
        return value



class _PostValidate(BaseModel, Post): # BaseModel MUST be first or you ll have some problems with init
    @field_validator('edited_at', mode='plain')
    @classmethod
    def validate_edited_at(cls, v: str | None):
        if v is None:
            return
        return parse_datetime(v)

    @field_validator('created_at', mode='plain')
    @classmethod
    def validate_created_at(cls, v: str):
        return parse_datetime(v)

    @field_validator('original_post', mode='plain')
    @classmethod
    def validate_original_post(cls, post: dict | None = None):
        if post is None:
            return
        return OriginalPost(post)

    @field_validator('poll', mode='plain')
    @classmethod
    def validate_poll(cls, poll: dict | None = None):
        if poll is None:
            return
        return Poll(poll)

    @field_validator('comments', mode='plain')
    @classmethod
    def validate_comments(cls, comments: list[dict]):
        return Comments(comments)

    @field_validator('author', mode='plain')
    @classmethod
    def validate_author(cls, author: dict | _UserBase | None):
        if author is None:
            return None
        if isinstance(author, _UserBase):
            return author
        return User._from_dict(author, False)

    @field_validator('wall_recipient', mode='plain')
    @classmethod
    def validate_wall_recipient(cls, wall_recipient: dict | None):
        if wall_recipient is not None:
            return User._from_dict(wall_recipient, False)




class OriginalPost(_BasePost):
    is_deleted: bool = Field(False, alias='isDeleted')

    _validator = lambda _: _OriginalPostValidate

    def __init__(self, post: dict, client: Client | None = None) -> None:
        super().__init__(client)

        validated = _OriginalPostValidate.model_validate(post)
        self._fields_from_data = validated.model_fields_set
        for name, value in validated.__dict__.items():
            setattr(self, name, value)
        self._loaded = True

    def delete(self, client: Client | None = None) -> None:
        super().delete(client)
        self.is_deleted = True

    def restore(self, client: Client | None = None) -> None:
        super().restore(client)
        self.is_deleted = False

    def to_post(self, client: Client | None = None) -> Post:
        instance = Post.__new__(Post)
        super(Post, instance).__init__(client or self.client)

        for name, value in self.__dict__.items():
            setattr(instance, name, value)


        return instance


class _OriginalPostValidate(BaseModel, OriginalPost):
    @field_validator('created_at', mode='plain')
    @classmethod
    def validate_created_at(cls, v: str):
        return parse_datetime(v)

    @field_validator('comments', mode='plain')
    @classmethod
    def validate_comments(cls, comments: list[dict]):
        return Comments(comments)

    @field_validator('author', mode='plain')
    @classmethod
    def validate_author(cls, author: dict):
        return User._from_dict(author, False)



class _BasePosts(ITDList, list[Post]):
    _limit = 50

    @staticmethod
    def _get_cursor(data: dict):
        return data['pagination']['nextCursor']

    @staticmethod
    def _get_has_more(data: dict):
        return data['pagination']['hasMore']

    @staticmethod
    def _get_objects(data: dict) -> list[dict]:
        return data['posts']

    def _extend(self, objects: list, client: Client):
        self.extend([Post._from_dict(post, client=client) for post in objects])

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

    def _fetch(self, client: Client, limit: int) -> dict:
        return get_posts(client, self.cursor, limit, self.tab).json()['data']

    @classmethod
    def popular(cls, client: Client | None = None): # i think no one will use it (cuz it is equals just to "Posts()") but why not
        return cls(PostsTab.POPULAR, client)

    @classmethod
    def trending(cls, client: Client | None = None): # same as "popular"
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

    # def _get_total(self, data: dict):
    #     return self.user.posts_count

    def __init__(self, user: str | UUID | _UserBase, sorting: UserPostSorting = UserPostSorting.NEW, client: Client | None = None) -> None:
        super().__init__(client)
        if isinstance(user, _UserBase):
            self.user = user
        else:
            self.user = User(user, client)

        self.sorting = sorting # sort is busy

    def _fetch(self, client: Client, limit: int) -> dict:
        if self.sorting == UserPostSorting.NEW and client.config.userposts_add_pinned_post:
            return get_user_posts(client, self.user._identifier, self.cursor, limit, self.user.pinned_post_id, self.sorting).json()['data']
        return get_user_posts(client, self.user._identifier, self.cursor, limit, sort=self.sorting).json()['data'] # you dont need pinned post for popular -_-

    @classmethod
    def popular(cls, user: str | UUID | _UserBase, client: Client | None = None):
        return cls(user, UserPostSorting.POPULAR, client)

    @classmethod
    def new(cls, user: str | UUID | _UserBase, client: Client | None = None):
        return cls(user, UserPostSorting.NEW, client)


class LikedPosts(_BasePosts): # [] if forbidden
    _load_with_parent = False
    cursor: datetime | None = None # actually datetime but in runtime its string

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


class HashtagPosts(_BasePosts):
    hashtag: Hashtag
    cursor: UUID | None = None

    def __init__(self, hashtag: Hashtag | str, client: Client | None = None) -> None:
        super().__init__(client)

        if isinstance(hashtag, str):
            hashtag = Hashtag(hashtag, self.client)
        self.hashtag = hashtag

    def _fetch(self, client: Client, limit: int) -> dict:
        return get_posts_by_hashtag(client, self.hashtag.name, self.cursor, limit).json()['data']

    def _extend(self, objects: list, client: Client):
        self.extend([Post._from_dict(post, False, client=client) for post in objects])

    def _get_total(self, data: dict):
        return data['hashtag']['postsCount']

    @staticmethod
    def _get_has_more(data: dict):
        return data['pagination']['hasMore']