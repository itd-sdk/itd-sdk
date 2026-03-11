from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from itd.models.pin import ShortPin
from itd.enums import AccessType


class _UserPrivacy(BaseModel):
    private: bool | None = Field(None, alias='isPrivate') # none for not me
    wall_access: AccessType = Field(AccessType.EVERYONE, alias='wallAccess')
    likes_visibility: AccessType = Field(AccessType.EVERYONE, alias='likesVisibility')

    model_config = {'serialize_by_alias': True}


class UserPrivacy(_UserPrivacy):
    show_last_seen: bool = Field(True, alias='showLastSeen')


class UserPrivacyData:
    def __init__(self, private: bool | None = None, wall_access: AccessType | None = None, likes_visibility: AccessType | None = None, show_last_seen: bool | None = None) -> None:
        self.private = private
        self.wall_access = wall_access
        self.likes_visibility = likes_visibility
        self.show_last_seen = show_last_seen

    def to_dict(self):
        data = {}
        if self.private is not None:
            data['isPrivate'] = self.private
        if self.wall_access is not None:
            data['wallAccess'] = self.wall_access.value
        if self.likes_visibility is not None:
            data['likesVisibility'] = self.likes_visibility.value
        if self.show_last_seen is not None:
            data['showLastSeen'] = self.show_last_seen

        return data


class _UserBase(BaseModel):
    username: str | None = None
    display_name: str = Field(alias='displayName')

class _UserId(_UserBase):
    id: UUID


class UserProfileUpdate(_UserId):
    bio: str | None = None
    updated_at: datetime | None = Field(None, alias='updatedAt')


class _UserAvatar(_UserBase):
    verified: bool = False
    avatar: str


class UserBlock(_UserAvatar):
    blocked_at: datetime = Field(alias='blockedAt')


class UserNewPost(_UserAvatar):
    pin: ShortPin | None = None


class UserNotification(UserNewPost, _UserId):
    pass


class UserPost(UserNotification):
    pass


class UserWhoToFollow(UserPost):
    followers_count: int = Field(0, alias='followersCount')


class UserFollower(UserPost):
    is_following: bool = Field(False, alias='isFollowing') # none for me


class UserSearch(UserFollower, UserWhoToFollow):
    pass


class User(UserSearch, _UserPrivacy):
    banner: str | None = None
    bio: str | None = None
    pinned_post_id: UUID | None = Field(None, alias='pinnedPostId')

    following_count: int = Field(0, alias='followingCount')
    posts_count: int = Field(0, alias='postsCount')

    is_followed: bool | None = Field(None, alias='isFollowedBy') # none for me
    is_blocked: bool = Field(False, alias='isBlockedByMe')
    is_blocking: bool = Field(False, alias='isBlockedByThem')

    created_at: datetime | None = Field(None, alias='createdAt') # none for blocked
    last_seen_at: datetime | dict | None = Field(None, alias='lastSeen')
    online: bool = False
