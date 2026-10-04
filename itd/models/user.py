from __future__ import annotations

from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING, Annotated, Literal, overload
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field

from itd.api.pins import get_pins, remove_pin
from itd.api.portal import get_event_balance, get_event_correctors_inventory, get_event_profile, get_event_red_pens_inventory, get_my_event_inventory
from itd.api.search import search
from itd.api.subscription import get_payment_methods, get_subscription, pay_subscription, toggle_subscription_auto_renewal
from itd.api.users import (
    block,
    delete_account,
    follow,
    get_blocked,
    get_followers,
    get_following,
    get_privacy,
    get_profile,
    get_user,
    get_who_to_follow,
    restore_account,
    unblock,
    unfollow,
    update_privacy,
    update_profile
)
from itd.api.users import get_follow_status as _get_follow_status
from itd.core.base import ITDBaseModel, ITDList
from itd.core.default import get_default_client
from itd.core.utils import parse_datetime, to_uuid
from itd.enums import AccessType, EventItemType, LastSeenUnit, LoadStatus, ReportReason, ReportTargetType, Role, Unset
from itd.exceptions import AccountDeletedError, NotFoundError, PinNotOwnedError
from itd.models.file import File
from itd.models.pin import Pin
from itd.models.poll import NewPoll
from itd.models.report import Report
from itd.models.span import Span
from itd.models.utils import ATTACHMENTS

if TYPE_CHECKING:
    from itd.core.client import Client
    from itd.models.post import LikedPosts, Post, UserPosts


class ProfileUser(BaseModel):
    id: UUID
    username: str
    display_name: str = Field(alias='displayName')
    avatar: str
    verified: bool = False
    bio: str | None = None
    is_phone_verified: bool = Field(False, alias='isPhoneVerified')
    roles: list[Role] = [Role.USER]

    def __str__(self) -> str:
        return self.display_name


class Profile(ITDBaseModel):
    _load_with_parent = False

    authenticated: bool = True
    user: ProfileUser | None = None
    banned: bool = False
    deleted: bool = False
    can_restore: bool = Field(True, alias='canRestore')
    message: str | None = None
    profile_required: bool = Field(False, alias='profileRequired')
    user_id: UUID | None = Field(None, alias='userId')
    roles: list[Role] | None = None

    def _refresh(self, *, client: Client):
        return get_profile(client).json()

    def __str__(self) -> str:
        if self.user:
            return str(self.user)
        return super().__str__()


class Privacy(ITDBaseModel):
    _user: 'Me | None' = None
    _load_with_parent = False
    _autorefresh_on_init = False

    is_private: bool = Field(alias='isPrivate')
    wall_access: AccessType = Field(alias='wallAccess')
    likes_visibility: AccessType = Field(alias='likesVisibility')
    show_last_seen: bool = Field(alias='showLastSeen')

    def _refresh(self, *, client: Client):
        return get_privacy(client).json()

    def update(
        self,
        is_private: bool | None = None,
        wall_access: AccessType | None = None,
        likes_visibility: AccessType | None = None,
        show_last_seen: bool | None = None,
        client: Client | None = None
    ):
        data = update_privacy(client or self.client, is_private, wall_access, likes_visibility, show_last_seen).json()
        if 'isPrivate' in data:
            self.is_private = data['isPrivate']
        if 'wallAccess' in data:
            self.wall_access = AccessType(data['wallAccess'])
        if 'likesVisibility' in data:
            self.likes_visibility = AccessType(data['likesVisibility'])
        if 'showLastSeen' in data:
            self.show_last_seen = data['showLastSeen']

        if self._user:
            for field in ('wall_access', 'likes_visibility', 'is_private'):
                setattr(self._user, field, object.__getattribute__(self, field))

    def update_from_fields(self):  # you can update fields (like privacy.is_private = True), then exec this func to update
        self.update(self.is_private, self.wall_access, self.likes_visibility, self.show_last_seen)


class Subscription(ITDBaseModel):
    _payment_methods: list
    _refreshable = False

    active: bool = Field(False, alias='isActive')
    expires_at: Annotated[datetime, BeforeValidator(parse_datetime)] | None = Field(None, alias='expiresAt')
    auto_renewal: bool = Field(True, alias='autoRenewal')

    def _refresh(self, *, client: Client):  # refreshes only is_active
        return get_subscription(client).json()

    def pay(self):
        return pay_subscription(self.client).json()['confirmationUrl']

    def set_auto_renewal(self, enabled: bool) -> bool:
        self.auto_renewal = toggle_subscription_auto_renewal(self.client, enabled).json()['autoRenewal']
        return self.auto_renewal

    def toggle_auto_renewal(self) -> bool:
        return self.set_auto_renewal(not self.auto_renewal)

    @cached_property
    def payment_methods(self):
        return get_payment_methods(self.client).json()['data']

    def __bool__(self):
        return self.active

    def __str__(self) -> str:
        return str(self.active)


class Nickname(BaseModel):
    id: str
    label: str
    style: str = Field(alias='styleKey')
    event_id: str = Field(alias='eventId')
    expires_at: datetime = Field(alias='expiresAt')
    state_version: int = Field(0, alias='stateVersion')

    def __str__(self):
        return self.label


class EventProfileWindow(ITDBaseModel):
    broken: bool = False
    asset: str | None = None
    broken_at: datetime | None = Field(None, alias='brokenAt')


class EventProfileCurtains(ITDBaseModel):
    amount: int = Field(alias='fund')
    goal: int = 100
    available: bool = Field(False, alias='hasCuratins')
    closed: bool = False


class EventAnchor(BaseModel):
    type: Literal['banner', 'profile_header', 'post'] = Field(alias='kind')
    id: UUID | None = None


class EventSticker(ITDBaseModel):
    id: UUID
    type: Literal['sticker'] = Field(alias='kind')
    asset: str
    x: float
    y: float
    z: float
    size: float
    angle: float
    # wear: Literal[0]
    anchor: EventAnchor
    created_at: datetime = Field(alias='createdAt')
    author: UUID = Field(alias='createdBy')


class EventBalloon(BaseModel):
    id: UUID
    x: float
    y: float
    angle: float
    created_at: datetime = Field(alias='thrownAt')
    author: UUID = Field(alias='thrownBy')
    expires_at: datetime = Field(alias='expiresAt')
    anchor: EventAnchor


class EventProfile(ITDBaseModel):
    id: UUID = Field(alias='profileId')
    revision: int = Field(alias='rev')
    # banner: EventProfileBanner # фронт не сомтрит на это + у всех одинаково это поле
    window: EventProfileWindow
    curtains: EventProfileCurtains
    aura: int | None = None
    nickname: str | None = None
    stickers: list[EventSticker] = Field(default_factory=list, alias='placements')
    balloons: list[EventBalloon] = Field(default_factory=list)

    def __init__(self, id: str | UUID, *, client: Client | None = None):
        super().__init__(client=client)
        self.id = to_uuid(id)

    def _refresh(self, client: Client):
        return get_event_profile(client, self.id).json()


class EventItem(BaseModel):
    id: str  # inventoryItemId
    type: EventItemType = Field(alias='kind')
    asset: str | None = None  # /public/events/aliceai/<asset>


class LastSeen(BaseModel):
    unit: LastSeenUnit
    value: int | None = None

    def __str__(self):
        match self.unit:
            case LastSeenUnit.JUST_NOW:
                return 'только что'
            case LastSeenUnit.RECENTLY:
                return 'недавно'
            case LastSeenUnit.MINUTES:
                return f'{self.value} минут назад'
            case LastSeenUnit.HOURS:
                return f'{self.value} часов назад'
            case LastSeenUnit.THIS_WEEK:
                return 'на этой неделе'
            case LastSeenUnit.THIS_MONTH:
                return 'в этом месяце'
            case LastSeenUnit.LONG_AGO:
                return 'давно'  # гавно


class _UserBase(ITDBaseModel):
    _identifier: str | UUID

    id: UUID
    username: str
    display_name: str = Field(alias='displayName')
    avatar: str = ''  # no avatar in reply_to # ! can be url
    clan_avatar: str = Field('', alias='clanAvatar')  # always emoji
    verified: bool = False
    pin: Pin | None = None
    banner: str | None = None
    bio: str | None = None
    nickname: Nickname | None = Field(None, alias='activeNickname')

    def __init__(self, username_or_id: str | UUID, client: Client | None = None) -> None:
        self._identifier = username_or_id
        if isinstance(username_or_id, str) and username_or_id != 'me':
            self.username = username_or_id
        elif isinstance(username_or_id, UUID):
            self.id = username_or_id
        super().__init__(client)

    def __str__(self) -> str:
        return self.display_name

    def _refresh(self, *, client: Client):
        return get_user(client, self._identifier).json()

    @cached_property
    def posts(self) -> UserPosts:
        from itd.models.post import UserPosts

        return UserPosts(self, client=self.client)

    @cached_property
    def liked_posts(self) -> LikedPosts:
        from itd.models.post import LikedPosts

        return LikedPosts(self, client=self.client)

    @cached_property
    def event_profile(self) -> EventProfile:
        return EventProfile(self.id, client=self.client)

    @property
    def url(self) -> str:
        return f'https://xn--d1ah4a.com/@{self.username}'

    @property
    def link(self) -> str:
        return self.url

    @property
    def has_picture_avatar(self) -> bool:
        return self.avatar.startswith('http')

    def __hash__(self):
        return int(self.id)


class User(_UserBase):
    is_following: bool = Field(False, alias='isFollowing')
    is_followed_by: bool = Field(False, alias='isFollowedBy')

    is_blocked_by: bool = Field(
        False, alias='isBlockedByThem'
    )  # not 100% true, server returns value only if isBlockedByThem is True and isBlockedByMe is False
    is_blocking: bool = Field(False, alias='isBlockedByMe')
    blocked_at: Annotated[datetime, BeforeValidator(parse_datetime)] | None = Field(None, alias='blockedAt')

    followers_count: int | None = Field(None, alias='followersCount')
    following_count: int | None = Field(None, alias='followingCount')
    posts_count: int | None = Field(None, alias='postsCount')

    wall_access: AccessType | None = Field(None, alias='wallAccess')  # none if blocked
    likes_visibility: AccessType | None = Field(None, alias='likesVisibility')  # none if blocked
    is_private: bool | None = Field(None, alias='isPrivate')  # none if following or blocked
    can_message: bool = Field(False, alias='canMessage')

    is_subscribed: bool = Field(False, alias='hasNuksta')
    last_seen: LastSeen | None = Field(None, alias='lastSeen')  # none if hidden or blocked
    online: bool = False

    pinned_post_id: UUID | None = Field(None, alias='pinnedPostId')  # none if no or blocked

    created_at: Annotated[datetime, BeforeValidator(parse_datetime)] | None = Field(None, alias='createdAt')  # none if blocked

    def _post_refresh(self, context: dict = {}):
        if 'id' in self.__dict__:
            self._identifier = self.id
        else:
            self._identifier = self.username

    @classmethod
    def by_id(cls, id: UUID | str) -> 'User':
        return cls(to_uuid(id))

    @classmethod
    def by_username(cls, username: str) -> 'User':
        return cls(username)

    @classmethod
    def by_u(cls, username: str) -> 'User':  # just abbr for username
        return User.by_username(username)

    @classmethod
    def me(cls, client: Client | None = None) -> 'Me':
        return Me(client)

    def for_client(self, client: Client) -> 'User':
        return User(self._identifier, client=client)

    def complete_actions_for_wall_access(self, client: Client | None = None) -> bool:
        if client != self.client:
            user = User(self._identifier, client)
        else:
            user = self

        if user.wall_access == AccessType.NOBODY:
            return False
        if user.wall_access == AccessType.MUTUAL:
            if user.is_followed_by:
                if not user.is_following:
                    user.follow(client)
                return True
            return False
        if user.wall_access == AccessType.FOLLOWERS:
            if not user.is_following:
                user.follow(client)
        return True

    def complete_actions_for_likes_visibility(self, client: Client | None = None) -> bool:
        if client != self.client:
            user = User(self._identifier, client)
        else:
            user = self

        if user.likes_visibility == AccessType.NOBODY:
            return False
        if user.likes_visibility == AccessType.MUTUAL:
            if user.is_followed_by:
                if not user.is_following:
                    user.follow(client)
                return True
            return False
        if user.likes_visibility == AccessType.FOLLOWERS:
            if not user.is_following:
                user.follow(client)
        return True

    @property
    def can_post_on_wall(self) -> bool:
        if self.wall_access == AccessType.NOBODY:
            return False
        if self.wall_access == AccessType.MUTUAL:
            return self.is_following and self.is_followed_by
        if self.wall_access == AccessType.FOLLOWERS:
            return self.is_following
        return True

    @property
    def can_see_liked_posts(self) -> bool:
        if self.likes_visibility == AccessType.NOBODY:
            return False
        if self.likes_visibility == AccessType.MUTUAL:
            return self.is_following and self.is_followed_by
        if self.likes_visibility == AccessType.FOLLOWERS:
            return self.is_following
        return True

    def report(self, reason: ReportReason, description: str | None = None, client: Client | None = None) -> Report:
        return Report(self.id, ReportTargetType.USER, reason, description, client or self.client)

    def follow(self, client: Client | None = None) -> int:
        self.followers_count = follow(client or self.client, self._identifier).json()['followersCount']
        if (client or self.client) == self.client:
            self.is_following = True

        return self.followers_count

    def unfollow(self, client: Client | None = None) -> int:
        self.followers_count = unfollow(client or self.client, self._identifier).json()['followersCount']
        if (client or self.client) == self.client:
            self.is_following = True

        return self.followers_count

    def block(self, client: Client | None = None) -> None:
        block(client or self.client, self._identifier)
        if (client or self.client) == self.client:
            self.is_blocking = True

    def unblock(self, client: Client | None = None) -> None:
        unblock(client or self.client, self._identifier)
        if (client or self.client) == self.client:
            self.is_blocking = False

    def post(
        self, content: str | None = None, spans: list[Span] = [], attachments: ATTACHMENTS = [], poll: NewPoll | None = None, client: Client | None = None
    ) -> Post:
        from itd.models.post import Post  # stupid circular import

        return Post.new(content, spans, attachments, poll, self, client or self.client)

    @cached_property
    def following(self) -> list[User]:
        return [User.from_dict(user, client=self.client) for user in get_following(self.client, self._identifier).json()['data']['users']]

    @cached_property
    def followers(self) -> list[User]:
        return [User.from_dict(user, client=self.client) for user in get_followers(self.client, self._identifier).json()['data']['users']]

    def get_follow_status(self) -> bool:
        return get_follow_status(self)

    @classmethod
    def search(cls, query: str):
        result = Users.search(query, limit=1)
        if result:
            return result[0]
        raise NotFoundError('User')


class Me(_UserBase):
    wall_access: AccessType = Field(alias='wallAccess')
    likes_visibility: AccessType = Field(alias='likesVisibility')
    is_private: bool = Field(False, alias='isPrivate')
    is_phone_verified: bool = Field(alias='isPhoneVerified')
    subscription: Subscription

    followers_count: int = Field(alias='followersCount')
    following_count: int = Field(alias='followingCount')
    posts_count: int = Field(alias='postsCount')

    created_at: Annotated[datetime, BeforeValidator(parse_datetime)] = Field(alias='createdAt')

    def __init__(self, client: Client | None = None) -> None:
        super().__init__('me', client)
        self.privacy = Privacy(self.client)
        self._init_refresh()

    def _post_refresh(self, context: dict = {}):
        if self.pin:
            self.pin._user = self
        for name in ('is_private', 'wall_access', 'likes_visibility'):
            setattr(self.privacy, name, getattr(self, name))
        self.privacy.load_status = LoadStatus.PARTIALLY

    def to_user(self) -> User:
        instance = User.__new__(User)
        ITDBaseModel.__init__(instance, self._client)
        for name in instance._validator.model_fields:
            if hasattr(self, name):
                setattr(instance, name, getattr(self, name))
        instance._identifier = self.id
        instance.load_status = LoadStatus.PARTIALLY
        return instance

    def delete(self) -> datetime:  # should not use other client, because you can get Me only from current client
        return parse_datetime(delete_account(self.client).json()['restoreDeadline'])

    def restore(self) -> None:
        restore_account(self.client)

    def update_privacy(
        self,
        is_private: bool | None = None,
        wall_access: AccessType | None = None,
        likes_visibility: AccessType | None = None,
        show_last_seen: bool | None = None
    ):
        self.privacy.update(is_private, wall_access, likes_visibility, show_last_seen)

    def update(
        self,
        bio: str | None = None,
        display_name: str | None = None,
        username: str | None = None,
        banner_id: UUID | str | Unset | None = None,  # deprecated
        banner: UUID | str | Unset | File | None = None
    ):
        if isinstance(banner, File):
            banner_id = banner.id
        elif banner:
            banner_id = banner
        if isinstance(banner_id, str):
            banner_id = to_uuid(banner_id)
        update_profile(self.client, bio, display_name, username, banner_id)
        if bio is not None:
            self.bio = bio
        if display_name is not None:
            self.display_name = display_name
        if username is not None:
            self.username = username

    def update_from_fields(self):
        update_profile(self.client, self.bio, self.display_name, self.username)

    def remove_pin(self) -> None:
        if object.__getattribute__(self, 'pin'):
            assert self.pin
            self.pin.remove()
        else:
            remove_pin(self.client)  # if pins not loaded just use straight call

    def set_pin(self, pin: Pin | str | None = None):
        if pin is None:
            if self.pins:
                self.pins[0].set()
            else:
                raise ValueError('No pins available')
        elif isinstance(pin, str):
            pins = [_pin for _pin in self.pins if _pin.slug == pin]
            if pins:
                pins[0].set()
            else:
                raise PinNotOwnedError(pin)
        else:
            if pin.slug in [p.slug for p in self.pins]:
                pin.set(self.client)  # can be not our pin, so set our client to ensure client is correct
            else:
                raise PinNotOwnedError(pin.slug)

    @cached_property
    def followers(self) -> 'Followers':
        return Followers(self.id)

    @cached_property
    def following(self) -> 'Following':
        return Following(self.id)

    @cached_property
    def pins(self) -> list[Pin]:
        return [Pin.from_dict(pin, context={'user': self}, client=self.client) for pin in get_pins(self.client).json()['data']['pins']]

    @cached_property
    def blocked(self) -> Blocked:
        return Blocked()

    @cached_property
    def profile(self) -> Profile:
        return Profile(self.client)

    def _refresh(self, *, client: Client):
        user = get_user(client, self._identifier).json()
        if user.get('isDeleted'):
            exc = AccountDeletedError()
            exc.can_restore = user.get('canRestore', True)
            exc.restore_deadline = parse_datetime(user['restoreDeadline']) if 'restoreDeadline' in user else None
            raise exc
        return user

    @cached_property
    def event_balance(self) -> int:
        return get_event_balance(self.client).json()['balance']

    @cached_property
    def event_inventory(self) -> list[EventItem]:
        return [EventItem.model_validate(item) for item in get_my_event_inventory(self.client).json()['items']]

    @cached_property
    def event_red_pens_count(self) -> int:
        return get_event_red_pens_inventory(self.client).json()['data']['events'][0]['balance']

    @cached_property
    def event_correctors_count(self) -> int:
        return get_event_correctors_inventory(self.client).json()['data']['events'][0]['balance']


class Followers(ITDList[User]):
    _load_with_parent = False
    cursor: int = 1
    _is_page_pagination = True

    def __init__(self, id: UUID):
        self.user_id = id

    def _fetch(self, client: Client, limit: int) -> dict:
        return get_followers(client, self.user_id, self.cursor, limit).json()['data']

    @staticmethod
    def _get_has_more(data: dict) -> bool:
        return data['pagination']['hasMore']

    @staticmethod
    def _get_total(data: dict):
        return data['pagination']['total']

    @staticmethod
    def _get_objects(data: dict) -> list[dict]:
        return data['users']

    @staticmethod
    def _get_cursor(data: dict):
        return data['pagination']['page'] + 1

    def _to_models(self, objects: list, client: Client):
        return [User.from_dict(user, client=client) for user in objects]


class Following(Followers):
    def _fetch(self, client: Client, limit: int) -> dict:
        return get_following(client, self.user_id, self.cursor, limit).json()['data']


class Blocked(Followers):
    def __init__(self):
        super(Followers, self).__init__()

    def _fetch(self, client: Client, limit: int) -> dict:
        return get_blocked(client, self.cursor, limit).json()['data']


class WhoToFollow(ITDBaseModel, list[User]):
    _refreshable = False

    def __init__(self, client: Client | None = None) -> None:
        super().__init__(client)
        self.refresh()

    def refresh(self, *, client: Client | None = None):
        self.load()

    def load(self):
        self.clear()
        self.extend([User.from_dict(user, client=self.client) for user in get_who_to_follow(self.client).json()['users']])


class Users(ITDBaseModel, list[User]):
    _refreshable = False

    def __init__(self, query: str, limit: int = 10, client: Client | None = None):
        super().__init__(client)
        self.query = query
        self.load(limit)

    def load(self, limit: int = 10):
        self.clear()
        self.extend([User.from_dict(hashtag) for hashtag in search(self.client, self.query, limit, 1).json()['data']['users']])
        return self

    @classmethod
    def search(cls, query: str, limit: int = 10):  # чисто для симетрии с хэштэгсами
        return cls(query, limit)


@overload
def get_follow_status(users: list[User | UUID | str], *, client: Client | None = None) -> dict[UUID, bool]: ...


@overload
def get_follow_status(users: User | UUID | str, *, client: Client | None = None) -> bool: ...


def get_follow_status(users: list[User | UUID | str] | User | UUID | str, *, client: Client | None = None) -> dict[UUID, bool] | bool:
    """Получить статус подписки

    Args:
        users (list[User | UUID | str] | User | UUID | str): Пользователи для проверки (можно как и списком, так и как одиночным объектом)

    Returns:
        dict[UUID, bool] | bool: Результат
    """
    user_ids: list[UUID] = []
    if isinstance(users, list):
        for user in users:
            if isinstance(user, User):
                user_ids.append(user.id)
            else:
                user_ids.append(to_uuid(user))  # ty: ignore[invalid-argument-type]
    elif isinstance(users, User):
        user_ids = [users.id]
    else:
        user_ids = [to_uuid(users)]

    res = {UUID(k): v for k, v in _get_follow_status((client or get_default_client()), user_ids).json()['data'].items()}
    if not isinstance(users, list):
        return next(iter(res.values()))
    return res
