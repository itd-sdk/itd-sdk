from __future__ import annotations
from typing import TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from math import ceil

from pydantic import Field, BaseModel, field_validator

from itd.base import ITDBaseModel, refresh_wrapper
from itd.enums import AccessType, ALL, All, Unset, Role
from itd.exceptions import PinNotOwned
from itd.pin import Pin
from itd.routes.users import (
    get_user, follow, unfollow, block, unblock, get_followers, get_following, delete_account,
    restore_account, get_blocked, get_privacy, update_privacy, update_profile, get_profile
)
from itd.routes.pins import get_pins, remove_pin
from itd.routes.subscription import get_subscription, pay_subscription, get_payment_methods, toggle_subscription_auto_renewal
from itd.utils import to_uuid
if TYPE_CHECKING:
    from itd.client import Client


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
    _validator = lambda _: _ProfileValidate
    _load_with_parent = False

    authenticated: bool = True
    user: ProfileUser | None
    banned: bool = False

    @refresh_wrapper
    def refresh(self, client: Client | None = None):
        return get_profile(client or self.client).json()

    def __str__(self) -> str:
        return str(self.user)

class _ProfileValidate(BaseModel, Profile):
    pass



class Privacy(ITDBaseModel):
    _validator = lambda _: _PrivacyValidate
    _user: 'Me | None' = None
    _load_with_parent = False

    is_private: bool = Field(False, alias='isPrivate')
    wall_access: AccessType = Field(alias='wallAccess')
    likes_visibility: AccessType = Field(alias='likesVisibility')
    show_last_seen: bool = Field(True, alias='showLastSeen')

    @refresh_wrapper
    def refresh(self, client: Client | None = None):
        return get_privacy(client or self.client)

    def update(self,
        is_private: bool | None = None,
        wall_access: AccessType | None = None,
        likes_visibility: AccessType | None = None,
        show_last_seen: bool | None = None,
        client: Client | None = None
    ):
        data = update_privacy(client or self.client, is_private, wall_access, likes_visibility, show_last_seen).json()
        if data['isPrivate']:
            self.is_private = data['isPrivate']
        if data['wallAccess']:
            self.wall_access = AccessType(data['wallAccess'])
        if data['likesVisibility']:
            self.likes_visibility = AccessType(data['likesVisibility'])
        if data['showLastSeen']:
            self.show_last_seen = data['showLastSeen']

        if self._user:
            for field in ('wall_access', 'likes_visibility', 'is_private'):
                setattr(self._user, field, getattr(self, field))

    def update_from_fields(self): # you can update fields (like privacy.is_private = True), then exec this func to update
        self.update(self.is_private, self.wall_access, self.likes_visibility, self.show_last_seen)

    @classmethod
    def _from_user(cls, user: 'Me', client: Client | None = None):
        instance = cls(client)
        instance._user = user
        return instance

    def __getattribute__(self, name: str):
        if name in ('is_private', 'wall_access', 'likes_visibility') and object.__getattribute__(self, '_user'):
            setattr(self, name, getattr(object.__getattribute__(self, '_user'), name))
        return super().__getattribute__(name)


class _PrivacyValidate(BaseModel):
    pass


class Subscription(ITDBaseModel):
    _validator = lambda _: _SubscriptionValidate
    _payment_methods: list

    active: bool = Field(False, alias='isActive')
    expires_at: datetime | None = Field(None, alias='expiresAt')
    auto_renewal: bool = Field(True, alias='autoRenewal')

    def __init__(self, data: dict, client: Client | None = None):
        super().__init__(client)

        validated = _SubscriptionValidate.model_validate(data)
        self._fields_from_data = validated.model_fields_set
        for name, value in validated.__dict__.items():
            setattr(self, name, value)

    @refresh_wrapper
    def refresh(self, client: Client | None = None): # refreshes only is_active
        return get_subscription(client or self.client).json()

    def pay(self):
        return pay_subscription(self.client).json()['confirmationUrl']

    def set_auto_renewal(self, enabled: bool) -> bool:
        self.auto_renewal = toggle_subscription_auto_renewal(self.client, enabled).json()['autoRenewal']
        return self.auto_renewal

    def toggle_auto_renewal(self) -> bool:
        return self.set_auto_renewal(not self.auto_renewal)

    @property
    def payment_methods(self):
        if getattr(self, '_payment_methods', None) is None:
            self._payment_methods = get_payment_methods(self.client).json()['data']
        return self._payment_methods

    def __bool__(self):
        return self.active

    def __str__(self) -> str:
        return str(self.active)


class _SubscriptionValidate(BaseModel, Subscription):
    pass



class _UserBase(ITDBaseModel):
    _identifier: str | UUID

    id: UUID
    username: str
    display_name: str = Field(alias='displayName')
    avatar: str
    verified: bool = False
    pin: Pin | None = None
    banner: str | None = None
    bio: str | None = None

    pinned_post_id: UUID | None = Field(None, alias='pinnedPostId') # none if no or blocked

    followers_count: int | None = Field(None, alias='followersCount')
    following_count: int | None = Field(None, alias='followingCount')
    posts_count: int = Field(0, alias='postsCount')

    is_blocked: bool = Field(False, alias='isBlockedByMe')
    is_blocking: bool = Field(False, alias='isBlockedByThem')

    created_at: datetime | None = Field(None, alias='createdAt') # none if blocked
    last_seen: datetime | dict | None = Field(None, alias='lastSeen') # none if hidden or blocked
    online: bool = False

    def __init__(self, username_or_id: str | UUID, client: Client | None = None) -> None:
        self._identifier = username_or_id
        if isinstance(username_or_id, str) and username_or_id != 'me':
            self.username = username_or_id
        elif isinstance(username_or_id, UUID):
            self.id = username_or_id

        super().__init__(client)


    def __str__(self) -> str:
        return self.display_name

    def __int__(self) -> int:
        return self.followers_count or 0

    @refresh_wrapper
    def refresh(self, client: Client | None = None):
        return get_user(client or self.client, self._identifier).json()




class User(_UserBase):
    _validator = lambda _: _UserValidate
    _fields_from_data: set[str] = set()

    _followers: list = []
    _following: list = []

    is_following: bool = Field(False, alias='isFollowing')
    is_followed_by: bool = Field(False, alias='isFollowedBy')

    blocked_at: datetime | None = Field(None, alias='blockedAt')

    wall_access: AccessType | None = Field(None, alias='wallAccess') # none if blocked
    likes_visibility: AccessType | None = Field(None, alias='likesVisibility') # none if blocked
    is_private: bool | None = Field(None, alias='isPrivate') # none if following or blocked
    is_subscribed: bool = Field(False, alias='hasNuksta')

    @classmethod
    def _from_dict(cls, data: dict, set_loaded: bool = True, client: Client | None = None):
        instance = cls(data['username'], client)
        validated = _UserValidate.model_validate(data)
        instance._fields_from_data = validated.model_fields_set
        for name, value in validated.__dict__.items():
            setattr(instance, name, value)

        instance._loaded = set_loaded
        return instance

    @classmethod
    def by_id(cls, id: UUID | str) -> 'User':
        return cls(to_uuid(id))

    @classmethod
    def by_username(cls, username: str) -> 'User':
        return cls(username)

    @classmethod
    def by_u(cls, username: str) -> 'User': # just abbr for username
        return User.by_username(username)

    @classmethod
    def me(cls, client: Client | None = None) -> 'Me':
        return Me(client)

    def follow(self, client: Client | None = None) -> int:
        self.followers_count = follow(client or self.client, self._identifier).json()['followersCount']
        assert self.followers_count is not None
        return self.followers_count

    def unfollow(self, client: Client | None = None) -> int:
        self.followers_count = unfollow(client or self.client, self._identifier).json()['followersCount']
        assert self.followers_count is not None
        return self.followers_count

    def block(self, client: Client | None = None) -> None:
        block(client or self.client, self._identifier)
        self.is_blocking = True

    def unblock(self, client: Client | None = None) -> None:
        unblock(client or self.client, self._identifier)
        self.is_blocking = False

    @property
    def following(self) -> list:
        if not self._following:
            self._following = [User._from_dict(user, False, self.client) for user in get_following(self.client, self._identifier).json()['data']['users']]
        return self._following

    @property
    def followers(self) -> list:
        if not self._followers:
            self._followers = [User._from_dict(user, False, self.client) for user in get_followers(self.client, self._identifier).json()['data']['users']]
        return self._followers



class _UserValidate(BaseModel, User):
    @field_validator('pin', mode='plain')
    @classmethod
    def validate_pin(cls, pin: dict | None):
        if pin:
            return Pin(pin)



class Me(_UserBase):
    _validator = lambda _: _MeValidate

    _followers: 'Followers'
    _following: 'Following'
    _blocked: 'Blocked'
    _pins: list[Pin]

    wall_access: AccessType = Field(alias='wallAccess')
    likes_visibility: AccessType = Field(alias='likesVisibility')
    is_private: bool = Field(False, alias='isPrivate')
    is_phone_verified: bool = Field(alias='isPhoneVerified')
    subscription: Subscription

    def __init__(self, client: Client | None = None) -> None:
        super().__init__('me', client)

        self._blocked = Blocked()
        self._followers = Followers()
        self._following = Following()
        self._pins: list[Pin] = []
        self.privacy: Privacy = Privacy._from_user(self, self.client)
        self.profile: Profile = Profile(self.client)


    def to_user(self) -> User:
        instance = User.__new__(User)
        ITDBaseModel.__init__(instance, self._client)
        for name in _UserValidate.model_fields:
            if hasattr(self, name):
                setattr(instance, name, getattr(self, name))
        instance._loaded = self._loaded
        return instance

    def delete(self) -> None: # should not use other client, because you can get Me only from current client
        delete_account(self.client)

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

    def update_profile(
        self,
        bio: str | None = None,
        display_name: str | None = None,
        username: str | None = None,
        banner_id: UUID | str | Unset | None = None
    ):
        if isinstance(banner_id, str):
            banner_id = to_uuid(banner_id)
        update_profile(self.client, bio, display_name, username, banner_id)

    def remove_pin(self) -> None:
        if object.__getattribute__(self, 'pin'):
            self.pin.remove() # pyright: ignore[reportOptionalMemberAccess]
        else:
            remove_pin(self.client) # if pins not loaded just use straight call

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
                raise PinNotOwned(pin)
        else:
            if pin.slug in [p.slug for p in self.pins]:
                pin.set(self.client) # can be not our pin, so set our client to ensure client is correct
            else:
                raise PinNotOwned(pin.slug)


    @property
    def blocked(self) -> 'Blocked':
        if not self._blocked:
            self._blocked._client = self.client
            self._blocked.load()
        return self._blocked

    @property
    def followers(self) -> 'Followers':
        if not self._followers:
            self._followers._user_id = self.id
            self._followers._client = self._client
            self._followers.load()
        return self._followers

    @property
    def following(self) -> 'Following':
        if not self._following:
            self._following._user_id = self.id
            self._following._client = self._client
            self._following.load()
        return self._following

    @property
    def pins(self) -> list[Pin]:
        if not self._pins:
            self._pins = [Pin(pin, self) for pin in get_pins(self.client).json()['data']['pins']]
        return self._pins

    def __getattribute__(self, name: str):
        value = super().__getattribute__(name)
        if name == 'pin' and value is not None and getattr(value, '_user', None) is None:
            value._user = self
        return value



class _MeValidate(BaseModel, Me):
    @field_validator('pin', mode='plain')
    @classmethod
    def validate_pin(cls, pin: dict) -> Pin:
        return Pin(pin)

    @field_validator('subscription', mode='plain')
    @classmethod
    def validate_subscription(cls, subscription: dict) -> Subscription:
        return Subscription(subscription)



class Followers(ITDBaseModel, list[User]):
    _refreshable = False

    _user_id: UUID
    limit: int = 20 # blocked can load 100, so it its var (not const)
    has_more: bool = True
    total: int = 0


    def _fetch(self, client: Client, page: int) -> dict:
        return get_followers(client, self._user_id, page).json()['data']

    def load(self, count: int | All = limit, client: Client | None = None) -> 'Followers':
        if isinstance(count, All):
            ncount = None
        else:
            ncount = count

        left = ncount or self.limit # if None get [20] firstly
        page = ceil(len(self) / self.limit) + 1

        while left > 0: # can be !=, but what if something went wrong
            data = self._fetch(
                client or self.client,
                page,
            )
            page += 1
            self.has_more = data['pagination']['hasMore']
            self.total = data['pagination']['total']

            if ncount is None:
                left = self.total - len(self)

            users = data['users']
            left -= len(users)
            if not users or not self.has_more:
                break

            print(f'fetched {len(users)} left={left} (was {len(self)})')
            self.extend([User._from_dict(user, False, self.client) for user in users])
        return self

    def load_all(self, client: Client | None = None) -> 'Followers':
        return self.load(ALL, client)

    def refresh(self, count: int | None = None, client: Client | None = None) -> 'Followers': # "None" count means already loaded count
        count = count or len(self)
        self.clear()
        return self.load(count, client)

    def __setattr__(self, name: str, value) -> None:
        if name == '_client':
            for user in self:
                user._client = value
        super().__setattr__(name, value)

    @property
    def all(self) -> "Followers": # me.followers.all
        return self.load_all()


class Following(Followers):
    def _fetch(self, client: Client, page: int) -> dict:
        return get_following(client, self._user_id, page).json()['data']


class Blocked(Followers):
    limit = 100

    def _fetch(self, client: Client, page: int) -> dict:
        return get_blocked(client, page).json()['data']